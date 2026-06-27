"""讨论 CRUD 路由：GET 列表 / GET 详情 / POST 创建 / DELETE 级联删除。"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/api/discussions", tags=["discussions"])


def _now():
    return datetime.now(timezone.utc).isoformat()


class CreateDiscussionRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    expert_count: int = Field(..., ge=2, le=8)


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


@router.post("", status_code=201)
async def create_discussion(body: CreateDiscussionRequest, db=Depends(get_db)):
    # 1) 内容审核
    from app.services.local_moderator import LocalContentModerator
    moderator = LocalContentModerator()
    mod_result = await moderator.check_topic(body.topic)
    if not mod_result.allowed:
        raise HTTPException(status_code=422, detail=mod_result.reason or "话题未通过审核")

    # 2) 限流守卫（in_progress + pending_panelists）
    row = await db.execute(
        "SELECT COUNT(*) FROM discussion WHERE status IN ('in_progress','pending_panelists')"
    )
    active_count = (await row.fetchone())[0]
    if active_count >= settings.max_concurrent_discussions:
        raise HTTPException(
            status_code=429,
            detail=f"当前讨论已满（{active_count}/{settings.max_concurrent_discussions}），请等待某场讨论结束后再发起",
        )

    # 3) 调用 PanelistGenerator
    from app.services.panelist_generator import PanelistGenerator, PanelistGenerationError
    gen = PanelistGenerator()
    try:
        panelists = await gen.generate(body.topic, body.expert_count)
    except PanelistGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"嘉宾生成失败: {e}")

    # 4) 持久化到数据库
    disc_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
        "VALUES (?, ?, 'pending_panelists', ?, ?, 0, ?)",
        (disc_id, body.topic, body.expert_count, settings.default_max_rounds, _now()),
    )
    for p in panelists:
        await db.execute(
            "INSERT INTO panelist (id, discussion_id, role, name, title, stance, color, status, public_focus, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'idle', '[]', ?)",
            (p["id"], disc_id, p["role"], p["name"], p["title"], p["stance"], p["color"], p["sort_order"]),
        )
    await db.commit()

    # 5) 返回响应
    return {
        "discussion_id": disc_id,
        "topic": body.topic,
        "status": "pending_panelists",
        "panelists": [{**p, "discussion_id": disc_id, "status": "idle", "public_focus": "[]"} for p in panelists],
    }


@router.patch("/{discussion_id}/panelists/confirm")
async def confirm_panelists(discussion_id: str, db=Depends(get_db)):
    row = await db.execute("SELECT id, status FROM discussion WHERE id = ?", (discussion_id,))
    disc = await row.fetchone()
    if disc is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    if disc["status"] != "pending_panelists":
        raise HTTPException(status_code=400, detail="讨论状态不允许确认阵容")
    await db.execute("UPDATE discussion SET status='in_progress' WHERE id=?", (discussion_id,))
    await db.commit()
    return {"discussion_id": discussion_id, "status": "in_progress"}


@router.post("/{discussion_id}/panelists/regenerate")
async def regenerate_panelists(discussion_id: str, db=Depends(get_db)):
    row = await db.execute("SELECT id, topic, expert_count FROM discussion WHERE id = ?", (discussion_id,))
    disc = await row.fetchone()
    if disc is None:
        raise HTTPException(status_code=404, detail="讨论不存在")

    # 删除旧 panelists
    await db.execute("DELETE FROM panelist WHERE discussion_id = ?", (discussion_id,))

    # 重新生成
    from app.services.panelist_generator import PanelistGenerator, PanelistGenerationError
    gen = PanelistGenerator()
    try:
        panelists = await gen.generate(disc["topic"], disc["expert_count"])
    except PanelistGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))

    for p in panelists:
        await db.execute(
            "INSERT INTO panelist (id, discussion_id, role, name, title, stance, color, status, public_focus, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'idle', '[]', ?)",
            (p["id"], discussion_id, p["role"], p["name"], p["title"], p["stance"], p["color"], p["sort_order"]),
        )
    await db.commit()

    return {"panelists": [{**p, "discussion_id": discussion_id, "status": "idle", "public_focus": "[]"} for p in panelists]}


@router.delete("/{discussion_id}")
async def delete_discussion(discussion_id: str, db=Depends(get_db)):
    row = await db.execute("SELECT id FROM discussion WHERE id = ?", (discussion_id,))
    if (await row.fetchone()) is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    await db.execute("DELETE FROM discussion WHERE id = ?", (discussion_id,))
    await db.commit()
    return {"deleted": True}
