
import cv2
import time
from typing import Optional
import numpy as np
import threading
from utils.logger import logger

class Camera:
    """
    Singleton class to manage camera access.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Camera, cls).__new__(cls)
            cls._instance.cap = None
            cls._instance._lock = threading.Lock()
        return cls._instance

    def get_frame(self, camera_index: int = 0) -> Optional[np.ndarray]:
        """
        Captures a single frame from the camera.
        Opens the camera if not already open, reads a frame, and releases it.
        For continuously streaming applications, strategy might need to change,
        but for snapshot based usage, this prevents resource locking.
        """
        try:
            with self._lock:
                cap = cv2.VideoCapture(camera_index)
                
                if not cap.isOpened():
                    logger.error(f"Cannot open camera with index {camera_index}")
                    return None

                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    logger.error("Failed to read frame from stream")
                    return None
                
                return frame

        except Exception as e:
            logger.error(f"Exception while fetching frame: {e}")
            return None

camera = Camera()

def get_frame():
    """Wrapper for backward compatibility or simple access."""
    return camera.get_frame()
