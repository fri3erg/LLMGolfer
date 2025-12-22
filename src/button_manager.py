import gpiod
import time
import subprocess
import signal
import os
import sys

# Button Pin (BCM Number)
BUTTON_PIN = 16

# GPIO Chip Path
GPIO_CHIP_PATH = "/dev/gpiochip4"

# Path to main script
SCRIPT_PATH = "/home/frigo/LLMGolfer/src/main_controller.py"
# Python interpreter to use (path to venv python)
PYTHON_PATH = "/home/frigo/LLMGolfer/venv/bin/python"


class ServiceManager:
    def __init__(self):
        self.process = None
        self.running = False

    def start_game(self):
        if self.running:
            print("Game already running. Restarting...")
            self.stop_game()
            time.sleep(1)

        print("Starting Golfer...")
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            self.process = subprocess.Popen(
                [PYTHON_PATH, SCRIPT_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            self.running = True

        except Exception as e:
            print(f"Failed to start process: {e}")
            self.running = False

    def stop_game(self):
        if self.process and self.running:
            print("Stopping Golfer...")
            # Send SIGINT (CTRL+C) to allow graceful cleanup in the script
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Process did not exit. Forcing kill.")
                self.process.kill()

            self.process = None
            self.running = False
            print("Stopped.")
        else:
            print("Nothing to stop.")


def main():
    print("Button Service Started.")
    manager = ServiceManager()

    # Setup GPIO
    try:
        chip = gpiod.Chip(GPIO_CHIP_PATH)
        # V2: request_lines
        config = {
            BUTTON_PIN: gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT, bias=gpiod.line.Bias.PULL_UP
            )
        }
        button_req = chip.request_lines(consumer="ButtonMgr", config=config)

    except Exception as e:
        print(f"GPIO Setup Failed: {e}")
        return

    # Button State Tracking
    last_val = gpiod.line.Value.ACTIVE

    try:
        while True:
            current_val = button_req.get_value(BUTTON_PIN)

            # Detect Falling Edge (Button Press: 1 -> 0)
            if (
                last_val == gpiod.line.Value.ACTIVE
                and current_val == gpiod.line.Value.INACTIVE
            ):
                print("Button Pressed!")

                # Simple Logic: Toggle
                # If running -> Stop
                # If stopped -> Start

                if manager.running:
                    # Check if process actually died on its own
                    if manager.process.poll() is not None:
                        manager.running = False
                        manager.start_game()  # Restart if it crashed/finished
                    else:
                        manager.stop_game()  # Stop if running
                else:
                    manager.start_game()

                # Debounce
                time.sleep(0.5)

            last_val = current_val
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exiting...")
        manager.stop_game()
    finally:
        chip.close()


if __name__ == "__main__":
    main()
