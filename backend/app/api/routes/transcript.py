"""T055: GET /api/discussions/{id}/transcript — 分页返回发言记录。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db

router = APIRouter(prefix="/api/discussions", tags=["transcript"])


@router.get("/{discussion_id}/transcript")
async def get_transcript(
    discussion_id: str,
    before_round: int | None = Query(None, alias="before_round"),
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    # 验证讨论存在
    row = await db.execute("SELECT id FROM discussion WHERE id = ?", (discussion_id,))
    if (await row.fetchone()) is None:
        raise HTTPException(status_code=404, detail="讨论不存在")

    if before_round is not None:
        rows = await db.execute(
            """SELECT u.id, u.round_no, u.panelist_id, u.type, u.content, u.created_at,
                      p.name AS panelist_name, p.title AS panelist_title, p.color AS panelist_color
               FROM utterance u JOIN panelist p ON p.id = u.panelist_id
               WHERE u.discussion_id = ? AND u.round_no < ?
               ORDER BY u.round_no DESC LIMIT ?""",
            (discussion_id, before_round, limit + 1),
        )
    else:
        rows = await db.execute(
            """SELECT u.id, u.round_no, u.panelist_id, u.type, u.content, u.created_at,
                      p.name AS panelist_name, p.title AS panelist_title, p.color AS panelist_color
               FROM utterance u JOIN panelist p ON p.id = u.panelist_id
               WHERE u.discussion_id = ?
               ORDER BY u.round_no DESC LIMIT ?""",
            (discussion_id, limit + 1),
        )

    utterances = []
    async for r in rows:
        utterances.append({
            "id": r["id"],
            "round_no": r["round_no"],
            "panelist_id": r["panelist_id"],
            "panelist_name": r["panelist_name"],
            "panelist_title": r["panelist_title"],
            "panelist_color": r["panelist_color"],
            "type": r["type"],
            "content": r["content"],
            "created_at": r["created_at"],
        })

    has_more = len(utterances) > limit
    if has_more:
        utterances.pop()

    # 后端按 DESC 查，前端期望 ASC 顺序
    utterances.reverse()

    return {"utterances": utterances, "has_more": has_more}
