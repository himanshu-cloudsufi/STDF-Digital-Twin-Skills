"""
Validation Utilities
Forecast consistency checking and data validation
"""

import numpy as np
from typing import Tuple, List, Optional, Union


def validate_forecast_consistency(
    market: np.ndarray,
    components: List[np.ndarray],
    tolerance: float = 0.001
) -> Tuple[bool, str]:
    """
    Validate that sum of components <= market and all values >= 0

    Args:
        market: Market demand array
        components: List of component arrays (e.g., [bev, phev, ice])
        tolerance: Relative tolerance for comparison (default: 0.1%)

    Returns:
        Tuple of (is_valid, error_message)
    """
    epsilon = np.max(market) * tolerance if len(market) > 0 else 1e-6

    # Check market non-negative
    if np.any(market < -epsilon):
        return False, "Market demand has negative values"

    # Check each component non-negative
    for i, component in enumerate(components):
        if np.any(component < -epsilon):
            return False, f"Component {i} has negative values"

    # Check sum constraint
    total = np.sum(components, axis=0)
    if np.any(total > market + epsilon):
        max_violation = np.max(total - market)
        max_relative = max_violation / np.max(market) if np.max(market) > 0 else 0
        return False, f"Sum exceeds market by up to {max_violation:.2f} ({max_relative:.2%})"

    return True, "Validation passed"


def validate_non_negative(
    array: np.ndarray,
    name: str = "Array",
    epsilon: float = 1e-6
) -> Tuple[bool, str]:
    """
    Validate that array has no negative values

    Args:
        array: Array to validate
        name: Name for error messages
        epsilon: Tolerance for comparison

    Returns:
        Tuple of (is_valid, error_message)
    """
    if np.any(array < -epsilon):
        min_val = np.min(array)
        return False, f"{name} has negative values (minimum: {min_val:.4f})"

    return True, "Validation passed"


def validate_monotonic_within_tolerance(
    array: np.ndarray,
    tolerance: float = 0.5,
    direction: str = "increasing"
) -> Tuple[bool, str]:
    """
    Validate that array is approximately monotonic (allowing some violations)

    Args:
        array: Array to validate
        tolerance: Maximum fraction of violations allowed (default: 50%)
        direction: "increasing" or "decreasing"

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(array) < 2:
        return True, "Validation passed (too few points)"

    # Calculate differences
    diffs = np.diff(array)

    # Count violations
    if direction == "increasing":
        violations = np.sum(diffs < 0)
    elif direction == "decreasing":
        violations = np.sum(diffs > 0)
    else:
        return False, f"Invalid direction: {direction}"

    violation_rate = violations / len(diffs)

    if violation_rate > tolerance:
        return False, f"Too many monotonicity violations ({violation_rate:.1%} > {tolerance:.1%})"

    return True, "Validation passed"


def validate_cagr_bounds(
    values: np.ndarray,
    years: np.ndarray,
    max_cagr: float = 0.20
) -> Tuple[bool, str]:
    """
    Validate that CAGR is within reasonable bounds

    Args:
        values: Value array
        years: Year array
        max_cagr: Maximum allowed CAGR magnitude (default: 20%)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(values) < 2 or len(years) < 2:
        return True, "Validation passed (too few points)"

    from .utils import calculate_cagr

    cagr = calculate_cagr(values, years)

    if abs(cagr) > max_cagr:
        return False, f"CAGR {cagr:.2%} exceeds maximum {max_cagr:.2%}"

    return True, "Validation passed"


def validate_smooth_transitions(
    array: np.ndarray,
    max_jump: float = 0.5,
    name: str = "Array"
) -> Tuple[bool, str]:
    """
    Validate that year-over-year changes are not too large

    Args:
        array: Array to validate
        max_jump: Maximum allowed relative change (default: 50%)
        name: Name for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(array) < 2:
        return True, "Validation passed (too few points)"

    # Calculate relative changes
    diffs = np.diff(array)
    relative_changes = np.abs(diffs / (array[:-1] + 1e-10))  # Add epsilon to avoid division by zero

    max_change = np.max(relative_changes)

    if max_change > max_jump:
        return False, f"{name} has abrupt transition ({max_change:.1%} > {max_jump:.1%})"

    return True, "Validation passed"


def validate_shares_sum_to_one(
    shares: List[np.ndarray],
    tolerance: float = 0.01
) -> Tuple[bool, str]:
    """
    Validate that shares sum to approximately 1.0

    Args:
        shares: List of share arrays
        tolerance: Maximum deviation from 1.0 (default: 1%)

    Returns:
        Tuple of (is_valid, error_message)
    """
    total = np.sum(shares, axis=0)
    deviations = np.abs(total - 1.0)
    max_deviation = np.max(deviations)

    if max_deviation > tolerance:
        return False, f"Shares do not sum to 1.0 (max deviation: {max_deviation:.3f})"

    return True, "Validation passed"


def validate_data_availability(
    years: Union[list, np.ndarray],
    values: Union[list, np.ndarray],
    min_points: int = 3
) -> Tuple[bool, str]:
    """
    Validate that sufficient data is available

    Args:
        years: Year array/list
        values: Value array/list
        min_points: Minimum required data points

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(years) < min_points or len(values) < min_points:
        return False, f"Insufficient data points ({len(years)} < {min_points})"

    if len(years) != len(values):
        return False, f"Mismatched array lengths (years: {len(years)}, values: {len(values)})"

    return True, "Validation passed"


def validate_forecast_result(
    forecast: dict,
    required_keys: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Validate forecast result dictionary structure

    Args:
        forecast: Forecast result dictionary
        required_keys: List of required keys (if None, uses default set)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if required_keys is None:
        required_keys = ['years', 'market', 'validation']

    missing_keys = [key for key in required_keys if key not in forecast]

    if missing_keys:
        return False, f"Missing required keys: {missing_keys}"

    # Validate array lengths match
    if 'years' in forecast:
        year_len = len(forecast['years'])
        for key in ['market', 'bev', 'phev', 'ice', 'ev']:
            if key in forecast and len(forecast[key]) != year_len:
                return False, f"Array length mismatch: {key} has {len(forecast[key])} points, expected {year_len}"

    return True, "Validation passed"


def run_comprehensive_validation(
    market: np.ndarray,
    bev: np.ndarray,
    phev: np.ndarray,
    ice: np.ndarray,
    years: np.ndarray
) -> dict:
    """
    Run comprehensive validation suite on forecast

    Args:
        market: Market demand array
        bev: BEV demand array
        phev: PHEV demand array
        ice: ICE demand array
        years: Year array

    Returns:
        Dictionary with validation results
    """
    results = {
        'all_passed': True,
        'checks': []
    }

    # 1. Check sum consistency
    is_valid, msg = validate_forecast_consistency(market, [bev, phev, ice])
    results['checks'].append({'name': 'sum_consistency', 'passed': is_valid, 'message': msg})
    if not is_valid:
        results['all_passed'] = False

    # 2. Check non-negative
    for arr, name in [(market, 'market'), (bev, 'bev'), (phev, 'phev'), (ice, 'ice')]:
        is_valid, msg = validate_non_negative(arr, name)
        results['checks'].append({'name': f'{name}_non_negative', 'passed': is_valid, 'message': msg})
        if not is_valid:
            results['all_passed'] = False

    # 3. Check smooth transitions
    for arr, name in [(market, 'market'), (bev, 'bev'), (ice, 'ice')]:
        is_valid, msg = validate_smooth_transitions(arr, max_jump=0.5, name=name)
        results['checks'].append({'name': f'{name}_smooth', 'passed': is_valid, 'message': msg})
        if not is_valid:
            results['all_passed'] = False

    # 4. Check CAGRs
    for arr, name in [(market, 'market'), (bev, 'bev')]:
        is_valid, msg = validate_cagr_bounds(arr, years, max_cagr=0.25)
        results['checks'].append({'name': f'{name}_cagr', 'passed': is_valid, 'message': msg})
        if not is_valid:
            results['all_passed'] = False

    return results
