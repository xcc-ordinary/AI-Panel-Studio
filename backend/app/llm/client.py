"""T019: DeepSeek LLM async 客户端——httpx 调用 chat/completions。"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger("llm.client")

# DeepSeek API 支持的惩罚参数默认值。
# - presence_penalty: 正值鼓励谈论新话题（抑制已出现过的内容）
# - frequency_penalty: 正值抑制逐字重复（降低高频词的采样概率）
DEFAULT_PRESENCE_PENALTY = 0.0
DEFAULT_FREQUENCY_PENALTY = 0.0


async def chat_completion(
    messages: list[dict],
    temperature: float = 0.8,
    response_format: str | None = None,
    presence_penalty: float = DEFAULT_PRESENCE_PENALTY,
    frequency_penalty: float = DEFAULT_FREQUENCY_PENALTY,
) -> dict:
    """调用 DeepSeek Chat API，返回完整响应 dict。

    惩罚参数说明：
    - presence_penalty [-2.0, 2.0]: 正值=鼓励谈新话题，负值=允许重复主题
    - frequency_penalty [-2.0, 2.0]: 正值=抑制字词逐字重复，负值=允许高频复用
    两者配合使用可有效抑制"复读机"现象。
    """
    body: dict = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
    }

    # 仅当调用方显式传入非零惩罚值时加入请求体（避免向不支持的服务端发送多余字段）
    if presence_penalty != 0.0:
        body["presence_penalty"] = presence_penalty
    if frequency_penalty != 0.0:
        body["frequency_penalty"] = frequency_penalty

    if response_format == "json_object":
        body["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=90.0)) as client:
        try:
            resp = await client.post(
                f"{settings.deepseek_base_url}/v1/chat/completions",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

        except httpx.HTTPStatusError as e:
            # 400 且响应中提到不支持 penalty 参数 → 安全降级重试
            if e.response.status_code == 400 and any(
                keyword in (e.response.text or "").lower()
                for keyword in ("penalty", "presence", "frequency")
            ):
                logger.warning(
                    "DeepSeek API 不支持 presence_penalty / frequency_penalty，"
                    "降级为不带惩罚参数重试"
                )
                body.pop("presence_penalty", None)
                body.pop("frequency_penalty", None)
                resp = await client.post(
                    f"{settings.deepseek_base_url}/v1/chat/completions",
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
            raise
