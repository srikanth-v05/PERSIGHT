
from config import config
from utils.logger import logger
from modules.iot import get_frame
from modules.voice import voice_service
from utils.groq_vision import analyze_frame
from utils.groq_client import run_with_groq_client

class SensoryService:
    def sensory_search(self):
        """
        Captures an image and asks Groq Vision about the object held, including buying options.
        Returns the context (description) implementation.
        """
        try:
            frame = get_frame()
            if frame is None:
                logger.error("Could not fetch frame for sensory search.")
                voice_service.speak("I couldn't access the camera.")
                return None
            
            prompt = (
                "Tell me about the object I am holding. What is this? "
                "and tell where can I buy this suggest both online and offline solutions. "
                "Describe as much as possible within 3 lines. "
                "Also do not use symbols like eg:(#,* etc)"
            )
            
            logger.info("Generating sensory search response with Groq Vision...")
            context = analyze_frame(prompt, frame, max_tokens=220)
            if not context:
                voice_service.speak("I couldn't identify the object.")
                return None
            logger.info(f"Sensory Context: {context}")
            voice_service.speak(context)
            return context

        except Exception as e:
            logger.error(f"Error in sensory search: {e}")
            voice_service.speak("Something went wrong while identifying the object.")
            return None

    def handle_follow_up_queries(self, context: str):
        """
        Handles an interactive loop for follow-up questions based on the provided context.
        """
        if not context:
            return

        voice_service.speak("You can ask follow-up questions or say 'exit' to end.")
        
        while True:
            # 1. Listen for user input
            user_query = voice_service.get_voice_input()
            
            if not user_query:
                voice_service.speak("I didn't hear anything. Please try again.")
                continue

            # 2. Check for exit condition
            if any(term in user_query.lower() for term in config.EXIT_TRIGGERS):
                voice_service.speak("Exiting follow-up session.")
                logger.info("Exiting follow-up session.")
                break
            
            # 3. Generate answer
            logger.info(f"Processing follow-up: {user_query}")
            answer = self._generate_response_with_context(user_query, context)
            voice_service.speak(answer)

    def _generate_response_with_context(self, user_input: str, context: str) -> str:
        """Helper to ask a Groq text model a follow-up question."""
        try:
            combined_input = f"Context: {context}\nUser Question: {user_input}\nAnswer concisely."
            response = run_with_groq_client(
                lambda client: client.chat.completions.create(
                    model=config.GROQ_TEXT_MODEL,
                    messages=[{"role": "user", "content": combined_input}],
                    temperature=0.3,
                    max_tokens=180,
                )
            )
            answer = response.choices[0].message.content.strip()
            logger.info(f"Follow-up Answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error generating follow-up response: {e}")
            return "Sorry, I couldn't process that question."

sensory_service = SensoryService()
