"""Hacker News collector using the public API."""

import logging
from datetime import datetime, timezone
from typing import Optional

import requests

from ..config import Config
from ..models import NewsItem

logger = logging.getLogger(__name__)


class HackerNewsCollector:
    """Collects stories from Hacker News public API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": Config.USER_AGENT})

    def collect(self, max_stories: Optional[int] = None) -> list[NewsItem]:
        """
        Collect top/best stories from Hacker News.

        Args:
            max_stories: Maximum number of stories to fetch (uses config default if None)

        Returns:
            List of NewsItem objects
        """
        max_stories = max_stories or Config.HN_MAX_STORIES
        story_type = Config.HN_STORY_TYPE

        logger.info(f"Fetching {story_type} from Hacker News (max {max_stories})")

        try:
            # Get list of story IDs
            story_ids = self._fetch_story_ids(story_type, max_stories)
            if not story_ids:
                logger.warning("No story IDs returned from Hacker News")
                return []

            # Fetch details for each story
            items = []
            for story_id in story_ids:
                item = self._fetch_story_details(story_id)
                if item:
                    items.append(item)

            logger.info(f"Successfully fetched {len(items)} stories from Hacker News")
            return items

        except Exception as e:
            logger.error(f"Error collecting from Hacker News: {e}")
            return []

    def _fetch_story_ids(self, story_type: str, limit: int) -> list[int]:
        """Fetch list of story IDs."""
        try:
            url = f"{self.BASE_URL}/{story_type}.json"
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            story_ids = response.json()
            return story_ids[:limit]
        except Exception as e:
            logger.error(f"Failed to fetch story IDs: {e}")
            return []

    def _fetch_story_details(self, story_id: int) -> Optional[NewsItem]:
        """Fetch details for a single story."""
        try:
            url = f"{self.BASE_URL}/item/{story_id}.json"
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Skip if no URL (Ask HN, Show HN without URL, etc.)
            if not data.get("url"):
                return None

            # Convert Unix timestamp to UTC datetime
            published_at = datetime.fromtimestamp(data["time"], tz=timezone.utc)

            return NewsItem(
                id=f"hn_{story_id}",
                title=data["title"],
                url=data["url"],
                source="HackerNews",
                published_at=published_at,
                summary=None,
                raw_score=float(data.get("score", 0)),
            )

        except Exception as e:
            logger.debug(f"Failed to fetch story {story_id}: {e}")
            return None
