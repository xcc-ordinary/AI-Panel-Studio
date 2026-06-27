"""SSE 事件管理器: per-discussion asyncio.Queue + 持久化 + 心跳。

TODO: Phase 4 — 假事件源由 discussion_orchestrator 替代。
"""
import asyncio
import json
from datetime import datetime, timezone

from app.database import get_db

_registry: dict[str, asyncio.Queue] = {}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get_or_create_queue(discussion_id: str) -> asyncio.Queue:
    if discussion_id not in _registry:
        _registry[discussion_id] = asyncio.Queue()
    return _registry[discussion_id]


async def publish(discussion_id: str, event_type: str, payload: dict):
    """持久化事件到 event 表，获取 seq，推送至队列。"""
    db = await get_db()

    # 获取该讨论下一个 seq（用 COALESCE 兜底起始值 1）
    row = await db.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM event WHERE discussion_id = ?", (discussion_id,))
    next_seq = (await row.fetchone())[0]

    payload_json = json.dumps(payload, ensure_ascii=False)
    await db.execute(
        "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (discussion_id, next_seq, event_type, payload_json, _now()),
    )
    await db.commit()

    # 构建 SSE 行
    lines = f"id: {next_seq}\nevent: {event_type}\ndata: {payload_json}\n\n"
    queue = _get_or_create_queue(discussion_id)
    await queue.put(lines)

    return next_seq


async def subscribe(discussion_id: str):
    """Async generator: 订阅讨论事件流，15s 无事件则发 heartbeat。"""
    queue = _get_or_create_queue(discussion_id)
    while True:
        try:
            lines = await asyncio.wait_for(queue.get(), timeout=15.0)
            yield lines
        except asyncio.TimeoutError:
            yield f"event: heartbeat\ndata: {{\"timestamp\":\"{_now()}\"}}\n\n"


async def get_events_after_seq(discussion_id: str, after_seq: int) -> list[str]:
    """查询 event 表中 seq > after_seq 的记录，返回 SSE 格式字符串列表（用于重连回放）。"""
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
    """讨论结束时清理队列。"""
    _registry.pop(discussion_id, None)
