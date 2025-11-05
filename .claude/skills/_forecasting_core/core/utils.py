"""
Utility Functions for Demand Forecasting
Common mathematical and data manipulation utilities
"""

import numpy as np
from typing import List, Tuple, Optional


def rolling_median(data: np.ndarray, window: int = 3) -> np.ndarray:
    """
    Apply rolling median smoothing to data

    Args:
        data: Input array
        window: Window size (default: 3)

    Returns:
        Smoothed array
    """
    if len(data) < window:
        return data.copy()

    result = np.zeros_like(data)
    half_window = window // 2

    for i in range(len(data)):
        start = max(0, i - half_window)
        end = min(len(data), i + half_window + 1)
        result[i] = np.median(data[start:end])

    return result


def calculate_cagr(values: np.ndarray, years: np.ndarray) -> float:
    """
    Calculate Compound Annual Growth Rate

    Args:
        values: Array of values
        years: Array of years

    Returns:
        CAGR as a decimal (e.g., 0.05 for 5%)
    """
    if len(values) < 2:
        return 0.0

    start_val = values[0]
    end_val = values[-1]
    num_years = years[-1] - years[0]

    if start_val <= 0 or end_val <= 0 or num_years <= 0:
        return 0.0

    cagr = (end_val / start_val) ** (1 / num_years) - 1
    return cagr


def theil_sen_slope(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate robust slope and intercept using Theil-Sen estimator

    Args:
        x: Independent variable
        y: Dependent variable

    Returns:
        Tuple of (slope, intercept)
    """
    n = len(x)
    if n < 2:
        return 0.0, y[0] if len(y) > 0 else 0.0

    # Calculate all pairwise slopes
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            if x[j] != x[i]:
                slope = (y[j] - y[i]) / (x[j] - x[i])
                slopes.append(slope)

    if not slopes:
        return 0.0, np.median(y)

    # Median of slopes
    slope = np.median(slopes)

    # Calculate intercept
    intercept = np.median(y - slope * x)

    return slope, intercept


def linear_extrapolation(
    historical_years: List[int],
    historical_values: List[float],
    end_year: int,
    max_cagr: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extrapolate values linearly using Theil-Sen robust regression

    Args:
        historical_years: Historical years
        historical_values: Historical values
        end_year: Final year to forecast to
        max_cagr: Maximum CAGR cap (default: 5%)

    Returns:
        Tuple of (all_years, all_values) including historical and forecast
    """
    years = np.array(historical_years)
    values = np.array(historical_values)

    # Robust linear fit
    slope, intercept = theil_sen_slope(years, values)

    # Apply CAGR cap if needed
    if len(values) > 0 and values[0] > 0:
        implied_cagr = calculate_cagr(
            np.array([intercept + slope * years[0], intercept + slope * years[-1]]),
            years[[0, -1]]
        )

        if abs(implied_cagr) > max_cagr:
            # Re-calculate slope with capped CAGR
            capped_cagr = max_cagr if implied_cagr > 0 else -max_cagr
            start_val = values[0]
            num_years = years[-1] - years[0]
            end_val = start_val * (1 + capped_cagr) ** num_years
            slope = (end_val - start_val) / num_years
            intercept = start_val - slope * years[0]

    # Generate forecast years
    forecast_years = np.arange(years[-1] + 1, end_year + 1)
    all_years = np.concatenate([years, forecast_years])

    # Calculate all values
    all_values = intercept + slope * all_years

    # Ensure non-negative
    all_values = np.maximum(all_values, 0)

    return all_years, all_values


def log_cagr_forecast(
    historical_years: List[int],
    historical_costs: List[float],
    end_year: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forecast cost curves using log-CAGR method

    Args:
        historical_years: Historical years
        historical_costs: Historical cost values
        end_year: Final year to forecast to

    Returns:
        Tuple of (all_years, all_costs) including historical and forecast
    """
    years = np.array(historical_years)
    costs = np.array(historical_costs)

    # Transform to log scale
    log_costs = np.log(costs)

    # Linear fit on log scale
    slope, intercept = np.polyfit(years, log_costs, 1)

    # Generate forecast years
    forecast_years = np.arange(years[-1] + 1, end_year + 1)
    all_years = np.concatenate([years, forecast_years])

    # Forecast in log scale
    log_forecast = intercept + slope * all_years

    # Convert back to normal scale
    all_costs = np.exp(log_forecast)

    return all_years, all_costs


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def clamp_array(arr: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
    """Clamp all values in array between min and max"""
    return np.clip(arr, min_val, max_val)


def find_intersection(
    years: np.ndarray,
    series1: np.ndarray,
    series2: np.ndarray
) -> Optional[int]:
    """
    Find first year where series1 crosses below series2

    Args:
        years: Array of years
        series1: First series (e.g., EV costs)
        series2: Second series (e.g., ICE costs)

    Returns:
        Year of first intersection, or None if no intersection
    """
    for i, year in enumerate(years):
        if series1[i] < series2[i]:
            return int(year)
    return None


def validate_forecast_consistency(
    market: np.ndarray,
    bev: np.ndarray,
    phev: np.ndarray,
    ice: np.ndarray,
    epsilon: float = 1e-6
) -> Tuple[bool, str]:
    """
    Validate that BEV + PHEV + ICE <= Market and all values >= 0

    Args:
        market: Market demand array
        bev: BEV demand array
        phev: PHEV demand array
        ice: ICE demand array
        epsilon: Tolerance for comparison

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check non-negative
    if np.any(market < -epsilon):
        return False, "Market demand has negative values"
    if np.any(bev < -epsilon):
        return False, "BEV demand has negative values"
    if np.any(phev < -epsilon):
        return False, "PHEV demand has negative values"
    if np.any(ice < -epsilon):
        return False, "ICE demand has negative values"

    # Check sum constraint
    total = bev + phev + ice
    if np.any(total > market + epsilon):
        max_violation = np.max(total - market)
        return False, f"Sum exceeds market by up to {max_violation:.2f}"

    return True, "Validation passed"
