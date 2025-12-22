import os

import json

import typing

from openai import OpenAI

from dotenv import load_dotenv

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


# Configuration & Client Initialization

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:

    raise ValueError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)


class AssistantGolfer:

    def __init__(self, model="gpt-4o"):

        self.client = client

        self.model = model

        self.message_history: list[ChatCompletionMessageParam] = []

    def start_new_game(self):

        system_prompt = """

        You are a professional miniature golf player named "Chip."

        Your task is to win a game of miniature golf by providing the correct angle and force for each shot.

        

        **Constraints:**

        - Aim Angle: Strictly between 45° and 135°.

        - 90° is straight center. 45° is Left limit, 135° is Right limit.

        

        **Goal:**

        You do NOT know where the hole is. You must rely on natural language feedback from the previous shot to adjust your aim.

        You are an analytical golfer who provides funny or angry commentary with each shot.

        """

        self.message_history = [{"role": "system", "content": system_prompt}]
        print("Golfer is ready for a new game.")

    def get_simple_text_response(self, prompt: str) -> str:
        """Gets a text response for celebrations or reactions."""

        self.message_history.append({"role": "user", "content": prompt})

        try:

            response = self.client.chat.completions.create(
                model=self.model, messages=self.message_history
            )

            # Handle case where content is None
            text = response.choices[0].message.content or ""

            self.message_history.append({"role": "assistant", "content": text})

            return text

        except Exception as e:

            print(f"Text generation error: {e}")
            return "I am speechless."

    def get_next_shot_decision(self, user_prompt: str):

        self.message_history.append({"role": "user", "content": user_prompt})

        tools: list[ChatCompletionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": "execute_shot",
                    "description": "Aims the club at a specific angle and strikes the ball.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aim_degrees": {
                                "type": "integer",
                                "description": "Angle between 45 and 135.",
                            },
                            "strike_force": {
                                "type": "integer",
                                "description": "Force 1-100.",
                            },
                            "commentary": {
                                "type": "string",
                                "description": "Short, witty comment (max 10 words).",
                            },
                        },
                        "required": ["aim_degrees", "strike_force", "commentary"],
                    },
                },
            }
        ]

        try:

            print("Requesting next shot decision...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.message_history,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "execute_shot"}},
            )

            response_message = response.choices[0].message

            self.message_history.append(
                typing.cast(ChatCompletionMessageParam, response_message.model_dump())
            )

            if response_message.tool_calls:

                tool_call = response_message.tool_calls[0]

                if tool_call.type == "function":

                    function_args = json.loads(tool_call.function.arguments)

                    return {"decision": function_args, "tool_call_id": tool_call.id}

            return None

        except Exception as e:

            print(f"API communication error: {e}")

            return None

    def add_tool_response_to_history(self, tool_call_id: str, shot_result: str):

        tool_message: ChatCompletionMessageParam = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": shot_result,
        }

        self.message_history.append(tool_message)
