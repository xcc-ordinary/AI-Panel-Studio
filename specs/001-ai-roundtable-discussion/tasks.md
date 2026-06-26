# Tasks: AI Panel Studio — AI圆桌讨论核心功能

**Input**: Design documents from `specs/001-ai-roundtable-discussion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution Principle III mandates TDD for core logic (嘉宾生成/发言调度/共识提炼). Test tasks MUST be written and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Tests: `backend/tests/unit/`, `backend/tests/integration/`, `frontend/tests/unit/`, `frontend/tests/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for both frontend and backend

- [ ] T001 [P] Initialize backend project structure per plan.md: create `backend/src/`, `backend/tests/` directories and subdirectories (models/, services/, api/routes/, api/sse/, llm/, core/)
- [ ] T002 [P] Initialize frontend project structure: verify existing `frontend/src/` layout, create `frontend/src/components/home/`, `frontend/src/components/studio/`, `frontend/src/components/shared/`, `frontend/src/hooks/`, `frontend/src/services/`, `frontend/src/types/`, `frontend/src/utils/`, `frontend/tests/unit/`, `frontend/tests/e2e/`
- [ ] T003 [P] Configure backend dev tooling: add `ruff` to `backend/requirements.txt`, create `pyproject.toml` with ruff rules
- [ ] T004 [P] Verify frontend tooling: ensure `tsconfig.json` has `"strict": true`, verify oxlint and vitest are configured in `frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create backend configuration: `backend/src/core/config.py` — load env vars (DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DATABASE_PATH, MAX_CONCURRENT_DISCUSSIONS, DEFAULT_MAX_ROUNDS) via pydantic-settings
- [ ] T006 Create backend database setup: `backend/src/core/database.py` — async SQLite connection via aiosqlite with WAL mode, `get_db()` dependency
- [ ] T007 [P] Create frontend TypeScript types: `frontend/src/types/index.ts` — Discussion, Panelist, Utterance, ConsensusPoint, DivergencePoint, PanelistStatus, SSEEvent interfaces matching data-model.md
- [ ] T008 [P] Create frontend API client: `frontend/src/services/api.ts` — base fetch wrapper with `X-Discussion-Id` header, typed request/response helpers
- [ ] T009 [P] Create frontend color utility: `frontend/src/utils/colors.ts` — 9-color preset palette from research.md, `getColor(index: number): string`
- [ ] T010 [P] Create content moderation interface: `backend/src/services/content_moderator.py` — `ContentModerator` abstract base class with `check_topic(topic: str) -> ModerationResult`
- [ ] T011 Create content moderation MVP implementation: `backend/src/services/local_moderator.py` — `LocalContentModerator(ContentModerator)`: keyword blocklist + 1–200 char length check
- [ ] T012 Run DB migrations: `backend/src/core/database.py` — CREATE TABLE statements for discussion, panelist, utterance, consensus_point, divergence_point, event per data-model.md, with indexes and FK ON DELETE CASCADE

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — 发起新讨论：生成嘉宾阵容 (Priority: P1) 🎯 MVP

**Goal**: User inputs topic + expert count → LLM generates 1 host + N experts with names/titles/stances/colors → user confirms or regenerates

**Independent Test**: `POST /api/discussions` → verify response has host + experts with all required fields → `PATCH .../panelists/confirm` → discussion status `in_progress`

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (Constitution III — 嘉宾生成 is core logic)**

- [ ] T013 [P] [US1] Unit test for panelist generator (mock DeepSeek API): `backend/tests/unit/test_panelist_generator.py` — test valid generation with 4 experts, test retry on malformed JSON, test stance diversity assertion
- [ ] T014 [P] [US1] Unit test for content moderator: `backend/tests/unit/test_content_moderator.py` — test empty topic rejection, test too-long topic, test blocked keyword rejection, test valid topic passes
- [ ] T015 [P] [US1] Integration test for POST /api/discussions: `backend/tests/integration/test_create_discussion.py` — test 201 with valid input, test 400 with invalid expert_count, test 422 with rejected topic, test 429 when at concurrency limit

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create Discussion model: `backend/src/models/discussion.py` — Pydantic model + DB CRUD operations (create, get, list, update_status, delete)
- [ ] T017 [P] [US1] Create Panelist model: `backend/src/models/panelist.py` — Pydantic model + DB CRUD (create_batch for discussion, get_by_discussion, delete_by_discussion)
- [ ] T018 [US1] Implement PanelistGenerator service: `backend/src/services/panelist_generator.py` — `generate(topic, expert_count) -> list[Panelist]`: assemble DeepSeek prompt, parse JSON response, validate diversity, assign colors from preset palette (depends on T016, T017)
- [ ] T019 [US1] Implement DeepSeek LLM client: `backend/src/llm/client.py` — async httpx client with `chat_completion(messages, temperature, response_format)` calling `https://api.deepseek.com/v1/chat/completions`
- [ ] T020 [US1] Implement prompt templates for panelist generation: `backend/src/llm/prompts.py` — `PANELIST_GENERATION_SYSTEM` and `PANELIST_GENERATION_USER` templates with JSON output format spec
- [ ] T021 [US1] Create POST /api/discussions route: `backend/src/api/routes/discussions.py` — validate input, call content moderator, call panelist generator, create Discussion + Panelist records, return 201
- [ ] T022 [US1] Create PATCH /api/discussions/{id}/panelists/confirm route: `backend/src/api/routes/panelists.py` — transition discussion status to `in_progress`, return 400 if no panelists
- [ ] T023 [US1] Create POST /api/discussions/{id}/panelists/regenerate route: `backend/src/api/routes/panelists.py` — delete existing panelists, re-call generator, return new roster
- [ ] T024 [P] [US1] Create frontend CreateDiscussion component: `frontend/src/components/home/CreateDiscussion.tsx` — topic input, expert count selector (2-8), submit button, loading state during generation
- [ ] T025 [P] [US1] Create frontend PanelistRoster component: `frontend/src/components/home/PanelistRoster.tsx` — display generated panelists as cards (name, title, stance, color badge), confirm/regenerate buttons
- [ ] T026 [P] [US1] Create frontend ColorBadge shared component: `frontend/src/components/shared/ColorBadge.tsx` — colored circle/badge using panelist.color hex
- [ ] T027 [P] [US1] Create frontend LoadingSkeleton shared component: `frontend/src/components/shared/LoadingSkeleton.tsx` — skeleton placeholder for async loading states
- [ ] T028 [US1] Wire US1 frontend flow: `frontend/src/services/api.ts` — add `createDiscussion()`, `confirmPanelists()`, `regeneratePanelists()` methods. Connect CreateDiscussion → PanelistRoster → navigate to studio on confirm

**Checkpoint**: User can create discussion, generate panelists, confirm roster, and arrive at studio URL

---

## Phase 4: User Story 2 — 首页讨论列表与加入观察 (Priority: P1)

**Goal**: Homepage shows all discussions (active/ended), user can join to observe or create new

**Independent Test**: Create 2-3 discussions via API → load homepage → verify cards rendered with correct data → click card → navigate to studio

### Tests for User Story 2

- [ ] T029 [P] [US2] Integration test for GET /api/discussions: `backend/tests/integration/test_list_discussions.py` — test empty list, test multiple discussions, test status filter, test active_count/max_concurrent fields
- [ ] T030 [P] [US2] Integration test for GET /api/discussions/{id}: `backend/tests/integration/test_get_discussion.py` — test existing discussion, test 404 for unknown id

### Implementation for User Story 2

- [ ] T031 [US2] Implement GET /api/discussions route: `backend/src/api/routes/discussions.py` — list all discussions with status, panelist count, round info; include active_count and max_concurrent
- [ ] T032 [US2] Implement GET /api/discussions/{id} route: `backend/src/api/routes/discussions.py` — return full discussion detail with panelists array
- [ ] T033 [US2] Implement DELETE /api/discussions/{id} route: `backend/src/api/routes/discussions.py` — cascade delete discussion and all child records
- [ ] T034 [P] [US2] Create frontend DiscussionCard component: `frontend/src/components/home/DiscussionCard.tsx` — topic, panelist count, current round, start time, status badge (进行中/已结束), click to join
- [ ] T035 [P] [US2] Create frontend DiscussionList component: `frontend/src/components/home/DiscussionList.tsx` — grid/list of DiscussionCards, empty state ("还没有讨论，发起第一场吧")
- [ ] T036 [P] [US2] Create frontend EmptyState shared component: `frontend/src/components/shared/EmptyState.tsx` — illustration + message + optional CTA button
- [ ] T037 [US2] Wire US2 frontend flow: `frontend/src/services/api.ts` — add `listDiscussions()`, `getDiscussion()`, `deleteDiscussion()` methods. Homepage loads DiscussionList on mount. Click card → navigate to `/discussion/{id}`

**Checkpoint**: Homepage fully functional — list discussions, join existing, create new, navigate to studio

---

## Phase 5: User Story 3 — 演播厅实时讨论 (Priority: P1) 🎯 MVP

**Goal**: Studio view with host moderation, expert autonomous turn-taking, real-time transcript, live consensus/divergence, SSE streaming

**Independent Test**: Confirm panelist roster → enter studio → host opening appears → experts speak non-mechanically → transcript scrolls → consensus panel updates → host summarizes in natural language

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (Constitution III — 发言调度 + 共识提炼 are core logic)**

- [ ] T038 [P] [US3] Unit test for speech scheduler (mock DeepSeek API): `backend/tests/unit/test_speech_scheduler.py` — test host opening generated, test expert rebuttal triggered by disagreement, test non-round-robin pattern, test silent detection after N rounds, test forced summary at max_rounds
- [ ] T039 [P] [US3] Unit test for consensus extractor (mock DeepSeek API): `backend/tests/unit/test_consensus_extractor.py` — test consensus point created from agreement, test divergence detected from opposing views, test incremental update merges with existing points, test no JSON in output
- [ ] T040 [P] [US3] Integration test for SSE event stream: `backend/tests/integration/test_sse_events.py` — test utterance event received, test panelist_status event, test consensus_update event, test discussion_end event, test heartbeat interval
- [ ] T041 [P] [US3] Integration test for SSE reconnection: `backend/tests/integration/test_sse_reconnect.py` — test snapshot returned with Last-Event-ID, test missed events replayed after snapshot, test recovery within 3s
- [ ] T042 [P] [US3] Integration test for GET /api/discussions/{id}/transcript: `backend/tests/integration/test_transcript.py` — test pagination with before_round, test has_more flag, test utterance fields complete
- [ ] T043 [P] [US3] Integration test for GET /api/discussions/{id}/consensus/current: `backend/tests/integration/test_consensus_api.py` — test returns current consensus/divergence state, test last_event_seq present

### Implementation for User Story 3

#### Backend — Data Layer

- [ ] T044 [P] [US3] Create Utterance model: `backend/src/models/utterance.py` — Pydantic model + DB CRUD (create, get_by_discussion with before_round pagination, get_recent for snapshot)
- [ ] T045 [P] [US3] Create ConsensusPoint model: `backend/src/models/consensus_point.py` — Pydantic model + DB CRUD (create, update, get_by_discussion)
- [ ] T046 [P] [US3] Create DivergencePoint model: `backend/src/models/divergence_point.py` — Pydantic model + DB CRUD (create, update, get_by_discussion)
- [ ] T047 [P] [US3] Create Event model: `backend/src/models/event.py` — Pydantic model + DB CRUD (create with auto-increment seq per discussion, get_by_discussion with seq > X for replay)

#### Backend — Core Services

- [ ] T048 [US3] Implement speech scheduler service: `backend/src/services/speech_scheduler.py` — `decide_next_speaker(discussion_id, transcript, panelist_states) -> (panelist_id, utterance_type)`: assemble scheduling prompt with full context, parse LLM response, handle no-volunteer fallback, enforce max_rounds check (depends on T044, T019, T020)
- [ ] T049 [US3] Implement consensus extractor service: `backend/src/services/consensus_extractor.py` — `extract(discussion_id, new_utterances) -> (new_consensus[], updated_consensus[], new_divergence[], updated_divergence[])`: assemble extraction prompt, parse LLM response, merge with existing records (depends on T045, T046, T019, T020)
- [ ] T050 [US3] Add prompt templates for speech scheduling and consensus extraction: `backend/src/llm/prompts.py` — `SPEECH_SCHEDULING_SYSTEM/USER`, `CONSENSUS_EXTRACTION_SYSTEM/USER` templates
- [ ] T051 [US3] Implement discussion orchestrator: `backend/src/services/discussion_orchestrator.py` — main discussion loop: host opening → scheduling → utterance → consensus extraction → loop until end. Manages Panelist state transitions (idle/preparing/speaking/silent). Pushes events to SSE queue. (depends on T048, T049)

#### Backend — SSE Infrastructure

- [ ] T052 [US3] Create SSE manager: `backend/src/api/sse/manager.py` — per-discussion `asyncio.Queue` registry, `subscribe(discussion_id) -> AsyncGenerator`, `publish(discussion_id, event)`, `unsubscribe(discussion_id)`, event also persisted to Event table
- [ ] T053 [US3] Create SSE endpoint: `backend/src/api/sse/events.py` — `GET /api/discussions/{id}/events` → StreamingResponse with `text/event-stream`. Handle `Last-Event-ID` header: if present, send snapshot + replay missed events; otherwise start streaming live events
- [ ] T054 [US3] Implement snapshot builder: `backend/src/api/sse/manager.py` — `build_snapshot(discussion_id) -> dict`: current consensus points + divergence points + last 20 utterances + current_round + last_event_seq

#### Backend — API Routes

- [ ] T055 [US3] Implement GET /api/discussions/{id}/transcript route: `backend/src/api/routes/transcript.py` — paginated by before_round, returns utterances with panelist info
- [ ] T056 [US3] Implement GET /api/discussions/{id}/consensus/current route: `backend/src/api/routes/consensus.py` — return current consensus + divergence state + last_event_seq

#### Frontend — SSE Client

- [ ] T057 [P] [US3] Create SSE client hook: `frontend/src/hooks/useSSE.ts` — `useSSE(discussionId)`: EventSource connection, parse events by type, handle reconnection with Last-Event-ID, expose `{ utterance, panelistStatus, consensus, divergence, discussionEnd, isConnected, lastEventSeq }`
- [ ] T058 [P] [US3] Create useDiscussion hook: `frontend/src/hooks/useDiscussion.ts` — fetch discussion detail + panelists, manage loading/error state
- [ ] T059 [P] [US3] Create useConsensus hook: `frontend/src/hooks/useConsensus.ts` — fetch current consensus, merge SSE consensus_update/divergence_update events, maintain sorted list

#### Frontend — Studio Components

- [ ] T060 [P] [US3] Create StudioView layout: `frontend/src/components/studio/StudioView.tsx` — responsive grid layout with independent scroll areas for transcript panel, consensus panel, and panelist windows. Desktop: side-by-side; Mobile: stacked tabs
- [ ] T061 [P] [US3] Create TranscriptPanel component: `frontend/src/components/studio/TranscriptPanel.tsx` — scrollable utterance list, auto-scroll to latest, each entry shows panelist name + title + color badge + content. Load more on scroll up via before_round pagination
- [ ] T062 [P] [US3] Create ConsensusPanel component: `frontend/src/components/studio/ConsensusPanel.tsx` — two sections: "已形成共识" and "存在分歧". Each consensus/divergence as a card. Animate on new/updated items
- [ ] T063 [P] [US3] Create PanelistWindow component: `frontend/src/components/studio/PanelistWindow.tsx` — single panelist status card: color badge, name, title, status indicator (idle/preparing/speaking/silent with distinct icons/animations), public focus list
- [ ] T064 [P] [US3] Create PanelistGrid component: `frontend/src/components/studio/PanelistGrid.tsx` — grid of PanelistWindows for all panelists in the discussion, host visually distinguished at top
- [ ] T065 [P] [US3] Create StatusIndicator shared component: `frontend/src/components/shared/StatusIndicator.tsx` — animated dot/badge for idle/preparing/speaking/silent states
- [ ] T066 [US3] Wire US3 frontend flow: StudioView mounts → useDiscussion fetches data → useSSE connects → events flow through hooks → TranscriptPanel/ConsensusPanel/PanelistGrid update in real-time. Handle discussion_end by showing summary overlay

#### Backend — Discussion Lifecycle

- [ ] T067 [US3] Implement discussion start trigger: `backend/src/api/routes/panelists.py` — on panelist confirm (PATCH), spawn `discussion_orchestrator.run(discussion_id)` as background task via asyncio.create_task
- [ ] T068 [US3] Implement discussion end flow: `backend/src/services/discussion_orchestrator.py` — on end (natural or forced), generate host summary via LLM, emit discussion_end SSE event, update Discussion status to ended, close SSE queues

**Checkpoint**: Full studio experience — host opens, experts speak non-mechanically, transcript streams in real-time, consensus/divergence updates live, host summarizes in natural language

---

## Phase 6: User Story 4 — 多讨论并行与数据隔离 (Priority: P2)

**Goal**: Multiple discussions run simultaneously with strict data isolation. Concurrency limit enforced with friendly rejection.

**Independent Test**: Create Discussion A and B → verify transcripts don't cross-contaminate → verify deleting A doesn't affect B → verify limit enforcement at max_concurrent

### Tests for User Story 4

- [ ] T069 [P] [US4] Integration test for data isolation: `backend/tests/integration/test_data_isolation.py` — create two discussions, add utterances to both, verify cross-discussion queries return only own data, verify cascade delete cleans only target discussion
- [ ] T070 [P] [US4] Integration test for concurrency limit: `backend/tests/integration/test_concurrency_limit.py` — create discussions up to MAX_CONCURRENT_DISCUSSIONS, verify next creation returns 429 with correct active_count/max_concurrent, delete one, verify creation succeeds again

### Implementation for User Story 4

- [ ] T071 [US4] Implement concurrency limit guard: `backend/src/api/routes/discussions.py` — before creating discussion, count active discussions, reject with 429 + active_count/max_concurrent if at limit
- [ ] T072 [US4] Add discussion_id filter enforcement: `backend/src/core/database.py` — add helper `ensure_discussion_scope(query, discussion_id)` for all discussion-scoped queries; add audit comment that cross-discussion queries are forbidden
- [ ] T073 [US4] Verify cascade delete completeness: `backend/src/core/database.py` — verify FK ON DELETE CASCADE covers panelist, utterance, consensus_point, divergence_point, event. Add integration test for orphan record cleanup (T069 covers this)
- [ ] T074 [P] [US4] Frontend concurrency display: `frontend/src/components/home/DiscussionList.tsx` — display "进行中: {active_count}/{max_concurrent}" indicator; show warning style when near limit
- [ ] T075 [P] [US4] Frontend error handling for 429: `frontend/src/components/home/CreateDiscussion.tsx` — catch 429 response, display friendly message "当前讨论已满（N/N），请等待某场讨论结束后再发起"

**Checkpoint**: Multi-discussion with full isolation, concurrency limit enforced end-to-end

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T076 [P] Implement backend structured logging: `backend/src/core/logging.py` — JSON-formatted logs for discussion lifecycle events, SSE connections/disconnections, LLM call durations, errors
- [ ] T077 [P] Frontend responsive polish: audit all components against 3 breakpoints (≥1024px, 768-1023px, <768px). Fix StudioView layout for tablet and mobile
- [ ] T078 [P] Frontend accessibility pass: color contrast WCAG AA check on all color badges, keyboard navigation for studio controls, aria-labels on status indicators
- [ ] T079 [P] Frontend error boundary: `frontend/src/components/shared/ErrorBoundary.tsx` — catch React render errors, display friendly Chinese error message with retry button
- [ ] T080 [P] Backend error handling polish: consistent error response format across all endpoints, translate all error messages to Chinese
- [ ] T081 Write E2E test — full user journey: `frontend/tests/e2e/create-and-watch-discussion.spec.ts` — Playwright: homepage → create discussion → verify panelists → confirm → watch host opening → verify expert utterance appears → verify consensus panel updates → discussion ends with summary
- [ ] T082 [P] Write E2E test — multi-discussion isolation: `frontend/tests/e2e/multi-discussion-isolation.spec.ts` — Playwright: create two discussions, open both in tabs, verify no cross-contamination
- [ ] T083 [P] Write E2E test — reconnection: `frontend/tests/e2e/sse-reconnection.spec.ts` — Playwright: simulate network disconnect during discussion, verify recovery within 3s, verify no missing utterances
- [ ] T084 Run quickstart.md validation: execute all 7 VS scenarios manually or via script, document any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — User Story 1
- **US2 (Phase 4)**: Depends on Foundational — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational + US1 (needs panelists + discussion model) — US2 not required but helpful for navigation
- **US4 (Phase 6)**: Depends on US1+US2+US3 core being complete — adds isolation enforcement and limit
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKS all stories
    ↓
    ├── US1 (嘉宾生成) ── independent ──┐
    ├── US2 (首页列表) ── independent ──┤
    └───────────────────────────────────┘
                    ↓
              US3 (演播厅) ← needs US1 models + US2 for navigation
                    ↓
              US4 (多讨论隔离) ← builds on US1–US3
                    ↓
              Phase 7 (Polish)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution III for US1+T013/T014, US3+T038/T039)
- Models before services
- Services before API routes
- Backend before frontend wiring (though frontend components marked [P] can be built in parallel)
- Story complete before moving to next priority (unless parallel team strategy)

### Parallel Opportunities

- All Setup tasks T001–T004 can run in parallel
- Foundational tasks T007–T011 can run in parallel (T005+T006+T012 are sequential)
- US1 and US2 can be developed in parallel after Foundational (different files, no dependency)
- Within US1: T013–T015 (tests) can run in parallel; T016+T017 (models) can run in parallel; T024–T027 (frontend components) can run in parallel
- Within US3: T044–T047 (models) can run in parallel; T038–T043 (tests) can run in parallel; T060–T065 (frontend components) can run in parallel
- Within US4: T069+T070 (tests) can run in parallel
- Polish tasks T076–T083 can run in parallel

---

## Parallel Example: User Story 3

```bash
# Phase A: Launch all US3 tests together (write them first, watch them FAIL):
Task: "T038 Unit test for speech scheduler in backend/tests/unit/test_speech_scheduler.py"
Task: "T039 Unit test for consensus extractor in backend/tests/unit/test_consensus_extractor.py"
Task: "T040 Integration test for SSE event stream in backend/tests/integration/test_sse_events.py"
Task: "T041 Integration test for SSE reconnection in backend/tests/integration/test_sse_reconnect.py"
Task: "T042 Integration test for transcript in backend/tests/integration/test_transcript.py"
Task: "T043 Integration test for consensus API in backend/tests/integration/test_consensus_api.py"

# Phase B: Launch all US3 models together:
Task: "T044 Create Utterance model in backend/src/models/utterance.py"
Task: "T045 Create ConsensusPoint model in backend/src/models/consensus_point.py"
Task: "T046 Create DivergencePoint model in backend/src/models/divergence_point.py"
Task: "T047 Create Event model in backend/src/models/event.py"

# Phase C: Services (sequential — depend on models + LLM client):
Task: "T048 Implement speech scheduler (depends on T044, T019, T020)"
Task: "T049 Implement consensus extractor (depends on T045, T046, T019, T020)"
Task: "T051 Implement discussion orchestrator (depends on T048, T049)"

# Phase D: Launch all US3 frontend components together:
Task: "T060 Create StudioView in frontend/src/components/studio/StudioView.tsx"
Task: "T061 Create TranscriptPanel in frontend/src/components/studio/TranscriptPanel.tsx"
Task: "T062 Create ConsensusPanel in frontend/src/components/studio/ConsensusPanel.tsx"
Task: "T063 Create PanelistWindow in frontend/src/components/studio/PanelistWindow.tsx"
Task: "T064 Create PanelistGrid in frontend/src/components/studio/PanelistGrid.tsx"
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T012) ← CRITICAL BLOCKER
3. Phase 3: US1 嘉宾生成 (T013–T028) — Write tests FIRST, watch fail, implement
4. Phase 4: US2 首页列表 (T029–T037) — Can run in parallel with US1
5. Phase 5: US3 演播厅 (T038–T068) — Write tests FIRST, watch fail, implement
6. **STOP and VALIDATE**: Run quickstart VS-1 through VS-6
7. Deploy/demo MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Users can create discussions and generate panelists
3. Add US2 → Test independently → Homepage with discussion list, join capability
4. Add US3 → Test independently → Full studio experience (MVP!)
5. Add US4 → Test independently → Multi-discussion with isolation guarantees
6. Polish → Production readiness

### Parallel Team Strategy

With multiple developers after Foundational:
- Developer A: US1 (嘉宾生成 — backend + frontend)
- Developer B: US2 (首页列表 — backend + frontend)
- Once US1+US2 done: Developer A takes US3 backend services, Developer B takes US3 frontend + SSE

---

## Notes

- [P] tasks = different files, no dependencies on other incomplete [P] tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify TDD tests FAIL before implementing core logic services
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution III compliance: T013, T014 (US1 tests) and T038, T039 (US3 tests) are NON-NEGOTIABLE
- Backend `.env` MUST exist with DEEPSEEK_API_KEY before running integration tests
