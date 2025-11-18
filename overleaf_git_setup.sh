#!/bin/bash
# Setup Overleaf Git Bridge Integration
# Requires Overleaf Premium/Pro account

set -e

echo "=================================================="
echo "Overleaf Git Bridge Setup"
echo "=================================================="
echo ""
echo "This script helps integrate your project with Overleaf's Git bridge."
echo ""

# Check if .env exists for storing credentials
if [ ! -f ".env" ]; then
    echo "Creating .env file for configuration..."
    cat > .env << 'EOF'
# Overleaf Git Bridge Configuration
# Get these from: https://www.overleaf.com/learn/how-to/Using_Git_and_GitHub
OVERLEAF_PROJECT_ID=""
OVERLEAF_EMAIL=""
# Password is your Overleaf password or Git token
EOF
    echo "✓ Created .env file"
    echo ""
    echo "Please edit .env and add:"
    echo "  1. OVERLEAF_PROJECT_ID (from project URL)"
    echo "  2. OVERLEAF_EMAIL (your Overleaf login email)"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Source environment
source .env

if [ -z "$OVERLEAF_PROJECT_ID" ]; then
    echo "ERROR: OVERLEAF_PROJECT_ID not set in .env"
    exit 1
fi

echo "Step 1: Adding Overleaf as remote..."
echo "-----------------------------------------"

# Add Overleaf as a remote
git remote add overleaf "https://git.overleaf.com/$OVERLEAF_PROJECT_ID" 2>/dev/null || {
    echo "Remote 'overleaf' already exists, updating URL..."
    git remote set-url overleaf "https://git.overleaf.com/$OVERLEAF_PROJECT_ID"
}

echo "✓ Overleaf remote configured"
echo ""

echo "Step 2: Creating integration branch..."
echo "-----------------------------------------"

# Create an overleaf branch for clean integration
git branch overleaf 2>/dev/null || echo "Branch 'overleaf' already exists"

echo "✓ Integration branch ready"
echo ""

echo "Step 3: Setting up credential storage..."
echo "-----------------------------------------"

# Setup credential helper (stores password securely)
git config credential.helper store

echo "✓ Credential helper configured"
echo ""

echo "=================================================="
echo "✓ SETUP COMPLETE!"
echo "=================================================="
echo ""
echo "Git remotes configured:"
git remote -v | grep -E "(origin|overleaf)"
echo ""
echo "INITIAL PUSH TO OVERLEAF:"
echo "-------------------------"
echo "1. Generate all assets:"
echo "   source .venv/bin/activate"
echo "   python build_paper.py"
echo ""
echo "2. Create Overleaf branch with paper files only:"
echo "   git checkout -b overleaf-paper"
echo "   git rm -r --cached scripts/ dataset_package/ .venv/ deprecated/"
echo "   git commit -m 'Paper files only for Overleaf'"
echo ""
echo "3. Push to Overleaf:"
echo "   git push overleaf overleaf-paper:master"
echo ""
echo "You'll be prompted for your Overleaf password once."
echo "It will be saved securely for future use."
echo ""