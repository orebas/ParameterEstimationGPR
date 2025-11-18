#!/usr/bin/env python3
"""
Shared Metrics Calculation Module
==================================
Single source of truth for all metric calculations.
All tables and figures MUST use these functions to ensure consistency.

Uses Option B: Pool all individual parameter errors across all runs.
"""

import pandas as pd
import numpy as np
import ast
from typing import Dict, List

# Constants
PENALTY = 1e6

# Success rate thresholds
SR_THRESHOLDS = {
    'SR-1': 0.01,
    'SR-10': 0.10,
    'SR-50': 0.50
}


def parse_result(result_str):
    """Parse result column from string to dict."""
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
    """
    Calculate individual relative errors for all parameters/states.

    Parameters
    ----------
    estimated : dict
        Estimated parameter values
    true_params : dict
        True parameter values
    true_states : dict
        True state values

    Returns
    -------
    list of float
        Individual relative errors for each parameter/state
    """
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


def calculate_pooled_errors(df, run_name=None):
    """
    Calculate pooled parameter errors for a subset of data (Option B).

    Parameters
    ----------
    df : pd.DataFrame
        Data to analyze (can be filtered by noise, system, etc.)
    run_name : str, optional
        If provided, filter to specific method/run

    Returns
    -------
    np.array
        All individual parameter errors pooled together
    """
    if run_name is not None:
        df = df[df['run'] == run_name]

    all_errors = []

    for _, row in df.iterrows():
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

    return np.array(all_errors)


def calculate_median_error(df, run_name=None):
    """
    Calculate median error using Option B (pooled parameters).

    Parameters
    ----------
    df : pd.DataFrame
        Data to analyze
    run_name : str, optional
        Filter to specific method

    Returns
    -------
    float
        Median relative error (as fraction, not percentage)
    """
    all_errors = calculate_pooled_errors(df, run_name)
    return np.median(all_errors) if len(all_errors) > 0 else np.nan


def calculate_success_rates(df, run_name=None):
    """
    Calculate success rates at multiple thresholds using Option B.

    Parameters
    ----------
    df : pd.DataFrame
        Data to analyze
    run_name : str, optional
        Filter to specific method

    Returns
    -------
    dict
        Success rates as percentages for SR-1, SR-10, SR-50
    """
    all_errors = calculate_pooled_errors(df, run_name)

    if len(all_errors) == 0:
        return {key: np.nan for key in SR_THRESHOLDS.keys()}

    return {
        key: (all_errors < threshold).sum() / len(all_errors) * 100
        for key, threshold in SR_THRESHOLDS.items()
    }


def calculate_all_metrics(df, run_name):
    """
    Calculate all metrics for a method using Option B.

    Parameters
    ----------
    df : pd.DataFrame
        Full dataset
    run_name : str
        Method to analyze

    Returns
    -------
    dict
        All metrics: SR-1, SR-10, SR-50, median_error, mean_time, n_total
    """
    method_df = df[df['run'] == run_name].copy()
    n_total = len(method_df)

    # Calculate pooled errors and success rates
    sr = calculate_success_rates(df, run_name)
    median_err = calculate_median_error(df, run_name)

    return {
        'sr_1': sr['SR-1'],
        'sr_10': sr['SR-10'],
        'sr_50': sr['SR-50'],
        'median_error': median_err,
        'mean_time': method_df['time'].mean(),
        'n_total': n_total
    }


def calculate_performance_by_noise(df, run_name):
    """
    Calculate median error for each noise level using Option B.

    Parameters
    ----------
    df : pd.DataFrame
        Full dataset
    run_name : str
        Method to analyze

    Returns
    -------
    dict
        Mapping from noise level to median error (as fraction)
    """
    noise_levels = sorted(df['noise'].unique())
    results = {}

    for noise in noise_levels:
        noise_df = df[(df['run'] == run_name) & (df['noise'] == noise)]
        results[noise] = calculate_median_error(noise_df)

    return results


def calculate_performance_by_system(df, run_name, noise_level):
    """
    Calculate median error for each system at a specific noise level.

    Parameters
    ----------
    df : pd.DataFrame
        Full dataset
    run_name : str
        Method to analyze
    noise_level : float
        Noise level to filter

    Returns
    -------
    dict
        Mapping from system name to median error (as fraction)
    """
    systems = sorted(df['name'].unique())
    results = {}

    for system in systems:
        system_df = df[(df['run'] == run_name) &
                      (df['noise'] == noise_level) &
                      (df['name'] == system)]
        results[system] = calculate_median_error(system_df)

    return results


def calculate_run_level_metrics(df, run_name):
    """
    Calculate metrics at the RUN level.

    For each run, compute max/median/mean error across parameters.
    Failed runs are assigned PENALTY for all error metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Full dataset
    run_name : str
        Method to analyze

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: system, noise, max_error, median_error, mean_error, failed
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
                    'max_error': PENALTY,
                    'median_error': PENALTY,
                    'mean_error': PENALTY,
                    'failed': True
                })
        else:
            # No result at all - assign penalty
            run_metrics.append({
                'system': row['name'],
                'noise': row['noise'],
                'max_error': PENALTY,
                'median_error': PENALTY,
                'mean_error': PENALTY,
                'failed': True
            })

    return pd.DataFrame(run_metrics)
