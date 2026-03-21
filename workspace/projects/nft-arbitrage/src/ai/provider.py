"""Abstract AI provider interface."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for AI providers (Anthropic, OpenAI)."""

    @abstractmethod
    async def complete(self, prompt: str, system: str = None, max_tokens: int = 1000) -> str:
        """Generate a completion from the AI model."""
        pass
