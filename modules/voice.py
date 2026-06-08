
import os
import pyttsx3
import sounddevice as sd
from scipy.io.wavfile import write
import warnings
from config import config
from utils.logger import logger
from utils.groq_client import run_with_groq_client

warnings.simplefilter("ignore", category=FutureWarning)

class VoiceService:
    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.duration = config.RECORDING_DURATION
        self.audio_filename = config.AUDIO_FILENAME
        self._engine = None

    # Engine property removed in favor of local instantiation for stability

    def clean_text(self, text: str) -> str:
        """Removes markdown and special characters for better TTS."""
        import re
        # Remove asterisks, hashes, etc.
        text = re.sub(r'[*#_`]', '', text)
        return text.strip()

    def speak(self, text: str):
        """Convert text to speech."""
        if not text:
            return
        
        try:
            cleaned_text = self.clean_text(text)
            logger.info(f"Speaking: {cleaned_text}")
            print(f"Speaking: {cleaned_text}")
            
            # Re-initialize engine to avoid loop issues
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(cleaned_text)
            engine.runAndWait()
            # engine.stop() is not needed if we just let it finish
        except Exception as e:
            logger.error(f"Error in TTS: {e}")

    def get_voice_input(self) -> str:
        """Records audio and transcribes it using Groq."""
        try:
            logger.info("Recording audio...")
            audio = sd.rec(
                int(self.duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1, 
                dtype="int16"
            )
            sd.wait()
            write(self.audio_filename, self.sample_rate, audio)
            logger.info(f"Recording saved to {self.audio_filename}")

            return self._transcribe_audio()
        except Exception as e:
            logger.error(f"Error recording or processing audio: {e}")
            return ""

    def _transcribe_audio(self) -> str:
        """Internal method to send audio to Groq for transcription."""
        if not os.path.exists(self.audio_filename):
            logger.error("Audio file not found.")
            return ""

        try:
            with open(self.audio_filename, "rb") as audio_file:
                audio_bytes = audio_file.read()
            transcription = run_with_groq_client(
                lambda client: client.audio.transcriptions.create(
                    file=(self.audio_filename, audio_bytes),
                    model=config.WHISPER_MODEL,
                )
            )
            text = transcription.text.strip()
            logger.info(f"Transcribed text: {text}")
            return text
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""

voice_service = VoiceService()
