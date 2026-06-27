"""T011: 本地内容审核——关键词拦截 + 长度校验。MVP 默认实现，预留第三方对接位。"""
from app.services.content_moderator import ContentModerator, ModerationResult

BLOCKED_KEYWORDS = [
    "违禁品", "赌博", "色情", "诈骗",
]


class LocalContentModerator(ContentModerator):
    def __init__(self, max_length: int = 200):
        self._max_length = max_length

    async def check_topic(self, topic: str) -> ModerationResult:
        stripped = topic.strip()

        if not stripped:
            return ModerationResult(allowed=False, reason="话题不能为空")

        if len(stripped) > self._max_length:
            return ModerationResult(allowed=False, reason=f"话题长度不能超过{self._max_length}字符")

        for kw in BLOCKED_KEYWORDS:
            if kw in stripped:
                return ModerationResult(allowed=False, reason="话题包含不当内容，请修改后重试")

        return ModerationResult(allowed=True)
