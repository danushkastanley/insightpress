"""Ranking algorithm for news items."""

import logging
from datetime import datetime, timezone, timedelta

from ..config import Config
from ..models import NewsItem, RankedItem

logger = logging.getLogger(__name__)


def rank_items(items: list[NewsItem], topics: list[str] | None = None) -> list[RankedItem]:
    """
    Rank news items based on multiple factors.

    Ranking factors:
    1. Recency - prefer items from last N hours
    2. Source weight - weight based on source
    3. Engagement - HN score or RSS weight
    4. Topic relevance - keyword matching

    Args:
        items: List of NewsItem objects
        topics: List of topics to match (uses config default if None)

    Returns:
        List of RankedItem objects sorted by score (descending)
    """
    topics = topics or Config.TOPICS
    topics_lower = [t.lower().strip() for t in topics]

    logger.info(f"Ranking {len(items)} items with topics: {topics_lower}")

    ranked = []
    now = datetime.now(timezone.utc)
    recency_cutoff = now - timedelta(hours=Config.RECENCY_HOURS)

    for item in items:
        score = 0.0
        reasons = []

        # Factor 1: Recency score (0.0 to 1.0)
        recency_score = calculate_recency_score(item.published_at, now, recency_cutoff)
        score += recency_score * 3.0  # Weight: 3x
        if recency_score > 0.7:
            reasons.append(f"Recent ({_format_age(item.published_at, now)})")

        # Factor 2: Source weight
        source_weight = get_source_weight(item.source)
        score += source_weight * 2.0  # Weight: 2x
        if source_weight > 0.8:
            reasons.append(f"Trusted source ({item.source})")

        # Factor 3: Engagement/raw score
        if item.raw_score:
            # Normalize HN scores (typically 0-500+) to 0-1 range
            normalized_score = min(item.raw_score / 100.0, 1.0)
            score += normalized_score * 2.0  # Weight: 2x
            if item.raw_score > 100:
                reasons.append(f"High engagement ({int(item.raw_score)} points)")

        # Factor 4: Topic relevance
        topic_score = calculate_topic_relevance(item, topics_lower)
        score += topic_score * 4.0  # Weight: 4x (most important)
        if topic_score > 0:
            matched_topics = get_matched_topics(item, topics_lower)
            if matched_topics:
                reasons.append(f"Relevant topics: {', '.join(matched_topics)}")

        ranked.append(RankedItem(item=item, score=score, reasons=reasons))

    # Sort by score (descending)
    ranked.sort()

    logger.info(f"Ranked {len(ranked)} items, top score: {ranked[0].score:.2f}")
    return ranked


def calculate_recency_score(published_at: datetime, now: datetime, cutoff: datetime) -> float:
    """
    Calculate recency score (0.0 to 1.0).

    Items within cutoff window get higher scores based on freshness.
    """
    if published_at > now:
        # Future dates get max score (might be timezone issues)
        return 1.0

    if published_at < cutoff:
        # Too old
        return 0.0

    # Linear decay within the recency window
    age_hours = (now - published_at).total_seconds() / 3600
    max_hours = Config.RECENCY_HOURS
    return 1.0 - (age_hours / max_hours)


def get_source_weight(source: str) -> float:
    """Get weight for a given source."""
    source_lower = source.lower()

    if "hackernews" in source_lower or "hacker news" in source_lower:
        return Config.WEIGHT_HN

    # Default RSS weight
    return Config.WEIGHT_RSS_DEFAULT


def calculate_topic_relevance(item: NewsItem, topics: list[str]) -> float:
    """
    Calculate topic relevance score (0.0 to 1.0).

    Checks title and summary for topic keywords.
    """
    text = f"{item.title} {item.summary or ''}".lower()

    matches = sum(1 for topic in topics if topic in text)

    if matches == 0:
        return 0.0

    # Normalize by number of topics (but cap at 1.0)
    return min(matches / 3.0, 1.0)  # 3+ matches = max score


def get_matched_topics(item: NewsItem, topics: list[str]) -> list[str]:
    """Get list of topics that match this item."""
    text = f"{item.title} {item.summary or ''}".lower()
    return [topic for topic in topics if topic in text]


def has_high_topic_confidence(item: NewsItem, topics: list[str]) -> bool:
    """
    Determine if item has high confidence match to configured topics.

    Used to filter "Other Candidates" - only include items that clearly
    relate to AI/DevOps/Security practice, not general news.

    Returns:
        True if item strongly matches at least one topic
    """
    text = f"{item.title} {item.summary or ''}".lower()

    # Must match at least one configured topic
    matched_topics = get_matched_topics(item, topics)
    if not matched_topics:
        return False

    # Additional filters for off-brand content
    off_brand_keywords = [
        "died", "death", "funeral", "obituary",  # Human interest
        "election", "vote", "congress", "senate",  # Politics
        "health", "medical", "doctor", "patient",  # Healthcare (unless tech-related)
        "entertainment", "movie", "film", "tv show",  # Entertainment
        "sports", "game", "player", "coach",  # Sports
        "lobster lady", "miles", "email",  # Humour/off-topic
    ]

    # Check if it contains off-brand keywords
    for keyword in off_brand_keywords:
        if keyword in text:
            # Exception: if it also strongly matches tech topics, allow it
            tech_keywords = ["security", "kubernetes", "ai", "ml", "devops", "cloud"]
            if not any(tech in text for tech in tech_keywords):
                return False

    # Check source - HN items without topic match are often off-brand
    if item.source == "HackerNews":
        # HN items need strong topic signal
        if len(matched_topics) < 1:
            return False

    return True


def _format_age(published_at: datetime, now: datetime) -> str:
    """Format age of item as human-readable string."""
    delta = now - published_at
    hours = delta.total_seconds() / 3600

    if hours < 1:
        return "< 1h ago"
    elif hours < 24:
        return f"{int(hours)}h ago"
    else:
        days = int(hours / 24)
        return f"{days}d ago"
