"""WebSocket real-time feed (Part 7 protocol).

Server pushes new_violation / stats_update / review_update events. A background
task subscribes to the Redis 'violations' channel and fans messages out to all
connected dashboard clients (optionally filtered by subscribed cameras).
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core import redis_bus

log = logging.getLogger("backend.ws")
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []
        self.subscriptions: dict[WebSocket, set[str]] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        self.subscriptions[ws] = set()  # empty => all cameras

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)
        self.subscriptions.pop(ws, None)

    async def broadcast(self, message: dict) -> None:
        camera = (message.get("data") or {}).get("camera") or (message.get("data") or {}).get("camera_id")
        dead = []
        for ws in self.active:
            subs = self.subscriptions.get(ws, set())
            if subs and camera and camera not in subs:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def redis_listener() -> None:
    """Subscribe to Redis and rebroadcast to WS clients. Safe if Redis is down."""
    r = await redis_bus.get_redis()
    if r is None:
        log.info("WS redis_listener: Redis unavailable, real-time relay disabled")
        return
    pubsub = r.pubsub()
    await pubsub.subscribe(redis_bus.CHANNEL)
    log.info("WS redis_listener subscribed to '%s'", redis_bus.CHANNEL)
    try:
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                payload = json.loads(msg["data"])
            except (TypeError, ValueError):
                continue
            await manager.broadcast(payload)
    except asyncio.CancelledError:  # pragma: no cover
        await pubsub.unsubscribe(redis_bus.CHANNEL)
        raise


@router.websocket("/ws/violations")
async def ws_violations(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            t = msg.get("type")
            if t == "subscribe":
                manager.subscriptions[ws].update(msg.get("cameras", []))
            elif t == "unsubscribe":
                manager.subscriptions[ws].difference_update(msg.get("cameras", []))
            elif t == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws)
