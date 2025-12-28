import time
try:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
    import hardware_controller as hc
except ImportError:
    print("Error: Could not import hardware_controller. Make sure you are running from the project root or raspberry_tests folder.")
    exit(1)


def test_swing_levels():
    print("Initializing Hardware...")
    try:
        hc.setup_all()
    except Exception as e:
        print(f"Setup failed (are you on the Pi?): {e}")
        # Proceeding might fail if not on Pi, but this is a test script
    
    print("\n--- Testing Swing Power Levels ---")
    
    levels = [30, 60, 90, 100]
    
    for power in levels:
        print(f"\nTesting Power: {power}%")
        print("You should see: " + ("Slower speed" if power <= 80 else "MAX speed"))
        hc.swing_club(power)
        time.sleep(1)

    print("\nTest Complete.")
    hc.cleanup_all()

if __name__ == "__main__":
    try:
        test_swing_levels()
    except KeyboardInterrupt:
        hc.cleanup_all()
        print("\nInterrupted.")
