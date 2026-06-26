"""T029: Integration tests for GET /api/discussions"""
import pytest
from tests.conftest import insert_discussion


@pytest.mark.asyncio
async def test_list_empty_returns_empty_array(client):
    """空数据库 → 返回空列表 + active_count=0 + max_concurrent"""
    resp = await client.get("/api/discussions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["discussions"] == []
    assert body["active_count"] == 0
    assert body["max_concurrent"] == 10


@pytest.mark.asyncio
async def test_list_returns_all_discussions(client, db):
    """多条讨论 → 全部返回，字段完整"""
    await insert_discussion(db, "d1", "话题A：AI是否应该开源", status="in_progress", expert_count=3, current_round=5)
    await insert_discussion(db, "d2", "话题B：远程办公的利弊", status="in_progress", expert_count=4, current_round=2)
    await insert_discussion(db, "d3", "话题C：城市交通治理", status="ended", expert_count=3, current_round=12)

    resp = await client.get("/api/discussions")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["discussions"]) == 3
    assert body["active_count"] == 2  # d1 + d2 are in_progress
    assert body["max_concurrent"] == 10

    # 验证每条讨论的字段完整性
    for d in body["discussions"]:
        assert "id" in d
        assert "topic" in d
        assert "status" in d
        assert "expert_count" in d
        assert "current_round" in d
        assert "max_rounds" in d
        assert "panelist_count" in d
        assert "created_at" in d

    # 验证话题排序（按 created_at 倒序或正序均可，此处只验证存在）
    topics = [d["topic"] for d in body["discussions"]]
    assert "话题A：AI是否应该开源" in topics
    assert "话题B：远程办公的利弊" in topics
    assert "话题C：城市交通治理" in topics


@pytest.mark.asyncio
async def test_list_active_count_excludes_ended(client, db):
    """active_count 仅计数 in_progress 状态的讨论"""
    await insert_discussion(db, "d1", "进行中的讨论1", status="in_progress")
    await insert_discussion(db, "d2", "进行中的讨论2", status="in_progress")
    await insert_discussion(db, "d3", "已结束的讨论", status="ended")
    await insert_discussion(db, "d4", "等待阵容", status="pending_panelists")

    resp = await client.get("/api/discussions")
    assert resp.status_code == 200
    body = resp.json()
    # active_count 只统计 in_progress
    assert body["active_count"] == 2


@pytest.mark.asyncio
async def test_list_includes_panelist_count(client, db):
    """panelist_count 反映每场讨论的实际嘉宾人数"""
    await insert_discussion(db, "d1", "测试讨论", status="in_progress", expert_count=3)
    from tests.conftest import insert_panelist
    await insert_panelist(db, "p1", "d1", role="host", name="主持人", sort_order=0)
    await insert_panelist(db, "p2", "d1", role="expert", name="专家A", sort_order=1)
    await insert_panelist(db, "p3", "d1", role="expert", name="专家B", sort_order=2)

    resp = await client.get("/api/discussions")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["discussions"]) == 1
    assert body["discussions"][0]["panelist_count"] == 3
