# Data Model: AI Panel Studio

**Date**: 2026-06-26

All entities are scoped by `discussion_id` for multi-discussion isolation (Constitution Principle V).

## Entity-Relationship Diagram

```
Discussion 1──* Panelist
Discussion 1──* Utterance
Discussion 1──* ConsensusPoint
Discussion 1──* DivergencePoint
Panelist   1──* Utterance
```

---

## Discussion

Core entity representing one AI roundtable discussion.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique discussion identifier |
| `topic` | TEXT | NOT NULL, 1–200 chars | Discussion topic (moderated) |
| `status` | TEXT | NOT NULL, DEFAULT 'pending_panelists' | Lifecycle state |
| `expert_count` | INTEGER | NOT NULL, 2–8 | Number of expert panelists requested |
| `max_rounds` | INTEGER | NOT NULL, DEFAULT 30 | Maximum utterance rounds before forced end |
| `current_round` | INTEGER | NOT NULL, DEFAULT 0 | Current round number |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Creation timestamp |
| `ended_at` | TEXT (ISO 8601) | nullable | End timestamp (null if active) |

**State Machine**:

```
pending_panelists ──→ in_progress ──→ ended
                          │
                     (panelists confirmed)
                          │
                     (host concludes OR max_rounds reached)
```

- `pending_panelists`: Panelist generation in progress / awaiting user confirmation
- `in_progress`: Discussion active, utterances flowing
- `ended`: Discussion concluded (natural or forced)

**Validation Rules**:
- `topic` MUST pass content moderation before creation
- `expert_count` MUST be 2–8
- Transition to `in_progress` requires confirmed panelist roster (1 host + N experts)
- Transition to `ended` triggers cascade: all panelist states frozen, SSE `discussion_end` event emitted

---

## Panelist

A participant (host or expert) in a discussion.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique panelist identifier |
| `discussion_id` | TEXT (UUID) | FK → Discussion.id, NOT NULL, INDEX | Owning discussion |
| `role` | TEXT | NOT NULL, 'host' or 'expert' | Role type |
| `name` | TEXT | NOT NULL | Generated display name |
| `title` | TEXT | NOT NULL | Profession/Title (e.g., "AI研究员") |
| `stance` | TEXT | NOT NULL | Position on topic (e.g., "支持有条件开源") |
| `color` | TEXT | NOT NULL | Hex color for UI badge (from preset palette) |
| `status` | TEXT | NOT NULL, DEFAULT 'idle' | Current activity state |
| `public_focus` | TEXT (JSON array) | DEFAULT '[]' | Public concerns/attention points |
| `sort_order` | INTEGER | NOT NULL | Display order (host=0, experts 1..N) |

**State Machine**:

```
idle ──→ preparing ──→ speaking ──→ idle
  │                                    │
  └──────────── silent ←───────────────┘
                (N consecutive rounds without speaking)
```

- `idle`: Waiting, no immediate intent to speak
- `preparing`: Evaluating transcript, about to request speak
- `speaking`: Currently delivering utterance
- `silent`: Has not spoken for multiple rounds (auto-assigned)

**Validation Rules**:
- `role='host'` panelist: exactly 1 per discussion, always `sort_order=0`
- `role='expert'` panelist: 2–8 per discussion, mutually diverse stances
- State transition `→ silent` is automatic after N consecutive rounds without speaking (N=5 suggested)
- `color` assigned from preset palette by sort_order index

---

## Utterance

A single speech entry in the discussion transcript.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique utterance identifier |
| `discussion_id` | TEXT (UUID) | FK → Discussion.id, NOT NULL, INDEX | Owning discussion |
| `panelist_id` | TEXT (UUID) | FK → Panelist.id, NOT NULL | Speaker |
| `seq` | INTEGER | NOT NULL, UNIQUE per discussion | Monotonic sequence number (for SSE id) |
| `type` | TEXT | NOT NULL | Utterance type |
| `content` | TEXT | NOT NULL, 1–500 chars | Speech content (1–2 sentences) |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Timestamp |

**Utterance Types**:

| Type | Speaker | Description |
|------|---------|-------------|
| `opening` | Host | Discussion opening, topic introduction, panelist introductions |
| `statement` | Expert | Opinion statement on topic |
| `rebuttal` | Expert | Counter-argument against another panelist's point |
| `supplement` | Expert | Additional supporting point |
| `question` | Host | Follow-up question to specific expert or group |
| `bridge` | Host | Transition between speakers/topics |
| `summary` | Host | Concluding natural-language summary |

**Validation Rules**:
- `seq` auto-increments per discussion (starts at 1)
- `content` length 1–500 chars (enforced 1–2 sentence guideline)
- Each utterance increments `Discussion.current_round` (one round = one utterance from any panelist)
- Expert utterances: `type` in (statement, rebuttal, supplement)
- Host utterances: `type` in (opening, question, bridge, summary)

---

## ConsensusPoint

A consensus finding extracted during discussion.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique consensus point identifier |
| `discussion_id` | TEXT (UUID) | FK → Discussion.id, NOT NULL, INDEX | Owning discussion |
| `content` | TEXT | NOT NULL | Consensus description in natural language |
| `involved_panelist_ids` | TEXT (JSON array) | NOT NULL | Panelists who agree on this point |
| `created_at` | TEXT (ISO 8601) | NOT NULL | First identified timestamp |
| `updated_at` | TEXT (ISO 8601) | NOT NULL | Last update timestamp |

**Behavior**:
- Consensus points are mutable — updated as discussion evolves (more panelists agree, or scope refines)
- New consensus points may emerge mid-discussion
- Consensus points are NOT deleted once created (they are part of the record)
- Each update triggers SSE `consensus_update` event

---

## DivergencePoint

A disagreement/divergence finding extracted during discussion.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique divergence point identifier |
| `discussion_id` | TEXT (UUID) | FK → Discussion.id, NOT NULL, INDEX | Owning discussion |
| `description` | TEXT | NOT NULL | Divergence description in natural language |
| `camps` | TEXT (JSON array) | NOT NULL | Grouped panelist positions: `[{"position": "...", "panelist_ids": [...]}]` |
| `created_at` | TEXT (ISO 8601) | NOT NULL | First identified timestamp |
| `updated_at` | TEXT (ISO 8601) | NOT NULL | Last update timestamp |

**Behavior**:
- Divergence points may resolve (panelists come to agreement) or persist
- Resolved divergences are NOT deleted — `updated_at` reflects resolution time, camps may collapse to one
- Each update triggers SSE `divergence_update` event

---

## Event (SSE Sequence Tracking)

Internal event log for SSE reconnection support.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PK AUTOINCREMENT | Monotonic event ID (global) |
| `discussion_id` | TEXT (UUID) | FK → Discussion.id, NOT NULL, INDEX | Owning discussion |
| `seq` | INTEGER | NOT NULL, UNIQUE per discussion | Per-discussion sequence number |
| `event_type` | TEXT | NOT NULL | SSE event type string |
| `payload_json` | TEXT | NOT NULL | Full event payload (JSON) |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Event timestamp |

**Usage**:
- Every SSE event is logged here for replay
- On reconnection with `Last-Event-ID`, server queries `WHERE discussion_id = ? AND seq > ? ORDER BY seq`
- Pruned when discussion is deleted (cascade)

---

## Index Strategy

```sql
-- Discussion queries
CREATE INDEX idx_discussion_status ON discussion(status);

-- Panelist queries
CREATE INDEX idx_panelist_discussion ON panelist(discussion_id);

-- Utterance queries
CREATE INDEX idx_utterance_discussion ON utterance(discussion_id);
CREATE UNIQUE INDEX idx_utterance_discussion_seq ON utterance(discussion_id, seq);

-- Consensus/Divergence queries
CREATE INDEX idx_consensus_discussion ON consensus_point(discussion_id);
CREATE INDEX idx_divergence_discussion ON divergence_point(discussion_id);

-- Event replay
CREATE INDEX idx_event_discussion_seq ON event(discussion_id, seq);
```

## Cascade Delete

```sql
-- All child records deleted when discussion is removed
-- Enforced via FK ON DELETE CASCADE or application-level cascade
DELETE FROM discussion WHERE id = ?;
-- Also deletes all related: panelist, utterance, consensus_point, divergence_point, event
```
