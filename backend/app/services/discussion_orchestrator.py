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

CONSENSUS_INTERVAL = 2  # Extract consensus every N rounds (higher frequency for real-time feel)


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
            # ═══════════════════════════════════════════════════════
            # Phase 1: 主持人开场
            # ═══════════════════════════════════════════════════════
            transcript = await self._load_transcript(db)
            panelist_states = self._build_states(panelists, transcript)
            decision = await self.scheduler.decide_next_speaker(
                self.discussion_id, transcript, panelist_states,
                current_round, max_rounds,
            )
            speaker_id = decision["speaker_id"]
            speaker = next((p for p in panelists if p["id"] == speaker_id), panelists[0])
            await self._persist_and_publish(db, decision, speaker, current_round, panelists)
            current_round += 1
            await asyncio.sleep(1.5)

            # ═══════════════════════════════════════════════════════
            # Phase 2: 专家立论——每人亮出开场陈述
            # ═══════════════════════════════════════════════════════
            experts = [p for p in panelists if p.get("role") != "host"]
            print(f"[orchestrator] generating opening statements for {len(experts)} experts...", flush=True)
            for expert in experts:
                if self._cancelled or current_round >= max_rounds:
                    break
                try:
                    statement = await self._generate_opening_statement(
                        expert["name"], expert.get("stance", ""), topic,
                    )
                except Exception:
                    statement = f"我是{expert['name']}，我的立场是{expert.get('stance', '')}。我认为这个话题需要在实践中寻找答案。"

                await self._persist_and_publish(db, {
                    "speaker_id": expert["id"], "type": "statement", "content": statement,
                }, expert, current_round, panelists)
                current_round += 1
                await asyncio.sleep(1.0)

            # ═══════════════════════════════════════════════════════
            # Phase 3: 自由辩论——只受 max_rounds 控制
            # ═══════════════════════════════════════════════════════
            while not self._cancelled and current_round < max_rounds:
                # ── Load transcript ──────────────────────────
                transcript = await self._load_transcript(db)
                panelist_states = self._build_states(panelists, transcript)

                # ── Decide next speaker ────────────────────────
                # SpeechScheduler 已在代码层剥夺了 LLM 的提前 summary 权：
                # 在 current_round < max_rounds 时，type="summary" 会被强制覆写为 question。
                decision = await self.scheduler.decide_next_speaker(
                    self.discussion_id, transcript, panelist_states,
                    current_round, max_rounds,
                )

                # ── Persist + publish (refactored) ──────────────
                speaker = next((p for p in panelists if p["id"] == decision["speaker_id"]), panelists[0])
                await self._persist_and_publish(db, decision, speaker, current_round, panelists)
                current_round += 1

                # ── Extract consensus every N rounds ────────────
                if current_round > 0 and current_round % CONSENSUS_INTERVAL == 0:
                    # 独立 try-except：提取失败不应当终止整场讨论
                    try:
                        await self._extract_and_publish(
                            db, transcript, panelists,
                            existing_c_ids, existing_d_ids,
                        )
                    except Exception as _extract_exc:
                        print(
                            f"[orchestrator] CRITICAL: _extract_and_publish crashed!\n"
                            f"  Error: {type(_extract_exc).__name__}: {_extract_exc}\n"
                            f"  Traceback:",
                            flush=True,
                        )
                        import traceback as _tb
                        _tb.print_exc()
                        # 讨论继续——不能因为提取失败就终止

                # ── Pacing between rounds ─────────────────────
                await asyncio.sleep(2.0)

            # ═══════════════════════════════════════════════════════
            # 主循环自然结束（current_round >= max_rounds）→ 强制触发总结
            # ═══════════════════════════════════════════════════════
            if not self._cancelled:
                print(f"[orchestrator] max_rounds reached, generating summary...", flush=True)
                try:
                    await self._emit_discussion_end_bulletproof(db, current_round, topic, panelists)
                except Exception as _end_exc:
                    print(f"[orchestrator] CRITICAL: _emit_discussion_end_bulletproof failed: {_end_exc}", flush=True)
                    # 终极安全网——裸 publish discussion_end
                    try:
                        await publish(self.discussion_id, "discussion_end", {
                            "discussion_id": self.discussion_id,
                            "summary": "感谢各位专家的精彩讨论，本场圆桌正式结束。",
                            "total_rounds": current_round,
                            "silent_panelists": [],
                            "ended_at": _now(),
                        })
                    except Exception:
                        pass

        except Exception as exc:
            print(f"[orchestrator] discussion={self.discussion_id} error: {exc}", flush=True)
            import traceback
            traceback.print_exc()
            # 即使异常路径的 bulletproof 也失败了，也要发 discussion_end
            try:
                await self._emit_discussion_end_bulletproof(db, current_round, "（异常结束）", panelists)
            except Exception:
                try:
                    await publish(self.discussion_id, "discussion_end", {
                        "discussion_id": self.discussion_id,
                        "summary": "讨论因技术原因提前结束，感谢各位专家的参与。",
                        "total_rounds": current_round,
                        "silent_panelists": [],
                        "ended_at": _now(),
                    })
                except Exception:
                    pass
        finally:
            # ── 无论如何更新 DB 状态 ──
            try:
                await db.execute(
                    "UPDATE discussion SET status = 'ended', ended_at = ? WHERE id = ?",
                    (_now(), self.discussion_id),
                )
                await db.commit()
            except Exception:
                pass
            print(f"[orchestrator] discussion={self.discussion_id} finished", flush=True)
            _orchestrators.pop(self.discussion_id, None)

    # ── helpers ───────────────────────────────────────────────────

    async def _persist_and_publish(
        self, db, decision: dict, speaker: dict, round_no: int, panelists: list[dict],
    ) -> str:
        """持久化发言 + 发布 SSE utterance + speaking/idle 状态切换。返回 utterance ID。"""
        utt_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO utterance (id, discussion_id, round_no, panelist_id, type, content, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (utt_id, self.discussion_id, round_no, decision["speaker_id"],
             decision["type"], decision["content"], _now()),
        )
        await db.execute(
            "UPDATE discussion SET current_round = ? WHERE id = ?",
            (round_no + 1, self.discussion_id),
        )
        await db.commit()

        await publish(self.discussion_id, "utterance", {
            "id": utt_id, "round_no": round_no,
            "panelist_id": decision["speaker_id"],
            "panelist_name": speaker["name"],
            "panelist_title": speaker["title"],
            "panelist_color": speaker["color"],
            "type": decision["type"],
            "content": decision["content"],
            "created_at": _now(),
        })

        # Status: speaking → idle
        await publish(self.discussion_id, "panelist_status", {
            "panelist_id": decision["speaker_id"],
            "status": "speaking", "public_focus": "[]",
        })
        await asyncio.sleep(1.2)
        await publish(self.discussion_id, "panelist_status", {
            "panelist_id": decision["speaker_id"],
            "status": "idle", "public_focus": "[]",
        })
        return utt_id

    async def _generate_opening_statement(
        self, name: str, stance: str, topic: str,
    ) -> str:
        """调 LLM 为一位专家生成开场立论陈述。异常时返回兜底陈述。"""
        from app.llm.prompts import OPENING_STATEMENT_SYSTEM, OPENING_STATEMENT_USER
        from app.llm.client import chat_completion

        messages = [
            {"role": "system", "content": OPENING_STATEMENT_SYSTEM},
            {"role": "user", "content": OPENING_STATEMENT_USER.format(
                topic=topic, name=name, stance=stance,
            )},
        ]
        try:
            resp = await chat_completion(messages, temperature=0.7)
            content = resp["choices"][0]["message"]["content"]
            content = content.strip().strip('"').strip("'").strip()
            return content if content else f"我是{name}。关于{topic}，我的立场是{stance}。"
        except Exception as e:
            print(f"[orchestrator] opening statement for {name} failed: {e}", flush=True)
            return f"我是{name}。关于{topic}，我的立场是{stance}。我希望通过今天的讨论找到更多共识。"

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

    async def _fetch_existing_consensus(self, db) -> list[dict]:
        """Query all existing consensus points for this discussion (with content)."""
        rows = await db.execute(
            "SELECT id, content FROM consensus_point WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        results: list[dict] = []
        async for r in rows:
            results.append({"id": r["id"], "content": r["content"]})
        return results

    async def _fetch_existing_divergence(self, db) -> list[dict]:
        """Query all existing divergence points for this discussion (with description + camps)."""
        rows = await db.execute(
            "SELECT id, description, camps FROM divergence_point WHERE discussion_id = ?",
            (self.discussion_id,),
        )
        results: list[dict] = []
        async for r in rows:
            camps = []
            try:
                camps = _json.loads(r["camps"]) if r["camps"] else []
            except (_json.JSONDecodeError, TypeError):
                camps = []
            results.append({
                "id": r["id"],
                "description": r["description"],
                "camps": camps,
            })
        return results

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
        """Call ConsensusExtractor, persist new points, publish SSE events.

        Passes existing consensus/divergence **content** (not just IDs) so the LLM can
        perform semantic dedup — preventing the same debate point from being re-extracted.
        """
        print(f"[orchestrator] extracting consensus after {len(transcript)} utterances...", flush=True)

        # Fetch existing content for semantic dedup (on top of ID-based dedup)
        existing_consensus = await self._fetch_existing_consensus(db)
        existing_divergence = await self._fetch_existing_divergence(db)

        result = await self.extractor.extract(
            self.discussion_id, transcript, panelists,
            existing_consensus, existing_divergence,
        )
        print(f"[orchestrator] consensus result: c={len(result.get('consensus_points',[]))} d={len(result.get('divergence_points',[]))}", flush=True)

        for cp in result.get("consensus_points", []):
            if not isinstance(cp, dict):
                continue
            cid = cp.get("id", str(uuid.uuid4()))
            if cid in existing_c_ids:
                continue
            existing_c_ids.add(cid)
            now = _now()
            c_content = cp.get("content", "") or "(共识点)"
            c_involved = cp.get("involved_panelist_ids", []) or []
            await db.execute(
                "INSERT INTO consensus_point (id, discussion_id, content, involved_panelist_ids, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (cid, self.discussion_id, c_content,
                 _json.dumps(c_involved, ensure_ascii=False),
                 cp.get("created_at", now), cp.get("updated_at", now)),
            )
            await db.commit()
            await publish(self.discussion_id, "consensus_update", {
                "id": cid, "content": c_content,
                "involved_panelist_ids": c_involved,
                "created_at": cp.get("created_at", now),
                "updated_at": cp.get("updated_at", now),
            })

        for dp in result.get("divergence_points", []):
            if not isinstance(dp, dict):
                continue
            did = dp.get("id", str(uuid.uuid4()))
            if did in existing_d_ids:
                continue
            existing_d_ids.add(did)
            now = _now()
            d_description = dp.get("description", "") or "(分歧点)"
            d_camps = dp.get("camps", []) or []
            await db.execute(
                "INSERT INTO divergence_point (id, discussion_id, description, camps, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (did, self.discussion_id, d_description,
                 _json.dumps(d_camps, ensure_ascii=False),
                 dp.get("created_at", now), dp.get("updated_at", now)),
            )
            await db.commit()
            await publish(self.discussion_id, "divergence_update", {
                "id": did, "description": d_description,
                "camps": d_camps,
                "created_at": dp.get("created_at", now),
                "updated_at": dp.get("updated_at", now),
            })

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

        # ── 总结用独立的 chat_completion，不经过 extractor._call_llm ──
        # extractor._call_llm 强制 response_format="json_object"，但总结需要纯文本
        from app.llm.client import chat_completion
        try:
            resp = await chat_completion(messages, temperature=0.5)
            content = resp["choices"][0]["message"]["content"]
            content = content.strip()
            # 兜底清洗：LLM 可能仍然包裹了 markdown
            content = content.removeprefix("```json").removeprefix("```").strip()
            content = content.removesuffix("```").strip()
            # 如果是纯 JSON 包裹的字符串，尝试解包
            if content.startswith("{") or content.startswith('"'):
                try:
                    data = _json.loads(content)
                    if isinstance(data, dict):
                        content = data.get("summary", data.get("content", content))
                    elif isinstance(data, str):
                        content = data
                except (_json.JSONDecodeError, TypeError):
                    pass
            return content if content else "感谢各位专家的精彩讨论。本次圆桌就相关话题进行了深入交流..."
        except Exception as e:
            print(
                f"[orchestrator] CRITICAL: _generate_summary failed!\n"
                f"  Error: {type(e).__name__}: {e}\n"
                f"  repr: {repr(e)}",
                flush=True,
            )
            import traceback as _tb3
            _tb3.print_exc()
            return "感谢各位专家的精彩讨论。本次圆桌就相关话题进行了深入交流，各方在多个层面达成共识，也存在值得继续探讨的分歧。期待下期再会。"

    async def _generate_summary_safe(
        self, db, topic: str, transcript: list[dict], panelists: list[dict],
    ) -> str:
        """100% 可靠的总结生成——无论 LLM 是否成功，始终返回自然语言文本。"""
        try:
            return await self._generate_summary(
                db, topic, transcript, set(), set(), panelists,
            )
        except Exception as e:
            print(f"[orchestrator] CRITICAL: _generate_summary_safe failed: {type(e).__name__}: {e}", flush=True)
            import traceback as _tbs
            _tbs.print_exc()
            return "感谢各位专家的精彩讨论。本次圆桌就相关话题进行了深入交流，各方在多个层面达成共识，也存在值得继续探讨的分歧。期待下期再会。"

    async def _emit_discussion_end_bulletproof(
        self, db, total_rounds: int, topic: str, panelists: list[dict],
    ) -> None:
        """终极安全网：无论如何都要把 discussion_end 发出去。

        先尝试正常生成总结 → 失败则用兜底文案。
        整个 publish + DB 更新包裹在独立 try-except 中，
        即使 silent_panelists 列表推导式炸了也不影响事件发送。
        """
        import traceback as _tb

        summary = "感谢各位专家的精彩讨论。本次圆桌就相关话题进行了深入交流，各方在多个层面达成共识，也存在值得继续探讨的分歧。期待下期再会。"
        silent_panelists: list[dict] = []

        # Step 1: 尝试正常生成总结（可能因 LLM 调用失败）
        try:
            transcript = await self._load_transcript(db)
            summary = await self._generate_summary_safe(
                db, topic, transcript, panelists,
            )
        except Exception as e:
            print(f"[orchestrator] CRITICAL: summary generation FAILED: {type(e).__name__}: {e}", flush=True)
            import traceback as _tbs2
            _tbs2.print_exc()

        # Step 2: 安全构建 silent_panelists（用 for 循环，绝不抛异常）
        try:
            final_transcript = await self._load_transcript(db)
            states = self._build_states(panelists, final_transcript)
            silent_panelists = []
            for s in states:
                try:
                    if s.get("silent_rounds", 0) >= 5:
                        silent_panelists.append({
                            "id": s.get("id", ""),
                            "name": s.get("name", "未知嘉宾"),
                        })
                except Exception:
                    # 单条记录构建失败不影响整体
                    continue
        except Exception as e:
            print(f"[orchestrator] CRITICAL: building silent_panelists failed: {type(e).__name__}: {e}", flush=True)
            import traceback as _tb2
            _tb2.print_exc()
            silent_panelists = []

        # Step 3: 发布 discussion_end（必须成功——这是前端浮层的触发器）
        try:
            await publish(self.discussion_id, "discussion_end", {
                "discussion_id": self.discussion_id,
                "summary": summary,
                "total_rounds": total_rounds,
                "silent_panelists": silent_panelists,
                "ended_at": _now(),
            })
        except Exception as e:
            print(f"[orchestrator] CRITICAL: publish discussion_end failed: {e}", flush=True)
            _tb.print_exc()
            # 最坏情况——连 publish 都失败了——尝试裸 publish
            try:
                await publish(self.discussion_id, "discussion_end", {
                    "discussion_id": self.discussion_id,
                    "summary": "本场圆桌讨论已结束。",
                    "total_rounds": total_rounds,
                    "silent_panelists": [],
                    "ended_at": _now(),
                })
            except Exception:
                print(f"[orchestrator] FATAL: even bare publish failed", flush=True)

        # Step 4: 更新 DB 状态为 ended（独立 try，不因 DB 错误影响前端通知）
        try:
            await db.execute(
                "UPDATE discussion SET status = 'ended', ended_at = ? WHERE id = ?",
                (_now(), self.discussion_id),
            )
            await db.commit()
        except Exception as e:
            print(f"[orchestrator] updating discussion status failed: {e}", flush=True)


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
