"""SSE 端点: GET /api/discussions/{id}/events → StreamingResponse。

TODO: Phase 4 — 假事件源由 discussion_orchestrator 替代。
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

STATUSES = ['idle', 'preparing', 'speaking', 'idle', 'silent']

FAKE_CONSENSUS_POINTS = [
    {"id": "c1", "content": "与会专家一致认为需要建立AI开源的安全标准与治理框架",
     "involved_panelist_ids": [], "updated_at": ""},
    {"id": "c2", "content": "各方认同开源有助于安全审计，能更快发现和修复关键漏洞",
     "involved_panelist_ids": [], "updated_at": ""},
]

FAKE_DIVERGENCE_POINTS = [
    {"id": "d1", "description": "关于开源程度的根本分歧：一方主张完全开源，另一方认为核心模型应保留商业壁垒",
     "camps": [], "updated_at": ""},
]

_fake_tasks: dict[str, asyncio.Task] = {}
_fake_rounds: dict[str, int] = {}
_fake_step: dict[str, int] = {}  # 每 discussion 的步数计数器


async def _load_fake_panelists(discussion_id: str) -> list[dict]:
    """尝试从 DB 加载 panelist 数据（seed 讨论），失败则用默认假数据。"""
    db = await get_db()
    rows = await db.execute(
        "SELECT id, discussion_id, role, name, title, stance, color, sort_order FROM panelist WHERE discussion_id = ? ORDER BY sort_order",
        (discussion_id,),
    )
    panelists = []
    async for r in rows:
        panelists.append({
            "id": r["id"], "role": r["role"], "name": r["name"],
            "title": r["title"], "color": r["color"], "sort_order": r["sort_order"],
        })
    if panelists:
        return panelists

    # fallback
    return [
        {"id": "fake-p-0", "role": "host", "name": "张明远", "title": "科技媒体主编", "color": "#38BDF8", "sort_order": 0},
        {"id": "fake-p-1", "role": "expert", "name": "李开放", "title": "开源社区领袖", "color": "#F87171", "sort_order": 1},
        {"id": "fake-p-2", "role": "expert", "name": "陈安全", "title": "网络安全专家", "color": "#818CF8", "sort_order": 2},
        {"id": "fake-p-3", "role": "expert", "name": "王商业", "title": "AI企业CEO", "color": "#FBBF24", "sort_order": 3},
        {"id": "fake-p-4", "role": "expert", "name": "赵伦理", "title": "科技伦理学者", "color": "#A78BFA", "sort_order": 4},
    ]


async def _publish_fake_utterance(discussion_id: str, panelists: list[dict]):
    round_no = _fake_rounds.get(discussion_id, 0)
    p = panelists[round_no % len(panelists)]

    utterances = [
        "开源是AI创新的生命线，没有开源就没有今天的深度学习革命。",
        "我补充一点：开源确实有助于安全审计，最近发现的关键漏洞正是因为代码公开。",
        "但企业的研发投入需要回报，完全开源会打击创新积极性。",
        "我们需要跳出二元思维，建立一套全球性的AI治理框架。",
        "监管不等于封杀。如果监管框架由社区共同制定，开源社区是愿意参与的。",
    ]
    type_ = "opening" if round_no == 0 else "statement" if round_no % 2 == 0 else "supplement"

    await publish(discussion_id, "utterance", {
        "id": f"fake-u-{discussion_id}-{round_no}",
        "round_no": round_no,
        "panelist_id": p["id"],
        "panelist_name": p["name"],
        "panelist_title": p["title"],
        "panelist_color": p["color"],
        "type": type_,
        "content": utterances[round_no % len(utterances)],
        "created_at": "2026-06-26T10:00:00Z",
    })
    _fake_rounds[discussion_id] = round_no + 1


async def _publish_fake_status(discussion_id: str, panelists: list[dict]):
    """随机选一个专家切换状态。"""
    experts = [p for p in panelists if p["role"] == "expert"]
    if not experts:
        return
    step = _fake_step.get(discussion_id, 0)
    p = experts[step % len(experts)]
    status = STATUSES[step % len(STATUSES)]

    await publish(discussion_id, "panelist_status", {
        "panelist_id": p["id"],
        "status": status,
        "public_focus": _json.dumps(
            ["关注开源生态可持续性"] if status == "idle" else
            ["准备回应李开放的生态观点"] if status == "preparing" else
            []
        ),
    })


async def _publish_fake_consensus(discussion_id: str):
    step = _fake_step.get(discussion_id, 0)
    cp = FAKE_CONSENSUS_POINTS[step % len(FAKE_CONSENSUS_POINTS)]
    await publish(discussion_id, "consensus_update", {
        **cp,
        "involved_panelist_ids": ["fake-p-0", "fake-p-1"] if not cp["involved_panelist_ids"] else cp["involved_panelist_ids"],
        "updated_at": "2026-06-26T10:05:00Z",
    })


async def _publish_fake_divergence(discussion_id: str):
    step = _fake_step.get(discussion_id, 0)
    dp = FAKE_DIVERGENCE_POINTS[step % len(FAKE_DIVERGENCE_POINTS)]
    await publish(discussion_id, "divergence_update", {
        **dp,
        "camps": _json.dumps([
            {"position": "完全开源", "panelist_ids": ["fake-p-1"]},
            {"position": "有限开源", "panelist_ids": ["fake-p-2"]},
        ]) if not dp["camps"] else dp["camps"],
        "updated_at": "2026-06-26T10:05:00Z",
    })


async def _start_fake_event_loop(discussion_id: str):
    """后台假事件循环：utterance 每秒 / status 每 3 秒 / consensus 每 8 秒。"""
    panelists = await _load_fake_panelists(discussion_id)
    step = 0

    while True:
        await asyncio.sleep(1)
        step += 1
        _fake_step[discussion_id] = step

        # 每秒一条 utterance
        await _publish_fake_utterance(discussion_id, panelists)

        # 每 3 步一次 panelist_status 切换
        if step % 3 == 0:
            await _publish_fake_status(discussion_id, panelists)

        # 每 5 步一次 consensus_update
        if step % 5 == 0:
            await _publish_fake_consensus(discussion_id)

        # 每 10 步一次 divergence_update
        if step % 10 == 0:
            await _publish_fake_divergence(discussion_id)


async def _ensure_fake_events(discussion_id: str):
    """幂等：确保某讨论有假事件源在运行，并立即发布首条事件。"""
    if discussion_id not in _fake_tasks:
        panelists = await _load_fake_panelists(discussion_id)
        await _publish_fake_utterance(discussion_id, panelists)
        _fake_tasks[discussion_id] = asyncio.create_task(_start_fake_event_loop(discussion_id))


# ── SSE 端点 ────────────────────────────────────────────


@router.get("/{discussion_id}/events")
async def event_stream(discussion_id: str, request: Request):
    last_event_id = request.headers.get("Last-Event-ID")

    async def generate():
        if last_event_id:
            db_row = await _get_db_snapshot(discussion_id)
            yield f"event: snapshot\ndata: {db_row}\n\n"
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
