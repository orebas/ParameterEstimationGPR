#!/usr/bin/env python3
"""
Data Loading and Preprocessing Module
======================================
This module handles loading the combined_results_filtered.csv file and
computing derived metrics for visualization. Designed to be reusable
when the dataset changes.
"""

import pandas as pd
import numpy as np
import ast
from pathlib import Path
import json
import yaml
from typing import Dict, List, Tuple, Optional, Any
import warnings
from tqdm import tqdm

# Configure paths relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
ROOT_DIR = PROJECT_DIR.parent  # Go up to ParameterEstimationGPR/
DATA_DIR = PROJECT_DIR / "data"
RAW_DATA_PATH = ROOT_DIR / "dataset_package" / "combined_results_filtered.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "processed_data.parquet"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)


class DataLoader:
    """Main class for loading and processing ODE parameter estimation results."""

    def __init__(self, csv_path: Path = RAW_DATA_PATH, use_cache: bool = True):
        """
        Initialize data loader.

        Parameters
        ----------
        csv_path : Path
            Path to combined_results_filtered.csv
        use_cache : bool
            Whether to use cached processed data if available
        """
        self.csv_path = csv_path
        self.use_cache = use_cache
        self.raw_df = None
        self.processed_df = None
        self.metadata = {}

    def load_raw_data(self) -> pd.DataFrame:
        """Load raw CSV data."""
        print(f"Loading raw data from {self.csv_path}...")
        self.raw_df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.raw_df)} rows with {len(self.raw_df.columns)} columns")

        # Store basic metadata
        self.metadata['n_rows'] = len(self.raw_df)
        self.metadata['methods'] = sorted(self.raw_df['run'].unique().tolist())
        self.metadata['systems'] = sorted(self.raw_df['name'].unique().tolist())
        self.metadata['noise_levels'] = sorted(self.raw_df['noise'].unique().tolist())

        return self.raw_df

    def parse_result_column(self, result_str: str) -> Dict[str, float]:
        """
        Parse result column from string format to dictionary.

        Parameters
        ----------
        result_str : str
            String representation of parameter estimates
            Format: "[['param1', 'value1'], ['param2', 'value2'], ...]"

        Returns
        -------
        Dict[str, float]
            Dictionary mapping parameter names to values
        """
        if pd.isna(result_str) or result_str == '[]':
            return {}

        try:
            result_list = ast.literal_eval(result_str)
            return {param: float(value) for param, value in result_list}
        except (ValueError, SyntaxError) as e:
            warnings.warn(f"Failed to parse result: {result_str[:50]}...")
            return {}

    def parse_true_parameters(self, param_str: str) -> Dict[str, float]:
        """
        Parse true_parameters column from string format to dictionary.

        Parameters
        ----------
        param_str : str
            String representation of true parameters
            Format: "{'k5': 0.539, 'k6': 0.672, ...}"

        Returns
        -------
        Dict[str, float]
            Dictionary mapping parameter names to true values
        """
        if pd.isna(param_str):
            return {}

        try:
            return ast.literal_eval(param_str)
        except (ValueError, SyntaxError) as e:
            warnings.warn(f"Failed to parse true parameters: {param_str[:50]}...")
            return {}

    def calculate_relative_error(self, estimated: Dict[str, float],
                                 true_params: Dict[str, float]) -> float:
        """
        Calculate mean relative error between estimated and true parameters.

        Parameters
        ----------
        estimated : Dict[str, float]
            Estimated parameter values
        true_params : Dict[str, float]
            True parameter values

        Returns
        -------
        float
            Mean relative error across all parameters
        """
        if not estimated or not true_params:
            return np.inf

        common_params = set(estimated.keys()) & set(true_params.keys())
        if len(common_params) == 0:
            return np.inf

        errors = []
        for param in common_params:
            est_val = estimated[param]
            true_val = true_params[param]

            if abs(true_val) < 1e-10:
                errors.append(abs(est_val - true_val))
            else:
                errors.append(abs(est_val - true_val) / abs(true_val))

        return np.mean(errors)

    def calculate_metrics(self, row: pd.Series) -> pd.Series:
        """
        Calculate all derived metrics for a single row.

        Parameters
        ----------
        row : pd.Series
            Single row from dataframe

        Returns
        -------
        pd.Series
            Series with calculated metrics
        """
        estimated = row['result_dict']
        true_params = row['true_params_dict']

        # Calculate various error metrics
        metrics = {}

        # Mean relative error
        metrics['mean_relative_error'] = self.calculate_relative_error(estimated, true_params)

        # Check if successful (has result and reasonable error)
        metrics['is_successful'] = (
            row['has_result'] and
            metrics['mean_relative_error'] < 0.5  # 50% threshold
        )

        # Calculate per-parameter errors
        param_errors = {}
        for param in set(estimated.keys()) & set(true_params.keys()):
            if abs(true_params[param]) < 1e-10:
                param_errors[param] = abs(estimated[param] - true_params[param])
            else:
                param_errors[param] = abs(estimated[param] - true_params[param]) / abs(true_params[param])

        metrics['max_param_error'] = max(param_errors.values()) if param_errors else np.inf
        metrics['min_param_error'] = min(param_errors.values()) if param_errors else np.inf
        metrics['median_param_error'] = np.median(list(param_errors.values())) if param_errors else np.inf

        # Calculate RMSE
        if param_errors:
            squared_errors = [(estimated[p] - true_params[p])**2
                            for p in param_errors.keys()]
            metrics['rmse'] = np.sqrt(np.mean(squared_errors))
        else:
            metrics['rmse'] = np.inf

        # Calculate MAE
        if param_errors:
            abs_errors = [abs(estimated[p] - true_params[p])
                         for p in param_errors.keys()]
            metrics['mae'] = np.mean(abs_errors)
        else:
            metrics['mae'] = np.inf

        # Number of parameters
        metrics['n_params'] = len(true_params)
        metrics['n_estimated'] = len(estimated)

        return pd.Series(metrics)

    def compute_system_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute metadata about each ODE system.

        Parameters
        ----------
        df : pd.DataFrame
            Processed dataframe

        Returns
        -------
        Dict[str, Any]
            Dictionary with system metadata
        """
        system_meta = {}

        for system in df['name'].unique():
            system_df = df[df['name'] == system]

            # Get a sample row to extract system properties
            sample_row = system_df.iloc[0]

            mean_diff = system_df.groupby('run')['mean_relative_error'].mean().mean()
            # Convert numpy types to Python types for YAML serialization
            system_meta[system] = {
                'n_parameters': int(len(sample_row['true_params_dict'])),
                'parameter_names': list(sample_row['true_params_dict'].keys()),
                'n_instances': int(len(system_df['id'].unique())),
                'mean_difficulty': float(mean_diff) if not np.isnan(mean_diff) else None,
                'complexity_score': int(len(sample_row['true_params_dict']))  # Simple metric, can be enhanced
            }

        return system_meta

    def numpy_to_python(self, obj):
        """Convert numpy types to Python types for YAML serialization."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self.numpy_to_python(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.numpy_to_python(item) for item in obj]
        else:
            return obj

    def process_data(self) -> pd.DataFrame:
        """
        Process raw data and compute all derived metrics.

        Returns
        -------
        pd.DataFrame
            Processed dataframe with all metrics
        """
        if self.raw_df is None:
            self.load_raw_data()

        print("Processing data...")
        df = self.raw_df.copy()

        # Parse result and true parameter columns
        print("Parsing result columns...")
        df['result_dict'] = df['result'].apply(self.parse_result_column)
        df['true_params_dict'] = df['true_parameters'].apply(self.parse_true_parameters)

        # Calculate metrics for each row
        print("Calculating metrics...")
        tqdm.pandas(desc="Computing metrics")
        metrics_df = df.progress_apply(self.calculate_metrics, axis=1)

        # Combine with original dataframe
        df = pd.concat([df, metrics_df], axis=1)

        # Add system metadata
        print("Computing system metadata...")
        self.metadata['systems_info'] = self.compute_system_metadata(df)

        # Store processed dataframe
        self.processed_df = df

        # Save to parquet for faster loading
        if self.use_cache:
            print(f"Saving processed data to {PROCESSED_DATA_PATH}...")
            df.to_parquet(PROCESSED_DATA_PATH)

            # Save metadata (convert numpy types first)
            metadata_path = DATA_DIR / "processed" / "metadata.yaml"
            clean_metadata = self.numpy_to_python(self.metadata)
            with open(metadata_path, 'w') as f:
                yaml.dump(clean_metadata, f)

        return df

    def get_data(self) -> pd.DataFrame:
        """
        Get processed data, using cache if available.

        Returns
        -------
        pd.DataFrame
            Processed dataframe
        """
        if self.use_cache and PROCESSED_DATA_PATH.exists():
            print(f"Loading cached data from {PROCESSED_DATA_PATH}...")
            self.processed_df = pd.read_parquet(PROCESSED_DATA_PATH)

            # Load metadata
            metadata_path = DATA_DIR / "processed" / "metadata.yaml"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.metadata = yaml.safe_load(f)
        else:
            self.process_data()

        return self.processed_df

    def get_summary_statistics(self) -> pd.DataFrame:
        """
        Compute summary statistics by method.

        Returns
        -------
        pd.DataFrame
            Summary statistics table
        """
        if self.processed_df is None:
            self.get_data()

        df = self.processed_df

        summary = []
        for method in df['run'].unique():
            method_df = df[df['run'] == method]

            summary.append({
                'method': method,
                'success_rate': method_df['is_successful'].mean(),
                'mean_error': method_df[method_df['is_successful']]['mean_relative_error'].mean(),
                'median_error': method_df[method_df['is_successful']]['mean_relative_error'].median(),
                'std_error': method_df[method_df['is_successful']]['mean_relative_error'].std(),
                'mean_time': method_df['time'].mean(),
                'median_time': method_df['time'].median(),
                'total_runs': len(method_df),
                'successful_runs': method_df['is_successful'].sum()
            })

        return pd.DataFrame(summary).sort_values('median_error')


def main():
    """Main function for testing data loading."""
    loader = DataLoader()
    df = loader.get_data()

    print("\n=== Data Summary ===")
    print(f"Total rows: {len(df)}")
    print(f"Methods: {df['run'].unique().tolist()}")
    print(f"Systems: {df['name'].unique().tolist()}")
    print(f"Noise levels: {sorted(df['noise'].unique().tolist())}")

    print("\n=== Summary Statistics ===")
    summary = loader.get_summary_statistics()
    print(summary.to_string(index=False))

    print("\n=== System Metadata ===")
    for system, info in loader.metadata.get('systems_info', {}).items():
        print(f"{system}: {info['n_parameters']} parameters, "
              f"difficulty={info['mean_difficulty']:.3f}")


if __name__ == "__main__":
    main()