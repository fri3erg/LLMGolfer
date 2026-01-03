# 🏌️‍♂️ S.I.S.I.F.O.

> **Sistema Intelligente di Swing Iterativo a Feedback Ostinato**
>
> *Project for the Laboratory of Making Exam*

**S.I.S.I.F.O.** is an autonomous, AI-powered mini-golf robot built with reclaimed materials and advanced electronics. Inspired by the Greek myth of Sisyphus, the robot "obstinately" hits and retries shots, learning from its failures through a complex inner monologue.

[**Watch the project in action on YouTube**](https://youtu.be/RGlZ7kFjT_A?si=QZfmthuxUeG2y_cD)

---

## Features

- **Inner Monologue (Brain):** Powered by OpenAI's GPT-4o. The AI acts as a professional golfer named "Chip," receiving sensory data (ball position, target distance) and reasoning "out loud" about its strategy, doubts, and results.
- **Vision:** Uses a Raspberry Pi Camera Module 3 with OpenCV to track the ball's position. The environment is optimized with high-contrast elements (dark brown wood, emerald emerald tablecloth, white ball) for reliable detection.
- **Voice:** Real-time neural text-to-speech using **Piper TTS**. Chip provides sarcastic commentary, celebrates partial successes, and laments failures.
- **Iterative Learning:** Unlike deterministic robots, S.I.S.I.F.O. embraces irregularities and learns through iteration rather than perfect physical modeling.

## Hardware Stack

- **Controller:** Raspberry Pi 5 (Headless).
- **Vision:** Pi Camera Module 3.
- **Precision Mechanics:**
  - **Stepper Motor (Nema 17):** Controls the aim angle via a custom "C" shaped wooden support.
  - **Servo Motor (5kg):** Executes the swing. Optimized for low-friction surfaces like the smeraldo tablecloth.
  - **Linear Actuator (12V):** Tilts the entire platform to approximately 25 degrees to gravitically reset the ball to the tee.
- **Power Management:**
  - 24V 10A PSU.
  - XL4015 DC-DC Step-downs for 5.5V (Servo) and 12V (Actuator).
  - DRV8825 Stepper Driver & L298N Dual H-Bridge for the actuator.

### Pinout Configuration (Default)

| Component | Pin / Channel | Description |
| :--- | :--- | :--- |
| **Stepper Step** | GPIO 20 | Step signal |
| **Stepper Dir** | GPIO 21 | Direction signal |
| **Stepper Enable** | GPIO 22 | Enable signal (Active Low) |
| **Limit Switch** | GPIO 4 | Homing switch |
| **Servo** | GPIO 19 | PWM Chip 0, Channel 3 |
| **Linear Actuator** | GPIO 18 | PWM Chip 0, Channel 2 |
| **Start Button** | GPIO 16 | Physical control interface (glued for easy access) |

---

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/fri3erg/S.I.S.I.F.O..git
    cd S.I.S.I.F.O.
    ```

2. **Set up Virtual Environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Install Piper TTS (Voice Models):**
    Install [Piper TTS](https://github.com/rhasspy/piper) and download the `en_US-lessac-medium` voice model.

5. **Environment Setup:**
    Create a `.env` file:

    ```ini
    OPENAI_API_KEY=your_sk_key_here
    ```

---

## Usage

### 1. Manual Start

```bash
python src/main_controller.py
```

### 2. Physical Button (Production)

The system is designed to run headless. The physical button allows for:

- **Press:** Start or Reset (if crashed).
- **Long Press/Running:** Stop.

### The Game Loop

1. **Calibration:** Detects the **Flag-Nail** target.
2. **Reset:** Linear actuator inclines the platform to return the ball.
3. **Reasoning:** The LLM analyzes the situation and decides on angle/force.
4. **Action:** Robot speaks, aims, and swings.
5. **Feedback:** System observes the outcome and loop restarts until success.

---

## Project Structure

- **`src/`**: Core logic (Main controller, LLM integration, Hardware, Vision, Audio).
- **`report/`**: Contains `relazione_sisifo.tex` documenting the construction process and engineering challenges.
- **`images/`**: Photos and diagrams (Wiring, Blueprints, Construction details).
- **`raspberry_tests/`**: Individual hardware test scripts.

---

## License

MIT License
