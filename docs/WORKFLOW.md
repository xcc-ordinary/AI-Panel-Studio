# 工作流说明 — AI Panel Studio

## SDD→DDD→TDD→E2E 范式切换逻辑

本项目严格按照作业要求的四范式推进，每个范式有明确的主导插件、核心目标和验收标准：

```
SDD（Spec-Driven）
  │  主导：spec-kit
  │  目标：在零代码状态下，把模糊的产品想法逼成精确的数据模型和 API 契约
  │  产出：constitution / spec / plan / data-model / contracts / tasks（84 任务）
  │  关键纪律：只说 What & Why，到 plan 才引入 How；到 tasks 为止，不敲 /speckit-implement
  │
  ▼
DDD（Design-Driven）
  │  主导：ui-ux-pro-max
  │  目标：先定死设计语言（配色/字体/布局/动效），再让组件服从它
  │  产出：design-system/MASTER.md（15 色主题色板 + 9 色嘉宾调色板 + 三区布局 + 可访问性规范）
  │  关键纪律：两轮色彩修正（身份色 vs 语义色分离）；设计系统存在 ≠ 设计系统被执行
  │
  ▼
TDD（Test-Driven）
  │  主导：Superpowers（test-driven-development 技能）
  │  目标：核心逻辑（嘉宾生成/发言调度/共识提炼）严格 RED→GREEN→REFACTOR
  │  产出：36 个单元测试 + 3 个核心服务（mock 覆盖合法/畸形/兜底场景）
  │  关键纪律：真红(逻辑未实现) ≠ 假红(import/async 配置缺失)；mock 测逻辑不测 LLM
  │
  ▼
E2E（End-to-End）
  │  主导：Superpowers + Playwright
  │  目标：覆盖"真实浏览器 × 真实数据链路"这一层——单元测试结构性无法覆盖的盲区
  │  产出：5 个 E2E spec（每条对应一个真实踩过的坑）+ 13 个 data-testid 锚点
  │  关键纪律：E2E 测管道通畅不测水质（mock LLM 确定性模式）；真实 LLM 质量靠人工联调抽验
  │
  ▼
交付
      PROMPTS.md（本文）+ WORKFLOW.md + README.md + Git 演进历史
```

**为什么这个顺序不能乱**：每一层的产出都是下一层的"宪法"。SDD 的 data-model 决定了 TDD 要测哪些实体；DDD 的 MASTER.md 决定了前端组件的每一个视觉 token；TDD 的 mock 模式决定了 E2E 怎么设计确定性测试环境。反过来，如果跳过 SDD 直接写代码，AI 会自由发挥、瞎编字段、接口前后不一致——这正是"契约约束 AI、防幻觉"的核心价值。

---

## 三插件分工：为什么需要三个 AI"角色"

本项目的核心挑战不是"AI 写不出代码"——AI 写代码很快。真正的挑战是：**在密集开发中，保持 AI 对项目全局状态的一致性理解，避免幻觉，同时产出 42 个绿测试、5 个 E2E spec、和后端 4 个 LLM 驱动服务的完整链路。**

答案是用三个 Claude Code 插件按职责拆解 AI 的工作上下文：

| 插件 | 职责 | 时机 | 加载的系统提示 |
|------|------|------|----------------|
| **Superpowers**（主干） | TDD 循环、写代码、修 bug、跑测试、code-review、分支管理 | 全程，95% 时间 | 通用开发规范（TDD 红绿重构、文件组织、Git 工作流） |
| **spec-kit** | SDD 阶段：constitution → specify → clarify → plan → tasks | Phase 1（一次性） | SDD 模板（spec 结构、clarify 流程、contracts 格式） |
| **ui-ux-pro-max** | DDD 阶段：设计系统生成、色彩/字体/动效/可访问性 | Phase 3.1-3.3（两轮修正） | 设计系统规范（色彩对比度检查、动效 token 定义、可访问性清单） |

**为什么这样拆**：AI 的上下文窗口不是无限的。如果在一个会话里让它同时理解"数据模型应该有几个实体"和"button 的 box-shadow 应该是多少"，它会混淆层次——在讨论 API 契约时推荐 CSS 变量，或者在写 React 组件时建议改数据库索引。拆分后，每个插件加载的是**该阶段最相关的系统提示**，让 AI 用该阶段的"专业身份"思考：
- spec-kit → "产品经理 + 架构师"
- ui-ux-pro-max → "设计师"
- Superpowers → "工程师"

**关键取舍：spec-kit 和 Superpowers 在"实现"这一步会争。** 两者在"需求→规划→实现→测试"主线上功能高度重叠——如果同时让它们各跑各的，会出现产出物打架（两份互相矛盾的"真理来源"）。处理原则（也是作业"严禁一键生成、必须体现工程拆解"的要求）：**实现环节以 Superpowers 的 TDD 流程为准，spec-kit 用到 `/speckit-tasks` 为止，不敲 `/speckit-implement` 一键生成。**

---

## 三个典型问题 + 如何被工程方法解决

### 问题 1：SSE 投递断链 — 七轮证据驱动排查

**这是整个项目最有教学价值的案例**，完整还原了"AI 给不出正确答案时，如何用工程方法一步步逼近真相"。

**现象**：Phase 4 把假事件源替换为真实 DiscussionOrchestrator 后，后端 trace 正常推进（round 1→2→3→4→5），但前端 EventStream 只收到心跳，收不到 utterance。

**AI 的默认诊断（全是错的）**：
- "LLM 调用太慢，timeout 不够" → 加了 90s timeout，无效
- "publish 队列写满阻塞" → breadcrumb trace 全部 `E:publish后` 正常通过
- "CORS 问题" → Console 无 CORS 报错
- "多 worker 进程隔离" → `id(_subscribers)` + `pid` 验证，单进程单实例

**为什么 AI 诊断错**：AI 训练数据中"单进程 asyncio 内存隔离"的 bug 模式极其罕见——它更习惯多进程/多容器的分布式问题。而这些"环境×代码"的耦合 bug，只有真实运行环境能暴露。

**真正的排查方法 — 证据驱动，不靠 AI 猜**：

| 轮次 | 假设 | 决定性实验 | 结果 | 结论 |
|------|------|-----------|------|------|
| 1 | LLM hang | 加 timeout | 仍卡 | ❌ 不是 LLM |
| 2 | publish 阻塞 | breadcrumb trace | 全部 E:publish后 正常 | ❌ 后端生产健康 |
| 3 | 前端渲染崩 | Console 检查 | 无报错 | ❌ 问题在投递 |
| 4 | 队列错位 | 心跳 vs 业务对比 | 心跳通·业务断 | 🔒 锁定投递链 |
| 5 | fan-out 缺失 | fan-out 重构 | 仍只有心跳 | ❌ 不是逻辑问题 |
| 6 | 模块双实例 | `id()` + `pid()` | pid 同，回退假源全通 | 🔒 两份 `_subscribers` |
| 7 | 对照实验 | 假源 vs 真源 | 假源收到/真源收不到 | ✅ **模块双路径 import** |

**根因**：orchestrator 的 `publish` 和 SSE endpoint 的 `subscribe` 引用了两份不同的 `_subscribers` 字典（模块被双路径 import 生成两份实例）。

**修复**：统一 import 路径 + 单进程启动 + per-discussion fan-out + 假源退休 + `print(id(_registry), pid)` 物理验证。

**教训**：这不是 AI 的能力问题，是人的工程判断问题——**当 AI 给的方向全是错的时，用 breadcrumb trace + 对照实验逐条推翻，比让 AI 再猜十次更有效。** 插件分工的意义不在于"AI 不会错"，而在于当 AI 给错方向时，你有明确的排查工具（测试基础设施、进程验证打印、回退对照）把问题逼回正轨。

---

### 问题 2：真实 LLM JSON 结构 ≠ mock — 单测绿 ≠ 真能用

SpeechScheduler 的 8 个单元测试全绿（mock AsyncMock 返回固定 JSON），但真实 DeepSeek 返回的 `content` 字段偶尔带 markdown 代码块包裹（`` ```json ... ``` ``）或中文标点不一致。

- **AI 的默认行为**：mock 通过后认为"代码正确"
- **真实问题**：`json.loads()` 无法解析被 markdown 包裹的 JSON 字符串
- **为什么单测没发现**：mock 返回的是"理想 JSON"，真实 LLM 返回的是"带噪声的 JSON"。单测验证的是"代码逻辑正确"，真实联调验证的是"prompt 工程正确"——**两者缺一不可。**

**修复**：在 `_call_llm` 的解析逻辑中加：
```python
content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
```

**教训**：TDD 的 mock 测试和 E2E 的真实 LLM 调用是互补的验证层。mock 保证"大模型返回垃圾时你的代码不崩"，E2E 保证"你的 prompt 能逼大模型返回对的结构"。**单测全绿只是必要条件，不是充分条件。**

---

### 问题 3：SSE `id: 0` 污染 Last-Event-ID — 规范中的隐含语义

浏览器 EventSource 的 `lastEventId` 会被任何带 `id:` 字段的 SSE 事件更新。早期实现中，heartbeat 事件带了 `id: 0\n`，导致浏览器重连时发送 `Last-Event-ID: 0`，后端从 seq 0 开始重放所有事件——我们 Phase 1 费大力气修好的"增量补拉"被一个心跳废掉了。

- **AI 的默认实现**：heartbeat 和其他事件用同一个 `publish()` 函数 → 自动带 `id:` 字段
- **真正的 SSE 规范要求**：不带 `id` 的事件不改变 `lastEventId`
- **修复**：heartbeat 和 snapshot 绕过 `publish()`，直接输出不带 `id:` 行的原始 SSE 字符串。补了 6 个回归测试（3 个 heartbeat 格式 + 3 个 snapshot 格式 + 1 个反例测试 `test_heartbeat_with_id_zero_would_be_bug`）。

**教训**：AI 熟悉"怎么写 SSE"，但不懂"为什么 heartbeat 不能有 id"。规范中的隐含语义（`id` 字段的副作用）需要人来注入。这也正是 SDD 阶段"把契约写进文件、人工审查"的价值——如果 SSE 契约没在 Phase 1 被人工审查修正，这个 bug 到 Phase 5 E2E 才暴露时，返工成本高得多。

---

## 工程化 AI 开发的理解

经过这个项目，我对"AI 辅助软件开发"形成了三层理解：

**第一层：AI 是代码生成器。** 这层最浅——AI 能高速产出 80% 的 boilerplate（CRUD 路由、React 组件骨架、pytest fixture、TypeScript 类型定义）。但剩下 20% 的"胶水代码"（服务之间的调用链、异步任务的 spawn/cancel、SSE 事件的 seq 管理、模块 import 路径一致性）需要人设计接口。**AI 产出量很大，但质量取决于你给它定的契约有多精确。**

**第二层：AI 是需求翻译器。** spec-kit 和 ui-ux-pro-max 在这层发挥作用——AI 把自然语言的业务需求翻译为结构化的 spec/plan/data-model/contracts，把设计理念翻译为可量化的色彩/字体/动效 token。但翻译质量取决于人的审查——panelist-2 颜色冲突（绿被共识独占）是人在审查 MASTER.md 时发现的，不是 AI；SSE `Event.seq` 和 `Utterance.seq` 双序列冲突是人在审查 data-model.md 时发现的，不是 AI。**AI 翻译得很快，但审稿人必须是人。**

**第三层：AI 不是调试器。** "环境×代码"的耦合 bug（多 worker 内存隔离、模块双实例、浏览器 SSE lastEventId 副作用、真实 LLM JSON 噪声、asyncio Task 被 GC 回收）只有真实运行环境才能暴露。AI 可以提供假设，但最终验证靠 `print(id(_registry), pid)`、breadcrumb trace、回退对照实验、和端到端的 httpx 直连测试。**AI 会给你十个可能的答案，但只有一个是正确的——你需要设计决定性实验来筛出那一个。**

**所以工程师的价值从"写代码"转向三个新能力：**

1. **设计契约** — 定义清晰的接口边界。`_call_llm` 作为唯一的 mock 点（生产和测试切换只改这一处）；`publish()` 作为 SSE 事件唯一入口（所有事件流经同一个函数）；`data-testid` 作为 E2E 锚点（组件不依赖 CSS class 或 DOM 结构定位）。**契约越精确，AI 的自由度越小，幻觉越少。**

2. **验证真相** — 当 AI 说"代码正确"，你能用独立手段验证。TDD 红绿循环验证逻辑正确性；端到端 HTTP 直连验证链路通畅；`print(id(_registry), pid)` 验证内存共享；回退对照实验分离变量。**AI 的输出是假设，不是真理——你需要自己能证明或推翻它。**

3. **掌控边界** — 知道什么该让 AI 做（boilerplate、prompt 模板、测试用例生成、设计系统初稿），什么必须人做（时序协议设计、并发安全分析、终极 bug 排查、设计系统的"身份色 vs 语义色"审计）。**边界模糊 = 上下文混乱 = 幻觉滋生。边界清晰 = AI 在框内高效产出 = 人只做 AI 做不了的事。**
