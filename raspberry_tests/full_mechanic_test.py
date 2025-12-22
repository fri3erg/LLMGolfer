import time
import os
import gpiod

# MASTER CONFIGURATION

# Stepper Motor & Limit Switch
STEP_PIN = 20
DIR_PIN = 21
LIMIT_SWITCH_PIN = 26
GPIO_CHIP = "gpiochip4"
TOTAL_STEPS_FOR_180_DEGREES = 350  # stepper motor steps for 180 degrees
HOMING_SPEED = 0.001  # Speed for finding the home position
MOVE_SPEED = 0.001  # Speed for moving to a target angle

# Servo Motor (The "Shooter")
SERVO_PWM_CHIP = 0
SERVO_PWM_CHANNEL = 0  # Mapped to GPIO 12
SERVO_PWM_FREQ = 50  # Standard frequency for servos
SERVO_REST_POS_NS = 700 * 1000  # 700µs pulse width for the resting position
SERVO_MAX_SWING_NS = 2300 * 1000  # 2300µs pulse width for the top of the swing

# Linear Actuator
ACTUATOR_IN1_PIN = 17
ACTUATOR_IN2_PIN = 27
ACTUATOR_PWM_CHIP = 0
ACTUATOR_PWM_CHANNEL = 1  # Mapped to GPIO 13
ACTUATOR_PWM_FREQ = 1000  # A common frequency for DC motor PWM

# Stepper Directions
CLOCKWISE = 1
COUNTER_CLOCKWISE = 0


# Global variables & handles

gpiod_chip = None

# Stepper
step_line = None
dir_line = None
limit_switch_line = None
current_stepper_position = 0  # Tracks position in steps from home

# Actuator
actuator_in1_line = None
actuator_in2_line = None


# Low-level functions
def pwm_export(chip, channel):
    """Makes a PWM channel available for use via the sysfs interface."""
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/export", "w") as f:
            f.write(str(channel))
    except (IOError, FileNotFoundError):
        print(f"PWM channel {channel} on chip {chip} may already be exported.")


def pwm_unexport(chip, channel):
    """Releases a PWM channel via the sysfs interface."""
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/unexport", "w") as f:
            f.write(str(channel))
    except (IOError, FileNotFoundError):
        pass  # Fail silently on cleanup


def pwm_set_period(chip, channel, freq):
    """Sets the PWM signal's period based on the desired frequency."""
    period_ns = int(1_000_000_000 / freq)
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/period", "w") as f:
        f.write(str(period_ns))


def pwm_set_duty_cycle(chip, channel, duty_cycle_ns):
    """Sets the PWM signal's active time (pulse width) in nanoseconds."""
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/duty_cycle", "w") as f:
        f.write(str(duty_cycle_ns))


def pwm_enable(chip, channel):
    """Enables the PWM signal output."""
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/enable", "w") as f:
        f.write("1")


def pwm_disable(chip, channel):
    """Disables the PWM signal output."""
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/enable", "w") as f:
            f.write("0")
    except (IOError, FileNotFoundError):
        pass  # Fail silently on cleanup


def setup_all():
    """Initializes all GPIO and PWM hardware for the project."""
    global gpiod_chip, step_line, dir_line, limit_switch_line, actuator_in1_line, actuator_in2_line
    print("Setting up all hardware...")

    # gpiod Setup (Stepper, Limit Switch, Actuator Direction)
    gpiod_chip = gpiod.Chip(GPIO_CHIP)
    step_line = gpiod_chip.get_line(STEP_PIN)
    dir_line = gpiod_chip.get_line(DIR_PIN)
    limit_switch_line = gpiod_chip.get_line(LIMIT_SWITCH_PIN)
    actuator_in1_line = gpiod_chip.get_line(ACTUATOR_IN1_PIN)
    actuator_in2_line = gpiod_chip.get_line(ACTUATOR_IN2_PIN)

    step_line.request(consumer="stepper_step", type=gpiod.LINE_REQ_DIR_OUT)
    dir_line.request(consumer="stepper_dir", type=gpiod.LINE_REQ_DIR_OUT)
    limit_switch_line.request(
        consumer="limit_switch",
        type=gpiod.LINE_REQ_DIR_IN,
        flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP,
    )
    actuator_in1_line.request(consumer="actuator_in1", type=gpiod.LINE_REQ_DIR_OUT)
    actuator_in2_line.request(consumer="actuator_in2", type=gpiod.LINE_REQ_DIR_OUT)

    # PWM Setup (Servo and Actuator Speed)
    pwm_export(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
    pwm_export(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
    time.sleep(0.2)  # Give sysfs time to create files

    pwm_set_period(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_PWM_FREQ)
    pwm_enable(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)

    pwm_set_period(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, ACTUATOR_PWM_FREQ)
    pwm_enable(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)

    print("Hardware setup complete.")


def cleanup_all():
    """Gracefully disables and releases all hardware resources."""
    print("Cleaning up all hardware...")
    try:
        # Stop actuator
        actuator_in1_line.set_value(0)
        actuator_in2_line.set_value(0)
        pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, 0)

        # Disable and unexport PWM channels
        pwm_disable(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
        pwm_unexport(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
        pwm_disable(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
        pwm_unexport(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)

        # Release gpiod lines
        if gpiod_chip:
            gpiod_chip.close()
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")
    finally:
        print("Cleanup complete.")


# =============================================================================
# --- HIGH-LEVEL ACTION FUNCTIONS ---
# =============================================================================


def home_stepper():
    """
    Homes the stepper motor by moving it counter-clockwise until the limit
    switch is triggered. Resets the current position to 0.
    """
    global current_stepper_position
    print("Homing stepper motor to establish zero position...")
    dir_line.set_value(COUNTER_CLOCKWISE)
    while limit_switch_line.get_value() == 0:
        step_line.set_value(1)
        time.sleep(HOMING_SPEED)
        step_line.set_value(0)
        time.sleep(HOMING_SPEED)
    current_stepper_position = 0
    print("Stepper homed. Position is now 0.")


def move_stepper(steps, direction, speed):
    """
    Moves the stepper motor a specific number of steps in a given direction.

    Args:
        steps (int): The number of steps to move.
        direction (int): The direction to move (CLOCKWISE or COUNTER_CLOCKWISE).
        speed (float): The delay between step pulses, controlling speed.
    """
    dir_line.set_value(direction)
    for step in range(steps):
        print(step)
        step_line.set_value(1)
        time.sleep(speed)
        step_line.set_value(0)
        time.sleep(speed)


def move_to_angle(angle):
    """
    Moves the stepper motor to a target position based on an angle (0-180).

    Args:
        angle (float): The target angle, where 0 is the home position.
    """
    global current_stepper_position
    if not 0 <= angle <= 180:
        print("Error: Angle must be between 0 and 180.")
        return

    # Calculate the target step based on the angle and total travel range
    target_steps = int((angle / 180.0) * TOTAL_STEPS_FOR_180_DEGREES)
    steps_to_move = target_steps - current_stepper_position

    print(f"Moving to angle: {angle}° (target step: {target_steps})...")

    if steps_to_move > 0:
        move_stepper(steps_to_move, CLOCKWISE, MOVE_SPEED)
    elif steps_to_move < 0:
        move_stepper(abs(steps_to_move), COUNTER_CLOCKWISE, MOVE_SPEED)
    else:
        # Add this block for better feedback
        print("Motor is already at the target angle. No move needed.")

    current_stepper_position = target_steps
    print(f"Move complete. Current position: {current_stepper_position} steps.")


def swing_servo(power):
    """
    Performs a single "shot" with the servo motor.

    Args:
        power (int): The swing power, from 0 to 100.
    """
    if not 0 <= power <= 100:
        print("Error: Power must be between 0 and 100.")
        return

    print(f"Performing servo swing with {power}% power")

    # Go to rest position first
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_REST_POS_NS)
    time.sleep(1)

    # Calculate the swing endpoint based on power
    swing_range_ns = SERVO_MAX_SWING_NS - SERVO_REST_POS_NS
    swing_endpoint_ns = int((power / 100.0) * swing_range_ns) + SERVO_REST_POS_NS

    # Swing to the endpoint
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, swing_endpoint_ns)
    time.sleep(0.5)

    # Return to rest
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_REST_POS_NS)
    time.sleep(1)
    print("Servo swing complete.")


def cycle_actuator(extend_time, retract_time):
    """
    Extends the linear actuator at 100% speed, then retracts it.

    Args:
        extend_time (float): The number of seconds to extend.
        retract_time (float): The number of seconds to retract.
    """
    print("--- Cycling the linear actuator ---")

    # Extend
    actuator_in1_line.set_value(1)
    actuator_in2_line.set_value(0)
    actuator_period_ns = int(1_000_000_000 / ACTUATOR_PWM_FREQ)
    pwm_set_duty_cycle(
        ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, actuator_period_ns
    )  # 100% duty
    print(f"Extending for {extend_time}s...")
    time.sleep(extend_time)

    # Retract
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(1)
    print(f"Retracting for {retract_time}s...")
    time.sleep(retract_time)

    # Stop
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(0)
    pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, 0)
    print("Actuator cycle complete.")


# Main Program Loop
if __name__ == "__main__":
    try:
        setup_all()

        print("\nGOLF MACHINE INITIALIZED\n")

        # 1. Home the stepper to establish the zero point. This runs only once.
        home_stepper()

        # 2. Enter the main interactive loop.
        while True:
            print("\nNew Shot Setup\n")

            # Get user input for angle
            angle_input = input("Enter target angle (0-180), or 'q' to quit: ")
            if angle_input.lower() == "q":
                break

            # Get user input for power
            power_input = input("Enter swing power (0-100): ")

            try:
                target_angle = float(angle_input)
                swing_power = int(power_input)

                move_to_angle(target_angle)
                time.sleep(0.5)

                swing_servo(swing_power)
                time.sleep(1)

                cycle_actuator(extend_time=10, retract_time=10)

            except ValueError:
                print("Invalid input. Please enter numbers for angle and power.")

        print("\nGOLF MACHINE SHUTTING DOWN\n")

    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
    finally:
        cleanup_all()
