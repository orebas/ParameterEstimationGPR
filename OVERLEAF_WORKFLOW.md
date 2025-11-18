# Overleaf + Local Repository Workflow

## The Challenge

Your paper has two needs that conflict:
1. **Computational reproducibility** - Generate tables/figures from data via Python
2. **Collaborative editing** - Work with advisor on Overleaf (which can't run Python)

## The Solution: Dual Workflow

### 🏠 Local Repository (GitHub)
**Purpose:** Source of truth for data, code, and generation
- Contains: Raw data, Python scripts, build system
- Use for: Regenerating tables/figures when data changes

### ☁️ Overleaf
**Purpose:** Collaborative text editing with advisor
- Contains: Static snapshot (pre-generated tables/figures)
- Use for: Writing, editing text, getting feedback

## Workflow Diagrams

### Initial Setup
```
Local Repo
    ↓
./prepare_for_overleaf.sh
    ↓
overleaf_package.zip
    ↓
Upload to Overleaf
```

### Ongoing Work

```
Edit text on Overleaf ←→ Download
                          ↓
                    ./sync_from_overleaf.sh
                          ↓
                    Local Repo
                          ↓
              Change data/regenerate?
                    ↙          ↘
                  No            Yes
                  ↓              ↓
            git commit    python build_paper.py
                          ./prepare_for_overleaf.sh
                               ↓
                         Re-upload to Overleaf
```

## Step-by-Step Instructions

### 1️⃣ Initial Overleaf Setup

```bash
# Generate everything fresh
source .venv/bin/activate
python build_paper.py

# Create Overleaf package
./prepare_for_overleaf.sh

# This creates:
# - overleaf_package/ directory
# - overleaf_package.zip
```

**Upload to Overleaf:**
1. Go to overleaf.com
2. New Project → Upload Project
3. Upload `overleaf_package.zip`
4. Share with advisor

### 2️⃣ Text Editing Phase (Overleaf)

Work with advisor on Overleaf for:
- Writing/editing text
- Adjusting formatting
- Adding citations
- Reviewer responses

**DO NOT** on Overleaf:
- Try to regenerate tables/figures
- Modify table numbers manually
- Add Python code

### 3️⃣ Syncing Text Changes Back

After editing on Overleaf:

```bash
# Download from Overleaf
# Menu → Download → Source → (save as overleaf_download.zip)

# Extract
unzip overleaf_download.zip -d overleaf_download/

# Sync back to local
./sync_from_overleaf.sh

# Review changes
git diff paper/

# Commit
git commit -am "Sync text edits from Overleaf session"
git push
```

### 4️⃣ Updating Data/Figures

When you need to change data or regenerate:

```bash
# Make data/script changes locally
vim scripts/generate_corrected_tables_1_2.py  # or whatever

# Regenerate everything
source .venv/bin/activate
python build_paper.py

# Prepare new Overleaf package
./prepare_for_overleaf.sh

# Upload NEW VERSION to Overleaf
# Either create new project or update existing files
```

## Important Files to Track

### Text Files (sync both ways)
- `paper/paper.tex` - Main document
- `paper/references.bib` - Bibliography

### Generated Files (local → Overleaf only)
- `paper/tables/*.tex` - Generated tables
- `paper/figures/*.pdf` - Generated figures

### Never Upload to Overleaf
- `*.csv` - Data files
- `*.py` - Python scripts
- `.venv/` - Virtual environment
- `outputs/` - Intermediate files

## Common Scenarios

### Scenario 1: "Just fixing typos"
- Edit on Overleaf
- Download & sync when done
- No need to regenerate

### Scenario 2: "Reviewer wants different statistics"
- Change locally in Python scripts
- Run `build_paper.py`
- Run `prepare_for_overleaf.sh`
- Re-upload to Overleaf

### Scenario 3: "Advisor rewrote introduction"
- Work happens on Overleaf
- Download & sync back
- Commit to git for version control

### Scenario 4: "New experimental data arrived"
- Update `dataset_package/combined_results.csv`
- Run full pipeline locally
- Prepare and upload new Overleaf version
- Continue text editing there

## Tips & Warnings

### ✅ DO
- Keep git commits frequent
- Tag versions before major Overleaf sessions
- Maintain clear communication about who's editing
- Use Overleaf's commenting feature

### ⚠️ DON'T
- Edit the same text in both places simultaneously
- Manually edit generated table values
- Try to merge complex conflicts manually
- Upload Python files to Overleaf

### 🔄 Conflict Resolution

If you accidentally edit in both places:
1. Back up both versions
2. Decide which is authoritative
3. Manually merge specific changes
4. Test compile in both environments

## File Inventory for Overleaf

Your Overleaf package will contain:

```
overleaf_package/
├── paper.tex           (main document)
├── references.bib      (bibliography)
├── README.txt          (instructions)
├── tables/
│   ├── table_1_overall_performance.tex
│   ├── table_2_performance_by_noise.tex
│   ├── system_performance_low_noise.tex
│   ├── system_performance_high_noise.tex
│   ├── success_1pct_by_noise.tex
│   ├── success_10pct_by_noise.tex
│   ├── success_50pct_by_noise.tex
│   ├── runtime_table.tex
│   └── observables_table.tex
└── figures/
    ├── figure1_gpr_demo.pdf
    ├── noise_degradation.pdf
    ├── pareto_frontier.pdf
    ├── performance_heatmap.pdf
    └── success_rate_curves.pdf
```

Total: ~2MB (perfect for Overleaf)

## Quick Reference

| Task | Command |
|------|---------|
| Generate everything | `python build_paper.py` |
| Prepare for Overleaf | `./prepare_for_overleaf.sh` |
| Sync from Overleaf | `./sync_from_overleaf.sh` |
| Check changes | `git diff paper/` |
| Activate environment | `source .venv/bin/activate` |

## Questions?

The key insight: **Tables/figures flow one-way** (local → Overleaf), while **text flows both ways**.

This keeps your computational pipeline intact while enabling collaborative editing!