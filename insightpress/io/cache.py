"""Caching system for fetched items."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import Config
from ..models import NewsItem

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of fetched news items."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files (uses config default if None)
        """
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, date: Optional[str] = None) -> Path:
        """
        Get cache file path for a given date.

        Args:
            date: Date string (YYYY-MM-DD), uses today if None

        Returns:
            Path to cache file
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        return self.cache_dir / f"items_{date}.json"

    def load_cached_items(self, date: Optional[str] = None) -> Optional[list[NewsItem]]:
        """
        Load cached items for a given date.

        Args:
            date: Date string (YYYY-MM-DD), uses today if None

        Returns:
            List of NewsItem objects, or None if cache doesn't exist
        """
        cache_path = self.get_cache_path(date)

        if not cache_path.exists():
            logger.info(f"No cache found at {cache_path}")
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            items = [NewsItem(**item_data) for item_data in data["items"]]
            logger.info(f"Loaded {len(items)} items from cache ({cache_path})")
            return items

        except Exception as e:
            logger.error(f"Failed to load cache from {cache_path}: {e}")
            return None

    def save_items(self, items: list[NewsItem], date: Optional[str] = None):
        """
        Save items to cache.

        Args:
            items: List of NewsItem objects
            date: Date string (YYYY-MM-DD), uses today if None
        """
        cache_path = self.get_cache_path(date)

        try:
            # Convert items to JSON-serializable format
            items_data = []
            for item in items:
                item_dict = {
                    "id": item.id,
                    "title": item.title,
                    "url": item.url,
                    "source": item.source,
                    "published_at": item.published_at.isoformat(),
                    "summary": item.summary,
                    "raw_score": item.raw_score,
                    "canonical_url": item.canonical_url,
                }
                items_data.append(item_dict)

            data = {
                "cached_at": datetime.now().isoformat(),
                "count": len(items),
                "items": items_data,
            }

            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(items)} items to cache ({cache_path})")

        except Exception as e:
            logger.error(f"Failed to save cache to {cache_path}: {e}")

    def clear_cache(self, date: Optional[str] = None):
        """
        Clear cache for a given date.

        Args:
            date: Date string (YYYY-MM-DD), uses today if None
        """
        cache_path = self.get_cache_path(date)

        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Cleared cache at {cache_path}")
        else:
            logger.info(f"No cache to clear at {cache_path}")
