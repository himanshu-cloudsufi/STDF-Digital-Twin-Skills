"""
Cost Analysis Module
Handles cost curve forecasting and tipping point detection
Generalized for any disruptor/incumbent pair
"""

import numpy as np
from typing import Tuple, Optional, Dict
from .utils import rolling_median, log_cagr_forecast, find_intersection, calculate_cagr


class CostAnalyzer:
    """Analyzes cost curves and determines tipping points for any disruptor/incumbent pair"""

    def __init__(self, smoothing_window: int = 3):
        """
        Initialize cost analyzer

        Args:
            smoothing_window: Window size for rolling median smoothing (default: 3)
        """
        self.smoothing_window = smoothing_window

    def prepare_cost_curves(
        self,
        disruptor_years: list,
        disruptor_costs: list,
        incumbent_years: list,
        incumbent_costs: list,
        end_year: int
    ) -> Dict[str, np.ndarray]:
        """
        Prepare and forecast cost curves for disruptor and incumbent

        Args:
            disruptor_years: Historical disruptor cost years
            disruptor_costs: Historical disruptor cost values
            incumbent_years: Historical incumbent cost years
            incumbent_costs: Historical incumbent cost values
            end_year: Final year to forecast to

        Returns:
            Dictionary with keys: 'years', 'disruptor_costs', 'incumbent_costs', etc.
        """
        # Apply smoothing to historical data
        disruptor_costs_arr = np.array(disruptor_costs)
        incumbent_costs_arr = np.array(incumbent_costs)

        disruptor_smoothed = rolling_median(disruptor_costs_arr, self.smoothing_window)
        incumbent_smoothed = rolling_median(incumbent_costs_arr, self.smoothing_window)

        # Forecast using log-CAGR method
        disruptor_forecast_years, disruptor_forecast_costs = log_cagr_forecast(
            disruptor_years, disruptor_smoothed.tolist(), end_year
        )

        incumbent_forecast_years, incumbent_forecast_costs = log_cagr_forecast(
            incumbent_years, incumbent_smoothed.tolist(), end_year
        )

        # Align to common year range
        min_year = min(disruptor_forecast_years[0], incumbent_forecast_years[0])
        max_year = max(disruptor_forecast_years[-1], incumbent_forecast_years[-1])
        common_years = np.arange(min_year, max_year + 1)

        # Interpolate both series to common years
        disruptor_aligned = np.interp(common_years, disruptor_forecast_years, disruptor_forecast_costs)
        incumbent_aligned = np.interp(common_years, incumbent_forecast_years, incumbent_forecast_costs)

        return {
            'years': common_years,
            'disruptor_costs': disruptor_aligned,
            'incumbent_costs': incumbent_aligned,
            'disruptor_historical_years': disruptor_years,
            'disruptor_historical_costs': disruptor_costs,
            'incumbent_historical_years': incumbent_years,
            'incumbent_historical_costs': incumbent_costs
        }

    def find_tipping_point(
        self,
        years: np.ndarray,
        disruptor_costs: np.ndarray,
        incumbent_costs: np.ndarray
    ) -> Optional[int]:
        """
        Determine the tipping point (cost parity year)

        Args:
            years: Array of years
            disruptor_costs: Disruptor cost series
            incumbent_costs: Incumbent cost series

        Returns:
            Tipping point year, or None if no crossover
        """
        # Check if disruptor is always cheaper
        if np.all(disruptor_costs <= incumbent_costs):
            return int(years[0])

        # Check if incumbent is always cheaper
        if np.all(incumbent_costs <= disruptor_costs):
            return None

        # Find first intersection
        tipping = find_intersection(years, disruptor_costs, incumbent_costs)

        return tipping

    def analyze_cost_trajectory(
        self,
        years: np.ndarray,
        disruptor_costs: np.ndarray,
        incumbent_costs: np.ndarray,
        tipping_point: Optional[int]
    ) -> Dict[str, any]:
        """
        Generate summary statistics for cost trajectory

        Args:
            years: Array of years
            disruptor_costs: Disruptor cost series
            incumbent_costs: Incumbent cost series
            tipping_point: Tipping point year

        Returns:
            Dictionary of summary statistics
        """
        # Calculate cost advantage over time
        cost_diff = incumbent_costs - disruptor_costs
        disruptor_advantage_years = years[cost_diff > 0]

        # Calculate CAGRs
        disruptor_cagr = calculate_cagr(disruptor_costs, years)
        incumbent_cagr = calculate_cagr(incumbent_costs, years)

        # Find current and future states
        current_year_idx = 0
        for i, year in enumerate(years):
            if year >= 2024:
                current_year_idx = i
                break

        current_disruptor_cost = disruptor_costs[current_year_idx]
        current_incumbent_cost = incumbent_costs[current_year_idx]

        summary = {
            'tipping_point': tipping_point,
            'disruptor_cagr': disruptor_cagr,
            'incumbent_cagr': incumbent_cagr,
            'current_disruptor_cost': current_disruptor_cost,
            'current_incumbent_cost': current_incumbent_cost,
            'current_cost_gap': current_incumbent_cost - current_disruptor_cost,
            'years_with_disruptor_advantage': len(disruptor_advantage_years),
            'max_disruptor_cost_advantage': np.max(cost_diff) if len(cost_diff) > 0 else 0
        }

        return summary

    def smooth_and_forecast_cost(
        self,
        years: list,
        costs: list,
        end_year: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply smoothing and forecast a single cost curve

        Args:
            years: Historical years
            costs: Historical cost values
            end_year: Final year to forecast to

        Returns:
            Tuple of (forecast_years, forecast_costs)
        """
        costs_arr = np.array(costs)
        smoothed = rolling_median(costs_arr, self.smoothing_window)
        forecast_years, forecast_costs = log_cagr_forecast(
            years, smoothed.tolist(), end_year
        )
        return forecast_years, forecast_costs
