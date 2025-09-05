import time
import os
import gpiod

# --- PWM Configuration (for Speed Control on ENA) ---
PWM_CHIP = 0
PWM_CHANNEL = 1      # GPIO 13 is Channel 1
PWM_FREQUENCY = 1000 # A good frequency for DC motors
PWM_BASE_PATH = f"/sys/class/pwm/pwmchip{PWM_CHIP}/"

# --- GPIO Configuration (for Direction Control on IN1/IN2) ---
IN1_PIN = 17
IN2_PIN = 27
GPIO_CHIP = 'gpiochip4'

# --- Global Handles ---
in1_line = None
in2_line = None
gpiod_chip = None

# --- PWM Helper Functions ---
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

# --- Actuator Specific Functions ---
def setup_gpio_direction():
    """Initializes IN1 and IN2 pins as outputs using gpiod."""
    global in1_line, in2_line, gpiod_chip
    gpiod_chip = gpiod.Chip(GPIO_CHIP)
    in1_line = gpiod_chip.get_line(IN1_PIN)
    in2_line = gpiod_chip.get_line(IN2_PIN)
    in1_line.request(consumer="actuator_in1", type=gpiod.LINE_REQ_DIR_OUT)
    in2_line.request(consumer="actuator_in2", type=gpiod.LINE_REQ_DIR_OUT)

def move_actuator(speed, direction):
    """Moves the linear actuator."""
    # Set direction
    if direction == "extend":
        in1_line.set_value(1)
        in2_line.set_value(0)
    elif direction == "retract":
        in1_line.set_value(0)
        in2_line.set_value(1)
    else:
        return

    # Set speed
    period_ns = int(1_000_000_000 / PWM_FREQUENCY)
    duty_ns = int(period_ns * (speed / 100.0))
    pwm_set_duty_cycle(duty_ns)
    print(f"Moving actuator: direction='{direction}', speed={speed}%")

def stop_actuator():
    """Stops the actuator."""
    if in1_line and in2_line:
        in1_line.set_value(0)
        in2_line.set_value(0)
    pwm_set_duty_cycle(0)
    print("Actuator stopped.")

# --- Main Actuator Program ---
if __name__ == "__main__":
    try:
        # Setup both PWM and GPIO pins
        print("Setting up actuator controls...")
        setup_gpio_direction()
        pwm_export()
        time.sleep(0.2) # Give system a moment to create files
        pwm_set_period(PWM_FREQUENCY)
        pwm_enable()
        
        # --- Test Sequence ---
        print("\n--- Starting Actuator Test ---")

        # Extend at 75% speed for 2 seconds
        move_actuator(speed=75, direction="extend")
        time.sleep(2)

        # Stop for 1 second
        stop_actuator()
        time.sleep(1)

        # Retract at full speed for 2 seconds
        move_actuator(speed=100, direction="retract")
        time.sleep(2)

        stop_actuator()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up...")
        # Ensure cleanup happens in a safe order
        try:
            stop_actuator()
            pwm_disable()
            pwm_unexport()
            if gpiod_chip:
                gpiod_chip.close()
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")
