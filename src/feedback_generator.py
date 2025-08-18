import math

def get_nl_feedback(landing_coords, hole_coords, start_coords):
    """
    Analyzes a shot's outcome and generates natural language feedback.
    """
    feedback_parts = []

    # --- 1. Analyze Strength (Distance) ---
    shot_distance = math.dist(start_coords, landing_coords)
    ideal_distance = math.dist(start_coords, hole_coords)
    
    distance_error_ratio = (shot_distance - ideal_distance) / ideal_distance

    if distance_error_ratio < -0.4:
        feedback_parts.append("way too weak")
    elif distance_error_ratio < -0.1:
        feedback_parts.append("a bit too weak")
    elif distance_error_ratio > 0.4:
        feedback_parts.append("way too strong")
    elif distance_error_ratio > 0.1:
        feedback_parts.append("a bit too strong")
    else:
        # The force was about right, so we don't need to say anything about it.
        pass

    # --- 2. Analyze Aim (Direction) ---
    # This simplified logic assumes a mostly vertical shot, which matches our setup.
    # It checks if the ball landed to the left or right of the hole.
    landing_x, _ = landing_coords
    hole_x, _ = hole_coords
    
    side_error = landing_x - hole_x
    
    if side_error < -50: # A large error to the left
        feedback_parts.append("far to the left")
    elif side_error < -10: # A small error to the left
        feedback_parts.append("slightly to the left")
    elif side_error > 50: # A large error to the right
        feedback_parts.append("far to the right")
    elif side_error > 10: # A small error to the right
        feedback_parts.append("slightly to the right")

    # --- 3. Combine the feedback ---
    if not feedback_parts:
        return "That was very close!"
    else:
        return "Your shot was " + " and ".join(feedback_parts) + "."