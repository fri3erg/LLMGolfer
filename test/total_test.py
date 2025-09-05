import time
import os
import gpiod

# =============================================================================
# --- MASTER CONFIGURATION ---
# =============================================================================

# -- Stepper Motor & Limit Switch --
STEP_PIN = 20
DIR_PIN = 21
LIMIT_SWITCH_PIN = 26
GPIO_CHIP = 'gpiochip4'
TOTAL_STEPS_FOR_180_DEGREES = 4000 # IMPORTANT: Calibrate this value for your setup!
HOMING_SPEED = 0.002
MOVE_SPEED = 0.001

# -- Servo Motor (The "Shooter") --
SERVO_PWM_CHIP = 0
SERVO_PWM_CHANNEL = 0 # GPIO 12 is PWM0 on pwmchip0
SERVO_PWM_FREQ = 50
SERVO_REST_POS_NS = 700 * 1000      # 700µs pulse
SERVO_MAX_SWING_NS = 2300 * 1000 # 2300µs pulse

# -- Linear Actuator --
ACTUATOR_IN1_PIN = 17
ACTUATOR_IN2_PIN = 27
ACTUATOR_PWM_CHIP = 0
ACTUATOR_PWM_CHANNEL = 1 # GPIO 13 is PWM1 on pwmchip0
ACTUATOR_PWM_FREQ = 1000

# =============================================================================
# --- GLOBAL VARIABLES & HANDLES ---
# =============================================================================
gpiod_chip = None

# Stepper
step_line = None
dir_line = None
limit_switch_line = None
current_stepper_position = 0 # Tracks position in steps from home

# Actuator
actuator_in1_line = None
actuator_in2_line = None


# =============================================================================
# --- LOW-LEVEL HARDWARE FUNCTIONS (PWM & GPIO) ---
# =============================================================================

# Refactored PWM functions to handle multiple channels
def pwm_export(chip, channel):
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/export", "w") as f:
            f.write(str(channel))
    except (IOError, FileNotFoundError):
        print(f"PWM channel {channel} on chip {chip} may already be exported.")

def pwm_unexport(chip, channel):
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/unexport", "w") as f:
            f.write(str(channel))
    except (IOError, FileNotFoundError):
        pass # Fail silently on cleanup

def pwm_set_period(chip, channel, freq):
    period_ns = int(1_000_000_000 / freq)
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/period", "w") as f:
        f.write(str(period_ns))

def pwm_set_duty_cycle(chip, channel, duty_cycle_ns):
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/duty_cycle", "w") as f:
        f.write(str(duty_cycle_ns))

def pwm_enable(chip, channel):
    with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/enable", "w") as f:
        f.write("1")

def pwm_disable(chip, channel):
    try:
        with open(f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/enable", "w") as f:
            f.write("0")
    except (IOError, FileNotFoundError):
        pass # Fail silently on cleanup

def setup_all():
    """Initializes all GPIO and PWM hardware."""
    global gpiod_chip, step_line, dir_line, limit_switch_line, actuator_in1_line, actuator_in2_line
    print("Setting up all hardware...")
    
    # --- gpiod Setup (Stepper, Limit Switch, Actuator Direction) ---
    gpiod_chip = gpiod.Chip(GPIO_CHIP)
    # Stepper
    step_line = gpiod_chip.get_line(STEP_PIN)
    dir_line = gpiod_chip.get_line(DIR_PIN)
    step_line.request(consumer="stepper_step", type=gpiod.LINE_REQ_DIR_OUT)
    dir_line.request(consumer="stepper_dir", type=gpiod.LINE_REQ_DIR_OUT)
    # Limit Switch
    limit_switch_line = gpiod_chip.get_line(LIMIT_SWITCH_PIN)
    limit_switch_line.request(consumer="limit_switch", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)
    # Actuator
    actuator_in1_line = gpiod_chip.get_line(ACTUATOR_IN1_PIN)
    actuator_in2_line = gpiod_chip.get_line(ACTUATOR_IN2_PIN)
    actuator_in1_line.request(consumer="actuator_in1", type=gpiod.LINE_REQ_DIR_OUT)
    actuator_in2_line.request(consumer="actuator_in2", type=gpiod.LINE_REQ_DIR_OUT)
    
    # --- PWM Setup (Servo and Actuator Speed) ---
    # Servo
    pwm_export(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
    time.sleep(0.1)
    pwm_set_period(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_PWM_FREQ)
    pwm_enable(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
    # Actuator
    pwm_export(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
    time.sleep(0.1)
    pwm_set_period(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, ACTUATOR_PWM_FREQ)
    pwm_enable(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)

    print("✅ Hardware setup complete.")

def cleanup_all():
    """Disables and releases all hardware resources."""
    print("Cleaning up all hardware...")
    # Stop motors
    pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, 0)
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(0)
    
    # Disable and unexport PWM
    pwm_disable(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
    pwm_unexport(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)
    pwm_disable(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
    pwm_unexport(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL)
    
    # Release gpiod lines
    if gpiod_chip:
        gpiod_chip.close()
    print("Cleanup complete.")

# =============================================================================
# --- HIGH-LEVEL ACTION FUNCTIONS ---
# =============================================================================

def home_stepper():
    """Homes the stepper motor to the left until the limit switch is hit."""
    global current_stepper_position
    print("Homing stepper motor to the far left...")
    dir_line.set_value(0) # 0 = Left/Counter-Clockwise for this setup
    while limit_switch_line.get_value() == 0:
        step_line.set_value(1)
        time.sleep(HOMING_SPEED)
        step_line.set_value(0)
        time.sleep(HOMING_SPEED)
    current_stepper_position = 0
    print("✅ Stepper homed. Position set to 0.")

def move_stepper(steps, direction, speed):
    """Moves the stepper motor a specific number of steps."""
    dir_line.set_value(direction)
    for _ in range(steps):
        step_line.set_value(1)
        time.sleep(speed)
        step_line.set_value(0)
        time.sleep(speed)

def move_to_angle(angle):
    """Moves the stepper to a position based on an angle from 0-180."""
    global current_stepper_position
    if not 0 <= angle <= 180:
        print("Error: Angle must be between 0 and 180.")
        return

    target_steps = int((angle / 180.0) * TOTAL_STEPS_FOR_180_DEGREES)
    steps_to_move = target_steps - current_stepper_position
    
    print(f"Moving to angle: {angle}° (target step: {target_steps})")
    
    if steps_to_move > 0:
        # Move Right (Clockwise)
        move_stepper(steps_to_move, 1, MOVE_SPEED)
    elif steps_to_move < 0:
        # Move Left (Counter-Clockwise)
        move_stepper(abs(steps_to_move), 0, MOVE_SPEED)
    else:
        print("Already at the target angle.")

    current_stepper_position = target_steps
    print(f"Move complete. Current position: {current_stepper_position} steps.")

def swing_servo(power):
    """Swings the servo with a given power (0-100) and returns to rest."""
    if not 0 <= power <= 100:
        print("Error: Power must be between 0 and 100.")
        return
        
    print(f"--- Performing servo swing with {power}% power ---")

    # 1. Ensure we are at the resting position
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_REST_POS_NS)
    time.sleep(1)

    # 2. Calculate the swing endpoint based on power
    swing_range_ns = SERVO_MAX_SWING_NS - SERVO_REST_POS_NS
    swing_endpoint_ns = int((power / 100.0) * swing_range_ns) + SERVO_REST_POS_NS
    
    # 3. Swing to the endpoint
    print(f"Swinging to {swing_endpoint_ns // 1000}µs...")
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, swing_endpoint_ns)
    time.sleep(0.5)

    # 4. Return to the resting position
    print("Returning to rest...")
    pwm_set_duty_cycle(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, SERVO_REST_POS_NS)
    time.sleep(1)
    print("✅ Servo swing complete.")

def cycle_actuator(extend_time, retract_time):
    """Extends the actuator at 100% speed, then retracts it."""
    print("--- Cycling the linear actuator ---")
    
    # Extend
    print(f"Extending actuator for {extend_time} seconds...")
    actuator_in1_line.set_value(1)
    actuator_in2_line.set_value(0)
    actuator_period_ns = int(1_000_000_000 / ACTUATOR_PWM_FREQ)
    pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, actuator_period_ns) # 100% duty cycle
    time.sleep(extend_time)
    
    # Retract
    print(f"Retracting actuator for {retract_time} seconds...")
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(1)
    time.sleep(retract_time)
    
    # Stop
    actuator_in1_line.set_value(0)
    actuator_in2_line.set_value(0)
    pwm_set_duty_cycle(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, 0)
    print("✅ Actuator cycle complete.")

# =============================================================================
# --- MAIN TEST SEQUENCE ---
# =============================================================================
if __name__ == "__main__":
    try:
        setup_all()

        print("\n--- ⛳ STARTING GOLF TEST ⛳ ---\n")
        
        # 1. Home the stepper to establish the zero point.
        home_stepper()
        time.sleep(1)
        
        # 2. Move to the middle position (90 degrees).
        move_to_angle(90)
        time.sleep(1)

        # 3. Perform a shot with 80% power.
        swing_servo(power=80)
        time.sleep(1)

        # 4. Wait for 5 seconds as requested.
        print("\nWaiting for 5 seconds...")
        time.sleep(5)
        
        # 5. Cycle the actuator (extend for 2s, retract for 2s).
        cycle_actuator(extend_time=2, retract_time=2)
        
        print("\n--- 🎉 GOLF TEST COMPLETE 🎉 ---")

    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
    finally:
        cleanup_all()