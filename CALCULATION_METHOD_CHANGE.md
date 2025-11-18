# ⚠️ IMPORTANT: CALCULATION METHOD CHANGE

**Date:** 2025-11-13

## Critical Change

All tables and figures were changed from **Method A** to **Method B** for error calculations.

### Method A (Previous - Per-Run Median)
- For each run: calculate mean relative error across all parameters/states
- Assign 10^6 penalty for failed runs
- Take median of per-run means
- **This is what the original paper tables used**

### Method B (Current - Pooled Parameters)
- Pool ALL individual parameter errors from ALL runs
- For failed runs: add 10^6 penalty for EACH parameter
- Take median of entire pool
- **Simpler, but produces significantly different results**

## Impact

### Table 1 (Overall Performance)
- Success rates: **+4-12% higher** with Method B
- Median errors: **2-10x lower** with Method B
  - Example: ODEPE-GPR median error 0.21% → 0.08%

### Table 2 (Performance by Noise)
- High noise (10^-2) errors: **~50-60% lower** with Method B
  - Example: ODEPE-GPR at 10^-2: 67.88% → 28.95%

### Tables 3 & 4 (System Performance)
- Similar magnitude changes expected

## Action Required

**BEFORE SUBMISSION:** This needs to be reviewed with colleagues.
- Verify which method matches the paper's described methodology
- Ensure consistency across all results
- Update paper text to accurately describe Method B if keeping this change

## Files Modified
- `visualization/scripts/generate_corrected_tables_1_2.py`
- `visualization/scripts/generate_system_performance_tables.py`
- `audit_all_tables.py`
- All table files regenerated
