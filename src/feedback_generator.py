import math

def get_nl_feedback(landing_coords, hole_coords, start_coords):
    """
    Analyzes a shot's outcome and generates natural language feedback using vector math.
    """
    feedback_parts = []

    # --- 1. Analyze Strength (Distance) ---
    shot_distance = math.dist(start_coords, landing_coords)
    ideal_distance = math.dist(start_coords, hole_coords)
    distance_error_ratio = (shot_distance - ideal_distance) / ideal_distance

    if distance_error_ratio < -0.4:
        feedback_parts.append("way too weak")
    elif distance_error_ratio < -0.1: # Adjusted for more sensitive feedback
        feedback_parts.append("a bit too weak")
    elif distance_error_ratio > 0.4:
        feedback_parts.append("way too strong")
    elif distance_error_ratio > 0.1: # Adjusted for more sensitive feedback
        feedback_parts.append("a bit too strong")

    # --- 2. Analyze Aim (Direction) with an extra layer of feedback ---
    # Vector from start to hole (the ideal path)
    vec_ideal_x = hole_coords[0] - start_coords[0]
    vec_ideal_y = hole_coords[1] - start_coords[1]

    # Vector from start to where the ball landed (the actual path)
    vec_actual_x = landing_coords[0] - start_coords[0]
    vec_actual_y = landing_coords[1] - start_coords[1]
    
    # Calculate the angle error in degrees
    angle_to_hole = math.atan2(vec_ideal_y, vec_ideal_x)
    angle_of_shot = math.atan2(vec_actual_y, vec_actual_x)
    angle_error_deg = math.degrees(angle_to_hole - angle_of_shot)

    # --- NEW: Three tiers of directional feedback ---
    if angle_error_deg > 15: # Large error to the right
        feedback_parts.append("way too far to the right")
    elif angle_error_deg > 5: # **NEW** Moderate error to the right
        feedback_parts.append("off to the right")
    elif angle_error_deg > 2: # Small error to the right
        feedback_parts.append("slightly to the right")
    elif angle_error_deg < -15: # Large error to the left
        feedback_parts.append("way too far to the left")
    elif angle_error_deg < -5: # **NEW** Moderate error to the left
        feedback_parts.append("off to the left")
    elif angle_error_deg < -2: # Small error to the left
        feedback_parts.append("slightly to the left")

    # --- 3. Combine the feedback ---
    if not feedback_parts:
        return "That was very close!"
    else:
        return "Your shot was " + " and ".join(feedback_parts) + "."