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


async def _read_sse(url: str, n=4, extra_headers=None) -> tuple[list[dict], httpx.Response]:
    """通过真实 HTTP 读取 n 个 SSE 事件后断开。"""
    raw = ""
    async with httpx.AsyncClient() as client:
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
    from tests.conftest import insert_discussion
    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    events, resp = await _read_sse(f"{live_server}{STREAM_PATH}", n=1)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    assert len(events) >= 1, "Expected >= 1 SSE event"


@pytest.mark.asyncio
async def test_sse_utterance_event_format(live_server, db):
    """utterance 含 id/event/data 三段，data 为合法 JSON 含 round_no/content/panelist_name/panelist_color"""
    from tests.conftest import insert_discussion
    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

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
    """带 Last-Event-ID 重连：首个事件为 snapshot"""
    from tests.conftest import insert_discussion
    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    # 首次连接——积累一些事件作为断线前的状态
    events1, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=2)
    last_id = events1[-1].get("id", "0")

    # 重连
    events2, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=3, extra_headers={"Last-Event-ID": last_id})
    assert len(events2) >= 1
    assert events2[0]["event"] == "snapshot", \
        f"Expected snapshot first, got '{events2[0].get('event')}'"


@pytest.mark.asyncio
async def test_snapshot_has_no_id_field_does_not_pollute_last_event_id(live_server, db):
    """回归测试: snapshot 不带 id 字段，不污染浏览器 Last-Event-ID。

    场景: 收到 utterance(seq=N) → 断线 → 用 N 重连 → snapshot 不修改 lastEventId。
    heartbeat 格式由 tests/unit/test_sse_heartbeat_format.py 覆盖。
    """
    from tests.conftest import insert_discussion
    await insert_discussion(db, "test-dummy", "测试SSE讨论", status="in_progress")

    # 首次连接——读到几个 utterance
    events1, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=3)
    u_events = [e for e in events1 if e.get("event") == "utterance"]
    assert len(u_events) >= 2

    # 模拟浏览器: 最后一个带 id 的事件决定 Last-Event-ID
    last_id = None
    for e in events1:
        if "id" in e and e["id"]:
            last_id = e["id"]
    assert last_id is not None
    assert last_id != "0", f"Utterance id should never be 0, got {last_id}"

    # 重连: 用 last_id 作为 Last-Event-ID
    events2, _ = await _read_sse(f"{live_server}{STREAM_PATH}", n=3,
                                 extra_headers={"Last-Event-ID": last_id})
    assert len(events2) >= 1
    assert events2[0]["event"] == "snapshot", \
        f"Expected snapshot first on reconnect, got '{events2[0].get('event')}'"

    # 关键断言: snapshot 不得携带 id 字段（否则会将浏览器 lastEventId 改写为 0）
    snap = events2[0]
    assert "id" not in snap or snap["id"] == "", \
        f"snapshot MUST NOT have id field to avoid polluting browser lastEventId, got id={snap.get('id')}"

    # 验证 snapshot 之后的回放事件有正确的 id
    replay_events = events2[1:]
    for evt in replay_events:
        if evt["event"] == "utterance":
            assert "id" in evt and evt["id"], \
                f"Replayed utterance must have non-empty id, got {evt}"
