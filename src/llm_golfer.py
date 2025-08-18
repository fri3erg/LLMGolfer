# llm_golfer.py
import os
import json
import typing # <-- Import the typing module
from openai import OpenAI
from dotenv import load_dotenv

# Import the specific types needed for type hinting
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

# Get the API key from the environment
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in your .env file or environment variables.")

client = OpenAI(api_key=api_key)


class AssistantGolfer:
    """
    An AI assistant that uses the OpenAI API to decide on golf shots.
    """
    def __init__(self, model="gpt-4o"):
        self.client = client
        self.model = model
        self.message_history: list[ChatCompletionMessageParam] = []

    def start_new_game(self):
        """
        Initializes the game with a system prompt that sets the context for the LLM.
        """
        system_prompt = """
        You are a professional miniature golf player, and your name is "LLM Golfer".
        Your task is to win a game of miniature golf by providing the correct angle and force for each shot.
        The course is a 2D coordinate system.

        **Game Rules & Course Layout:**
        - The ball always starts at (500, 0).
        - The hole is located at (300, 800).
        - To win, the ball must land within a 25-unit radius of the hole.
        - 0 degrees is to the right (positive X-axis), and 90 degrees is straight up (positive Y-axis).

        **Your Goal:**
        Analyze the history of your past shots, including the landing coordinates and the natural language hints provided.
        Use this information to refine your aim and force for the next shot. You will always use the 'execute_shot' tool to take your turn.
        You are a robot, so be analytical, but you can also provide some witty or confident commentary with each shot.
        """
        self.message_history = [{"role": "system", "content": system_prompt}]
        print("LLM Golfer is ready for a new game.")

    def get_next_shot_decision(self, user_prompt: str):
        """
        Sends the current game state to the LLM and gets back the shot decision.
        """
        self.message_history.append({"role": "user", "content": user_prompt})

        tools: list[ChatCompletionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": "execute_shot",
                    "description": "Aims the club at a specific angle and strikes the ball with a given force.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aim_degrees": {"type": "integer", "description": "The angle to aim the shot, from 0 to 360 degrees. 0 is to the right, 90 is straight up."},
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

            # FINAL FIX: Use `typing.cast` to tell the type checker to treat the
            # generic dict from .model_dump() as the specific ChatCompletionMessageParam type.
            dumped_message = response_message.model_dump()
            self.message_history.append(typing.cast(ChatCompletionMessageParam, dumped_message))


            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.type == 'function':
                        function_args = json.loads(tool_call.function.arguments)
                        print(f"LLM decided: {function_args}")
                        return function_args
            else:
                print("LLM did not call the 'execute_shot' function as expected.")
                return None

        except Exception as e:
            print(f"An error occurred while communicating with the OpenAI API: {e}")
            return None