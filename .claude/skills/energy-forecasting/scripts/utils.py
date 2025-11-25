"""
Utility Functions for Energy Forecasting (SWB)
Common mathematical and data manipulation utilities
"""

import numpy as np
from typing import List, Tuple, Optional, Dict


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
        series1: First series (e.g., SWB costs)
        series2: Second series (e.g., Coal/Gas costs)

    Returns:
        Year of first intersection, or None if no intersection
    """
    for i, year in enumerate(years):
        if series1[i] < series2[i]:
            return int(year)
    return None


def calculate_capacity_factor(
    generation_gwh: float,
    capacity_gw: float,
    hours_per_year: float = 8760
) -> float:
    """
    Calculate capacity factor from generation and capacity

    Args:
        generation_gwh: Annual generation in GWh
        capacity_gw: Installed capacity in GW
        hours_per_year: Hours per year (default: 8760)

    Returns:
        Capacity factor (0.0 to 1.0)
    """
    if capacity_gw <= 0:
        return 0.0

    theoretical_max = capacity_gw * hours_per_year
    cf = generation_gwh / theoretical_max

    # Clamp to valid range
    return clamp(cf, 0.0, 1.0)


def convert_capacity_to_generation(
    capacity_gw: np.ndarray,
    capacity_factor: float,
    hours_per_year: float = 8760
) -> np.ndarray:
    """
    Convert capacity to generation using capacity factor

    Args:
        capacity_gw: Installed capacity in GW
        capacity_factor: Capacity factor (0.0 to 1.0)
        hours_per_year: Hours per year (default: 8760)

    Returns:
        Generation in GWh
    """
    return capacity_gw * capacity_factor * hours_per_year


def convert_generation_to_capacity(
    generation_gwh: np.ndarray,
    capacity_factor: float,
    hours_per_year: float = 8760
) -> np.ndarray:
    """
    Convert generation to capacity using capacity factor

    Args:
        generation_gwh: Annual generation in GWh
        capacity_factor: Capacity factor (0.0 to 1.0)
        hours_per_year: Hours per year (default: 8760)

    Returns:
        Capacity in GW
    """
    if capacity_factor <= 0:
        return np.zeros_like(generation_gwh)

    return generation_gwh / (capacity_factor * hours_per_year)


def forecast_demand_growth(
    historical_years: List[int],
    historical_demand: List[float],
    end_year: int,
    min_growth_rate: float = 0.005,
    max_growth_rate: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forecast electricity demand using YoY growth averaging.
    Per swb_instructions_v4 Section 2: "Take average of historical rates to forecast forward"

    Args:
        historical_years: Historical years
        historical_demand: Historical demand values (TWh or GWh)
        end_year: Final year to forecast to
        min_growth_rate: Minimum annual growth rate (default: 0.5%)
        max_growth_rate: Maximum annual growth rate (default: 5%)

    Returns:
        Tuple of (all_years, all_demand) including historical and forecast
    """
    years = np.array(historical_years)
    demand = np.array(historical_demand)

    if len(years) < 2:
        # Not enough data, return constant
        forecast_years = np.arange(years[-1] + 1, end_year + 1)
        all_years = np.concatenate([years, forecast_years])
        all_demand = np.full(len(all_years), demand[-1])
        return all_years, all_demand

    # Calculate YoY growth rates
    yoy_rates = []
    for i in range(1, len(demand)):
        if demand[i-1] > 0:
            rate = (demand[i] - demand[i-1]) / demand[i-1]
            rate = clamp(rate, -0.1, 0.1)  # Cap outliers at ±10%
            yoy_rates.append(rate)

    if not yoy_rates:
        avg_growth = 0.02  # Default 2% growth
    else:
        # Average of last 5 years (or all if less) per instructions
        recent_rates = yoy_rates[-5:] if len(yoy_rates) >= 5 else yoy_rates
        avg_growth = np.mean(recent_rates)

    # Bound growth rate to reasonable range
    avg_growth = clamp(avg_growth, min_growth_rate, max_growth_rate)

    # Forecast forward
    forecast_years = np.arange(years[-1] + 1, end_year + 1)
    forecast_demand = []
    current = demand[-1]

    for _ in forecast_years:
        current = current * (1 + avg_growth)
        forecast_demand.append(current)

    all_years = np.concatenate([years, forecast_years])
    all_demand = np.concatenate([demand, np.array(forecast_demand)])

    return all_years, all_demand


def yoy_growth_average(
    historical_years: List[int],
    historical_values: List[float],
    end_year: int,
    max_yoy_growth: float = 0.50,
    decay_rate: float = 0.0,
    floor_growth_rate: float = 0.02
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forecast using year-over-year growth averaging method with optional decay.

    Growth rate maturation: as technologies mature, growth rates naturally decrease.
    This prevents unrealistic compounding where SWB exceeds total demand.

    Args:
        historical_years: Historical years
        historical_values: Historical values
        end_year: Final year to forecast to
        max_yoy_growth: Maximum YoY growth rate cap (default: 50%)
        decay_rate: Annual decay applied to growth rate (default: 0, no decay)
                    E.g., 0.05 means growth rate decreases by 5% each year
        floor_growth_rate: Minimum growth rate floor (default: 2%)

    Returns:
        Tuple of (all_years, all_values) including historical and forecast
    """
    years = np.array(historical_years)
    values = np.array(historical_values)

    if len(years) < 2:
        # Not enough data, return constant
        forecast_years = np.arange(years[-1] + 1, end_year + 1)
        all_years = np.concatenate([years, forecast_years])
        all_values = np.full(len(all_years), values[-1])
        return all_years, all_values

    # Calculate year-over-year growth rates
    yoy_growth_rates = []
    for i in range(1, len(values)):
        if values[i-1] > 0:
            growth_rate = (values[i] - values[i-1]) / values[i-1]
            # Cap growth rate
            growth_rate = clamp(growth_rate, -max_yoy_growth, max_yoy_growth)
            yoy_growth_rates.append(growth_rate)

    if not yoy_growth_rates:
        # No valid growth rates, use last value
        forecast_years = np.arange(years[-1] + 1, end_year + 1)
        all_years = np.concatenate([years, forecast_years])
        all_values = np.full(len(all_years), values[-1])
        return all_years, all_values

    # Base growth rate (median for robustness)
    base_growth_rate = np.median(yoy_growth_rates)

    # Generate forecast with optional decay
    forecast_years = np.arange(years[-1] + 1, end_year + 1)
    forecast_values = []

    current_value = values[-1]
    current_growth_rate = base_growth_rate

    for i, _ in enumerate(forecast_years):
        # Apply time-based decay to growth rate
        if decay_rate > 0 and i > 0:
            current_growth_rate = current_growth_rate * (1 - decay_rate)

        # Ensure growth rate doesn't fall below floor
        effective_growth_rate = max(current_growth_rate, floor_growth_rate)

        # Cap at maximum
        effective_growth_rate = min(effective_growth_rate, max_yoy_growth)

        # Apply growth
        current_value = current_value * (1 + effective_growth_rate)
        forecast_values.append(max(0, current_value))  # Ensure non-negative

    all_years = np.concatenate([years, forecast_years])
    all_values = np.concatenate([values, np.array(forecast_values)])

    return all_years, all_values


def validate_energy_balance(
    total_generation: np.ndarray,
    swb_generation: np.ndarray,
    coal_generation: np.ndarray,
    gas_generation: np.ndarray,
    other_generation: np.ndarray,
    tolerance: float = 0.02
) -> Tuple[bool, str]:
    """
    Validate energy balance: SWB + Coal + Gas + Other = Total

    Args:
        total_generation: Total electricity generation
        swb_generation: SWB generation (Solar + Wind + Battery discharge)
        coal_generation: Coal generation
        gas_generation: Gas generation
        other_generation: Other generation (nuclear, hydro, etc.)
        tolerance: Tolerance as fraction (default: 2%)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check non-negative
    if np.any(total_generation < 0):
        return False, "Total generation has negative values"
    if np.any(swb_generation < 0):
        return False, "SWB generation has negative values"
    if np.any(coal_generation < 0):
        return False, "Coal generation has negative values"
    if np.any(gas_generation < 0):
        return False, "Gas generation has negative values"
    if np.any(other_generation < 0):
        return False, "Other generation has negative values"

    # Check energy balance
    sum_generation = swb_generation + coal_generation + gas_generation + other_generation
    max_total = np.max(total_generation)

    if max_total > 0:
        relative_error = np.abs(sum_generation - total_generation) / max_total
        if np.any(relative_error > tolerance):
            max_error = np.max(relative_error)
            return False, f"Energy balance violated by up to {max_error:.2%}"

    return True, "Energy balance validation passed"


def validate_capacity_factors(
    capacity_factors: Dict[str, float],
    min_cf: float = 0.05,
    max_cf: float = 0.70
) -> Tuple[bool, str]:
    """
    Validate that capacity factors are within physical bounds

    Args:
        capacity_factors: Dictionary of technology -> CF
        min_cf: Minimum CF (default: 0.05 or 5%)
        max_cf: Maximum CF (default: 0.70 or 70%)

    Returns:
        Tuple of (is_valid, error_message)
    """
    for tech, cf in capacity_factors.items():
        if cf < min_cf:
            return False, f"{tech} CF {cf:.2%} is below minimum {min_cf:.2%}"
        if cf > max_cf and tech not in ["Nuclear", "Coal_Power", "Natural_Gas_Power"]:
            # Allow higher CFs for baseload technologies
            return False, f"{tech} CF {cf:.2%} exceeds maximum {max_cf:.2%}"

    return True, "Capacity factor validation passed"


if __name__ == "__main__":
    # Test utilities
    print("Testing Energy Forecasting Utilities...")

    # Test capacity factor calculation
    generation = 1000  # GWh
    capacity = 1.0  # GW
    cf = calculate_capacity_factor(generation, capacity)
    print(f"\nCapacity Factor: {cf:.2%}")

    # Test capacity to generation conversion
    capacity_array = np.array([1.0, 2.0, 3.0])  # GW
    cf = 0.25
    generation = convert_capacity_to_generation(capacity_array, cf)
    print(f"\nCapacity: {capacity_array} GW")
    print(f"CF: {cf:.2%}")
    print(f"Generation: {generation} GWh")

    # Test YoY growth averaging
    years = [2015, 2016, 2017, 2018, 2019, 2020]
    values = [100, 120, 150, 180, 220, 270]
    forecast_years, forecast_values = yoy_growth_average(years, values, 2025)
    print(f"\nYoY Growth Forecast:")
    print(f"Years: {forecast_years}")
    print(f"Values: {forecast_values}")
