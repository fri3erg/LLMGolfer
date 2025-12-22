import time
import os
import sys

# Define Constants
SERVO_PWM_CHANNEL = 0
SERVO_PWM_FREQ = 50
SERVO_REST_POS_NS = 1100 * 1000
SERVO_MAX_SWING_NS = 1900 * 1000


def get_pwm_chip():
    """Finds the PWM chip with at least 2 channels."""
    found_chip = None
    for i in range(10):
        path = f"/sys/class/pwm/pwmchip{i}"
        if os.path.exists(path):
            try:
                with open(f"{path}/npwm", "r") as f:
                    npwm = int(f.read().strip())
                if npwm >= 2:
                    print(f"Found PWM Chip {i} with {npwm} channels.")
                    return i
            except:
                continue
    print("Could not find suitable PWM chip. Defaulting to 0.")
    return 0


def pwm_write(chip, channel, file, value):
    """Safely writes to a PWM file."""
    path = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/{file}"
    try:
        with open(path, "w") as f:
            f.write(str(value))
    except Exception as e:
        print(f"PWM Write Error ({file}): {e}")


def pwm_export(chip, channel):
    """Exports a PWM channel."""
    export_path = f"/sys/class/pwm/pwmchip{chip}/export"
    pwm_dir = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}"

    if os.path.exists(pwm_dir):
        return

    try:
        with open(export_path, "w") as f:
            f.write(str(channel))
    except (IOError, OSError):
        pass

    time.sleep(0.5)  # Wait for OS


def test_servo():
    print("Starting Servo Test (GPIO 12 / PWM0)...")
    chip = get_pwm_chip()

    # Setup
    pwm_export(chip, SERVO_PWM_CHANNEL)

    period = int(1_000_000_000 / SERVO_PWM_FREQ)
    pwm_write(chip, SERVO_PWM_CHANNEL, "period", period)
    pwm_write(chip, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)
    pwm_write(chip, SERVO_PWM_CHANNEL, "enable", "1")

    print("Servo ON. Outputting PWM on GPIO 12 (Pin 32).")
    print(
        "-> If no movement: Check White Wire on GPIO 12, Power +/-, and Grounds tied together."
    )

    try:
        while True:
            print(f"Duty Cycle: {SERVO_REST_POS_NS} (Rest)")
            pwm_write(chip, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)
            time.sleep(2)

            print(f"Duty Cycle: {SERVO_MAX_SWING_NS} (Swing)")
            pwm_write(chip, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_MAX_SWING_NS)
            time.sleep(2)

    except KeyboardInterrupt:
        print("Test Stopped.")
        pwm_write(chip, SERVO_PWM_CHANNEL, "enable", "0")


if __name__ == "__main__":
    test_servo()
