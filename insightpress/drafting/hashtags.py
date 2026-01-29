"""Hashtag mapping and selection."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from ..config import Config
from ..models import NewsItem

logger = logging.getLogger(__name__)


class HashtagMapper:
    """Maps keywords to hashtags."""

    def __init__(self, hashtags_config_path: Optional[Path] = None):
        """
        Initialize hashtag mapper.

        Args:
            hashtags_config_path: Path to hashtags.yaml config file
        """
        self.config_path = hashtags_config_path or Config.CONFIG_DIR / "hashtags.yaml"
        self.mappings = self._load_hashtag_config()

    def _load_hashtag_config(self) -> dict[str, str]:
        """Load hashtag mappings from YAML file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Hashtags config not found at {self.config_path}, using defaults")
                return self._default_mappings()

            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                mappings = config.get("mappings", {})
                logger.debug(f"Loaded {len(mappings)} hashtag mappings")
                return mappings
        except Exception as e:
            logger.error(f"Failed to load hashtags config: {e}")
            return self._default_mappings()

    def _default_mappings(self) -> dict[str, str]:
        """Default keyword -> hashtag mappings."""
        return {
            "ai": "AI",
            "artificial intelligence": "AI",
            "machine learning": "MachineLearning",
            "ml": "MachineLearning",
            "deep learning": "DeepLearning",
            "llm": "LLM",
            "large language model": "LLM",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "docker": "Docker",
            "devops": "DevOps",
            "security": "Security",
            "cybersecurity": "CyberSecurity",
            "infosec": "InfoSec",
            "mlops": "MLOps",
            "rust": "RustLang",
            "python": "Python",
            "golang": "Golang",
            "go": "Golang",
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "GCP",
            "cloud": "CloudComputing",
            "observability": "Observability",
            "monitoring": "Monitoring",
            "terraform": "Terraform",
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "claude": "Claude",
            "chatgpt": "ChatGPT",
            "api": "API",
            "opensource": "OpenSource",
            "open source": "OpenSource",
        }

    def get_hashtags(self, item: NewsItem, max_tags: int = 3) -> list[str]:
        """
        Get relevant hashtags for a news item.

        STRICT RULES:
        - All hashtags must be lowercase
        - Maximum HASHTAGS_MAX tags (default 3)
        - Only from whitelist (no ad-hoc tags)
        - Represent domains, not brands

        Args:
            item: NewsItem to analyze
            max_tags: Maximum number of hashtags to return

        Returns:
            List of lowercase hashtag strings (without # prefix)
        """
        text = f"{item.title} {item.summary or ''}".lower()

        # Find matching keywords
        matched_tags = []
        for keyword, hashtag in self.mappings.items():
            if keyword.lower() in text:
                # Enforce lowercase
                hashtag_lower = hashtag.lower()
                if hashtag_lower not in matched_tags:
                    matched_tags.append(hashtag_lower)

        # Return top N tags (respect HASHTAGS_MAX)
        return matched_tags[:max_tags]


# Global instance
_hashtag_mapper: Optional[HashtagMapper] = None


def get_relevant_hashtags(item: NewsItem, max_tags: Optional[int] = None) -> list[str]:
    """
    Get relevant hashtags for a news item (convenience function).

    Args:
        item: NewsItem to analyze
        max_tags: Maximum number of hashtags (uses config default if None)

    Returns:
        List of hashtag strings
    """
    global _hashtag_mapper

    if _hashtag_mapper is None:
        _hashtag_mapper = HashtagMapper()

    max_tags = max_tags or Config.HASHTAGS_MAX
    return _hashtag_mapper.get_hashtags(item, max_tags)
