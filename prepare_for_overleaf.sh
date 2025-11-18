#!/bin/bash
# Prepare static package for Overleaf
# This creates overleaf/ directory with all needed files

set -e

echo "=================================================="
echo "Preparing Paper for Overleaf"
echo "=================================================="
echo ""

# Create overleaf directory
OVERLEAF_DIR="overleaf_package"
rm -rf $OVERLEAF_DIR
mkdir -p $OVERLEAF_DIR

echo "Step 1: Generating all tables and figures..."
echo "-----------------------------------------"

# Activate venv and run build to ensure everything is up-to-date
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠️  Warning: No .venv found, using system Python"
fi

# Generate all outputs
echo "Generating tables..."
python3 scripts/generate_corrected_tables_1_2.py || echo "  Warning: Table generation failed"
python3 scripts/generate_system_performance_tables.py || echo "  Warning: System tables failed"

echo "Generating figures..."
python3 scripts/generate_figure1_gpr_demo.py || echo "  Warning: Figure 1 generation failed"
python3 scripts/generate_all_final_figures.py || echo "  Warning: Figure generation failed"

echo ""
echo "Step 2: Copying paper source files..."
echo "-----------------------------------------"

# Copy main LaTeX file
cp paper/paper.tex $OVERLEAF_DIR/
cp paper/references.bib $OVERLEAF_DIR/
echo "✓ Copied paper.tex and references.bib"

# Copy tables (from outputs to paper location first)
echo ""
echo "Step 3: Copying tables..."
echo "-----------------------------------------"
mkdir -p $OVERLEAF_DIR/tables

# Copy from outputs/tables to paper/tables (if newer)
if [ -d "outputs/tables" ]; then
    for table in outputs/tables/*.tex; do
        if [ -f "$table" ]; then
            filename=$(basename "$table")
            # Map corrected names to expected names
            case $filename in
                "table_1_overall_performance_corrected.tex")
                    cp "$table" "paper/tables/table_1_overall_performance.tex"
                    echo "  Updated table_1_overall_performance.tex"
                    ;;
                "table_2_performance_by_noise_corrected.tex")
                    cp "$table" "paper/tables/table_2_performance_by_noise.tex"
                    echo "  Updated table_2_performance_by_noise.tex"
                    ;;
                *)
                    if [ -f "paper/tables/$filename" ] || [[ "$filename" == system_* ]] || [[ "$filename" == success_* ]]; then
                        cp "$table" "paper/tables/$filename" 2>/dev/null || true
                    fi
                    ;;
            esac
        fi
    done
fi

# Now copy all tables to Overleaf package
cp paper/tables/*.tex $OVERLEAF_DIR/tables/ 2>/dev/null || true
echo "✓ Copied $(ls -1 $OVERLEAF_DIR/tables/*.tex 2>/dev/null | wc -l) table files"

echo ""
echo "Step 4: Copying figures..."
echo "-----------------------------------------"
mkdir -p $OVERLEAF_DIR/figures

# Copy from outputs/figures if they exist
if [ -d "outputs/figures/corrected" ]; then
    cp outputs/figures/corrected/*.pdf paper/figures/ 2>/dev/null || true
fi

# Copy all PDF figures
cp paper/figures/*.pdf $OVERLEAF_DIR/figures/ 2>/dev/null || true
echo "✓ Copied $(ls -1 $OVERLEAF_DIR/figures/*.pdf 2>/dev/null | wc -l) figure files"

echo ""
echo "Step 5: Creating Overleaf README..."
echo "-----------------------------------------"

cat > $OVERLEAF_DIR/README.txt << 'EOF'
GPR Parameter Estimation Paper - Overleaf Package
==================================================

This is a STATIC snapshot for Overleaf collaborative editing.

IMPORTANT NOTES:
----------------
1. Tables and figures are PRE-GENERATED
2. To regenerate with new data, use the local repository
3. Main file: paper.tex

FILES INCLUDED:
--------------
- paper.tex         : Main LaTeX document
- references.bib    : Bibliography
- tables/*.tex      : Pre-generated tables (9 files)
- figures/*.pdf     : Pre-generated figures (5 files)

TO UPLOAD TO OVERLEAF:
----------------------
1. Create new project on Overleaf
2. Upload all files (maintaining directory structure)
3. Set paper.tex as main document
4. Compile

TO SYNC CHANGES BACK:
--------------------
After editing on Overleaf, download and copy paper.tex
and references.bib back to the main repository.

REGENERATING TABLES/FIGURES:
----------------------------
Use the main repository with:
  source .venv/bin/activate
  python build_paper.py

Then run prepare_for_overleaf.sh again.
EOF

echo "✓ Created README"

echo ""
echo "Step 6: Creating ZIP for easy upload..."
echo "-----------------------------------------"

cd $OVERLEAF_DIR
zip -r ../overleaf_package.zip . -q
cd ..
echo "✓ Created overleaf_package.zip"

echo ""
echo "=================================================="
echo "✓ OVERLEAF PACKAGE READY!"
echo "=================================================="
echo ""
echo "Package contents:"
echo "  Directory: $OVERLEAF_DIR/"
echo "  ZIP file:  overleaf_package.zip"
echo ""
echo "File counts:"
echo "  Tables:  $(ls -1 $OVERLEAF_DIR/tables/*.tex 2>/dev/null | wc -l)"
echo "  Figures: $(ls -1 $OVERLEAF_DIR/figures/*.pdf 2>/dev/null | wc -l)"
echo ""
echo "To upload to Overleaf:"
echo "  1. Go to overleaf.com"
echo "  2. Create 'New Project' → 'Upload Project'"
echo "  3. Upload overleaf_package.zip"
echo ""
echo "Alternative: Upload files manually from $OVERLEAF_DIR/"
echo ""