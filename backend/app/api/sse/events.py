"""SSE endpoint: GET /api/discussions/{id}/events → StreamingResponse.

Reconnection protocol:
  1. Browser EventSource auto-reconnects with Last-Event-ID = last received Event.seq
  2. Server sends snapshot (no id: field) + missed events (seq > Last-Event-ID)
  3. Live events from queue (pushed by DiscussionOrchestrator)

Test mode (APANEL_TEST=true): skips orchestrator spawn, tests publish their own events.
"""
import asyncio
import json as _json
import os as _os
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.sse.manager import publish, subscribe, get_events_after_seq
from app.database import get_db

router = APIRouter(prefix="/api/discussions", tags=["sse"])

_TEST_MODE = _os.environ.get("APANEL_TEST", "").lower() == "true"


# ── Orchestrator lifecycle ──────────────────────────────────────

async def _ensure_orchestrator(discussion_id: str) -> None:
    """Spawn orchestrator for in_progress discussions if not already running.
    In test mode, this is a no-op (tests publish their own events).
    """
    if _TEST_MODE:
        return

    from app.services.discussion_orchestrator import spawn_discussion, is_running

    if is_running(discussion_id):
        return

    db = await get_db()
    row = await db.execute("SELECT status FROM discussion WHERE id = ?", (discussion_id,))
    disc = await row.fetchone()
    if disc and disc["status"] == "in_progress":
        await spawn_discussion(discussion_id)


# ── SSE endpoint ────────────────────────────────────────────────


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

        await _ensure_orchestrator(discussion_id)

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


# ── Snapshot (reconnection) ─────────────────────────────────────


async def _get_db_snapshot(discussion_id: str) -> str:
    """Rebuild current discussion snapshot from event table for reconnection."""
    db = await get_db()

    # ── last_seq ──────────────────────────────────────────
    row = await db.execute(
        "SELECT COALESCE(MAX(seq), 0) AS last_seq FROM event WHERE discussion_id = ?",
        (discussion_id,),
    )
    last_seq = (await row.fetchone())[0]

    # ── recent utterances (last 50, chronological) ─────────
    u_rows = await db.execute(
        "SELECT payload_json FROM event "
        "WHERE discussion_id = ? AND event_type = 'utterance' "
        "ORDER BY seq DESC LIMIT 50",
        (discussion_id,),
    )
    recent_utterances = []
    async for r in u_rows:
        try:
            recent_utterances.append(_json.loads(r["payload_json"]))
        except (_json.JSONDecodeError, TypeError):
            pass
    recent_utterances.reverse()

    # ── latest consensus per id ────────────────────────────
    c_rows = await db.execute(
        "SELECT payload_json FROM event "
        "WHERE discussion_id = ? AND event_type = 'consensus_update' "
        "ORDER BY seq DESC",
        (discussion_id,),
    )
    consensus_map: dict[str, dict] = {}
    async for r in c_rows:
        try:
            cp = _json.loads(r["payload_json"])
            if cp.get("id") and cp["id"] not in consensus_map:
                consensus_map[cp["id"]] = cp
        except (_json.JSONDecodeError, TypeError):
            pass

    # ── latest divergence per id ───────────────────────────
    d_rows = await db.execute(
        "SELECT payload_json FROM event "
        "WHERE discussion_id = ? AND event_type = 'divergence_update' "
        "ORDER BY seq DESC",
        (discussion_id,),
    )
    divergence_map: dict[str, dict] = {}
    async for r in d_rows:
        try:
            dp = _json.loads(r["payload_json"])
            if dp.get("id") and dp["id"] not in divergence_map:
                divergence_map[dp["id"]] = dp
        except (_json.JSONDecodeError, TypeError):
            pass

    # ── current round ─────────────────────────────────────
    cur_round = recent_utterances[-1]["round_no"] + 1 if recent_utterances else 0

    return _json.dumps({
        "consensus_points": list(consensus_map.values()),
        "divergence_points": list(divergence_map.values()),
        "recent_utterances": recent_utterances,
        "current_round": cur_round,
        "last_event_seq": last_seq,
    }, ensure_ascii=False)
