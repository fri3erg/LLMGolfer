import time
import os

# GPIO 19 is mapped to PWM Channel 3 in the RP1 hardware


PIN_DESC = "GPIO 19"


def try_pwm(chip_num, channel_num):
    base = f"/sys/class/pwm/pwmchip{chip_num}"
    export_path = f"{base}/export"
    pwm_path = f"{base}/pwm{channel_num}"

    # 1. Export
    if not os.path.exists(pwm_path):
        try:
            with open(export_path, "w") as f:
                f.write(str(channel_num))
            time.sleep(0.1)
        except OSError:
            print(
                f"   [Skip] Chip {chip_num} Channel {channel_num} (Export failed/Busy)"
            )
            return False

    # 2. Configure Period (20ms / 50Hz)
    try:
        with open(f"{pwm_path}/period", "w") as f:
            f.write("20000000")

        with open(f"{pwm_path}/duty_cycle", "w") as f:
            f.write("1500000")  # 1.5ms Center

        with open(f"{pwm_path}/enable", "w") as f:
            f.write("1")

        print(f"SUCCESS? Chip {chip_num} Channel {channel_num} is ACTIVE.")
        print("-> Check Servo now!")

        # Wiggle
        while True:
            print("   -> 1.0ms")
            with open(f"{pwm_path}/duty_cycle", "w") as f:
                f.write("1000000")
            time.sleep(1)
            print("   -> 2.0ms")
            with open(f"{pwm_path}/duty_cycle", "w") as f:
                f.write("2000000")
            time.sleep(1)

    except Exception as e:
        print(f"Fail Chip {chip_num} Channel {channel_num}: {e}")
        return False


def main():
    print(f" Hunting for {PIN_DESC} PWM Controller...")

    # Try probable combinations for RP1 (Pi 5)
    # Usually Chip 2 matches GPIO 18/19 logic

    # Try Chip 0, Channel 3 (Raw match)
    if not try_pwm(0, 3):
        # Try Chip 2, Channel 3
        if not try_pwm(2, 3):
            # Try Chip 0, Channel 1 (Sometimes it's offset)
            try_pwm(0, 1)


if __name__ == "__main__":
    main()
