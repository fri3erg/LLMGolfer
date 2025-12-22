import time
import os
import gpiod
import cv2
import numpy as np
from picamera2 import Picamera2

# master configuration

# Stepper Motor & Limit Switch
STEP_PIN = 20
DIR_PIN = 21
LIMIT_SWITCH_PIN = 26
GPIO_CHIP = "gpiochip4"
TOTAL_STEPS_FOR_180_DEGREES = 300
HOMING_SPEED = 0.002
MOVE_SPEED = 0.001

# Servo Motor (The "Shooter")
SERVO_PWM_CHIP = 0
SERVO_PWM_CHANNEL = 0
SERVO_PWM_FREQ = 50
SERVO_REST_POS_NS = 700 * 1000
SERVO_MAX_SWING_NS = 2300 * 1000

# Linear Actuator
ACTUATOR_IN1_PIN = 17
ACTUATOR_IN2_PIN = 27
ACTUATOR_PWM_CHIP = 0
ACTUATOR_PWM_CHANNEL = 1
ACTUATOR_PWM_FREQ = 1000

# Stepper Directions
CLOCKWISE = 1
COUNTER_CLOCKWISE = 0

# Computer Vision
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
LOWER_WHITE = np.array([0, 0, 180])
UPPER_WHITE = np.array([179, 40, 255])
MIN_BALL_AREA = 500

# Shot Power (No longer user input)
SHOT_POWER = 80  # Power percentage (0-100)

# Global variables & handles
gpiod_chip = None
step_line, dir_line, limit_switch_line = None, None, None
actuator_in1_line, actuator_in2_line = None, None
current_stepper_position = 0


# Low-level hardware functions (PWM & GPIO)
def pwm_export(chip, channel):
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/export", "w") as f:
            f.write(str(channel))
    except (IOError, FileNotFoundError):
        print(f"PWM channel {channel} on chip {chip} may already be exported.")


def pwm_unexport(chip, channel):
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/unexport", "w") as f:
            f.write(str(channel))
    except (IOError, FileNotFoundError):
        pass


def pwm_set_period(chip, channel, freq):
    period_ns = int(1_000_000_000 / freq)
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/period", "w") as f:
        f.write(str(period_ns))


def pwm_set_duty_cycle(chip, channel, duty_cycle_ns):
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/duty_cycle", "w") as f:
        f.write(str(duty_cycle_ns))


def pwm_enable(chip, channel):
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/enable", "w") as f:
        f.write("1")


def pwm_disable(chip, channel):
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/enable", "w") as f:
            f.write("0")
    except (IOError, FileNotFoundError):
        pass


# Setup & Cleanup


def setup_all():
    global gpiod_chip, step_line, dir_line, limit_switch_line, actuator_in1_line, actuator_in2_line
    print("Setting up all hardware...")
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

    pwm_export(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
    pwm_export(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
    time.sleep(0.2)

    pwm_set_period(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_PWM_FREQ)
    pwm_enable(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)

    pwm_set_period(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, ACTUATOR_PWM_FREQ)
    pwm_enable(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
    print("Hardware setup complete.")


def cleanup_all():
    print("Cleaning up all hardware...")
    try:
        actuator_in1_line.set_value(0)
        actuator_in2_line.set_value(0)
        pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, 0)
        pwm_disable(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
        pwm_unexport(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
        pwm_disable(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
        pwm_unexport(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
        if gpiod_chip:
            gpiod_chip.close()
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")
    finally:
        print("Cleanup complete.")


# High-level action functions
def find_ball_x_coordinate():
    """
    Initializes the camera, finds the golf ball, and returns its X coordinate.
    Returns None if the ball is not found.
    """
    print("Initializing camera to find the ball...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(1)  # Allow camera to adjust to light

    frame = picam2.capture_array()
    picam2.stop()  # Release the camera

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, LOWER_WHITE, UPPER_WHITE)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        ball_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(ball_contour) > MIN_BALL_AREA:
            M = cv2.moments(ball_contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                print(f"Ball found at X coordinate: {cX}")
                return cX

    print("Ball not found!")
    return None


def home_stepper():
    """
    Homes the stepper, then backs off slightly to release the switch.
    """
    global current_stepper_position
    print("Homing stepper motor...")
    dir_line.set_value(COUNTER_CLOCKWISE)
    # Move until the switch is pressed
    while limit_switch_line.get_value() == 0:
        step_line.set_value(1)
        time.sleep(HOMING_SPEED)
        step_line.set_value(0)
        time.sleep(HOMING_SPEED)

    print("Limit switch triggered.")

    # Back off the switch a few steps to release it
    time.sleep(0.1)
    move_stepper(steps=10, direction=CLOCKWISE, speed=HOMING_SPEED)

    current_stepper_position = 0  # Define this point as the true zero
    print("Stepper homed. Position is now 0.")


def move_stepper(steps, direction, speed):
    dir_line.set_value(direction)
    for _ in range(steps):
        step_line.set_value(1)
        time.sleep(speed)
        step_line.set_value(0)
        time.sleep(speed)


def map_angle_to_steps_non_linear(angle):
    """
    Maps an angle (0-180) to a step position (0-300) using a fractional exponent
    for fine-tuned control.
    """
    exponent = 1.5

    # 1. Normalize angle from [0, 180] to [-1, 1].
    normalized_input = (angle / 90.0) - 1.0

    # 2. Apply the easing function, preserving the sign.
    sign = np.sign(normalized_input)
    eased_output = sign * (abs(normalized_input) ** exponent)

    # 3. De-normalize the output from [-1, 1] back to the step range [0, 300].
    target_steps = (eased_output + 1.0) / 2.0 * TOTAL_STEPS_FOR_180_DEGREES

    return int(TOTAL_STEPS_FOR_180_DEGREES - target_steps)


def swing_servo(power):
    print(f"--- Performing servo swing with {power}% power ---")
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_REST_POS_NS)
    time.sleep(1)
    swing_range_ns = SERVO_MAX_SWING_NS - SERVO_REST_POS_NS
    swing_endpoint_ns = int((power / 100.0) * swing_range_ns) + SERVO_REST_POS_NS
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, swing_endpoint_ns)
    time.sleep(0.5)
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_REST_POS_NS)
    time.sleep(1)
    print("Servo swing complete.")


def cycle_actuator(extend_time, retract_time):
    print("--- Cycling the linear actuator ---")
    actuator_in1_line.set_value(1)
    actuator_in2_line.set_value(0)
    actuator_period_ns = int(1_000_000_000 / ACTUATOR_PWM_FREQ)
    pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, actuator_period_ns)
    print(f"Extending for {extend_time}s...")
    time.sleep(extend_time)
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(1)
    print(f"Retracting for {retract_time}s...")
    time.sleep(retract_time)
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(0)
    pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, 0)
    print("Actuator cycle complete.")


# Move stepper to a target step position (0-300)
def move_to_steps(target_steps):
    global current_stepper_position
    if not 0 <= target_steps <= TOTAL_STEPS_FOR_180_DEGREES:
        print(f"Error: Target steps {target_steps} is out of range.")
        return

    steps_to_move = target_steps - current_stepper_position

    print(f"Moving to step: {target_steps}...")

    if steps_to_move > 0:
        move_stepper(steps_to_move, CLOCKWISE, MOVE_SPEED)
    elif steps_to_move < 0:
        move_stepper(abs(steps_to_move), COUNTER_CLOCKWISE, MOVE_SPEED)
    else:
        print("Motor is already at the target position.")

    current_stepper_position = target_steps
    print(f"Move complete. Current position: {current_stepper_position} steps.")


# Main program sequence
if __name__ == "__main__":
    try:
        setup_all()
        print("\nVISION GOLF MACHINE INITIALIZED\n")

        home_stepper()
        time.sleep(1)

        ball_x = find_ball_x_coordinate()

        if ball_x is not None:
            # 1. Convert pixel X to a 0-180 degree conceptual angle
            target_angle = (ball_x / CAMERA_WIDTH) * 180.0

            # 2. Convert the angle to steps using our new non-linear function
            target_steps = map_angle_to_steps_non_linear(target_angle)

            print(
                f"Ball X: {ball_x} -> Angle: {target_angle:.1f}° -> Non-Linear Steps: {target_steps}"
            )

            # 3. Move to the calculated step position
            move_to_steps(target_steps)

            time.sleep(0.5)
            swing_servo(SHOT_POWER)
            time.sleep(1)
            cycle_actuator(extend_time=2, retract_time=2)
        else:
            print("\nCould not find the ball. Halting operation.")

        print("\nSEQUENCE COMPLETE\n")

    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
    finally:
        cleanup_all()
