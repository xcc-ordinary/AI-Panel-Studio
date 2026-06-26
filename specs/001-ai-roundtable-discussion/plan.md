# Implementation Plan: AI Panel Studio — AI圆桌讨论核心功能

**Branch**: `001-ai-roundtable-discussion` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-ai-roundtable-discussion/spec.md`

## Summary

构建 AI Panel Studio 的 MVP 核心功能：首页讨论列表、LLM 嘉宾阵容生成、演播厅实时讨论（主持人调度 + 专家自主发言 + 实时共识提炼）、多讨论并行隔离。后端 Python FastAPI + SQLite + SSE 实时推送；前端 React + Vite + TypeScript strict；大模型经后端代理调用 DeepSeek，前端零密钥暴露。

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 6 (frontend)

**Primary Dependencies**:
- Backend: FastAPI (async), uvicorn, aiosqlite, httpx (DeepSeek API client), pydantic
- Frontend: React 19, Vite 8, TypeScript strict, oxlint

**Storage**: SQLite via aiosqlite (async), single-file DB per environment. Tables: discussion, panelist, utterance, event, consensus_point — all keyed by discussion_id.

**Testing**: pytest + pytest-asyncio (backend unit/integration), vitest (frontend unit), Playwright (E2E)

**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge latest 2 versions). SSE support required.

**Project Type**: Web application — `frontend/` (React SPA) + `backend/` (FastAPI REST + SSE)

**Performance Goals**:
- Panelist generation: <10s end-to-end
- Consensus update latency: <3s post-utterance
- SSE reconnection recovery: <3s to latest state
- Concurrent discussions: ≥10 with full data isolation

**Constraints**:
- DeepSeek API Key in `backend/.env` only — never exposed to frontend
- All data scoped by `discussion_id` — cross-discussion queries forbidden except admin audit
- Chinese UI throughout
- Responsive: desktop (≥1024px), tablet (768-1023px), mobile (<768px)
- Independent scrolling per logical area in studio view

**Scale/Scope**: MVP — open access (no auth), 10 concurrent discussions, 2-8 panelists each, max 30 rounds per discussion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. 前后端分离架构 | ✅ PASS | `frontend/` (React SPA) ↔ `backend/` (FastAPI), REST + SSE communication only |
| II. 代码质量标准 | ✅ PASS | TypeScript strict enabled; Python type hints; modules organized by responsibility |
| III. TDD (核心逻辑) | ⚠ GATE | panelist generation, speech scheduling, consensus extraction MUST follow Red-Green-Refactor in implementation phase. Plan defines test structure; actual TDD enforcement in `/speckit-tasks` and `/speckit-implement` |
| IV. 安全第一 | ✅ PASS | DeepSeek API key in `backend/.env`; all LLM calls proxied through backend API endpoints |
| V. 数据隔离 | ✅ PASS | All entities keyed by `discussion_id`; API routes scoped `/api/discussions/{id}/...`; SSE channels per-discussion |
| VI. 实时共识 | ✅ PASS | SSE incremental consensus updates after each utterance round; snapshot + Last-Event-ID recovery |

**Gate Result**: PASS — Principle III (TDD) flagged for implementation-phase enforcement; all design-time principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-roundtable-discussion/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api-rest.md      # REST endpoint contracts
│   └── api-sse.md       # SSE event stream contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # Pydantic + DB models (discussion, panelist, utterance, event, consensus_point)
│   ├── services/        # Business logic: panelist_generator, speech_scheduler, consensus_extractor, content_moderator
│   ├── api/
│   │   ├── routes/      # FastAPI route handlers
│   │   └── sse/         # SSE stream endpoints
│   ├── llm/             # DeepSeek API client (prompt templates, response parsing)
│   └── core/            # Config, logging, database setup
├── tests/
│   ├── unit/            # Service-level unit tests
│   ├── integration/     # API + DB integration tests
│   └── contract/        # API contract tests
└── requirements.txt

frontend/
├── src/
│   ├── components/      # React components
│   │   ├── home/        # DiscussionList, DiscussionCard, CreateDiscussion
│   │   ├── studio/      # StudioView, TranscriptPanel, ConsensusPanel, PanelistWindow
│   │   └── shared/      # ColorBadge, StatusIndicator, LoadingSkeleton, EmptyState
│   ├── hooks/           # useSSE, useDiscussion, useConsensus
│   ├── services/        # API client, SSE client (reconnection logic)
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Color palette, formatters
├── tests/
│   ├── unit/
│   └── e2e/             # Playwright E2E tests
├── index.html
├── vite.config.ts
└── tsconfig.json
```

**Structure Decision**: Web application with separate `frontend/` and `backend/` directories. Frontend is a Vite SPA with component/hook/service layers; backend is a FastAPI app with models/services/api layers. All entities scoped by `discussion_id` for data isolation.

## Complexity Tracking

> No constitution violations to justify. All principles pass the design-time gate.
