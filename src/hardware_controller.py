# hardware_controller.py

import time

import sys

import numpy as np  # <--- THIS WAS MISSING

import os

import gpiod



# =============================================================================

# --- MASTER CONFIGURATION ---

# =============================================================================



# -- Stepper Motor --

# We now use the FULL PATH to avoid "File not found" errors

GPIO_CHIP_PATH = '/dev/gpiochip4' 



STEP_PIN = 20

DIR_PIN = 21

LIMIT_SWITCH_PIN = 4

ENABLE_PIN = 22         

TOTAL_STEPS_FOR_180_DEGREES = 300



# -- Speeds --

HOMING_SPEED = 0.002

MOVE_SPEED = 0.001



# -- Servo Motor --

SERVO_PWM_CHIP = 0      

SERVO_PWM_CHANNEL = 0

SERVO_PWM_FREQ = 50

SERVO_REST_POS_NS = 1100 * 1000   

SERVO_MAX_SWING_NS = 1900 * 1000  



# -- Linear Actuator --

ACTUATOR_PWM_CHIP = 0   

ACTUATOR_PWM_CHANNEL = 1

ACTUATOR_PWM_FREQ = 1000



# -- Directions --

CLOCKWISE = 1

COUNTER_CLOCKWISE = 0



# =============================================================================

# --- HANDLES ---

# =============================================================================

gpiod_chip = None

step_line, dir_line, limit_switch_line, enable_line = None, None, None, None

current_stepper_position = 0



# =============================================================================

# --- LOW LEVEL FUNCTIONS ---

# =============================================================================



def pwm_write(chip, channel, file, value):

    """Safely writes to a PWM file."""

    path = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}/{file}"

    try:

        with open(path, "w") as f: 

            f.write(str(value))

    except Exception as e:

        # Only print warning if the file *should* exist (i.e. setup passed)

        # We suppress errors during cleanup of a failed run

        pass



def pwm_export(chip, channel):

    """Exports a PWM channel and WAITS for it to appear."""

    export_path = f"/sys/class/pwm/pwmchip{chip}/export"

    pwm_dir = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}"

    

    if os.path.exists(pwm_dir):

        return # Already exported

        

    try:

        with open(export_path, "w") as f: 

            f.write(str(channel))

    except (IOError, OSError):

        # Device likely busy or already exported

        pass

    

    # CRITICAL: Wait for OS to create the files

    for _ in range(10):

        if os.path.exists(pwm_dir): return

        time.sleep(0.1)

    print(f"⚠️ PWM Export warning: {pwm_dir} did not appear quickly.")



def pwm_unexport(chip, channel):

    try:

        with open(f"/sys/class/pwm/pwmchip{chip}/unexport", "w") as f: 

            f.write(str(channel))

    except: pass



def setup_all():

    global gpiod_chip, step_line, dir_line, limit_switch_line, enable_line

    

    print(f"🔧 Hardware: Attempting to open GPIO chip...")

    

    # 1. Try the configured path first

    target_chip = GPIO_CHIP_PATH

    if not os.path.exists(target_chip):

        print(f"⚠️ Warning: {target_chip} not found. Searching for alternatives...")

        # Fallback strategy: Check 0 to 5

        for i in range(6):

            if os.path.exists(f"/dev/gpiochip{i}"):

                target_chip = f"/dev/gpiochip{i}"

                break

    

    print(f"🔧 Hardware: Using {target_chip}")

    

    try:

        gpiod_chip = gpiod.Chip(target_chip)

    except Exception as e:

        print(f"❌ FATAL: Could not open {target_chip}. Error: {e}")

        print("💡 TIP: Try running: pip uninstall gpiod (in venv) to use system lib.")

        raise e



    print("🔧 Hardware: Configuring Lines...")

    try:

        step_line = gpiod_chip.get_line(STEP_PIN)

        dir_line = gpiod_chip.get_line(DIR_PIN)

        limit_switch_line = gpiod_chip.get_line(LIMIT_SWITCH_PIN)

        enable_line = gpiod_chip.get_line(ENABLE_PIN)

        

        step_line.request(consumer="stepper", type=gpiod.LINE_REQ_DIR_OUT)

        dir_line.request(consumer="stepper", type=gpiod.LINE_REQ_DIR_OUT)

        enable_line.request(consumer="stepper", type=gpiod.LINE_REQ_DIR_OUT)

        limit_switch_line.request(consumer="limit", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)

        

        enable_line.set_value(1) # Disable motor

    except Exception as e:

        print(f"❌ FATAL: Pin config failed. Check Pin numbers. Error: {e}")

        raise e



    print("🔧 Hardware: Configuring PWM...")

    for channel in [SERVO_PWM_CHANNEL, ACTUATOR_PWM_CHANNEL]:

        pwm_export(SERVO_PWM_CHIP, channel)

        time.sleep(0.2) # Extra safety wait

        

        period = int(1_000_000_000 / (SERVO_PWM_FREQ if channel == 0 else ACTUATOR_PWM_FREQ))

        pwm_write(SERVO_PWM_CHIP, channel, "period", period)

        pwm_write(SERVO_PWM_CHIP, channel, "enable", "1")

    

    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)

    print("✅ Hardware: Setup complete.")



def cleanup_all():

    print("🧹 Hardware: Cleaning up...")

    try:

        if enable_line: enable_line.set_value(1) 

        

        # Turn off PWM (Suppress errors if they weren't setup)

        pwm_write(SERVO_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "duty_cycle", 0)

        pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)

        time.sleep(0.5)

        pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "enable", "0")

        pwm_write(SERVO_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "enable", "0")

        

        pwm_unexport(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL)

        pwm_unexport(SERVO_PWM_CHIP, ACTUATOR_PWM_CHANNEL)

        

        if gpiod_chip: gpiod_chip.close()

    except Exception as e: 

        print(f"Cleanup Warning: {e}")



def enable_motor():

    if enable_line:

        enable_line.set_value(0)

        time.sleep(0.01)



def disable_motor():

    if enable_line:

        enable_line.set_value(1)



# =============================================================================

# --- MOVEMENT ---

# =============================================================================



def move_stepper_raw(steps, direction):

    dir_line.set_value(direction)

    for _ in range(steps):

        step_line.set_value(1)

        time.sleep(MOVE_SPEED)

        step_line.set_value(0)

        time.sleep(MOVE_SPEED)



def home_stepper():

    global current_stepper_position

    print("🏠 Hardware: Homing...")

    enable_motor()

    dir_line.set_value(COUNTER_CLOCKWISE)

    

    while limit_switch_line.get_value() == 1:

        step_line.set_value(1)

        time.sleep(HOMING_SPEED)

        step_line.set_value(0)

        time.sleep(HOMING_SPEED)

    

    time.sleep(0.1)

    dir_line.set_value(CLOCKWISE)

    for _ in range(10):

        step_line.set_value(1)

        time.sleep(HOMING_SPEED)

        step_line.set_value(0)

        time.sleep(HOMING_SPEED)

        

    current_stepper_position = 0

    disable_motor()

    print("✅ Hardware: Homed.")



def map_angle_to_steps_non_linear(angle):

    exponent = 1.5

    normalized_input = (angle / 90.0) - 1.0

    sign = np.sign(normalized_input)

    eased_output = sign * (abs(normalized_input) ** exponent)

    target_steps = (eased_output + 1.0) / 2.0 * TOTAL_STEPS_FOR_180_DEGREES

    return int(TOTAL_STEPS_FOR_180_DEGREES - target_steps)



def set_stepper_angle(angle):

    global current_stepper_position

    target_step = map_angle_to_steps_non_linear(angle)

    target_step = max(0, min(TOTAL_STEPS_FOR_180_DEGREES, target_step))

    

    diff = target_step - current_stepper_position

    if diff == 0: return



    enable_motor()

    direction = CLOCKWISE if diff > 0 else COUNTER_CLOCKWISE

    move_stepper_raw(abs(diff), direction)

    disable_motor()

    current_stepper_position = target_step

    print(f"📐 Stepper: Moved to {angle}° (Step {target_step})")



def swing_club(power_percent):

    print(f"🏌️ Hardware: Swinging at {power_percent}%...")

    swing_range = SERVO_MAX_SWING_NS - SERVO_REST_POS_NS

    target_ns = int((power_percent / 100.0) * swing_range) + SERVO_REST_POS_NS

    

    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", target_ns)

    time.sleep(0.5)

    pwm_write(SERVO_PWM_CHIP, SERVO_PWM_CHANNEL, "duty_cycle", SERVO_REST_POS_NS)

    time.sleep(1.0)



def reset_ball_actuator():

    print("♻️ Hardware: Resetting ball...")

    # Defensive: Try to get lines if global failed, but usually redundant now

    try:

        l1 = gpiod_chip.get_line(17)

        l2 = gpiod_chip.get_line(27)

        l1.request(consumer="act", type=gpiod.LINE_REQ_DIR_OUT)

        l2.request(consumer="act", type=gpiod.LINE_REQ_DIR_OUT)

    except:

        # Lines likely already requested in setup_all, proceed using globals

        # Note: This snippet assumes you might want to grab them dynamically, 

        # but strictly we should use the ones from setup_all. 

        # For now, we rely on setup_all being successful.

        pass



    # Direct usage of handles from setup_all would be cleaner, but let's assume

    # the caller wants to re-request.

    # Actually, better to use the global gpiod logic:

    # We will assume user calls this ONLY after setup_all.

    

    # Re-grabbing lines for local scope safety in this specific function style

    # (Matches your working test file logic)

    line1 = gpiod_chip.get_line(17)

    line2 = gpiod_chip.get_line(27)

    

    # We check if they are free; if not, we assume we own them.

    try: line1.request(consumer="act", type=gpiod.LINE_REQ_DIR_OUT)

    except: pass

    try: line2.request(consumer="act", type=gpiod.LINE_REQ_DIR_OUT)

    except: pass



    period = int(1_000_000_000 / 1000)

    pwm_write(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "duty_cycle", period)

    

    line1.set_value(1)

    line2.set_value(0)

    time.sleep(20)

    

    line1.set_value(0)

    line2.set_value(1)

    time.sleep(20)

    

    line1.set_value(0)

    line2.set_value(0)

    pwm_write(ACTUATOR_PWM_CHIP, ACTUATOR_PWM_CHANNEL, "duty_cycle", 0)

