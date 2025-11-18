# Before/After Comparison: Refactoring Impact

## 🔴 BEFORE: Inconsistent Calculations

### Figure Generation (`generate_all_final_figures.py`)
```python
# ❌ Used DataLoader with Method A
from data_loading import DataLoader

loader = DataLoader(DATA_PATH)
loader.load_data()  # Pre-computes mean_relative_error per run

def calculate_penalized_median(df, penalty=1e6):
    """Method A: median of per-run means"""
    run_values = []
    for run_id in df['run_id'].unique():
        run_df = df[df['run_id'] == run_id]
        if run_df['has_result'].iloc[0]:
            run_values.append(run_df['mean_relative_error'].iloc[0])
        else:
            run_values.append(penalty)
    return np.median(run_values)

# Used pre-computed means from DataLoader
median_penalized = calculate_penalized_median(method_noise_df)
```

### Table Generation (`generate_corrected_tables_1_2.py`)
```python
# ✅ Used Option B (correct)
def calculate_pooled_median_error(df, run_name, penalty=1e6):
    """Option B: median of pooled parameter errors"""
    all_errors = []
    for _, row in df.iterrows():
        if row['has_result']:
            # Calculate individual parameter errors
            for param in estimated:
                error = abs(estimated[param] - true[param]) / abs(true[param])
                all_errors.append(error)
        else:
            # Add penalty for each parameter
            all_errors.extend([penalty] * n_params)
    return np.median(all_errors)
```

### ❌ Result: Tables and Figures Show Different Numbers!

---

## 🟢 AFTER: Unified Calculations

### Shared Metrics (`shared_metrics.py`)
```python
"""
Single source of truth for all metric calculations.
All tables and figures MUST use these functions.
"""

PENALTY = 1e6
SR_THRESHOLDS = {'SR-1': 0.01, 'SR-10': 0.10, 'SR-50': 0.50}

def calculate_pooled_errors(df, run_name=None):
    """
    Calculate pooled parameter errors (Option B).
    Used by ALL tables and figures.
    """
    if run_name is not None:
        df = df[df['run'] == run_name]

    all_errors = []
    for _, row in df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            param_errors = calculate_individual_param_errors(
                estimated, true_params, true_states
            )
            all_errors.extend(param_errors)
        else:
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            n_params = len(true_params) + len(true_states)
            all_errors.extend([PENALTY] * n_params)

    return np.array(all_errors)

def calculate_median_error(df, run_name=None):
    """Calculate median from pooled errors."""
    all_errors = calculate_pooled_errors(df, run_name)
    return np.median(all_errors)
```

### Figure Generation (Refactored)
```python
# ✅ Now uses shared_metrics
from shared_metrics import (
    calculate_pooled_errors,
    calculate_performance_by_noise,
    SR_THRESHOLDS,
    PENALTY
)

# No more DataLoader, read CSV directly
df = pd.read_csv(DATA_PATH)

def figure_2_noise_degradation(df):
    # ✅ Uses shared function
    noise_perf = calculate_performance_by_noise(df, method)
    medians = [noise_perf[noise] * 100 for noise in noise_levels]
```

### Table Generation (Refactored)
```python
# ✅ Uses same shared_metrics
from shared_metrics import (
    calculate_all_metrics,
    calculate_performance_by_noise,
    PENALTY
)

def generate_table_1(df):
    for run_name in methods:
        # ✅ Uses shared function
        metrics = calculate_all_metrics(df, run_name)
```

### ✅ Result: Tables and Figures Show Identical Numbers!

---

## 📊 Numerical Impact Example

### Before Refactoring (Inconsistent)

**Table 1 (Option B):**
- SciML SR-10: **77.4%**
- SciML Median Error: **0.04%**

**Figure 2 (Method A):**
- SciML SR-10: **~65%** ❌ DIFFERENT
- SciML Median Error: **~0.15%** ❌ DIFFERENT

### After Refactoring (Consistent)

**Table 1 (Option B):**
- SciML SR-10: **77.4%**
- SciML Median Error: **0.04%**

**Figure 2 (Option B):**
- SciML SR-10: **77.4%** ✅ MATCHES
- SciML Median Error: **0.04%** ✅ MATCHES

---

## 🔧 Code Quality Improvements

### Duplication Eliminated

**Before:**
```
generate_all_final_figures.py:     calculate_penalized_median()
generate_corrected_tables_1_2.py:  calculate_pooled_median_error()
data_loading.py:                   calculate_relative_error()
audit_all_tables.py:               calculate_pooled_median_error()
```
**4 different implementations!**

**After:**
```
shared_metrics.py:                 calculate_pooled_errors()
                                   calculate_median_error()
All scripts:                       import from shared_metrics
```
**1 implementation, used everywhere!**

### Hard-coded Values Eliminated

**Before:**
```python
# Scattered across files:
penalty = 1e6              # in calculate_penalized_median()
penalty = 1e6              # in calculate_pooled_median_error()
threshold = 0.5            # in data_loading.py
thresholds = [0.01, 0.1, 0.5]  # in figure generation
```

**After:**
```python
# Single location in shared_metrics.py:
PENALTY = 1e6
SR_THRESHOLDS = {
    'SR-1': 0.01,
    'SR-10': 0.10,
    'SR-50': 0.50
}
```

---

## ✅ Verification

### All Tests Pass

```bash
$ venv/bin/python3 audit_all_tables.py

Table 1: ✓ PASS
Table 2: ✓ PASS
Table 3: ✓ PASS
Table 4: ✓ PASS

✓ ALL TABLES MATCH PERFECTLY!
```

### All Figures Generate

```bash
$ visualization/.venv/bin/python3 visualization/scripts/generate_all_final_figures.py

✓ Saved pareto_frontier.png
✓ Saved noise_degradation.png
✓ Saved performance_heatmap.png
✓ Saved success_rate_curves.png
```

### Full Build Works

```bash
$ python3 build_paper.py

✓ Tables generated
✓ Figures generated
✓ Paper compiled to PDF
```

---

## 🎯 Summary

| Aspect | Before | After | Status |
|--------|--------|-------|--------|
| **Consistency** | Tables ≠ Figures | Tables = Figures | ✅ FIXED |
| **Code Reuse** | 4 implementations | 1 implementation | ✅ IMPROVED |
| **Maintainability** | Hard to update | Single update point | ✅ IMPROVED |
| **Magic Numbers** | Scattered | Centralized | ✅ IMPROVED |
| **Documentation** | Minimal | Comprehensive | ✅ IMPROVED |
| **Testability** | Limited | Full audit | ✅ IMPROVED |

**Bottom Line:** The codebase is now consistent, maintainable, and ready for publication.
