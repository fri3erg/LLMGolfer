import lgpio
import time

# Configuration
# Control pins for L298N
ENA_PIN = 12
IN1_PIN = 17
IN2_PIN = 27

# PWM settings for speed control
PWM_FREQUENCY = 2000

# Global Handle
h = None


def setup_actuator():
    """Initialize GPIO pins for the L298N driver."""
    global h
    try:
        h = lgpio.gpiochip_open(0)
        # Claim IN1 and IN2 as simple outputs
        lgpio.gpio_claim_output(h, IN1_PIN)
        lgpio.gpio_claim_output(h, IN2_PIN)
        print("GPIO chip opened and pins claimed.")
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        exit()


def move_actuator(speed, direction):
    """
    Moves the linear actuator.

    Args:
        speed (int): Speed from 0 (stop) to 100 (full speed).
        direction (str): "extend" or "retract".
    """
    if not h:
        print("Actuator not set up.")
        return

    # Set the direction pins
    if direction == "extend":
        lgpio.gpio_write(h, IN1_PIN, 1)
        lgpio.gpio_write(h, IN2_PIN, 0)
    elif direction == "retract":
        lgpio.gpio_write(h, IN1_PIN, 0)
        lgpio.gpio_write(h, IN2_PIN, 1)
    else:
        print("Invalid direction.")
        return

    # Set the speed using PWM on the ENA pin
    print(f"Moving actuator: direction='{direction}', speed={speed}%")
    lgpio.tx_pwm(h, ENA_PIN, PWM_FREQUENCY, speed)


def stop_actuator():
    """Stops the actuator by cutting power and braking."""
    if h:
        # Set PWM duty cycle to 0
        lgpio.tx_pwm(h, ENA_PIN, PWM_FREQUENCY, 0)
        # Set both direction pins low (this can act as a brake on some motors)
        lgpio.gpio_write(h, IN1_PIN, 0)
        lgpio.gpio_write(h, IN2_PIN, 0)
        print("Actuator stopped.")


def cleanup():
    """Stops the motor and releases GPIO resources."""
    if h:
        try:
            stop_actuator()
            lgpio.gpiochip_close(h)
            print("GPIO cleaned up.")
        except Exception as e:
            print(f"Error during cleanup: {e}")


# Main Program
if __name__ == "__main__":
    try:
        setup_actuator()
        print("\nStarting Actuator Test")

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

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        cleanup()
