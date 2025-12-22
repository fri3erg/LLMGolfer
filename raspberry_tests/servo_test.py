import time
import os

# --- Configuration ---
PWM_CHIP = 0
PWM_CHANNEL = 3
PWM_FREQUENCY = 50

MIN_PULSE = 500
MAX_PULSE = 2500
REST_POS = 1500  # Center/neutral
BACKSWING_POS = 800  # Full backswing
FORWARD_POS = 2500  # Full forward swing

# Global to track current position for smooth transitions
current_servo_pos = REST_POS

PWM_BASE = f"/sys/class/pwm/pwmchip{PWM_CHIP}"
PWM_PATH = f"{PWM_BASE}/pwm{PWM_CHANNEL}"
PERIOD_NS = int(1_000_000_000 / PWM_FREQUENCY)


def pwm_write(filename, value):
    try:
        with open(f"{PWM_PATH}/{filename}", "w") as f:
            f.write(str(value))
    except Exception as e:
        print(f"Error: {e}")


def setup_servo():
    if not os.path.exists(PWM_PATH):
        try:
            with open(f"{PWM_BASE}/export", "w") as f:
                f.write(str(PWM_CHANNEL))
            time.sleep(0.1)
        except Exception as e:
            return False
    pwm_write("period", PERIOD_NS)
    return True


def set_servo_position(pulse_width_us):
    """Directly sets the PWM duty cycle."""
    global current_servo_pos
    duty_cycle_ns = int(pulse_width_us * 1000)
    pwm_write("duty_cycle", duty_cycle_ns)
    current_servo_pos = pulse_width_us


def smooth_move(target_us, steps=30, delay=0.01):
    """
    Moves the servo in small increments to prevent amp spikes.
    - steps: Higher number = slower/smoother move.
    - delay: Time in seconds between steps.
    """
    global current_servo_pos

    start_pos = current_servo_pos
    if start_pos == target_us:
        return

    # Calculate step increment
    diff = target_us - start_pos
    step_inc = diff / steps

    for i in range(1, steps + 1):
        next_pos = int(start_pos + (step_inc * i))
        set_servo_position(next_pos)
        time.sleep(delay)


def swing_club(power=100):
    if not (0 <= power <= 100):
        return

    print(f"--- Swinging: {power}% power ---")

    # Enable PWM if not already
    pwm_write("enable", "1")

    # Boost power for weaker servo (50-100% range)
    boosted_power = 50 + (power / 100.0) * 50

    # Calculate backswing position based on power
    backswing_range = BACKSWING_POS - REST_POS  # Negative range
    backswing_pos = int((boosted_power / 100.0) * backswing_range) + REST_POS

    # 1. Start from neutral
    print(f"Moving to center ({REST_POS}µs)...")
    set_servo_position(REST_POS)
    time.sleep(0.2)

    # 2. Backswing
    print(f"Backswing to {backswing_pos}µs...")
    set_servo_position(backswing_pos)
    time.sleep(1.0)  # Hold backswing

    # 3. Forward swing (hitting the ball)
    print(f"Forward swing to {FORWARD_POS}µs...")
    set_servo_position(FORWARD_POS)
    time.sleep(1.0)  # Hold forward

    # 4. Return to neutral
    print(f"Return to center ({REST_POS}µs)...")
    set_servo_position(REST_POS)
    time.sleep(0.5)


def cleanup():
    pwm_write("enable", "0")


if __name__ == "__main__":
    try:
        if not setup_servo():
            exit(1)

        # Start at rest
        set_servo_position(REST_POS)
        pwm_write("enable", "1")

        while True:
            swing_club(power=100)  # Only 100% power
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()
