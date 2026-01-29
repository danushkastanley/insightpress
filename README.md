# InsightPress 🎯

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Generate high-quality draft X (Twitter) posts from trusted tech and AI sources automatically.**

InsightPress is a production-ready CLI tool that fetches, ranks, and transforms tech news into ready-to-post social media content. Built for developers, tech writers, and DevRel professionals who want to maintain an active X presence without the manual work.

> **🚀 New to this?** Check out [QUICKSTART.md](QUICKSTART.md) for a 2-minute setup guide.

---

## ✨ Why InsightPress?

- 🤖 **Fully Automated** - Fetches from Hacker News + 11 curated RSS feeds
- 🎯 **Smart Filtering** - Ranks by recency, engagement, and topic relevance
- 📝 **Ready-to-Post** - Generates polished drafts with hashtags and links
- 🔒 **Privacy First** - No API keys required, no auto-posting, no data collection
- ⚡ **Fast Setup** - One command to install and run
- 🎨 **Customizable** - Adjust topics, feeds, hashtags, and templates

**Important:** This tool only creates drafts for human review. It never posts automatically.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Example Output](#example-output)
- [CLI Reference](#cli-reference)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Features

### Content Collection
- **Hacker News Integration** - Top stories with scores and engagement metrics
- **RSS Feed Aggregation** - 11 pre-configured sources (AWS, OpenAI, Kubernetes, etc.)
- **Zero Configuration** - Works out of the box, no API keys needed
- **Daily Caching** - Avoids redundant API calls

### Smart Processing
- **Intelligent Ranking** - Multi-factor scoring (recency, engagement, topics, source weight)
- **Deduplication** - URL canonicalization + fuzzy title matching
- **Topic Filtering** - Focus on AI, DevOps, Security, Cloud, etc.
- **Source Weighting** - Prioritize trusted sources

### Draft Generation
- **X-Optimized Format** - Hook + Value + Action + Link structure
- **Smart Hashtags** - Keyword-based mapping with customizable whitelist
- **Character Counting** - Ensures tweets stay within limits
- **Template Variety** - Technical and casual styles available

### Developer Experience
- **Type Hints** - Full type coverage for better IDE support
- **Comprehensive Logging** - Debug mode for troubleshooting
- **Modular Architecture** - Easy to extend with new sources
- **Production Ready** - Error handling, timeouts, and safe defaults

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Internet connection (for fetching news)
- macOS, Linux, or WSL on Windows

### Installation

#### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/insightpress.git
cd insightpress

# Run the setup script
./setup.sh
```

This single command:
- Creates a virtual environment
- Installs all dependencies
- Generates your first batch of drafts
- Shows you where to find the output

**For daily use:**
```bash
./run.sh
```

#### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install python-dotenv feedparser requests pyyaml

# Run the tool
python -m insightpress run
```

#### Option 3: Direct Dependency Install (Advanced)

```bash
pip install python-dotenv feedparser requests pyyaml
python -m insightpress run
```

### Basic Usage

```bash
# Generate drafts with defaults (4 posts, AI/DevOps topics)
./run.sh

# Generate 5 drafts on specific topics
./run.sh run --drafts 5 --topics "ai,security,kubernetes"

# Force fresh data (ignore cache)
./run.sh run --refresh

# Get more candidates
./run.sh run --max-items 50

# See all options
./run.sh run --help
```

### First Run Results

After running, you'll find your drafts in:
```bash
output/daily_drafts_YYYY-MM-DD.md
```

Open this file to see:
- 4 ready-to-post X drafts
- 26+ ranked candidates for future posts
- Metadata and statistics

## Configuration

### Environment Variables

Copy [.env.example](.env.example) to `.env` and customize:

```bash
# Collection settings
MAX_ITEMS=30              # Items to keep after ranking
DRAFTS_COUNT=4            # Number of drafts to generate
HN_STORY_TYPE=beststories # or topstories

# Ranking
TOPICS=ai,llm,kubernetes,devops,security,mlops
RECENCY_HOURS=72          # Prefer items from last N hours

# Drafts
HASHTAGS_MAX=3            # Max hashtags per post
DRAFT_STYLE=technical     # or casual

# Network
REQUEST_TIMEOUT=10
USER_AGENT=insightpress/0.1
```

### RSS Feeds

Edit [config/feeds.yaml](config/feeds.yaml) to add/remove feeds:

```yaml
feeds:
  - name: "AWS News"
    url: "https://aws.amazon.com/blogs/aws/feed/"
    weight: 0.9

  - name: "Your Custom Feed"
    url: "https://example.com/feed.xml"
    weight: 0.8
```

**Default feeds included:**
- AWS, Azure, Google Cloud blogs
- OpenAI, Anthropic news
- Kubernetes, Docker, HashiCorp blogs
- Cloudflare, GitHub blogs
- The New Stack

### Hashtags

Edit [config/hashtags.yaml](config/hashtags.yaml) to customize keyword → hashtag mappings:

```yaml
mappings:
  "kubernetes": "Kubernetes"
  "llm": "LLM"
  "your-keyword": "YourHashtag"
```

## How It Works

1. **Fetch** – Collect items from Hacker News API + RSS feeds (parallel, with timeouts)
2. **Deduplicate** – Canonicalize URLs (remove UTM params) and fuzzy-match titles
3. **Rank** – Score by recency (72h window), topic keywords, source weight, engagement
4. **Generate** – Create X-style drafts using templates (hook + why + action + link + hashtags)
5. **Write** – Save to `output/daily_drafts_YYYY-MM-DD.md` with metadata

## 📊 Example Output

Here's what InsightPress generates:

### Top Drafts Section
```markdown
### Draft 1

```
Rust at Scale: An Added Layer of Security for WhatsApp This could impact
security posture. Worth testing in a side project.

https://engineering.fb.com/2026/01/27/security/rust-at-scale-security-whatsapp/
#Security #RustLang
```

**Source:** Rust at Scale: An Added Layer of Security for WhatsApp
**From:** HackerNews
**Published:** 2026-01-28 06:21 UTC
**Character count:** 225/280
```

### Other Candidates Section
```markdown
1. **Ingress NGINX: Statement from Kubernetes Security**
   - Source: Kubernetes Blog
   - Score: 7.87
   - Reasons: Recent (17h ago), Relevant topics: kubernetes, security
   - Link: https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/

2. **Claude Code Daily Benchmarks for Degradation Tracking**
   - Source: HackerNews
   - Score: 7.45
   - Reasons: Recent (9h ago), High engagement (156 points)
   - Link: https://marginlab.ai/trackers/claude-code/
```

Each report includes:
- ✅ 3-4 copy-paste ready drafts
- ✅ Character counts (Twitter limit aware)
- ✅ Source attribution and timestamps
- ✅ Ranked alternatives for future posts
- ✅ Statistics (items fetched, duplicates removed)

**See a real example:** Check the `output/` directory after your first run.

## CLI Reference

```bash
python -m insightpress run [OPTIONS]

Options:
  --drafts N           Number of drafts to generate (default: 4)
  --max-items N        Max items after ranking (default: 30)
  --refresh            Ignore cache, fetch fresh
  --topics "a,b,c"     Override topic keywords
  --output PATH        Custom output file
  --log-level LEVEL    DEBUG|INFO|WARNING|ERROR (default: INFO)
```

## Project Structure

```
insightpress/
├── __init__.py
├── __main__.py          # CLI entry point
├── main.py              # Core orchestration
├── config.py            # Configuration management
├── models.py            # Data models
├── collectors/          # Data fetchers
│   ├── hn.py           # Hacker News API
│   └── rss.py          # RSS feeds
├── processing/          # Data processing
│   ├── dedupe.py       # Deduplication logic
│   └── rank.py         # Ranking algorithm
├── drafting/            # Draft generation
│   ├── composer.py     # Template-based drafts
│   └── hashtags.py     # Hashtag mapping
└── io/                  # I/O operations
    ├── cache.py        # Caching system
    └── writer.py       # Markdown output

config/
├── feeds.yaml          # RSS feed configuration
└── hashtags.yaml       # Hashtag mappings

output/                 # Generated reports (gitignored)
cache/                  # Cached fetches (gitignored)
```

## Development

### Requirements

- Python 3.11+
- Dependencies: `python-dotenv`, `feedparser`, `requests`, `pyyaml`

### Type Hints

All code includes type hints for better IDE support and maintainability.

### Logging

Set `LOG_LEVEL=DEBUG` in `.env` for verbose output:

```bash
python -m insightpress run --log-level DEBUG
```

### Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (if added)
pytest

# Format code
black insightpress/
```

## Design Principles

- **No secrets required** – Works with zero configuration
- **Safe defaults** – Sensible behavior out of the box
- **Modular design** – Easy to extend with new sources or LLM rewriting
- **Minimal dependencies** – Only essential libraries
- **Production ready** – Proper error handling, timeouts, logging

## Limitations

- No X posting (by design – drafts only)
- Sequential HTTP requests (no async) for simplicity
- Basic template-based drafts (no LLM)
- English-language sources only

## Future Enhancements

Potential additions (not implemented):

- arXiv RSS for cs.AI/cs.LG papers
- Optional LLM rewriting stage (OpenAI/Anthropic)
- Sentiment analysis for filtering
- Historical tracking of posted drafts
- Web dashboard (separate project)

## License

MIT License - see [LICENSE](LICENSE) file.

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Ways to Contribute

1. **Add RSS Feeds** - Submit PRs with new trusted sources
2. **Improve Templates** - Enhance draft generation templates
3. **Add Features** - LLM integration, sentiment analysis, etc.
4. **Fix Bugs** - Report or fix issues you encounter
5. **Documentation** - Improve guides, add examples, fix typos

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/insightpress.git
cd insightpress
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run with debug logging
python -m insightpress run --log-level DEBUG

# Format code
black insightpress/

# Type check
mypy insightpress/
```

### Guidelines

- Keep dependencies minimal (avoid heavy frameworks)
- Include type hints for all functions
- Add logging for debugging (use appropriate levels)
- Follow existing code structure
- Update tests if modifying core logic
- Update README for user-facing changes

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

## 🙏 Acknowledgments

- Hacker News for the excellent public API
- RSS feed providers for making content accessible
- The Python community for amazing libraries

## 📞 Support & Community

- **Issues:** [GitHub Issues](https://github.com/yourusername/insightpress/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/insightpress/discussions)
- **Documentation:** This README + [QUICKSTART.md](QUICKSTART.md)

## ⭐ Star History

If you find InsightPress useful, please consider giving it a star! It helps others discover the project.

---

**Built with ❤️ using Python | No API keys required | Privacy-focused | Drafts only, never auto-posts**

Made for developers who want to maintain an active tech presence on X without the manual grind.
