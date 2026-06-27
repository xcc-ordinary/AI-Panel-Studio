"""Discussion Orchestrator — confirmed panelists → spawn → speech loop → end.

Flow:
  confirm_panelists (PATCH) → spawn_discussion() → asyncio.create_task(run())
  run(): load state → loop{ schedule → persist → publish → extract_consensus } → discussion_end → cleanup

Key constraint: orchestrator and SSE endpoint share the same asyncio event loop
and the same `app.api.sse.manager._registry` dict (single process, no --workers).
"""
import asyncio
import json as _json
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.api.sse.manager import publish, cleanup as sse_cleanup
from app.services.speech_scheduler import SpeechScheduler
from app.services.consensus_extractor import ConsensusExtractor


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

CONSENSUS_INTERVAL = 3  # Extract consensus every N rounds


class DiscussionOrchestrator:
    """Runs one discussion to completion: speech scheduling → persist → SSE publish."""

    def __init__(self, discussion_id: str):
        self.discussion_id = discussion_id
        self.scheduler = SpeechScheduler()
        self.extractor = ConsensusExtractor()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def run(self) -> None:
        """Main loop. Exits when discussion ends, is cancelled, or errors."""
        db = await get_db()

        # ── Load discussion ──────────────────────────────────
        row = await db.execute("SELECT * FROM discussion WHERE id = ?", (self.discussion_id,))
        disc = await row.fetchone()
        if not disc:
            return

        # ── Load panelists ────────────────────────────────────
        p_rows = await db.execute(
            "SELECT id, role, name, title, stance, color, status, sort_order "
            "FROM panelist WHERE discussion_id = ? ORDER BY sort_order",
            (self.discussion_id,),
        )
        panelists: list[dict] = []
        async for p in p_rows:
            panelists.append({
                "id": p["id"], "role": p["role"], "name": p["name"],
                "title": p["title"], "stance": p["stance"], "color": p["color"],
                "status": p["status"], "sort_order": p["sort_order"],
            })

        # ── Derive next round_no from utterance table (sole source of truth) ──
        row = await db.execute(
            "SELECT COALESCE(MAX(round_no), -1) + 1 AS next_round "
            "FROM utterance WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        current_round = (await row.fetchone())[0]
        max_rounds = disc["max_rounds"]
        topic = disc["topic"]

        if current_round != disc["current_round"]:
            await db.execute(
                "UPDATE discussion SET current_round = ? WHERE id = ?",
                (current_round, self.discussion_id),
            )
            await db.commit()

        # ── Load existing consensus/divergence IDs for dedup ──
        existing_c_ids: set[str] = set()
        existing_d_ids: set[str] = set()
        c_rows = await db.execute(
            "SELECT id FROM consensus_point WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        async for r in c_rows:
            existing_c_ids.add(r["id"])
        d_rows = await db.execute(
            "SELECT id FROM divergence_point WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        async for r in d_rows:
            existing_d_ids.add(r["id"])

        print(f"[orchestrator] discussion={self.discussion_id} start "
              f"round={current_round}/{max_rounds} panelists={len(panelists)}", flush=True)

        try:
            while not self._cancelled:
                # ── Load transcript ──────────────────────────
                transcript = await self._load_transcript(db)
                panelist_states = self._build_states(panelists, transcript)

                # ── Decide next speaker ────────────────────────
                decision = await self.scheduler.decide_next_speaker(
                    self.discussion_id, transcript, panelist_states,
                    current_round, max_rounds,
                )

                # ── Summary → end discussion ──────────────────
                if decision["type"] == "summary":
                    summary = await self._generate_summary(
                        db, topic, transcript, existing_c_ids, existing_d_ids, panelists,
                    )
                    await self._end_discussion(db, summary, current_round, panelist_states)
                    return

                # ── Persist utterance ─────────────────────────
                speaker_id = decision["speaker_id"]
                speaker = next((p for p in panelists if p["id"] == speaker_id), panelists[0])

                utt_id = str(uuid.uuid4())
                await db.execute(
                    "INSERT INTO utterance (id, discussion_id, round_no, panelist_id, type, content, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (utt_id, self.discussion_id, current_round, speaker_id,
                     decision["type"], decision["content"], _now()),
                )
                await db.execute(
                    "UPDATE discussion SET current_round = ? WHERE id = ?",
                    (current_round + 1, self.discussion_id),
                )
                await db.commit()

                # ── Publish utterance SSE event ───────────────
                await publish(self.discussion_id, "utterance", {
                    "id": utt_id,
                    "round_no": current_round,
                    "panelist_id": speaker_id,
                    "panelist_name": speaker["name"],
                    "panelist_title": speaker["title"],
                    "panelist_color": speaker["color"],
                    "type": decision["type"],
                    "content": decision["content"],
                    "created_at": _now(),
                })

                # ── Publish status: speaking → idle ────────────
                await publish(self.discussion_id, "panelist_status", {
                    "panelist_id": speaker_id,
                    "status": "speaking",
                    "public_focus": "[]",
                })
                await asyncio.sleep(1.2)
                await publish(self.discussion_id, "panelist_status", {
                    "panelist_id": speaker_id,
                    "status": "idle",
                    "public_focus": "[]",
                })

                current_round += 1

                # ── Extract consensus every N rounds ────────────
                if current_round > 0 and current_round % CONSENSUS_INTERVAL == 0:
                    await self._extract_and_publish(
                        db, transcript, panelists,
                        existing_c_ids, existing_d_ids,
                    )

                # ── Pacing between rounds ─────────────────────
                await asyncio.sleep(2.0)

        except Exception as exc:
            print(f"[orchestrator] discussion={self.discussion_id} error: {exc}", flush=True)
            # ── Natural language error summary, no JSON leak ──
            await publish(self.discussion_id, "discussion_end", {
                "discussion_id": self.discussion_id,
                "summary": "讨论因技术原因提前结束，感谢各位专家的参与。请返回首页查看其他讨论。",
                "total_rounds": current_round,
                "silent_panelists": [],
                "ended_at": _now(),
            })
            await db.execute(
                "UPDATE discussion SET status = 'ended', ended_at = ? WHERE id = ?",
                (_now(), self.discussion_id),
            )
            await db.commit()
        finally:
            print(f"[orchestrator] discussion={self.discussion_id} finished", flush=True)
            _orchestrators.pop(self.discussion_id, None)

    # ── helpers ───────────────────────────────────────────────────

    async def _load_transcript(self, db) -> list[dict]:
        rows = await db.execute(
            "SELECT panelist_id, type, content FROM utterance "
            "WHERE discussion_id = ? ORDER BY round_no",
            (self.discussion_id,),
        )
        transcript: list[dict] = []
        async for r in rows:
            transcript.append({
                "speaker_id": r["panelist_id"],
                "type": r["type"],
                "content": r["content"],
            })
        return transcript

    def _build_states(self, panelists: list[dict], transcript: list[dict]) -> list[dict]:
        states = []
        for p in panelists:
            silent = 0
            for u in reversed(transcript):
                if u["speaker_id"] == p["id"]:
                    break
                silent += 1
            states.append({
                "id": p["id"], "role": p["role"], "name": p["name"],
                "stance": p["stance"], "silent_rounds": silent,
            })
        return states

    async def _extract_and_publish(
        self, db, transcript: list[dict], panelists: list[dict],
        existing_c_ids: set[str], existing_d_ids: set[str],
    ) -> None:
        """Call ConsensusExtractor, persist new points, publish SSE events."""
        print(f"[orchestrator] extracting consensus after {len(transcript)} utterances...", flush=True)
        result = await self.extractor.extract(
            self.discussion_id, transcript, panelists,
            existing_c_ids, existing_d_ids,
        )
        print(f"[orchestrator] consensus result: c={len(result.get('consensus_points',[]))} d={len(result.get('divergence_points',[]))}", flush=True)

        for cp in result.get("consensus_points", []):
            if cp["id"] in existing_c_ids:
                continue
            existing_c_ids.add(cp["id"])
            await db.execute(
                "INSERT INTO consensus_point (id, discussion_id, content, involved_panelist_ids, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (cp["id"], self.discussion_id, cp["content"],
                 _json.dumps(cp["involved_panelist_ids"], ensure_ascii=False),
                 cp["created_at"], cp["updated_at"]),
            )
            await db.commit()
            await publish(self.discussion_id, "consensus_update", cp)

        for dp in result.get("divergence_points", []):
            if dp["id"] in existing_d_ids:
                continue
            existing_d_ids.add(dp["id"])
            await db.execute(
                "INSERT INTO divergence_point (id, discussion_id, description, camps, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (dp["id"], self.discussion_id, dp["description"],
                 _json.dumps(dp["camps"], ensure_ascii=False),
                 dp["created_at"], dp["updated_at"]),
            )
            await db.commit()
            await publish(self.discussion_id, "divergence_update", dp)

    async def _generate_summary(
        self, db, topic: str, transcript: list[dict],
        existing_c_ids: set[str], existing_d_ids: set[str],
        panelists: list[dict],
    ) -> str:
        """Generate a natural-language Chinese summary via LLM."""
        from app.llm.prompts import SUMMARY_SYSTEM, SUMMARY_USER

        id_to_name = {p["id"]: p["name"] for p in panelists}

        # Format transcript for summary
        transcript_text = ""
        for t in transcript[-10:]:
            name = id_to_name.get(t.get("speaker_id", ""), "?")
            transcript_text += f"[{name}]: {t.get('content', '')}\n"

        # Load consensus/divergence summaries from DB
        consensus_items = []
        c_rows = await db.execute(
            "SELECT content FROM consensus_point WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        async for r in c_rows:
            consensus_items.append(f"· {r['content']}")
        consensus_summary = "\n".join(consensus_items) if consensus_items else "暂无"

        divergence_items = []
        d_rows = await db.execute(
            "SELECT description FROM divergence_point WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        async for r in d_rows:
            divergence_items.append(f"· {r['description']}")
        divergence_summary = "\n".join(divergence_items) if divergence_items else "暂无"

        messages = [
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": SUMMARY_USER.format(
                topic=topic,
                transcript=transcript_text,
                consensus_summary=consensus_summary,
                divergence_summary=divergence_summary,
            )},
        ]

        try:
            resp = await self.extractor._call_llm(messages)
            content = resp["choices"][0]["message"]["content"]
            # Strip any accidental JSON wrapping
            content = content.strip()
            if content.startswith("{") or content.startswith("```"):
                # LLM returned JSON instead of plain text — try to extract
                try:
                    data = _json.loads(content)
                    if isinstance(data, dict):
                        content = data.get("summary", data.get("content", content))
                except _json.JSONDecodeError:
                    content = content.replace("```json", "").replace("```", "").strip()
            return content
        except Exception as e:
            print(f"[orchestrator] Summary generation failed: {e}", flush=True)
            return "感谢各位专家的精彩讨论。本次圆桌就相关话题进行了深入交流，各方在多个层面达成共识，也存在值得继续探讨的分歧。期待下期再会。"

    async def _end_discussion(self, db, summary: str, total_rounds: int,
                              states: list[dict]) -> None:
        silent = [s for s in states if s.get("silent_rounds", 0) >= 5]

        await db.execute(
            "UPDATE discussion SET status = 'ended', ended_at = ? WHERE id = ?",
            (_now(), self.discussion_id),
        )
        await db.commit()

        await publish(self.discussion_id, "discussion_end", {
            "discussion_id": self.discussion_id,
            "summary": summary,
            "total_rounds": total_rounds,
            "silent_panelists": [{"id": s["id"], "name": s["name"]} for s in silent],
            "ended_at": _now(),
        })


# ── Module-level orchestrator registry ───────────────────────────

_orchestrators: dict[str, DiscussionOrchestrator] = {}


async def spawn_discussion(discussion_id: str) -> bool:
    """Start a discussion orchestrator in the background. Idempotent."""
    if discussion_id in _orchestrators:
        return False
    orch = DiscussionOrchestrator(discussion_id)
    _orchestrators[discussion_id] = orch

    async def _runner():
        await orch.run()

    asyncio.create_task(_runner())
    return True


async def cancel_discussion(discussion_id: str) -> bool:
    """Cancel a running discussion orchestrator."""
    orch = _orchestrators.pop(discussion_id, None)
    if orch:
        orch.cancel()
        return True
    return False


def is_running(discussion_id: str) -> bool:
    """Check if an orchestrator is currently running for this discussion."""
    return discussion_id in _orchestrators
