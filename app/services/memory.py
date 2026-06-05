import json

import redis

from app.core.config import settings

HISTORY_TTL_SECONDS = 60 * 60 * 24 * 7
MAX_MESSAGES = 20

_client = redis.from_url(settings.redis_url, decode_responses=True)


class ConversationMemory:
    """Redis-backed store for multi-turn conversation history."""

    @staticmethod
    def _key(user_id: str) -> str:
        return f"chat:{user_id}"

    def load(self, user_id: str) -> list[dict[str, str]]:
        raw = _client.get(self._key(user_id))
        return json.loads(raw) if raw else []

    def append(self, user_id: str, role: str, content: str) -> None:
        messages = self.load(user_id)
        messages.append({"role": role, "content": content})
        _client.set(
            self._key(user_id),
            json.dumps(messages[-MAX_MESSAGES:]),
            ex=HISTORY_TTL_SECONDS,
        )
