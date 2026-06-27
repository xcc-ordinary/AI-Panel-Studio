# AI Panel Studio

AI 圆桌讨论演播厅 — 用户发起话题，AI 自动生成主持人与专家阵容，实时辩论、转录、提炼共识与分歧。

## 快速开始

### 环境要求

- Python 3.13+（后端）
- Node.js 20+（前端）
- DeepSeek API Key（或兼容 OpenAI 格式的 LLM）

### 1. 后端

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate  # Windows
# python -m venv .venv && source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env：填入 DEEPSEEK_API_KEY

# 初始化数据库 + 种子数据
python -m scripts.seed

# 启动
python -m uvicorn app.main:app --port 8767 --reload
```

### 2. 前端

```bash
cd frontend
npm install
cp .env.example .env  # VITE_API_BASE=http://localhost:8767
npm run dev            # → http://localhost:5173
```

### 3. 运行测试

```bash
# 后端（42 个测试）
cd backend && APANEL_TEST=true python -m pytest tests/ -v

# 前端 E2E（Playwright）
cd frontend && npx playwright install chromium
npx playwright test                    # 全部 5 个 spec
npx playwright test render-robustness  # 单跑（不调 LLM，快速验证）
```

## 项目结构

```
├── frontend/                     # React 19 + Vite 8 + TypeScript 6 strict
│   ├── src/
│   │   ├── components/
│   │   │   ├── home/             # 首页（DiscussionList/Card, CreateDiscussion, PanelistRoster）
│   │   │   ├── studio/           # 演播厅（StudioView, PanelistGrid, TranscriptPanel, ConsensusPanel）
│   │   │   └── shared/           # 通用（ColorBadge, LoadingSkeleton, EmptyState）
│   │   ├── hooks/                # useSSE, useDiscussion, useConsensus
│   │   ├── services/api.ts       # REST API 客户端
│   │   ├── types/index.ts        # TypeScript 类型定义
│   │   └── utils/colors.ts       # 9 色调色板 + 语义色
│   ├── tests/e2e/                # Playwright E2E（5 个 spec）
│   └── playwright.config.ts
│
├── backend/                      # Python 3.13 + FastAPI + aiosqlite
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/           # discussions, transcript, consensus（REST）
│   │   │   └── sse/              # events.py（SSE 端点）+ manager.py（发布/订阅）
│   │   ├── services/             # DiscussionOrchestrator, SpeechScheduler, ConsensusExtractor, PanelistGenerator
│   │   ├── llm/                  # DeepSeek 客户端 + prompt 模板
│   │   ├── config.py             # 配置（环境变量）
│   │   └── database.py           # aiosqlite WAL + schema 迁移
│   ├── scripts/seed.py           # 6 场预设讨论（含 utterances/consensus/divergence）
│   └── tests/                    # 42 个测试（unit + integration, pytest）
│
├── specs/001-ai-roundtable-discussion/  # SDD 产物（spec/plan/data-model/contracts/tasks）
├── design-system/MASTER.md              # 设计系统规范
└── docs/
    ├── PROMPTS.md                # Prompt 记录（SDD/DDD/TDD/E2E + 排查实录）
    ├── WORKFLOW.md               # 工作流说明（插件分工 + 工程化理解）
    └── dev-log.md                # 开发日志
```

## 架构概览

```
浏览器 (EventSource)
  │  GET /api/discussions/{id}/events
  ▼
FastAPI SSE endpoint ──subscribe()──▶ asyncio.Queue (per-discussion)
                                          │
                                          │ put()
                                          ▼
DiscussionOrchestrator ──publish()──▶ event 表 (seq 日志)
  │
  ├── SpeechScheduler.decide_next_speaker() ──▶ DeepSeek API
  ├── ConsensusExtractor.extract()         ──▶ DeepSeek API (每 3 轮)
  └── _generate_summary()                  ──▶ DeepSeek API (结束时)
```

**核心设计原则：**
- **单进程内存模型**：orchestrator 和 SSE endpoint 共享同一个 `asyncio.Queue` dict，无跨进程通信。uvicorn 不带 `--workers`。
- **Event.seq 为唯一规范源**：所有事件类型共用一条单调递增序列，用于 SSE `id:` 字段 + 重连回放。
- **seq 去重**：前端 `useDiscussion.ts` 维护 `seenSeqsRef<Set<number>>`，按 Event.seq 防止重连/快照导致的重复 append。
- **共识实时提炼**：`ConsensusExtractor` 每 3 轮触发，不等讨论结束。LLM 分析最近 20 轮 transcript，提取新的共识点和分歧阵营。

## 已实现能力

| 能力 | 说明 |
|------|------|
| 🏠 **首页讨论列表** | 展示所有讨论（进行中/已结束），显示 active_count/max_concurrent、嘉宾色点排、状态徽标 |
| 🤖 **AI 嘉宾生成** | 输入话题 + 人数(2-8)，DeepSeek 动态生成主持人 + 专家阵容（姓名/职业/立场/专属颜色） |
| 🎬 **演播厅实时讨论** | 主持人开场/追问/串联/总结；专家自主非轮流发言（反驳/补充/追问），30 轮上限兜底 |
| 📊 **专家状态小窗** | 实时显示 idle/preparing/speaking/silent 四态（不同脉冲动效），公开关注点摘要 |
| 📝 **现场 Transcript** | 发言人姓名 + 职业 Title + 专属色块区分，最新发言入场动画，历史发言不重复动画 |
| 🤝 **实时共识与分歧** | 每 3 轮触发提炼，讨论中途持续更新共识点（绿）与分歧阵营（琥珀），不等结束 |
| 📡 **SSE 实时推送** | Event.seq 单调序列，15s heartbeat，断线重连快照 + Last-Event-ID 增量补发 |
| 🔒 **多讨论严格隔离** | discussion_id 外键 + 应用层 WHERE 过滤 + per-discussion SSE 队列，并行讨论互不串台 |
| 🎨 **设计系统** | 15 色主题色板 + 9 色嘉宾调色板（语义色独占：绿=共识/琥珀=分歧/红=直播）+ 响应式三区布局 |
| 🧪 **TDD 测试** | 42 个后端测试（pytest）+ 5 个 E2E spec（Playwright），核心逻辑严格红绿重构 |

## 主要 API

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/discussions` | 讨论列表（含 active_count / max_concurrent） |
| `POST` | `/api/discussions` | 创建讨论 + 生成嘉宾阵容 |
| `GET` | `/api/discussions/{id}` | 讨论详情（含 panelists） |
| `DELETE` | `/api/discussions/{id}` | 级联删除讨论 |
| `POST` | `/api/discussions/{id}/panelists/regenerate` | 重新生成嘉宾 |
| `PATCH` | `/api/discussions/{id}/panelists/confirm` | 确认阵容 → 启动讨论 |
| `GET` | `/api/discussions/{id}/transcript` | 发言记录（分页） |
| `GET` | `/api/discussions/{id}/consensus/current` | 当前共识与分歧 |
| `GET` | `/api/discussions/{id}/events` | SSE 事件流（6 种事件 + 重连协议） |

## Git Commit 演进

按作业要求的层级演进：`docs/schema → ui-components → tests → feat: logic`

```
chore: init project scaffold
 docs(spec): clarify 5 edge cases
 docs(schema): add data-model, REST/SSE contracts, research & quickstart
 docs(schema): finalize PRD, ER diagram, API doc & task breakdown
 docs(schema): add seed-data task
 fix(schema): add database layer, divergence_point schema
 test(api): add discussion CRUD integration tests (list/detail/delete)
 feat(api): implement discussion list/detail/delete with isolation & N+1 fix
 test(sse): add SSE stream & reconnection integration tests (live_server)
 feat(sse): minimal SSE channel with seq-based reconnection (fake source, TODO Phase4)
 fix(sse): drop id field on heartbeat/snapshot to preserve Last-Event-ID
 docs(design): finalize design system; separate identity/semantic colors
 ui-components: home & create-discussion pages aligned to design system
 ui-components: studio three-pane layout + realtime components
 fix(ui): replace fetchedRef with cancelled flag to fix Strict Mode loading deadlock
 test: panelist generator unit tests (mock LLM, malformed-json retry, diversity)
 feat: panelist generation via DeepSeek with JSON parsing & color assignment
 test: speech scheduler & SSE manager unit tests (non-round-robin, silent detection, fan-out)
 feat: discussion orchestrator with speech scheduling + consensus extraction + summary
 docs: rewrite prompt log, workflow doc, README with real dev process & tabbit principles
 test(e2e): add Playwright E2E specs (full-cycle, delivery, robustness, isolation, reconnect)
 feat: studio real-time SSE integration, seq dedup, E2E verification & API docs update
 feat: anti-hallucination guardrails, robust JSON parsing, bulletproof discussion_end
 feat: opening-statement phase, fallback diversity, JSON mode lockdown, same-speaker prevention
 feat: Apple Studio redesign (glass-nav, marquee glow), consensus dedup, summary bulletproof
```

## 后续改进方向

### 多 Worker 场景 → Redis Pub/Sub

当前单进程 `asyncio.Queue` 在 `--workers > 1` 时失效——每个 worker 进程有独立的内存空间，orchestrator 推送到 Worker A 的 queue，但 SSE 连接可能在 Worker B。`print(id(_registry), pid)` 已验证当前单进程下 `_subscribers` 共享正常，但多 worker 扩展必须换跨进程方案。

**方案**：将 `manager.py` 的 `_registry[discussion_id] = asyncio.Queue()` 替换为 Redis Pub/Sub channel。`publish()` → `REDIS PUBLISH discussion:{id}`，`subscribe()` → `REDIS SUBSCRIBE discussion:{id}`。每个 worker 进程内的 SSE 连接各自 subscribe 同一个 Redis channel。

### SSE publish 加 per-discussion asyncio.Lock（防 seq 竞态）

当前 `publish()` 用 `SELECT COALESCE(MAX(seq), 0) + 1` 计算下一个 seq，在高并发下存在竞态窗口——两个并发的 publish 可能读到相同的 MAX 值，导致 seq 重复或 UNIQUE 约束冲突。

**方案**：在 `manager.py` 中维护 `_locks: dict[str, asyncio.Lock]`，每个 `publish()` 调用包裹在 `async with _locks[discussion_id]:` 中。或者改用 `INSERT INTO event ... RETURNING seq`（SQLite 3.35+ 支持 `RETURNING` 子句，将"计算 seq + INSERT"原子化为一步）。

### Orchestrator 恢复（Server Restart）

当前 orchestrator 是内存 asyncio Task，服务器重启后丢失。`_ensure_orchestrator()` 在 SSE 连接时检测 `discussion.status == 'in_progress'` 但 `_orchestrators` 中没有对应条目时重新 spawn——已部分覆盖重启场景。但存在盲区：**如果所有 SSE 连接断开（没有客户端触发 `_ensure_orchestrator`），讨论会永久停在 `in_progress`。**

**方案**：在 FastAPI `lifespan` 事件中扫描所有 `status='in_progress'` 的讨论并重新 spawn orchestrator。需配合 `round_no` 从 `SELECT MAX(round_no)+1 FROM utterance` 推导（已实现），确保恢复后从断点继续而非从 0 开始。

### Orchestrator 用独立 DB 连接

当前 orchestrator、SSE endpoint、REST 路由共享同一个 `aiosqlite.Connection`。虽然 asyncio 的协作式调度避免了真正的并发写入冲突，但 `publish()` 的 `SELECT MAX → INSERT` 跨多个 `await` 不是原子的，且共享连接的写锁可能阻塞 web 请求的读操作。

**方案**：给 orchestrator 分配独立的 aiosqlite 连接。读操作（REST 路由的 GET 请求）从共享连接走，写操作（utterance/consensus/divergence INSERT + event INSERT）在独立连接上以 WAL 模式并发执行。SQLite WAL 模式天然支持一个 writer + 多个 readers。

### 前端 → react-router

当前使用 `useState` 状态路由（`App.tsx` 的 `Page` 联合类型）。对于当前 4 个页面规模够用，但更深层级的导航（如从演播厅直接跳转到另一场讨论、浏览器刷新保持当前页面）需要 URL 驱动的路由。

**方案**：引入 `react-router` v7，将 `Page` 状态映射为 URL 路径（`/`→首页、`/create`→创建、`/roster/:id`→阵容、`/studio/:id`→演播厅）。保留 `data-testid` 属性确保 E2E 测试不因路由实现变更而失效。

### ConsensusExtractor 状态感知

当前每 3 轮触发一次提炼，每次独立分析最近 20 轮 transcript。虽已向 prompt 注入已有共识/分歧的 ID 和摘要，但 LLM 仍可能将同一观点的细微变体识别为"新共识/分歧"，导致内容相似的条目重复入库。

**方案**：在 prompt 中增加"去重判定"指令——要求 LLM 对每个新提取的观点，先判断"这是新观点还是已存在观点的强化/重述"。如为强化，输出 `update_existing: true` + 被强化的已有条目 ID，而非 `new_consensus`。

### 内容审核 → 第三方服务

当前 `LocalContentModerator` 用关键词 blocklist + 长度校验（1-200 字符）。已设计为可插拔接口（`ContentModerator` 抽象基类 → `ModerationResult`），但未接入真实语义审核服务。

**方案**：实现 `OpenAIModerator` 或 `AzureContentSafetyModerator` 适配器，调用外部 API 进行语义级别的安全审核。`check_topic()` 接口不变（返回 `ModerationResult`），只需在 `config.py` 中增加 `moderator_type` 配置项并工厂化实例化。
