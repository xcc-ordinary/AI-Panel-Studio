# AI Panel Studio — API 文档

**版本**: v1.0.0 | **Base URL**: `/api` | **更新**: 2026-06-26

---

## 1. 概述

AI Panel Studio 后端提供 REST API（资源的 CRUD 操作）和 SSE 事件流（讨论实时推送）。

- **REST**: 所有讨论相关端点遵循 `/api/discussions/{discussion_id}/...` 模式，实现 discussion_id 级数据隔离
- **SSE**: 每场讨论一条独立的事件流连接 `GET /api/discussions/{discussion_id}/events`
- **通用响应头**: 讨论相关端点返回 `X-Discussion-Id: {discussion_id}`

---

## 2. REST 端点

### 2.1 讨论

#### `GET /api/discussions`

获取所有讨论列表。

**响应** `200`:
```json
{
  "discussions": [
    {
      "id": "uuid",
      "topic": "AI是否应该开源？",
      "status": "in_progress",
      "expert_count": 4,
      "current_round": 12,
      "max_rounds": 30,
      "panelist_count": 5,
      "created_at": "2026-06-26T10:00:00Z"
    }
  ],
  "active_count": 3,
  "max_concurrent": 10
}
```

> `active_count` 和 `max_concurrent` 用于首页展示并发讨论数与上限（FR-010）。

---

#### `POST /api/discussions`

创建新讨论，触发嘉宾阵容生成。

**请求**:
```json
{
  "topic": "AI是否应该开源？",
  "expert_count": 4
}
```

**响应** `201`:
```json
{
  "discussion_id": "uuid",
  "topic": "AI是否应该开源？",
  "status": "pending_panelists",
  "panelists": [
    {
      "id": "uuid",
      "role": "host",
      "name": "张明远",
      "title": "科技媒体主编",
      "stance": "中立——关注技术发展与社会影响的平衡",
      "color": "#2563EB",
      "sort_order": 0
    },
    {
      "id": "uuid",
      "role": "expert",
      "name": "李开放",
      "title": "开源社区领袖",
      "stance": "强烈支持——开源是技术创新的核心驱动力",
      "color": "#DC2626",
      "sort_order": 1
    }
  ]
}
```

**错误响应**:

| 状态码 | 错误类型 | 示例 detail |
|--------|---------|-------------|
| `400` | `validation_error` | "专家人数必须在2-8之间" |
| `422` | `content_rejected` | "话题包含不当内容，请修改后重试" |
| `429` | `too_many_discussions` | "当前讨论已满（10/10），请等待某场讨论结束后再发起" |
| `502` | `generation_failed` | "嘉宾生成失败，请稍后重试" |

`429` 响应额外包含:
```json
{
  "error": "too_many_discussions",
  "detail": "当前讨论已满（10/10），请等待某场讨论结束后再发起",
  "active_count": 10,
  "max_concurrent": 10
}
```

---

#### `GET /api/discussions/{discussion_id}`

获取单场讨论详情。

**响应** `200`:
```json
{
  "id": "uuid",
  "topic": "AI是否应该开源？",
  "status": "in_progress",
  "expert_count": 4,
  "current_round": 12,
  "max_rounds": 30,
  "created_at": "2026-06-26T10:00:00Z",
  "ended_at": null,
  "panelists": [...]
}
```

---

#### `DELETE /api/discussions/{discussion_id}`

删除讨论及所有关联数据（级联删除 panelist、utterance、consensus_point、divergence_point、event）。

**响应** `200`:
```json
{ "deleted": true }
```

---

### 2.2 嘉宾

#### `POST /api/discussions/{discussion_id}/panelists/regenerate`

重新生成嘉宾阵容（替换当前所有 panelists）。

**响应** `200`: 与 `POST /api/discussions` 返回的 `panelists` 数组结构一致。

---

#### `PATCH /api/discussions/{discussion_id}/panelists/confirm`

确认嘉宾阵容，将讨论状态从 `pending_panelists` 切换为 `in_progress`。

**响应** `200`:
```json
{
  "discussion_id": "uuid",
  "status": "in_progress"
}
```

**错误** `400` — 尚未生成嘉宾:
```json
{
  "error": "invalid_state",
  "detail": "请先生成嘉宾阵容"
}
```

---

### 2.3 Transcript

#### `GET /api/discussions/{discussion_id}/transcript`

获取讨论发言记录（分页，按 `round_no` 倒序）。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `before_round` | int | 可选 | 获取此轮次之前的发言（上翻加载） |
| `limit` | int | 50 | 单次最大返回条数 |

**响应** `200`:
```json
{
  "utterances": [
    {
      "id": "uuid",
      "round_no": 1,
      "panelist_id": "uuid",
      "panelist_name": "张明远",
      "panelist_title": "科技媒体主编",
      "panelist_color": "#2563EB",
      "type": "opening",
      "content": "各位好，欢迎来到今天的圆桌讨论...",
      "created_at": "2026-06-26T10:00:05Z"
    }
  ],
  "has_more": true
}
```

---

### 2.4 共识与分歧

#### `GET /api/discussions/{discussion_id}/consensus/current`

获取当前共识与分歧快照（用于 SSE 重连时恢复状态，也可独立轮询）。

**响应** `200`:
```json
{
  "consensus_points": [
    {
      "id": "uuid",
      "content": "与会专家一致认为AI开源需要建立统一的安全标准",
      "involved_panelist_ids": ["uuid1", "uuid2", "uuid3"],
      "updated_at": "2026-06-26T10:05:00Z"
    }
  ],
  "divergence_points": [
    {
      "id": "uuid",
      "description": "关于开源程度：一方主张完全开源，另一方认为核心模型应保留",
      "camps": [
        { "position": "完全开源", "panelist_ids": ["uuid1"] },
        { "position": "有限开源", "panelist_ids": ["uuid2", "uuid3"] }
      ],
      "updated_at": "2026-06-26T10:05:00Z"
    }
  ],
  "last_event_seq": 12
}
```

> `last_event_seq` 对应 `Event.seq`——SSE 事件流的最新序列号，用于判断是否有增量更新。

---

## 3. SSE 事件流

### 3.1 连接

**端点**: `GET /api/discussions/{discussion_id}/events`

每个客户端、每场讨论一条持久连接。

**请求**:
```
GET /api/discussions/{discussion_id}/events
Accept: text/event-stream
Last-Event-ID: {last_received_event_seq}   // 可选：重连时发送，值为 Event.seq
```

**响应头**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Discussion-Id: {discussion_id}
```

### 3.2 事件格式

所有事件遵循标准 SSE 格式：

```
id: {seq}
event: {event_type}
data: {json_payload}

```

- **`id`**: 讨论内单调递增序列号——**始终来源于 `Event.seq`**，是讨论内所有事件类型共享的唯一规范序列
- **`event`**: 事件类型字符串
- **`data`**: 单行 JSON 载荷

### 3.3 事件类型

#### `utterance` — 新发言

```
id: 5
event: utterance
data: {"id":"uuid","round_no":5,"panelist_id":"uuid","panelist_name":"李开放","panelist_title":"开源社区领袖","panelist_color":"#DC2626","type":"statement","content":"我认为开源不仅仅是代码共享，更是一种协作文化和创新机制。","created_at":"2026-06-26T10:02:00Z"}
// 注意: id(Event.seq) 与 round_no 相互独立——前者计入所有事件,后者仅计发言,示例数值相同纯属巧合。
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uuid | 发言唯一标识 |
| `round_no` | int | 讨论内发言轮次编号（仅用于排序和分页） |
| `panelist_id` | uuid | 发言人 ID |
| `panelist_name` | string | 发言人姓名 |
| `panelist_title` | string | 发言人职业/Title |
| `panelist_color` | string | 发言人专属色块 hex |
| `type` | string | 发言类型（opening/statement/rebuttal/supplement/question/bridge/summary） |
| `content` | string | 发言内容（1–2句） |
| `created_at` | ISO 8601 | 发言时间 |

---

#### `panelist_status` — 嘉宾状态变更

```
id: 6
event: panelist_status
data: {"panelist_id":"uuid","status":"preparing","public_focus":["关注李开放关于开源文化的论述","准备补充企业级开源案例"]}
```

**状态值**: `idle`（待发言）、`preparing`（准备发言）、`speaking`（发言中）、`silent`（沉默中）

---

#### `consensus_update` — 共识更新

共识点被创建或更新时触发。

```
id: 7
event: consensus_update
data: {"id":"uuid","content":"与会专家一致认为AI开源需要建立统一的安全标准","involved_panelist_ids":["uuid1","uuid2","uuid3"],"updated_at":"2026-06-26T10:05:00Z"}
```

---

#### `divergence_update` — 分歧更新

分歧点被创建或更新时触发。

```
id: 8
event: divergence_update
data: {"id":"uuid","description":"关于开源程度：一方主张完全开源，另一方认为核心模型应保留","camps":[{"position":"完全开源","panelist_ids":["uuid1"]},{"position":"有限开源","panelist_ids":["uuid2","uuid3"]}],"updated_at":"2026-06-26T10:05:00Z"}
```

---

#### `discussion_end` — 讨论结束

讨论结束时发送（自然结束或轮次达上限强制结束）。发送后服务器关闭 SSE 连接。

```
id: 42
event: discussion_end
data: {"discussion_id":"uuid","summary":"感谢各位专家今天的精彩讨论。关于AI是否应该开源，我们形成了几个重要共识：首先...然而在开源程度上，专家们存在明显分歧...","total_rounds":30,"silent_panelists":[{"id":"uuid","name":"王保守"}],"ended_at":"2026-06-26T10:15:00Z"}
```

| 字段 | 说明 |
|------|------|
| `summary` | 主持人自然语言总结，不含 JSON |
| `total_rounds` | 讨论总轮次 |
| `silent_panelists` | 未发言的沉默专家列表 |
| `ended_at` | 结束时间 |

---

#### `heartbeat` — 心跳

每15秒无其他事件时发送，保持连接活跃。若30秒内未收到心跳，客户端应假设连接已断开并重连。

```
event: heartbeat
data: {"timestamp":"2026-06-26T10:02:15Z"}
```

> heartbeat 故意**不携带 `id` 字段**——不得修改浏览器的 `lastEventId`。

---

### 3.4 断线重连协议

**快照 + 基于 Last-Event-ID 的增量补拉：**

1. 客户端 `EventSource` 断线后自动重连，携带 `Last-Event-ID: {最后收到的 Event.seq}`
2. 服务端检测到 `Last-Event-ID` 头 → 进入重连模式
3. 服务端响应顺序：
   - **首条事件**: `snapshot`，包含当前共识/分歧状态 + 最近 20 条发言
   - **后续事件**: 所有 `Event.seq > Last-Event-ID` 的事件按序重放
4. 客户端合并快照到 UI 状态，然后正常处理重放事件

#### `snapshot` 事件（仅重连时发送）

```
event: snapshot
data: {"consensus_points":[...],"divergence_points":[...],"recent_utterances":[...],"current_round":12,"last_event_seq":12}
```

> snapshot 故意**不携带 `id` 字段**——不得修改浏览器的 `lastEventId`，保证重连序列号连续。紧随其后的是断线期间缺失的增量事件重放。
