# llm_golfer.py
import os
import json
import typing
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

# --- Configuration & Client Initialization (is the same) ---
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set.")
client = OpenAI(api_key=api_key)


class AssistantGolfer:
    # ... (__init__ and start_new_game methods are the same) ...
    def __init__(self, model="gpt-4o"):
        self.client = client
        self.model = model
        self.message_history: list[ChatCompletionMessageParam] = []

    def start_new_game(self):
        system_prompt = """
        You are a professional miniature golf player named "Chip."
        Your task is to win a game of miniature golf by providing the correct angle and force for each shot.
        
        **Coordinate & Angle System:**
        - The course is a 2D coordinate system.
        - Angles are in degrees: 0° is to the right (positive X-axis), 90° is straight up (positive Y-axis), 180° is to the left.
        - For example, to shoot from (0,0) towards (10,10), the angle would be 45°. To shoot from (0,0) towards (-10, 0), the angle would be 180°.

        **Your Goal:**
        You will be given the start coordinates, the hole coordinates, and a history of your past shots.
        Analyze the landing coordinates and the natural language hints to refine your aim and force.
        You must always use the 'execute_shot' tool to take your turn.
        You are an analytical AI, but please provide funny or angry commentary with each shot.
        """
        self.message_history = [{"role": "system", "content": system_prompt}]
        print("LLM Golfer is ready for a new game.")


    def get_next_shot_decision(self, user_prompt: str):
        self.message_history.append({"role": "user", "content": user_prompt})
        
        # ... (tools definition is the same) ...
        tools: list[ChatCompletionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": "execute_shot",
                    "description": "Aims the club at a specific angle and strikes the ball with a given force.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aim_degrees": {"type": "integer", "description": "The angle to aim the shot, from 0 to 180 degrees. 0 is to the right, 90 is straight up."},
                            "strike_force": {"type": "integer", "description": "The force of the shot, on a scale of 1 (a gentle tap) to 100 (full power)."},
                            "commentary": {"type": "string", "description": "A brief, witty, or analytical comment about the planned shot."}
                        },
                        "required": ["aim_degrees", "strike_force", "commentary"]
                    }
                }
            }
        ]

        try:
            print("⛳ Asking the LLM for the next shot...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.message_history,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "execute_shot"}}
            )
            response_message = response.choices[0].message
            self.message_history.append(typing.cast(ChatCompletionMessageParam, response_message.model_dump()))

            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                if tool_call.type == 'function':
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"LLM decided: {function_args}")
                    
                    # *** CHANGE 1: Return the tool_call_id along with the decision ***
                    return {
                        "decision": function_args,
                        "tool_call_id": tool_call.id
                    }
            return None
        except Exception as e:
            print(f"An error occurred while communicating with the OpenAI API: {e}")
            return None

    # *** CHANGE 2: Add a new method to record the tool's result ***
    def add_tool_response_to_history(self, tool_call_id: str, shot_result: str):
        """
        Adds the result of the tool call to the message history.
        This is required by the OpenAI API.
        """
        tool_message: ChatCompletionMessageParam = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": shot_result
        }
        self.message_history.append(tool_message)
        print("Tool response added to history.")