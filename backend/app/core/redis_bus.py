"""Redis pub/sub bus for real-time violation fan-out to WebSocket clients."""
from __future__ import annotations

import json
import logging

import redis.asyncio as aioredis

from .config import settings

log = logging.getLogger("backend.redis")
CHANNEL = "violations"

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
        except Exception as e:  # pragma: no cover
            log.warning("Redis unavailable (%s) — pub/sub disabled", e)
            _redis = None
    return _redis


async def publish(message: dict) -> None:
    from ..api.websocket import manager
    r = await get_redis()
    if r is None:
        try:
            await manager.broadcast(message)
        except Exception as e:
            log.warning("local broadcast failed: %s", e)
        return
    try:
        await r.publish(CHANNEL, json.dumps(message, default=str))
    except Exception as e:  # pragma: no cover
        log.warning("publish failed: %s", e)
