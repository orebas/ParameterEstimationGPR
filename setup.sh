#!/bin/bash
# Setup script for GPR Parameter Estimation Paper Repository
# Uses uv for fast, modern Python dependency management

set -e  # Exit on error

echo "========================================="
echo "GPR Parameter Estimation - Setup"
echo "========================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed"
    echo ""
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or visit: https://github.com/astral-sh/uv"
    echo ""
    exit 1
fi

echo "✓ Found uv: $(uv --version)"
echo ""

# Check Python version
echo "Checking Python version..."
if ! python3 --version | grep -qE "Python 3\.(1[0-9]|[2-9][0-9])"; then
    echo "⚠️  Warning: Python 3.10+ recommended"
    echo "   Current: $(python3 --version)"
    echo ""
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  .venv already exists, skipping creation"
else
    uv venv
    echo "✓ Created .venv"
fi
echo ""

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .
echo "✓ Dependencies installed"
echo ""

# Success message
echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Build the paper:      python build_paper.py"
echo ""
echo "Or run directly without activation:"
echo "  python build_paper.py"
echo ""
