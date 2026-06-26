# REST API Contracts

**Base URL**: `/api`

All discussion-scoped endpoints follow the pattern `/api/discussions/{discussion_id}/...`.

---

## Discussions

### `GET /api/discussions`

List all discussions.

**Response** `200`:
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

**Notes**: `active_count` and `max_concurrent` support the concurrency limit display (FR-010).

---

### `POST /api/discussions`

Create a new discussion (triggers panelist generation).

**Request**:
```json
{
  "topic": "AI是否应该开源？",
  "expert_count": 4
}
```

**Response** `201`:
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

**Error Responses**:

`400` — Validation failure:
```json
{
  "error": "validation_error",
  "detail": "专家人数必须在2-8之间"
}
```

`422` — Content moderation rejection:
```json
{
  "error": "content_rejected",
  "detail": "话题包含不当内容，请修改后重试"
}
```

`429` — Concurrency limit reached:
```json
{
  "error": "too_many_discussions",
  "detail": "当前讨论已满（10/10），请等待某场讨论结束后再发起",
  "active_count": 10,
  "max_concurrent": 10
}
```

`502` — LLM generation failure:
```json
{
  "error": "generation_failed",
  "detail": "嘉宾生成失败，请稍后重试"
}
```

---

### `GET /api/discussions/{discussion_id}`

Get discussion details.

**Response** `200`:
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

### `DELETE /api/discussions/{discussion_id}`

Delete a discussion and all associated data.

**Response** `200`:
```json
{ "deleted": true }
```

---

## Panelists

### `POST /api/discussions/{discussion_id}/panelists/regenerate`

Regenerate the panelist roster (replaces all current panelists).

**Response** `200`: Same structure as `POST /api/discussions` response panelists array.

---

### `PATCH /api/discussions/{discussion_id}/panelists/confirm`

Confirm panelist roster and transition discussion to `in_progress`.

**Response** `200`:
```json
{
  "discussion_id": "uuid",
  "status": "in_progress"
}
```

**Error** `400` — No panelists generated yet:
```json
{
  "error": "invalid_state",
  "detail": "请先生成嘉宾阵容"
}
```

---

## Transcript

### `GET /api/discussions/{discussion_id}/transcript`

Get discussion transcript (paginated).

**Query Parameters**:
- `before_round` (int, optional): Get utterances before this round number (for loading older entries)
- `limit` (int, default=50): Max utterances to return

**Response** `200`:
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

## Consensus & Divergence

### `GET /api/discussions/{discussion_id}/consensus/current`

Get current consensus and divergence state (for snapshot on reconnection).

**Response** `200`:
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

---

## Common Response Headers

All responses include:
- `X-Discussion-Id: {discussion_id}` (for discussion-scoped endpoints)
