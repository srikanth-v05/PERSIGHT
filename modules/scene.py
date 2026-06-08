
from utils.logger import logger
from modules.iot import get_frame
from utils.groq_vision import analyze_frame

class SceneService:
    def describe_scene(self) -> str:
        """
        Captures the scene description from the live feed using Groq Vision.
        """
        try:
            frame = get_frame()
            if frame is None:
                logger.error("Could not fetch frame for scene description.")
                return "I couldn't access the camera."

            prompt = (
                "You are a describing assistant. Describe everything within 3 lines. "
                "Return only the description and avoid special symbols."
            )

            logger.info("Generating scene description with Groq Vision...")
            description = analyze_frame(prompt, frame, max_tokens=180)
            if not description:
                return "Sorry, I couldn't describe the scene."
            logger.info(f"Scene Description: {description}")
            return description

        except Exception as e:
            logger.error(f"Error generating scene description: {e}")
            return "Sorry, I encountered an error describing the scene."

scene_service = SceneService()
