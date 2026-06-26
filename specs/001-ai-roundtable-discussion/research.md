# Research: AI Panel Studio — Phase 0

**Date**: 2026-06-26

## 1. DeepSeek API Integration

**Decision**: Use DeepSeek Chat API (`deepseek-chat` model) via httpx async client. All LLM calls proxied through backend only.

**Rationale**:
- DeepSeek API is OpenAI-compatible, supporting chat completions with system/user/assistant roles
- API Key loaded from `backend/.env` (`DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`)
- httpx chosen over openai SDK for lighter dependency footprint; OpenAI-compatible endpoint allows standard REST calls
- All prompt assembly happens server-side; frontend never sees model name or API key

**Alternatives considered**:
- openai Python SDK: Rejected — adds dependency weight for a single endpoint call pattern
- Multiple model providers: Rejected for MVP — single provider simplifies key management and prompt tuning

**Prompt Engineering Strategy**:
- Panelist generation: System prompt defines host + expert archetype generation with JSON output format
- Speech scheduling: Conversation-style prompt with full transcript context, each panelist evaluates whether to speak
- Consensus extraction: Analytical prompt asking model to identify agreement/disagreement points from recent utterances
- Host summary: Narrative prompt with full transcript, requesting natural language summary

### DeepSeek API Call Patterns

```
POST https://api.deepseek.com/v1/chat/completions
Authorization: Bearer $DEEPSEEK_API_KEY
{
  "model": "deepseek-chat",
  "messages": [...],
  "temperature": 0.8,      // Higher for panelist generation (diversity)
  "response_format": { "type": "json_object" }  // For structured outputs
}
```

- Panelist generation: temperature 0.8–1.0 (creativity for diverse personas)
- Speech scheduling: temperature 0.6–0.8 (balanced)
- Consensus extraction: temperature 0.3–0.5 (precision)
- Host summary: temperature 0.5–0.7 (natural but faithful)

---

## 2. FastAPI SSE (Server-Sent Events)

**Decision**: Use `StreamingResponse` with async generators. Each discussion gets its own SSE channel managed via asyncio queues.

**Rationale**:
- FastAPI natively supports `StreamingResponse` for SSE — no extra dependencies
- `asyncio.Queue` per discussion enables fan-out to multiple connected clients
- SSE is unidirectional (server→client) — ideal for transcript/consensus push; client actions go through REST

**Alternatives considered**:
- WebSockets: Rejected — bidirectional not needed; SSE is simpler, auto-reconnects, works through most proxies
- Polling: Rejected — violates real-time requirement and wastes resources

**SSE Event Types**:

| Event | Data | Trigger |
|-------|------|---------|
| `utterance` | {id, panelist_id, name, title, content, color, type, seq, timestamp} | New utterance created |
| `panelist_status` | {panelist_id, status, public_focus[]} | Panelist state change |
| `consensus_update` | {consensus_id, content, involved_panelists[]} | Consensus point created/updated |
| `divergence_update` | {divergence_id, description, camps[]} | Divergence point created/updated |
| `discussion_end` | {discussion_id, summary} | Discussion concluded |
| `heartbeat` | {timestamp} | Every 15s to keep connection alive |

**Snapshot + Last-Event-ID Recovery**:
- Each SSE event carries an `id` field (monotonic sequence number per discussion)
- Client tracks `lastEventId`; on reconnect, sends `Last-Event-ID` header
- Server receives `Last-Event-ID`, returns snapshot (current consensus + last 20 utterances), then replays events after that ID
- Sequence numbers stored in `event` table alongside utterance/consensus records

---

## 3. SQLite Async Patterns

**Decision**: Use `aiosqlite` with WAL journal mode for concurrent read access.

**Rationale**:
- SQLite is zero-config, perfect for MVP single-server deployment
- WAL mode allows concurrent reads while a write is in progress — critical for SSE read-heavy pattern while utterances are being written
- aiosqlite wraps sqlite3 for asyncio compatibility
- Single-file DB simplifies backup and teardown per discussion

**Alternatives considered**:
- PostgreSQL: Rejected for MVP — operational overhead disproportionate to scale (10 concurrent discussions)
- SQLAlchemy async: Considered but aiosqlite + raw SQL is simpler for MVP schema; can migrate later
- Tortoise ORM: Rejected — adds abstraction layer not needed for 5 tables

**Schema Strategy**:
- All tables include `discussion_id TEXT NOT NULL` as first indexed column
- Queries always filter by `WHERE discussion_id = ?`
- Foreign keys: `ON DELETE CASCADE` from discussion → panelist/utterance/event/consensus_point

---

## 4. React SSE Client

**Decision**: Use native `EventSource` API with custom reconnection wrapper hook (`useSSE`).

**Rationale**:
- `EventSource` is built into all modern browsers — zero dependency
- Auto-reconnects on connection loss with `Last-Event-ID` header
- Custom `useSSE` hook encapsulates: connection lifecycle, event parsing, reconnection state, snapshot recovery

**Alternatives considered**:
- `@microsoft/fetch-event-source`: Rejected — adds dependency; native EventSource suffices for unidirectional SSE
- `eventsource` polyfill: Not needed — all target browsers support EventSource

**Reconnection Flow**:
1. `EventSource` auto-reconnects with `Last-Event-ID` header
2. Server detects `Last-Event-ID`, returns snapshot then replays missed events
3. Client merges snapshot into existing state, then processes replayed events normally
4. Max reconnection attempts: infinite with exponential backoff (browser default)

---

## 5. Content Moderation — Pluggable Architecture

**Decision**: Abstract interface `ContentModerator` with MVP default implementation using keyword + length checks. Interface designed for future third-party service integration.

**Rationale**:
- MVP needs basic filtering (empty, too long, obvious profanity) — keyword list suffices
- Pluggable interface ensures no refactoring when upgrading to third-party service
- Allows per-environment configuration (local keyword list for dev, API service for prod)

**Interface Design**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ModerationResult:
    allowed: bool
    reason: str | None = None  # Human-readable rejection reason (Chinese)

class ContentModerator(ABC):
    @abstractmethod
    async def check_topic(self, topic: str) -> ModerationResult:
        """Validate discussion topic text."""
        ...

class LocalContentModerator(ContentModerator):
    """MVP: keyword blocklist + length check (1-200 chars)."""
    ...

# Future: ThirdPartyContentModerator(ContentModerator)
```

**Alternatives considered**:
- Hardcoded validation in route handler: Rejected — violates single responsibility and makes migration harder
- No moderation: Rejected — FR-002 requires content review service check

---

## 6. Panelist Color Palette

**Decision**: Use a hand-picked palette of 9 distinguishable colors, assigned sequentially on panelist generation.

**Rationale**:
- Maximum 9 panelists (1 host + 8 experts) → need 9 distinct colors
- Colors chosen for: mutual distinguishability, WCAG AA contrast on both light/dark backgrounds, colorblind-safe subset
- Host always gets the first color (prominent, stable identifier)

**Palette** (CSS variables approach for theming):

| Index | Color | Hex | Role |
|-------|-------|-----|------|
| 0 | 深蓝 | #2563EB | Host default |
| 1 | 朱红 | #DC2626 | Expert |
| 2 | 翠绿 | #059669 | Expert |
| 3 | 琥珀 | #D97706 | Expert |
| 4 | 紫罗兰 | #7C3AED | Expert |
| 5 | 天蓝 | #0891B2 | Expert |
| 6 | 品红 | #DB2777 | Expert |
| 7 | 青绿 | #65A30D | Expert |
| 8 | 石板灰 | #4B5563 | Expert |

**Alternatives considered**:
- Algorithmic color generation: Rejected — hard to guarantee distinguishability and contrast
- User-assigned colors: Rejected — adds friction to creation flow

---

## 7. Speech Scheduling Strategy

**Decision**: LLM-driven round-based scheduling. Each round, the scheduling prompt includes full transcript + panelist states; the DeepSeek model returns who speaks next and what type (statement/rebuttal/supplement).

**Rationale**:
- Constitution VI requires non-mechanical turn-taking — LLM must evaluate context to decide
- Round-based (not timer-based) ensures natural pacing: one utterance completes, next is decided
- Panelist states (idle/preparing/speaking/silent) injected into scheduling prompt as context

**Scheduling Flow**:
1. After each utterance or host action, scheduling service assembles prompt:
   - System: "You are a discussion moderator. Decide which panelist should speak next."
   - Context: Full transcript (last N utterances if too long), panelist states, consensus status
   - Constraints: No mechanical round-robin, 1-2 sentences per utterance, prioritize rebuttals/supplements
2. LLM returns: `{ "next_speaker": panelist_id, "type": "rebuttal|supplement|statement|question_response", "reason": "..." }`
3. If no panelist volunteers (all silent/idle for 2+ rounds), host is prompted to ask a question or move toward summary
4. After 30 rounds total → forced summary

**Alternatives considered**:
- Rule-based scheduling: Rejected — cannot achieve natural discussion feel
- Timer-based with "buzzer": Rejected — adds complexity without improving discussion quality
- Multi-agent framework (CrewAI/AutoGen): Rejected for MVP — heavyweight, harder to control output format

---

## Summary of Technical Decisions

| Area | Decision | Key Dependency |
|------|----------|---------------|
| LLM API | DeepSeek Chat via httpx | `DEEPSEEK_API_KEY` env var |
| Real-time push | FastAPI StreamingResponse (SSE) | asyncio.Queue |
| Database | SQLite via aiosqlite (WAL mode) | — |
| SSE Client | Native EventSource + useSSE hook | — |
| Content Moderation | Pluggable interface, MVP local impl | — |
| Color System | 9-color preset palette | — |
| Speech Scheduling | LLM-driven round-based | DeepSeek API |
| Testing | pytest + vitest + Playwright | — |
