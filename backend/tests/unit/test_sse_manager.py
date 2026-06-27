"""T040-ext: SSE manager 合约遵从测试 — get_events_after_seq + snapshot 内容"""

import json
import pytest
from app.api.sse.manager import get_events_after_seq
from app.api.sse.events import _get_db_snapshot


# ═══════════════════════════════════════════════════════════════
# get_events_after_seq — 合约: 只补发 seq > Last-Event-ID 的事件
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_events_after_seq_returns_only_strictly_greater(db):
    """合约 api-sse.md §Reconnection step 3:
    后端只补发 seq > Last-Event-ID 的事件，用 > 而非 >= 防止边界重复。
    """
    disc_id = "test-replay"

    # 插入测试数据
    await db.execute("INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
                     "VALUES (?, ?, 'in_progress', 3, 30, 0, '2026-06-26T00:00:00Z')",
                     (disc_id, "SSE回放测试"))

    events = [
        (1, "utterance", '{"round_no":0}'),
        (2, "utterance", '{"round_no":1}'),
        (3, "utterance", '{"round_no":2}'),
        (4, "panelist_status", '{"panelist_id":"p-1"}'),
        (5, "utterance", '{"round_no":3}'),
    ]
    for seq, evt_type, payload in events:
        await db.execute(
            "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, '2026-06-26T00:00:00Z')",
            (disc_id, seq, evt_type, payload),
        )
    await db.commit()

    # ── 断点在 seq=3：应该只返回 seq 4,5 ──
    replayed = await get_events_after_seq(disc_id, after_seq=3)

    assert len(replayed) == 2, f"Expected 2 events with seq>3, got {len(replayed)}"
    for line in replayed:
        # 每行格式为 id: {seq}\nevent: ...\ndata: ...\n\n
        assert line.startswith("id: ") or line.startswith("id:"), f"Missing id field: {line!r}"
        id_part = line.split("\n")[0]
        seq_val = int(id_part.replace("id:", "").replace("id: ", "").strip())
        assert seq_val > 3, f"Expected seq>3, got seq={seq_val} in {line!r}"


@pytest.mark.asyncio
async def test_get_events_after_seq_does_not_include_exact_boundary(db):
    """边界测试: after_seq=2 不返回 seq=2 的事件（严格大于）。"""
    disc_id = "test-boundary"

    await db.execute("INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
                     "VALUES (?, ?, 'in_progress', 3, 30, 0, '2026-06-26T00:00:00Z')",
                     (disc_id, "边界测试"))

    await db.execute(
        "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, 2, 'utterance', '{\"seq\":2}', '2026-06-26T00:00:00Z')",
        (disc_id,),
    )
    await db.commit()

    # after_seq=2: 要求 seq > 2，所以 seq=2 不返回
    replayed = await get_events_after_seq(disc_id, after_seq=2)

    assert len(replayed) == 0, (
        f"边界违反: after_seq=2 应返回 0 条 (seq>2 为空), 实际返回 {len(replayed)} 条。"
        f"检查 WHERE 子句是否使用了 > 而非 >="
    )


@pytest.mark.asyncio
async def test_get_events_after_seq_returns_sorted_by_seq(db):
    """回放事件必须按 seq 升序排列。"""
    disc_id = "test-sorted"

    await db.execute("INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
                     "VALUES (?, ?, 'in_progress', 3, 30, 0, '2026-06-26T00:00:00Z')",
                     (disc_id, "排序测试"))

    # 故意乱序插入
    for seq in [7, 3, 5, 1, 9]:
        await db.execute(
            "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, ?, 'utterance', ?, '2026-06-26T00:00:00Z')",
            (disc_id, seq, json.dumps({"seq": seq})),
        )
    await db.commit()

    replayed = await get_events_after_seq(disc_id, after_seq=0)
    seqs = []
    for line in replayed:
        id_part = line.split("\n")[0]
        seqs.append(int(id_part.replace("id:", "").replace("id: ", "").strip()))

    assert seqs == sorted(seqs), f"Replay must be sorted by seq ASC, got {seqs}"


# ═══════════════════════════════════════════════════════════════
# _get_db_snapshot — 合约: 重连快照含真实数据
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_snapshot_returns_non_empty_when_events_exist(db):
    """合约 api-sse.md §snapshot:
    ```json
    {"consensus_points":[...],"divergence_points":[...],"recent_utterances":[...],"current_round":N,"last_event_seq":N}
    ```
    当 event 表中有数据时，各字段不应为空。
    """
    disc_id = "test-snap-full"

    await db.execute("INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
                     "VALUES (?, ?, 'in_progress', 3, 30, 5, '2026-06-26T00:00:00Z')",
                     (disc_id, "快照测试"))

    # 插入 utterance 事件
    for seq in range(1, 6):
        payload = json.dumps({
            "id": f"u-{seq}", "round_no": seq - 1, "panelist_id": f"p-{seq % 3}",
            "panelist_name": f"专家{seq}", "panelist_title": f"Title{seq}",
            "panelist_color": "#818CF8", "type": "statement",
            "content": f"发言内容{seq}", "created_at": "2026-06-26T10:00:00Z",
        }, ensure_ascii=False)
        await db.execute(
            "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, ?, 'utterance', ?, '2026-06-26T00:00:00Z')",
            (disc_id, seq, payload),
        )

    # 插入 consensus_update
    c_payload = json.dumps({
        "id": "c-1", "content": "共识点1", "involved_panelist_ids": ["p-1", "p-2"], "updated_at": "2026-06-26T10:05:00Z",
    }, ensure_ascii=False)
    await db.execute(
        "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, 6, 'consensus_update', ?, '2026-06-26T00:00:00Z')",
        (disc_id, c_payload),
    )

    # 插入 divergence_update
    d_payload = json.dumps({
        "id": "d-1", "description": "分歧点1",
        "camps": [{"position": "完全开源", "panelist_ids": ["p-1"]}], "updated_at": "2026-06-26T10:05:00Z",
    }, ensure_ascii=False)
    await db.execute(
        "INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, 7, 'divergence_update', ?, '2026-06-26T00:00:00Z')",
        (disc_id, d_payload),
    )

    await db.commit()

    snapshot = await _get_db_snapshot(disc_id)
    data = json.loads(snapshot)

    # 合约字段全部存在
    for field in ("consensus_points", "divergence_points", "recent_utterances", "current_round", "last_event_seq"):
        assert field in data, f"snapshot missing required field '{field}'"
        assert data[field] is not None, f"snapshot field '{field}' is None"

    # 真实数据断言——不再是空数组
    assert len(data["recent_utterances"]) == 5, f"Expected 5 utterances, got {len(data['recent_utterances'])}"
    assert len(data["consensus_points"]) >= 1, f"Expected >=1 consensus, got {len(data['consensus_points'])}"
    assert len(data["divergence_points"]) >= 1, f"Expected >=1 divergence, got {len(data['divergence_points'])}"
    assert data["last_event_seq"] == 7

    # utterance 内容校验
    assert data["recent_utterances"][0]["content"] == "发言内容1"

    # consensus 内容校验
    assert data["consensus_points"][0]["content"] == "共识点1"

    # divergence 内容校验
    assert data["divergence_points"][0]["description"] == "分歧点1"
    assert isinstance(data["divergence_points"][0]["camps"], list)
    assert data["divergence_points"][0]["camps"][0]["position"] == "完全开源"


@pytest.mark.asyncio
async def test_snapshot_returns_empty_arrays_for_discussion_with_no_events(db):
    """没有事件的讨论快照应为空数组——不做假数据。"""
    disc_id = "test-snap-empty"

    await db.execute("INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
                     "VALUES (?, ?, 'pending_panelists', 3, 30, 0, '2026-06-26T00:00:00Z')",
                     (disc_id, "空快照测试"))
    await db.commit()

    snapshot = await _get_db_snapshot(disc_id)
    data = json.loads(snapshot)

    assert data["recent_utterances"] == []
    assert data["consensus_points"] == []
    assert data["divergence_points"] == []
    assert data["current_round"] == 0
    assert data["last_event_seq"] == 0


@pytest.mark.asyncio
async def test_snapshot_dedup_consensus_by_id_keeps_latest(db):
    """同一 consensus id 多次更新时，快照只保留最新（按 seq DESC 首次出现）。"""
    disc_id = "test-snap-dedup"

    await db.execute("INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at) "
                     "VALUES (?, ?, 'in_progress', 3, 30, 3, '2026-06-26T00:00:00Z')",
                     (disc_id, "去重测试"))
    await db.commit()

    # 同一 consensus id 两次更新：seq=1 旧版本，seq=2 新版本
    old_payload = json.dumps({"id": "c-x", "content": "旧共识", "involved_panelist_ids": [], "updated_at": "2026-06-26T10:00:00Z"})
    new_payload = json.dumps({"id": "c-x", "content": "新共识", "involved_panelist_ids": ["p-1"], "updated_at": "2026-06-26T10:05:00Z"})

    await db.execute("INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, 1, 'consensus_update', ?, '2026-06-26T00:00:00Z')", (disc_id, old_payload))
    await db.execute("INSERT INTO event (discussion_id, seq, event_type, payload_json, created_at) VALUES (?, 2, 'consensus_update', ?, '2026-06-26T00:00:00Z')", (disc_id, new_payload))
    await db.commit()

    snapshot = await _get_db_snapshot(disc_id)
    data = json.loads(snapshot)

    assert len(data["consensus_points"]) == 1, f"Should dedup to 1, got {len(data['consensus_points'])}"
    assert data["consensus_points"][0]["content"] == "新共识", "Should keep latest version (higher seq = first in DESC order)"
