"""aiosqlite 异步连接管理 + Schema 迁移（幂等 CREATE TABLE IF NOT EXISTS）。"""
import os
import aiosqlite

from app.config import settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """FastAPI 依赖：返回共享的 aiosqlite 连接（WAL 模式）。"""
    global _db
    if _db is None:
        os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)
        _db = await aiosqlite.connect(settings.database_path)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def close_db():
    """应用关闭时调用，安全关闭数据库连接。"""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


async def init_db():
    """幂等建表 + 索引（数据模型参考 data-model.md）。"""
    db = await get_db()

    # ── discussion ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS discussion (
            id          TEXT PRIMARY KEY,
            topic       TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending_panelists',
            expert_count INTEGER NOT NULL,
            max_rounds  INTEGER NOT NULL DEFAULT 30,
            current_round INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            ended_at    TEXT
        )
    """)

    # ── panelist ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS panelist (
            id              TEXT PRIMARY KEY,
            discussion_id   TEXT NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
            role            TEXT NOT NULL,
            name            TEXT NOT NULL,
            title           TEXT NOT NULL,
            stance          TEXT NOT NULL,
            color           TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'idle',
            public_focus    TEXT NOT NULL DEFAULT '[]',
            sort_order      INTEGER NOT NULL DEFAULT 0
        )
    """)

    # ── utterance ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS utterance (
            id              TEXT PRIMARY KEY,
            discussion_id   TEXT NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
            panelist_id     TEXT NOT NULL REFERENCES panelist(id) ON DELETE CASCADE,
            round_no        INTEGER NOT NULL,
            type            TEXT NOT NULL,
            content         TEXT NOT NULL,
            created_at      TEXT NOT NULL
        )
    """)

    # ── consensus_point ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS consensus_point (
            id                    TEXT PRIMARY KEY,
            discussion_id         TEXT NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
            content               TEXT NOT NULL,
            involved_panelist_ids TEXT NOT NULL DEFAULT '[]',
            created_at            TEXT NOT NULL,
            updated_at            TEXT NOT NULL
        )
    """)

    # ── divergence_point ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS divergence_point (
            id              TEXT PRIMARY KEY,
            discussion_id   TEXT NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
            description     TEXT NOT NULL,
            camps           TEXT NOT NULL DEFAULT '[]',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)

    # ── event ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS event (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            discussion_id   TEXT NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
            seq             INTEGER NOT NULL,
            event_type      TEXT NOT NULL,
            payload_json    TEXT NOT NULL,
            created_at      TEXT NOT NULL
        )
    """)

    # ── Indexes ──
    await db.execute("CREATE INDEX IF NOT EXISTS idx_discussion_status ON discussion(status)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_panelist_discussion ON panelist(discussion_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_utterance_discussion ON utterance(discussion_id)")
    await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_utterance_discussion_round ON utterance(discussion_id, round_no)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_consensus_discussion ON consensus_point(discussion_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_divergence_discussion ON divergence_point(discussion_id)")
    await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_event_discussion_seq ON event(discussion_id, seq)")

    await db.commit()
