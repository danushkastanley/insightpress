"""CLI entry point for InsightPress."""

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .main import run


def setup_logging(level: str):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="insightpress",
        description="Generate draft X posts from trusted tech/AI sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m insightpress run
  python -m insightpress run --drafts 5 --topics "ai,kubernetes,security"
  python -m insightpress run --refresh --max-items 50
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Generate drafts")
    run_parser.add_argument(
        "--drafts",
        type=int,
        help=f"Number of drafts to generate (default: {Config.DRAFTS_COUNT})",
    )
    run_parser.add_argument(
        "--max-items",
        type=int,
        help=f"Maximum items to keep after ranking (default: {Config.MAX_ITEMS})",
    )
    run_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh, ignore cache",
    )
    run_parser.add_argument(
        "--topics",
        type=str,
        help="Comma-separated topics to filter by (default: from config)",
    )
    run_parser.add_argument(
        "--output",
        type=Path,
        help="Custom output file path",
    )
    run_parser.add_argument(
        "--log-level",
        type=str,
        default=Config.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    run_parser.add_argument(
        "--llm-provider",
        type=str,
        choices=["openai", "anthropic", "gemini", "none"],
        help=f"LLM provider for draft generation (default: {Config.LLM_PROVIDER})",
    )
    run_parser.add_argument(
        "--llm-model",
        type=str,
        help="LLM model name (provider-specific)",
    )
    run_parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Force template-based drafting (ignore LLM config)",
    )

    args = parser.parse_args()

    # Check if command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    setup_logging(args.log_level)

    try:
        if args.command == "run":
            # Parse topics if provided
            topics = None
            if args.topics:
                topics = [t.strip() for t in args.topics.split(",")]

            # Run the main logic
            output_file = run(
                drafts_count=args.drafts,
                max_items=args.max_items,
                refresh=args.refresh,
                topics=topics,
                output_path=args.output,
                llm_provider=args.llm_provider if hasattr(args, 'llm_provider') else None,
                llm_model=args.llm_model if hasattr(args, 'llm_model') else None,
                no_llm=args.no_llm if hasattr(args, 'no_llm') else False,
            )

            print(f"\n✓ Successfully generated drafts!")
            print(f"  Output: {output_file}")
            print(f"\nView your drafts: cat {output_file}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
