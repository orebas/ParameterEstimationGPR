# Code Audit: Figure Generation Scripts

**Date:** 2025-11-13
**Auditor:** Claude Code

## Issues Found

### ❌ CRITICAL: Inconsistent Calculation Methods

**Location:** `visualization/scripts/data_loading.py` + all figure scripts

**Problem:**
1. **Tables** now use **Option B** (pooled parameter errors)
2. **Figures** still use **Method A** (per-run mean errors) via DataLoader

**Evidence:**
- `data_loading.py:151` - Returns `np.mean(errors)` per run
- `data_loading.py:174` - Stores as `mean_relative_error` column
- `generate_all_final_figures.py:33-37` - Uses pre-computed `mean_relative_error`
- `generate_all_final_figures.py:41` - Calculates statistics from `mean_relative_error`

**Impact:**
- Figures show different numbers than tables
- Violates single source of truth principle
- Not reproducible - changing calculation method only affects tables

---

### ❌ CRITICAL: Multiple Data Sources

**Location:** Multiple scripts

**Problem:**
- Tables read from: `ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"`
- Figures use: `DataLoader` which wraps the same file but adds Method A pre-processing

**Evidence:**
- `generate_corrected_tables_1_2.py:22` - Direct CSV read
- `generate_system_performance_tables.py:25` - Direct CSV read
- `generate_all_final_figures.py:20` - Uses DataLoader
- `data_loading.py:25` - Same CSV path but pre-processes

**Impact:**
- Two different code paths to same data
- DataLoader adds derived columns that hide calculation method
- Changes to data loading logic must be made in two places

---

### ⚠️ WARNING: Hard-coded Threshold

**Location:** `data_loading.py:179`

```python
metrics['is_successful'] = (
    row['has_result'] and
    metrics['mean_relative_error'] < 0.5  # 50% threshold
)
```

**Problem:**
- Hard-coded 0.5 threshold
- Should reference configuration or constant

---

### ⚠️ WARNING: Penalty Value Inconsistency

**Location:** Multiple files

**Problem:**
- Tables: `PENALTY = 1e6` (explicit constant)
- Figures: `penalty=1e6` (default parameter)
- DataLoader: Returns `np.inf` for failures (line 135, 139)

**Evidence:**
- `audit_all_tables.py:18` - `PENALTY = 1e6`
- `generate_corrected_tables_1_2.py:26` - `PENALTY = 1e6`
- `generate_all_final_figures.py:33` - `penalty=1e6` (parameter)
- `data_loading.py:135, 139` - Returns `np.inf`

**Impact:**
- Inconsistent handling of failures
- DataLoader uses `inf`, tables use `1e6`
- This affects sorting and statistical calculations differently

---

### ✅ GOOD: Single CSV Source

**Location:** All scripts

**Finding:**
All scripts now correctly reference:
```python
ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"
```

No hard-coded data values found.

---

## Recommendations

### 1. **CRITICAL: Unify Calculation Method**

Create a shared module with Option B calculation:

```python
# shared_metrics.py
def calculate_pooled_median_error(df, run_name, penalty=1e6):
    """Single source of truth for Option B calculation."""
    # ... implementation ...
```

Use in both:
- Table generation scripts
- Figure generation scripts (replace DataLoader usage)

### 2. **CRITICAL: Eliminate DataLoader or Update It**

**Option A:** Stop using DataLoader in figures, read CSV directly
**Option B:** Update DataLoader to use Option B calculations

Recommend Option A - simpler, less abstraction.

### 3. **HIGH: Create Constants Module**

```python
# constants.py
PENALTY = 1e6
SUCCESS_THRESHOLDS = {
    'SR-1': 0.01,
    'SR-10': 0.10,
    'SR-50': 0.50
}
```

### 4. **MEDIUM: Consolidate Data Loading**

Either:
- Remove DataLoader entirely, use direct CSV reads everywhere
- Or make DataLoader the ONLY way to access data

Current mixed approach is error-prone.

---

## Summary

**Total Issues:** 6
- Critical: 2 (inconsistent calculations, multiple data sources)
- Warning: 2 (hard-coded threshold, penalty inconsistency)
- Good: 2 (single CSV source, no hard-coded data)

**Next Steps:**
1. Fix figure scripts to use Option B
2. Create shared metrics module
3. Eliminate or update DataLoader
4. Test full pipeline end-to-end
