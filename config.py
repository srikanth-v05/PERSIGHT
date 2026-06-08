
import os
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

@dataclass
class Config:
    """Centralized configuration management."""
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_KEYS_RAW: str = os.getenv("GROQ_API_KEYS", "")
    GROQ_API_KEYS: list = field(default_factory=list)
    
    # Twilio Configuration
    TWILIO_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    TWILIO_TO_NUMBER: str = os.getenv("TWILIO_TO_NUMBER", "")

    # Audio Settings
    SAMPLE_RATE: int = 16000
    RECORDING_DURATION: int = 5
    AUDIO_FILENAME: str = "user_audio.wav"
    
    # Triggers
    SCENE_TRIGGERS: tuple = ("scene", "describe", "description", "seeing", "see")
    SENSORY_TRIGGERS: tuple = ("sensory", "search", "holding", "buy")
    SOS_TRIGGERS: tuple = ("sos", "emergency", "help")
    OCR_TRIGGERS: tuple = ("text", "ocr", "read", "extract", "recognize", "scan", "document")
    MEMORY_SAVE_TRIGGERS: tuple = ("remember", "save", "memorize", "store")
    MEMORY_RECALL_TRIGGERS: tuple = ("recall", "remember what", "where", "when did", "what was")
    NAVIGATION_TRIGGERS: tuple = ("navigate", "navigation", "path", "guide me", "walk mode")
    NAVIGATION_STOP_TRIGGERS: tuple = ("stop navigation", "stop guiding", "pause navigation", "end navigation")
    EXIT_TRIGGERS: tuple = ("exit", "stop", "bye")

    # Memory / RAG
    MEMORY_DB_PATH: str = "memory_db"
    MEMORY_EMBEDDING_MODEL: str = os.getenv("MEMORY_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    MEMORY_CAPTURE_INTERVAL_SEC: float = float(os.getenv("MEMORY_CAPTURE_INTERVAL_SEC", "10"))
    MEMORY_MAX_RESULTS: int = int(os.getenv("MEMORY_MAX_RESULTS", "3"))
    NAVIGATION_INTERVAL_SEC: float = float(os.getenv("NAVIGATION_INTERVAL_SEC", "1.5"))
    NAVIGATION_MAX_STEPS: int = int(os.getenv("NAVIGATION_MAX_STEPS", "20"))

    # Models
    WHISPER_MODEL: str = "whisper-large-v3"
    GROQ_TEXT_MODEL: str = os.getenv("GROQ_TEXT_MODEL", "llama-3.1-8b-instant")
    GROQ_VISION_MODEL: str = os.getenv(
        "GROQ_VISION_MODEL",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    )

    def __post_init__(self):
        # Parse comma-separated keys with whitespace trimming
        keys = []
        if self.GROQ_API_KEYS_RAW:
            keys = [k.strip() for k in self.GROQ_API_KEYS_RAW.split(",")]
        if not keys and self.GROQ_API_KEY:
            keys = [k.strip() for k in self.GROQ_API_KEY.split(",")]
        self.GROQ_API_KEYS = [k for k in keys if k]

    def validate(self):
        """Validates that necessary configuration is present."""
        missing = []
        if not self.GROQ_API_KEYS:
            missing.append("GROQ_API_KEY or GROQ_API_KEYS")
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

config = Config()
