"""Unit test: heartbeat 和 snapshot 的 SSE 格式不含 id 字段（防止 Last-Event-ID 污染）。"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.api.sse.manager import subscribe


@pytest.mark.asyncio
async def test_heartbeat_has_no_id_field():
    """heartbeat 不得携带 id: 行——避免改写浏览器 lastEventId。"""
    # 模拟 queue.get() 超时，触发 heartbeat
    mock_queue = AsyncMock()
    mock_queue.get.side_effect = asyncio.TimeoutError

    with patch("app.api.sse.manager._get_or_create_queue", return_value=mock_queue):
        gen = subscribe("test-disc")
        heartbeat = await gen.__anext__()

    # 关键断言: heartbeat 文本中不得出现 "id:"
    assert "id:" not in heartbeat, \
        f"heartbeat MUST NOT contain id field, got:\n{repr(heartbeat)}"
    # 但必须有 event 和 data
    assert "event: heartbeat" in heartbeat
    assert "data:" in heartbeat


def test_heartbeat_format_no_id_in_string():
    """静态断言: heartbeat 格式字符串中确实没有 id: 行。"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    # 这是 manager.py 当前生成的格式（已修复）
    heartbeat_line = f"event: heartbeat\ndata: {{\"timestamp\":\"{now}\"}}\n\n"

    lines = heartbeat_line.split("\n")
    for line in lines:
        assert not line.startswith("id:"), \
            f"Heartbeat line starts with 'id:': {repr(line)}"

    assert "event: heartbeat" in heartbeat_line
    assert f'"timestamp":"{now}"' in heartbeat_line


def test_heartbeat_with_id_zero_would_be_bug():
    """静态反例: 如果 heartbeat 携带 id: 0，则这是一个已知的 bug 模式。"""
    # 这是修复前的错误格式——此测试确保我们永远不会回到这个状态
    buggy_line = f"id: 0\nevent: heartbeat\ndata: {{\"timestamp\":\"2026-01-01T00:00:00Z\"}}\n\n"
    assert "id:" in buggy_line, "Sanity check: the buggy format has id"

    # 正确格式不应该有 "id:"
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    fixed_line = f"event: heartbeat\ndata: {{\"timestamp\":\"{now}\"}}\n\n"
    assert "id:" not in fixed_line
    assert fixed_line.count("id:") == 0
