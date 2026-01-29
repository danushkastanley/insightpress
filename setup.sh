#!/bin/bash
#
# InsightPress Setup Script
# Automates installation and first run
#

set -e  # Exit on error

echo "================================================"
echo "  InsightPress Setup"
echo "================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    echo "   Please install Python 3.11+ first"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Step 1: Create virtual environment
echo "📦 Step 1/4: Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   Virtual environment already exists, skipping..."
else
    python3 -m venv .venv
    echo "   ✓ Virtual environment created"
fi
echo ""

# Step 2: Activate and upgrade pip
echo "🔧 Step 2/4: Setting up package manager..."
source .venv/bin/activate
pip install --upgrade pip setuptools wheel --quiet
echo "   ✓ Package manager ready"
echo ""

# Step 3: Install dependencies
echo "📥 Step 3/4: Installing dependencies..."
pip install python-dotenv feedparser requests pyyaml --quiet
echo "   ✓ Dependencies installed"
echo "      - python-dotenv"
echo "      - feedparser"
echo "      - requests"
echo "      - pyyaml"
echo ""

# Step 4: Run the app
echo "🚀 Step 4/4: Running InsightPress..."
echo ""
echo "================================================"
echo ""

python -m insightpress run

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo ""
echo "📝 Your drafts are saved in: output/daily_drafts_$(date +%Y-%m-%d).md"
echo ""
echo "To run again later:"
echo "   ./run.sh"
echo ""
echo "To customize configuration:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "================================================"
