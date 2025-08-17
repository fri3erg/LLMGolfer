# hardware_controller.py (Conceptual)
from gpiozero import Servo, Motor
import time

# Placeholder GPIO pins
SERVO_PIN = 17
STEPPER_DIR_PIN = 20
STEPPER_STEP_PIN = 21
ACTUATOR_FORWARD_PIN = 23
ACTUATOR_BACKWARD_PIN = 24

# --- Setup ---
# You'll need to configure the stepper driver (DRV8825) microstepping pins
# and create a stepper control function.
# For the servo, gpiozero is excellent.
striking_servo = Servo(SERVO_PIN)
ball_reset_actuator = Motor(forward=ACTUATOR_FORWARD_PIN, backward=ACTUATOR_BACKWARD_PIN)

# --- State Variables ---
current_stepper_position = 0 # Track the club's position

def aim_club(target_position):
    """Moves the stepper motor from its current position to the target.
    target_position is from -100 to 100.
    """
    global current_stepper_position
    # TODO: Add logic to convert target_position to a number of steps
    # and pulse the STEP pin.
    print(f"Aiming club at position {target_position}...")
    # ... your stepper motor logic here ...
    current_stepper_position = target_position
    time.sleep(1) # Wait for movement to complete

def strike_ball(force_percentage):
    """Swings the servo to strike the ball.
    force_percentage (1-100) is mapped to servo speed/angle.
    """
    # TODO: Map force_percentage to a meaningful servo movement.
    # A simple way: map force to the servo's max angle.
    # A more advanced way: control the speed of the swing.
    print(f"Striking ball with {force_percentage}% force...")
    striking_servo.min()
    time.sleep(0.5)
    striking_servo.max() # Simple swing
    time.sleep(0.5)
    striking_servo.min() # Reset position

def reset_ball():
    """Tilts the surface to reset the ball."""
    print("Resetting the ball...")
    ball_reset_actuator.forward()
    time.sleep(2) # Time to tilt up
    ball_reset_actuator.backward()
    time.sleep(2) # Time to return to flat
    ball_reset_actuator.stop()
    print("Surface is level.")