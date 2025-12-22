import time

import sys

import numpy as np

import os

import gpiod

# Stepper Motor


GPIO_CHIP_PATH = "/dev/gpiochip4"


STEP_PIN = 20

DIR_PIN = 21

LIMIT_SWITCH_PIN = 4

ENABLE_PIN = 22

# Stepper calibration: steps required for 180 degree rotation
TOTAL_STEPS_FOR_180_DEGREES = 300


# Speeds

HOMING_SPEED = 0.002

MOVE_SPEED = 0.001


# Servo Motor
# Pulse widths in nanoseconds (1ms = 1,000,000ns)
# Standard servo range: 1-2ms

SERVO_PWM_CHIP = 0

SERVO_PWM_CHANNEL = 3  # GPIO 19

SERVO_PWM_FREQ = 50

SERVO_REST_POS_NS = 1500 * 1000  # Middle/neutral position
SERVO_MAX_SWING_NS = 800 * 1000  # Full backswing (servo mounted upside down)
SERVO_FORWARD_SWING_NS = 2500 * 1000  # Full forward swing


# Linear Actuator

ACTUATOR_PWM_CHIP = 0

ACTUATOR_PWM_CHANNEL = 2  # GPIO 18

ACTUATOR_PWM_FREQ = 1000


# Directions

CLOCKWISE = 1

COUNTER_CLOCKWISE = 0


# Handles

gpiod_chip = None

step_line, dir_line, limit_switch_line, enable_line = None, None, None, None

current_stepper_position = 0


# Low Level Functions


def pwm_write(chip, channel, file, value):
    """Safely writes to a PWM file."""

    path = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/{file}"

    try:

        with open(path, "w") as f:

            f.write(str(value))

    except Exception as e:
        # Suppress errors during cleanup
        pass


def pwm_export(chip, channel):
    """Exports a PWM channel and waits for filesystem to initialize."""

    export_path = f"/sys/class/pwm/pwmchip{chip}/export"

    pwm_dir = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}"

    if os.path.exists(pwm_dir):

        return  # Already exported

    try:

        with open(export_path, "w") as f:

            f.write(str(channel))

    except (IOError, OSError):

        # Device likely busy or already exported

        pass

    # Wait for OS to create the PWM files
    for _ in range(10):

        if os.path.exists(pwm_dir):
            return

        time.sleep(0.1)

    print(f"PWM Export warning: {pwm_dir} did not appear quickly.")


def pwm_unexport(chip, channel):

    try:

        with open(f"/sys/class/pwm/pwmchip{chip}/unexport", "w") as f:

            f.write(str(channel))

    except:
        pass


def setup_all():

    global gpiod_chip, step_line, dir_line, limit_switch_line, enable_line

    print("Attempting to open GPIO chip...")

    # Try the configured path first

    target_chip = GPIO_CHIP_PATH

    if not os.path.exists(target_chip):

        print("Warning: {target_chip} not found. Searching for alternatives...")

        # Fallback strategy: Check 0 to 5

        for i in range(6):

            if os.path.exists(f"/dev/gpiochip{i}"):

                target_chip = f"/dev/gpiochip{i}"

                break

    print(f"Using {target_chip}")

    try:

        gpiod_chip = gpiod.Chip(target_chip)

    except Exception as e:
        print(f"Error: Could not open {target_chip}. {e}")
        raise e

    print("Configuring Lines...")

    try:
        # Configure GPIO lines using gpiod v2 API

        # STEP PIN
        config = {
            STEP_PIN: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE,
            )
        }
        step_line = gpiod_chip.request_lines(consumer="stepper_step", config=config)

        # DIR PIN
        config = {
            DIR_PIN: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE,
            )
        }
        dir_line = gpiod_chip.request_lines(consumer="stepper_dir", config=config)

        # ENABLE PIN
        # Default to 1 (Disable) on start
        config = {
            ENABLE_PIN: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.ACTIVE,
            )
        }
        enable_line = gpiod_chip.request_lines(consumer="stepper_enable", config=config)

        # LIMIT SWITCH
        config = {
            LIMIT_SWITCH_PIN: gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT, bias=gpiod.line.Bias.PULL_UP
            )
        }
        limit_switch_line = gpiod_chip.request_lines(
            consumer="limit_switch", config=config
        )

    except Exception as e:
        print(f"Error: Pin configuration failed. Check pin numbers. {e}")
        raise e

    print("Configuring PWM...")

    # Dynamic PWM Chip Finder for Pi 5 / Pi 4
    global SERVO_PWM_CHIP, ACTUATOR_PWM_CHIP

    found_chip = None
    potential_chips = [0, 2, 1, 3]

    for i in potential_chips:
        path = f"/sys/class/pwm/pwmchip{i}"
        if os.path.exists(path):
            try:
                with open(f"{path}/npwm", "r") as f:
                    npwm = int(f.read().strip())
                if npwm >= 2:
                    found_chip = i
                    print(f"Found PWM Chip {i} with {npwm} channels.")
                    break
            except:
                continue

    if found_chip is not None:
        SERVO_PWM_CHIP = found_chip
        ACTUATOR_PWM_CHIP = found_chip
    else:
        print("PWM Warning: Could not find a suitable PWM chip. Defaulting to 0.")
        SERVO_PWM_CHIP = 0
        ACTUATOR_PWM_CHIP = 0

    for channel in [SERVO_PWM_CHANNEL, ACTUATOR_PWM_CHANNEL]:
        pwm_export(SERVO_PWM_CHIP, channel)

        time.sleep(0.2)  # Extra safety wait

        # Use correct frequency based on which channel this is
        period = int(
            1_000_000_000
            / (SERVO_PWM_FREQ if channel == SERVO_PWM_CHANNEL else ACTUATOR_PWM_FREQ)
        )

        pwm_write(SERVO_PWM_CHIP, channel, "period", period)

        pwm_write(SERVO_PWM_CHIP, channel, "enable", "1")

    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)

    print("Setup complete.")


def cleanup_all():

    print("Cleaning up...")

    try:

        if enable_line:
            enable_line.set_value(
                ENABLE_PIN, gpiod.line.Value.ACTIVE
            )  # Disable (set to 1/Active)

        # Turn off PWM (Suppress errors if they weren't setup)

        pwm_write(SERVO_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "duty_cycle", 0)

        pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)

        time.sleep(0.5)

        pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "enable", "0")

        pwm_write(SERVO_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "enable", "0")

        pwm_unexport(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)

        pwm_unexport(SERVO_PWM_CHIP, ACTUATOR_PWM_CHANNEL)

        if gpiod_chip:
            gpiod_chip.close()

    except Exception as e:

        print(f"Cleanup Warning: {e}")


def enable_motor():
    if enable_line:
        # v2: request.set_value(offset, value)
        enable_line.set_value(ENABLE_PIN, gpiod.line.Value.INACTIVE)  # 0 to Enable
        time.sleep(0.01)


def disable_motor():
    if enable_line:
        enable_line.set_value(ENABLE_PIN, gpiod.line.Value.ACTIVE)  # 1 to Disable


# =============================================================================
# --- MOVEMENT ---
# =============================================================================


def move_stepper_raw(steps, direction):
    # direction is 0 or 1
    val_dir = gpiod.line.Value.ACTIVE if direction == 1 else gpiod.line.Value.INACTIVE
    dir_line.set_value(DIR_PIN, val_dir)

    for _ in range(steps):
        step_line.set_value(STEP_PIN, gpiod.line.Value.ACTIVE)
        time.sleep(MOVE_SPEED)
        step_line.set_value(STEP_PIN, gpiod.line.Value.INACTIVE)
        time.sleep(MOVE_SPEED)


def home_stepper():
    global current_stepper_position
    print("Homing...")
    enable_motor()

    dir_line.set_value(DIR_PIN, gpiod.line.Value.ACTIVE)

    while limit_switch_line.get_value(LIMIT_SWITCH_PIN) == gpiod.line.Value.ACTIVE:
        step_line.set_value(STEP_PIN, gpiod.line.Value.ACTIVE)
        time.sleep(HOMING_SPEED)
        step_line.set_value(STEP_PIN, gpiod.line.Value.INACTIVE)
        time.sleep(HOMING_SPEED)

    time.sleep(0.1)

    dir_line.set_value(DIR_PIN, gpiod.line.Value.INACTIVE)

    for _ in range(10):
        step_line.set_value(STEP_PIN, gpiod.line.Value.ACTIVE)
        time.sleep(HOMING_SPEED)
        step_line.set_value(STEP_PIN, gpiod.line.Value.INACTIVE)
        time.sleep(HOMING_SPEED)

    current_stepper_position = 0

    disable_motor()

    print("Homed.")


def map_angle_to_steps_non_linear(angle):
    # Non-linear mapping: exponent > 1.0 provides finer center control
    exponent = 1.5

    normalized_input = (angle / 90.0) - 1.0

    sign = np.sign(normalized_input)

    eased_output = sign * (abs(normalized_input) ** exponent)

    target_steps = (eased_output + 1.0) / 2.0 * TOTAL_STEPS_FOR_180_DEGREES

    return int(TOTAL_STEPS_FOR_180_DEGREES - target_steps)


def set_stepper_angle(angle):

    global current_stepper_position

    target_step = map_angle_to_steps_non_linear(angle)

    target_step = max(0, min(TOTAL_STEPS_FOR_180_DEGREES, target_step))

    diff = target_step - current_stepper_position

    if diff == 0:
        return

    enable_motor()

    # Determine direction based on position difference
    # Positive diff: move away from limit switch (INACTIVE)
    # Negative diff: move toward limit switch (ACTIVE)
    direction = gpiod.line.Value.INACTIVE if diff > 0 else gpiod.line.Value.ACTIVE

    move_stepper_raw(abs(diff), direction)

    disable_motor()

    current_stepper_position = target_step

    print(f"Stepper: Moved to {angle}° (Step {target_step})")


def swing_club(power_percent):

    print(f"Swinging at {power_percent}%...")

    # Boost power for weaker 5kg servo: scale 0-100% to 50-100% range
    # This ensures even low power swings have enough force
    boosted_power = 50 + (power_percent / 100.0) * 50

    # Start from neutral position
    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)
    time.sleep(0.2)

    # Calculate backswing position based on power
    backswing_range = SERVO_MAX_SWING_NS - SERVO_REST_POS_NS
    backswing_ns = int((boosted_power / 100.0) * backswing_range) + SERVO_REST_POS_NS

    # Move to backswing position
    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", backswing_ns)
    time.sleep(1.0)  # Hold backswing for 1 second

    # Swing through to full forward position (hitting the ball)
    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_FORWARD_SWING_NS)
    time.sleep(1.0)  # Hold forward position

    # Return to neutral/rest
    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)
    time.sleep(0.5)


def reset_ball_actuator():
    print("Resetting ball...")

    ACT_PIN_1 = 17
    ACT_PIN_2 = 27

    try:
        # Request lines for the actuator
        # v2: Request as block
        config = {
            ACT_PIN_1: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE,
            ),
            ACT_PIN_2: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE,
            ),
        }

        act_req = gpiod_chip.request_lines(consumer="actuator", config=config)

        period = int(1_000_000_000 / 1000)
        pwm_write(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "duty_cycle", period)

        # Extend
        act_req.set_value(ACT_PIN_1, gpiod.line.Value.ACTIVE)
        act_req.set_value(ACT_PIN_2, gpiod.line.Value.INACTIVE)
        time.sleep(20)  # Extend for 20 seconds

        # Wait at full extension
        act_req.set_value(ACT_PIN_1, gpiod.line.Value.INACTIVE)
        act_req.set_value(ACT_PIN_2, gpiod.line.Value.INACTIVE)
        time.sleep(3)  # Hold at full extension for 3 seconds

        # Retract
        act_req.set_value(ACT_PIN_1, gpiod.line.Value.INACTIVE)
        act_req.set_value(ACT_PIN_2, gpiod.line.Value.ACTIVE)
        time.sleep(20)  # Retract for 20 seconds

        # Stop
        act_req.set_value(ACT_PIN_1, gpiod.line.Value.INACTIVE)
        act_req.set_value(ACT_PIN_2, gpiod.line.Value.INACTIVE)

        # Stop PWM
        pwm_write(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "duty_cycle", 0)

    except Exception as e:
        print(f"Error in Reset Ball: {e}")
