import time
import numpy as np
import cv2
from picamera2 import Picamera2

# --- Configuration ---
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
MIN_BALL_AREA = 300  # Matched to your tuning script

# !!! IMPORTANT: UPDATE THESE WITH YOUR TUNING SCRIPT RESULTS !!!
# If you haven't tuned yet, these are the defaults from your script:
LOWER_WHITE = np.array([0, 0, 190])      
UPPER_WHITE = np.array([179, 30, 255])   

def get_live_ball_position():
    """
    Captures a frame, ROTATES 180, processes it, saves a debug image,
    and returns (x, y) coordinates.
    """
    print("📸 VISION: Starting camera capture...")
    ball_coords = None
    
    # 1. Initialize & Configure Camera
    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)})
        picam2.configure(config)
        picam2.start()
        
        # 2. Warm Up
        time.sleep(2.0) 
        
        # 3. Capture Image
        frame = picam2.capture_array()
        picam2.stop()
        picam2.close() 
        
        # --- CRITICAL: ROTATE TO MATCH YOUR TUNING ---
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        # ---------------------------------------------

        # 4. Image Processing
        blurred_frame = cv2.GaussianBlur(frame, (7, 7), 0)
        hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, LOWER_WHITE, UPPER_WHITE)
        
        morph_kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, morph_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, morph_kernel)

        # 5. Find Contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > MIN_BALL_AREA:
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    ball_coords = (cX, cY)
                    
                    # DRAW DEBUG INFO ON THE IMAGE
                    cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                    cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)
                    cv2.putText(frame, f"Ball: {ball_coords}", (cX - 20, cY - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    
                    print(f"✅ VISION: Ball found at {ball_coords} (Area: {area})")
            else:
                print(f"⚠️ VISION: Object detected but too small (Area: {area})")
        else:
            print("❌ VISION: No white objects found.")

        # 6. Save Debug Image (Always save so you can see what happened)
        cv2.imwrite("debug_view.jpg", frame)
        print("💾 Saved debug image to 'debug_view.jpg'")

    except Exception as e:
        print(f"❌ VISION ERROR: {e}")
        try:
            picam2.stop()
            picam2.close()
        except:
            pass

    return ball_coords

# ==========================================
# --- TEST BLOCK (Runs only if executed directly) ---
# ==========================================
if __name__ == "__main__":
    print("\n--- 🧪 RUNNING VISION SYSTEM TEST ---")
    
    # 1. Run the vision function
    coords = get_live_ball_position()
    
    # 2. Report results
    if coords:
        print(f"\n🎯 SUCCESS! Ball detected at: {coords}")
        
        # Optional: Calculate distance to your hole for verification
        HOLE_X, HOLE_Y = 408, 112
        import math
        dist = math.dist(coords, (HOLE_X, HOLE_Y))
        print(f"📏 Distance to Hole ({HOLE_X}, {HOLE_Y}): {dist:.2f} pixels")
    else:
        print("\n❌ FAILURE! No ball detected.")
        print("Check 'debug_view.jpg' to see if lighting/color tuning is the issue.")