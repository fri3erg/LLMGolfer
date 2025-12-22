import cv2
import numpy as np
from picamera2 import Picamera2
import time

# Tweakable Parameters
# Define the range for white color in HSV color space
# Hue: 0-179, Saturation: 0-255, Value: 0-255
lower_white = np.array([0, 0, 180])
upper_white = np.array([179, 40, 255])
# Minimum area of the ball to be detected (filters out noise)
min_ball_area = 500

# Initialize Picamera2
picam2 = Picamera2()
# Configure camera for a smaller, faster resolution suitable for processing
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("Camera feed started. Looking for the golf ball...")
print("Press 'q' in the preview window to stop.")

try:
    while True:
        # Capture a frame as a NumPy array
        # The default color format from Picamera2 is BGR, which OpenCV uses
        frame = picam2.capture_array()

        # 1. Convert the image to the HSV color space
        # HSV is better for color detection under different lighting
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 2. Create a mask for the white color
        # The mask will be a binary image: white for pixels in the range, black otherwise
        mask = cv2.inRange(hsv_frame, lower_white, upper_white)

        # 3. Find contours (outlines of shapes) in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find the largest contour, which should be the ball
        if contours:
            ball_contour = max(contours, key=cv2.contourArea)

            # Check if the largest contour is big enough to be the ball
            if cv2.contourArea(ball_contour) > min_ball_area:
                # 4. Calculate the center coordinates of the ball
                M = cv2.moments(ball_contour)
                if M["m00"] != 0:
                    # Calculate center x and y
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])

                    # 5. Draw on the original frame for visualization
                    # Draw the contour outline
                    cv2.drawContours(frame, [ball_contour], -1, (0, 255, 0), 2)
                    # Draw a circle at the center
                    cv2.circle(frame, (cX, cY), 7, (0, 0, 255), -1)
                    # Put the coordinates as text
                    cv2.putText(
                        frame,
                        f"Ball at ({cX}, {cY})",
                        (cX - 50, cY - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        2,
                    )

                    # Print coordinates to the terminal
                    print(f"Ball detected at: X={cX}, Y={cY}")
                else:
                    print("Ball not found")
            else:
                print("Ball not found")
        else:
            print("Ball not found")

        # Display the resulting frame
        cv2.imshow("Golf Ball Detection", frame)

        # Exit if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        time.sleep(0.1)  # Small delay to prevent overwhelming the CPU

finally:
    # Cleanup
    picam2.stop()
    cv2.destroyAllWindows()
    print("Camera stopped and windows closed.")
