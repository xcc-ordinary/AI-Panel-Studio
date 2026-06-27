"""Phase 4.3: ConsensusExtractor — 讨论过程中每 N 轮提炼共识与分歧。

与 SpeechScheduler 相同模式：_call_llm 可被测试 mock。
"""
import json
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
        existing_consensus_ids: set[str],
        existing_divergence_ids: set[str],
    ) -> dict:
        """返回 {"consensus_points": [...], "divergence_points": [...]}。

        每个 point 含 id/content/involved_panelist_ids（consensus）或
        id/description/camps（divergence），已 ready for DB + SSE publish。
        """
        from app.llm.prompts import CONSENSUS_EXTRACTION_SYSTEM, CONSENSUS_EXTRACTION_USER

        # ── Format transcript ───────────────────────────
        transcript_text = self._format_transcript(transcript, panelists)

        # ── Format existing points ──────────────────────
        existing_text = ""
        if existing_consensus_ids or existing_divergence_ids:
            existing_text = f"\n已有的共识ID（不要重复生成）：{', '.join(sorted(existing_consensus_ids))}\n已有的分歧ID（不要重复生成）：{', '.join(sorted(existing_divergence_ids))}\n"

        messages = [
            {"role": "system", "content": CONSENSUS_EXTRACTION_SYSTEM},
            {"role": "user", "content": CONSENSUS_EXTRACTION_USER.format(
                transcript=transcript_text,
                existing=existing_text,
            )},
        ]

        try:
            resp = await self._call_llm(messages)
            content = resp["choices"][0]["message"]["content"]
            data = json.loads(content)

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
            print(f"[consensus_extractor] Extraction failed: {e}", flush=True)
            return {"consensus_points": [], "divergence_points": []}

    def _format_transcript(self, transcript: list[dict], panelists: list[dict]) -> str:
        if not transcript:
            return "（讨论尚未开始）"

        id_to_name = {p["id"]: p["name"] for p in panelists}
        lines = []
        for t in transcript[-20:]:  # Last 20 rounds
            name = id_to_name.get(t.get("speaker_id", ""), t.get("speaker_id", "?"))
            lines.append(f"[{name}] ({t.get('type', '?')}): {t.get('content', '')}")
        return "\n".join(lines)
