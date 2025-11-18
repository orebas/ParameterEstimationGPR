#!/usr/bin/env python3
"""
Generate All Final Figures for Paper
====================================
Creates all publication-ready figures with run-level aggregation:
1. Pareto Frontier
2. Noise Degradation Curves
3. Performance Heatmap
4. Success Rate Curves
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import yaml
import warnings
warnings.filterwarnings('ignore')

# Import shared metrics module
from shared_metrics import (
    parse_result, parse_dict, calculate_individual_param_errors
)

# Configure paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
CONFIG_DIR = ROOT_DIR / "config"
OUTPUT_DIR = ROOT_DIR / "outputs" / "figures" / "corrected"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"

FAILURE_PENALTY = 1e6

# Load configuration
with open(CONFIG_DIR / "plotting_params.yaml", 'r') as f:
    CONFIG = yaml.safe_load(f)

def calculate_run_level_metrics(df, run_name):
    """Calculate metrics at the RUN level.

    For each run, compute max/median/mean error across parameters.
    Failed runs are assigned 10^6 penalty for all error metrics.
    """
    method_df = df[df['run'] == run_name].copy()
    run_metrics = []

    for _, row in method_df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            param_errors = calculate_individual_param_errors(estimated, true_params, true_states)

            if len(param_errors) > 0:
                run_metrics.append({
                    'system': row['name'],
                    'noise': row['noise'],
                    'max_error': np.max(param_errors),
                    'median_error': np.median(param_errors),
                    'mean_error': np.mean(param_errors),
                    'failed': False
                })
            else:
                # Failed to parse parameters - assign penalty
                run_metrics.append({
                    'system': row['name'],
                    'noise': row['noise'],
                    'max_error': FAILURE_PENALTY,
                    'median_error': FAILURE_PENALTY,
                    'mean_error': FAILURE_PENALTY,
                    'failed': True
                })
        else:
            # No result at all - assign penalty
            run_metrics.append({
                'system': row['name'],
                'noise': row['noise'],
                'max_error': FAILURE_PENALTY,
                'median_error': FAILURE_PENALTY,
                'mean_error': FAILURE_PENALTY,
                'failed': True
            })

    return pd.DataFrame(run_metrics)

def figure_1_pareto_frontier(df):
    """Generate Pareto frontier with run-level metrics."""
    print("\n1. Generating Pareto Frontier")

    # Calculate statistics for each method
    methods_data = []
    for method in df['run'].unique():
        run_df = calculate_run_level_metrics(df, method)
        method_df = df[df['run'] == method]

        # Calculate run-level median max error
        median_max = np.median(run_df['max_error'])

        # Calculate success rate (runs where max_error < 10%)
        success_rate = (run_df['max_error'] < 0.10).sum() / len(run_df) * 100

        methods_data.append({
            'method': CONFIG['method_names'][method],
            'median_max_error': median_max,
            'mean_time': method_df['time'].mean(),
            'success_rate': success_rate
        })

    methods_df = pd.DataFrame(methods_data)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(methods_df['mean_time'],
                        methods_df['median_max_error'],
                        s=methods_df['success_rate'] * 10,
                        alpha=0.7,
                        c=range(len(methods_df)),
                        cmap='viridis')

    for idx, row in methods_df.iterrows():
        ax.annotate(row['method'],
                   (row['mean_time'], row['median_max_error']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=10, fontweight='bold')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Mean Computation Time (seconds)', fontsize=12)
    ax.set_ylabel('Median Max Error (per run, failures penalized)', fontsize=12)
    ax.set_title('Pareto Frontier: Accuracy vs Speed\\n(Point size = success rate @10%)',
                fontsize=14, fontweight='bold')
    ax.grid(True, which="both", ls="-", alpha=0.2)
    ax.legend(['Size ∝ Success@10%'], loc='upper left')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'pareto_frontier.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'pareto_frontier.pdf', bbox_inches='tight')
    plt.close()

    print(f"   ✓ Saved to {OUTPUT_DIR / 'pareto_frontier.png'}")

def figure_2_noise_degradation(df):
    """Generate noise degradation curves with run-level metrics."""
    print("\n2. Generating Noise Degradation Curves")

    # Distinct colors and line styles
    method_styles = {
        'sciml': {'color': '#2E86AB', 'linestyle': '-', 'marker': 'o', 'linewidth': 3.5},
        'odepe': {'color': '#A23B72', 'linestyle': '--', 'marker': 's', 'linewidth': 3.5},
        'odepe_polish': {'color': '#F18F01', 'linestyle': '-.', 'marker': '^', 'linewidth': 3.5},
        'amigo2_0_10': {'color': '#C73E1D', 'linestyle': ':', 'marker': 'D', 'linewidth': 3.5},
        'amigo2_0_100': {'color': '#6A994E', 'linestyle': '-', 'marker': 'v', 'linewidth': 3}
    }

    fig, ax = plt.subplots(figsize=(12, 8))

    noise_levels = sorted(df['noise'].unique())
    noise_labels = [CONFIG['noise_labels'].get(n, f"{n:.0e}") for n in noise_levels]
    x_positions = list(range(len(noise_levels)))

    method_data = {}
    for method in ['sciml', 'odepe', 'odepe_polish', 'amigo2_0_10', 'amigo2_0_100']:
        medians = []
        for noise in noise_levels:
            noise_df = df[(df['run'] == method) & (df['noise'] == noise)]
            run_df = calculate_run_level_metrics(noise_df, method)
            median_max = np.median(run_df['max_error']) * 100  # Convert to percentage
            medians.append(median_max)

        method_data[method] = medians

        style = method_styles[method]
        label = CONFIG['method_names'][method]

        ax.plot(x_positions, medians,
               label=label,
               marker=style['marker'],
               markersize=12,
               linestyle=style['linestyle'],
               linewidth=style['linewidth'],
               color=style['color'],
               alpha=0.9,
               markeredgewidth=2,
               markeredgecolor='white',
               zorder=5)

    # Add value annotations
    final_pos = x_positions[-1]
    methods_sorted = sorted(['sciml', 'odepe', 'odepe_polish', 'amigo2_0_10', 'amigo2_0_100'],
                           key=lambda m: method_data[m][-1])

    for i, method in enumerate(methods_sorted):
        final_value = method_data[method][-1]
        style = method_styles[method]
        y_offset = (i - 2) * 12

        ax.annotate(f'{final_value:.2f}%',
                   xy=(final_pos, final_value),
                   xytext=(15, y_offset),
                   textcoords='offset points',
                   fontsize=10,
                   color=style['color'],
                   fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                            edgecolor=style['color'], alpha=0.9, linewidth=2))

    ax.set_yscale('log')
    ax.set_xlabel('Noise Level', fontsize=14, fontweight='bold')
    ax.set_ylabel('Median Max Error (% per run)', fontsize=14, fontweight='bold')
    ax.set_title('Performance Degradation with Noise\\n(Run-level aggregation, failures penalized)',
                fontsize=16, fontweight='bold', pad=20)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(noise_labels, fontsize=13)
    ax.tick_params(axis='y', labelsize=12)
    ax.set_ylim(1e-3, 1000)

    ax.grid(True, which="major", axis='y', ls="-", alpha=0.4, linewidth=1)
    ax.grid(True, which="minor", axis='y', ls=":", alpha=0.2, linewidth=0.5)
    ax.grid(True, which="major", axis='x', ls="-", alpha=0.3, linewidth=1)

    legend = ax.legend(loc='upper left',
                      frameon=True,
                      fancybox=True,
                      shadow=True,
                      fontsize=11,
                      markerscale=1)
    legend.get_frame().set_alpha(0.95)

    critical_pos = 2.5
    ax.axvline(x=critical_pos, color='red', linestyle='--', alpha=0.6, linewidth=3, zorder=0)
    ax.text(critical_pos + 0.1, 1e-2, 'Critical\\nthreshold',
           fontsize=11, color='red', fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.85,
                    edgecolor='red', linewidth=2))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'noise_degradation.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'noise_degradation.pdf', bbox_inches='tight')
    plt.close()

    print(f"   ✓ Saved to {OUTPUT_DIR / 'noise_degradation.png'}")

def figure_3_performance_heatmap(df):
    """Generate performance heatmap with run-level metrics per system."""
    print("\n3. Generating Performance Heatmap")

    heatmap_data = []
    for system in sorted(df['name'].unique()):
        for method in ['odepe', 'odepe_polish', 'sciml', 'amigo2_0_10', 'amigo2_0_100']:
            system_method_df = df[(df['name'] == system) & (df['run'] == method)]
            run_df = calculate_run_level_metrics(system_method_df, method)

            median_max = np.median(run_df['max_error']) if len(run_df) > 0 else np.nan
            # Convert to percentage and cap at 100%
            median_max_pct = min(median_max * 100, 100.0)

            heatmap_data.append({
                'System': CONFIG['system_names'].get(system, system),
                'Method': CONFIG['method_names'][method],
                'Median Max Error': median_max_pct
            })

    heatmap_df = pd.DataFrame(heatmap_data)
    pivot = heatmap_df.pivot(index='System', columns='Method', values='Median Max Error')

    system_difficulty = pivot.mean(axis=1).sort_values()
    pivot = pivot.loc[system_difficulty.index]

    fig, ax = plt.subplots(figsize=(12, 10))

    sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn_r',
                vmin=0, vmax=100.0,
                cbar_kws={'label': 'Median Max Error (% per run, capped at 100%)'},
                linewidths=0.5, linecolor='gray',
                ax=ax)

    ax.set_title('Performance Heatmap: Median Max Error (%)\\n(Run-level aggregation, systems ordered by difficulty)',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Method', fontsize=12)
    ax.set_ylabel('System', fontsize=12)

    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    plt.setp(ax.yaxis.get_majorticklabels(), rotation=0)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'performance_heatmap.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'performance_heatmap.pdf', bbox_inches='tight')
    plt.close()

    print(f"   ✓ Saved to {OUTPUT_DIR / 'performance_heatmap.png'}")

def figure_4_success_rate_curves(df):
    """Generate success rate curves across thresholds using run-level metrics."""
    print("\n4. Generating Success Rate Curves")

    # Distinct colors and markers for each method
    method_styles = {
        'sciml': {'color': '#2E86AB', 'marker': 'o', 'linewidth': 3},
        'odepe': {'color': '#A23B72', 'marker': 's', 'linewidth': 3},
        'odepe_polish': {'color': '#F18F01', 'marker': '^', 'linewidth': 3},
        'amigo2_0_10': {'color': '#C73E1D', 'marker': 'D', 'linewidth': 3},
        'amigo2_0_100': {'color': '#6A994E', 'marker': 'v', 'linewidth': 3}
    }

    fig, ax = plt.subplots(figsize=(10, 8))

    thresholds = [0.01, 0.10, 0.50]
    threshold_labels = ['Success@1%\n(all params <1%)', 'Success@10%\n(all params <10%)', 'Success@50%\n(all params <50%)']
    x_positions = [0, 1, 2]

    for method in ['sciml', 'odepe', 'odepe_polish', 'amigo2_0_10', 'amigo2_0_100']:
        run_df = calculate_run_level_metrics(df, method)
        total_runs = len(run_df)

        success_rates = []
        for threshold in thresholds:
            # Count runs where max_error < threshold
            sr = (run_df['max_error'] < threshold).sum() / total_runs * 100
            success_rates.append(sr)

        style = method_styles[method]
        label = CONFIG['method_names'][method]

        ax.plot(x_positions, success_rates,
               label=label,
               marker=style['marker'],
               markersize=14,
               linewidth=style['linewidth'],
               color=style['color'],
               alpha=0.9,
               markeredgewidth=2,
               markeredgecolor='white',
               zorder=5)

        # Annotate final value
        ax.annotate(f'{success_rates[-1]:.1f}%',
                   xy=(x_positions[-1], success_rates[-1]),
                   xytext=(10, 0),
                   textcoords='offset points',
                   fontsize=9,
                   color=style['color'],
                   fontweight='bold',
                   va='center')

    ax.set_xticks(x_positions)
    ax.set_xticklabels(threshold_labels, fontsize=13)
    ax.set_xlabel('Success Threshold', fontsize=14, fontweight='bold')
    ax.set_ylabel('Success Rate (% of runs)', fontsize=14, fontweight='bold')
    ax.set_title('Success Rate Curves Across Error Thresholds\\n(Fraction of runs where ALL parameters meet criterion)',
                fontsize=14, fontweight='bold', pad=20)

    ax.set_ylim(0, 100)
    ax.grid(True, axis='y', ls='-', alpha=0.3, linewidth=1)
    ax.tick_params(axis='y', labelsize=12)

    legend = ax.legend(loc='lower right',
                      frameon=True,
                      fancybox=True,
                      shadow=True,
                      fontsize=11)
    legend.get_frame().set_alpha(0.95)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'success_rate_curves.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'success_rate_curves.pdf', bbox_inches='tight')
    plt.close()

    print(f"   ✓ Saved to {OUTPUT_DIR / 'success_rate_curves.png'}")

def main():
    """Generate all final figures."""
    print("="*70)
    print("GENERATING ALL FINAL FIGURES (RUN-LEVEL AGGREGATION)")
    print("="*70)

    # Load data directly from CSV
    print(f"\nLoading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows")

    figure_1_pareto_frontier(df)
    figure_2_noise_degradation(df)
    figure_3_performance_heatmap(df)
    figure_4_success_rate_curves(df)

    print("\n" + "="*70)
    print("All figures generated successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("="*70)

if __name__ == "__main__":
    main()
