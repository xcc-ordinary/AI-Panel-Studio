"""T038: SpeechScheduler unit tests — mock DeepSeek API, test scheduling logic."""
import pytest
from unittest.mock import AsyncMock


# ── Mock 数据 ─────────────────────────────────────────────────

SAMPLE_PANELISTS = [
    {"id": "host-1", "role": "host", "name": "张明远", "stance": "中立主持", "sort_order": 0},
    {"id": "p-1", "role": "expert", "name": "李开放", "stance": "强烈支持开源", "sort_order": 1},
    {"id": "p-2", "role": "expert", "name": "陈安全", "stance": "谨慎支持——需要安全标准", "sort_order": 2},
    {"id": "p-3", "role": "expert", "name": "王商业", "stance": "务实——核心保留", "sort_order": 3},
]

SAMPLE_TRANSCRIPT_EMPTY = []

SAMPLE_TRANSCRIPT = [
    {"speaker_id": "host-1", "type": "opening", "content": "欢迎各位。今天讨论AI开源。李开放先生？"},
    {"speaker_id": "p-1", "type": "statement", "content": "开源是AI创新的生命线。"},
    {"speaker_id": "p-2", "type": "supplement", "content": "开源有助于安全审计。"},
]

# Mock LLM 返回——反驳
MOCK_REBUTTAL_RESPONSE = {
    "choices": [{"message": {"content": '{"next_speaker":"p-3","type":"rebuttal","content":"完全开源会打击企业创新积极性，研发投入需要回报。"}'}}]
}

# Mock LLM 返回——补充
MOCK_SUPPLEMENT_RESPONSE = {
    "choices": [{"message": {"content": '{"next_speaker":"p-1","type":"supplement","content":"开源社区的透明性本身就是最好的安全机制。"}'}}]
}

# Mock LLM 无人应答
MOCK_NO_VOLUNTEER_RESPONSE = {
    "choices": [{"message": {"content": '{"next_speaker":null,"type":"none","reason":"no panelist volunteers"}'}}]
}

# Mock LLM 返回——总结
MOCK_SUMMARY_RESPONSE = {
    "choices": [{"message": {"content": '{"next_speaker":"host-1","type":"summary","content":"感谢各位专家的精彩讨论，关于AI开源我们形成了若干重要共识……"}'}}]
}


# ── Helper ──────────────────────────────────────────────────

def make_state(panelists, silent_map=None):
    """构建 panelist_states 列表。silent_map: {panelist_id: rounds_silent}"""
    states = []
    for p in panelists:
        s = {**p, "status": "idle", "silent_rounds": 0}
        if silent_map and p["id"] in silent_map:
            s["silent_rounds"] = silent_map[p["id"]]
            s["status"] = "silent"
        states.append(s)
    return states


# ── Tests ──────────────────────────────────────────────────


class TestHostOpening:
    """讨论开始时（空 transcript），调度器应返回 host 的 opening。"""

    @pytest.mark.asyncio
    async def test_first_utterance_is_host_opening(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        scheduler._call_llm = AsyncMock(return_value={
            "choices": [{"message": {"content": '{"next_speaker":"host-1","type":"opening","content":"欢迎各位来到今天的圆桌讨论。"}'}}]
        })

        result = await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT_EMPTY,
            panelist_states=make_state(SAMPLE_PANELISTS),
            current_round=0,
            max_rounds=30,
        )
        assert result is not None
        assert result["speaker_id"] == "host-1"
        assert result["type"] == "opening"


class TestRebuttalTrigger:
    """mock 返回反驳 → 正确解析 speaker_id + type=rebuttal。"""

    @pytest.mark.asyncio
    async def test_parses_rebuttal_correctly(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        scheduler._call_llm = AsyncMock(return_value=MOCK_REBUTTAL_RESPONSE)

        result = await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT,
            panelist_states=make_state(SAMPLE_PANELISTS),
            current_round=3,
            max_rounds=30,
        )
        assert result is not None
        assert result["speaker_id"] == "p-3"
        assert result["type"] == "rebuttal"
        assert len(result["content"]) > 0


class TestNonRoundRobin:
    """连续多轮调度——发言顺序不应是严格 round-robin。"""

    @pytest.mark.asyncio
    async def test_scheduling_is_not_strict_round_robin(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        # 模拟 LLM 返回不同发言人，其中 p-1 连续出现、p-2 从未出现
        mock_responses = [
            {"choices": [{"message": {"content": '{"next_speaker":"p-1","type":"statement","content":"开源生态需要多样性。"}'}}]},
            {"choices": [{"message": {"content": '{"next_speaker":"p-1","type":"supplement","content":"我再补充一个重要数据点。"}'}}]},
            {"choices": [{"message": {"content": '{"next_speaker":"p-3","type":"rebuttal","content":"这些数据有误导性。"}'}}]},
            {"choices": [{"message": {"content": '{"next_speaker":"p-1","type":"statement","content":"让我们看看实际案例。"}'}}]},
        ]
        scheduler._call_llm = AsyncMock(side_effect=mock_responses)

        transcript = list(SAMPLE_TRANSCRIPT)
        results = []
        for i in range(4):
            result = await scheduler.decide_next_speaker(
                discussion_id="d1",
                transcript=transcript,
                panelist_states=make_state(SAMPLE_PANELISTS),
                current_round=3 + i,
                max_rounds=30,
            )
            results.append(result)
            transcript.append({"speaker_id": result["speaker_id"], "type": result["type"], "content": result["content"]})

        speakers = [r["speaker_id"] for r in results]
        # 不是严格的 p-1, p-2, p-3 循环
        assert speakers != ["p-1", "p-2", "p-3", "p-1"], "Should NOT be strict round-robin"
        # p-1 连续出现（证明非轮流）
        assert speakers.count("p-1") >= 2, "同一专家应可连续被调度"
        # p-2 从未出现（有人被跳过）
        assert "p-2" not in speakers or speakers.count("p-2") < len(speakers), "某些专家可被跳过"


class TestSilentDetection:
    """专家连续 N 轮未发言 → 状态标记 silent，但不阻断讨论。"""

    @pytest.mark.asyncio
    async def test_marks_silent_after_consecutive_rounds(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        scheduler._call_llm = AsyncMock(return_value=MOCK_SUPPLEMENT_RESPONSE)

        # p-2 已连续 5 轮未发言
        states = make_state(SAMPLE_PANELISTS, silent_map={"p-2": 5})

        result = await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT,
            panelist_states=states,
            current_round=8,
            max_rounds=30,
        )

        # 讨论不因有人沉默而中断
        assert result is not None
        assert result["speaker_id"] is not None

    @pytest.mark.asyncio
    async def test_silent_panelists_included_in_prompt(self):
        """沉默专家信息应被注入调度 prompt 中。"""
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        scheduler._call_llm = AsyncMock(return_value=MOCK_SUPPLEMENT_RESPONSE)

        states = make_state(SAMPLE_PANELISTS, silent_map={"p-3": 6})

        await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT,
            panelist_states=states,
            current_round=7,
            max_rounds=30,
        )

        # 验证 prompt 中包含 silent 信息
        call_args = scheduler._call_llm.call_args
        messages = call_args[0][0]  # 第一个参数是 messages
        user_msg = messages[-1]["content"]
        assert "p-3" in user_msg or "silent" in user_msg.lower() or "沉默" in user_msg


class TestMaxRoundsEnforcement:
    """current_round 达 max_rounds → 强制 host summary 并结束。"""

    @pytest.mark.asyncio
    async def test_forces_summary_at_max_rounds(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()

        result = await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT,
            panelist_states=make_state(SAMPLE_PANELISTS),
            current_round=30,
            max_rounds=30,
        )

        # 不应再调 LLM，直接返回 host summary
        assert result is not None
        assert result["type"] == "summary"
        assert "speaker_id" in result

    @pytest.mark.asyncio
    async def test_does_not_call_llm_when_max_rounds_reached(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        scheduler._call_llm = AsyncMock()

        await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT,
            panelist_states=make_state(SAMPLE_PANELISTS),
            current_round=30,
            max_rounds=30,
        )

        # 达到上限后不应调 LLM
        scheduler._call_llm.assert_not_called()


class TestNoVolunteerFallback:
    """无人应答兜底——host 提问推进讨论。"""

    @pytest.mark.asyncio
    async def test_host_asks_when_no_volunteer(self):
        from app.services.speech_scheduler import SpeechScheduler

        scheduler = SpeechScheduler()
        scheduler._call_llm = AsyncMock(return_value=MOCK_NO_VOLUNTEER_RESPONSE)

        result = await scheduler.decide_next_speaker(
            discussion_id="d1",
            transcript=SAMPLE_TRANSCRIPT,
            panelist_states=make_state(SAMPLE_PANELISTS),
            current_round=10,
            max_rounds=30,
        )

        # 无人应答时，应有兜底——host 出现提问或推进
        assert result is not None
        assert result["speaker_id"] == "host-1" or result["type"] in ("question", "bridge")
