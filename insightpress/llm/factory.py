"""Factory for creating LLM clients."""

import logging
from typing import Optional

from .anthropic_client import AnthropicClient
from .base import LLMClient
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


def get_llm_client(
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    temperature: float = 0.2,
    timeout: int = 20,
    max_retries: int = 2,
) -> Optional[LLMClient]:
    """
    Create LLM client for specified provider.

    Args:
        provider: Provider name (openai|anthropic|gemini|none)
        api_key: API key for provider
        model: Model name (provider-specific)
        temperature: Sampling temperature (default 0.2)
        timeout: Request timeout in seconds (default 20)
        max_retries: Max retry attempts (default 2)

    Returns:
        LLMClient instance or None if provider is 'none' or key is missing
    """
    provider = provider.lower().strip()

    # Handle 'none' explicitly
    if provider == "none" or not provider:
        logger.info("LLM provider set to 'none' - using template-based drafting")
        return None

    # Check for missing API key
    if not api_key:
        logger.warning(
            f"LLM provider '{provider}' selected but API key missing - falling back to template drafting"
        )
        return None

    # Set default models if not specified
    if not model:
        model = _get_default_model(provider)
        logger.info(f"Using default model for {provider}: {model}")

    # Create client based on provider
    try:
        if provider == "openai":
            return OpenAIClient(
                api_key=api_key,
                model=model,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )
        elif provider == "anthropic":
            return AnthropicClient(
                api_key=api_key,
                model=model,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )
        elif provider == "gemini":
            return GeminiClient(
                api_key=api_key,
                model=model,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )
        else:
            logger.warning(f"Unknown LLM provider '{provider}' - falling back to template drafting")
            return None

    except Exception as e:
        logger.error(f"Failed to create LLM client for {provider}: {e}")
        return None


def _get_default_model(provider: str) -> str:
    """Get default model for provider."""
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "gemini": "gemini-2.0-flash-exp",
    }
    return defaults.get(provider, "")
