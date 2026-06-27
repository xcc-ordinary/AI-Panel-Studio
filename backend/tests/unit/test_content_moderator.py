"""T014: ContentModerator unit tests — keyword/length checks."""
import pytest


@pytest.mark.asyncio
async def test_rejects_empty_topic():
    from app.services.local_moderator import LocalContentModerator

    mod = LocalContentModerator()
    result = await mod.check_topic("")
    assert result.allowed is False


@pytest.mark.asyncio
async def test_rejects_whitespace_only_topic():
    from app.services.local_moderator import LocalContentModerator

    mod = LocalContentModerator()
    result = await mod.check_topic("   ")
    assert result.allowed is False


@pytest.mark.asyncio
async def test_rejects_too_long_topic():
    from app.services.local_moderator import LocalContentModerator

    mod = LocalContentModerator()
    result = await mod.check_topic("A" * 201)
    assert result.allowed is False


@pytest.mark.asyncio
async def test_rejects_blocked_keyword():
    from app.services.local_moderator import LocalContentModerator

    mod = LocalContentModerator()
    result = await mod.check_topic("违禁品交易指南")
    assert result.allowed is False
    assert result.reason is not None


@pytest.mark.asyncio
async def test_accepts_valid_topic():
    from app.services.local_moderator import LocalContentModerator

    mod = LocalContentModerator()
    result = await mod.check_topic("AI是否应该开源？")
    assert result.allowed is True


@pytest.mark.asyncio
async def test_accepts_boundary_length():
    from app.services.local_moderator import LocalContentModerator

    mod = LocalContentModerator()
    result = await mod.check_topic("A" * 200)
    assert result.allowed is True
