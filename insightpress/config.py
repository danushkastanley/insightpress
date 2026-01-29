"""Configuration management for InsightPress."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Application configuration."""

    # Directories
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "cache"))
    CONFIG_DIR: Path = Path("config")

    # Collection settings
    MAX_ITEMS: int = int(os.getenv("MAX_ITEMS", "30"))
    DRAFTS_COUNT: int = int(os.getenv("DRAFTS_COUNT", "4"))
    HN_STORY_TYPE: str = os.getenv("HN_STORY_TYPE", "beststories")
    HN_MAX_STORIES: int = int(os.getenv("HN_MAX_STORIES", "50"))

    # Ranking settings
    TOPICS: list[str] = os.getenv("TOPICS", "ai,llm,kubernetes,devops,security,mlops,rust,python,aws,observability").split(",")
    RECENCY_HOURS: int = int(os.getenv("RECENCY_HOURS", "72"))

    # Source weights
    WEIGHT_HN: float = float(os.getenv("WEIGHT_HN", "1.0"))
    WEIGHT_RSS_DEFAULT: float = float(os.getenv("WEIGHT_RSS_DEFAULT", "0.8"))

    # Draft generation
    HASHTAGS_MAX: int = int(os.getenv("HASHTAGS_MAX", "3"))
    DRAFT_STYLE: str = os.getenv("DRAFT_STYLE", "technical")
    CHAR_LIMIT: int = int(os.getenv("CHAR_LIMIT", "260"))  # Hard limit for X posts
    VOICE_FILE: Optional[Path] = None  # Set to Path("voice.md") if exists

    # LLM provider settings (optional)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")  # openai|anthropic|gemini|none
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL")  # Provider-specific model name
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    LLM_TIMEOUT_SECS: int = int(os.getenv("LLM_TIMEOUT_SECS", "20"))

    # API keys (optional - only needed if using LLM providers)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    # Network settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    USER_AGENT: str = os.getenv("USER_AGENT", "insightpress/0.1")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def ensure_dirs(cls):
        """Ensure output and cache directories exist."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Check if voice.md exists
        voice_path = Path("voice.md")
        if voice_path.exists():
            cls.VOICE_FILE = voice_path

    @classmethod
    def override(cls, **kwargs):
        """Override configuration values at runtime."""
        for key, value in kwargs.items():
            if hasattr(cls, key.upper()):
                setattr(cls, key.upper(), value)
