"""
Demand Forecasting Module for Three-Wheeler Market
Handles market, EV, and ICE demand forecasting with logistic adoption curves
"""

import numpy as np
from typing import Dict, Optional, Tuple
from scipy.optimize import differential_evolution
from utils import linear_extrapolation, clamp_array, validate_forecast_consistency


class DemandForecaster:
    """Forecasts demand for three-wheeler market, EV, and ICE segments"""

    def __init__(
        self,
        end_year: int = 2040,
        logistic_ceiling: float = 0.9,
        max_market_cagr: float = 0.05
    ):
        """
        Initialize demand forecaster

        Args:
            end_year: Final forecast year
            logistic_ceiling: Maximum EV adoption share (default: 0.9 = 90%)
            max_market_cagr: Maximum market CAGR cap (default: 5%)
        """
        self.end_year = end_year
        self.logistic_ceiling = logistic_ceiling
        self.max_market_cagr = max_market_cagr

    def forecast_market(
        self,
        historical_years: list,
        historical_demand: list
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forecast total three-wheeler market demand using linear extrapolation with CAGR cap

        Args:
            historical_years: Historical years
            historical_demand: Historical market demand

        Returns:
            Tuple of (years, demand)
        """
        years, demand = linear_extrapolation(
            historical_years,
            historical_demand,
            self.end_year,
            max_cagr=self.max_market_cagr
        )

        return years, demand

    def logistic_function(
        self,
        t: np.ndarray,
        L: float,
        k: float,
        t0: float
    ) -> np.ndarray:
        """
        Logistic growth function (S-curve)

        Args:
            t: Time array (years)
            L: Ceiling (maximum adoption share)
            k: Growth rate (slope parameter)
            t0: Midpoint year (inflection point)

        Returns:
            Logistic curve values
        """
        return L / (1 + np.exp(-k * (t - t0)))

    def fit_logistic_curve(
        self,
        years: np.ndarray,
        shares: np.ndarray,
        L: Optional[float] = None,
        tipping_point: Optional[int] = None
    ) -> Tuple[float, float]:
        """
        Fit logistic curve to EV share data

        Args:
            years: Array of years
            shares: Array of EV share values (0-1)
            L: Ceiling parameter (if None, uses self.logistic_ceiling)
            tipping_point: Cost parity year (used to anchor t0)

        Returns:
            Tuple of (k, t0) parameters
        """
        if L is None:
            L = self.logistic_ceiling

        # Handle sparse data
        if len(years) < 3:
            # Use default parameters
            k = 0.4
            t0 = tipping_point if tipping_point else (years[0] if len(years) > 0 else 2025)
            return k, t0

        # Filter out zero or very small shares for better fitting
        mask = shares > 0.01
        if np.sum(mask) < 3:
            # Not enough non-zero data points
            k = 0.4
            t0 = tipping_point if tipping_point else years[np.argmax(shares)]
            return k, t0

        fit_years = years[mask]
        fit_shares = shares[mask]

        def objective(params):
            k, t0 = params
            predicted = self.logistic_function(fit_years, L, k, t0)
            return np.sum((fit_shares - predicted) ** 2)

        # Set bounds for optimization
        # k: growth rate (0.05 = slow, 1.5 = fast)
        # t0: midpoint year (anchor around tipping point if available)
        if tipping_point:
            t0_bounds = (tipping_point - 5, tipping_point + 10)
        else:
            t0_bounds = (np.min(fit_years) - 5, np.max(fit_years) + 10)

        bounds = [
            (0.05, 1.5),  # k bounds
            t0_bounds  # t0 bounds
        ]

        try:
            result = differential_evolution(
                objective,
                bounds,
                seed=42,
                maxiter=1000,
                tol=1e-6,
                atol=1e-6
            )
            k, t0 = result.x
        except Exception as e:
            print(f"Warning: Logistic fit failed ({e}), using defaults")
            k = 0.4
            t0 = tipping_point if tipping_point else years[np.argmax(shares)]

        return k, t0

    def forecast_ev(
        self,
        historical_years: list,
        historical_ev: list,
        market_years: np.ndarray,
        market_demand: np.ndarray,
        tipping_point: Optional[int]
    ) -> np.ndarray:
        """
        Forecast EV three-wheeler demand using logistic adoption model

        Args:
            historical_years: Historical years for EV
            historical_ev: Historical EV demand
            market_years: Market forecast years
            market_demand: Market forecast demand
            tipping_point: Cost parity year

        Returns:
            EV demand forecast (aligned with market_years)
        """
        hist_years = np.array(historical_years)
        hist_ev = np.array(historical_ev)

        # Get historical market demand for share calculation
        hist_market = np.interp(hist_years, market_years, market_demand)

        # Calculate historical EV share (avoid division by zero)
        hist_share = np.zeros_like(hist_ev, dtype=float)
        mask = hist_market > 0
        hist_share[mask] = hist_ev[mask] / hist_market[mask]
        hist_share = clamp_array(hist_share, 0, 1)

        # Pre-tipping extrapolation: extend historical share linearly to tipping point
        if tipping_point is not None and tipping_point > hist_years[-1]:
            extended_years = np.arange(hist_years[-1] + 1, tipping_point + 1)
            if len(hist_share) >= 2:
                # Calculate recent trend
                recent_window = min(5, len(hist_share))
                slope = (hist_share[-1] - hist_share[-recent_window]) / (hist_years[-1] - hist_years[-recent_window])
                extended_share = hist_share[-1] + slope * (extended_years - hist_years[-1])
                extended_share = clamp_array(extended_share, 0, 1)

                hist_years = np.concatenate([hist_years, extended_years])
                hist_share = np.concatenate([hist_share, extended_share])

        # Fit logistic curve to historical + pre-tipping data
        k, t0 = self.fit_logistic_curve(hist_years, hist_share, tipping_point=tipping_point)

        # Generate forecast shares using logistic curve
        forecast_share = self.logistic_function(market_years, self.logistic_ceiling, k, t0)
        forecast_share = clamp_array(forecast_share, 0, 1)

        # Convert to absolute demand
        ev_demand = forecast_share * market_demand
        ev_demand = clamp_array(ev_demand, 0, market_demand)

        return ev_demand

    def forecast_ice(
        self,
        market_demand: np.ndarray,
        ev_demand: np.ndarray
    ) -> np.ndarray:
        """
        Forecast ICE three-wheeler demand as residual

        Args:
            market_demand: Market demand forecast
            ev_demand: EV demand forecast

        Returns:
            ICE demand forecast
        """
        ice_demand = market_demand - ev_demand
        ice_demand = np.maximum(ice_demand, 0)

        return ice_demand

    def calculate_fleet_evolution(
        self,
        sales: np.ndarray,
        years: np.ndarray,
        lifetime_years: float,
        initial_fleet: float = 0.0
    ) -> np.ndarray:
        """
        Calculate fleet evolution using stock-flow accounting

        Args:
            sales: Annual sales array
            years: Years array
            lifetime_years: Vehicle lifetime in years
            initial_fleet: Initial fleet size

        Returns:
            Fleet size array
        """
        fleet = np.zeros_like(sales, dtype=float)
        fleet[0] = initial_fleet + sales[0]

        for i in range(1, len(sales)):
            # Fleet evolution: Fleet(t) = Fleet(t-1) + Sales(t) - Scrappage(t)
            scrappage = fleet[i-1] / lifetime_years
            fleet[i] = fleet[i-1] + sales[i] - scrappage

        return fleet


def run_demand_forecast(
    data_loader,
    region: str,
    tipping_point: Optional[int],
    end_year: int = 2040,
    logistic_ceiling: float = 0.9,
    track_fleet: bool = False
) -> Dict[str, any]:
    """
    Run complete demand forecast for a region

    Args:
        data_loader: DataLoader instance
        region: Region name
        tipping_point: Cost parity year from cost analysis
        end_year: Final forecast year
        logistic_ceiling: Maximum EV adoption share
        track_fleet: Whether to calculate fleet evolution

    Returns:
        Dictionary containing all demand forecasts
    """
    # Initialize forecaster
    forecaster = DemandForecaster(
        end_year=end_year,
        logistic_ceiling=logistic_ceiling
    )

    # Load historical data
    market_years, market_hist = data_loader.get_demand_data("Three_Wheelers", region)
    ev_years, ev_hist = data_loader.get_demand_data("EV_3_Wheelers", region)

    # Forecast market
    years, market_demand = forecaster.forecast_market(market_years, market_hist)

    # Forecast EV
    ev_demand = forecaster.forecast_ev(
        ev_years, ev_hist,
        years, market_demand,
        tipping_point
    )

    # Forecast ICE (residual)
    ice_demand = forecaster.forecast_ice(market_demand, ev_demand)

    # Validate
    is_valid, message = validate_forecast_consistency(
        market_demand, ev_demand, ice_demand
    )

    result = {
        'years': years,
        'market': market_demand,
        'ev': ev_demand,
        'ice': ice_demand,
        'validation': {'is_valid': is_valid, 'message': message},
        'historical': {
            'market_years': market_years,
            'market_demand': market_hist,
            'ev_years': ev_years,
            'ev_demand': ev_hist
        },
        'parameters': {
            'tipping_point': tipping_point,
            'logistic_ceiling': logistic_ceiling,
            'end_year': end_year
        }
    }

    # Optional fleet tracking
    if track_fleet:
        try:
            # Calculate fleet evolution (10-year lifetime for three-wheelers)
            ev_fleet = forecaster.calculate_fleet_evolution(
                ev_demand, years, lifetime_years=10.0
            )
            ice_fleet = forecaster.calculate_fleet_evolution(
                ice_demand, years, lifetime_years=10.0
            )
            result['ev_fleet'] = ev_fleet
            result['ice_fleet'] = ice_fleet
            result['total_fleet'] = ev_fleet + ice_fleet
        except Exception as e:
            result['fleet_error'] = str(e)

    return result


if __name__ == "__main__":
    # Test demand forecasting
    from data_loader import DataLoader
    from cost_analysis import run_cost_analysis

    print("Testing Three-Wheeler Demand Forecasting...")

    try:
        loader = DataLoader()

        # Run cost analysis first to get tipping point
        cost_result = run_cost_analysis(loader, "China", end_year=2040)
        tipping_point = cost_result['tipping_point']

        print(f"\n{'='*60}")
        print(f"Using Tipping Point: {tipping_point}")
        print(f"{'='*60}")

        # Run demand forecast
        demand_result = run_demand_forecast(
            loader, "China", tipping_point,
            end_year=2040, logistic_ceiling=0.9, track_fleet=True
        )

        print(f"\nValidation: {demand_result['validation']['message']}")
        print(f"\nForecast for {int(demand_result['years'][-1])}:")
        final_idx = -1
        print(f"  Market:  {demand_result['market'][final_idx]:>15,.0f} units")
        print(f"  EV:      {demand_result['ev'][final_idx]:>15,.0f} units ({demand_result['ev'][final_idx]/demand_result['market'][final_idx]*100:.1f}%)")
        print(f"  ICE:     {demand_result['ice'][final_idx]:>15,.0f} units ({demand_result['ice'][final_idx]/demand_result['market'][final_idx]*100:.1f}%)")

        if 'ev_fleet' in demand_result:
            print(f"\nFleet Evolution for {int(demand_result['years'][-1])}:")
            print(f"  EV Fleet:    {demand_result['ev_fleet'][final_idx]:>15,.0f} units")
            print(f"  ICE Fleet:   {demand_result['ice_fleet'][final_idx]:>15,.0f} units")
            print(f"  Total Fleet: {demand_result['total_fleet'][final_idx]:>15,.0f} units")

        print(f"\n{'='*60}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
