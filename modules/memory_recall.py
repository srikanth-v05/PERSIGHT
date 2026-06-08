import threading
import uuid
from datetime import datetime
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from config import config
from utils.logger import logger
from modules.iot import get_frame
from modules.voice import voice_service
from utils.groq_vision import analyze_frame
from utils.groq_client import run_with_groq_client


class MemoryRecallService:
    """
    RAG-based Memory Recall for visually impaired users.

    Background mode:
        Continuously captures frames in a thread, describes them using Groq Vision,
        and stores the description in ChromaDB.

    Recall mode:
        User asks a question -> semantic search in ChromaDB -> Groq synthesizes answer.
    """

    COLLECTION_NAME = "visual_memories"

    def __init__(self):
        # Use Chroma's built-in embedding function for broad compatibility.
        self._embedding_fn = DefaultEmbeddingFunction()

        # ChromaDB persistent client (local on-disk, no server needed)
        self._chroma = chromadb.PersistentClient(path=config.MEMORY_DB_PATH)
        self._collection = self._chroma.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._embedding_fn,
        )

        # Background capture thread
        self._stop_event = threading.Event()
        self._thread = None
        self._db_lock = threading.Lock()
        self._last_description = ""

    # ------------------------------------------------------------------ #
    #  Background Memory Capture                                           #
    # ------------------------------------------------------------------ #

    def start_background_capture(self):
        if self._thread and self._thread.is_alive():
            return
        logger.info("Starting background memory capture.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def is_background_capture_running(self):
        return bool(self._thread and self._thread.is_alive())

    def stop_background_capture(self):
        if not self._thread:
            return
        logger.info("Stopping background memory capture.")
        self._stop_event.set()
        timeout = max(2.0, float(config.MEMORY_CAPTURE_INTERVAL_SEC) + 5.0)
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            logger.warning("Background memory thread did not stop within timeout.")
        else:
            self._thread = None

    def _capture_loop(self):
        while not self._stop_event.is_set():
            try:
                frame = get_frame()
                if frame is None:
                    logger.warning("Background capture: could not access camera.")
                else:
                    description = self._describe_frame(frame)
                    if description:
                        self._store_description(description, source="background")
            except Exception as e:
                logger.error(f"Background capture error: {e}")

            self._stop_event.wait(config.MEMORY_CAPTURE_INTERVAL_SEC)

    # ------------------------------------------------------------------ #
    #  Save Memory (Manual)                                                #
    # ------------------------------------------------------------------ #

    def save_memory(self):
        """Capture an image, describe it, and store the description in ChromaDB."""
        try:
            frame = get_frame()
            if frame is None:
                logger.error("Could not fetch frame for memory save.")
                voice_service.speak("I couldn't access the camera.")
                return

            description = self._describe_frame(frame)
            if not description:
                voice_service.speak("I couldn't describe the scene.")
                return

            self._store_description(description, source="manual")
            logger.info(f"Memory saved: {description}")
            voice_service.speak(f"Memory saved. {description}")

        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            voice_service.speak("Sorry, I couldn't save the memory.")

    # ------------------------------------------------------------------ #
    #  Recall Memory                                                       #
    # ------------------------------------------------------------------ #

    def recall_memory(self):
        """Ask the user what they want to recall, search ChromaDB, and speak the result."""
        try:
            # 0. Check if any memories exist
            with self._db_lock:
                total = self._collection.count()
            if total == 0:
                voice_service.speak("You have no saved memories yet.")
                return

            # 1. Get the user's query
            voice_service.speak("What would you like to recall?")
            query = voice_service.get_voice_input()

            if not query:
                voice_service.speak("I didn't hear anything. Please try again.")
                return

            logger.info(f"Recall query: {query}")

            # 2. Semantic search
            n_results = min(config.MEMORY_MAX_RESULTS, total)
            with self._db_lock:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=n_results,
                )

            if not results["documents"] or not results["documents"][0]:
                voice_service.speak("I couldn't find any matching memories.")
                return

            # 3. Build context from retrieved memories
            memories_context = "\n".join(
                f"- [{(meta or {}).get('timestamp', 'unknown')}] {doc}"
                for doc, meta in zip(
                    results["documents"][0], results["metadatas"][0]
                )
            )

            # 4. Synthesize answer with Groq text model
            synthesis_prompt = (
                "You are a helpful assistant for a visually impaired person.\n"
                "Based on the following stored visual memories, answer the user's question.\n\n"
                f"Stored memories:\n{memories_context}\n\n"
                f"User's question: {query}\n\n"
                "Give a concise, spoken-friendly answer in 2-3 sentences. "
                "Do not use special symbols."
            )

            response = run_with_groq_client(
                lambda client: client.chat.completions.create(
                    model=config.GROQ_TEXT_MODEL,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    temperature=0.3,
                    max_tokens=220,
                )
            )
            answer_text = response.choices[0].message.content.strip()
            logger.info(f"Recall answer: {answer_text}")
            voice_service.speak(answer_text)

        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            voice_service.speak("Sorry, I couldn't recall that memory.")

    # ------------------------------------------------------------------ #
    #  Internal Helpers                                                    #
    # ------------------------------------------------------------------ #

    def _describe_frame(self, frame) -> str:
        prompt = (
            "Describe what you see in this image in detail. "
            "Include objects, their positions, colors, text if any, "
            "and any notable features. Keep it within 5 lines. "
            "Do not use special symbols."
        )
        logger.info("Generating scene description for memory...")
        description = analyze_frame(prompt, frame, max_tokens=220)
        return description.strip() if description else ""

    def _store_description(self, description: str, source: str):
        description = description.strip()
        if not description:
            return

        # Avoid storing identical consecutive descriptions
        if description == self._last_description:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc_id = str(uuid.uuid4())

        with self._db_lock:
            self._collection.add(
                documents=[description],
                metadatas=[{"timestamp": timestamp, "source": source}],
                ids=[doc_id],
            )
            self._last_description = description

        logger.info(f"Memory stored: {doc_id} at {timestamp} [{source}]")


memory_service = MemoryRecallService()
