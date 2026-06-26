"""共享 pytest 夹具：临时数据库 + FastAPI TestClient + Live Server。

绝不污染 seed 数据库。
"""
import os
import uuid
import socket
import pytest
import aiosqlite
import httpx
from datetime import datetime, timezone

from app.main import app
from app.database import get_db, init_db


def _now():
    return datetime.now(timezone.utc).isoformat()


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ── 临时数据库 fixture ──────────────────────────────────────────

@pytest.fixture
async def db():
    """创建临时 aiosqlite 数据库，初始化 schema，yield 连接，完成后清理。"""
    db_path = f"data/test_{uuid.uuid4().hex}.db"
    os.makedirs("data", exist_ok=True)

    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")

    # 临时覆盖 database 模块的全局 _db
    import app.database as db_module
    db_module._db = conn

    await init_db()

    yield conn

    await conn.close()
    db_module._db = None
    try:
        os.remove(db_path)
    except OSError:
        pass


# ── FastAPI 依赖覆盖（REST 测试用 ASGITransport）───────────────

@pytest.fixture
async def client(db):
    """返回 AsyncClient，其 get_db 依赖被覆盖为测试数据库（ASGI 直连，用于 REST）。"""
    async def override_get_db():
        return db

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Live Server fixture（SSE 测试用真实 HTTP 连接）──────────────

@pytest.fixture
async def live_server(db):
    """启动 uvicorn 真实 HTTP 服务器，返回 base_url。SSE 流测试用。"""
    import uvicorn
    import app.api.sse.manager as sse_manager
    import app.api.sse.events as sse_events

    # 清理上个测试残留的全局状态
    sse_manager._registry.clear()
    for t in sse_events._fake_tasks.values():
        t.cancel()
    sse_events._fake_tasks.clear()
    sse_events._fake_rounds.clear()

    async def override_get_db():
        return db

    app.dependency_overrides[get_db] = override_get_db

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    async def serve():
        await server.serve()

    import asyncio
    task = asyncio.ensure_future(serve())
    await asyncio.sleep(0.5)

    yield base_url

    server.should_exit = True
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    # 测试结束后清理
    for t in sse_events._fake_tasks.values():
        t.cancel()
    sse_events._fake_tasks.clear()
    sse_events._fake_rounds.clear()
    sse_manager._registry.clear()

    app.dependency_overrides.clear()


# ── 辅助函数：插入测试数据 ──────────────────────────────────────

async def insert_discussion(db, id, topic, status="in_progress", expert_count=3, max_rounds=30, current_round=0, created_at=None, ended_at=None):
    await db.execute(
        "INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at, ended_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (id, topic, status, expert_count, max_rounds, current_round, created_at or _now(), ended_at),
    )
    await db.commit()


async def insert_panelist(db, id, discussion_id, role="expert", name="测试专家", title="测试Title", stance="测试立场", color="#DC2626", status="idle", sort_order=1):
    await db.execute(
        "INSERT INTO panelist (id, discussion_id, role, name, title, stance, color, status, public_focus, sort_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', ?)",
        (id, discussion_id, role, name, title, stance, color, status, sort_order),
    )
    await db.commit()
