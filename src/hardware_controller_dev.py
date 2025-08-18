# hardware_controller_dev.py (Mock version with physics)
import math

# A simple scaling factor for how force translates to distance
FORCE_SCALAR = 10 

def execute_shot_physics(aim_degrees, force_percentage, start_coords):
    """
    MOCK FUNCTION: Simulates the physics of a shot.
    Takes an angle and force and calculates where the ball will land.
    """
    # Convert angle to radians for math functions
    angle_rad = math.radians(aim_degrees)
    
    # Calculate distance based on force
    distance = force_percentage * FORCE_SCALAR
    
    # Calculate the new X and Y coordinates using trigonometry
    # Note: In many graphics systems, Y decreases as you go "up", 
    # so we subtract for Y. Here we assume Y increases going "up".
    # 0 degrees is right, 90 is up.
    start_x, start_y = start_coords
    end_x = start_x + distance * math.cos(angle_rad)
    end_y = start_y + distance * math.sin(angle_rad)
    
    # Return the landing coordinates as integers
    return (int(end_x), int(end_y))

def reset_ball():
    """ MOCK FUNCTION: Simulates resetting the ball. """
    print("--- MOCK HW --- Ball has been reset to the starting point.")