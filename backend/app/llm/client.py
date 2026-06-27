"""T019: DeepSeek LLM async 客户端——httpx 调用 chat/completions。"""
import httpx
from app.config import settings


async def chat_completion(
    messages: list[dict],
    temperature: float = 0.8,
    response_format: str | None = None,
) -> dict:
    """调用 DeepSeek Chat API，返回完整响应 dict。"""
    body: dict = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format == "json_object":
        body["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.deepseek_base_url}/v1/chat/completions",
            json=body,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()
