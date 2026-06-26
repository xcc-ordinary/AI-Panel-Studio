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
