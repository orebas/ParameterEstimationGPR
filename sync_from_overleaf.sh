#!/bin/bash
# Sync changes from Overleaf back to main repository
# Use after downloading project from Overleaf

set -e

echo "=================================================="
echo "Syncing Changes from Overleaf"
echo "=================================================="
echo ""

# Check if overleaf download exists
if [ ! -d "overleaf_download" ]; then
    echo "ERROR: overleaf_download/ directory not found!"
    echo ""
    echo "Instructions:"
    echo "1. Download project ZIP from Overleaf (Menu → Download → Source)"
    echo "2. Extract to overleaf_download/ directory"
    echo "3. Run this script again"
    echo ""
    exit 1
fi

echo "Found overleaf_download/ directory"
echo ""

# Backup current files
echo "Step 1: Creating backups..."
echo "-----------------------------------------"
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="backups/backup_$timestamp"
mkdir -p $backup_dir

cp paper/paper.tex $backup_dir/ 2>/dev/null || true
cp paper/references.bib $backup_dir/ 2>/dev/null || true
echo "✓ Backed up to $backup_dir"

echo ""
echo "Step 2: Syncing text changes..."
echo "-----------------------------------------"

# Copy paper source files back
if [ -f "overleaf_download/paper.tex" ]; then
    cp overleaf_download/paper.tex paper/paper.tex
    echo "✓ Updated paper.tex"
else
    echo "⚠️  paper.tex not found in download"
fi

if [ -f "overleaf_download/references.bib" ]; then
    cp overleaf_download/references.bib paper/references.bib
    echo "✓ Updated references.bib"
else
    echo "⚠️  references.bib not found in download"
fi

echo ""
echo "Step 3: Checking for conflicts..."
echo "-----------------------------------------"

# Show what changed
echo "Changes in paper.tex:"
diff -u $backup_dir/paper.tex paper/paper.tex 2>/dev/null | head -20 || echo "  (no changes or new file)"

echo ""
echo "=================================================="
echo "✓ SYNC COMPLETE!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Review changes with: git diff paper/"
echo "2. If you modified data/calculations:"
echo "   - Update scripts as needed"
echo "   - Run: python build_paper.py"
echo "   - Run: ./prepare_for_overleaf.sh"
echo "3. Commit changes: git commit -am 'Sync from Overleaf'"
echo ""
echo "Backup saved to: $backup_dir"
echo ""