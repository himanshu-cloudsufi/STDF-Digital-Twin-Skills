#!/usr/bin/env python3
"""
Utility Functions Module
Common utility functions for datacenter UPS battery forecasting
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import matplotlib.pyplot as plt
import seaborn as sns


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Load configuration from JSON file

    Args:
        config_path: Path to config.json (optional)

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config.json'

    with open(config_path, 'r') as f:
        return json.load(f)


def smooth_time_series(data: pd.Series, window: int = 3,
                       method: str = 'median') -> pd.Series:
    """
    Smooth time series data

    Args:
        data: Input time series
        window: Smoothing window size
        method: Smoothing method ('median', 'mean', 'ewm')

    Returns:
        Smoothed time series
    """
    if len(data) < window:
        return data

    if method == 'median':
        return data.rolling(window=window, center=True, min_periods=1).median()
    elif method == 'mean':
        return data.rolling(window=window, center=True, min_periods=1).mean()
    elif method == 'ewm':
        return data.ewm(span=window, adjust=False).mean()
    else:
        raise ValueError(f"Unknown smoothing method: {method}")


def interpolate_missing_data(data: pd.Series, method: str = 'linear',
                            max_gap: int = 3) -> pd.Series:
    """
    Interpolate missing data points

    Args:
        data: Time series with potential gaps
        method: Interpolation method
        max_gap: Maximum gap size to interpolate

    Returns:
        Interpolated series
    """
    # First, identify gap sizes
    if data.empty:
        return data

    # Convert to DataFrame for easier manipulation
    df = data.to_frame('value')
    df['interpolated'] = False

    # Identify gaps
    years = sorted(data.index)
    for i in range(len(years) - 1):
        gap = years[i+1] - years[i]
        if 1 < gap <= max_gap + 1:
            # Interpolate this gap
            for year in range(years[i] + 1, years[i+1]):
                if year not in df.index:
                    df.loc[year, 'interpolated'] = True

    # Sort and interpolate
    df = df.sort_index()
    df['value'] = df['value'].interpolate(method=method, limit=max_gap)

    return df['value']


def calculate_cagr(start_value: float, end_value: float, years: int) -> float:
    """
    Calculate Compound Annual Growth Rate

    Args:
        start_value: Initial value
        end_value: Final value
        years: Number of years

    Returns:
        CAGR as decimal (e.g., 0.08 for 8%)
    """
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0

    return (end_value / start_value) ** (1 / years) - 1


def calculate_log_cagr(data: pd.Series) -> float:
    """
    Calculate CAGR in log space for cost projections

    Args:
        data: Time series of values

    Returns:
        Log-space CAGR (slope)
    """
    if len(data) < 2:
        return 0.0

    years = data.index.values
    values = data.values

    # Remove zero or negative values
    valid_mask = values > 0
    if not any(valid_mask):
        return 0.0

    years = years[valid_mask]
    values = values[valid_mask]

    if len(years) < 2:
        return 0.0

    # Calculate log-linear regression
    log_values = np.log(values)
    coeffs = np.polyfit(years, log_values, 1)

    return coeffs[0]  # Return slope


def validate_dataframe_schema(df: pd.DataFrame, required_columns: List[str],
                             optional_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate DataFrame has required columns and proper types

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        optional_columns: List of optional column names

    Returns:
        Validation results dictionary
    """
    results = {
        'valid': True,
        'missing_required': [],
        'missing_optional': [],
        'type_issues': [],
        'columns_present': list(df.columns)
    }

    # Check required columns
    for col in required_columns:
        if col not in df.columns:
            results['missing_required'].append(col)
            results['valid'] = False

    # Check optional columns
    if optional_columns:
        for col in optional_columns:
            if col not in df.columns:
                results['missing_optional'].append(col)

    # Check data types for numeric columns
    numeric_suffixes = ['_gwh', '_mwh', '_mw', '_pct', '_per_kwh', '_years']
    for col in df.columns:
        if any(col.endswith(suffix) for suffix in numeric_suffixes):
            if not pd.api.types.is_numeric_dtype(df[col]):
                results['type_issues'].append(f"{col} is not numeric")
                results['valid'] = False

    return results


def apply_regional_multipliers(base_value: float, region: str,
                              multipliers: Dict[str, float]) -> float:
    """
    Apply regional cost multipliers

    Args:
        base_value: Base value before regional adjustment
        region: Region name
        multipliers: Dictionary of regional multipliers

    Returns:
        Adjusted value
    """
    multiplier = multipliers.get(region, 1.0)
    return base_value * multiplier


def enforce_monotonic_increase(series: pd.Series) -> pd.Series:
    """
    Enforce monotonic increase in a series

    Args:
        series: Input series

    Returns:
        Series with monotonic increase enforced
    """
    result = series.copy()
    for i in range(1, len(result)):
        if result.iloc[i] < result.iloc[i-1]:
            result.iloc[i] = result.iloc[i-1]
    return result


def calculate_mass_balance_error(installed_base: pd.Series, demand: pd.Series,
                                retirements: pd.Series) -> pd.Series:
    """
    Calculate mass balance error for validation

    Args:
        installed_base: Installed base series
        demand: Annual demand (additions)
        retirements: Annual retirements

    Returns:
        Series of mass balance errors
    """
    errors = []

    for i in range(1, len(installed_base)):
        ib_start = installed_base.iloc[i-1]
        ib_end = installed_base.iloc[i]
        adds = demand.iloc[i] if i < len(demand) else 0
        retire = retirements.iloc[i] if i < len(retirements) else 0

        expected_ib = ib_start + adds - retire
        error = abs(expected_ib - ib_end)

        if ib_end > 0:
            error_pct = error / ib_end
        else:
            error_pct = error

        errors.append(error_pct)

    return pd.Series(errors, index=installed_base.index[1:])


def export_results_to_csv(results: pd.DataFrame, output_path: str,
                         metadata: Optional[Dict] = None):
    """
    Export results to CSV with optional metadata

    Args:
        results: Results DataFrame
        output_path: Path to save CSV
        metadata: Optional metadata to include as comment
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Add metadata as comment if provided
    if metadata:
        with open(output_path, 'w') as f:
            f.write(f"# Datacenter UPS Battery Forecast\n")
            f.write(f"# Generated: {metadata.get('timestamp', 'N/A')}\n")
            f.write(f"# Region: {metadata.get('region', 'N/A')}\n")
            f.write(f"# Scenario: {metadata.get('scenario', 'N/A')}\n")
            f.write(f"# Tipping Year: {metadata.get('tipping_year', 'N/A')}\n")
            f.write("\n")

    # Write CSV
    results.to_csv(output_path, index=False, mode='a' if metadata else 'w')


def export_results_to_json(results: pd.DataFrame, analysis: Dict,
                          output_path: str, metadata: Optional[Dict] = None):
    """
    Export results to JSON format

    Args:
        results: Results DataFrame
        analysis: Additional analysis dictionary
        output_path: Path to save JSON
        metadata: Optional metadata
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert DataFrame to dictionary format
    forecast_data = {
        'years': results['year'].tolist(),
        'demand': {
            'total_gwh': results['total_demand_gwh'].tolist() if 'total_demand_gwh' in results.columns else [],
            'vrla_gwh': results['vrla_demand_gwh'].tolist() if 'vrla_demand_gwh' in results.columns else [],
            'lithium_gwh': results['lithium_demand_gwh'].tolist() if 'lithium_demand_gwh' in results.columns else [],
        },
        'shares': {
            'vrla_pct': results['vrla_share_pct'].tolist() if 'vrla_share_pct' in results.columns else [],
            'lithium_pct': results['lithium_share_pct'].tolist() if 'lithium_share_pct' in results.columns else [],
        }
    }

    # Add TCO data if available
    if 'vrla_tco_per_kwh' in results.columns:
        forecast_data['tco'] = {
            'vrla_per_kwh': results['vrla_tco_per_kwh'].tolist(),
            'lithium_per_kwh': results['lithium_tco_per_kwh'].tolist(),
            'advantage': results['tco_advantage'].tolist() if 'tco_advantage' in results.columns else []
        }

    # Combine all data
    output_data = {
        'metadata': metadata or {},
        'forecast': forecast_data,
        'analysis': analysis
    }

    # Write JSON
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)


def create_summary_table(results: pd.DataFrame, key_years: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Create summary table for key years

    Args:
        results: Full results DataFrame
        key_years: List of years to include (default: 2025, 2030, 2035)

    Returns:
        Summary DataFrame
    """
    if key_years is None:
        key_years = [2025, 2030, 2035]

    # Filter to key years
    available_years = [year for year in key_years if year in results['year'].values]
    summary = results[results['year'].isin(available_years)].copy()

    # Select key columns
    key_columns = [
        'year', 'total_demand_gwh', 'vrla_demand_gwh', 'lithium_demand_gwh',
        'vrla_share_pct', 'lithium_share_pct'
    ]

    available_columns = [col for col in key_columns if col in summary.columns]
    summary = summary[available_columns]

    # Round for readability
    for col in summary.columns:
        if col != 'year':
            if 'pct' in col:
                summary[col] = summary[col].round(1)
            else:
                summary[col] = summary[col].round(2)

    return summary


def format_number(value: float, decimals: int = 2, suffix: str = '') -> str:
    """
    Format number for display

    Args:
        value: Numeric value
        decimals: Number of decimal places
        suffix: Optional suffix (e.g., '%', 'GWh')

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return 'N/A'

    if abs(value) >= 1e9:
        return f"{value/1e9:.{decimals}f}B{suffix}"
    elif abs(value) >= 1e6:
        return f"{value/1e6:.{decimals}f}M{suffix}"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.{decimals}f}k{suffix}"
    else:
        return f"{value:.{decimals}f}{suffix}"


def validate_scenario_config(scenario: Dict, required_params: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate scenario configuration

    Args:
        scenario: Scenario configuration dictionary
        required_params: List of required parameter names

    Returns:
        Tuple of (is_valid, list_of_missing_params)
    """
    missing = [param for param in required_params if param not in scenario]
    return len(missing) == 0, missing


def aggregate_regional_results(regional_results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Aggregate regional results into global totals

    Args:
        regional_results: Dictionary of regional DataFrames

    Returns:
        Aggregated global DataFrame
    """
    # Get all years across regions
    all_years = set()
    for df in regional_results.values():
        all_years.update(df['year'].values)
    years = sorted(all_years)

    # Initialize aggregated data
    aggregated = pd.DataFrame({'year': years})

    # Columns to sum
    sum_columns = [
        'total_demand_gwh', 'vrla_demand_gwh', 'lithium_demand_gwh',
        'vrla_installed_base_gwh', 'lithium_installed_base_gwh',
        'new_build_demand_gwh', 'replacement_demand_gwh'
    ]

    # Columns to average (weighted by demand)
    avg_columns = [
        'vrla_share_pct', 'lithium_share_pct',
        'vrla_tco_per_kwh', 'lithium_tco_per_kwh'
    ]

    # Sum appropriate columns
    for col in sum_columns:
        aggregated[col] = 0
        for region, df in regional_results.items():
            if col in df.columns:
                for year in years:
                    if year in df['year'].values:
                        value = df[df['year'] == year][col].iloc[0]
                        aggregated.loc[aggregated['year'] == year, col] += value

    # Calculate weighted averages
    total_demand = aggregated['total_demand_gwh']
    for col in avg_columns:
        if any(col in df.columns for df in regional_results.values()):
            weighted_sum = 0
            for region, df in regional_results.items():
                if col in df.columns:
                    for year in years:
                        if year in df['year'].values:
                            value = df[df['year'] == year][col].iloc[0]
                            weight = df[df['year'] == year]['total_demand_gwh'].iloc[0]
                            idx = aggregated['year'] == year
                            if aggregated.loc[idx, 'total_demand_gwh'].iloc[0] > 0:
                                contribution = value * weight / aggregated.loc[idx, 'total_demand_gwh'].iloc[0]
                                if col not in aggregated.columns:
                                    aggregated[col] = 0
                                aggregated.loc[idx, col] += contribution

    # Add metadata
    aggregated['region'] = 'Global'
    aggregated['scenario'] = regional_results[list(regional_results.keys())[0]]['scenario'].iloc[0] if 'scenario' in regional_results[list(regional_results.keys())[0]].columns else 'baseline'

    return aggregated


def print_section_header(title: str, width: int = 70):
    """Print formatted section header"""
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)


def print_subsection_header(title: str, width: int = 70):
    """Print formatted subsection header"""
    print("\n" + "-" * width)
    print(title)
    print("-" * width)