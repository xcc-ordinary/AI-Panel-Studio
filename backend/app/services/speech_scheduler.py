"""T048: SpeechScheduler——组装调度prompt→调LLM→解析→兜底→max_rounds检查。"""
import json
import logging
import random
import re

logger = logging.getLogger("speech_scheduler")

SILENT_THRESHOLD = 5  # 连续 N 轮未发言标记 silent
HOST_ID_MARKER = "host"  # 主持人 id 包含此标记


class SpeechScheduler:
    """默认通过 _call_llm 调 DeepSeek；测试时 mock 替换。"""

    async def _call_llm(self, messages: list[dict]) -> dict:
        from app.llm.client import chat_completion
        return await chat_completion(
            messages,
            temperature=0.7,
            response_format="json_object",
            presence_penalty=0.6,
            frequency_penalty=0.6,
        )

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
            raw_content = resp["choices"][0]["message"]["content"]

            # ── 强力清洗 Markdown 包裹 (LLM 经常给 JSON 套 ```json ... ```) ──
            content = self._strip_markdown_fences(raw_content)
            data = json.loads(content)

            speaker_id = data.get("next_speaker")
            utterance_type = data.get("type", "statement")

            # ── 身份校验: LLM 返回的 speaker_id 必须在 panelist_states 中 ──
            valid_ids = {s["id"] for s in panelist_states}
            if speaker_id and speaker_id not in valid_ids:
                # LLM 幻觉——捏造了不存在的 speaker_id，fallback 到 host
                host = self._find_host(panelist_states)
                return {
                    "speaker_id": host["id"] if host else panelist_states[0]["id"],
                    "type": "bridge",
                    "content": "感谢刚才的发言。让我们换个角度继续讨论。",
                }

            # ── 角色越权拦截：专家不能提问、不能点名 ──
            speaker_role = self._get_role(speaker_id, panelist_states) if speaker_id else None
            if speaker_role == "expert" and utterance_type in ("question", "bridge", "summary"):
                # 专家越权——改由 host 接管
                host = self._find_host(panelist_states)
                return {
                    "speaker_id": host["id"] if host else panelist_states[0]["id"],
                    "type": "question",
                    "content": self._build_fallback_question(panelist_states, transcript),
                }

            # ── 自我称呼检测：content 中不能出现 speaker 自己的名字 ──
            utterance_content = data.get("content", "")
            if speaker_id and utterance_content:
                speaker_name = self._get_name(speaker_id, panelist_states)
                if speaker_name and speaker_name in utterance_content:
                    # LLM 产生了"自我采访"——用兜底 host 发言替代
                    host = self._find_host(panelist_states)
                    return {
                        "speaker_id": host["id"] if host else panelist_states[0]["id"],
                        "type": "bridge",
                        "content": "感谢刚才的发言。让我们继续深入讨论。",
                    }

            # ── 剥夺 LLM 提前结束权：不到 max_rounds 绝不收尾 ──
            # LLM 经常 3-4 轮就急于 summary，此处由代码绝对控场。
            # 只有 current_round >= max_rounds 时（入口处已处理），summary 才能生效。
            if utterance_type == "summary" and current_round < max_rounds:
                host = self._find_host(panelist_states)
                expert = self._pick_quietest_expert(panelist_states, transcript)
                return {
                    "speaker_id": host["id"] if host else panelist_states[0]["id"],
                    "type": "question",
                    "content": (
                        "刚才的讨论很精彩，但我们还不能这么早下结论。"
                        + self._build_sharp_question(panelist_states, transcript, expert)
                    ),
                }

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

        except json.JSONDecodeError as e:
            logger.error(
                f"[speech_scheduler] JSONDecodeError: {e}\n"
                f"  Raw response (first 500 chars): {raw_content[:500]}\n"
                f"  After stripping: {content[:500] if 'content' in dir() else '(strip failed)'}"
            )
            host = self._find_host(panelist_states)
            return {
                "speaker_id": host["id"] if host else panelist_states[0]["id"],
                "type": "bridge",
                "content": self._random_bridge(),
            }
        except KeyError as e:
            logger.error(
                f"[speech_scheduler] KeyError: {e} — LLM JSON missing required field\n"
                f"  Parsed data keys: {list(data.keys()) if 'data' in dir() else 'N/A'}\n"
                f"  Raw response (first 300 chars): {raw_content[:300]}"
            )
            host = self._find_host(panelist_states)
            return {
                "speaker_id": host["id"] if host else panelist_states[0]["id"],
                "type": "bridge",
                "content": self._random_bridge(),
            }

    # ── JSON 清洗 ────────────────────────────────────────

    @staticmethod
    def _strip_markdown_fences(raw: str) -> str:
        """强力剥离 LLM 返回内容外的 Markdown 代码块包裹。

        覆盖以下所有情况：
        - ```json\\n{...}\\n```
        - ```JSON\\n{...}\\n```
        - ```\\n{...}\\n```
        - ```json\\n{...}\\n```\\n一些废话
        - 多层嵌套 fence（极少见但防御）
        """
        text = raw.strip()
        # 1. 去掉开头 ```json / ```JSON / ```（不区分大小写）及其后空白
        text = re.sub(r'^```(?:json|JSON)?\s*', '', text)
        # 2. 找到 JSON 对象的结束位置（最后一个 } 或 ]），截断其后的所有内容
        #    这比只去掉尾部 ``` 更强——LLM 常会在 ``` 后加 "Hope this helps!" 等废话
        last_brace = max(text.rfind('}'), text.rfind(']'))
        if last_brace > 0:
            text = text[:last_brace + 1]
        # 3. 再尝试去掉可能残留在末尾的 ```
        text = re.sub(r'\s*```\s*$', '', text)
        return text.strip()

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
        """格式化嘉宾阵容名单——用 [主持人]/[专家] 标签帮助 LLM 牢记谁是谁。

        silent_rounds 作为调度参考传入，但 SYSTEM prompt 已强制 LLM 不得在 content 中暴露此信息。
        """
        lines = []
        for s in states:
            role_label = "主持人" if s.get("role") == "host" else "专家"
            silent = s.get("silent_rounds", 0)
            tag = f" （已{silent}轮未发言，可考虑点名邀请）" if silent >= SILENT_THRESHOLD else ""
            lines.append(
                f"[{role_label}] id: {s['id']}, 姓名: {s.get('name','?')}, 立场: {s.get('stance','')}{tag}"
            )
        return "\n".join(lines)

    _BRIDGE_PHRASES = [
        "刚才的发言很有启发性。让我们继续深入这个话题。",
        "感谢分享。还有其他专家想补充不同的视角吗？",
        "讨论越来越有意思了。请继续。",
        "这个角度很好。各位对刚才的观点有什么回应吗？",
        "让我们换一个维度继续探讨。",
    ]

    @classmethod
    def _random_bridge(cls) -> str:
        """返回一条随机的主持人桥接语，避免兜底时每次都重复同一句话。"""
        return random.choice(cls._BRIDGE_PHRASES)

    def _find_host(self, panelist_states: list[dict]) -> dict | None:
        for p in panelist_states:
            if p.get("role") == "host" or HOST_ID_MARKER in p.get("id", ""):
                return p
        return None

    def _get_role(self, panelist_id: str, states: list[dict]) -> str | None:
        """根据 panelist_id 查找角色（host/expert）。"""
        for s in states:
            if s["id"] == panelist_id:
                return s.get("role")
        return None

    def _get_name(self, panelist_id: str, states: list[dict]) -> str | None:
        """根据 panelist_id 查找姓名。"""
        for s in states:
            if s["id"] == panelist_id:
                return s.get("name")
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

    def _pick_quietest_expert(self, states: list[dict], transcript: list[dict]) -> dict | None:
        """选出发言轮次最少的专家（用于主持人有目标地追问）。"""
        experts = [s for s in states if s.get("role") != "host"]
        if not experts:
            return None
        # 统计每个专家在 transcript 中的出现次数
        counts = {e["id"]: 0 for e in experts}
        for t in transcript:
            sid = t.get("speaker_id", "")
            if sid in counts:
                counts[sid] += 1
        # 选出出现次数最少的
        quietest_id = min(counts, key=counts.get)  # type: ignore[arg-type]
        return next((e for e in experts if e["id"] == quietest_id), experts[0])

    def _build_sharp_question(
        self, states: list[dict], transcript: list[dict], target_expert: dict | None
    ) -> str:
        """生成尖锐追问——引导深入探讨而非泛泛而谈。

        优先向发言最少的专家提问，问题围绕 transcript 中最近出现的争议点。
        """
        # 提取最近的争议线索——发言类型为 rebuttal 的最后一条
        last_tension = ""
        for t in reversed(transcript):
            if t.get("type") in ("rebuttal", "supplement"):
                last_tension = t.get("content", "")
                break

        if target_expert:
            name = target_expert.get("name", "这位专家")
            if last_tension:
                return (
                    f"{name}老师，刚才有嘉宾提到" +
                    last_tension[:40] +
                    "，您怎么看这个具体问题？"
                )
            return f"{name}老师，您对这个问题是否有不同角度的思考？"

        # 没有特定目标时，抛出开放但尖锐的问题
        sharp_prompts = [
            "刚才有嘉宾提出了很有争议的观点，是否有人持不同意见？",
            "让我们把讨论再深入一层——各位觉得这个问题的底层矛盾到底是什么？",
            "在座有谁完全不同意刚才的观点？请大胆反驳。",
        ]
        return random.choice(sharp_prompts)
