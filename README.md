# PERSIGHT

PERSIGHT is a voice-first accessibility assistant built for scene understanding, object identification, OCR, memory recall, navigation guidance, and emergency SOS alerts.

## What it does

- Describes the current scene using the camera and vision models
- Identifies objects or items in hand with follow-up questions
- Reads text from documents and signs using OCR
- Saves and recalls visual memories
- Gives step-by-step navigation guidance
- Sends emergency SOS alerts with location details via Twilio
- Runs startup and runtime health checks for camera, microphone, and Groq connectivity

## Tech stack

- Python
- Groq for text and vision reasoning
- OpenCV and camera input
- `sounddevice` and `pyttsx3` for audio input/output
- ChromaDB for memory storage
- Twilio for SOS messages

## Requirements

- Python 3.10 or newer
- A working microphone
- A working camera
- A Groq API key
- Optional: Twilio credentials for SOS alerts

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/srikanth-v05/PERSIGHT.git
   cd PERSIGHT
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your secrets and settings.

## Environment variables

At minimum, set one of these:

```env
GROQ_API_KEY=your_key_here
# or
GROQ_API_KEYS=key1,key2
```

Optional Twilio variables for SOS:

```env
TWILIO_SID=your_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+10000000000
TWILIO_TO_NUMBER=+10000000000
```

Optional tuning variables:

```env
MEMORY_CAPTURE_INTERVAL_SEC=10
MEMORY_MAX_RESULTS=3
NAVIGATION_INTERVAL_SEC=1.5
NAVIGATION_MAX_STEPS=20
GROQ_TEXT_MODEL=llama-3.1-8b-instant
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
MEMORY_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Run

```bash
python main.py
```

After startup, speak a command such as:

- “describe scene”
- “read text”
- “save this”
- “recall memory”
- “navigate”
- “sos”
- “exit”

## Project structure

- `main.py` — application entry point and command loop
- `config.py` — environment-backed configuration
- `modules/` — voice, scene, sensory, OCR, memory, navigation, and emergency services
- `utils/` — logging and Groq helpers

## Notes

- The app expects camera and microphone access.
- Startup health checks will warn early if a required device or API is unavailable.
- `.env`, logs, generated audio, and local memory data are intentionally excluded from version control.
