"""T040: SSE event stream integration tests —— 通过真实 HTTP (live_server) 验证。"""
import json
import httpx
import pytest

STREAM_PATH = "/api/discussions/test-dummy/events"


def _parse_sse(raw: str) -> list[dict]:
    events = []
    cur = {}
    for line in raw.split("\n"):
        if line.startswith("id:"):
            cur["id"] = line[3:].strip()
        elif line.startswith("event:"):
            cur["event"] = line[6:].strip()
        elif line.startswith("data:"):
            cur["data"] = line[5:].strip()
        elif line == "" and cur:
            events.append(cur)
            cur = {}
    if cur:
        events.append(cur)
    return events


async def _read_sse(url: str, n: int = 4, extra_headers=None,
                    timeout: float = 10.0) -> tuple[list[dict], httpx.Response]:
    """通过真实 HTTP 读取 n 个 SSE 事件后断开。"""
    raw = ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, read=timeout)) as client:
        async with client.stream("GET", url, headers=extra_headers or {}) as resp:
            assert resp.status_code == 200
            async for chunk in resp.aiter_bytes():
                raw += chunk.decode("utf-8", errors="replace")
                if raw.count("\n\n") >= n:
                    break
    return _parse_sse(raw), resp


@pytest.mark.asyncio
async def test_sse_content_type_and_first_event(live_server, db):
    """SSE 返回 200 + text/event-stream + 至少一个事件"""
    from tests.conftest import insert_discussion, publish_test_event

    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    await publish_test_event(db, "test-dummy", "utterance", {
        "id": "test-u-0", "round_no": 0, "panelist_id": "p-0",
        "panelist_name": "测试主持", "panelist_title": "主持人",
        "panelist_color": "#38BDF8", "type": "opening",
        "content": "欢迎来到测试讨论", "created_at": "2026-06-26T10:00:00Z",
    })

    events, resp = await _read_sse(f"{live_server}{STREAM_PATH}", n=1)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    assert len(events) >= 1, "Expected >= 1 SSE event"


@pytest.mark.asyncio
async def test_sse_utterance_event_format(live_server, db):
    """utterance 含 id/event/data 三段，data 为合法 JSON 含 round_no/content/panelist_name/panelist_color"""
    from tests.conftest import insert_discussion, publish_test_event

    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    for i in range(3):
        await publish_test_event(db, "test-dummy", "utterance", {
            "id": f"test-u-{i}", "round_no": i,
            "panelist_id": f"p-{i % 2}",
            "panelist_name": f"专家{i}", "panelist_title": f"Title{i}",
            "panelist_color": "#818CF8", "type": "statement",
            "content": f"发言内容{i}", "created_at": "2026-06-26T10:00:00Z",
        })

    events, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=3)
    u_events = [e for e in events if e.get("event") == "utterance"]
    assert len(u_events) >= 1, f"No utterance in {len(events)} events"

    u = u_events[0]
    assert "id" in u and "event" in u and "data" in u, f"Bad SSE format: {u}"

    payload = json.loads(u["data"])
    for key in ("round_no", "content", "panelist_name", "panelist_color"):
        assert key in payload, f"Missing '{key}' in data: {payload}"


@pytest.mark.asyncio
async def test_sse_reconnect_snapshot_first(live_server, db):
    """带 Last-Event-ID 重连：首个事件为 snapshot。

    策略：先发事件 → 首连读1个拿到 last_id → 再连验证 snapshot 排第一。
    用少数量避免 HTTP chunk 批量导致 last_id 拿成最大 seq。
    """
    from tests.conftest import insert_discussion, publish_test_event

    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    # Publish events to build up state
    for i in range(3):
        await publish_test_event(db, "test-dummy", "utterance", {
            "id": f"test-u-{i}", "round_no": i,
            "panelist_id": f"p-{i % 3}", "panelist_name": f"专家{i % 3}",
            "panelist_title": f"Title{i % 3}", "panelist_color": "#818CF8",
            "type": "statement", "content": f"发言{i}",
            "created_at": "2026-06-26T10:00:00Z",
        })

    # 首次连接——读 2 个事件作为断线前的状态
    events1, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=2)
    assert len(events1) >= 2, f"Expected >=2 events, got {len(events1)}"

    # 取第一个带 id 的事件（模拟浏览器只收到第一个 utterance）
    last_id = None
    for e in events1:
        if e.get("id"):
            last_id = e["id"]
            break
    assert last_id is not None, "No event with id found in first batch"

    # 重连——期望首个事件为 snapshot
    events2, _ = await _read_sse(
        f"{live_server}{STREAM_PATH}", n=3,
        extra_headers={"Last-Event-ID": last_id},
    )
    assert len(events2) >= 1, f"Expected >=1 event on reconnect, got {len(events2)}"
    assert events2[0]["event"] == "snapshot", \
        f"Expected snapshot first, got '{events2[0].get('event')}'"


@pytest.mark.asyncio
async def test_snapshot_has_no_id_field_does_not_pollute_last_event_id(live_server, db):
    """回归测试: snapshot 不带 id 字段，不污染浏览器 Last-Event-ID。

    场景: 收到 utterance(seq=N) → 断线 → 用 N 重连 → snapshot 不修改 lastEventId。
    heartbeat 格式由 tests/unit/test_sse_heartbeat_format.py 覆盖。
    """
    from tests.conftest import insert_discussion, publish_test_event

    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    for i in range(6):
        await publish_test_event(db, "test-dummy", "utterance", {
            "id": f"test-u-{i}", "round_no": i,
            "panelist_id": f"p-{i % 3}", "panelist_name": f"专家{i % 3}",
            "panelist_title": f"Title{i % 3}", "panelist_color": "#818CF8",
            "type": "statement", "content": f"发言{i}",
            "created_at": "2026-06-26T10:00:00Z",
        })

    # 首次连接——读到 2 个事件拿到一个有效 id
    events1, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=2)
    u_events = [e for e in events1 if e.get("event") == "utterance"]
    assert len(u_events) >= 1, f"Expected >=1 utterances, got {len(u_events)}"

    # 取第一个 utterance 的 id
    last_id = u_events[0]["id"]
    assert last_id, f"Last utterance id is empty"

    # 重连: snapshot + replayed events (seq > last_id) + remaining queue events ≥ 3
    events2, _ = await _read_sse(
        f"{live_server}{STREAM_PATH}", n=3,
        extra_headers={"Last-Event-ID": last_id},
    )
    assert len(events2) >= 1
    assert events2[0]["event"] == "snapshot", \
        f"Expected snapshot first on reconnect, got '{events2[0].get('event')}'"

    # 关键断言: snapshot 不得携带 id 字段
    snap = events2[0]
    assert "id" not in snap or snap["id"] == "", \
        f"snapshot MUST NOT have id field, got id={snap.get('id')}"

    # 验证 snapshot 之后的回放事件有正确的 id
    replay_events = events2[1:]
    for evt in replay_events:
        if evt["event"] == "utterance":
            assert "id" in evt and evt["id"], \
                f"Replayed utterance must have non-empty id, got {evt}"
