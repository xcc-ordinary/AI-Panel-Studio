"""T048: SpeechScheduler——组装调度prompt→调LLM→解析→兜底→max_rounds检查。"""
import json

SILENT_THRESHOLD = 5  # 连续 N 轮未发言标记 silent
HOST_ID_MARKER = "host"  # 主持人 id 包含此标记


class SpeechScheduler:
    """默认通过 _call_llm 调 DeepSeek；测试时 mock 替换。"""

    async def _call_llm(self, messages: list[dict]) -> dict:
        from app.llm.client import chat_completion
        return await chat_completion(messages, temperature=0.6, response_format="json_object")

    async def decide_next_speaker(
        self,
        discussion_id: str,
        transcript: list[dict],
        panelist_states: list[dict],
        current_round: int,
        max_rounds: int,
    ) -> dict:
        """返回 {speaker_id, type, content} 或 max_rounds 时返回 summary。"""

        # ── max_rounds 兜底 ──────────────────────
        if current_round >= max_rounds:
            host = self._find_host(panelist_states)
            return {
                "speaker_id": host["id"] if host else panelist_states[0]["id"],
                "type": "summary",
                "content": "感谢各位专家的精彩讨论。今天的圆桌到此结束，我们下期再见。",
            }

        # ── 首轮 → host opening ──────────────────
        if len(transcript) == 0:
            host = self._find_host(panelist_states) or panelist_states[0]
            return {
                "speaker_id": host["id"],
                "type": "opening",
                "content": self._build_opening(panelist_states),
            }

        # ── 组装 prompt → 调 LLM ─────────────────
        from app.llm.prompts import SPEECH_SCHEDULING_SYSTEM, SPEECH_SCHEDULING_USER

        transcript_text = self._format_transcript(transcript)
        states_text = self._format_states(panelist_states)

        messages = [
            {"role": "system", "content": SPEECH_SCHEDULING_SYSTEM},
            {"role": "user", "content": SPEECH_SCHEDULING_USER.format(
                transcript=transcript_text, panelist_states=states_text,
            )},
        ]

        try:
            resp = await self._call_llm(messages)
            content = resp["choices"][0]["message"]["content"]
            data = json.loads(content)

            speaker_id = data.get("next_speaker")
            utterance_type = data.get("type", "statement")

            # ── 无人应答兜底 ──────────────────
            if not speaker_id or utterance_type == "none":
                host = self._find_host(panelist_states)
                return {
                    "speaker_id": host["id"] if host else panelist_states[0]["id"],
                    "type": "question",
                    "content": self._build_fallback_question(panelist_states, transcript),
                }

            return {
                "speaker_id": speaker_id,
                "type": utterance_type,
                "content": data.get("content", ""),
            }

        except (json.JSONDecodeError, KeyError):
            # LLM 返回异常 → host 推进讨论
            host = self._find_host(panelist_states)
            return {
                "speaker_id": host["id"] if host else panelist_states[0]["id"],
                "type": "bridge",
                "content": "感谢刚才的发言。让我们继续讨论。还有其他专家想补充吗？",
            }

    # ── 格式化辅助 ──────────────────────────────────────

    def _format_transcript(self, transcript: list[dict]) -> str:
        if not transcript:
            return "（讨论尚未开始）"
        lines = []
        for t in transcript[-10:]:  # 最近 10 轮
            speaker = t.get("speaker_id", "?")
            lines.append(f"[{speaker}] ({t.get('type', '?')}): {t.get('content', '')}")
        return "\n".join(lines)

    def _format_states(self, states: list[dict]) -> str:
        lines = []
        for s in states:
            silent = s.get("silent_rounds", 0)
            tag = f" [沉默{silent}轮]" if silent >= SILENT_THRESHOLD else ""
            lines.append(f"- {s['id']} ({s['role']}): {s.get('stance','')}{tag}")
        return "\n".join(lines)

    def _find_host(self, panelist_states: list[dict]) -> dict | None:
        for p in panelist_states:
            if p.get("role") == "host" or HOST_ID_MARKER in p.get("id", ""):
                return p
        return None

    def _build_opening(self, states: list[dict]) -> str:
        experts = [s for s in states if s.get("role") != "host"]
        names = "、".join([e["name"] for e in experts[:4]])
        return f"欢迎各位来到今天的圆桌讨论。今天我们有{len(experts)}位来自不同领域的专家——{names}——共同探讨这个话题。让我们开始吧！"

    def _build_fallback_question(self, states: list[dict], transcript: list[dict]) -> str:
        experts = [s for s in states if s.get("role") != "host" and s.get("silent_rounds", 0) < SILENT_THRESHOLD]
        if experts:
            return f"{experts[0]['name']}，您对这个话题有什么看法？"
        return "各位专家，还有什么想要补充的吗？"
