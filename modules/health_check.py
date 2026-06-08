import sounddevice as sd

from config import config
from modules.iot import get_frame
from utils.groq_client import run_with_groq_client
from utils.logger import logger


class HealthCheckService:
    """
    Startup/runtime health checks for critical dependencies.
    """

    def run_startup_checks(self):
        return [
            self._check_camera(),
            self._check_microphone(),
            self._check_groq_api(),
        ]

    def run_runtime_checks(self):
        # Keep runtime checks lightweight to avoid long blocking recovery loops.
        return [
            self._check_camera(),
            self._check_groq_api(),
        ]

    def _check_camera(self):
        try:
            frame = get_frame()
            if frame is None:
                return self._failure(
                    name="camera",
                    message="Camera frame unavailable.",
                    spoken="Camera health check failed. Please check the camera connection.",
                    critical=False,
                )
            shape = getattr(frame, "shape", None)
            logger.info(f"Health check camera OK: shape={shape}")
            return self._success("camera", "Camera is available.")
        except Exception as error:
            return self._failure(
                name="camera",
                message=f"Camera exception: {error}",
                spoken="Camera health check failed due to an internal error.",
                critical=False,
            )

    def _check_microphone(self):
        try:
            input_device_index = sd.default.device[0]
            if input_device_index is None or int(input_device_index) < 0:
                return self._failure(
                    name="microphone",
                    message="No default input device configured.",
                    spoken="Microphone health check failed. No input device is configured.",
                    critical=True,
                )

            devices = sd.query_devices()
            device = devices[int(input_device_index)]
            if int(device.get("max_input_channels", 0)) < 1:
                return self._failure(
                    name="microphone",
                    message=f"Device has no input channels: {device.get('name', 'unknown')}",
                    spoken="Microphone health check failed. The selected device has no input channels.",
                    critical=True,
                )

            sample_rate = int(
                device.get("default_samplerate") or config.SAMPLE_RATE
            )
            recording = sd.rec(
                int(0.2 * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            _ = recording

            logger.info(f"Health check microphone OK: {device.get('name', 'unknown')}")
            return self._success("microphone", "Microphone is available.")
        except Exception as error:
            return self._failure(
                name="microphone",
                message=f"Microphone exception: {error}",
                spoken="Microphone health check failed. Please reconnect or select a working microphone.",
                critical=True,
            )

    def _check_groq_api(self):
        try:
            response = run_with_groq_client(
                lambda client: client.chat.completions.create(
                    model=config.GROQ_TEXT_MODEL,
                    messages=[{"role": "user", "content": "health check"}],
                    temperature=0,
                    max_tokens=5,
                )
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                return self._failure(
                    name="groq_api",
                    message="Groq API responded with empty completion.",
                    spoken="Groq API health check failed. I did not receive a valid response.",
                    critical=True,
                )

            logger.info("Health check Groq API OK.")
            return self._success("groq_api", "Groq API is reachable.")
        except Exception as error:
            return self._failure(
                name="groq_api",
                message=f"Groq API exception: {error}",
                spoken="Groq API health check failed. Please verify your keys and model settings.",
                critical=True,
            )

    @staticmethod
    def _success(name: str, message: str):
        return {
            "name": name,
            "ok": True,
            "critical": False,
            "message": message,
            "spoken": "",
        }

    @staticmethod
    def _failure(name: str, message: str, spoken: str, critical: bool):
        return {
            "name": name,
            "ok": False,
            "critical": critical,
            "message": message,
            "spoken": spoken,
        }


health_check_service = HealthCheckService()
