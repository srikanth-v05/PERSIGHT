
from config import config
from utils.logger import logger
from modules.voice import voice_service
from modules.scene import scene_service
from modules.sensory import sensory_service
from modules.emergency import emergency_service
from modules.ocr_service import ocr_service
from modules.memory_recall import memory_service
from modules.navigation import navigation_service
from modules.health_check import health_check_service
import time


def _run_startup_health_checks():
    voice_service.speak("Running startup health checks.")
    checks = health_check_service.run_startup_checks()

    failures = []
    for check in checks:
        if check["ok"]:
            logger.info(f"Startup health check passed: {check['name']}")
        else:
            logger.warning(f"Startup health check failed: {check['name']} - {check['message']}")
            failures.append(check)

    for failure in failures:
        if failure["spoken"]:
            voice_service.speak(failure["spoken"])

    critical_failures = [check for check in failures if check["critical"]]
    if critical_failures:
        voice_service.speak("Critical startup checks failed. Please fix issues and restart.")
        logger.error("Critical startup health checks failed. Aborting startup.")
        return False

    if failures:
        voice_service.speak("Startup checks completed with warnings. Some features may be limited.")

    return True


def _attempt_runtime_recovery():
    logger.warning("Attempting runtime recovery for long-running stability.")

    try:
        memory_service.stop_background_capture()
    except Exception as error:
        logger.error(f"Recovery: failed to stop memory capture: {error}")

    try:
        memory_service.start_background_capture()
        logger.info("Recovery: background memory capture restarted.")
    except Exception as error:
        logger.error(f"Recovery: failed to restart memory capture: {error}")

    runtime_checks = health_check_service.run_runtime_checks()
    runtime_failures = [check for check in runtime_checks if not check["ok"]]
    for failure in runtime_failures:
        logger.warning(f"Runtime health warning: {failure['name']} - {failure['message']}")

    if runtime_failures:
        voice_service.speak("Recovery completed with warnings. Some services are still unavailable.")
    else:
        voice_service.speak("Recovery completed. All core services look healthy.")


def main():
    try:
        config.validate()
    except ValueError as e:
        logger.error(str(e))
        print(str(e))
        return

    logger.info("Blindkit Application Started")
    voice_service.speak("System initialized.")

    if not _run_startup_health_checks():
        return

    voice_service.speak("I am ready.")
    memory_service.start_background_capture()

    consecutive_errors = 0
    consecutive_empty_inputs = 0
    last_heartbeat = time.monotonic()

    try:
        while True:
            try:
                now = time.monotonic()
                if now - last_heartbeat >= 60:
                    logger.info("Heartbeat: main loop alive and running.")
                    last_heartbeat = now

                if not memory_service.is_background_capture_running():
                    logger.warning("Background memory capture stopped unexpectedly. Restarting.")
                    memory_service.start_background_capture()

                logger.info("Listening for command...")
                print("Listening...")

                user_input = voice_service.get_voice_input()

                if not user_input:
                    consecutive_empty_inputs += 1
                    logger.info("No input detected.")
                    if consecutive_empty_inputs in (3, 6):
                        voice_service.speak(
                            "I am not hearing clear input. Please speak louder or check your microphone."
                        )
                    continue

                consecutive_empty_inputs = 0
                user_input = user_input.lower()
                logger.info(f"User said: {user_input}")

                # 1. Exit
                if any(trigger in user_input for trigger in config.EXIT_TRIGGERS):
                    voice_service.speak("Goodbye.")
                    logger.info("Exiting application.")
                    break

                # 2. Scene Description
                elif any(trigger in user_input for trigger in config.SCENE_TRIGGERS):
                    voice_service.speak("Describing the scene.")
                    description = scene_service.describe_scene()
                    voice_service.speak(description)

                # 3. Sensory Search
                elif any(trigger in user_input for trigger in config.SENSORY_TRIGGERS):
                    voice_service.speak("Let me identify that for you.")
                    context = sensory_service.sensory_search()
                    if context:
                        sensory_service.handle_follow_up_queries(context)

                # 4. OCR
                elif any(trigger in user_input for trigger in config.OCR_TRIGGERS):
                    voice_service.speak("Reading text.")
                    ocr_service.extract_and_read_text()

                # 5. Memory Save
                elif any(trigger in user_input for trigger in config.MEMORY_SAVE_TRIGGERS):
                    voice_service.speak("Saving this to memory.")
                    memory_service.save_memory()

                # 6. Memory Recall
                elif any(trigger in user_input for trigger in config.MEMORY_RECALL_TRIGGERS):
                    voice_service.speak("Let me search your memories.")
                    memory_service.recall_memory()

                # 7. Navigation
                elif any(trigger in user_input for trigger in config.NAVIGATION_TRIGGERS):
                    voice_service.speak("Starting path navigation.")
                    memory_service.stop_background_capture()
                    try:
                        navigation_service.start_navigation()
                    finally:
                        memory_service.start_background_capture()

                # 8. SOS
                elif any(trigger in user_input for trigger in config.SOS_TRIGGERS):
                    voice_service.speak("Sending emergency alert.")
                    emergency_service.send_sos()

                else:
                    logger.info("Unknown command.")
                    voice_service.speak("I didn't understand the command. Please try again.")

                consecutive_errors = 0

            except KeyboardInterrupt:
                logger.info("Keyboard Interrupt. Exiting...")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.exception("An unexpected error occurred in the main loop.")
                if consecutive_errors >= 3:
                    logger.warning("Alert: repeated runtime errors detected.")
                    voice_service.speak("I detected repeated errors. Attempting recovery now.")
                    _attempt_runtime_recovery()
                    consecutive_errors = 0
                else:
                    voice_service.speak("An internal error occurred. Restarting listener.")

                # Small bounded backoff helps long-running stability.
                time.sleep(min(5, 1 + consecutive_errors))
    finally:
        try:
            memory_service.stop_background_capture()
        except Exception as error:
            logger.error(f"Failed to stop memory capture cleanly during shutdown: {error}")

if __name__ == "__main__":
    main()
