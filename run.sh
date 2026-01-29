#!/bin/bash
#
# InsightPress Run Script
# Quick execution after initial setup
#

set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run setup first: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import dotenv, feedparser, requests, yaml" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "   Please run setup first: ./setup.sh"
    exit 1
fi

echo "================================================"
echo "  InsightPress"
echo "================================================"
echo ""

# Parse command line arguments
ARGS="$@"

# If no arguments provided, use default 'run' command
if [ -z "$ARGS" ]; then
    ARGS="run"
fi

# Run the app with provided arguments
python -m insightpress $ARGS

# Show output location if successful and running 'run' command
if [ "$?" -eq 0 ] && [[ "$ARGS" == "run"* ]]; then
    echo ""
    echo "================================================"
    echo "✅ Done!"
    echo ""
    echo "📝 View your drafts:"
    echo "   cat output/daily_drafts_$(date +%Y-%m-%d).md"
    echo ""
    echo "🔄 Run with options:"
    echo "   ./run.sh run --drafts 5 --topics \"ai,security\""
    echo "   ./run.sh run --refresh"
    echo "   ./run.sh run --help"
    echo ""
    echo "================================================"
fi
