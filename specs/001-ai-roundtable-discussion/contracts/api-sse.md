# SSE Event Stream Contracts

**Endpoint**: `GET /api/discussions/{discussion_id}/events`

**Content-Type**: `text/event-stream`

**Connection**: Persistent SSE connection. One per client per discussion.

---

## Connection

### Request

```
GET /api/discussions/{discussion_id}/events
Accept: text/event-stream
Last-Event-ID: {last_received_event_seq}   // Optional: sent on reconnection, value from Event.seq
```

### Response Headers

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Discussion-Id: {discussion_id}
```

---

## Event Format

All events follow standard SSE format:

```
id: {seq}
event: {event_type}
data: {json_payload}

```

- `id`: Monotonic sequence number per discussion — **always sourced from `Event.seq`**, the sole canonical SSE sequence across all event types within a discussion
- `event`: Event type string
- `data`: JSON payload (single line)

---

## Event Types

### `utterance`

New speech entry in transcript.

```
id: 5
event: utterance
data: {"id":"uuid","round_no":5,"panelist_id":"uuid","panelist_name":"李开放","panelist_title":"开源社区领袖","panelist_color":"#DC2626","type":"statement","content":"我认为开源不仅仅是代码共享，更是一种协作文化和创新机制。","created_at":"2026-06-26T10:02:00Z"}
// 注意: id(Event.seq) 与 round_no 相互独立——前者计入所有事件,后者仅计发言,示例数值相同纯属巧合。

```

---

### `panelist_status`

Panelist state change.

```
id: 6
event: panelist_status
data: {"panelist_id":"uuid","status":"preparing","public_focus":["关注李开放关于开源文化的论述","准备补充企业级开源案例"]}

```

**Status values**: `idle`, `preparing`, `speaking`, `silent`

---

### `consensus_update`

Consensus point created or updated.

```
id: 7
event: consensus_update
data: {"id":"uuid","content":"与会专家一致认为AI开源需要建立统一的安全标准","involved_panelist_ids":["uuid1","uuid2","uuid3"],"updated_at":"2026-06-26T10:05:00Z"}

```

---

### `divergence_update`

Divergence point created or updated.

```
id: 8
event: divergence_update
data: {"id":"uuid","description":"关于开源程度：一方主张完全开源，另一方认为核心模型应保留","camps":[{"position":"完全开源","panelist_ids":["uuid1"]},{"position":"有限开源","panelist_ids":["uuid2","uuid3"]}],"updated_at":"2026-06-26T10:05:00Z"}

```

---

### `discussion_end`

Discussion concluded (natural end or forced by max rounds).

```
id: 42
event: discussion_end
data: {"discussion_id":"uuid","summary":"感谢各位专家今天的精彩讨论。关于AI是否应该开源，我们形成了几个重要共识：首先...然而在开源程度上，专家们存在明显分歧...","total_rounds":30,"silent_panelists":[{"id":"uuid","name":"王保守"}],"ended_at":"2026-06-26T10:15:00Z"}

```

After this event, the SSE connection is closed by the server.

---

### `heartbeat`

Keep-alive ping, sent every 15 seconds when no other events.

```
event: heartbeat
data: {"timestamp":"2026-06-26T10:02:15Z"}

```

**Note**: heartbeat deliberately has **no `id` field** — it must not alter the browser's `lastEventId`.

If no heartbeat received for 30 seconds, client SHOULD assume connection lost and reconnect.

---

## Reconnection: Snapshot + Last-Event-ID

### Client Reconnection Flow

1. Client's `EventSource` auto-reconnects with `Last-Event-ID: {last_received_event_seq}` header (value from `Event.seq`)
2. Server detects `Last-Event-ID` header → reconnection mode
3. Server response:
   - First event: `snapshot` with current consensus/divergence state + last 20 utterances
   - Subsequent events: All `Event` rows with `seq > Last-Event-ID` replayed in order
4. Client merges snapshot into UI state, then processes replay events normally

### `snapshot` Event (Reconnection Only)

```
event: snapshot
data: {"consensus_points":[...],"divergence_points":[...],"recent_utterances":[...],"current_round":12,"last_event_seq":12}

```

**Note**: snapshot deliberately has **no `id` field**. Per SSE spec, events without `id` do not alter the browser's `lastEventId`, so the reconnection sequence remains continuous. It is immediately followed by replay events.

---

## Server Implementation Notes

- Each discussion maintains an `asyncio.Queue` of events
- Connected SSE clients are registered as queue consumers
- On new event (utterance/status/consensus), event is pushed to all connected clients' queues
- Event also persisted to `event` table for replay
- Cleanup: when discussion ends, `discussion_end` sent, then all queues closed
