"""
Cost Analysis Module
Handles cost curve forecasting and tipping point detection
"""

import numpy as np
from typing import Tuple, Optional, Dict
from utils import rolling_median, log_cagr_forecast, find_intersection


class CostAnalyzer:
    """Analyzes cost curves and determines tipping points"""

    def __init__(self, smoothing_window: int = 3):
        """
        Initialize cost analyzer

        Args:
            smoothing_window: Window size for rolling median smoothing (default: 3)
        """
        self.smoothing_window = smoothing_window

    def prepare_cost_curves(
        self,
        ev_years: list,
        ev_costs: list,
        ice_years: list,
        ice_costs: list,
        end_year: int
    ) -> Dict[str, np.ndarray]:
        """
        Prepare and forecast cost curves for EV and ICE

        Args:
            ev_years: Historical EV cost years
            ev_costs: Historical EV cost values
            ice_years: Historical ICE cost years
            ice_costs: Historical ICE cost values
            end_year: Final year to forecast to

        Returns:
            Dictionary with keys: 'years', 'ev_costs', 'ice_costs', 'ev_smoothed', 'ice_smoothed'
        """
        # Apply smoothing to historical data
        ev_costs_arr = np.array(ev_costs)
        ice_costs_arr = np.array(ice_costs)

        ev_smoothed = rolling_median(ev_costs_arr, self.smoothing_window)
        ice_smoothed = rolling_median(ice_costs_arr, self.smoothing_window)

        # Forecast using log-CAGR method
        ev_forecast_years, ev_forecast_costs = log_cagr_forecast(
            ev_years, ev_smoothed.tolist(), end_year
        )

        ice_forecast_years, ice_forecast_costs = log_cagr_forecast(
            ice_years, ice_smoothed.tolist(), end_year
        )

        # Align to common year range
        min_year = min(ev_forecast_years[0], ice_forecast_years[0])
        max_year = max(ev_forecast_years[-1], ice_forecast_years[-1])
        common_years = np.arange(min_year, max_year + 1)

        # Interpolate both series to common years
        ev_aligned = np.interp(common_years, ev_forecast_years, ev_forecast_costs)
        ice_aligned = np.interp(common_years, ice_forecast_years, ice_forecast_costs)

        return {
            'years': common_years,
            'ev_costs': ev_aligned,
            'ice_costs': ice_aligned,
            'ev_historical_years': ev_years,
            'ev_historical_costs': ev_costs,
            'ice_historical_years': ice_years,
            'ice_historical_costs': ice_costs
        }

    def find_tipping_point(
        self,
        years: np.ndarray,
        ev_costs: np.ndarray,
        ice_costs: np.ndarray
    ) -> Optional[int]:
        """
        Determine the tipping point (cost parity year)

        Args:
            years: Array of years
            ev_costs: EV cost series
            ice_costs: ICE cost series

        Returns:
            Tipping point year, or None if no crossover
        """
        # Check if EV is always cheaper
        if np.all(ev_costs <= ice_costs):
            return int(years[0])

        # Check if ICE is always cheaper
        if np.all(ice_costs <= ev_costs):
            return None

        # Find first intersection
        tipping = find_intersection(years, ev_costs, ice_costs)

        return tipping

    def analyze_cost_trajectory(
        self,
        years: np.ndarray,
        ev_costs: np.ndarray,
        ice_costs: np.ndarray,
        tipping_point: Optional[int]
    ) -> Dict[str, any]:
        """
        Generate summary statistics for cost trajectory

        Args:
            years: Array of years
            ev_costs: EV cost series
            ice_costs: ICE cost series
            tipping_point: Tipping point year

        Returns:
            Dictionary of summary statistics
        """
        # Calculate cost advantage over time
        cost_diff = ice_costs - ev_costs
        ev_advantage_years = years[cost_diff > 0]

        # Calculate CAGRs
        from utils import calculate_cagr

        ev_cagr = calculate_cagr(ev_costs, years)
        ice_cagr = calculate_cagr(ice_costs, years)

        # Find current and future states
        current_year_idx = 0
        for i, year in enumerate(years):
            if year >= 2024:
                current_year_idx = i
                break

        current_ev_cost = ev_costs[current_year_idx]
        current_ice_cost = ice_costs[current_year_idx]

        summary = {
            'tipping_point': tipping_point,
            'ev_cagr': ev_cagr,
            'ice_cagr': ice_cagr,
            'current_ev_cost': current_ev_cost,
            'current_ice_cost': current_ice_cost,
            'current_cost_gap': current_ice_cost - current_ev_cost,
            'years_with_ev_advantage': len(ev_advantage_years),
            'max_ev_cost_advantage': np.max(cost_diff) if len(cost_diff) > 0 else 0
        }

        return summary


def run_cost_analysis(
    data_loader,
    region: str,
    end_year: int = 2040
) -> Dict[str, any]:
    """
    Run complete cost analysis for a region

    Args:
        data_loader: DataLoader instance
        region: Region name
        end_year: Final forecast year

    Returns:
        Dictionary containing cost curves and tipping point analysis
    """
    # Load cost data
    ev_years, ev_costs = data_loader.get_cost_data("EV_Cars", region)
    ice_years, ice_costs = data_loader.get_cost_data("ICE_Cars", region)

    # Initialize analyzer
    analyzer = CostAnalyzer(smoothing_window=3)

    # Prepare cost curves
    cost_curves = analyzer.prepare_cost_curves(
        ev_years, ev_costs,
        ice_years, ice_costs,
        end_year
    )

    # Find tipping point
    tipping_point = analyzer.find_tipping_point(
        cost_curves['years'],
        cost_curves['ev_costs'],
        cost_curves['ice_costs']
    )

    # Generate summary
    summary = analyzer.analyze_cost_trajectory(
        cost_curves['years'],
        cost_curves['ev_costs'],
        cost_curves['ice_costs'],
        tipping_point
    )

    # Combine results
    result = {
        **cost_curves,
        **summary
    }

    return result


if __name__ == "__main__":
    # Test cost analysis
    from data_loader import DataLoader

    print("Testing Cost Analysis...")

    loader = DataLoader()
    result = run_cost_analysis(loader, "China", end_year=2040)

    print(f"\nTipping Point: {result['tipping_point']}")
    print(f"EV CAGR: {result['ev_cagr']:.2%}")
    print(f"ICE CAGR: {result['ice_cagr']:.2%}")
    print(f"Current EV Cost: ${result['current_ev_cost']:.2f}")
    print(f"Current ICE Cost: ${result['current_ice_cost']:.2f}")
    print(f"Cost Gap: ${result['current_cost_gap']:.2f}")
