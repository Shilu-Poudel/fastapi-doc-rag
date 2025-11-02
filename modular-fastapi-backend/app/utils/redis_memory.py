from typing import Any, Dict, List
import os
import json
import redis.asyncio as aioredis
from collections import defaultdict

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_REDIS = os.getenv("USE_REDIS", "true").lower() in ("1", "true", "yes")
CHAT_TTL = 60 * 60 * 24 * 7  # 7 days

class InMemoryStore:
    """Simple in-memory fallback when Redis is not available."""
    def __init__(self) -> None:
        self.messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    async def get(self, key: str) -> str | None:
        msgs = self.messages.get(key)
        return json.dumps(msgs) if msgs else None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.messages[key] = json.loads(value)

class RedisMemory:
    """
    Async wrapper for chat memory, with in-memory fallback.
    Controlled by USE_REDIS env var; if true but Redis unreachable, falls back.
    """
    def __init__(self) -> None:
        self._redis_available = False
        self.client = InMemoryStore()
        if USE_REDIS:
            try:
                client = aioredis.from_url(REDIS_URL, decode_responses=True)
                # don't await here — assign client and rely on runtime try/except on operations
                self.client = client
                self._redis_available = True
            except Exception:
                # fail silently to fallback to memory store
                self.client = InMemoryStore()
                self._redis_available = False

    async def get_messages(self, user_id: str) -> List[Dict[str, Any]]:
        key = f"chat:{user_id}"
        try:
            raw = await self.client.get(key)  # aioredis raises if unreachable
        except Exception:
            # fallback to memory store behavior
            return []
        if not raw:
            return []
        return json.loads(raw)

    async def append_message(self, user_id: str, message: Dict[str, Any]) -> None:
        key = f"chat:{user_id}"
        messages = await self.get_messages(user_id)
        messages.append(message)
        try:
            await self.client.set(key, json.dumps(messages), ex=CHAT_TTL if self._redis_available else None)
        except Exception:
            # swallow and keep messages in-memory
            if not isinstance(self.client, InMemoryStore):
                self.client = InMemoryStore()
            await self.client.set(key, json.dumps(messages))