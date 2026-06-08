import base64
import cv2
from config import config
from utils.logger import logger
from utils.groq_client import run_with_groq_client


def _frame_to_data_url(frame) -> str:
    """Encode a BGR frame to a base64 data URL suitable for Groq Vision."""
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return ""
    encoded = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def analyze_frame(prompt: str, frame, max_tokens: int = 220, temperature: float = 0.2) -> str:
    """
    Send a frame + prompt to a Groq vision model and return the text response.
    """
    data_url = _frame_to_data_url(frame)
    if not data_url:
        logger.error("Failed to encode frame for vision request.")
        return ""

    try:
        response = run_with_groq_client(
            lambda client: client.chat.completions.create(
                model=config.GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq vision request failed: {e}")
        return ""
