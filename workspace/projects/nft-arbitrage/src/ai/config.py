"""AI configuration and provider factory."""

from src.config import get_settings


def get_ai_provider():
    """Get the configured AI provider instance."""
    settings = get_settings()
    provider = settings.ai.primary_provider

    if provider == "anthropic" and settings.ai.anthropic_api_key:
        from src.ai.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    elif provider == "openai" and settings.ai.openai_api_key:
        from src.ai.openai_provider import OpenAIProvider
        return OpenAIProvider()

    # Try fallback
    fallback = settings.ai.fallback_provider
    if fallback == "openai" and settings.ai.openai_api_key:
        from src.ai.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif fallback == "anthropic" and settings.ai.anthropic_api_key:
        from src.ai.anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    return None
