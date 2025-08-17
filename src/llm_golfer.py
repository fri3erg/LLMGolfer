# llm_golfer.py
import openai
import json
import os
from dotenv import load_dotenv

# 1. IMPORT BOTH SPECIFIC TYPES FROM THE OPENAI LIBRARY
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat import ChatCompletionMessageParam

# --- Load environment variables and initialize client ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found in .env file.")
client = openai.OpenAI(api_key=api_key)


def get_available_tools() -> list[ChatCompletionToolParam]:
    """Defines the tools (functions) the LLM can call."""
    tools: list[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": "execute_shot",
                "description": "Aims the club and strikes the golf ball.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "aim_position": {
                            "type": "integer",
                            "description": "Lateral position to aim. -100 is far left, 0 is center, 100 is far right."
                        },
                        "strike_force": {
                            "type": "integer",
                            "description": "The force of the shot, from 1 (light tap) to 100 (full power)."
                        },
                        "commentary": {
                            "type": "string",
                            "description": "A brief, witty, or analytical comment about the planned shot."
                        }
                    },
                    "required": ["aim_position", "strike_force", "commentary"]
                }
            }
        }
    ]
    return tools


def get_llm_decision(game_state_prompt: str):
    """Sends the current game state to the LLM and gets its decision."""
    # 2. ADD THE TYPE HINT TO YOUR MESSAGES LIST
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are a professional and slightly witty miniature golf player. Your goal is to get the ball in the hole. The hole is at position 0. You will be given the ball's current position and must decide on the aim and force for the next shot. Call the execute_shot function to take your turn."
        },
        {
            "role": "user",
            "content": game_state_prompt
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=get_available_tools(),
        tool_choice="auto"
    )

    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call.type == "function" and tool_call.function.name == "execute_shot":
            arguments = json.loads(tool_call.function.arguments)
            return {
                "aim": arguments.get("aim_position"),
                "force": arguments.get("strike_force"),
                "commentary": arguments.get("commentary")
            }
    return None