"""
Common modules for light vehicle demand forecasting.

Shared utilities for two-wheeler and three-wheeler demand forecasting.
"""

from .utils import (
    rolling_median,
    calculate_cagr,
    log_cagr_forecast,
    linear_extrapolation,
    find_intersection,
    clamp_array,
    validate_forecast_consistency,
    smooth_time_series
)

__all__ = [
    'rolling_median',
    'calculate_cagr',
    'log_cagr_forecast',
    'linear_extrapolation',
    'find_intersection',
    'clamp_array',
    'validate_forecast_consistency',
    'smooth_time_series'
]
