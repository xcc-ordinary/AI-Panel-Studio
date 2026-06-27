"""T018: PanelistGenerator — 组装 prompt → 调 LLM → 解析 JSON → 校验多样性 → 分配颜色。"""
import json
import uuid

# 与 frontend/src/utils/colors.ts + MASTER.md §1.2 完全一致的 9 色调色板
PANELIST_COLORS = [
    "#38BDF8",  # 0: 天空蓝 — 主持人
    "#F87171",  # 1: 珊瑚红
    "#818CF8",  # 2: 靛蓝
    "#FBBF24",  # 3: 琥珀金
    "#A78BFA",  # 4: 紫罗兰
    "#FB923C",  # 5: 活力橙
    "#E879F9",  # 6: 品红
    "#2DD4BF",  # 7: 青碧绿
    "#FCA5A5",  # 8: 浅珊瑚
]

MAX_RETRIES = 3


class PanelistGenerationError(Exception):
    """嘉宾生成失败（重试耗尽或校验不通过）。"""
    pass


class PanelistGenerator:
    """默认使用 DeepSeek LLM；测试时可通过 _call_llm mock 替换。"""

    async def _call_llm(self, messages: list[dict], temperature: float = 0.8) -> dict:
        from app.llm.client import chat_completion
        return await chat_completion(messages, temperature=temperature, response_format="json_object")

    async def generate(self, topic: str, expert_count: int) -> list[dict]:
        """返回 panelist dict 列表：[{id, role, name, title, stance, color, sort_order, ...}]"""
        from app.llm.prompts import PANELIST_GENERATION_SYSTEM, PANELIST_GENERATION_USER

        messages = [
            {"role": "system", "content": PANELIST_GENERATION_SYSTEM},
            {"role": "user", "content": PANELIST_GENERATION_USER.format(topic=topic, expert_count=expert_count)},
        ]

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await self._call_llm(messages, temperature=0.8)
                content = resp["choices"][0]["message"]["content"]
                data = json.loads(content)

                # 校验基本结构
                host = data["host"]
                experts = data["experts"]
                if not isinstance(experts, list) or len(experts) != expert_count:
                    raise ValueError(f"Expected {expert_count} experts, got {len(experts)}")

                # 校验多样性
                stances = [e["stance"] for e in experts] + [host.get("stance", "")]
                if not self._check_diversity(stances):
                    raise ValueError("Stance diversity too low")

                # 组装返回
                panelists = []
                panelists.append(self._build_panelist(host, role="host", sort_order=0))

                for i, expert in enumerate(experts):
                    panelists.append(self._build_panelist(expert, role="expert", sort_order=i + 1))

                return panelists

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                last_error = e
                continue

        raise PanelistGenerationError(f"嘉宾生成失败（已重试{MAX_RETRIES}次）: {last_error}")

    def _build_panelist(self, raw: dict, role: str, sort_order: int) -> dict:
        return {
            "id": f"gen-{uuid.uuid4().hex[:8]}",
            "role": role,
            "name": raw["name"],
            "title": raw["title"],
            "stance": raw["stance"],
            "color": PANELIST_COLORS[sort_order % len(PANELIST_COLORS)],
            "sort_order": sort_order,
        }

    @staticmethod
    def _check_diversity(stances: list[str]) -> bool:
        """简单多样性检查：去掉标点后做 Jaccard 相似度，任一对超过阈值则拒绝。"""
        import re

        def _tokenize(s: str) -> set[str]:
            return set(re.findall(r"[一-鿿\w]+", s.lower()))

        tokens_list = [_tokenize(s) for s in stances]
        for i in range(len(tokens_list)):
            for j in range(i + 1, len(tokens_list)):
                a, b = tokens_list[i], tokens_list[j]
                if not a or not b:
                    continue
                intersection = len(a & b)
                union = len(a | b)
                if union == 0:
                    continue
                if intersection / union > 0.6:  # >60% 词重叠 → 太相似
                    return False
        return True
