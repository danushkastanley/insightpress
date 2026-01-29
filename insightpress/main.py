"""Main application logic for InsightPress."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .collectors import HackerNewsCollector, RSSCollector
from .config import Config
from .drafting import generate_drafts
from .io import CacheManager, write_report
from .llm import get_llm_client
from .models import DraftReport
from .processing import deduplicate_items, rank_items
from .processing.rank import has_high_topic_confidence

logger = logging.getLogger(__name__)


def run(
    drafts_count: Optional[int] = None,
    max_items: Optional[int] = None,
    refresh: bool = False,
    topics: Optional[list[str]] = None,
    output_path: Optional[Path] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    no_llm: bool = False,
) -> Path:
    """
    Main execution function for InsightPress.

    Args:
        drafts_count: Number of drafts to generate
        max_items: Maximum items to keep after ranking
        refresh: Force refresh (ignore cache)
        topics: Override topics list
        output_path: Custom output path
        llm_provider: LLM provider override (openai|anthropic|gemini|none)
        llm_model: LLM model override
        no_llm: Force template-based drafting

    Returns:
        Path to generated report file
    """
    logger.info("Starting InsightPress run")

    # Apply overrides
    if drafts_count:
        Config.DRAFTS_COUNT = drafts_count
    if max_items:
        Config.MAX_ITEMS = max_items
    if topics:
        Config.TOPICS = topics
    if llm_provider:
        Config.LLM_PROVIDER = llm_provider
    if llm_model:
        Config.LLM_MODEL = llm_model
    if no_llm:
        Config.LLM_PROVIDER = "none"

    # Ensure directories exist
    Config.ensure_dirs()

    # Initialize cache manager
    cache = CacheManager()

    # Step 1: Load or fetch items
    items = []
    if not refresh:
        cached_items = cache.load_cached_items()
        if cached_items:
            logger.info("Using cached items")
            items = cached_items

    if not items:
        logger.info("Fetching fresh items")
        items = _fetch_all_items()

        # Cache the fetched items
        if items:
            cache.save_items(items)

    if not items:
        logger.error("No items fetched, cannot continue")
        raise RuntimeError("No items available")

    total_fetched = len(items)
    logger.info(f"Total items: {total_fetched}")

    # Step 2: Deduplicate
    unique_items, skipped = deduplicate_items(items)
    logger.info(f"After deduplication: {len(unique_items)} unique items")

    # Step 3: Rank items
    ranked_items = rank_items(unique_items, topics=Config.TOPICS)
    logger.info(f"Ranked {len(ranked_items)} items")

    # Step 4: Initialize LLM client if configured
    llm_client = None
    if Config.LLM_PROVIDER != "none":
        # Get API key based on provider
        api_key = None
        if Config.LLM_PROVIDER == "openai":
            api_key = Config.OPENAI_API_KEY
        elif Config.LLM_PROVIDER == "anthropic":
            api_key = Config.ANTHROPIC_API_KEY
        elif Config.LLM_PROVIDER == "gemini":
            api_key = Config.GEMINI_API_KEY

        llm_client = get_llm_client(
            provider=Config.LLM_PROVIDER,
            api_key=api_key,
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            timeout=Config.LLM_TIMEOUT_SECS,
            max_retries=Config.LLM_MAX_RETRIES,
        )

    # Step 5: Generate drafts
    # Generate more than needed to account for filtering
    candidate_items = ranked_items[:Config.DRAFTS_COUNT * 3]
    drafts = generate_drafts(candidate_items, count=Config.DRAFTS_COUNT, llm_client=llm_client)
    logger.info(f"Generated {len(drafts)} drafts")

    # Step 6: Prepare other candidates with topic confidence filtering
    remaining_items = ranked_items[Config.DRAFTS_COUNT * 3:]
    other_candidates = [
        item for item in remaining_items[:Config.MAX_ITEMS]
        if has_high_topic_confidence(item.item, Config.TOPICS)
    ]
    logger.info(f"Filtered to {len(other_candidates)} high-confidence candidates")

    # Step 7: Build report
    now = datetime.now()
    report = DraftReport(
        date=now.strftime("%Y-%m-%d"),
        timestamp=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        top_drafts=drafts,
        other_candidates=other_candidates,
        skipped_items=skipped,
        total_items_fetched=total_fetched,
        total_duplicates_removed=len(skipped),
    )

    # Step 8: Write report
    output_file = write_report(report, output_path)
    logger.info(f"Report written to {output_file}")

    return output_file


def _fetch_all_items():
    """Fetch items from all sources."""
    all_items = []

    # Fetch from Hacker News
    logger.info("Collecting from Hacker News")
    hn_collector = HackerNewsCollector()
    hn_items = hn_collector.collect()
    all_items.extend(hn_items)
    logger.info(f"Collected {len(hn_items)} items from Hacker News")

    # Fetch from RSS feeds
    logger.info("Collecting from RSS feeds")
    rss_collector = RSSCollector()
    rss_items = rss_collector.collect()
    all_items.extend(rss_items)
    logger.info(f"Collected {len(rss_items)} items from RSS feeds")

    return all_items
