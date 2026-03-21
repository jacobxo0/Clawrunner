"""Anthropic (Claude) AI provider."""

import structlog
from src.ai.provider import AIProvider
from src.config import get_settings

logger = structlog.get_logger()


class AnthropicProvider(AIProvider):
    """AI provider using Anthropic's Claude API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ai.anthropic_api_key
        self.model = settings.ai.model_anthropic
        self.max_retries = settings.ai.max_retries
        self.timeout = settings.ai.timeout_seconds

    async def complete(self, prompt: str, system: str = None, max_tokens: int = 1000) -> str:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            response = await client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error("anthropic_error", error=str(e))
            return ""
