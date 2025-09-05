import time
import os

# --- Configuration ---
# We confirmed the PWM controller is pwmchip0 on your Pi 5.
PWM_CHIP = 0
PWM_CHANNEL = 0
PWM_FREQUENCY = 50 

# Base path for the PWM controller
PWM_BASE_PATH = f"/sys/class/pwm/pwmchip{PWM_CHIP}/"

# Servo pulse widths in nanoseconds (e.g., 700µs = 700,000ns)
REST_POS_NS = 700 * 1000
TOP_OF_SWING_NS = 2300 * 1000

# --- Helper Functions (These are the same as your working LED code) ---
def pwm_export():
    """Makes the PWM channel available for use."""
    try:
        with open(os.path.join(PWM_BASE_PATH, "export"), "w") as f:
            f.write(str(PWM_CHANNEL))
    except (IOError, FileNotFoundError):
        print(f"PWM channel {PWM_CHANNEL} may already be exported.")

def pwm_unexport():
    """Releases the PWM channel."""
    try:
        with open(os.path.join(PWM_BASE_PATH, "unexport"), "w") as f:
            f.write(str(PWM_CHANNEL))
    except (IOError, FileNotFoundError):
        print("Could not unexport PWM channel.")

def pwm_set_period(freq):
    """Sets the PWM frequency."""
    period_ns = int(1_000_000_000 / freq)
    path = os.path.join(PWM_BASE_PATH, f"pwm{PWM_CHANNEL}/period")
    with open(path, "w") as f:
        f.write(str(period_ns))
    return period_ns

def pwm_set_duty_cycle(duty_cycle_ns):
    """Sets the pulse width (ON time)."""
    path = os.path.join(PWM_BASE_PATH, f"pwm{PWM_CHANNEL}/duty_cycle")
    with open(path, "w") as f:
        f.write(str(duty_cycle_ns))

def pwm_enable():
    """Starts the PWM signal."""
    path = os.path.join(PWM_BASE_PATH, f"pwm{PWM_CHANNEL}/enable")
    with open(path, "w") as f:
        f.write("1")

def pwm_disable():
    """Stops the PWM signal."""
    path = os.path.join(PWM_BASE_PATH, f"pwm{PWM_CHANNEL}/enable")
    with open(path, "w") as f:
        f.write("0")

# --- Main Servo Program ---
if __name__ == "__main__":
    # This block is what has changed.
    try:
        print("Setting up PWM for servo...")
        pwm_export()
        time.sleep(0.1) 
        
        pwm_set_period(PWM_FREQUENCY)
        pwm_enable()
        
        # --- Perform a test swing ---
        power = 100 # Set swing power from 0 to 100
        
        print(f"--- Starting servo swing with {power}% power ---")

        # 1. Move to the resting position and wait
        print("Moving to rest position...")
        pwm_set_duty_cycle(REST_POS_NS)
        time.sleep(1.5)

        # 2. Calculate the swing endpoint based on power
        swing_endpoint_ns = int(((power / 100.0) * (TOP_OF_SWING_NS - REST_POS_NS)) + REST_POS_NS)
        
        # 3. Swing to the endpoint
        print(f"Swinging to {swing_endpoint_ns // 1000}µs...")
        pwm_set_duty_cycle(swing_endpoint_ns)
        time.sleep(0.5) # Time for the servo to complete its swing

        # 4. Return to the resting position
        print("Returning to rest...")
        pwm_set_duty_cycle(REST_POS_NS)
        time.sleep(1.5)

        print("Test swing complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up...")
        pwm_disable()
        pwm_unexport()
