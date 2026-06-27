"""T056: GET /api/discussions/{id}/consensus/current — 当前共识/分歧快照。"""
import json
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db

router = APIRouter(prefix="/api/discussions", tags=["consensus"])


def _parse_json_array(raw: str):
    try:
        return json.loads(raw) if isinstance(raw, str) else raw or []
    except (json.JSONDecodeError, TypeError):
        return []


@router.get("/{discussion_id}/consensus/current")
async def get_consensus_current(discussion_id: str, db=Depends(get_db)):
    # 验证讨论存在
    row = await db.execute("SELECT id FROM discussion WHERE id = ?", (discussion_id,))
    if (await row.fetchone()) is None:
        raise HTTPException(status_code=404, detail="讨论不存在")

    # consensus points
    c_rows = await db.execute(
        "SELECT id, content, involved_panelist_ids, created_at, updated_at "
        "FROM consensus_point WHERE discussion_id = ? ORDER BY updated_at DESC",
        (discussion_id,),
    )
    consensus_points = []
    async for r in c_rows:
        consensus_points.append({
            "id": r["id"],
            "content": r["content"],
            "involved_panelist_ids": _parse_json_array(r["involved_panelist_ids"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })

    # divergence points
    d_rows = await db.execute(
        "SELECT id, description, camps, created_at, updated_at "
        "FROM divergence_point WHERE discussion_id = ? ORDER BY updated_at DESC",
        (discussion_id,),
    )
    divergence_points = []
    async for r in d_rows:
        divergence_points.append({
            "id": r["id"],
            "description": r["description"],
            "camps": _parse_json_array(r["camps"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })

    # last_event_seq
    seq_row = await db.execute(
        "SELECT COALESCE(MAX(seq), 0) AS last_seq FROM event WHERE discussion_id = ?",
        (discussion_id,),
    )
    last_seq = (await seq_row.fetchone())[0]

    return {
        "consensus_points": consensus_points,
        "divergence_points": divergence_points,
        "last_event_seq": last_seq,
    }
