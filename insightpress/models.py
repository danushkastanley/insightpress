"""Data models for InsightPress."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """Represents a single news item from any source."""

    id: str
    title: str
    url: str
    source: str
    published_at: datetime
    summary: Optional[str] = None
    raw_score: Optional[float] = None
    canonical_url: Optional[str] = None

    def __post_init__(self):
        """Ensure published_at is a datetime object."""
        if isinstance(self.published_at, str):
            self.published_at = datetime.fromisoformat(self.published_at.replace('Z', '+00:00'))


@dataclass
class RankedItem:
    """A NewsItem with ranking information."""

    item: NewsItem
    score: float
    reasons: list[str] = field(default_factory=list)

    def __lt__(self, other):
        """Enable sorting by score (descending)."""
        return self.score > other.score


@dataclass
class Draft:
    """A draft X post."""

    content: str
    source_item: NewsItem
    hashtags: list[str] = field(default_factory=list)
    char_count: int = 0
    generation_mode: str = "template"  # template|llm:openai|llm:anthropic|llm:gemini

    def __post_init__(self):
        """Calculate character count."""
        self.char_count = len(self.content)


@dataclass
class DraftReport:
    """Complete report of generated drafts and candidates."""

    date: str
    timestamp: str
    top_drafts: list[Draft]
    other_candidates: list[RankedItem]
    skipped_items: list[tuple[str, str]]  # (title, reason)
    total_items_fetched: int
    total_duplicates_removed: int
