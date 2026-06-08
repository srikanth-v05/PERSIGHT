
import requests
from twilio.rest import Client
from config import config
from utils.logger import logger
from modules.voice import voice_service

class EmergencyService:
    def __init__(self):
        try:
            self.client = Client(config.TWILIO_SID, config.TWILIO_AUTH_TOKEN)
        except Exception as e:
            logger.error(f"Twilio client initialization failed: {e}")
            self.client = None

    def get_location(self) -> str:
        """Fetches current location based on IP."""
        try:
            response = requests.get("https://ipinfo.io/json", timeout=10)
            data = response.json()
            loc = data.get("loc", "Unknown")
            city = data.get("city", "Unknown city")
            region = data.get("region", "Unknown region")
            country = data.get("country", "Unknown country")
            
            maps_link = ""
            if loc != "Unknown":
                maps_link = f"https://www.google.com/maps?q={loc}"
                
            return f"{city}, {region}, {country}\nLocation: {loc}\nMaps: {maps_link}"
        except Exception as e:
            logger.error(f"Failed to get location: {e}")
            return "Location unavailable"

    def send_sos(self):
        """Sends an SOS message via Twilio."""
        if not self.client:
            logger.error("Cannot send SOS: Twilio client not initialized.")
            voice_service.speak("SOS service is not available.")
            return

        try:
            location_info = self.get_location()
            message_body = f"SOS Alert! Please send help.\n{location_info}"
            
            message = self.client.messages.create(
                from_=config.TWILIO_FROM_NUMBER,
                body=message_body,
                to=config.TWILIO_TO_NUMBER
            )
            logger.info(f"SOS sent successfully. SID: {message.sid}")
            voice_service.speak("SOS message sent successfully.")
            return message.sid
        except Exception as e:
            logger.error(f"Failed to send SOS: {e}")
            voice_service.speak("Failed to send SOS message.")
            return None

emergency_service = EmergencyService()
