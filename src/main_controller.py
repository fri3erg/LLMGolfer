# main_controller.py

import math

import time

import sys

from llm_golfer import AssistantGolfer

import audio_manager

import hardware_controller

import feedback_generator

import vision_system



# --- Game Configuration ---

# REAL WORLD Coordinates (Vision System)

HOLE_X = 408  

HOLE_Y = 112  

HOLE_COORDS = (HOLE_X, HOLE_Y)



WIN_DISTANCE_THRESHOLD = 30 # Pixels



def run_game():

    print("⛳ Starting STRICT HARDWARE Golf Game ⛳")

    golfer = AssistantGolfer()

    golfer.start_new_game()

    shot_history = []

    shot_count = 0

    

    try:

        # 1. Setup

        hardware_controller.setup_all()

        hardware_controller.home_stepper()

        

        while True:

            shot_count += 1

            print(f"\n--- Shot {shot_count} ---")

            

            # 2. Construct Prompt (HOLE LOCATION HIDDEN)

            # The LLM only knows it needs to hit the ball.

            history_str = "\n".join(shot_history) if shot_history else "No previous shots."

            

            # We constrain the prompt instructions

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

            print("🤔 Asking LLM...")

            response = golfer.get_next_shot_decision(prompt)

            

            if response is None:

                print("❌ Network/API Error: Could not get shot decision. Retrying...")

                continue # Skip to the start of the loop to try again

            

            decision = response.get("decision", {})

            tool_id = response.get("tool_call_id", {})

            

            aim = float(decision.get('aim_degrees', 90))

            force = int(decision.get('strike_force', 50))

            comment = decision.get('commentary', "Here we go.")

            

            # Play audio immediately

            audio_manager.play_speech(comment)

            

            # 4. Execute Shot

            hardware_controller.set_stepper_angle(aim)

            time.sleep(0.5)

            hardware_controller.swing_club(force)

            

            # 5. Wait for Settle (10 Seconds)

            print("⏳ Waiting 10s for ball to settle...")

            time.sleep(10)

            

            # 6. Vision & Feedback

            # CALL THE NEW LIVE CAMERA FUNCTION HERE

            ball_pos = vision_system.get_live_ball_position()

            

            if ball_pos is None:

                print("⚠️ Ball not found. Assuming missed/out of bounds.")

                nl_feedback = "I lost sight of the ball completely. It might be off the course."

                distance = 9999

            else:

                # Calculate distance and generate feedback...

                distance = math.dist(ball_pos, HOLE_COORDS)

                nl_feedback = feedback_generator.get_fuzzy_feedback(ball_pos, HOLE_COORDS)

                print(f"🗣️ Feedback: {nl_feedback}")

            

            shot_result = f"Shot {shot_count}: Aim {aim}, Force {force}. Result: {nl_feedback}"

            shot_history.append(shot_result)

            golfer.add_tool_response_to_history(tool_id, shot_result)

            

            # 7. Check Win Condition

            if distance <= WIN_DISTANCE_THRESHOLD:

                print("🎉 HOLE IN ONE! 🎉")

                

                # Ask for celebration

                celebration_prompt = "You just sank the ball! Give me a loud, short celebration line!"

                cel_resp = golfer.get_simple_text_response(celebration_prompt)

                audio_manager.play_speech(cel_resp)

                

                print("🏆 Game Over. Winning.")

                break # EXIT LOOP

                

            else:

                # 8. Continuation Loop

                print("❌ Missed. Preparing for next shot...")

                

                # Ask for reaction to the miss

                reaction_prompt = f"You missed. Feedback was: {nl_feedback}. Give a 5-word regretful comment."

                react_resp = golfer.get_simple_text_response(reaction_prompt)

                audio_manager.play_speech(react_resp)

                

                # Reset Ball

                hardware_controller.reset_ball_actuator()

                

                # Loop continues...



    except KeyboardInterrupt:

        print("User stopped game.")

    except Exception as e:

        print(f"CRITICAL ERROR: {e}")

    finally:

        hardware_controller.cleanup_all()

        sys.exit()



if __name__ == "__main__":

    run_game()