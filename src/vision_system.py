import time
import numpy as np
import cv2
from picamera2 import Picamera2

# vision tuning parameters

# Camera resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Minimum ball detection area (pixels)
MIN_BALL_AREA = 100
MAX_BALL_AREA = 4000

# HSV color detection range for white ball
# Adjust these values based on lighting conditions
LOWER_WHITE = np.array([0, 0, 200])
UPPER_WHITE = np.array([180, 25, 255])

# Field Coordinates (Bottom Left, Top Left, Top Right, Bottom Right)
FIELD_CORNERS = np.array([
    [570, 90],   # Bottom Left
    [481, 337],  # Top Left
    [94, 365],   # Top Right
    [0, 70]      # Bottom Right
], dtype=np.int32)


class VisionSystem:
    def __init__(self):
        self.picam2 = None
        self.is_running = False

    def start_camera(self):
        """Initializes and starts the camera preview."""
        if self.is_running:
            return

        print("Initializing camera...")
        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}
            )
            self.picam2.configure(config)
            self.picam2.start()

            # Camera warmup for auto-exposure and white balance
            time.sleep(2.0)
            self.is_running = True
            print("Camera started and ready.")
        except Exception as e:
            print(f"VISION ERROR: Could not start camera: {e}")

    def stop_camera(self):
        """Stops and closes the camera resources."""
        if not self.is_running or not self.picam2:
            return

        print("Stopping camera...")
        try:
            self.picam2.stop()
            self.picam2.close()
            self.is_running = False
            self.picam2 = None
        except Exception as e:
            print(f"VISION ERROR: Error stopping camera: {e}")

    def is_point_in_quad(self, point, corners):
        """
        Checks if a point (x, y) is inside the quadrilateral defined by corners.
        Uses OpenCV's pointPolygonTest.
        """
        return cv2.pointPolygonTest(corners, point, False) >= 0

    def get_live_ball_position(self):
        """
        Captures a frame from the running camera, processes it, and returns (x, y).
        """
        if not self.is_running:
            print("Camera not running. Attempting to start...")
            self.start_camera()
            if not self.is_running:
                return None

        print("Capturing frame...")
        ball_coords = None

        try:
            # Capture from existing stream
            frame = self.picam2.capture_array()

            # Rotate 180 degrees to match physical camera orientation
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            # 2. Blur (Reduces noise)
            blurred_frame = cv2.GaussianBlur(frame, (7, 7), 0)

            # 3. Convert to HSV
            hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)

            # 4. Mask
            mask = cv2.inRange(hsv_frame, LOWER_WHITE, UPPER_WHITE)

            # 5. Morphological Operations
            morph_kernel = np.ones((7, 7), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, morph_kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, morph_kernel)

            # 6. Find Contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                if MIN_BALL_AREA < area < MAX_BALL_AREA:
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        
                        # Check if inside field boundaries
                        if self.is_point_in_quad((cX, cY), FIELD_CORNERS):
                            ball_coords = (cX, cY)
                            debug_color = (0, 255, 0) # Green for valid
                            status_text = f"Pos:{ball_coords} Area:{int(area)}"
                            print(f"Ball found at {ball_coords} (Area: {area})")
                        else:
                            debug_color = (0, 0, 255) # Red for out of bounds
                            status_text = f"OUT:{cX},{cY} Area:{int(area)}"
                            print(f"Ball ignored at {cX},{cY} (Out of bounds)")

                        # Draw Debug Info
                        cv2.drawContours(frame, [largest_contour], -1, debug_color, 2)
                        cv2.circle(frame, (cX, cY), 5, debug_color, -1)
                        if len(FIELD_CORNERS) > 0:
                            cv2.polylines(frame, [FIELD_CORNERS], True, (255, 0, 0), 2)

                        cv2.putText(
                            frame,
                            status_text,
                            (cX - 20, cY - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 255, 255),
                            2,
                        )
                else:
                    print(f"Object detected but too small (Area: {area})")
            else:
                print("No white objects found.")

            # Save image for verification
            cv2.imwrite("debug_view.jpg", frame)

        except Exception as e:
            print(f"VISION ERROR: {e}")

        return ball_coords


# global instance for easy import
vision_system_instance = VisionSystem()


def get_live_ball_position():
    """Wrapper for backward compatibility, uses the global instance."""
    return vision_system_instance.get_live_ball_position()
