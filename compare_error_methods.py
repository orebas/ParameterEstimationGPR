#!/usr/bin/env python3
"""
Comparison script to determine which error calculation method was actually used in the paper.

Tests two methods:
1. Per-run median: Calculate mean error per run, then median across runs (with 10^6 penalty)
2. Per-parameter pooling: Pool all individual parameter errors, then median (with 10^6 penalty)

Compares results to the inline table values in paper.tex to determine ground truth.
"""

import pandas as pd
import numpy as np
import ast
from pathlib import Path

# Paper's inline Table 1 values (median error in %)
PAPER_TABLE1_VALUES = {
    'odepe': 0.26,
    'odepe_polish': 0.13,
    'sciml': 0.44,
    'amigo2_0_10': 0.15,
    'amigo2_0_100': 0.38
}

def parse_result(result_str):
    """Parse result column to extract estimated parameters."""
    if pd.isna(result_str) or result_str == '[]':
        return {}
    result_list = ast.literal_eval(result_str)
    return {param: float(value) for param, value in result_list}

def parse_true_params(params_str):
    """Parse true parameters column."""
    if pd.isna(params_str):
        return {}
    return ast.literal_eval(params_str)

def parse_true_states(states_str):
    """Parse true states column."""
    if pd.isna(states_str) or states_str == '{}':
        return {}
    return ast.literal_eval(states_str)

def calculate_per_parameter_errors(estimated, true_params, true_states):
    """
    Calculate relative error for each parameter and state individually.
    Returns a list of individual errors (one per parameter/state).
    """
    errors = []

    # Combine parameters and states
    all_true = {**true_params, **true_states}

    for key in all_true:
        if key not in estimated:
            continue

        true_val = all_true[key]
        est_val = estimated[key]

        if abs(true_val) < 1e-10:
            error = abs(est_val - true_val)
        else:
            error = abs(est_val - true_val) / abs(true_val)

        errors.append(error)

    return errors

def calculate_mean_error_per_run(estimated, true_params, true_states):
    """
    Calculate mean relative error for a single run (averaging across parameters/states).
    Returns a single number.
    """
    errors = calculate_per_parameter_errors(estimated, true_params, true_states)
    if len(errors) == 0:
        return np.nan
    return np.mean(errors)

def method_a_per_run_median(df, run_name, penalty=1e6):
    """
    Method A: Per-run median (current implementation).

    1. For each run, calculate mean error across parameters
    2. Assign penalty to failed runs
    3. Take median of per-run means
    """
    method_df = df[df['run'] == run_name].copy()

    # Calculate mean error per run
    per_run_errors = []
    for _, row in method_df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_true_params(row['true_parameters'])
            true_states = parse_true_states(row['true_states'])
            mean_error = calculate_mean_error_per_run(estimated, true_params, true_states)
            per_run_errors.append(mean_error if not np.isnan(mean_error) else penalty)
        else:
            per_run_errors.append(penalty)

    median_value = np.median(per_run_errors)
    return median_value, per_run_errors

def method_b_per_parameter_pooling(df, run_name, penalty=1e6):
    """
    Method B: Per-parameter pooling.

    1. For each run, for each parameter, calculate individual error
    2. Pool ALL parameter errors across ALL runs
    3. For failed runs, add penalty for each parameter
    4. Take median of entire pool
    """
    method_df = df[df['run'] == run_name].copy()

    # Collect all individual parameter errors
    all_param_errors = []

    for _, row in method_df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_true_params(row['true_parameters'])
            true_states = parse_true_states(row['true_states'])
            param_errors = calculate_per_parameter_errors(estimated, true_params, true_states)
            all_param_errors.extend(param_errors)
        else:
            # For failed runs, add penalty for each parameter that should have been estimated
            true_params = parse_true_params(row['true_parameters'])
            true_states = parse_true_states(row['true_states'])
            num_params = len(true_params) + len(true_states)
            all_param_errors.extend([penalty] * num_params)

    median_value = np.median(all_param_errors)
    return median_value, all_param_errors

def main():
    print("=" * 80)
    print("ERROR CALCULATION METHOD COMPARISON")
    print("=" * 80)

    # Load data
    data_path = Path('dataset_package/combined_results_filtered.csv')
    print(f"\nLoading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows")

    # Test both methods for each software
    methods_to_test = ['odepe', 'odepe_polish', 'sciml', 'amigo2_0_10', 'amigo2_0_100']

    results = []

    for run_name in methods_to_test:
        print(f"\n{'=' * 80}")
        print(f"Testing: {run_name.upper()}")
        print(f"{'=' * 80}")

        # Method A: Per-run median
        median_a, errors_a = method_a_per_run_median(df, run_name)
        print(f"\nMethod A (Per-run median):")
        print(f"  Number of values: {len(errors_a)} (one per run)")
        print(f"  Median value: {median_a:.6f} ({median_a * 100:.2f}%)")

        # Method B: Per-parameter pooling
        median_b, errors_b = method_b_per_parameter_pooling(df, run_name)
        print(f"\nMethod B (Per-parameter pooling):")
        print(f"  Number of values: {len(errors_b)} (one per parameter across all runs)")
        print(f"  Median value: {median_b:.6f} ({median_b * 100:.2f}%)")

        # Compare to paper value
        paper_value = PAPER_TABLE1_VALUES.get(run_name, None)
        if paper_value:
            print(f"\nPaper Table 1 value: {paper_value}%")
            diff_a = abs((median_a * 100) - paper_value)
            diff_b = abs((median_b * 100) - paper_value)
            print(f"  Difference from Method A: {diff_a:.2f} percentage points")
            print(f"  Difference from Method B: {diff_b:.2f} percentage points")

            if diff_a < diff_b:
                print(f"  ✓ Method A is CLOSER to paper value")
                closer = 'A'
            else:
                print(f"  ✓ Method B is CLOSER to paper value")
                closer = 'B'
        else:
            closer = '?'

        results.append({
            'method': run_name,
            'paper_value': paper_value,
            'method_a': median_a * 100,
            'method_b': median_b * 100,
            'closer': closer
        })

    # Summary table
    print(f"\n{'=' * 80}")
    print("SUMMARY COMPARISON")
    print(f"{'=' * 80}\n")

    summary_df = pd.DataFrame(results)
    print(summary_df.to_string(index=False))

    # Determine which method was likely used
    print(f"\n{'=' * 80}")
    print("CONCLUSION")
    print(f"{'=' * 80}")

    if all(r['closer'] == 'A' for r in results):
        print("\n✓ Method A (Per-run median) matches ALL paper values")
        print("  This is what was actually used in the paper.")
    elif all(r['closer'] == 'B' for r in results):
        print("\n✓ Method B (Per-parameter pooling) matches ALL paper values")
        print("  This is what was actually used in the paper.")
    else:
        print("\n⚠ Mixed results - neither method consistently matches paper values")
        print("  Further investigation needed.")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
