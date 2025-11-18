#!/usr/bin/env python3
"""
Generate Tables 1 and 2 with run-level aggregation.

Uses run-level metrics where each run's worst parameter is computed first,
then aggregated across runs. Failed runs are assigned 10^6 penalty.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Import shared metrics module
from shared_metrics import parse_result, parse_dict, calculate_individual_param_errors, calculate_run_level_metrics

# Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_PATH = ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"
OUTPUT_DIR = ROOT_DIR / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FAILURE_PENALTY = 1e6

def generate_table_1(df):
    """Generate Table 1: Overall Performance with run-level metrics."""
    print("\nGenerating Table 1: Overall Performance (run-level)...")

    methods = {
        'odepe': 'ODEPE-GPR',
        'odepe_polish': 'ODEPE-GPR (polished)',
        'sciml': 'SciML',
        'amigo2_0_10': 'AMIGO2 [0,10]',
        'amigo2_0_100': 'AMIGO2 [0,100]'
    }

    rows = []
    for run_name, display_name in methods.items():
        run_df = calculate_run_level_metrics(df, run_name)
        total = len(run_df)

        # Success rates (count runs with max_error < threshold)
        success_1pct = (run_df['max_error'] < 0.01).sum() / total * 100
        success_10pct = (run_df['max_error'] < 0.10).sum() / total * 100
        success_50pct = (run_df['max_error'] < 0.50).sum() / total * 100

        # Median and P90 of max error (includes failures as 10^6)
        median_max = np.median(run_df['max_error'])
        p90_max = np.percentile(run_df['max_error'], 90)

        # Time
        method_df = df[df['run'] == run_name]
        mean_time = method_df['time'].mean()

        rows.append({
            'Method': display_name,
            'Success@1% (%)': f"{success_1pct:.1f}",
            'Success@10% (%)': f"{success_10pct:.1f}",
            'Success@50% (%)': f"{success_50pct:.1f}",
            'Median Max Error (%)': f"{median_max*100:.2f}",
            'P90 Max Error (%)': f"{p90_max*100:.1f}",
        })

    # Create LaTeX table (timing removed to prevent overflow)
    latex = r"""\begin{table}[ht]
\centering
\caption{Overall performance with run-level aggregation. Success@X\%: fraction of runs where \emph{all} parameters have relative error $<$X\%. Median/P90 Max Error: For each run, the maximum parameter error is computed; the median and 90th percentile across all runs are reported. Failed runs are assigned $10^6$ penalty.}
\label{tab:overall_performance}
\begin{tabular}{lccccc}
\toprule
Method & Success@1\% & Success@10\% & Success@50\% & Median Max (\%) & P90 Max (\%) \\
\midrule
"""

    for row in rows:
        latex += f"{row['Method']} & {row['Success@1% (%)']} & {row['Success@10% (%)']} & {row['Success@50% (%)']} & {row['Median Max Error (%)']} & {row['P90 Max Error (%)']} \\\\\n"

    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

    # Save
    output_file = OUTPUT_DIR / "table_1_overall_performance_corrected.tex"
    with open(output_file, 'w') as f:
        f.write(latex)

    print(f"✓ Saved to {output_file}")

    # Print table for verification
    print("\nTable 1 values:")
    for row in rows:
        print(f"  {row['Method']:25} Success@10%: {row['Success@10% (%)']}%  Median Max: {row['Median Max Error (%)']}%")

def generate_table_2(df):
    """Generate Table 2: Performance by Noise Level with run-level metrics."""
    print("\nGenerating Table 2: Performance by Noise Level (run-level)...")

    methods = {
        'odepe': 'ODEPE-GPR',
        'odepe_polish': 'ODEPE-GPR (polished)',
        'sciml': 'SciML',
        'amigo2_0_10': 'AMIGO2 [0,10]',
        'amigo2_0_100': 'AMIGO2 [0,100]'
    }

    noise_levels = sorted(df['noise'].unique())

    # Collect data
    data = []
    for run_name, display_name in methods.items():
        row = {'Method': display_name}

        for noise in noise_levels:
            noise_df = df[(df['run'] == run_name) & (df['noise'] == noise)]
            run_df = calculate_run_level_metrics(noise_df, run_name)

            # Include all runs (failures have 10^6 penalty)
            if len(run_df) > 0:
                median_max = np.median(run_df['max_error']) * 100
            else:
                median_max = np.nan

            row[f'noise_{noise}'] = median_max

        data.append(row)

    # Create LaTeX table
    latex = r"""\begin{table}[ht]
\centering
\caption{Median worst-parameter error (\%) by noise level using run-level aggregation. For each run, the maximum parameter error is computed; the median across runs at each noise level is reported. Failed runs are assigned $10^6$ penalty.}
\label{tab:noise_performance}
\begin{tabular}{l"""

    for _ in noise_levels:
        latex += "c"
    latex += "}\n\\toprule\n"

    # Header
    latex += "Method"
    for noise in noise_levels:
        if noise == 0:
            latex += " & 0"
        else:
            latex += f" & $10^{{{int(np.log10(noise))}}}$"
    latex += " \\\\\n\\midrule\n"

    # Data rows
    for row in data:
        latex += row['Method']
        for noise in noise_levels:
            val = row[f'noise_{noise}']
            if np.isnan(val):
                latex += " & ---"
            else:
                latex += f" & {val:.2f}"
        latex += " \\\\\n"

    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

    # Save
    output_file = OUTPUT_DIR / "table_2_performance_by_noise_corrected.tex"
    with open(output_file, 'w') as f:
        f.write(latex)

    print(f"✓ Saved to {output_file}")

    # Print for verification
    print("\nTable 2 sample values (noise = 0.0):")
    for row in data:
        print(f"  {row['Method']:25} {row['noise_0.0']:.2f}%")

def main():
    print("=" * 80)
    print("GENERATING TABLES 1 AND 2 (RUN-LEVEL AGGREGATION)")
    print("=" * 80)

    print(f"\nLoading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows")

    generate_table_1(df)
    generate_table_2(df)

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)
    print(f"\nGenerated tables saved to: {OUTPUT_DIR}")
    print("\nTo use in paper:")
    print("  \\input{tables/table_1_overall_performance.tex}")
    print("  \\input{tables/table_2_performance_by_noise.tex}")
    print()

if __name__ == '__main__':
    main()
