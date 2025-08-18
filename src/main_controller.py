# main_controller.py (Iterative Learning Version)
import math
from llm_golfer import AssistantGolfer
import audio_manager
import hardware_controller_dev  # Use the mock version for Windows
import feedback_generator # <-- Import the new module

# --- Game Configuration ---
START_COORDS = (500, 0) # The ball always starts here
HOLE_COORDS = (300, 800)  # The target
WIN_RADIUS = 25           # How close the ball needs to be to the hole to win
MAX_SHOTS = 10            # Prevent infinite loops

def run_game():
    print("⛳ Starting Miniature Golf Simulator - Iterative Learning Mode ⛳")

    # --- Initialization ---
    golfer = AssistantGolfer()
    golfer.start_new_game()
    shot_history = []
    shot_count = 0
    game_over = False

    while not game_over:
        shot_count += 1
        print(f"\n--- Shot {shot_count} ---")

        # 1. Build the prompt from the shot history
        if not shot_history:
            # First shot prompt is special
            prompt = "This is your first shot. Make your best guess to start."
        else:
            # Subsequent prompts include history
            history_str = "\n".join(shot_history)
            prompt = (
                f"Here is the history of your shots:\n{history_str}\n"
                f"The ball is now back at the start. Analyze your past attempts and take your next shot."
            )

        print(f"Sending prompt to LLM:\n{prompt}\n")

        # 2. Get the LLM's decision
        decision = golfer.get_next_shot_decision(prompt)

        if not decision or "aim_degrees" not in decision:
            print("LLM failed to make a valid decision. Ending game.")
            break

        audio_manager.play_speech(decision['commentary'])
        
        aim = decision['aim_degrees']
        force = decision['strike_force']
        print(f"Executing shot: Aim={aim}°, Force={force}%")

        landing_coords = hardware_controller_dev.execute_shot_physics(aim, force, START_COORDS)
        print(f"Ball landed at: {landing_coords}")
        
        # --- NEW: Generate and record NL feedback ---
        nl_feedback = feedback_generator.get_nl_feedback(landing_coords, HOLE_COORDS, START_COORDS)
        print(f"Feedback: {nl_feedback}")
        
        shot_result = (
            f"Shot {shot_count}: Aim={aim}°, Force={force}% -> Ball landed at {landing_coords}. "
            f"Hint: {nl_feedback}" # <-- Add the hint here
        )
        shot_history.append(shot_result)


        # 5. Check for a win or loss
        distance_to_hole = math.dist(landing_coords, HOLE_COORDS)
        print(f"Distance to hole: {distance_to_hole:.2f} units.")

        if distance_to_hole <= WIN_RADIUS:
            print("\n🎉 Congratulations! You got the ball in the hole! 🎉")
            audio_manager.play_speech("Incredible! A perfect shot, if I do say so myself.")
            game_over = True
        elif shot_count >= MAX_SHOTS:
            print("\nMaximum shots reached. Game over.")
            audio_manager.play_speech("Well, that didn't go as planned. Let's try again another time.")
            game_over = True

    print("\n--- Game Over ---")
    print("Final Shot History:")
    for entry in shot_history:
        print(entry)

if __name__ == "__main__":
    run_game()