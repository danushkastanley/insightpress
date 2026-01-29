"""RSS feed collector."""

import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

import feedparser
import yaml

from ..config import Config
from ..models import NewsItem

logger = logging.getLogger(__name__)


class RSSCollector:
    """Collects items from RSS feeds."""

    def __init__(self, feeds_config_path: Optional[Path] = None):
        """
        Initialize RSS collector.

        Args:
            feeds_config_path: Path to feeds.yaml config file
        """
        self.feeds_config_path = feeds_config_path or Config.CONFIG_DIR / "feeds.yaml"
        self.feeds = self._load_feeds_config()

    def _load_feeds_config(self) -> list[dict]:
        """Load RSS feeds configuration from YAML file."""
        try:
            if not self.feeds_config_path.exists():
                logger.warning(f"Feeds config not found at {self.feeds_config_path}, using empty list")
                return []

            with open(self.feeds_config_path, "r") as f:
                config = yaml.safe_load(f)
                return config.get("feeds", [])
        except Exception as e:
            logger.error(f"Failed to load feeds config: {e}")
            return []

    def collect(self) -> list[NewsItem]:
        """
        Collect items from all configured RSS feeds.

        Returns:
            List of NewsItem objects
        """
        if not self.feeds:
            logger.warning("No RSS feeds configured")
            return []

        logger.info(f"Fetching from {len(self.feeds)} RSS feeds")

        all_items = []
        for feed_config in self.feeds:
            items = self._fetch_feed(feed_config)
            all_items.extend(items)

        logger.info(f"Successfully fetched {len(all_items)} items from RSS feeds")
        return all_items

    def _fetch_feed(self, feed_config: dict) -> list[NewsItem]:
        """Fetch items from a single RSS feed."""
        url = feed_config.get("url")
        name = feed_config.get("name", url)
        weight = feed_config.get("weight", Config.WEIGHT_RSS_DEFAULT)

        if not url:
            logger.warning(f"Feed config missing URL: {feed_config}")
            return []

        try:
            logger.debug(f"Fetching feed: {name}")
            # Set user agent for feedparser
            feed = feedparser.parse(
                url,
                agent=Config.USER_AGENT,
            )

            if feed.bozo and not feed.entries:
                logger.warning(f"Failed to parse feed {name}: {feed.bozo_exception}")
                return []

            items = []
            for entry in feed.entries:
                item = self._parse_entry(entry, name, weight)
                if item:
                    items.append(item)

            logger.debug(f"Fetched {len(items)} items from {name}")
            return items

        except Exception as e:
            logger.error(f"Error fetching feed {name}: {e}")
            return []

    def _parse_entry(self, entry, feed_name: str, weight: float) -> Optional[NewsItem]:
        """Parse a single RSS entry into a NewsItem."""
        try:
            # Get URL
            url = entry.get("link")
            if not url:
                return None

            # Get title
            title = entry.get("title", "Untitled")

            # Get published date
            published_at = self._parse_date(entry)
            if not published_at:
                published_at = datetime.now(timezone.utc)

            # Get summary (optional)
            summary = entry.get("summary") or entry.get("description")
            if summary:
                # Clean HTML tags from summary (basic cleaning)
                summary = summary[:500]  # Limit length

            # Generate ID from URL
            item_id = f"rss_{hash(url)}"

            return NewsItem(
                id=item_id,
                title=title,
                url=url,
                source=feed_name,
                published_at=published_at,
                summary=summary,
                raw_score=weight,  # Use feed weight as base score
            )

        except Exception as e:
            logger.debug(f"Failed to parse entry: {e}")
            return None

    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse publication date from RSS entry."""
        # Try published_parsed first, then updated_parsed
        for date_field in ["published_parsed", "updated_parsed"]:
            date_tuple = entry.get(date_field)
            if date_tuple:
                try:
                    return datetime(*date_tuple[:6], tzinfo=timezone.utc)
                except Exception:
                    pass

        # Try ISO format strings
        for date_field in ["published", "updated"]:
            date_str = entry.get(date_field)
            if date_str:
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except Exception:
                    pass

        return None
