"""
Utility Functions for Two-Wheeler Demand Forecasting
Provides smoothing, CAGR calculation, forecasting, and validation utilities
"""

import numpy as np
from typing import Tuple, List, Optional
from scipy.stats import theilslopes


def rolling_median(data: np.ndarray, window: int) -> np.ndarray:
    """
    Apply rolling median smoothing to data

    Args:
        data: Input data array
        window: Window size for rolling median

    Returns:
        Smoothed data array
    """
    if len(data) < window:
        return data

    smoothed = np.zeros_like(data, dtype=float)
    half_window = window // 2

    for i in range(len(data)):
        start = max(0, i - half_window)
        end = min(len(data), i + half_window + 1)
        smoothed[i] = np.median(data[start:end])

    return smoothed


def calculate_cagr(values: np.ndarray, years: np.ndarray) -> float:
    """
    Calculate Compound Annual Growth Rate

    Args:
        values: Array of values
        years: Array of corresponding years

    Returns:
        CAGR as decimal (e.g., 0.05 for 5%)
    """
    if len(values) < 2 or values[0] <= 0 or values[-1] <= 0:
        return 0.0

    n_years = years[-1] - years[0]
    if n_years <= 0:
        return 0.0

    cagr = (values[-1] / values[0]) ** (1 / n_years) - 1
    return cagr


def log_cagr_forecast(
    historical_years: list,
    historical_values: list,
    end_year: int,
    stable_window: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forecast using log-scale CAGR extrapolation

    Args:
        historical_years: Historical year values
        historical_values: Historical data values
        end_year: Final forecast year
        stable_window: Number of recent years to use for CAGR (None = use all)

    Returns:
        Tuple of (forecast_years, forecast_values)
    """
    years = np.array(historical_years)
    values = np.array(historical_values)

    # Filter positive values only
    mask = values > 0
    years = years[mask]
    values = values[mask]

    if len(values) < 2:
        # Not enough data, return flat forecast
        forecast_years = np.arange(years[0] if len(years) > 0 else 2020, end_year + 1)
        forecast_values = np.full_like(forecast_years, values[0] if len(values) > 0 else 1000.0, dtype=float)
        return forecast_years, forecast_values

    # Use recent window for CAGR if specified
    if stable_window is not None and len(years) > stable_window:
        years = years[-stable_window:]
        values = values[-stable_window:]

    # Transform to log scale
    log_values = np.log(values)

    # Calculate CAGR in log space
    cagr = calculate_cagr(values, years)

    # Generate forecast years
    last_year = years[-1]
    forecast_years = np.arange(years[0], end_year + 1)

    # Extrapolate in log space
    log_forecast = np.zeros_like(forecast_years, dtype=float)
    for i, year in enumerate(forecast_years):
        if year <= last_year:
            # Interpolate historical
            log_forecast[i] = np.interp(year, years, log_values)
        else:
            # Extrapolate forward
            years_ahead = year - last_year
            log_forecast[i] = log_values[-1] + np.log(1 + cagr) * years_ahead

    # Convert back to normal scale
    forecast_values = np.exp(log_forecast)

    return forecast_years, forecast_values


def linear_extrapolation(
    historical_years: list,
    historical_values: list,
    end_year: int,
    max_cagr: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forecast using Theil-Sen robust linear regression with CAGR capping

    Args:
        historical_years: Historical year values
        historical_values: Historical data values
        end_year: Final forecast year
        max_cagr: Maximum allowed CAGR (default: 0.05 = 5%)

    Returns:
        Tuple of (forecast_years, forecast_values)
    """
    years = np.array(historical_years)
    values = np.array(historical_values)

    if len(values) < 2:
        # Not enough data
        forecast_years = np.arange(years[0] if len(years) > 0 else 2020, end_year + 1)
        forecast_values = np.full_like(forecast_years, values[0] if len(values) > 0 else 1000000.0, dtype=float)
        return forecast_years, forecast_values

    # Fit Theil-Sen regression (robust to outliers)
    try:
        slope, intercept, _, _ = theilslopes(values, years)
    except:
        # Fallback to simple linear regression
        slope = (values[-1] - values[0]) / (years[-1] - years[0])
        intercept = values[0] - slope * years[0]

    # Generate forecast years
    forecast_years = np.arange(years[0], end_year + 1)
    forecast_values = slope * forecast_years + intercept

    # Apply CAGR cap to future values
    last_year = years[-1]
    last_value = values[-1]

    for i, year in enumerate(forecast_years):
        if year > last_year:
            years_ahead = year - last_year
            # Calculate implied CAGR
            if last_value > 0:
                max_value = last_value * ((1 + max_cagr) ** years_ahead)
                min_value = last_value * ((1 - max_cagr) ** years_ahead)
                # Clamp forecast value
                forecast_values[i] = np.clip(forecast_values[i], min_value, max_value)

    # Ensure non-negative
    forecast_values = np.maximum(forecast_values, 0)

    return forecast_years, forecast_values


def find_intersection(
    years: np.ndarray,
    series1: np.ndarray,
    series2: np.ndarray
) -> Optional[int]:
    """
    Find first intersection point where series1 crosses below series2

    Args:
        years: Year array
        series1: First series (e.g., EV costs)
        series2: Second series (e.g., ICE costs)

    Returns:
        Year of first intersection, or None if no intersection
    """
    diff = series1 - series2

    # Find where sign changes from positive to negative (series1 crosses below series2)
    for i in range(len(diff) - 1):
        if diff[i] > 0 and diff[i + 1] <= 0:
            # Linear interpolation to find exact crossing year
            if diff[i] != diff[i + 1]:
                fraction = -diff[i] / (diff[i + 1] - diff[i])
                crossing_year = years[i] + fraction * (years[i + 1] - years[i])
                return int(np.round(crossing_year))
            else:
                return int(years[i + 1])

    return None


def clamp_array(arr: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
    """
    Clamp array values to [min_val, max_val]

    Args:
        arr: Input array
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped array
    """
    return np.clip(arr, min_val, max_val)


def validate_forecast_consistency(
    market: np.ndarray,
    ev: np.ndarray,
    ice: np.ndarray,
    tolerance: float = 0.01
) -> Tuple[bool, str]:
    """
    Validate forecast consistency (sum checks, non-negativity)

    Args:
        market: Market demand array
        ev: EV demand array
        ice: ICE demand array
        tolerance: Tolerance for sum check (1% default)

    Returns:
        Tuple of (is_valid, message)
    """
    # Check non-negativity
    if np.any(market < 0) or np.any(ev < 0) or np.any(ice < 0):
        return False, "Negative values detected in forecast"

    # Check sum consistency: EV + ICE should equal Market (within tolerance)
    total = ev + ice
    relative_diff = np.abs(total - market) / np.maximum(market, 1)

    if np.any(relative_diff > tolerance):
        max_diff_idx = np.argmax(relative_diff)
        return False, f"Sum consistency violated at index {max_diff_idx}: EV+ICE={total[max_diff_idx]:.0f}, Market={market[max_diff_idx]:.0f}"

    # Check that EV and ICE don't exceed market
    if np.any(ev > market) or np.any(ice > market):
        return False, "EV or ICE demand exceeds market demand"

    return True, "All validation checks passed"


def smooth_time_series(
    years: np.ndarray,
    values: np.ndarray,
    method: str = "median",
    window: int = 3
) -> np.ndarray:
    """
    Smooth time series data

    Args:
        years: Year array
        values: Value array
        method: Smoothing method ("median", "mean")
        window: Window size

    Returns:
        Smoothed values
    """
    if method == "median":
        return rolling_median(values, window)
    elif method == "mean":
        # Rolling mean
        smoothed = np.zeros_like(values, dtype=float)
        half_window = window // 2

        for i in range(len(values)):
            start = max(0, i - half_window)
            end = min(len(values), i + half_window + 1)
            smoothed[i] = np.mean(values[start:end])

        return smoothed
    else:
        return values


if __name__ == "__main__":
    # Test utilities
    print("Testing Utility Functions...")

    # Test rolling median
    data = np.array([1, 5, 2, 8, 3, 9, 4, 7])
    smoothed = rolling_median(data, 3)
    print(f"\nRolling Median Test:")
    print(f"Original: {data}")
    print(f"Smoothed: {smoothed}")

    # Test CAGR
    values = np.array([100, 110, 121, 133])
    years = np.array([2020, 2021, 2022, 2023])
    cagr = calculate_cagr(values, years)
    print(f"\nCAGR Test:")
    print(f"Values: {values}")
    print(f"CAGR: {cagr:.2%}")

    # Test log forecast
    hist_years = [2015, 2016, 2017, 2018, 2019, 2020]
    hist_values = [1000, 950, 900, 850, 800, 750]
    forecast_years, forecast_values = log_cagr_forecast(hist_years, hist_values, 2025)
    print(f"\nLog-CAGR Forecast Test:")
    print(f"Forecast 2025: {forecast_values[-1]:.2f}")

    # Test intersection
    years = np.array([2020, 2021, 2022, 2023, 2024, 2025])
    ev_cost = np.array([2000, 1800, 1600, 1400, 1200, 1000])
    ice_cost = np.array([1500, 1520, 1540, 1560, 1580, 1600])
    tipping = find_intersection(years, ev_cost, ice_cost)
    print(f"\nIntersection Test:")
    print(f"Tipping Point: {tipping}")

    # Test validation
    market = np.array([1000, 1100, 1200])
    ev = np.array([100, 200, 300])
    ice = np.array([900, 900, 900])
    is_valid, msg = validate_forecast_consistency(market, ev, ice)
    print(f"\nValidation Test:")
    print(f"Valid: {is_valid}, Message: {msg}")
