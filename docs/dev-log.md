# AI Panel Studio — 开发日志

**最后更新**: 2026-06-27 (§6 指导原则补录) | **分支**: `001-ai-roundtable-discussion`

---

## 1. 已完成

### Phase 0 — 项目骨架

- [x] `frontend/` + `backend/` 目录分离
- [x] 前端 React 19 + Vite 8 + TypeScript 6 strict
- [x] 后端 Python 3.13 + FastAPI + uvicorn + aiosqlite + httpx
- [x] `backend/.env.example` 含完整环境变量清单
- [x] 前后端各自 `npm run dev` / `uvicorn` 可独立启动

### Phase 1 — SDD 全产物（Spec-Driven Development）

- [x] **Constitution** (v1.0.0): 6 原则——前后端分离 / TS strict / TDD 核心逻辑 / API Key 隔离 / discussion_id 数据隔离 / 实时共识
- [x] **Spec**: `specs/001-ai-roundtable-discussion/spec.md` — 4 用户故事 + 13 FR + 7 SC + 5 条 clarify 结论
- [x] **Plan**: 技术栈、项目结构、Constitution Check 通过
- [x] **Research**: DeepSeek API / FastAPI SSE / aiosqlite WAL / content moderation 可插拔 / 9 色嘉宾调色板 / speech scheduling 策略
- [x] **Data Model**: 6 实体 — discussion, panelist, utterance, consensus_point, divergence_point, event（全部 discussion_id 隔离 + FK ON DELETE CASCADE）
- [x] **Contracts**: `api-rest.md` (7 端点) + `api-sse.md` (6 事件类型 + Last-Event-ID 重连协议)
- [x] **Tasks**: `tasks.md` — 84 任务，按用户故事组织，标注 TDD 强制范围与并行机会
- [x] **Data model fix**: `Utterance.seq` → `round_no`，`Event.seq` 为 SSE id 唯一规范源
- [x] **SSE contract fix**: heartbeat + snapshot 去掉 `id:` 字段（防止污染浏览器 Last-Event-ID）

### Phase 2 — 后端基础设施 + 讨论 CRUD + SSE 最小通道

- [x] **T005**: `backend/app/config.py` — pydantic-settings，含 `DATABASE_PATH` / `MAX_CONCURRENT_DISCUSSIONS` / `DEFAULT_MAX_ROUNDS`
- [x] **T006**: `backend/app/database.py` — aiosqlite + WAL + `get_db()` / `close_db()`
- [x] **T012**: `init_db()` — 6 表建表 + 索引 + FK ON DELETE CASCADE
- [x] **T012b**: `backend/scripts/seed.py` — 6 条预设讨论，26 嘉宾，24 发言，6 共识+6 分歧。幂等，`python -m scripts.seed`
- [x] **T029–T033**: 讨论 CRUD — `GET /api/discussions` (列表+active_count+max_concurrent) / `GET /api/discussions/{id}` (含 panelists) / `DELETE /api/discussions/{id}` (级联删除)。全查询带 discussion_id 隔离。**严格 TDD：8 测试先红后绿**
- [x] **T040–T053**: SSE 最小通道 — `manager.py` (per-discussion asyncio.Queue + publish/subscribe + 15s heartbeat) / `events.py` (StreamingResponse + Last-Event-ID 重连 snapshot 增量补发)。假事件源每秒一条 utterance（标注 TODO Phase 4）。**严格 TDD：4 测试先红后绿 + 3 回归测试**
- [x] **SSE id:0 bug fix**: heartbeat 和 snapshot 移除 `id:` 行——SSE 规范要求 `id` 字段会改写浏览器 `lastEventId`。补测 `tests/unit/test_sse_heartbeat_format.py` + `test_snapshot_has_no_id_field_does_not_pollute_last_event_id`

### Phase 3 — 设计系统 + 前端组件 + 演播厅

- [x] **Phase 3.1 设计系统定稿**: `design-system/MASTER.md` — 15 色主题色板 + 9 色嘉宾调色板（靛蓝 #818CF8 替换翡翠绿，绿被共识独占）/ Poppins → Noto Sans SC 字体栈 / 三区布局 + 4 断点 / 150-300ms 动效 + prefers-reduced-motion
- [x] **Phase 3.2 首页 + 嘉宾确认页**: DiscussionCard / DiscussionList / CreateDiscussion / PanelistRoster + 共享组件（ColorBadge/LoadingSkeleton/EmptyState）+ API 客户端 + TypeScript 类型
- [x] **Phase 3.4 演播厅三大区**: StudioView 三区布局 + PanelistGrid/PanelistWindow/TranscriptPanel/ConsensusPanel/StatusIndicator + SSE 实时驱动（useSSE/useDiscussion/useConsensus）

### Phase 4 — 真实讨论编排 + 共识提炼 + E2E

- [x] **Phase 4.1 PanelistGenerator TDD**: 7 tests — 解析/重试/多样性检查，Jaccard 相似度阈值 0.6
- [x] **Phase 4.2 SpeechScheduler TDD**: 8 tests — host opening / rebuttal / non-round-robin / silent detection / max_rounds / no-volunteer fallback
- [x] **manager.py 进程身份验证**: 模块 import 时 `print(id(_registry), pid)`，确认单进程单实例
- [x] **DiscussionOrchestrator**: `backend/app/services/discussion_orchestrator.py`
  - `run()`: 加载 panelists → loop{ load transcript → SpeechScheduler → persist utterance → publish SSE → extract consensus } → discussion_end
  - round_no 从 `SELECT MAX(round_no)+1 FROM utterance` 推导（以 utterance 表为唯一真相源，避免 discussion.current_round 不同步导致 UNIQUE 冲突）
  - `spawn_discussion()` / `cancel_discussion()` — 模块级 registry
  - 错误处理: 异常路径用固定中文总结，不泄漏 `{exc}` 原文
- [x] **events.py 去假源**: 移除全部 `_fake_*` 代码，`_ensure_orchestrator()` 改为 spawn 真 orchestrator
  - 测试模式: `APANEL_TEST=true` env var → skip orchestrator spawn
- [x] **confirm 时 spawn**: `PATCH /api/discussions/{id}/panelists/confirm` → `spawn_discussion()`
- [x] **delete 时 cancel**: `DELETE /api/discussions/{id}` → `cancel_discussion()`
- [x] **端到端验证**: `utterance.id` = 真实 UUID（非 `fake-u-*`），`round_no` 严格递增

### Phase 4.3 — 共识提炼 + LLM 总结 + 非轮流强化

- [x] **ConsensusExtractor**: `backend/app/services/consensus_extractor.py`
  - 从最近 20 轮 transcript 中提炼共识/分歧点
  - 每次产生新 UUID 避免 `consensus_point.id` PRIMARY KEY 冲突（LLM 可能返回重复 ID）
  - `_call_llm` 可被 AsyncMock 替换（测试模式同 SpeechScheduler）
- [x] **共识提炼接入 orchestrator 主循环**: `CONSENSUS_INTERVAL=3`，每 3 轮触发 `_extract_and_publish()`
  - 共识/分歧点持久化到 consensus_point/divergence_point 表
  - SSE 推送 `consensus_update` / `divergence_update` 事件
  - 前端 ConsensusPanel 实时渲染
- [x] **LLM 生成自然语言总结**: `_generate_summary()` — 调 LLM 用 SUMMARY_SYSTEM/USER prompt，输出纯中文段落
  - 异常路径用固定中文："讨论因技术原因提前结束，感谢各位专家的参与。"
  - prompt 明确"不要列出 JSON 或结构化数据"、"直接输出纯文本段落"
- [x] **调度 prompt 强化非轮流**: "禁止机械轮流——绝不按固定顺序 1→2→3→4→1→2 轮换" + "同一嘉宾可以连续发言两轮，这比硬换人更自然" + "反驳、补充、追问优先"
- [x] **共识 ID 修复**: `consensus_extractor.py` 始终用 `uuid.uuid4()` 而非 LLM 返回的 id，避免 PRIMARY KEY 全局唯一约束冲突
- [x] **4 点需求验证**: 共识中途出现 ✅ / 总结纯自然语言 ✅ / 非机械轮流 ✅ / 多讨论隔离 ✅

### Phase 5 — E2E Playwright 测试

- [x] **Playwright 安装 + 配置**: `@playwright/test` + `playwright.config.ts`（`webServer` 自动启动前后端，`DEFAULT_MAX_ROUNDS=6`）
- [x] **13 个 data-testid 属性**: discussion-card / topic-input / confirm-roster-btn / utterance-entry / consensus-card / divergence-card / host-section / experts-section / status-* / connection-status / discussion-end-banner 等
- [x] **5 个 E2E spec**:
  - `full-live-cycle.spec.ts` — 创建→阵容→确认→演播厅→transcript 增长→discussion_end 无 JSON
  - `delivery-liveness.spec.ts` — 进入 in_progress → N 秒内 utterance 数 > 初始 snapshot
  - `render-robustness.spec.ts` — 加载含 camps 的分歧讨论 → 不白屏 camps 正常渲染
  - `multi-discussion-isolation.spec.ts` — 两场讨论零串台
  - `sse-reconnection.spec.ts` — 断开重连 → snapshot+增量完整记录无重复
- [x] **E2E helpers**: `tests/e2e/helpers.ts` — goHome / clickCreateDiscussion / fillAndGenerate / confirmRoster / waitForUtterances / joinDiscussion / assertLiveStatus / waitForDiscussionEnd
- [x] **E2E global setup**: 幂等 seed 脚本
- [x] **render-robustness + multi-discussion-isolation 已验证通过**

### SSE 合约遵从 + 前端去重

- [x] **SSE 合约遵从测试** (+6 tests): `test_sse_manager.py`
  - `get_events_after_seq` 只返回 `seq > after_seq`（严格大于边界）
  - 回放按 seq ASC 排序
  - `_get_db_snapshot` 含真实数据（非空数组），同 id 去重保留最新
- [x] **SSE seq 去重 + 幂等合并** (frontend):
  - `useDiscussion.ts`: `seenSeqsRef<Set<number>>` 按 Event.seq 去重 utterance
  - snapshot handler 从替换改为合并（upsert by id）
  - panelist_status / consensus / divergence 幂等合并

### 文档

- [x] `docs/PROMPTS.md` — Prompt 记录（SDD/DDD/TDD/E2E 四阶段 + 六轮排查实录）
- [x] `docs/WORKFLOW.md` — 工作流说明（三插件分工 + 3 个典型问题 + 三层工程化理解）
- [x] `README.md` — 项目首页（快速开始 + 架构图 + 6 个后续改进方向含方案）

---

## 2. 测试覆盖

```
backend/tests/
├── unit/
│   ├── test_sse_heartbeat_format.py    # 3 tests — heartbeat 不含 id:
│   ├── test_sse_manager.py             # 6 tests — replay边界/快照内容/去重
│   ├── test_content_moderator.py       # 6 tests
│   ├── test_panelist_generator.py      # 7 tests
│   └── test_speech_scheduler.py        # 8 tests
├── integration/
│   ├── test_list_discussions.py        # 4 tests
│   ├── test_get_discussion.py          # 4 tests
│   └── test_sse_events.py             # 4 tests — SSE 流 + 重连 + snapshot id 回归
├── conftest.py                         # db fixture + client (ASGI) + live_server (uvicorn)

42 tests — 0 failures
```

```
frontend/tests/e2e/
├── full-live-cycle.spec.ts             # 完整直播链路
├── delivery-liveness.spec.ts           # 投递活性
├── render-robustness.spec.ts           # 渲染健壮性 ✅ 已验证
├── multi-discussion-isolation.spec.ts  # 多讨论隔离 ✅ 已验证
├── sse-reconnection.spec.ts            # 重连恢复
├── helpers.ts                          # 共享工具
└── fixtures/global-setup.ts            # 种子数据
```

---

## 3. 关键约定（实施时必须遵守）

| 约定 | 说明 |
|------|------|
| `backend/app/` 非 `backend/src/` | 现有代码落地在 `app/` 包，Phase 1 的 plan 模板写 `src/` 仅作参考 |
| 限流计数 | 并发上限判断 = `in_progress` + `pending_panelists` |
| `active_count` 仅计 `in_progress` | 首页展示用——区别于限流计数 |
| SSE `Event.seq` 是唯一规范 id 源 | `Utterance.round_no` 仅用于排序/分页 |
| heartbeat / snapshot 不带 `id:` 字段 | SSE 规范：不带 `id` 的事件不改变浏览器 `lastEventId`（6 个回归测试锁定） |
| panelist-2 = `#818CF8` 靛蓝 | 不是翡翠绿——绿被共识独占（MASTER.md §1.2 + colors.ts 对齐） |
| 后端端口 8767 / 前端 `VITE_API_BASE` 配置化 | 8000/8010 被 Windows 系统保留（WinError 10013），8765 有僵尸进程暂时用 8767 |
| orchestrator + SSE 同进程 | uvicorn 不带 `--workers`，`_registry` 单实例，print id+pid 验证 |
| `round_no` 从 utterance 表推导 | `SELECT MAX(round_no)+1 FROM utterance`——不以 discussion.current_round 为准 |
| 共识提炼每 3 轮触发 | `CONSENSUS_INTERVAL=3`，`_extract_and_publish()` 在主循环中 |
| consensus/divergence ID 用 UUID | LLM 可能返回重复 ID，始终以 `uuid.uuid4()` 覆盖，避免 PRIMARY KEY 冲突 |

---

## 4. 待办

| # | 待办 | 原因 |
|---|------|------|
| ① | 一讨论一 queue → 多订阅者各自 queue + fan-out | 当前一个 queue 被多个 SSE 连接共享，慢客户端阻塞其他 |
| ② | `subscribe` 加 `finally` 清理 | 客户端断开时需注销其 queue，否则内存泄漏 |
| ③ | `publish` 加 per-discussion `asyncio.Lock` | `Event.seq` 取自 `MAX(seq)+1`，并发 publish 会竞态 |
| ④ | orchestrator 恢复（server restart） | orchestrator 是内存 task，重启后丢失 |
| ⑤ | 前端 → react-router | 状态路由够用但无 URL 驱动导航 |
| ⑥ | ConsensusExtractor 状态感知 | 当前不追踪"分歧是否已提过"，可能重复入 |
| ⑦ | 内容审核 → 第三方服务 | 当前 `LocalContentModerator` 仅关键词 + 长度 |
| ⑧ | multi-worker → Redis Pub/Sub | 当前单进程内存 queue 在 `--workers > 1` 时失效 |
| ⑨ | orchestrator 用独立 DB 连接 | 当前共享 aiosqlite 连接存在竞态窗口 |

---

## 5. 临时脚手架清理

| 文件 | 状态 |
|------|------|
| `backend/app/api/sse/events.py` ~~假事件源~~ | ✅ 已替换为真实 orchestrator |
| `frontend/src/App.tsx` 状态路由 | Phase 5 换 react-router（待办 ⑤） |
| `frontend/src/components/debug/SseDebug.tsx` | Phase 5 移除 |
| `backend/app/services/discussion_orchestrator.py` | 🆕 真实编排器（SpeechScheduler + ConsensusExtractor 驱动） |
| `backend/app/services/consensus_extractor.py` | 🆕 共识提炼服务（每 3 轮触发） |
| `frontend/tests/e2e/` | 🆕 Playwright E2E（5 specs） |

---

## 6. 指导原则（源自 tabbit 系统化学习AI开发方法论）

> 完整记录见 `docs/tabbit_系统化学习AI开发的逐步指导原则.md`（7634 行对话实录），核心原则已存入 memory。

### 6.1 四范式工程拆解（SDD→DDD→TDD→E2E）

| 范式 | 主导插件 | 核心产出 | 关键纪律 |
|------|----------|----------|----------|
| **SDD** | spec-kit | constitution / spec / plan / data-model / contracts / tasks | 只说 What & Why，到 plan 才引入 How；实现以 Superpowers TDD 为准，不敲 `/speckit-implement` |
| **DDD** | ui-ux-pro-max | MASTER.md 设计系统（配色/字体/布局/动效/可访问性） | 先定死设计语言再让组件服从；设计系统存在 ≠ 设计系统被执行，需一轮"还原度对齐" |
| **TDD** | Superpowers | mock 单元测试 + 红绿重构 | 真红(逻辑未实现失败) ≠ 假红(import/async配置缺失)；mock 测逻辑不测大模型 |
| **E2E** | Superpowers/Playwright | 端到端自动化测试 | E2E 测管道通畅不测水质（mock LLM 确定性模式）；覆盖单元测试结构性无法覆盖的真实链路 |

### 6.2 三插件分工

```
Superpowers（主干，全程 95%）── TDD 循环 / 写代码 / 修 bug / code-review
    ├── spec-kit（SDD 阶段主角）── 结构化产出规格、数据模型、契约、任务清单
    └── ui-ux-pro-max（DDD 阶段主角）── 设计系统生成与持久化
```

**核心取舍**：spec-kit 用到 `/speckit-tasks` 为止，实现环节以 Superpowers TDD 为准——守住"过程可溯 > 一键完成"的评分导向。

### 6.3 核心工程原则

**① "先铺水管，再通水源"**
把大模型（不确定因素）和基础设施（确定因素）隔离。Phase 2 SSE 假数据通道 → Phase 3 假数据 UI → Phase 4 接真 LLM。出问题时能立刻判断是水管漏还是水源有问题。

**② "单一真理来源" (Single Source of Truth)**
所有关键决策锁进文件：数据模型→`data-model.md`、设计系统→`MASTER.md`、进度→`dev-log.md`、上下文锚点→`CLAUDE.md`。已定稿的设计不反复交给 AI 凭记忆重生成。

**③ "契约约束 AI" (Contract-Driven Anti-Hallucination)**
先把数据长什么样、接口怎么调用用文档钉死，再让 AI 照着契约实现。当实现与契约不一致时，默认改实现去对齐契约。

**④ "单测全绿 ≠ 真能用"**
mock 测试结构性无法覆盖：浏览器订阅者生命周期、真实 LLM JSON 格式噪声、异步 task GC 回收、asyncio Queue 时序竞态。E2E + 真实环境联调是最终真相源。

**⑤ "证据驱动排查" (Evidence-Driven Debugging)**
异步卡死类 bug 不靠读代码猜 → breadcrumb `print(flush=True)` 埋点定位最后一口气 → `id()` + `pid()` 验证内存共享 → 回退对照实验分离变量。**"环境×代码"的耦合 bug 只有真实运行环境能暴露。**

**⑥ "上下文锚点" (Context Restore Anchor)**
`dev-log.md` 是上下文清理后的秒级恢复锚点——必须包含：已完成产物、关键约定、跨阶段待办、临时脚手架清单。清了能秒恢复才有底气清。

### 6.4 SSE 投递断链排查实录（6 轮证据驱动排查）

这是整个项目最有教学价值的排查案例，印证了"AI 输出掌控力"的核心考点：

| 轮次 | 假设 | 证据 | 结论 |
|------|------|------|------|
| 1 | LLM 调用 hang | timeout 加后仍卡 → 排除 LLM | 卡点不在 LLM |
| 2 | publish 队列写满阻塞 | breadcrumb trace 全部 E:publish后 正常 → 排除 | 后端生产健康 |
| 3 | 前端渲染崩 | Console 干净无报错 → 排除 | 问题在投递 |
| 4 | 队列错位 (fan-out 缺失) | 心跳通·业务断 → 锁定投递链 | publish 与 subscribe 队列不是同一个 |
| 5 | 多 worker 进程隔离 | `id(_subscribers)` + `pid` 验证 → 单进程排除 | 模块双实例嫌疑 |
| 6 | 回退对照实验 | 假源版全收到 / 真源版只有心跳 | **真 orchestrator import 的 manager 与 SSE endpoint 不是同一模块实例** |

**根因**：`publish` 与 `subscribe` 操作了不同的 `_subscribers` 字典（模块被双路径 import 生成两份实例）。
**修复**：统一 import 路径 + 单进程启动 + fan-out + 假源退休。
**教训**：36 个 mock 单测一个都没覆盖"浏览器订阅者连接/断开/重连"的真实生命周期——这类只能靠 E2E 兜。

### 6.5 工程化 AI 开发的三层理解

1. **AI 是代码生成器**：高速产出 80% 样板代码，20% 胶水代码需人设计接口边界
2. **AI 是需求翻译器**：翻译质量取决于人的审查——panelist-2 颜色冲突是人发现的，不是 AI
3. **AI 不是调试器**："环境×代码"耦合 bug 只有真实运行环境能暴露

**工程师价值从"写代码"转向三个新能力**：
- **设计契约** — 清晰接口边界（`_call_llm` mock 点、`publish()` 唯一入口、`data-testid` E2E 锚点）
- **验证真相** — 用 TDD 红绿循环、端到端 HTTP 直连、`print(id(_registry), pid)` 独立验证 AI 输出
- **掌控边界** — 知道什么让 AI 做（样板/模板/测试用例生成），什么必须人做（时序协议设计、并发安全分析、终极 bug 排查）
