"""Phase 4.3: ConsensusExtractor — 讨论过程中每 N 轮提炼共识与分歧。

与 SpeechScheduler 相同模式：_call_llm 可被测试 mock。
"""
import json
import re
import traceback
import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConsensusExtractor:
    """从 transcript 中提炼共识点和分歧点。"""

    async def _call_llm(self, messages: list[dict]) -> dict:
        from app.llm.client import chat_completion
        return await chat_completion(messages, temperature=0.3, response_format="json_object")

    async def extract(
        self,
        discussion_id: str,
        transcript: list[dict],
        panelists: list[dict],
        existing_consensus: list[dict],
        existing_divergence: list[dict],
    ) -> dict:
        """返回 {"consensus_points": [...], "divergence_points": [...]}。

        existing_consensus: [{"id": str, "content": str}, ...]
        existing_divergence: [{"id": str, "description": str, "camps": [...]}, ...]
        传入已有点的完整内容，让 LLM 能做语义级去重（而非仅靠 ID 比对）。
        """
        from app.llm.prompts import CONSENSUS_EXTRACTION_SYSTEM, CONSENSUS_EXTRACTION_USER

        # ── Format transcript ───────────────────────────
        transcript_text = self._format_transcript(transcript, panelists)

        # ── Format existing points with CONTENT for semantic dedup ──
        existing_consensus_text = self._format_existing_consensus(existing_consensus)
        existing_divergence_text = self._format_existing_divergence(existing_divergence)

        messages = [
            {"role": "system", "content": CONSENSUS_EXTRACTION_SYSTEM},
            {"role": "user", "content": CONSENSUS_EXTRACTION_USER.format(
                transcript=transcript_text,
                existing_consensus=existing_consensus_text,
                existing_divergence=existing_divergence_text,
            )},
        ]

        raw_content = ""
        try:
            resp = await self._call_llm(messages)
            raw_content = resp["choices"][0]["message"]["content"]

            # ── 强力清洗 Markdown 包裹 (正则，不区分大小写) ──
            cleaned = raw_content.strip()
            cleaned = re.sub(r'^```(?:json|JSON)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```\s*$', '', cleaned)
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            consensus_points = []
            for cp in data.get("consensus_points", []):
                # Always use UUID — id is PRIMARY KEY across all discussions
                cid = str(uuid.uuid4())
                consensus_points.append({
                    "id": cid,
                    "content": cp.get("content", ""),
                    "involved_panelist_ids": cp.get("involved_panelist_ids", []),
                    "created_at": _now(),
                    "updated_at": _now(),
                })

            divergence_points = []
            for dp in data.get("divergence_points", []):
                did = str(uuid.uuid4())
                camps = []
                for camp in dp.get("camps", []):
                    camps.append({
                        "position": camp.get("position", ""),
                        "panelist_ids": camp.get("panelist_ids", []),
                    })
                divergence_points.append({
                    "id": did,
                    "description": dp.get("description", ""),
                    "camps": camps,
                    "created_at": _now(),
                    "updated_at": _now(),
                })

            return {
                "consensus_points": consensus_points,
                "divergence_points": divergence_points,
            }

        except (json.JSONDecodeError, KeyError, Exception) as e:
            # Print full context for debugging — never silently swallow extraction failures
            print(
                f"[consensus_extractor] Extraction failed!\n"
                f"  Error: {type(e).__name__}: {e}\n"
                f"  Traceback:\n{traceback.format_exc()}\n"
                f"  Raw LLM response (first 500 chars): {raw_content[:500] if raw_content else '(empty)'}",
                flush=True,
            )
            return {"consensus_points": [], "divergence_points": []}

    def _format_existing_consensus(self, items: list[dict]) -> str:
        """将已有共识格式化为 LLM 可做语义比对的文本。"""
        if not items:
            return "暂无已有共识"
        lines = []
        for i, c in enumerate(items, 1):
            lines.append(f"{i}. {c.get('content', '')}")
        return "\n".join(lines)

    def _format_existing_divergence(self, items: list[dict]) -> str:
        """将已有分歧格式化为 LLM 可做语义比对的文本（含阵营详情）。"""
        if not items:
            return "暂无已有分歧"
        lines = []
        for i, d in enumerate(items, 1):
            desc = d.get("description", "")
            camps = d.get("camps", [])
            camp_texts = []
            for camp in camps:
                pos = camp.get("position", "")
                camp_texts.append(f"    - {pos}")
            camp_summary = "\n".join(camp_texts) if camp_texts else "    (无阵营详情)"
            lines.append(f"{i}. {desc}\n{camp_summary}")
        return "\n".join(lines)

    def _format_transcript(self, transcript: list[dict], panelists: list[dict]) -> str:
        if not transcript:
            return "（讨论尚未开始）"

        id_to_name = {p["id"]: p["name"] for p in panelists}
        lines = []
        for t in transcript[-20:]:  # Last 20 rounds
            name = id_to_name.get(t.get("speaker_id", ""), t.get("speaker_id", "?"))
            lines.append(f"[{name}] ({t.get('type', '?')}): {t.get('content', '')}")
        return "\n".join(lines)
