
from utils.logger import logger
from modules.iot import get_frame
from modules.voice import voice_service
from utils.groq_vision import analyze_frame

class OCRService:
    def extract_and_read_text(self) -> str:
        """
        Captures a frame, extracts text using Groq Vision, and reads it aloud.
        """
        try:
            frame = get_frame()
            if frame is None:
                logger.error("Could not fetch frame for OCR.")
                voice_service.speak("I couldn't access the camera.")
                return "Error: No frame"
            
            prompt = "You are an OCR assistant. Extract all readable text from this image and return only the text. No description, no labels, no greetings."
            
            logger.info("Extracting text via Groq Vision OCR...")
            extracted_text = analyze_frame(prompt, frame, max_tokens=300)
            logger.info(f"OCR Extracted: {extracted_text}")
            
            if extracted_text:
                voice_service.speak(extracted_text)
            else:
                voice_service.speak("No text detected.")
                
            return extracted_text

        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            voice_service.speak("An error occurred while reading text.")
            return "Error in OCR"

ocr_service = OCRService()
