"""SSE event manager: per-discussion asyncio.Queue + persist + heartbeat.

Process identity: prints _registry id + PID at import time.
Same process → same module instance → same _registry dict.
Two prints with different id/PID → multi-process problem.
"""
import asyncio
import json
import os as _os
from datetime import datetime, timezone

from app.database import get_db

_registry: dict[str, asyncio.Queue] = {}

# ── Process identity verification (prints once on first import) ──
print(f"[manager] _registry id={id(_registry)} pid={_os.getpid()}", flush=True)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get_or_create_queue(discussion_id: str) -> asyncio.Queue:
    if discussion_id not in _registry:
        _registry[discussion_id] = asyncio.Queue()
    return _registry[discussion_id]


async def publish(discussion_id: str, event_type: str, payload: dict):
    """Persist event to event table, get seq, push to queue."""
    db = await get_db()

    # Get next seq for this discussion (COALESCE for initial value 1)
    row = await db.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM event WHERE discussion_id = ?", (discussion_id,))
    next_seq = (await row.fetchone())[0]

    payload_json = json.dumps(payload, ensure_ascii=False)
    await db.execute(
        "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (discussion_id, next_seq, event_type, payload_json, _now()),
    )
    await db.commit()

    # Build SSE lines
    lines = f"id: {next_seq}\nevent: {event_type}\ndata: {payload_json}\n\n"
    queue = _get_or_create_queue(discussion_id)
    await queue.put(lines)

    return next_seq


async def subscribe(discussion_id: str):
    """Async generator: subscribe to discussion event stream, 15s heartbeat on idle."""
    queue = _get_or_create_queue(discussion_id)
    while True:
        try:
            lines = await asyncio.wait_for(queue.get(), timeout=15.0)
            yield lines
        except asyncio.TimeoutError:
            yield f"event: heartbeat\ndata: {{\"timestamp\":\"{_now()}\"}}\n\n"


async def get_events_after_seq(discussion_id: str, after_seq: int) -> list[str]:
    """Query event table for seq > after_seq, return SSE-formatted strings (reconnection replay)."""
    db = await get_db()
    rows = await db.execute(
        "SELECT seq, event_type, payload_json FROM event "
        "WHERE discussion_id = ? AND seq > ? ORDER BY seq",
        (discussion_id, after_seq),
    )
    events = []
    async for r in rows:
        events.append(f"id: {r['seq']}\nevent: {r['event_type']}\ndata: {r['payload_json']}\n\n")
    return events


async def cleanup(discussion_id: str):
    """Remove queue when discussion ends."""
    _registry.pop(discussion_id, None)
