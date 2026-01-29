"""Deduplication logic for news items."""

import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional

from ..models import NewsItem

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL for deduplication.

    - Normalize scheme to https
    - Remove trailing slashes
    - Remove common tracking parameters (utm_*, fbclid, etc.)
    - Lowercase domain
    """
    try:
        parsed = urlparse(url)

        # Normalize scheme
        scheme = "https" if parsed.scheme in ["http", "https"] else parsed.scheme

        # Lowercase domain
        netloc = parsed.netloc.lower()

        # Remove trailing slash from path
        path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path

        # Filter out tracking parameters
        if parsed.query:
            params = parse_qs(parsed.query)
            tracking_params = {
                "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid",
                "_hsenc", "_hsmi", "mkt_tok",
            }
            filtered_params = {k: v for k, v in params.items() if k not in tracking_params}
            query = urlencode(filtered_params, doseq=True) if filtered_params else ""
        else:
            query = ""

        # Reconstruct URL
        canonical = urlunparse((scheme, netloc, path, "", query, ""))
        return canonical

    except Exception as e:
        logger.debug(f"Failed to canonicalize URL {url}: {e}")
        return url


def title_similarity(title1: str, title2: str) -> float:
    """
    Calculate simple token-based similarity between titles.

    Returns value between 0.0 (no match) and 1.0 (exact match).
    """
    # Normalize titles
    tokens1 = set(title1.lower().split())
    tokens2 = set(title2.lower().split())

    if not tokens1 or not tokens2:
        return 0.0

    # Jaccard similarity
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


def deduplicate_items(
    items: list[NewsItem],
    url_threshold: float = 0.95,
    title_threshold: float = 0.85,
) -> tuple[list[NewsItem], list[tuple[str, str]]]:
    """
    Deduplicate news items by URL and title similarity.

    Args:
        items: List of NewsItem objects
        url_threshold: Similarity threshold for URL matching (not used, URLs are exact)
        title_threshold: Similarity threshold for title matching

    Returns:
        Tuple of (unique_items, skipped_items)
        skipped_items is a list of (title, reason) tuples
    """
    logger.info(f"Deduplicating {len(items)} items")

    # First pass: canonicalize URLs
    for item in items:
        item.canonical_url = canonicalize_url(item.url)

    # Track seen URLs and titles
    seen_urls: dict[str, NewsItem] = {}
    seen_titles: dict[str, NewsItem] = {}
    unique_items: list[NewsItem] = []
    skipped: list[tuple[str, str]] = []

    for item in items:
        # Check for duplicate URL
        if item.canonical_url in seen_urls:
            original = seen_urls[item.canonical_url]
            reason = f"Duplicate URL (original from {original.source})"
            skipped.append((item.title, reason))
            logger.debug(f"Skipping duplicate URL: {item.title}")
            continue

        # Check for similar title
        is_duplicate = False
        for seen_title, seen_item in seen_titles.items():
            similarity = title_similarity(item.title, seen_title)
            if similarity >= title_threshold:
                reason = f"Similar title to '{seen_title[:50]}...' (similarity: {similarity:.2f})"
                skipped.append((item.title, reason))
                logger.debug(f"Skipping similar title: {item.title}")
                is_duplicate = True
                break

        if not is_duplicate:
            unique_items.append(item)
            seen_urls[item.canonical_url] = item
            seen_titles[item.title] = item

    logger.info(f"After deduplication: {len(unique_items)} unique items, {len(skipped)} duplicates")
    return unique_items, skipped
