"""内容审核可插拔接口（T010）+ 本地轻量实现（T011）。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModerationResult:
    allowed: bool
    reason: str | None = None


class ContentModerator(ABC):
    @abstractmethod
    async def check_topic(self, topic: str) -> ModerationResult:
        """验证讨论话题文本。返回 ModerationResult。"""
        ...
