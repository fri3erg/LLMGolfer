# 🏌️‍♂️ LLMGolfer

> **Project for the Laboratory of Making Exam**
>
> This project demonstrates an autonomous system combining Computer Vision, AI (LLM), and Robotics.

**LLMGolfer** is an autonomous, AI-powered mini-golf robot. It uses **Computer Vision** to see the course, an **LLM (OpenAI GPT-4o)** to plan its shots and generate witty commentary, and a custom **Robotic Hardware** stack to aim and swing.

## Features

- **Brain:** Powered by OpenAI's GPT-4o. The AI acts as a professional golfer named "Chip," aiming based on visual feedback and learning from previous shots.
- **Vision:** Uses a Raspberry Pi Camera Module 3 with OpenCV to track the ball's position relative to the target.
- **Voice:** Real-time neural text-to-speech using **Piper TTS**. Chip trash-talks when he misses and celebrates when he wins.
- **Precision Hardware:**
  - **Stepper Motor:** Controls the aim angle (45° - 135°).
  - **Servo Motor:** Controls the swing power (0 - 100%).
  - **Linear Actuator:** Automatically resets the ball to the tee after a miss.

### The Course

Instead of a traditional hole, the target is a **Flag-Nail**. The objective is to hit the nail or stop the ball as close to it as possible ("Given" putt). The system calibrates by detecting this target and calculates accuracy based on distance to this point.

---

## Hardware Requirements

- **Raspberry Pi 5** (recommended for performance).
- **Pi Camera Module 3**.
- **Stepper Motor** + Driver (e.g., A4988/DRV8825).
- **Servo Motor** (High toque).
- **Linear Actuator** (12V).
- **Button** (for physical start/stop control).
- 3D Printed Parts (Chassis, Club Holder, Camera Mount).

### Pinout Configuration (Default)

| Component | Pin / Channel | Description |
| :--- | :--- | :--- |
| **Stepper Step** | GPIO 20 | Step signal |
| **Stepper Dir** | GPIO 21 | Direction signal |
| **Stepper Enable** | GPIO 22 | Enable signal (Active Low) |
| **Limit Switch** | GPIO 4 | Homing switch |
| **Servo** | GPIO 19 | PWM Chip 0, Channel 3 |
| **Linear Actuator** | GPIO 18 | PWM Chip 0, Channel 2 |
| **Start Button** | GPIO 16 | Physical control interface |

> Note: Pin assignments can be modified in `src/hardware_controller.py`.

---

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/LLMGolfer.git
    cd LLMGolfer
    ```

2. **Set up Virtual Environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies:**

    > **Warning:** `requirements.txt` may be incomplete. If you encounter `ModuleNotFoundError`, please install the missing package via pip.

    ```bash
    pip install -r requirements.txt
    ```

4. **Install Piper TTS (Voice Models):**
    Follow the official [Piper TTS instructions](https://github.com/rhasspy/piper) to install the binary and download the `en_US-lessac-medium` voice model to your local data directory.

5. **Environment Setup:**
    Create a `.env` file in the root directory:

    ```ini
    OPENAI_API_KEY=your_sk_key_here
    ```

---

## Usage

### 1. Manual Start

Run the main controller to start a game immediately:

```bash
python src/main_controller.py
```

### 2. Button Service (Production Mode)

The system is designed to run headless on a Raspberry Pi, managed by a systemd service (or similar process supervisor). The `button_manager.py` script acts as the interface, monitoring a physical button to toggle the game state.

```bash
python src/button_manager.py
```

- **Press:** Starts the game loop (if stopped) or Resets it (if crashed).
- **Press (while running):** Stops the game.

### Game Loop Workflow

1. **Calibration:** The bot detects the **flag-nail** position.
2. **Setup:** The bot resets the ball to the tee.
3. **Play:**
    - The AI analyzes the previous shot.
    - It decides on an **Aim Angle** and **Swing Force**.
    - It speaks a commentary line.
    - It takes the shot.
    - It waits for the ball to stop and checks the camera.
    - If it misses, it resets the ball and tries again.
    - If it hits the target (within threshold), it celebrates!

---

## Project Structure

- **`src/`**
  - `main_controller.py`: The orchestrator. Manages the game flow.
  - `llm_golfer.py`: Handles OpenAI API communication and prompt engineering.
  - `hardware_controller.py`: Low-level interface for GPIO and PWM control.
  - `vision_system.py`: OpenCV logic for ball detection and tracking.
  - `audio_manager.py`: Text-to-Speech logic using Piper.
  - `feedback_generator.py`: Translates vision data into natural language for the AI.

- **`raspberry_tests/`**
  - Contains individual test scripts (`test_servo.py`, `full_test.py`, etc.).
  - > **Note:** These tests may be outdated compared to the main source code. Use them as a reference for hardware verification but expect potential adjustments needed.

- **`report/`**: Contains the detailed project report (PDF).
- **`images/`**: Contains photos and videos of the project in action.

---

## License

[MIT License](LICENSE)
