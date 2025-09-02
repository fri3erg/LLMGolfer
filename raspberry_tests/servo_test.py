import lgpio
import time

# --- Configuration ---
SERVO_PIN = 12  # GPIO 12 (Hardware PWM Channel 0)
PWM_FREQUENCY = 50  # Standard frequency for servos is 50 Hz

# Pulse widths in microseconds (µs). Adjust these to match your servo's range.
# 500 µs is typically 0 degrees, 2500 µs is 180 degrees.
MIN_PULSE = 500
MAX_PULSE = 2500

# Swing positions (as pulse widths).
# 'REST' is the starting position of the club.
# 'TOP_OF_SWING' is the furthest back it will go.
REST_POS = 700
TOP_OF_SWING = 2300

# --- Global Handle ---
h = None

def setup_servo():
    """Initialize the GPIO for PWM servo control."""
    global h
    try:
        h = lgpio.gpiochip_open(0)  # Open the default GPIO chip
        print("GPIO chip opened successfully.")
    except Exception as e:
        print(f"Error opening GPIO chip: {e}")
        exit()

def map_value(value, from_low, from_high, to_low, to_high):
    """Maps a value from one range to another."""
    return (value - from_low) * (to_high - to_low) / (from_high - from_low) + to_low

def swing_club(power=100):
    """
    Swings the golf club.
    
    Args:
        power (int): A value from 0 to 100. This determines the range of the swing.
                     0 means no swing, 100 means a full swing.
    """
    if not (0 <= power <= 100):
        print("Power must be between 0 and 100.")
        return

    if not h:
        print("Servo not set up. Call setup_servo() first.")
        return
        
    print(f"--- Swinging with {power}% power ---")
    
    # 1. Go to the resting position
    lgpio.tx_pwm(h, SERVO_PIN, PWM_FREQUENCY, REST_POS)
    print("At rest...")
    time.sleep(1)

    # 2. Calculate the swing endpoint based on power
    # Map the 0-100 power to a point between REST and TOP_OF_SWING
    swing_endpoint = int(map_value(power, 0, 100, REST_POS, TOP_OF_SWING))
    
    # 3. Perform the swing (move quickly to the endpoint)
    print(f"Swinging to pulse width: {swing_endpoint}")
    lgpio.tx_pwm(h, SERVO_PIN, PWM_FREQUENCY, swing_endpoint)
    time.sleep(0.3) # The duration of the swing itself

    # 4. Return to rest
    print("Returning to rest...")
    lgpio.tx_pwm(h, SERVO_PIN, PWM_FREQUENCY, REST_POS)
    time.sleep(1)

def cleanup():
    """Stop PWM and release GPIO resources."""
    if h:
        try:
            # Set duty cycle to 0 to stop the servo pulse
            lgpio.tx_pwm(h, SERVO_PIN, PWM_FREQUENCY, 0)
            lgpio.gpiochip_close(h)
            print("GPIO cleaned up.")
        except Exception as e:
            print(f"Error during cleanup: {e}")

# --- Main Program ---
if __name__ == "__main__":
    try:
        setup_servo()
        while True:
            # Demonstrate a few swings with different power levels
            swing_club(power=50)  # A half-power swing
            time.sleep(1)
            
            swing_club(power=100) # A full-power swing
            time.sleep(1)
            
            swing_club(power=10) # A very gentle tap
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        cleanup()