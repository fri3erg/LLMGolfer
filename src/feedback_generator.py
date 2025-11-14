# feedback_generator.py
import math

def get_fuzzy_feedback(ball_pos, hole_pos):
    """
    Converts precise pixel coordinates into vague, natural language feedback.
    
    Coordinate assumption (Standard Image):
    X: 0 is Left, Max is Right.
    Y: 0 is Top, Max is Bottom.
    """
    # Vector from Hole TO Ball
    # Positive dx = Ball is to the RIGHT of hole
    # Positive dy = Ball is BELOW hole (assuming Y grows down)
    
    dx = ball_pos[0] - hole_pos[0]
    dy = ball_pos[1] - hole_pos[1]
    
    # --- Define Thresholds (in Pixels) ---
    # Adjust these based on your camera resolution (640x480)
    TINY_MISS = 20
    MODERATE_MISS = 80
    LARGE_MISS = 150
    
    feedback_parts = []
    
    # --- Analyze Horizontal (Left/Right) ---
    direction_x = "right" if dx > 0 else "left"
    abs_dx = abs(dx)
    
    if abs_dx < TINY_MISS:
        # If it's extremely close horizontally, we might ignore it or say "dead center"
        pass 
    elif abs_dx < MODERATE_MISS:
        feedback_parts.append(f"a little bit to the {direction_x}")
    elif abs_dx < LARGE_MISS:
        feedback_parts.append(f"too far to the {direction_x}")
    else:
        feedback_parts.append(f"way, way too far to the {direction_x}")
        
    # --- Analyze Vertical (Short/Long) ---
    # NOTE: This depends on camera orientation. 
    # If Tee is at Bottom (High Y) and Hole is Top (Low Y):
    # If Ball Y > Hole Y -> Ball is "Short" (didn't reach top)
    # If Ball Y < Hole Y -> Ball is "Long" (went past top)
    
    # Let's assume standard setup: Tee (Bottom) -> Hole (Top)
    direction_y = "short" if dy > 0 else "long" 
    abs_dy = abs(dy)
    
    if abs_dy < TINY_MISS:
        pass
    elif abs_dy < MODERATE_MISS:
        feedback_parts.append(f"just a little {direction_y}")
    elif abs_dy < LARGE_MISS:
        feedback_parts.append(f"quite {direction_y}")
    else:
        feedback_parts.append(f"way too {direction_y}")

    # --- Combine ---
    if not feedback_parts:
        return "You were incredibly close, almost in!"
    
    return "You were " + " and ".join(feedback_parts) + "."