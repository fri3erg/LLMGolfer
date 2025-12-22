# main_controller.py

import math

import time

import sys

from llm_golfer import AssistantGolfer

import audio_manager

import hardware_controller

import feedback_generator

import vision_system


# Game Configuration

# Position and Win Condition Parameters
# Fixed coordinates are no longer used - hole position is calibrated at game start
# HOLE_X = 408
# HOLE_Y = 112
# HOLE_COORDS = (HOLE_X, HOLE_Y)

# Win threshold: radius in pixels around the hole
WIN_DISTANCE_THRESHOLD = 30


def calibrate_hole_position():
    """
    Calibrates hole position by detecting ball placed in hole.
    Returns: tuple (x, y) of hole coordinates
    """
    print("\nHole Calibration")

    # Detect ball position (which is in the hole)
    hole_coords = vision_system.get_live_ball_position()

    if hole_coords is None:
        print("ERROR: Could not detect ball. Please ensure ball is visible.")
        sys.exit(1)

    print(f"Hole position detected at: {hole_coords}")

    # Reset ball to starting position
    print("Running actuator cycle to reset ball...")
    hardware_controller.reset_ball_actuator()

    print("Calibration complete!\n")
    return hole_coords


def run_game():

    print("Starting Golf Game")

    golfer = AssistantGolfer()

    golfer.start_new_game()

    shot_history = []

    shot_count = 0

    try:

        # 1. Setup
        hardware_controller.setup_all()
        hardware_controller.home_stepper()

        print("Initializing Vision System...")
        vision_system.vision_system_instance.start_camera()

        # Calibrate hole position at game start
        hole_coords = calibrate_hole_position()

        while True:

            shot_count += 1

            print(f"\nShot {shot_count}")

            # Construct prompt

            history_str = (
                "\n".join(shot_history) if shot_history else "No previous shots."
            )

            prompt = (
                f"You are at the tee. Shot #{shot_count}.\n"
                "The hole location is unknown to you, rely on feedback.\n"
                f"History:\n{history_str}\n"
                "Choose your shot:\n"
                "- aim_degrees (strictly between 45 and 135)\n"
                "- strike_force (0-100)\n"
                "- commentary (keep it very short, under 10 words)"
            )

            # 3. Get Decision

            print("Requesting shot decision...")

            response = golfer.get_next_shot_decision(prompt)

            if response is None:

                print("Network/API Error: Could not get shot decision. Retrying...")

                continue  # Skip to the start of the loop to try again

            decision = response.get("decision", {})

            tool_id = response.get("tool_call_id", {})

            aim = float(decision.get("aim_degrees", 90))

            force = int(decision.get("strike_force", 50))

            comment = decision.get("commentary", "Here we go.")

            # Play audio immediately

            audio_manager.play_speech(comment)

            # 4. Execute Shot

            hardware_controller.set_stepper_angle(aim)

            time.sleep(0.5)

            hardware_controller.swing_club(force)

            # 5. Wait for Settle

            print("Waiting 3s for ball to settle...")

            time.sleep(3)

            # Vision and Feedback
            ball_pos = vision_system.get_live_ball_position()

            if ball_pos is None:

                print("Ball not found. Assuming missed/out of bounds.")

                nl_feedback = (
                    "I lost sight of the ball completely. It might be off the course."
                )

                distance = 9999

            else:

                # Calculate distance and generate feedback...

                distance = math.dist(ball_pos, hole_coords)

                nl_feedback = feedback_generator.get_fuzzy_feedback(
                    ball_pos, hole_coords
                )

                print(f"Feedback: {nl_feedback}")

            shot_result = (
                f"Shot {shot_count}: Aim {aim}, Force {force}. Result: {nl_feedback}"
            )

            shot_history.append(shot_result)

            golfer.add_tool_response_to_history(tool_id, shot_result)

            # 7. Check Win Condition

            if distance <= WIN_DISTANCE_THRESHOLD:

                print("HOLE IN ONE!")

                # Ask for celebration

                celebration_prompt = (
                    "You just sank the ball! Give me a loud, short celebration line!"
                )

                cel_resp = golfer.get_simple_text_response(celebration_prompt)

                audio_manager.play_speech(cel_resp)

                print("Game Over. Winning.")

                break

            else:

                # 8. Continuation Loop

                print("Missed. Preparing for next shot...")

                # Ask for reaction to the miss

                reaction_prompt = f"You missed. Feedback was: {nl_feedback}. Give a 5-word regretful comment."

                react_resp = golfer.get_simple_text_response(reaction_prompt)

                audio_manager.play_speech(react_resp)

                # Reset Ball

                hardware_controller.reset_ball_actuator()

    except KeyboardInterrupt:

        print("User stopped game.")

    except Exception as e:

        print(f"CRITICAL ERROR: {e}")

    finally:

        print("Shutting down systems...")
        hardware_controller.cleanup_all()

        # Cleanup Camera
        vision_system.vision_system_instance.stop_camera()

        sys.exit()


if __name__ == "__main__":

    run_game()
