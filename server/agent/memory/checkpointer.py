from __future__ import annotations
import json
from typing import Any, Optional
import time
import redis

from ...infra.settings import settings


class RedisCheckpointer:
    def __init__(self, namespace: str = "kisan:agent"):
        self.r = redis.Redis.from_url(settings.redis_url or "redis://localhost:6379/0")
        self.ns = namespace

    def _key(self, session_id: str) -> str:
        return f"{self.ns}:session:{session_id}"

    def load(self, session_id: str) -> Optional[dict]:
        data = self.r.get(self._key(session_id))
        if not data:
            return None
        return json.loads(data)

    def save(self, session_id: str, state: dict, ttl_seconds: int = 86400) -> None:
        payload = json.dumps({"ts": int(time.time()), "state": state}, ensure_ascii=False)
        self.r.set(self._key(session_id), payload, ex=ttl_seconds)
