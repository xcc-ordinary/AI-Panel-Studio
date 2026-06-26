"""SSE 端点: GET /api/discussions/{id}/events → StreamingResponse。

TODO: Phase 4 — 假事件源触发器由 discussion_orchestrator 替代。
"""
import asyncio
import json as _json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.sse.manager import publish, subscribe, get_events_after_seq
from app.database import get_db

router = APIRouter(prefix="/api/discussions", tags=["sse"])

# ── 假事件源（仅用于 MVP SSE 通道验证）──────────────────────
# TODO: Phase 4 — 替换为 discussion_orchestrator.run()

FAKE_PANELISTS = [
    {"id": "fake-p-0", "name": "张明远", "title": "科技媒体主编", "color": "#2563EB"},
    {"id": "fake-p-1", "name": "李开放", "title": "开源社区领袖", "color": "#DC2626"},
    {"id": "fake-p-2", "name": "陈安全", "title": "网络安全专家", "color": "#059669"},
    {"id": "fake-p-3", "name": "王商业", "title": "AI企业CEO", "color": "#D97706"},
]

FAKE_UTTERANCES = [
    "开源是AI创新的生命线，没有开源就没有今天的深度学习革命。",
    "我补充一点：开源确实有助于安全审计，最近发现的关键漏洞正是因为代码公开。",
    "但企业的研发投入需要回报，完全开源会打击创新积极性。",
    "我们需要跳出二元思维，建立一套全球性的AI治理框架。",
]

_fake_tasks: dict[str, asyncio.Task] = {}
_fake_rounds: dict[str, int] = {}


async def _publish_fake_utterance(discussion_id: str):
    """发布一条假发言，round_no 自增。"""
    round_no = _fake_rounds.get(discussion_id, 0)
    p = FAKE_PANELISTS[round_no % len(FAKE_PANELISTS)]
    payload = {
        "id": f"fake-u-{discussion_id}-{round_no}",
        "round_no": round_no,
        "panelist_id": p["id"],
        "panelist_name": p["name"],
        "panelist_title": p["title"],
        "panelist_color": p["color"],
        "type": "opening" if round_no == 0 else "statement",
        "content": FAKE_UTTERANCES[round_no % len(FAKE_UTTERANCES)],
        "created_at": "2026-06-26T10:00:00Z",
    }
    await publish(discussion_id, "utterance", payload)
    _fake_rounds[discussion_id] = round_no + 1


async def _start_fake_event_loop(discussion_id: str):
    """后台假事件循环：每秒发布一条假发言。"""
    while True:
        await asyncio.sleep(1)
        await _publish_fake_utterance(discussion_id)


async def _ensure_fake_events(discussion_id: str):
    """幂等：确保某讨论有假事件源在运行，并立即发布首条事件。"""
    if discussion_id not in _fake_tasks:
        # 先同步发布首条事件（确保订阅者不会饿死）
        await _publish_fake_utterance(discussion_id)
        # 再启动后台定时器
        _fake_tasks[discussion_id] = asyncio.create_task(_start_fake_event_loop(discussion_id))


# ── SSE 端点 ────────────────────────────────────────────


@router.get("/{discussion_id}/events")
async def event_stream(discussion_id: str, request: Request):
    last_event_id = request.headers.get("Last-Event-ID")

    async def generate():
        if last_event_id:
            db_row = await _get_db_snapshot(discussion_id)
            yield f"id: 0\nevent: snapshot\ndata: {db_row}\n\n"
            missed = await get_events_after_seq(discussion_id, int(last_event_id))
            for evt in missed:
                yield evt

        await _ensure_fake_events(discussion_id)

        async for lines in subscribe(discussion_id):
            yield lines

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Discussion-Id": discussion_id,
        },
    )


async def _get_db_snapshot(discussion_id: str) -> str:
    db = await get_db()
    row = await db.execute(
        "SELECT COALESCE(MAX(seq), 0) AS last_seq FROM event WHERE discussion_id = ?",
        (discussion_id,),
    )
    last_seq = (await row.fetchone())[0]
    return _json.dumps({
        "consensus_points": [],
        "divergence_points": [],
        "recent_utterances": [],
        "current_round": 0,
        "last_event_seq": last_seq,
    }, ensure_ascii=False)
