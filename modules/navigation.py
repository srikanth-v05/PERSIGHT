import json
import re
import time

from config import config
from modules.iot import get_frame
from modules.voice import voice_service
from utils.groq_vision import analyze_frame
from utils.logger import logger


class NavigationService:
    """
    Vision-based path navigation assistant.

    Captures camera frames and speaks short movement instructions with
    obstacle warnings for left, right, forward, and stop actions.
    """

    def start_navigation(self):
        voice_service.speak(
            "Navigation mode started. I will guide you step by step."
        )
        voice_service.speak(
            "Say continue for the next update, or say stop navigation to end."
        )
        logger.info("Navigation mode started.")

        steps = 0
        last_instruction = ""

        while steps < config.NAVIGATION_MAX_STEPS:
            frame = get_frame()
            if frame is None:
                logger.error("Navigation: camera frame unavailable.")
                voice_service.speak("I cannot access the camera right now.")
                break

            nav_data = self._analyze_navigation(frame)
            instruction = self._build_instruction(nav_data)

            if instruction and instruction != last_instruction:
                voice_service.speak(instruction)
                last_instruction = instruction
            elif instruction:
                # Keep speech compact when the scene has not changed much.
                voice_service.speak("Same guidance. Continue carefully.")
            else:
                voice_service.speak("I could not read the path clearly. Move slowly.")

            steps += 1
            logger.info(f"Navigation step {steps}: {instruction}")

            if steps >= config.NAVIGATION_MAX_STEPS:
                voice_service.speak("Navigation session limit reached. Say navigate to start again.")
                break

            voice_service.speak("Say continue for next guidance or stop navigation to end.")
            command = (voice_service.get_voice_input() or "").strip().lower()

            if self._is_stop_command(command):
                voice_service.speak("Navigation stopped.")
                logger.info("Navigation mode stopped by user command.")
                return

            # Default path: continue even if command is empty or unrecognized.
            time.sleep(max(0.0, config.NAVIGATION_INTERVAL_SEC))

        logger.info("Navigation mode ended.")

    def _is_stop_command(self, command: str) -> bool:
        if not command:
            return False
        if any(trigger in command for trigger in config.NAVIGATION_STOP_TRIGGERS):
            return True
        if any(trigger in command for trigger in config.EXIT_TRIGGERS):
            return True
        return False

    def _analyze_navigation(self, frame) -> dict:
        prompt = (
            "You are a mobility navigation assistant for a visually impaired person. "
            "Analyze this camera frame and suggest the safest immediate movement. "
            "Return ONLY valid JSON, no markdown. Use this exact schema: "
            "{\"action\":\"forward|left|right|stop\","
            "\"instruction\":\"short spoken step\","
            "\"safe_path\":\"left|center|right|none\","
            "\"obstacles\":[{\"name\":\"object\",\"position\":\"left|center|right\","
            "\"distance\":\"near|medium|far\",\"risk\":\"low|medium|high\"}],"
            "\"confidence\":\"low|medium|high\"}. "
            "Rules: prioritize safety; if obstacle is close in center then action must be stop."
        )

        raw = analyze_frame(prompt, frame, max_tokens=320, temperature=0.1)
        if not raw:
            return {}
        parsed = self._parse_navigation_response(raw)
        return parsed

    def _parse_navigation_response(self, text: str) -> dict:
        # Prefer strict JSON parsing, then fallback to keyword extraction.
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if isinstance(data, dict):
                    return data
            except Exception:
                logger.warning("Navigation JSON parse failed. Using fallback parser.")

        fallback = {
            "action": "forward",
            "instruction": "Move forward slowly.",
            "safe_path": "center",
            "obstacles": [],
            "confidence": "low",
        }
        low = text.lower()
        if "stop" in low:
            fallback["action"] = "stop"
            fallback["instruction"] = "Stop now. Obstacle ahead."
        elif "left" in low:
            fallback["action"] = "left"
            fallback["instruction"] = "Move slightly to your left."
        elif "right" in low:
            fallback["action"] = "right"
            fallback["instruction"] = "Move slightly to your right."
        return fallback

    def _build_instruction(self, data: dict) -> str:
        if not data:
            return ""

        action = str(data.get("action", "forward")).lower().strip()
        safe_path = str(data.get("safe_path", "center")).lower().strip()
        base_instruction = str(data.get("instruction", "")).strip()
        obstacles = data.get("obstacles", [])

        if action not in ("forward", "left", "right", "stop"):
            action = "forward"

        if not base_instruction:
            if action == "stop":
                base_instruction = "Stop immediately."
            elif action == "left":
                base_instruction = "Move slightly to your left."
            elif action == "right":
                base_instruction = "Move slightly to your right."
            else:
                base_instruction = "Move forward slowly."

        warnings = []
        if isinstance(obstacles, list):
            for obstacle in obstacles[:2]:
                if not isinstance(obstacle, dict):
                    continue
                name = str(obstacle.get("name", "obstacle")).strip()
                position = str(obstacle.get("position", "ahead")).strip()
                distance = str(obstacle.get("distance", "near")).strip()
                risk = str(obstacle.get("risk", "medium")).strip().lower()
                if risk in ("high", "medium"):
                    warnings.append(f"{name} {position} {distance}.")

        if action != "stop" and safe_path in ("left", "right"):
            route_hint = f"Safer path is {safe_path}."
        elif action != "stop" and safe_path == "center":
            route_hint = "Center path looks clearer."
        else:
            route_hint = ""

        parts = [base_instruction]
        if route_hint:
            parts.append(route_hint)
        if warnings:
            parts.append("Obstacle warning. " + " ".join(warnings))

        final_text = " ".join(p for p in parts if p).strip()
        return final_text


navigation_service = NavigationService()
