import gpiod
import time

# --- Configuration ---
# GPIO pins
STEP_PIN = 20
DIR_PIN = 21

# GPIO chip for Raspberry Pi 5
GPIO_CHIP = 'gpiochip4'

# --- Constants ---
# Define directions for clarity
CLOCKWISE = 1
COUNTER_CLOCKWISE = 0

# --- Global GPIO objects ---
# We define them globally to be accessible by all functions
chip = None
step_line = None
dir_line = None

def setup_gpio():
    """Initializes GPIO pins for the motor controller."""
    global chip, step_line, dir_line
    try:
        chip = gpiod.Chip(GPIO_CHIP)
        step_line = chip.get_line(STEP_PIN)
        dir_line = chip.get_line(DIR_PIN)

        step_line.request(consumer="stepper_step", type=gpiod.LINE_REQ_DIR_OUT)
        dir_line.request(consumer="stepper_dir", type=gpiod.LINE_REQ_DIR_OUT)
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        exit()

def cleanup_gpio():
    """Releases GPIO resources."""
    if step_line:
        step_line.release()
    if dir_line:
        dir_line.release()
    if chip:
        chip.close()
    print("GPIO cleanup complete.")

def move(steps, direction, speed=0.001):
    """
    Moves the stepper motor a given number of steps in a specific direction.
    
    Args:
        steps (int): The number of steps to move.
        direction (int): CLOCKWISE (1) or COUNTER_CLOCKWISE (0).
        speed (float): The delay between steps, controlling speed. Lower is faster.
    """
    if not all([chip, step_line, dir_line]):
        print("GPIO not initialized. Call setup_gpio() first.")
        return

    # Set the direction
    dir_line.set_value(direction)

    # Execute the steps
    for _ in range(steps):
        step_line.set_value(1)
        time.sleep(speed)
        step_line.set_value(0)
        time.sleep(speed)

def main():
    """Main function to test the stepper motor."""
    try:
        setup_gpio()
        
        # Most NEMA 17 motors are 200 steps/revolution
        steps_per_rev = 200
        
        print("Starting back-and-forth test...")
        while True:
            # Move one full rotation clockwise
            print("Moving clockwise...")
            move(steps_per_rev, CLOCKWISE, speed=0.0005)
            time.sleep(1) # Pause for a second

            # Move one full rotation counter-clockwise
            print("Moving counter-clockwise...")
            move(steps_per_rev, COUNTER_CLOCKWISE, speed=0.0005)
            time.sleep(1) # Pause for a second

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()