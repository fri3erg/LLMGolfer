import time

import numpy as np

import cv2

from picamera2 import Picamera2



# --- Configuration ---

CAMERA_WIDTH = 640

CAMERA_HEIGHT = 480

MIN_BALL_AREA = 500  # Minimum pixel area to count as a ball (filters noise)



# Color Definitions (HSV) - Tuned for a White Ball

# Adjust 'S' (Saturation) and 'V' (Value) if your room is darker/brighter

LOWER_WHITE = np.array([0, 0, 180])      # Low saturation, High brightness

UPPER_WHITE = np.array([179, 40, 255])   # Allow any hue, Low saturation, Max brightness



def get_live_ball_position():

    """

    Initializes the camera, captures a single frame, finds the ball,

    and returns (x, y) coordinates. Returns None if no ball is found.

    """

    print("📸 VISION: Starting camera capture...")

    ball_coords = None

    

    # 1. Initialize & Configure Camera

    # We use a context manager or try/finally to ensure camera closes properly

    try:

        picam2 = Picamera2()

        config = picam2.create_preview_configuration(main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)})

        picam2.configure(config)

        

        # 2. Warm Up (Auto-Exposure/White Balance)

        picam2.start()

        # Wait 2 seconds for the sensor to adjust to the light

        time.sleep(2.0) 

        

        # 3. Capture Image

        frame = picam2.capture_array()

        picam2.stop()

        picam2.close() # Release hardware immediately

        

        # 4. Image Processing

        # Convert BGR (standard OpenCV) to HSV (easier for color detection)

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        

        # Create a mask: White pixels become 255, everything else 0

        mask = cv2.inRange(hsv_frame, LOWER_WHITE, UPPER_WHITE)

        

        # Optional: Clean up noise (Erosion/Dilation)

        # kernel = np.ones((5,5), np.uint8)

        # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)



        # 5. Find Contours

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)



        if contours:

            # Find the largest contour (assumed to be the ball)

            ball_contour = max(contours, key=cv2.contourArea)

            

            if cv2.contourArea(ball_contour) > MIN_BALL_AREA:

                M = cv2.moments(ball_contour)

                if M["m00"] != 0:

                    cX = int(M["m10"] / M["m00"])

                    cY = int(M["m01"] / M["m00"])

                    ball_coords = (cX, cY)

                    print(f"✅ VISION: Ball found at {ball_coords}")

                    

                    # (Optional) Save debug image to check what the robot saw

                    # cv2.circle(frame, (cX, cY), 10, (0, 255, 0), 2)

                    # cv2.imwrite("debug_last_shot.jpg", frame)

            else:

                print("⚠️ VISION: Object detected, but too small (noise).")

        else:

            print("❌ VISION: No white objects found.")



    except Exception as e:

        print(f"❌ VISION ERROR: {e}")

        # Attempt to close camera if it crashed open

        try:

            picam2.stop()

            picam2.close()

        except:

            pass



    return ball_coords

