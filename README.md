# PERSIGHT

PERSIGHT is a voice-first accessibility assistant for scene description, object identification, OCR, memory recall, navigation guidance, and SOS alerts.

## Architecture

The app is organized as a small service pipeline:

- `main.py` is the command loop and orchestration layer.
- `config.py` loads environment settings and command triggers.
- `modules/voice.py` handles speech output and voice input.
- `modules/scene.py` generates scene descriptions from camera frames.
- `modules/sensory.py` identifies objects and supports follow-up questions.
- `modules/ocr_service.py` extracts text from images.
- `modules/memory_recall.py` stores and recalls visual memories.
- `modules/navigation.py` provides camera-based navigation guidance.
- `modules/emergency.py` sends SOS messages through Twilio.
- `modules/health_check.py` validates camera, microphone, and Groq access at startup.
- `modules/iot.py` provides camera access helpers.
- `utils/groq_client.py` manages Groq client pooling.
- `utils/groq_vision.py` sends vision prompts to Groq.
- `utils/logger.py` configures application logging.

## Setup

### 1) Clone the repository

```bash
git clone https://github.com/srikanth-v05/PERSIGHT.git
cd PERSIGHT
```

### 2) Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
copy .env.example .env
```

### 5) Run the app

```bash
python main.py
```

## Environment file

The repository includes `.env.example` with the required and optional variables. At minimum, set a Groq API key. Twilio variables are only required if you want SOS messaging to work.

## Notes

- Camera and microphone access are required for the main features.
- Startup health checks will warn if a required device or API is unavailable.
- Local runtime files such as `.env`, logs, generated audio, and memory data are ignored by Git.
