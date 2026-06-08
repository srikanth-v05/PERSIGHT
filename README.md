# PERSIGHT

PERSIGHT is a voice-first accessibility assistant that helps with scene description, object identification, OCR, memory recall, navigation guidance, and emergency SOS alerts.

## Features

- Describe scenes using the camera and vision models
- Identify objects with conversational follow-up
- Read text from documents, signs, and labels
- Save and recall visual memories
- Guide navigation with camera-based instructions
- Send SOS alerts with location details through Twilio
- Run startup health checks for camera, microphone, and Groq access

## Architecture

PERSIGHT is organized as a lightweight service pipeline:

| Component | Responsibility |
| --- | --- |
| `main.py` | Application entry point and command loop |
| `config.py` | Loads environment settings and command triggers |
| `modules/voice.py` | Handles speech output and voice input |
| `modules/scene.py` | Generates scene descriptions from camera frames |
| `modules/sensory.py` | Identifies objects and supports follow-up questions |
| `modules/ocr_service.py` | Extracts text from images |
| `modules/memory_recall.py` | Stores and recalls visual memories |
| `modules/navigation.py` | Provides camera-based navigation guidance |
| `modules/emergency.py` | Sends SOS messages through Twilio |
| `modules/health_check.py` | Validates camera, microphone, and Groq access |
| `modules/iot.py` | Provides camera access helpers |
| `utils/groq_client.py` | Manages Groq client pooling |
| `utils/groq_vision.py` | Sends vision prompts to Groq |
| `utils/logger.py` | Configures application logging |

## Tech Stack

- Python
- Groq for text and vision reasoning
- OpenCV for camera access
- `sounddevice` and `pyttsx3` for audio input/output
- ChromaDB for memory storage
- Twilio for SOS messaging

## Prerequisites

- Python 3.10 or newer
- A working microphone
- A working camera
- A Groq API key
- Optional: Twilio credentials for SOS alerts

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/srikanth-v05/PERSIGHT.git
cd PERSIGHT
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your values:

```bash
copy .env.example .env
```

## Environment Variables

At minimum, set a Groq API key. Twilio variables are only required if you want SOS messaging to work.

| Variable | Required | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Primary Groq API key |
| `GROQ_API_KEYS` | No | Comma-separated fallback Groq keys |
| `TWILIO_SID` | No | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | No | Twilio auth token |
| `TWILIO_FROM_NUMBER` | No | Twilio sender number |
| `TWILIO_TO_NUMBER` | No | Emergency destination number |
| `MEMORY_EMBEDDING_MODEL` | No | Embedding model for memory storage |
| `MEMORY_CAPTURE_INTERVAL_SEC` | No | Interval between background memory captures |
| `MEMORY_MAX_RESULTS` | No | Number of memory results returned |
| `NAVIGATION_INTERVAL_SEC` | No | Delay between navigation steps |
| `NAVIGATION_MAX_STEPS` | No | Maximum navigation loop steps |
| `GROQ_TEXT_MODEL` | No | Model used for text reasoning |
| `GROQ_VISION_MODEL` | No | Model used for vision tasks |

## Run

```bash
python main.py
```

## Example Voice Commands

- `describe scene`
- `read text`
- `save this`
- `recall memory`
- `navigate`
- `sos`
- `exit`

## Project Structure

```text
.
|-- main.py
|-- config.py
|-- modules/
|-- utils/
|-- requirements.txt
|-- README.md
`-- .env.example
```

## Notes

- Keep secrets in `.env` and never commit them.
- Camera and microphone access are required for the main features.
- Startup health checks warn early if a required device or API is unavailable.

## Troubleshooting

- If startup fails, verify your `GROQ_API_KEY` and device access.
- If voice input is not working, check microphone permissions and system input selection.
- If SOS alerts fail, confirm the Twilio credentials and destination number.
