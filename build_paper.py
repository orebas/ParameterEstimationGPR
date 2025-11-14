#!/usr/bin/env python3
"""
Automated Build Pipeline: Data → Tables/Figures → Compiled Paper

This script automates the entire workflow from raw data to compiled paper.pdf
"""

import subprocess
import shutil
from pathlib import Path
import sys

# Paths
ROOT_DIR = Path(__file__).parent
VIZ_DIR = ROOT_DIR / "visualization"
DATASET_DIR = ROOT_DIR / "dataset_package"
PAPER_DIR = ROOT_DIR / "paper"
VIZ_SCRIPTS = VIZ_DIR / "scripts"
VIZ_OUTPUTS = VIZ_DIR / "outputs"
VENV_PYTHON = VIZ_DIR / ".venv" / "bin" / "python3"

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ FAILED")
        print(f"STDERR:\n{result.stderr}")
        print(f"STDOUT:\n{result.stdout}")
        return False

    print(f"✓ SUCCESS")
    if result.stdout:
        # Print last 20 lines of output
        lines = result.stdout.strip().split('\n')
        for line in lines[-20:]:
            print(f"  {line}")
    return True

def step1_filter_data():
    """Step 1: Filter non-identifiable parameters (optional)."""
    print("\n" + "="*80)
    print("STEP 1: Filter Data (from combined_results.csv)")
    print("="*80)

    script = DATASET_DIR / "filter_nonidentifiable.py"
    if not script.exists():
        print(f"⚠ Script not found: {script}")
        print("  Skipping - assuming filtered data already exists")
        return True

    cmd = ["python3", str(script)]
    return run_command(cmd, "Filtering non-identifiable parameters")

def step2_generate_tables():
    """Step 2: Generate all tables."""
    print("\n" + "="*80)
    print("STEP 2: Generate Tables")
    print("="*80)

    # Generate corrected Tables 1 & 2
    cmd1 = [str(VENV_PYTHON), str(VIZ_SCRIPTS / "generate_corrected_tables_1_2.py")]
    if not run_command(cmd1, "Generating Tables 1-2 (corrected with 10^6 penalty)"):
        return False

    # Generate system performance tables (Tables 3-4)
    cmd2 = [str(VENV_PYTHON), str(VIZ_SCRIPTS / "generate_system_performance_tables.py")]
    if not run_command(cmd2, "Generating system performance tables (Tables 3-4)"):
        return False

    return True

def step3_generate_figures():
    """Step 3: Generate all figures."""
    print("\n" + "="*80)
    print("STEP 3: Generate Figures")
    print("="*80)

    # Check which figure generation scripts exist
    fig_scripts = [
        "generate_figure1_gpr_demo.py",
        "generate_all_final_figures.py"
    ]

    for script_name in fig_scripts:
        script = VIZ_SCRIPTS / script_name
        if script.exists():
            cmd = [str(VENV_PYTHON), str(script)]
            if not run_command(cmd, f"Running {script_name}"):
                print(f"  ⚠ {script_name} failed, continuing...")
        else:
            print(f"  ⚠ Script not found: {script_name}, skipping")

    return True

def step4_copy_outputs():
    """Step 4: Copy generated outputs to paper directory."""
    print("\n" + "="*80)
    print("STEP 4: Copy Outputs to Paper Directory")
    print("="*80)

    # Tables to copy
    tables = [
        ("table_1_overall_performance_corrected.tex", "table_1_overall_performance.tex"),
        ("table_2_performance_by_noise_corrected.tex", "table_2_performance_by_noise.tex"),
        ("system_performance_low_noise.tex", "system_performance_low_noise.tex"),
        ("system_performance_high_noise.tex", "system_performance_high_noise.tex"),
    ]

    print("\nCopying tables:")
    for src_name, dst_name in tables:
        src = VIZ_OUTPUTS / "tables" / src_name
        dst = PAPER_DIR / "tables" / dst_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✓ {src_name} → {dst_name}")
        else:
            print(f"  ⚠ Source not found: {src_name}")

    # Figures to copy
    figures_dir = VIZ_OUTPUTS / "figures" / "corrected"
    if figures_dir.exists():
        print("\nCopying figures:")
        for fig_file in figures_dir.glob("*.pdf"):
            dst = PAPER_DIR / "figures" / fig_file.name
            shutil.copy2(fig_file, dst)
            print(f"  ✓ {fig_file.name}")
    else:
        print(f"  ⚠ Figures directory not found: {figures_dir}")

    return True

def step5_compile_latex():
    """Step 5: Compile LaTeX paper."""
    print("\n" + "="*80)
    print("STEP 5: Compile LaTeX Paper")
    print("="*80)

    # Run pdflatex multiple times for cross-references
    commands = [
        (["pdflatex", "-interaction=nonstopmode", "paper.tex"], "First pdflatex pass"),
        (["bibtex", "paper"], "BibTeX bibliography"),
        (["pdflatex", "-interaction=nonstopmode", "paper.tex"], "Second pdflatex pass"),
        (["pdflatex", "-interaction=nonstopmode", "paper.tex"], "Third pdflatex pass (final)"),
    ]

    for cmd, desc in commands:
        if not run_command(cmd, desc, cwd=PAPER_DIR):
            print(f"  ⚠ {desc} failed, but continuing...")

    # Check if PDF was created
    pdf_file = PAPER_DIR / "paper.pdf"
    if pdf_file.exists():
        print(f"\n✓ SUCCESS: Paper compiled to {pdf_file}")
        return True
    else:
        print(f"\n✗ FAILED: PDF not created")
        return False

def main():
    print("="*80)
    print("AUTOMATED PAPER BUILD PIPELINE")
    print("="*80)
    print(f"\nRoot directory: {ROOT_DIR}")

    # Verify environment
    if not VENV_PYTHON.exists():
        print(f"\n✗ ERROR: Python venv not found at {VENV_PYTHON}")
        print("Please ensure the visualization environment is set up.")
        sys.exit(1)

    # Run pipeline steps
    success = True

    if not step1_filter_data():
        print("\n⚠ Step 1 had issues, but continuing...")

    if not step2_generate_tables():
        print("\n✗ Step 2 FAILED - stopping")
        success = False
    else:
        if not step3_generate_figures():
            print("\n⚠ Step 3 had issues, but continuing...")

        if not step4_copy_outputs():
            print("\n✗ Step 4 FAILED - stopping")
            success = False
        else:
            if not step5_compile_latex():
                print("\n✗ Step 5 FAILED")
                success = False

    # Final summary
    print("\n" + "="*80)
    if success:
        print("✓ BUILD COMPLETE!")
        print(f"✓ Paper compiled: {PAPER_DIR / 'paper.pdf'}")
    else:
        print("✗ BUILD FAILED - see errors above")
    print("="*80 + "\n")

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
