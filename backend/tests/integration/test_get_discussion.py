"""T030: Integration tests for GET /api/discussions/{id}"""
import pytest
from tests.conftest import insert_discussion, insert_panelist


@pytest.mark.asyncio
async def test_get_existing_discussion_returns_full_detail(client, db):
    """存在的讨论 → 200 + 完整字段 + panelists 数组"""
    await insert_discussion(db, "d1", "AI是否应该开源？", status="in_progress", expert_count=3, current_round=5)
    await insert_panelist(db, "p1", "d1", role="host", name="主持人张", title="科技主编", stance="中立", color="#2563EB", sort_order=0)
    await insert_panelist(db, "p2", "d1", role="expert", name="李开放", title="开源领袖", stance="强烈支持开源", color="#DC2626", sort_order=1)

    resp = await client.get("/api/discussions/d1")
    assert resp.status_code == 200
    body = resp.json()

    # 讨论基础字段
    assert body["id"] == "d1"
    assert body["topic"] == "AI是否应该开源？"
    assert body["status"] == "in_progress"
    assert body["expert_count"] == 3
    assert body["current_round"] == 5
    assert body["max_rounds"] == 30
    assert body["created_at"] is not None
    assert body["ended_at"] is None

    # panelists 数组
    assert "panelists" in body
    assert len(body["panelists"]) == 2

    host = next(p for p in body["panelists"] if p["role"] == "host")
    assert host["name"] == "主持人张"
    assert host["title"] == "科技主编"
    assert host["color"] == "#2563EB"
    assert host["sort_order"] == 0

    expert = next(p for p in body["panelists"] if p["role"] == "expert")
    assert expert["name"] == "李开放"
    assert expert["stance"] == "强烈支持开源"
    assert expert["color"] == "#DC2626"


@pytest.mark.asyncio
async def test_get_nonexistent_discussion_returns_404(client):
    """不存在的 discussion_id → 404"""
    resp = await client.get("/api/discussions/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_discussion_data_isolation(client, db):
    """不同 discussion 的数据严格隔离——查询讨论A不应包含讨论B的panelists"""
    await insert_discussion(db, "dA", "讨论A", status="in_progress")
    await insert_discussion(db, "dB", "讨论B", status="in_progress")
    await insert_panelist(db, "pA1", "dA", role="host", name="主持人A", sort_order=0)
    await insert_panelist(db, "pB1", "dB", role="host", name="主持人B", sort_order=0)

    resp = await client.get("/api/discussions/dA")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["panelists"]) == 1
    assert body["panelists"][0]["name"] == "主持人A"
    # 讨论B的panelist不应出现
    names = [p["name"] for p in body["panelists"]]
    assert "主持人B" not in names


@pytest.mark.asyncio
async def test_get_ended_discussion_has_ended_at(client, db):
    """已结束的讨论 → ended_at 不为空"""
    await insert_discussion(db, "d1", "已结束的讨论", status="ended", ended_at="2026-06-25T10:00:00Z")

    resp = await client.get("/api/discussions/d1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ended"
    assert body["ended_at"] == "2026-06-25T10:00:00Z"
