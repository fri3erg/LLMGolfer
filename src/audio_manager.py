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
        # Hardcoded for Raspberry Pi (absolute path to avoid service/root user issues)
        # Using /home/frigo directly instead of ~
        data_dir = os.path.join('/home/frigo', '.local', 'share', 'piper')
        
        voice_model = "en_US-lessac-medium"
        model_path = os.path.join(data_dir, f"{voice_model}.onnx")
        
        # Check if voice model exists
        if not os.path.exists(model_path):
            with open("/home/frigo/audio_debug.log", "a") as f:
                f.write(f"ERROR: Voice model not found at {model_path}\n")
            raise FileNotFoundError(f"Voice model not found: {model_path}")
        
        # Use Piper with full path to model
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Use sys.executable to ensure we use the same python interpreter (venv)
        # PATH issues might prevent finding 'python' otherwise
        piper_cmd = [sys.executable, "-m", "piper", "--model", model_path, "--output-file", tmp_path]
        
        subprocess.run(
            piper_cmd,
            input=text.encode(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        
        # Play using hardcoded USB device
        # Use plughw:2,0 as found in logs
        device = "plughw:2,0"
        
        # Use absolute path for aplay
        aplay_path = "/usr/bin/aplay"
        if not os.path.exists(aplay_path):
             aplay_path = "aplay" # Fallback if not at standard location
        
        cmd = [aplay_path, "-D", device, tmp_path]
        print(f"Using audio device: {device}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
             with open("/home/frigo/audio_debug.log", "a") as f:
                f.write(f"APLAY ERROR: {result.stderr}\n")
        
        os.unlink(tmp_path)
        return
        
    except Exception as e:
        with open("/home/frigo/audio_debug.log", "a") as f:
            f.write(f"PIPER EXCEPTION: {e}\n")
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

