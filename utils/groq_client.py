import threading
from groq import Groq
from config import config
from utils.logger import logger

_pool_lock = threading.Lock()
_pool = None


class _GroqClientPool:
    def __init__(self, keys: list[str]):
        if not keys:
            raise ValueError("No GROQ API keys provided.")
        self._clients = [Groq(api_key=key) for key in keys]
        self._lock = threading.Lock()
        self._index = 0

    def next_client(self) -> Groq:
        with self._lock:
            client = self._clients[self._index]
            self._index = (self._index + 1) % len(self._clients)
        return client


def get_groq_client() -> Groq:
    """
    Returns a Groq client using round-robin key rotation.
    Keys are loaded from GROQ_API_KEYS (comma-separated) or GROQ_API_KEY.
    """
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not config.GROQ_API_KEYS:
                    raise ValueError("GROQ_API_KEY or GROQ_API_KEYS not configured.")
                logger.info(f"Initializing Groq client pool with {len(config.GROQ_API_KEYS)} key(s).")
                _pool = _GroqClientPool(config.GROQ_API_KEYS)
    return _pool.next_client()


def run_with_groq_client(fn):
    """
    Execute a Groq operation with key failover.
    Tries each configured key at most once for the current operation.
    """
    if not config.GROQ_API_KEYS:
        raise ValueError("GROQ_API_KEY or GROQ_API_KEYS not configured.")

    last_error = None
    attempts = len(config.GROQ_API_KEYS)
    for attempt in range(attempts):
        client = get_groq_client()
        try:
            return fn(client)
        except Exception as error:
            last_error = error
            logger.warning(f"Groq call failed on rotated key attempt {attempt + 1}/{attempts}: {error}")

    raise last_error
