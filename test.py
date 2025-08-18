# test_openai.py
import os
from dotenv import load_dotenv
from openai import OpenAI

print("--- Starting OpenAI connection test ---")

try:
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("ASSISTANT_ID")

    if not api_key or not assistant_id:
        raise ValueError("API key or Assistant ID not found in .env file.")

    print("Initializing OpenAI client...")
    client = OpenAI(api_key=api_key)

    # The exact line that Pylance dislikes
    print("Attempting to retrieve assistant...")
    assistant = client.assistants.retrieve(assistant_id) 
    
    print("\n✅ SUCCESS! ✅")
    print(f"Successfully retrieved Assistant '{assistant.name}' (ID: {assistant.id})")
    print("\nThis proves your OpenAI library and environment are working correctly.")
    print("The error you see in VS Code is a Pylance static analysis issue, not a runtime error.")

except Exception as e:
    print(f"\n❌ FAILED! ❌")
    print(f"A runtime error occurred: {e}")