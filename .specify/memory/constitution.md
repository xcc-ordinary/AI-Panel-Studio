<!--
Sync Impact Report
==================
Version Change: N/A (initial) → 1.0.0
Ratification: 2026-06-26 (initial adoption)

Principles Defined (6 new):
  I.   前后端分离架构 — Frontend-Backend Separation Architecture
  II.  代码质量标准 — TypeScript Strict + Single Module Responsibility
  III. 测试驱动开发 (NON-NEGOTIABLE) — TDD Red-Green-Refactor for core logic + E2E
  IV.  安全第一 — LLM API Key isolation, backend env vars only
  V.   数据隔离 — Strict discussion_id scoping for all discussion data
  VI.  实时共识与分歧 — Real-time consensus/divergence updates during discussion

Sections:
  - Additional Constraints: UI & User Experience Standards
  - Development Workflow: Branching, Code Review, Quality Gates

Templates Checked:
  ✅ plan-template.md — "Constitution Check" gate section remains generic; populated at plan-time
  ✅ spec-template.md — User stories, requirements, success criteria aligned with principles
  ✅ tasks-template.md — Test-optional text preserved; TDD mandated by constitution for core logic
  ✅ checklist-template.md — Generic; no changes needed
  ⚠ tasks-template.md — Note: template defaults tests to OPTIONAL; constitution mandates TDD for
    core logic (guest generation, speech scheduling, consensus extraction). The /speckit-tasks
    command MUST override the "optional" default when tasks touch core logic modules.

Follow-up TODOs: None
-->

# AI Panel Studio Constitution

## Core Principles

### I. 前后端分离架构

前端与后端 MUST 作为独立项目进行开发、构建与部署。

- **前端**: `frontend/` 目录，React 19 + TypeScript + Vite 8，仅负责 UI 渲染与用户交互。
- **后端**: `backend/` 目录，Python FastAPI，仅负责业务逻辑、LLM 调用、数据持久化。
- 前后端通过 REST API 或 WebSocket 进行通信，接口契约 MUST 在 `contracts/` 中明确定义。
- 前端 MUST NOT 直接访问数据库、文件存储或任何后端专属资源。
- 后端 MUST NOT 包含 UI 渲染逻辑（模板渲染除外，如必要）。

**Rationale**: 物理隔离确保安全边界清晰、团队可并行开发、部署可独立伸缩。

### II. 代码质量标准

所有代码 MUST 遵循以下强制性质量要求：

- **TypeScript Strict**: 前端 `tsconfig.json` MUST 启用 `"strict": true`。禁止使用 `any` 类型（除非有明确的 `// eslint-disable-next-line` 注释说明原因并经 review 确认）。
- **模块职责单一**: 每个模块/文件 MUST 仅承担一个明确职责。组件、服务、工具函数 MUST 可独立理解和测试。
- **Lint 门禁**: Oxlint（前端）MUST 在 `tsc -b` 之前零错误通过。后端 MUST 配置 ruff 或 pylint 并纳入 CI。
- **命名规范**: 文件命名 MUST 使用 kebab-case（前端组件文件可用 PascalCase）；变量/函数 MUST 使用 camelCase；类型/接口 MUST 使用 PascalCase。
- **依赖方向**: 模块间依赖 MUST 遵循单向依赖原则——服务层 → 数据层，组件层 → hooks → 服务层。禁止循环依赖。

**Rationale**: TypeScript strict 在编译阶段拦截类型错误；单一职责降低变更风险、提升可测试性。

### III. 测试驱动开发 (NON-NEGOTIABLE)

核心业务逻辑 MUST 严格遵循 TDD 红-绿-重构循环。

- **强制 TDD 范围**: 以下模块 MUST 先写测试、确认测试 FAIL、再编写实现代码：
  - 嘉宾生成逻辑（AI Panelist Generation）
  - 发言调度逻辑（Speech Scheduling / Turn Management）
  - 共识提炼逻辑（Consensus Extraction）
- **测试分层**:
  - **单元测试**: 覆盖所有核心服务函数，mock 外部依赖。
  - **集成测试**: 覆盖 API 端点与数据库交互。
  - **E2E 测试**: 覆盖关键用户旅程——创建讨论 → 嘉宾发言 → 共识生成。MUST 使用 Playwright 或等效框架。
- **覆盖率要求**: 核心逻辑（上述三类）的分支覆盖率 MUST ≥ 80%。
- **非核心代码**: 鼓励但不强制 TDD；至少 MUST 具备集成测试覆盖关键路径。

**Rationale**: 嘉宾生成、发言调度、共识提炼是产品核心价值所在——任何回归都直接影响用户体验和讨论质量。TDD 确保行为正确且可回归。

### IV. 安全第一

LLM API 密钥及相关凭证 MUST 仅存在于后端环境变量中。

- **API Key 隔离**: `OPENAI_API_KEY`、`ANTHROPIC_API_KEY` 或任何大模型 API 密钥 MUST 仅配置于 `backend/.env`，该文件 MUST 被 `.gitignore` 排除。
- **前端零暴露**: 前端代码、构建产物、环境变量（`VITE_*`）中 MUST NOT 出现任何 API Key、Secret 或 Token。
- **后端代理**: 所有 LLM 调用 MUST 经过后端 API 代理。前端通过后端端点发起讨论，后端负责组装 prompt 并调用大模型。
- **传输安全**: 生产环境中 API 通信 MUST 使用 HTTPS；WebSocket 连接 MUST 使用 WSS。
- **输入校验**: 所有用户输入（讨论主题、嘉宾配置等）MUST 在后端进行服务端校验，不可仅依赖前端校验。

**Rationale**: API Key 泄露是最常见且后果最严重的安全事故之一。前端代码对用户完全可见，任何放置于前端的密钥等价于公开。

### V. 数据隔离

多讨论场景下的所有数据 MUST 以 `discussion_id` 进行严格隔离。

- **隔离范围**: 讨论状态、事件流、transcript（发言记录）、共识结果、分歧记录 MUST 全部按 `discussion_id` 分区。
- **查询强制**: 所有数据库查询、缓存读取、日志检索 MUST 携带 `discussion_id` 过滤条件。禁止跨讨论扫描或聚合，除非属于管理审计功能（需显式授权）。
- **API 设计**: 讨论相关 API 路径 MUST 包含 `discussion_id`（如 `/api/discussions/{discussion_id}/messages`），确保路由层级即隔离边界。
- **WebSocket 隔离**: 每个讨论 MUST 使用独立的 WebSocket channel/room，客户端只能订阅其所参与的讨论。
- **数据清理**: 讨论删除时，其关联的所有数据（状态、事件、transcript、共识）MUST 级联删除，不留孤儿数据。

**Rationale**: 数据隔离不仅是安全需求，更是正确性保障——讨论 A 的发言不应污染讨论 B 的共识提炼。

### VI. 实时共识与分歧

共识（Consensus）与分歧（Divergence）MUST 在讨论进行过程中实时更新，而非等待讨论结束后一次性生成。

- **增量更新**: 每轮发言结束后，后端 MUST 增量更新当前共识快照与分歧记录。前端通过 WebSocket 接收增量更新并渲染。
- **不阻断讨论流**: 共识/分歧计算 MUST 异步执行，不阻塞嘉宾发言调度主循环。
- **可视化展示**: 前端 MUST 在讨论面板中实时展示共识演变（如共识热力图、分歧标注）。讨论结束后的最终共识报告仅为快照归档，不是首次展示。
- **中间状态可查询**: API MUST 提供获取讨论当前中间共识状态的端点（`GET /api/discussions/{discussion_id}/consensus/current`）。

**Rationale**: 实时共识是 AI 圆桌讨论的核心交互体验——用户应该看到观点如何逐步靠拢或分化，而非面对一个黑盒结果。

## Additional Constraints: UI & User Experience

以下约束适用于前端 UI 实现：

- **中文界面**: 所有 UI 文案、提示、错误消息、按钮标签 MUST 为简体中文。代码注释和文档可使用中文或英文，但对外展示文本 MUST 为中文。
- **响应式设计**: 前端 MUST 适配桌面端（≥1024px）、平板端（768px–1023px）、移动端（<768px）三种断点。核心功能在移动端 MUST 可用但允许降级布局。
- **独立滚动区域**: 讨论面板中的各个逻辑区域（嘉宾列表、发言区、共识面板、transcript 区）MUST 各自独立滚动（`overflow-y: auto`），不得依靠整页滚动。
- **可访问性**: 颜色对比度 MUST 满足 WCAG AA 标准；关键交互 MUST 支持键盘操作。
- **加载与空状态**: 每个异步数据区域 MUST 实现 loading 骨架屏和 empty state 提示。

## Development Workflow

### 分支策略

- `main` 分支 MUST 始终保持可部署状态。
- 功能开发 MUST 在 `feature/<描述>` 分支上进行，通过 PR 合并回 `main`。
- PR MUST 在合并前通过 CI 检查：lint → typecheck → unit tests → integration tests。

### 代码审查

- 所有 PR MUST 至少经过一人 Review 并批准后方可合并。
- Review 检查项 MUST 包含：TypeScript strict 合规、TDD 流程证据（测试先行提交）、API Key 无泄露、数据隔离正确性。
- 发现原则违规的 PR MUST 被拒绝，修复后方可重新提交。

### 质量门禁

| 门禁 | 触发时机 | 要求 |
|------|---------|------|
| Lint | pre-commit / CI | 零错误 |
| TypeCheck | CI | `tsc -b` 零错误 |
| Unit Tests | CI | 核心模块覆盖率 ≥ 80% |
| E2E Tests | CI / pre-merge | 关键旅程全通过 |
| Security Scan | CI | 无 API Key 泄露检测 |

## Governance

本 Constitution 是 AI Panel Studio 项目的最高开发准则，所有开发实践、代码审查、架构决策 MUST 以此为准。

- **修订流程**: 修改 Constitution 需通过 PR 提议，说明修订理由、影响范围与迁移计划。至少一位项目维护者批准后方可合并。
- **版本策略**: 遵循语义化版本 `MAJOR.MINOR.PATCH`：
  - MAJOR: 原则删除或不兼容重定义。
  - MINOR: 新增原则或实质性扩展。
  - PATCH: 措辞澄清、错字修正、非语义调整。
- **合规审查**: 每个功能分支的 PR 描述中 SHOULD 包含 Constitution 合规自查清单。架构评审时 MUST 逐条对照 Constitution 原则。
- **运行时指导**: 日常开发细节（shell 命令、环境配置、调试方法）参见 `CLAUDE.md` 及各功能 `plan.md`。

**Version**: 1.0.0 | **Ratified**: 2026-06-26 | **Last Amended**: 2026-06-26
