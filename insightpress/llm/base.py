"""Base abstractions for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class LLMResponse:
    """Structured response from LLM."""

    hook: str
    implication: str
    action: Optional[str]
    hashtags: list[str]
    final_post: str
    char_count: int

    def is_valid(self, max_chars: int, max_hashtags: int) -> tuple[bool, Optional[str]]:
        """
        Validate LLM response against rules.

        Returns:
            (is_valid, error_message)
        """
        # Check character limit
        if self.char_count > max_chars:
            return False, f"Exceeds {max_chars} char limit: {self.char_count}"

        # Check implication presence
        if not self.implication or len(self.implication.strip()) < 10:
            return False, "Missing or too short implication"

        # Check hashtag count
        if len(self.hashtags) > max_hashtags:
            return False, f"Too many hashtags: {len(self.hashtags)} > {max_hashtags}"

        # Check hashtags are lowercase
        for tag in self.hashtags:
            if tag != tag.lower():
                return False, f"Hashtag not lowercase: {tag}"

        return True, None


class LLMClient(Protocol):
    """Protocol for LLM provider implementations."""

    def generate_draft(
        self,
        title: str,
        url: str,
        source: str,
        published_at: str,
        summary: Optional[str],
        matched_topics: list[str],
        allowed_hashtags: list[str],
    ) -> Optional[LLMResponse]:
        """
        Generate a draft post from item metadata.

        Args:
            title: Item title
            url: Item URL
            source: Source name (e.g., "Hacker News")
            published_at: ISO timestamp
            summary: Optional short summary/snippet
            matched_topics: Topics matched from config
            allowed_hashtags: Whitelisted hashtags suggested

        Returns:
            LLMResponse if successful, None if failed
        """
        ...


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        timeout: int = 20,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def generate_draft(
        self,
        title: str,
        url: str,
        source: str,
        published_at: str,
        summary: Optional[str],
        matched_topics: list[str],
        allowed_hashtags: list[str],
    ) -> Optional[LLMResponse]:
        """Generate draft using provider-specific API."""
        pass

    @abstractmethod
    def _call_api(self, prompt: str) -> Optional[str]:
        """Call provider API and return raw response."""
        pass
