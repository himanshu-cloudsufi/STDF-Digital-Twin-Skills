"""
Logistic Models Module
S-curve fitting and adoption modeling for disruptive technologies
"""

import numpy as np
from typing import Tuple, Optional
from scipy.optimize import differential_evolution
from .utils import clamp_array


def logistic_function(
    t: np.ndarray,
    L: float,
    k: float,
    t0: float
) -> np.ndarray:
    """
    Logistic growth function (S-curve)

    Args:
        t: Time array
        L: Ceiling (maximum value, typically 1.0 for 100%)
        k: Growth rate (steepness of the curve)
        t0: Midpoint year (inflection point)

    Returns:
        Logistic curve values
    """
    return L / (1 + np.exp(-k * (t - t0)))


def fit_logistic_curve(
    years: np.ndarray,
    shares: np.ndarray,
    L: Optional[float] = None,
    initial_guess: Optional[dict] = None
) -> Tuple[float, float, float]:
    """
    Fit logistic curve to share data using differential evolution

    Args:
        years: Array of years
        shares: Array of share values (typically 0-1 range)
        L: Ceiling parameter (if None, defaults to 1.0)
        initial_guess: Optional dict with 'k' and 't0' for seeding

    Returns:
        Tuple of (L, k, t0) parameters
    """
    if L is None:
        L = 1.0

    # Handle sparse data - use defaults
    if len(years) < 3:
        k = initial_guess.get('k', 0.4) if initial_guess else 0.4
        t0 = initial_guess.get('t0', years[0]) if initial_guess and len(years) > 0 else 2020
        return L, k, t0

    def objective(params):
        k, t0 = params
        predicted = logistic_function(years, L, k, t0)
        return np.sum((shares - predicted) ** 2)

    # Set bounds for optimization
    k_bounds = (0.05, 1.5)  # Growth rate bounds
    t0_bounds = (np.min(years) - 5, np.max(years) + 10)  # Inflection point bounds

    # Use initial guess if provided
    if initial_guess:
        # Narrow bounds around initial guess
        k_init = initial_guess.get('k', 0.4)
        t0_init = initial_guess.get('t0', np.median(years))
        k_bounds = (max(0.05, k_init - 0.3), min(1.5, k_init + 0.3))
        t0_bounds = (t0_init - 5, t0_init + 5)

    bounds = [k_bounds, t0_bounds]

    try:
        result = differential_evolution(
            objective,
            bounds,
            seed=42,
            maxiter=1000,
            tol=1e-6,
            atol=1e-8,
            workers=1
        )
        k, t0 = result.x
    except Exception as e:
        # Fallback to defaults if optimization fails
        k = initial_guess.get('k', 0.4) if initial_guess else 0.4
        t0 = initial_guess.get('t0', years[0]) if initial_guess and len(years) > 0 else years[0]

    return L, k, t0


def forecast_logistic_share(
    historical_years: np.ndarray,
    historical_shares: np.ndarray,
    end_year: int,
    L: float = 1.0,
    initial_guess: Optional[dict] = None
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Fit logistic curve to historical data and forecast to end_year

    Args:
        historical_years: Historical years
        historical_shares: Historical share values
        end_year: Final year to forecast to
        L: Logistic ceiling (default: 1.0 = 100%)
        initial_guess: Optional dict with 'k' and 't0' for seeding

    Returns:
        Tuple of (forecast_years, forecast_shares, parameters)
    """
    # Fit curve
    L_fit, k, t0 = fit_logistic_curve(historical_years, historical_shares, L, initial_guess)

    # Generate forecast years
    min_year = int(np.min(historical_years))
    forecast_years = np.arange(min_year, end_year + 1)

    # Calculate forecast shares
    forecast_shares = logistic_function(forecast_years, L_fit, k, t0)
    forecast_shares = clamp_array(forecast_shares, 0, 1)

    parameters = {
        'L': L_fit,
        'k': k,
        't0': t0
    }

    return forecast_years, forecast_shares, parameters


def linear_to_logistic_transition(
    historical_years: np.ndarray,
    historical_shares: np.ndarray,
    tipping_point: Optional[int],
    end_year: int,
    L: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Generate forecast with linear growth pre-tipping, logistic post-tipping

    Args:
        historical_years: Historical years
        historical_shares: Historical share values
        tipping_point: Tipping point year (transition from linear to logistic)
        end_year: Final year to forecast to
        L: Logistic ceiling (default: 1.0)

    Returns:
        Tuple of (forecast_years, forecast_shares, info_dict)
    """
    hist_years = np.array(historical_years)
    hist_shares = np.array(historical_shares)

    if tipping_point is None:
        # No tipping point - use simple linear extrapolation
        from .utils import linear_extrapolation
        forecast_years, forecast_shares = linear_extrapolation(
            historical_years,
            historical_shares,
            end_year,
            max_cagr=0.05
        )
        forecast_shares = clamp_array(forecast_shares, 0, 1)
        return forecast_years, forecast_shares, {'mode': 'linear_only', 'tipping_point': None}

    # Extend historical data to tipping point with linear trend
    if tipping_point > hist_years[-1]:
        # Calculate linear slope from recent history
        if len(hist_shares) >= 2:
            slope = (hist_shares[-1] - hist_shares[-2]) / (hist_years[-1] - hist_years[-2])
        else:
            slope = 0.01  # Default small growth

        # Extend years to tipping point
        extended_years = np.arange(hist_years[-1] + 1, tipping_point + 1)
        extended_shares = hist_shares[-1] + slope * (extended_years - hist_years[-1])
        extended_shares = np.clip(extended_shares, 0, 1)

        # Combine historical and extended
        combined_years = np.concatenate([hist_years, extended_years])
        combined_shares = np.concatenate([hist_shares, extended_shares])
    else:
        combined_years = hist_years
        combined_shares = hist_shares

    # Fit logistic curve to combined data (with t0 seeded near tipping point)
    initial_guess = {'k': 0.4, 't0': tipping_point}
    L_fit, k, t0 = fit_logistic_curve(combined_years, combined_shares, L, initial_guess)

    # Generate full forecast
    min_year = int(np.min(hist_years))
    forecast_years = np.arange(min_year, end_year + 1)
    forecast_shares = logistic_function(forecast_years, L_fit, k, t0)
    forecast_shares = clamp_array(forecast_shares, 0, 1)

    info = {
        'mode': 'linear_to_logistic',
        'tipping_point': tipping_point,
        'logistic_params': {'L': L_fit, 'k': k, 't0': t0}
    }

    return forecast_years, forecast_shares, info


def forecast_chimera_hump(
    years: np.ndarray,
    tipping_point: Optional[int],
    peak_share: float = 0.15,
    decay_half_life: float = 3.0
) -> np.ndarray:
    """
    Generate chimera (bridge technology) "hump" trajectory

    Rises linearly to peak at tipping point, then decays exponentially

    Args:
        years: Array of forecast years
        tipping_point: Cost parity year (peak of hump)
        peak_share: Peak share at tipping point (default: 15%)
        decay_half_life: Half-life for exponential decay (default: 3 years)

    Returns:
        Array of chimera shares (0-peak_share range)
    """
    shares = np.zeros_like(years, dtype=float)

    if tipping_point is None:
        return shares

    for i, year in enumerate(years):
        if year < tipping_point:
            # Rising phase: linear growth to peak
            progress = (year - years[0]) / (tipping_point - years[0]) if tipping_point > years[0] else 0
            shares[i] = peak_share * np.clip(progress, 0, 1)
        else:
            # Decay phase: exponential decay with half-life
            years_after = year - tipping_point
            shares[i] = peak_share * np.exp(-np.log(2) * years_after / decay_half_life)

    return clamp_array(shares, 0, 1)
