#!/usr/bin/env python3
"""
Comprehensive audit of ALL table values against actual data.
Compares what's in the LaTeX table files vs what calculations produce.
"""

import pandas as pd
import numpy as np
import ast
import re
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent
PAPER_TABLES = ROOT_DIR / "paper" / "tables"
DATA_PATH = ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"

PENALTY = 1e6

def parse_result(result_str):
    """Parse result column."""
    if pd.isna(result_str) or result_str == '[]':
        return {}
    result_list = ast.literal_eval(result_str)
    return {param: float(value) for param, value in result_list}

def parse_dict(dict_str):
    """Parse dictionary string."""
    if pd.isna(dict_str) or dict_str == '{}':
        return {}
    return ast.literal_eval(dict_str)

def calculate_individual_param_errors(estimated, true_params, true_states):
    """Calculate individual relative errors for all parameters/states."""
    all_true = {**true_params, **true_states}
    errors = []
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

def calculate_metrics(df, run_name):
    """Calculate all metrics for a method using Option B (pooled errors)."""
    method_df = df[df['run'] == run_name].copy()
    n_total = len(method_df)

    # Pool all individual parameter errors
    all_errors = []
    for _, row in method_df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            param_errors = calculate_individual_param_errors(estimated, true_params, true_states)
            all_errors.extend(param_errors)
        else:
            # Add penalty for each parameter that would have been estimated
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            n_params = len(true_params) + len(true_states)
            all_errors.extend([PENALTY] * n_params)

    all_errors = np.array(all_errors)

    return {
        'sr_1': (all_errors < 0.01).sum() / len(all_errors) * 100,
        'sr_10': (all_errors < 0.10).sum() / len(all_errors) * 100,
        'sr_50': (all_errors < 0.50).sum() / len(all_errors) * 100,
        'median_error': np.median(all_errors) * 100,  # Convert to %
        'mean_time': method_df['time'].mean(),
        'n_total': n_total
    }

def extract_table1_values(filepath):
    """Extract values from Table 1 LaTeX file."""
    with open(filepath, 'r') as f:
        content = f.read()

    values = {}
    lines = content.split('\n')

    for line in lines:
        if 'ODEPE-GPR &' in line and 'polished' not in line:
            parts = line.split('&')
            values['odepe'] = {
                'sr_1': float(parts[1].strip()),
                'sr_10': float(parts[2].strip()),
                'sr_50': float(parts[3].strip()),
                'median_error': float(parts[4].strip()),
                'mean_time': float(parts[5].strip())
            }
        elif 'ODEPE-GPR (polished)' in line:
            parts = line.split('&')
            values['odepe_polish'] = {
                'sr_1': float(parts[1].strip()),
                'sr_10': float(parts[2].strip()),
                'sr_50': float(parts[3].strip()),
                'median_error': float(parts[4].strip()),
                'mean_time': float(parts[5].strip())
            }
        elif 'SciML' in line:
            parts = line.split('&')
            values['sciml'] = {
                'sr_1': float(parts[1].strip()),
                'sr_10': float(parts[2].strip()),
                'sr_50': float(parts[3].strip()),
                'median_error': float(parts[4].strip()),
                'mean_time': float(parts[5].strip())
            }
        elif 'AMIGO2 [0,10]' in line:
            parts = line.split('&')
            values['amigo2_0_10'] = {
                'sr_1': float(parts[1].strip()),
                'sr_10': float(parts[2].strip()),
                'sr_50': float(parts[3].strip()),
                'median_error': float(parts[4].strip()),
                'mean_time': float(parts[5].strip())
            }
        elif 'AMIGO2 [0,100]' in line:
            parts = line.split('&')
            values['amigo2_0_100'] = {
                'sr_1': float(parts[1].strip()),
                'sr_10': float(parts[2].strip()),
                'sr_50': float(parts[3].strip()),
                'median_error': float(parts[4].strip()),
                'mean_time': float(parts[5].strip())
            }

    return values

def calculate_median_error_only(df, run_name):
    """Calculate just median error for a method using Option B (pooled errors)."""
    method_df = df[df['run'] == run_name].copy()

    # Pool all individual parameter errors
    all_errors = []
    for _, row in method_df.iterrows():
        if row['has_result']:
            estimated = parse_result(row['result'])
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            param_errors = calculate_individual_param_errors(estimated, true_params, true_states)
            all_errors.extend(param_errors)
        else:
            # Add penalty for each parameter that would have been estimated
            true_params = parse_dict(row['true_parameters'])
            true_states = parse_dict(row['true_states'])
            n_params = len(true_params) + len(true_states)
            all_errors.extend([PENALTY] * n_params)

    return np.median(all_errors) * 100  # Convert to %

def audit_table1():
    """Audit Table 1: Overall Performance."""
    print("\n" + "="*80)
    print("AUDITING TABLE 1: Overall Performance")
    print("="*80)

    # Load data
    df = pd.read_csv(DATA_PATH)

    # Read table values
    table_file = PAPER_TABLES / "table_1_overall_performance.tex"
    table_values = extract_table1_values(table_file)

    # Calculate actual values
    methods = ['odepe', 'odepe_polish', 'sciml', 'amigo2_0_10', 'amigo2_0_100']
    method_names = {
        'odepe': 'ODEPE-GPR',
        'odepe_polish': 'ODEPE-GPR (polished)',
        'sciml': 'SciML',
        'amigo2_0_10': 'AMIGO2 [0,10]',
        'amigo2_0_100': 'AMIGO2 [0,100]'
    }

    all_match = True
    discrepancies = []

    for method in methods:
        print(f"\n{method_names[method]}:")
        calc = calculate_metrics(df, method)
        table = table_values.get(method, {})

        for metric in ['sr_1', 'sr_10', 'sr_50', 'median_error', 'mean_time']:
            table_val = table.get(metric, np.nan)
            calc_val = calc[metric]
            diff = abs(table_val - calc_val)

            # Tolerance: 0.1 for percentages, 1.0 for time
            tolerance = 1.0 if metric == 'mean_time' else 0.1

            match_symbol = "✓" if diff < tolerance else "✗"
            print(f"  {metric:15} Table: {table_val:7.2f}  Calc: {calc_val:7.2f}  Diff: {diff:6.2f} {match_symbol}")

            if diff >= tolerance:
                all_match = False
                discrepancies.append({
                    'table': 'Table 1',
                    'method': method_names[method],
                    'metric': metric,
                    'table_val': table_val,
                    'calc_val': calc_val,
                    'diff': diff
                })

    return all_match, discrepancies

def extract_table2_values(filepath):
    """Extract values from Table 2 LaTeX file."""
    with open(filepath, 'r') as f:
        content = f.read()

    values = {}
    lines = content.split('\n')

    for line in lines:
        if 'ODEPE-GPR &' in line and 'polished' not in line:
            parts = line.split('&')
            values['odepe'] = [float(parts[i].strip().replace('\\\\', '')) for i in range(1, 6)]
        elif 'ODEPE-GPR (polished)' in line:
            parts = line.split('&')
            values['odepe_polish'] = [float(parts[i].strip().replace('\\\\', '')) for i in range(1, 6)]
        elif 'SciML' in line:
            parts = line.split('&')
            values['sciml'] = [float(parts[i].strip().replace('\\\\', '')) for i in range(1, 6)]
        elif 'AMIGO2 [0,10]' in line:
            parts = line.split('&')
            values['amigo2_0_10'] = [float(parts[i].strip().replace('\\\\', '')) for i in range(1, 6)]
        elif 'AMIGO2 [0,100]' in line:
            parts = line.split('&')
            values['amigo2_0_100'] = [float(parts[i].strip().replace('\\\\', '')) for i in range(1, 6)]

    return values

def audit_table2():
    """Audit Table 2: Performance by Noise."""
    print("\n" + "="*80)
    print("AUDITING TABLE 2: Performance by Noise")
    print("="*80)

    # Load data
    df = pd.read_csv(DATA_PATH)

    # Read table values
    table_file = PAPER_TABLES / "table_2_performance_by_noise.tex"
    table_values = extract_table2_values(table_file)

    methods = ['odepe', 'odepe_polish', 'sciml', 'amigo2_0_10', 'amigo2_0_100']
    method_names = {
        'odepe': 'ODEPE-GPR',
        'odepe_polish': 'ODEPE-GPR (polished)',
        'sciml': 'SciML',
        'amigo2_0_10': 'AMIGO2 [0,10]',
        'amigo2_0_100': 'AMIGO2 [0,100]'
    }

    noise_levels = [0, 1e-8, 1e-6, 1e-4, 1e-2]
    noise_labels = ['0', '10^-8', '10^-6', '10^-4', '10^-2']

    all_match = True
    discrepancies = []

    for method in methods:
        print(f"\n{method_names[method]}:")
        table_vals = table_values.get(method, [])

        for i, noise in enumerate(noise_levels):
            # Filter by noise level
            noise_df = df[df['noise'] == noise].copy()
            calc_val = calculate_median_error_only(noise_df, method)
            table_val = table_vals[i] if i < len(table_vals) else np.nan
            diff = abs(table_val - calc_val)

            tolerance = 0.1
            match_symbol = "✓" if diff < tolerance else "✗"
            print(f"  {noise_labels[i]:8} Table: {table_val:7.2f}  Calc: {calc_val:7.2f}  Diff: {diff:6.2f} {match_symbol}")

            if diff >= tolerance:
                all_match = False
                discrepancies.append({
                    'table': 'Table 2',
                    'method': method_names[method],
                    'metric': f'noise_{noise_labels[i]}',
                    'table_val': table_val,
                    'calc_val': calc_val,
                    'diff': diff
                })

    return all_match, discrepancies

def extract_table3_values(filepath):
    """Extract values from Table 3 LaTeX file."""
    with open(filepath, 'r') as f:
        content = f.read()

    values = {}
    lines = content.split('\n')

    systems = ['Biohydrogenation', 'Crauste', 'DAISY MaMil3', 'DAISY MaMil4',
               'FitzHugh-Nagumo', 'Harmonic Oscillator', 'HIV', 'Lotka-Volterra',
               'SEIR', 'Slow-Fast', 'Van der Pol']

    for line in lines:
        for system in systems:
            if line.startswith(system):
                parts = line.split('&')
                if len(parts) >= 4:
                    values[system] = {
                        'odepe_polish': float(parts[1].strip()),
                        'sciml': float(parts[2].strip()),
                        'amigo2_0_10': float(parts[3].strip().replace('\\\\', ''))
                    }

    return values

def extract_table4_values(filepath):
    """Extract values from Table 4 LaTeX file."""
    return extract_table3_values(filepath)  # Same format

def audit_table3():
    """Audit Table 3: System Performance at Low Noise."""
    print("\n" + "="*80)
    print("AUDITING TABLE 3: System Performance at Low Noise (10^-6)")
    print("="*80)

    # Load data
    df = pd.read_csv(DATA_PATH)

    # Filter for low noise
    df_low_noise = df[df['noise'] == 1e-6].copy()

    # Read table values
    table_file = PAPER_TABLES / "system_performance_low_noise.tex"
    table_values = extract_table3_values(table_file)

    methods = ['odepe_polish', 'sciml', 'amigo2_0_10']
    method_names = {
        'odepe_polish': 'ODEPE-GPR (polished)',
        'sciml': 'SciML',
        'amigo2_0_10': 'AMIGO2 [0,10]'
    }

    systems = ['Biohydrogenation', 'Crauste', 'DAISY MaMil3', 'DAISY MaMil4',
               'FitzHugh-Nagumo', 'Harmonic Oscillator', 'HIV', 'Lotka-Volterra',
               'SEIR', 'Slow-Fast', 'Van der Pol']

    # Map table names to dataset names
    system_name_map = {
        'Biohydrogenation': 'biohydrogenation',
        'Crauste': 'crauste',
        'DAISY MaMil3': 'daisy_mamil3',
        'DAISY MaMil4': 'daisy_mamil4',
        'FitzHugh-Nagumo': 'fitzhugh_nagumo',
        'Harmonic Oscillator': 'harmonic',
        'HIV': 'hiv',
        'Lotka-Volterra': 'lotka_volterra',
        'SEIR': 'seir',
        'Slow-Fast': 'slowfast',
        'Van der Pol': 'vanderpol'
    }

    all_match = True
    discrepancies = []

    for system in systems:
        print(f"\n{system}:")
        table = table_values.get(system, {})

        for method in methods:
            # Filter by system (map to dataset name)
            dataset_name = system_name_map[system]
            system_df = df_low_noise[df_low_noise['name'] == dataset_name].copy()
            calc_val = calculate_median_error_only(system_df, method)
            table_val = table.get(method, np.nan)
            diff = abs(table_val - calc_val)

            tolerance = 0.1
            match_symbol = "✓" if diff < tolerance else "✗"
            print(f"  {method_names[method]:25} Table: {table_val:7.2f}  Calc: {calc_val:7.2f}  Diff: {diff:6.2f} {match_symbol}")

            if diff >= tolerance:
                all_match = False
                discrepancies.append({
                    'table': 'Table 3',
                    'method': method_names[method],
                    'metric': system,
                    'table_val': table_val,
                    'calc_val': calc_val,
                    'diff': diff
                })

    return all_match, discrepancies

def audit_table4():
    """Audit Table 4: System Performance at High Noise."""
    print("\n" + "="*80)
    print("AUDITING TABLE 4: System Performance at High Noise (10^-2)")
    print("="*80)

    # Load data
    df = pd.read_csv(DATA_PATH)

    # Filter for high noise
    df_high_noise = df[df['noise'] == 1e-2].copy()

    # Read table values
    table_file = PAPER_TABLES / "system_performance_high_noise.tex"
    table_values = extract_table4_values(table_file)

    methods = ['odepe_polish', 'sciml', 'amigo2_0_10']
    method_names = {
        'odepe_polish': 'ODEPE-GPR (polished)',
        'sciml': 'SciML',
        'amigo2_0_10': 'AMIGO2 [0,10]'
    }

    systems = ['Biohydrogenation', 'Crauste', 'DAISY MaMil3', 'DAISY MaMil4',
               'FitzHugh-Nagumo', 'Harmonic Oscillator', 'HIV', 'Lotka-Volterra',
               'SEIR', 'Slow-Fast', 'Van der Pol']

    # Map table names to dataset names
    system_name_map = {
        'Biohydrogenation': 'biohydrogenation',
        'Crauste': 'crauste',
        'DAISY MaMil3': 'daisy_mamil3',
        'DAISY MaMil4': 'daisy_mamil4',
        'FitzHugh-Nagumo': 'fitzhugh_nagumo',
        'Harmonic Oscillator': 'harmonic',
        'HIV': 'hiv',
        'Lotka-Volterra': 'lotka_volterra',
        'SEIR': 'seir',
        'Slow-Fast': 'slowfast',
        'Van der Pol': 'vanderpol'
    }

    all_match = True
    discrepancies = []

    for system in systems:
        print(f"\n{system}:")
        table = table_values.get(system, {})

        for method in methods:
            # Filter by system (map to dataset name)
            dataset_name = system_name_map[system]
            system_df = df_high_noise[df_high_noise['name'] == dataset_name].copy()
            calc_val = calculate_median_error_only(system_df, method)
            table_val = table.get(method, np.nan)
            diff = abs(table_val - calc_val)

            tolerance = 0.1
            match_symbol = "✓" if diff < tolerance else "✗"
            print(f"  {method_names[method]:25} Table: {table_val:7.2f}  Calc: {calc_val:7.2f}  Diff: {diff:6.2f} {match_symbol}")

            if diff >= tolerance:
                all_match = False
                discrepancies.append({
                    'table': 'Table 4',
                    'method': method_names[method],
                    'metric': system,
                    'table_val': table_val,
                    'calc_val': calc_val,
                    'diff': diff
                })

    return all_match, discrepancies

def main():
    print("="*80)
    print("COMPREHENSIVE TABLE AUDIT")
    print("Comparing generated LaTeX tables against recalculated values from data")
    print("="*80)

    # Audit all tables
    table1_ok, table1_disc = audit_table1()
    table2_ok, table2_disc = audit_table2()
    table3_ok, table3_disc = audit_table3()
    table4_ok, table4_disc = audit_table4()

    # Combine all discrepancies
    all_discrepancies = table1_disc + table2_disc + table3_disc + table4_disc

    # Summary
    print("\n" + "="*80)
    print("AUDIT SUMMARY")
    print("="*80)

    print(f"\nTable 1 (Overall Performance): {'✓ PASS' if table1_ok else f'✗ FAIL ({len(table1_disc)} issues)'}")
    print(f"Table 2 (Performance by Noise): {'✓ PASS' if table2_ok else f'✗ FAIL ({len(table2_disc)} issues)'}")
    print(f"Table 3 (System Performance Low Noise): {'✓ PASS' if table3_ok else f'✗ FAIL ({len(table3_disc)} issues)'}")
    print(f"Table 4 (System Performance High Noise): {'✓ PASS' if table4_ok else f'✗ FAIL ({len(table4_disc)} issues)'}")

    if table1_ok and table2_ok and table3_ok and table4_ok:
        print("\n✓ ALL TABLES MATCH PERFECTLY!")
    else:
        print(f"\n✗ FOUND {len(all_discrepancies)} TOTAL DISCREPANCIES")
        print("\nDetails:")
        for disc in all_discrepancies:
            print(f"  {disc['table']} - {disc['method']} - {disc['metric']}:")
            print(f"    Table: {disc['table_val']:.2f}, Calculated: {disc['calc_val']:.2f}, Diff: {disc['diff']:.2f}")

    print("\n" + "="*80)

if __name__ == '__main__':
    main()
