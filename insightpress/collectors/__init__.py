"""Data collectors for various sources."""

from .hn import HackerNewsCollector
from .rss import RSSCollector

__all__ = ["HackerNewsCollector", "RSSCollector"]
