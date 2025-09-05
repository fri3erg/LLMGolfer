import gpiod
import time

# --- Configuration ---
# GPIO pins
STEP_PIN = 20
DIR_PIN = 21
LIMIT_SWITCH_PIN = 26 # Using GPIO 26 for the switch

# GPIO chip for Raspberry Pi 5
GPIO_CHIP = 'gpiochip4'

# --- Constants ---
# Define directions for clarity
CLOCKWISE = 1
COUNTER_CLOCKWISE = 0

# Homing parameters
TEST_SPEED = 0.01 # A slow speed for the test

# --- Global GPIO objects ---
chip = None
step_line = None
dir_line = None
limit_switch_line = None

def setup_gpio():
    """Initializes GPIO pins for the motor controller and limit switch."""
    global chip, step_line, dir_line, limit_switch_line
    try:
        chip = gpiod.Chip(GPIO_CHIP)
        
        # Motor pins (Outputs)
        step_line = chip.get_line(STEP_PIN)
        dir_line = chip.get_line(DIR_PIN)
        step_line.request(consumer="stepper_step", type=gpiod.LINE_REQ_DIR_OUT)
        dir_line.request(consumer="stepper_dir", type=gpiod.LINE_REQ_DIR_OUT)
        
        # Limit switch pin (Input with pull-up)
        limit_switch_line = chip.get_line(LIMIT_SWITCH_PIN)
        limit_switch_line.request(
            consumer="limit_switch",
            type=gpiod.LINE_REQ_DIR_IN,
            flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP
        )
        print("GPIO setup successful.")
        
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        exit()

def cleanup_gpio():
    """Releases GPIO resources."""
    if step_line:
        step_line.release()
    if dir_line:
        dir_line.release()
    if limit_switch_line:
        limit_switch_line.release()
    if chip:
        chip.close()
    print("GPIO cleanup complete.")

def find_limit(direction, message):
    """Moves the motor in a set direction until the limit switch is pressed."""
    print(message)
    
    # Set the motor direction
    dir_line.set_value(direction)
    
    # Move one step at a time until the switch is pressed (reads HIGH)
    while limit_switch_line.get_value() == 0:
        step_line.set_value(1)
        time.sleep(TEST_SPEED)
        step_line.set_value(0)
        time.sleep(TEST_SPEED)
        
    print("✅ Limit reached!")

def main():
    """Runs a two-way homing test using a single, manually activated switch."""
    try:
        setup_gpio()
        
        # --- Test Part 1: First Direction ---
        find_limit(
            COUNTER_CLOCKWISE, 
            "\nPART 1: Moving COUNTER-CLOCKWISE... Please press the limit switch."
        )
        time.sleep(1)

        # --- Wait for switch release before starting the next part ---
        print("\nNow, please RELEASE the limit switch to continue...")
        while limit_switch_line.get_value() == 1:
            time.sleep(0.1) # Wait until the switch is no longer pressed
        print("Switch released. Starting Part 2 in 2 seconds...")
        time.sleep(2)

        # --- Test Part 2: Opposite Direction ---
        find_limit(
            CLOCKWISE,
            "\nPART 2: Moving CLOCKWISE... Please press the limit switch again."
        )

        print("\n🎉 Two-way homing test complete.")

    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()
