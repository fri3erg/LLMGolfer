# hardware_controller.py (Mock version for Windows)
import time

def aim_club(target_position):
    """ MOCK FUNCTION: Simulates aiming the club. """
    print(f"--- MOCK HW --- Aiming club at position: {target_position}")
    time.sleep(1)

def strike_ball(force_percentage):
    """ MOCK FUNCTION: Simulates striking the ball. """
    print(f"--- MOCK HW --- Striking ball with {force_percentage}% force!")
    time.sleep(0.5)

def reset_ball():
    """ MOCK FUNCTION: Simulates tilting the surface. """
    print("--- MOCK HW --- Resetting ball...")
    time.sleep(2)
    print("--- MOCK HW --- Surface is level.")