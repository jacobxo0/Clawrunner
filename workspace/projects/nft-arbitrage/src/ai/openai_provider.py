"""OpenAI AI provider."""

import structlog
from src.ai.provider import AIProvider
from src.config import get_settings

logger = structlog.get_logger()


class OpenAIProvider(AIProvider):
    """AI provider using OpenAI's API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ai.openai_api_key
        self.model = settings.ai.model_openai
        self.max_retries = settings.ai.max_retries
        self.timeout = settings.ai.timeout_seconds

    async def complete(self, prompt: str, system: str = None, max_tokens: int = 1000) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("openai_error", error=str(e))
            return ""
