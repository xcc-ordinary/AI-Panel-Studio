"""T013: PanelistGenerator unit tests — mock DeepSeek API, test parsing/retry/diversity."""
import pytest
from unittest.mock import AsyncMock, patch


# 9 色后端调色板（与 frontend/src/utils/colors.ts + MASTER.md §1.2 完全一致）
PANELIST_COLORS = [
    "#38BDF8", "#F87171", "#818CF8", "#FBBF24",
    "#A78BFA", "#FB923C", "#E879F9", "#2DD4BF", "#FCA5A5",
]

# 模拟合法的 DeepSeek 返回
VALID_MOCK_RESPONSE = {
    "choices": [{
        "message": {
            "content": '''{
                "host": {"name": "张明远", "title": "科技媒体主编", "stance": "中立——引导多元观点对话"},
                "experts": [
                    {"name": "李开放", "title": "开源社区领袖", "stance": "强烈支持——技术创新的核心驱动力"},
                    {"name": "陈安全", "title": "网络安全专家", "stance": "谨慎支持——安全审计需建立标准"},
                    {"name": "王商业", "title": "AI企业CEO", "stance": "务实立场——核心保留工具链开源"},
                    {"name": "赵伦理", "title": "科技伦理学者", "stance": "需全球治理框架——开源不等于无监管"}
                ]
            }'''
        }
    }]
}

# 模拟立场雷同的返回（所有专家立场几乎一样 → 应触发重新生成）
LOW_DIVERSITY_MOCK_RESPONSE = {
    "choices": [{
        "message": {
            "content": '''{
                "host": {"name": "测试主持", "title": "主持人", "stance": "中立"},
                "experts": [
                    {"name": "专家A", "title": "研究员", "stance": "支持开源"},
                    {"name": "专家B", "title": "工程师", "stance": "支持开源"},
                    {"name": "专家C", "title": "教授", "stance": "支持开源"},
                    {"name": "专家D", "title": "顾问", "stance": "支持开源，很有价值"}
                ]
            }'''
        }
    }]
}

MALFORMED_JSON_RESPONSE = {
    "choices": [{
        "message": {
            "content": '这不是合法的JSON {broken'
        }
    }]
}

# ── Tests ───────────────────────────────────────────────────


class TestPanelistGeneratorParsing:
    """合法 JSON → 正确解析出 host + experts"""

    @pytest.mark.asyncio
    async def test_parses_valid_response_into_correct_count(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        gen._call_llm = AsyncMock(return_value=VALID_MOCK_RESPONSE)

        result = await gen.generate("AI是否应该开源？", expert_count=4)
        assert len(result) == 5  # 1 host + 4 experts
        host = [p for p in result if p["role"] == "host"]
        experts = [p for p in result if p["role"] == "expert"]
        assert len(host) == 1
        assert len(experts) == 4

    @pytest.mark.asyncio
    async def test_parses_all_required_fields(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        gen._call_llm = AsyncMock(return_value=VALID_MOCK_RESPONSE)

        result = await gen.generate("AI是否应该开源？", expert_count=4)
        for p in result:
            assert "id" in p, f"Missing id in {p}"
            assert "name" in p, f"Missing name in {p}"
            assert "title" in p, f"Missing title in {p}"
            assert "stance" in p, f"Missing stance in {p}"
            assert "color" in p, f"Missing color in {p}"
            assert "role" in p, f"Missing role in {p}"
            assert "sort_order" in p, f"Missing sort_order in {p}"

    @pytest.mark.asyncio
    async def test_assigns_colors_by_sort_order_from_preset_palette(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        gen._call_llm = AsyncMock(return_value=VALID_MOCK_RESPONSE)

        result = await gen.generate("AI是否应该开源？", expert_count=4)
        for p in result:
            expected_color = PANELIST_COLORS[p["sort_order"] % len(PANELIST_COLORS)]
            assert p["color"] == expected_color, \
                f"sort_order={p['sort_order']} expected {expected_color} got {p['color']}"

    @pytest.mark.asyncio
    async def test_host_always_sort_order_zero(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        gen._call_llm = AsyncMock(return_value=VALID_MOCK_RESPONSE)

        result = await gen.generate("AI是否应该开源？", expert_count=4)
        host = [p for p in result if p["role"] == "host"][0]
        assert host["sort_order"] == 0
        assert host["color"] == PANELIST_COLORS[0]


class TestPanelistGeneratorRetry:
    """畸形 JSON → 重试逻辑"""

    @pytest.mark.asyncio
    async def test_retries_on_malformed_json(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        # 前 2 次返回畸形 JSON，第 3 次返回合法
        gen._call_llm = AsyncMock(side_effect=[
            MALFORMED_JSON_RESPONSE,
            MALFORMED_JSON_RESPONSE,
            VALID_MOCK_RESPONSE,
        ])

        # 用 expert_count=4 匹配 VALID_MOCK_RESPONSE（含 4 位专家）
        result = await gen.generate("测试", expert_count=4)
        assert len(result) == 5  # 1 host + 4 experts
        assert gen._call_llm.call_count == 3

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        gen._call_llm = AsyncMock(return_value=MALFORMED_JSON_RESPONSE)

        with pytest.raises(Exception) as exc:
            await gen.generate("测试", expert_count=2)
        assert "生成" in str(exc.value) or "重试" in str(exc.value) or "retry" in str(exc.value).lower()


class TestPanelistGeneratorDiversity:
    """立场雷同 → 重新生成"""

    @pytest.mark.asyncio
    async def test_rejects_low_stance_diversity_and_regenerates(self):
        from app.services.panelist_generator import PanelistGenerator

        gen = PanelistGenerator()
        # 第一次返回雷同立场，第二次返回多样化立场
        gen._call_llm = AsyncMock(side_effect=[
            LOW_DIVERSITY_MOCK_RESPONSE,
            VALID_MOCK_RESPONSE,
        ])

        result = await gen.generate("测试", expert_count=4)
        # 最终应该用第二次的多样化结果
        assert len(result) == 5
        assert gen._call_llm.call_count >= 2
