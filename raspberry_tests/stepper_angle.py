import gpiod
import time

# Configuration
STEP_PIN = 20
DIR_PIN = 21
LIMIT_SWITCH_PIN = 26  # Input pin for the limit switch
GPIO_CHIP = "gpiochip4"

# Motor & System Specs
TOTAL_STEPS = 4500  # EXAMPLE: The total steps from left to right
HOME_DIRECTION = 0  # 0 for Counter-Clockwise (left)
HOME_SPEED = 0.002  # Move slowly when homing

# Global State
current_position = -1  # Start with an unknown position
chip = None
step_line = None
dir_line = None
limit_switch_line = None


def home_motor():
    """Moves the motor until the limit switch is triggered to find position 0."""
    global current_position, limit_switch_line

    print("Homing motor... Moving left.")

    # Make sure the limit switch is set up as an input
    limit_switch_line = chip.get_line(LIMIT_SWITCH_PIN)
    limit_switch_line.request(consumer="limit_switch", type=gpiod.LINE_REQ_DIR_IN)

    # Move one step at a time until the switch is pressed (reads 0)
    while limit_switch_line.get_value() == 1:
        move(1, HOME_DIRECTION, HOME_SPEED)

    current_position = 0
    print(f"Homing complete. Current position is {current_position}.")
    limit_switch_line.release()  # Release the line


def go_to_angle(angle):
    """Calculates and moves the motor to a position based on a 0-180 degree input."""
    global current_position

    if current_position == -1:
        print("Motor not homed. Please home first.")
        return

    # Calculate the target step position
    target_steps = angle_to_steps(angle, TOTAL_STEPS)

    # Calculate the number of steps and direction to move
    steps_to_move = target_steps - current_position

    direction = (
        1 if steps_to_move > 0 else 0
    )  # 1=Clockwise (right), 0=Counter-Clockwise (left)

    print(
        f"Moving from {current_position} to {target_steps} ({abs(steps_to_move)} steps)"
    )

    move(abs(steps_to_move), direction, speed=0.0005)

    # Update our current position
    current_position = target_steps


# Main Application
if __name__ == "__main__":
    try:
        setup_gpio()  # This now needs to set up all 3 pins
        home_motor()

        # Now your calls are independent and precise
        print("\nStarting Operations")
        go_to_angle(90)  # Move to the middle
        time.sleep(2)

        go_to_angle(0)  # Move to the start
        time.sleep(2)

        go_to_angle(180)  # Move to the far end
        time.sleep(2)

        go_to_angle(45)  # Move to a quarter position
        time.sleep(2)

    finally:
        cleanup_gpio()
