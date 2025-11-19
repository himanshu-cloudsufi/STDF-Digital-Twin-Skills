"""
Cost Analysis Module for Three-Wheeler Demand Forecasting
Handles cost curve forecasting and tipping point detection
"""

import numpy as np
from typing import Tuple, Optional, Dict
from utils import rolling_median, log_cagr_forecast, find_intersection, calculate_cagr


class CostAnalyzer:
    """Analyzes cost curves and determines tipping points for three-wheeler EV adoption"""

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
        Prepare and forecast cost curves for EV and ICE three-wheelers

        Args:
            ev_years: Historical EV cost years
            ev_costs: Historical EV cost values
            ice_years: Historical ICE cost years
            ice_costs: Historical ICE cost values
            end_year: Final year to forecast to

        Returns:
            Dictionary with keys: 'years', 'ev_costs', 'ice_costs', etc.
        """
        # Convert to arrays
        ev_costs_arr = np.array(ev_costs, dtype=float)
        ice_costs_arr = np.array(ice_costs, dtype=float)

        # Apply smoothing to historical data (3-year rolling median)
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
            'ice_historical_costs': ice_costs,
            'ev_smoothed': ev_smoothed,
            'ice_smoothed': ice_smoothed
        }

    def find_tipping_point(
        self,
        years: np.ndarray,
        ev_costs: np.ndarray,
        ice_costs: np.ndarray
    ) -> Optional[int]:
        """
        Determine the tipping point (cost parity year) where EV becomes cheaper than ICE

        Args:
            years: Array of years
            ev_costs: EV cost series
            ice_costs: ICE cost series

        Returns:
            Tipping point year, or None if no crossover occurs
        """
        # Check if EV is always cheaper (already past tipping point)
        if np.all(ev_costs <= ice_costs):
            return int(years[0])

        # Check if ICE is always cheaper (no tipping point in forecast horizon)
        if np.all(ice_costs <= ev_costs):
            return None

        # Find first intersection where EV crosses below ICE
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
        # Calculate cost difference over time
        cost_diff = ice_costs - ev_costs
        ev_advantage_years = years[cost_diff > 0]

        # Calculate CAGRs
        ev_cagr = calculate_cagr(ev_costs, years)
        ice_cagr = calculate_cagr(ice_costs, years)

        # Find current year state (2024 or closest available)
        current_year_idx = 0
        for i, year in enumerate(years):
            if year >= 2024:
                current_year_idx = i
                break

        current_ev_cost = ev_costs[current_year_idx]
        current_ice_cost = ice_costs[current_year_idx]
        current_cost_gap = current_ice_cost - current_ev_cost

        # Calculate cost parity metrics
        if tipping_point is not None:
            years_to_parity = max(0, tipping_point - 2024)
            cost_at_parity_idx = np.argmin(np.abs(years - tipping_point))
            ev_cost_at_parity = ev_costs[cost_at_parity_idx]
            ice_cost_at_parity = ice_costs[cost_at_parity_idx]
        else:
            years_to_parity = None
            ev_cost_at_parity = None
            ice_cost_at_parity = None

        summary = {
            'tipping_point': tipping_point,
            'years_to_parity': years_to_parity,
            'ev_cagr': ev_cagr,
            'ice_cagr': ice_cagr,
            'current_ev_cost': float(current_ev_cost),
            'current_ice_cost': float(current_ice_cost),
            'current_cost_gap': float(current_cost_gap),
            'years_with_ev_advantage': int(len(ev_advantage_years)),
            'max_ev_cost_advantage': float(np.max(cost_diff)) if len(cost_diff) > 0 else 0.0,
            'ev_cost_at_parity': float(ev_cost_at_parity) if ev_cost_at_parity is not None else None,
            'ice_cost_at_parity': float(ice_cost_at_parity) if ice_cost_at_parity is not None else None
        }

        return summary

    def sensitivity_check(
        self,
        ev_primary_years: list,
        ev_primary_costs: list,
        ev_secondary_years: list,
        ev_secondary_costs: list,
        ice_years: list,
        ice_costs: list,
        end_year: int
    ) -> Dict[str, any]:
        """
        Perform sensitivity check using alternative EV cost series

        Args:
            ev_primary_years: EV lowest cost years
            ev_primary_costs: EV lowest cost values
            ev_secondary_years: EV median cost years
            ev_secondary_costs: EV median cost values
            ice_years: ICE cost years
            ice_costs: ICE cost values
            end_year: Forecast end year

        Returns:
            Sensitivity analysis results
        """
        # Primary tipping point (EV lowest vs ICE median)
        primary_curves = self.prepare_cost_curves(
            ev_primary_years, ev_primary_costs,
            ice_years, ice_costs,
            end_year
        )
        primary_tipping = self.find_tipping_point(
            primary_curves['years'],
            primary_curves['ev_costs'],
            primary_curves['ice_costs']
        )

        # Secondary tipping point (EV median vs ICE median)
        secondary_curves = self.prepare_cost_curves(
            ev_secondary_years, ev_secondary_costs,
            ice_years, ice_costs,
            end_year
        )
        secondary_tipping = self.find_tipping_point(
            secondary_curves['years'],
            secondary_curves['ev_costs'],
            secondary_curves['ice_costs']
        )

        # Calculate difference
        tipping_diff = None
        if primary_tipping is not None and secondary_tipping is not None:
            tipping_diff = abs(primary_tipping - secondary_tipping)

        return {
            'primary_tipping': primary_tipping,
            'secondary_tipping': secondary_tipping,
            'tipping_difference_years': tipping_diff,
            'sensitivity_note': 'Primary uses EV 100km lowest cost, Secondary uses EV median cost'
        }


def run_cost_analysis(
    data_loader,
    region: str,
    end_year: int = 2040,
    include_sensitivity: bool = False
) -> Dict[str, any]:
    """
    Run complete cost analysis for a region

    Args:
        data_loader: DataLoader instance
        region: Region name
        end_year: Final forecast year
        include_sensitivity: Whether to include sensitivity analysis

    Returns:
        Dictionary containing cost curves and tipping point analysis
    """
    # Load cost data
    ev_years, ev_costs = data_loader.get_cost_data("ev_primary", region)
    ice_years, ice_costs = data_loader.get_cost_data("ice", region)

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

    # Optionally add sensitivity analysis
    if include_sensitivity:
        try:
            ev_sec_years, ev_sec_costs = data_loader.get_cost_data("ev_secondary", region)
            sensitivity = analyzer.sensitivity_check(
                ev_years, ev_costs,
                ev_sec_years, ev_sec_costs,
                ice_years, ice_costs,
                end_year
            )
            result['sensitivity'] = sensitivity
        except Exception as e:
            result['sensitivity'] = {'error': str(e)}

    return result


if __name__ == "__main__":
    # Test cost analysis
    from data_loader import DataLoader

    print("Testing Three-Wheeler Cost Analysis...")

    try:
        loader = DataLoader()
        result = run_cost_analysis(loader, "China", end_year=2040, include_sensitivity=True)

        print(f"\n{'='*60}")
        print(f"Cost Analysis for China")
        print(f"{'='*60}")
        print(f"\nTipping Point: {result['tipping_point']}")
        if result['tipping_point']:
            print(f"Years to Parity: {result.get('years_to_parity', 'N/A')}")
        print(f"EV CAGR: {result['ev_cagr']:.2%}")
        print(f"ICE CAGR: {result['ice_cagr']:.2%}")
        print(f"Current EV Cost: ${result['current_ev_cost']:.2f}")
        print(f"Current ICE Cost: ${result['current_ice_cost']:.2f}")
        print(f"Cost Gap: ${result['current_cost_gap']:.2f}")

        if 'sensitivity' in result and 'error' not in result['sensitivity']:
            sens = result['sensitivity']
            print(f"\nSensitivity Check:")
            print(f"  Primary Tipping: {sens['primary_tipping']}")
            print(f"  Secondary Tipping: {sens['secondary_tipping']}")
            print(f"  Difference: {sens['tipping_difference_years']} years")

        print(f"\n{'='*60}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
