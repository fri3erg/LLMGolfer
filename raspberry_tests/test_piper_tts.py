"""
Piper TTS Test Script
Tests different phrases with Piper TTS before deploying to Raspberry Pi
"""

import subprocess
import tempfile
import os
import time
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def play_speech_piper(text: str, voice_model="en_US-lessac-medium"):
    """Play speech using Piper TTS"""
    if not text:
        return
    
    print(f"\n[SPEAK] '{text}'")
    
    try:
        # Determine voice model path
        if sys.platform == 'win32':
            data_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'piper')
        else:
            data_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'piper')
        
        model_path = os.path.join(data_dir, f"{voice_model}.onnx")
        
        if not os.path.exists(model_path):
            print(f"   [ERROR] Voice model not found at: {model_path}")
            return
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        
        print(f"   Using model: {model_path}")
        result = subprocess.run(
            ["python", "-m", "piper", "--model", model_path, "--output-file", tmp_path],
            input=text.encode(),
            capture_output=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode()
            print(f"   [WARNING] Piper error: {error_msg}")
            return
        
        # Play the audio file on Windows
        if os.name == 'nt':
            import winsound
            winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
        else:
            # On Linux/Mac, use aplay or afplay
            import shutil
            if shutil.which("aplay"):
                # Simple USB detection
                device_arg = []
                try:
                    out = subprocess.run(["aplay", "-l"], capture_output=True, text=True).stdout
                    for line in out.splitlines():
                        if "USB" in line and "card" in line:
                            # Format: card 2: ...
                            card = line.split(":")[0].split()[1]
                            device_arg = ["-D", f"plughw:{card},0"]
                            print(f"   [INFO] Detected USB Audio at card {card}")
                            break
                except:
                    pass
                
                subprocess.run(["aplay"] + device_arg + [tmp_path])
            elif shutil.which("afplay"):
                subprocess.run(["afplay", tmp_path])
        
        # Clean up
        time.sleep(0.5)
        os.unlink(tmp_path)
        print("DONE")
        
    except subprocess.TimeoutExpired:
        print("Piper TTS timed out")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Test Piper TTS with golf-related phrases"""
    
    print("=" * 60)
    print("PIPER TTS TEST - Golfer Commentary System")
    print("=" * 60)
    
    # Test phrases
    test_phrases = [
        "Hello! I am the Golfer.",
        "Let's aim for the center and give it a gentle tap.",
        "Perfect shot! Right in the hole!",
        "Fore! Watch out!",
        "Hole in one! What a magnificent shot!",
    ]
    
    print(f"\n[TEST] Testing with {len(test_phrases)} phrases...")
    print("Press Ctrl+C to exit\n")
    
    for i, phrase in enumerate(test_phrases, 1):
        try:
            print(f"\n[{i}/{len(test_phrases)}]")
            play_speech_piper(phrase, "en_US-lessac-medium")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[EXIT] Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
