# audio_manager.py
import pyttsx3

# Initialize the text-to-speech engine once when the module is loaded
try:
    engine = pyttsx3.init()
    # You can adjust properties if you want
    # engine.setProperty('rate', 150) # Speed of speech
    # engine.setProperty('volume', 0.9) # Volume (0.0 to 1.0)
except Exception as e:
    print(f"Failed to initialize TTS engine: {e}")
    engine = None

def play_speech(text: str):
    """
    Converts the given text to speech and plays it.
    """
    if engine and text:
        print(f"🔊 Playing audio: '{text}'")
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Could not play speech: {e}")
    elif not text:
        print("No text provided to play.")
    else:
        print("TTS engine not available. Cannot play speech.")

# You could add a test here to run when you execute this file directly
if __name__ == "__main__":
    print("Testing audio manager...")
    play_speech("Hello, world! I am the LLM Golfer.")
    play_speech("This is a test of the commentary system.")