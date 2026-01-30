"""Track previously used items to avoid repetition across runs."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class UsedItemsTracker:
    """Tracks items that have been used in previous drafts."""

    def __init__(self, cache_dir: Path, retention_days: int = 7):
        """
        Initialize used items tracker.

        Args:
            cache_dir: Directory to store tracking file
            retention_days: Number of days to remember used items (default 7)
        """
        self.cache_file = cache_dir / "used_items.json"
        self.retention_days = retention_days
        self.used_items = self._load()

    def _load(self) -> dict[str, str]:
        """Load used items from cache file."""
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)

            # Clean up old entries
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            cleaned = {
                url: timestamp
                for url, timestamp in data.items()
                if datetime.fromisoformat(timestamp) > cutoff
            }

            logger.info(f"Loaded {len(cleaned)} used items (removed {len(data) - len(cleaned)} old entries)")
            return cleaned

        except Exception as e:
            logger.warning(f"Failed to load used items: {e}")
            return {}

    def _save(self):
        """Save used items to cache file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self.used_items, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save used items: {e}")

    def is_used(self, url: str) -> bool:
        """Check if item URL has been used recently."""
        return url in self.used_items

    def mark_used(self, url: str):
        """Mark an item URL as used."""
        self.used_items[url] = datetime.now().isoformat()

    def mark_multiple_used(self, urls: list[str]):
        """Mark multiple item URLs as used."""
        now = datetime.now().isoformat()
        for url in urls:
            self.used_items[url] = now

    def save(self):
        """Save the current state."""
        self._save()
        logger.info(f"Saved {len(self.used_items)} used items")

    def get_stats(self) -> dict:
        """Get statistics about tracked items."""
        return {
            "total_tracked": len(self.used_items),
            "retention_days": self.retention_days,
            "cache_file": str(self.cache_file),
        }
