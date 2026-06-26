"""讨论 CRUD 路由：GET 列表 / GET 详情 / DELETE 级联删除。"""
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/api/discussions", tags=["discussions"])


def _discussion_row_to_dict(row, panelist_count=0) -> dict:
    """将 discussion 数据库行 + panelist_count 转为 API 响应字典。"""
    return {
        "id": row["id"],
        "topic": row["topic"],
        "status": row["status"],
        "expert_count": row["expert_count"],
        "max_rounds": row["max_rounds"],
        "current_round": row["current_round"],
        "panelist_count": panelist_count,
        "created_at": row["created_at"],
    }


async def _count_panelists(db, discussion_id: str) -> int:
    row = await db.execute("SELECT COUNT(*) FROM panelist WHERE discussion_id = ?", (discussion_id,))
    return (await row.fetchone())[0]


@router.get("")
async def list_discussions(db=Depends(get_db)):
    rows = await db.execute(
        "SELECT d.id, d.topic, d.status, d.expert_count, d.max_rounds, d.current_round, d.created_at, "
        "COUNT(p.id) AS panelist_count "
        "FROM discussion d LEFT JOIN panelist p ON p.discussion_id = d.id "
        "GROUP BY d.id ORDER BY d.created_at DESC"
    )
    discussions = []
    active_count = 0
    async for r in rows:
        if r["status"] == "in_progress":
            active_count += 1
        discussions.append(_discussion_row_to_dict(r, panelist_count=r["panelist_count"]))

    return {
        "discussions": discussions,
        "active_count": active_count,
        "max_concurrent": settings.max_concurrent_discussions,
    }


@router.get("/{discussion_id}")
async def get_discussion(discussion_id: str, db=Depends(get_db)):
    row = await db.execute("SELECT * FROM discussion WHERE id = ?", (discussion_id,))
    disc = await row.fetchone()
    if disc is None:
        raise HTTPException(status_code=404, detail="讨论不存在")

    p_rows = await db.execute(
        "SELECT id, discussion_id, role, name, title, stance, color, status, public_focus, sort_order "
        "FROM panelist WHERE discussion_id = ? ORDER BY sort_order",
        (discussion_id,),
    )
    panelists = []
    async for p in p_rows:
        panelists.append({
            "id": p["id"],
            "discussion_id": p["discussion_id"],
            "role": p["role"],
            "name": p["name"],
            "title": p["title"],
            "stance": p["stance"],
            "color": p["color"],
            "status": p["status"],
            "public_focus": p["public_focus"],
            "sort_order": p["sort_order"],
        })

    return {
        **_discussion_row_to_dict(disc, panelist_count=len(panelists)),
        "ended_at": disc["ended_at"],
        "panelists": panelists,
    }


@router.delete("/{discussion_id}")
async def delete_discussion(discussion_id: str, db=Depends(get_db)):
    row = await db.execute("SELECT id FROM discussion WHERE id = ?", (discussion_id,))
    if (await row.fetchone()) is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    await db.execute("DELETE FROM discussion WHERE id = ?", (discussion_id,))
    await db.commit()
    return {"deleted": True}
