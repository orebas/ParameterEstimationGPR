#!/usr/bin/env python3
"""
Generate System Performance Tables for Paper
============================================
Creates two tables showing performance by system at low vs high noise
using run-level aggregation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import warnings
warnings.filterwarnings('ignore')

# Import shared metrics module
from shared_metrics import parse_result, parse_dict, calculate_individual_param_errors

# Configure paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
CONFIG_DIR = ROOT_DIR / "config"
OUTPUT_DIR = ROOT_DIR / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"

FAILURE_PENALTY = 1e6

# Load configuration
with open(CONFIG_DIR / "plotting_params.yaml", 'r') as f:
    CONFIG = yaml.safe_load(f)

def calculate_run_level_metrics_by_system(df, run_name, noise_level, system):
    """Calculate run-level median max error for a specific system/noise combination."""
    subset_df = df[(df['run'] == run_name) &
                   (df['noise'] == noise_level) &
                   (df['name'] == system)]

    run_metrics = []
    for _, row in subset_df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            param_errors = calculate_individual_param_errors(estimated, true_params, true_states)

            if len(param_errors) > 0:
                run_metrics.append(np.max(param_errors))
            else:
                run_metrics.append(FAILURE_PENALTY)
        else:
            run_metrics.append(FAILURE_PENALTY)

    if len(run_metrics) > 0:
        return np.median(run_metrics)
    else:
        return np.nan

def generate_low_noise_table(df):
    """Generate Table A: Low-Noise Performance by System."""
    print("\nGenerating Table A: Low-Noise Performance (10^-6)...")

    noise_level = 1e-6
    methods = ['odepe_polish', 'sciml', 'amigo2_0_10']

    table_data = []
    for system in sorted(df['name'].unique()):
        row = {'System': CONFIG['system_names'].get(system, system)}

        for method in methods:
            median_max_error = calculate_run_level_metrics_by_system(df, method, noise_level, system)
            median_pct = median_max_error * 100

            # Format nicely
            if np.isnan(median_pct):
                row[CONFIG['method_names'][method]] = "N/A"
            elif median_pct > 1000:
                row[CONFIG['method_names'][method]] = "$>1000$"
            elif median_pct > 10:
                row[CONFIG['method_names'][method]] = f"{median_pct:.1f}"
            elif median_pct > 0.1:
                row[CONFIG['method_names'][method]] = f"{median_pct:.2f}"
            else:
                row[CONFIG['method_names'][method]] = f"{median_pct:.3f}"

        table_data.append(row)

    return pd.DataFrame(table_data)

def generate_high_noise_table(df):
    """Generate Table B: High-Noise Performance by System."""
    print("Generating Table B: High-Noise Performance (10^-2)...")

    noise_level = 1e-2
    methods = ['odepe_polish', 'sciml', 'amigo2_0_10']

    table_data = []
    for system in sorted(df['name'].unique()):
        row = {'System': CONFIG['system_names'].get(system, system)}

        for method in methods:
            median_max_error = calculate_run_level_metrics_by_system(df, method, noise_level, system)
            median_pct = median_max_error * 100

            # Format nicely
            if np.isnan(median_pct):
                row[CONFIG['method_names'][method]] = "N/A"
            elif median_pct > 1000:
                row[CONFIG['method_names'][method]] = "$>1000$"
            elif median_pct > 10:
                row[CONFIG['method_names'][method]] = f"{median_pct:.1f}"
            elif median_pct > 0.1:
                row[CONFIG['method_names'][method]] = f"{median_pct:.2f}"
            else:
                row[CONFIG['method_names'][method]] = f"{median_pct:.3f}"

        table_data.append(row)

    return pd.DataFrame(table_data)

def save_latex_table(df, filename, caption, label=None):
    """Save DataFrame as LaTeX table."""
    latex = "\\begin{table}[H]\n"
    latex += "\\centering\n"
    latex += f"\\caption{{{caption}}}\n"
    if label:
        latex += f"\\label{{{label}}}\n"
    latex += "\\small\n"
    latex += "\\begin{tabular}{l" + "c" * (len(df.columns) - 1) + "}\n"
    latex += "\\toprule\n"

    # Header
    latex += " & ".join(df.columns) + " \\\\\n"
    latex += "\\midrule\n"

    # Data rows
    for _, row in df.iterrows():
        latex += " & ".join(str(row[col]) for col in df.columns) + " \\\\\n"

    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"

    output_path = OUTPUT_DIR / filename
    with open(output_path, 'w') as f:
        f.write(latex)

    print(f"   ✓ Saved to {output_path}")
    return latex

def main():
    """Generate both system performance tables."""
    print("="*60)
    print("GENERATING SYSTEM PERFORMANCE TABLES (RUN-LEVEL)")
    print("="*60)

    # Load raw data directly
    print(f"\nLoading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    # Generate Table A: Low-Noise Performance
    table_a = generate_low_noise_table(df)
    latex_a = save_latex_table(
        table_a,
        "system_performance_low_noise.tex",
        "Median worst-parameter error (\\%) at low noise ($10^{-6}$) by system. For each run, the maximum parameter error is computed; the median across runs is reported.",
        label="tab:low_noise_systems"
    )

    # Generate Table B: High-Noise Performance
    table_b = generate_high_noise_table(df)
    latex_b = save_latex_table(
        table_b,
        "system_performance_high_noise.tex",
        "Median worst-parameter error (\\%) at high noise ($10^{-2}$) by system. For each run, the maximum parameter error is computed; the median across runs is reported.",
        label="tab:high_noise_systems"
    )

    print("\n" + "="*60)
    print("TABLES GENERATED SUCCESSFULLY")
    print("="*60)
    print("\nTo use in your paper, add:")
    print("\\input{tables/system_performance_low_noise.tex}")
    print("\\input{tables/system_performance_high_noise.tex}")

if __name__ == "__main__":
    main()
