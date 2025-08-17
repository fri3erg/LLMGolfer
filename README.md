# Autonomous Mini Golf Simulator: An LLM-Powered Golfer 🤖⛳

This project is an ambitious and innovative endeavor to create a miniature golf simulator where a Large Language Model (LLM) acts as the "golfer." The system leverages a combination of electronics, mechanical engineering, computer vision, and AI to demonstrate an autonomous, learning agent in a physical environment.

The core idea is to have the LLM make decisions on shot direction and force, receive visual feedback on the ball's outcome, and then adjust its strategy for subsequent shots. A unique and fun element is the LLM providing real-time commentary on its performance.

---

## Key Components

The project consists of two main, physically separate units.

### 1. The "Robot Golfer" (Main Contraption)

This is the active part, housing all the intelligence and motion systems.

* **Raspberry Pi 5 (The Brain):** Chosen for its processing power, essential for Computer Vision and managing API calls to the LLM.
* **Linear Positioning System (1-Axis Rail):** A **NEMA 17 Stepper Motor** with a **DRV8825 Driver** moves the golf club head precisely left and right along a linear rail, providing shot aiming.
* **Striking Mechanism:** A **High-Torque Digital Metal Gear Servo** (15-20 kg-cm+) swings the golf club head to strike the ball. Its rotation speed directly controls the shot force.
* **Computer Vision System:** A **Raspberry Pi Camera Module 3** captures high-resolution images of the golf course to detect the ball's final position.
* **Audio Output:** A speaker to play the LLM's commentary.
* **Power Management:** A single **24V DC, 10A-15A Switching Power Supply** powers the entire system. Two DC-DC Step-Down Buck Converters step down the voltage: one for the Raspberry Pi (to 5.1V) and one for the servo (to 5V/6V).
* **Ball Reset System:** A fast, low-force **Linear Actuator** controlled by an H-Bridge Motor Driver tilts the entire playing surface to return the ball to the start.

### 2. The "Green" (Playing Surface)

This is a passive, independent physical component.

* A flat, rigid platform with a grass surface.
* It has a hole as the target for the golf ball.
* It features a **tiltable design** that allows the linear actuator to tip it, resetting the game.

---

## Project Logic & Workflow

The system operates on a closed-loop feedback system, allowing the LLM to learn and adapt.

1. **Initial Calibration:** The user manually places the golf ball into the hole. The camera detects the hole's precise coordinates, saving them as the target.
2. **Game Loop:**
    * **Ball Reset:** The linear actuator tilts the Green, causing the ball to roll back to the starting point.
    * **LLM Decision:** The Raspberry Pi sends the current game state (e.g., ball position relative to the hole) to the LLM via an API.
    * **LLM Command:** The LLM, acting as the golfer, decides the next shot's lateral aim and strike force. These commands are sent back to the Pi.
    * **Shot Execution:** The Pi translates the LLM's commands into precise movements for the stepper motor (aim) and the servo (force). The club then hits the ball.
    * **Real-time Commentary:** Immediately after the shot, the LLM generates a commentary based on the outcome, which is played through the speaker.
    * **Visual Feedback:** The computer vision system acquires a new photo to determine the ball's new resting position, providing the feedback for the next decision cycle.

---

## Key Technical Challenges

* **Precise Mechanical Assembly:** Building the linear rail and tilt mechanism accurately is crucial for consistent performance.
* **Motor Control:** Fine-tuning the stepper motor for positioning and the servo for speed-controlled impact.
* **Computer Vision:** Robustly detecting the golf ball's position in images and accurately converting pixel coordinates to real-world measurements.
* **LLM Integration & Prompt Engineering:** Crafting effective prompts for the LLM to interpret physical feedback and make intelligent, improving decisions.
* **Power Management:** Designing a stable and safe power distribution system for multiple components with varying power needs.

---

## Getting Started

Future sections could include details on setting up the environment, code structure, and assembly instructions.
