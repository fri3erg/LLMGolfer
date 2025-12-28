import math


def get_fuzzy_feedback(ball_pos, hole_pos):
    """
    Converts precise pixel coordinates into vague, natural language feedback.
    Coordinate system: X=0 is left, Y=0 is top.
    """

    # Vector from Hole TO Ball

    # Positive dx = Ball is to the RIGHT of hole

    # Positive dy = Ball is BELOW hole

    dx = ball_pos[0] - hole_pos[0]

    dy = ball_pos[1] - hole_pos[1]

    # Distance thresholds in pixels (based on 640x480 resolution)
    # Tightened thresholds for harsher feedback
    TINY_MISS = 10
    MODERATE_MISS = 60
    LARGE_MISS = 120

    feedback_parts = []

    # Analyze Horizontal

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

    # Vertical distance (short/long)
    # Positive dy: ball is below hole (short)
    # Negative dy: ball is above hole (long)
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

    # Combine

    if not feedback_parts:

        return "You were incredibly close, almost in!"

    return "You were " + " and ".join(feedback_parts) + "."
