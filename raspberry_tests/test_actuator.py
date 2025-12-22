import time
import os
import gpiod
import sys

# Define Constants
ACTUATOR_PWM_CHANNEL = 1
ACT_PIN_1 = 17
ACT_PIN_2 = 27
GPIO_CHIP_PATH = "/dev/gpiochip4"


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

    time.sleep(0.5)


def test_actuator():
    print(" Starting Actuator Test...")
    print("   -> PWM Enable: GPIO 13 (Pin 33)")
    print("   -> Direction 1: GPIO 17 (Pin 11)")
    print("   -> Direction 2: GPIO 27 (Pin 13)")

    # 1. Setup PWM (Speed Control)
    pwm_chip = get_pwm_chip()
    pwm_export(pwm_chip, ACTUATOR_PWM_CHANNEL)

    # 1kHz Frequency
    period = int(1_000_000_000 / 1000)
    pwm_write(pwm_chip, ACTUATOR_PWM_CHANNEL, "period", period)
    pwm_write(pwm_chip, ACTUATOR_PWM_CHANNEL, "duty_cycle", period)  # Full Speed
    pwm_write(pwm_chip, ACTUATOR_PWM_CHANNEL, "enable", "1")

    # 2. Setup GPIO (Direction Control)
    try:
        gpiod_chip = gpiod.Chip(GPIO_CHIP_PATH)
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
        lines = gpiod_chip.request_lines(consumer="test_actuator", config=config)
    except Exception as e:
        print(f"GPIO Error: {e}")
        return

    print("Actuator ON. Cycling Extend/Retract...")

    try:
        while True:
            print("\n>>> EXTENDING")
            print("    GPIO 17 (IN1) => HIGH")
            print("    GPIO 27 (IN2) => LOW")
            print("    GPIO 13 (ENA) => PWM HIGH")
            lines.set_value(ACT_PIN_1, gpiod.line.Value.ACTIVE)
            lines.set_value(ACT_PIN_2, gpiod.line.Value.INACTIVE)
            time.sleep(5)

            print("\n<<< RETRACTING")
            print("    GPIO 17 (IN1) => LOW")
            print("    GPIO 27 (IN2) => HIGH")
            print("    GPIO 13 (ENA) => PWM HIGH")
            lines.set_value(ACT_PIN_1, gpiod.line.Value.INACTIVE)
            lines.set_value(ACT_PIN_2, gpiod.line.Value.ACTIVE)
            time.sleep(5)

            print("\n--- STOP")
            print("    GPIO 17 (IN1) => LOW")
            print("    GPIO 27 (IN2) => LOW")
            lines.set_value(ACT_PIN_1, gpiod.line.Value.INACTIVE)
            lines.set_value(ACT_PIN_2, gpiod.line.Value.INACTIVE)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nTest Stopped.")
        lines.set_value(ACT_PIN_1, gpiod.line.Value.INACTIVE)
        lines.set_value(ACT_PIN_2, gpiod.line.Value.INACTIVE)
        pwm_write(pwm_chip, ACTUATOR_PWM_CHANNEL, "enable", "0")


if __name__ == "__main__":
    test_actuator()
