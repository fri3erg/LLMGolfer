# main_controller.py (with fix for tool call loop)
import math
from llm_golfer import AssistantGolfer
import audio_manager
import hardware_controller_dev
import feedback_generator

# ... (Game Configuration is the same) ...
START_COORDS = (500, 0) # The ball always starts here
HOLE_COORDS = (300, 800)  # The target
WIN_RADIUS = 25           # How close the ball needs to be to the hole to win
MAX_SHOTS = 10            # Prevent infinite loops

def run_game():
    # ... (Initialization is the same) ...
    print("⛳ Starting Miniature Golf Simulator - Iterative Learning Mode ⛳")
    golfer = AssistantGolfer()
    golfer.start_new_game()
    shot_history = []
    shot_count = 0
    game_over = False

    while not game_over:
        shot_count += 1
        print(f"\n--- Shot {shot_count} ---")

        # ... (Prompt building is the same) ...
        history_str = "\n".join(shot_history) if shot_history else "No previous shots."
        prompt = (
            "The ball starts always at the start\n\n"
            f"Shot History:\n{history_str}\n\n"
            "Analyze the history and determine your next shot."
        )
        print(f"Sending prompt to LLM:\n{prompt}\n")

        # Get the LLM's decision and tool_call_id
        response_data = golfer.get_next_shot_decision(prompt)

        # Safely validate the response
        if not response_data or not response_data.get("decision") or not response_data.get("tool_call_id"):
            print("LLM response was incomplete or invalid. Ending game.")
            break
        
        decision = response_data["decision"]
        tool_call_id = response_data["tool_call_id"]
        
        # ... (Safely check decision keys) ...
        required_keys = ['aim_degrees', 'strike_force', 'commentary']
        if not all(key in decision for key in required_keys):
            print("LLM decision was missing required keys. Ending game.")
            break
        
        audio_manager.play_speech(decision['commentary'])
        
        aim = decision['aim_degrees']
        force = decision['strike_force']
        print(f"Executing shot: Aim={aim}°, Force={force}%")

        landing_coords = hardware_controller_dev.execute_shot_physics(aim, force, START_COORDS)
        print(f"Ball landed at: {landing_coords}")
        
        nl_feedback = feedback_generator.get_nl_feedback(landing_coords, HOLE_COORDS, START_COORDS)
        print(f"Feedback: {nl_feedback}")
        
        shot_result = (
            f"Shot {shot_count}: Aim={aim}°, Force={force}% -> Ball landed at {landing_coords}. "
            f"Hint: {nl_feedback}"
        )
        shot_history.append(shot_result)
        
        # *** ADD THIS LINE: Complete the loop by sending the tool result back ***
        golfer.add_tool_response_to_history(tool_call_id, shot_result)

        # ... (Win/loss checking is the same) ...
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