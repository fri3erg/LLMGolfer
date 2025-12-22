import subprocess
import shutil
import os
import sys


def play_speech(text: str):
    """
    Uses Piper TTS for high-quality neural text-to-speech.
    Falls back to espeak if Piper is not available.
    """
    if not text:
        return

    print(f"Playing audio: '{text}'")
    
    # Try Piper TTS first (better quality)
    try:
        # Determine voice model path
        if sys.platform == 'win32':
            data_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'piper')
        else:
            data_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'piper')
        
        voice_model = "en_US-lessac-medium"
        model_path = os.path.join(data_dir, f"{voice_model}.onnx")
        
        # Check if voice model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Voice model not found: {model_path}")
        
        # Use Piper with full path to model
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        
        subprocess.run(
            ["python", "-m", "piper", "--model", model_path, "--output-file", tmp_path],
            input=text.encode(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        
        # Play using system default
        if os.name == 'nt':  # Windows
            import winsound
            winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
        elif shutil.which("aplay"):  # Linux
            subprocess.run(["aplay", tmp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        os.unlink(tmp_path)
        return
        
    except Exception as e:
        print(f"Piper TTS not available ({e}), falling back to espeak")
    
    # Fallback to espeak
    try:
        subprocess.Popen(["espeak", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Audio Error (espeak): {e}")



if __name__ == "__main__":

    print("Testing audio manager...")

    play_speech("Hello, world! I am the Golfer.")

    play_speech("This is a test of the commentary system.")

