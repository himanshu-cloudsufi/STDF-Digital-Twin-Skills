"""
Demand Forecasting Module
Handles market, BEV, PHEV, and ICE demand forecasting
"""

import numpy as np
from typing import Dict, Optional, Tuple
from scipy.optimize import differential_evolution
from utils import linear_extrapolation, clamp_array, validate_forecast_consistency


class DemandForecaster:
    """Forecasts demand for market, BEV, PHEV, and ICE"""

    def __init__(
        self,
        end_year: int = 2040,
        logistic_ceiling: float = 1.0,
        max_market_cagr: float = 0.05
    ):
        """
        Initialize demand forecaster

        Args:
            end_year: Final forecast year
            logistic_ceiling: Maximum EV adoption share (default: 1.0 = 100%)
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
        Forecast total market demand using linear extrapolation

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
        Logistic growth function

        Args:
            t: Time array
            L: Ceiling (maximum value)
            k: Growth rate
            t0: Midpoint year

        Returns:
            Logistic curve values
        """
        return L / (1 + np.exp(-k * (t - t0)))

    def fit_logistic_curve(
        self,
        years: np.ndarray,
        shares: np.ndarray,
        L: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Fit logistic curve to share data

        Args:
            years: Array of years
            shares: Array of share values
            L: Ceiling parameter (if None, uses self.logistic_ceiling)

        Returns:
            Tuple of (k, t0) parameters
        """
        if L is None:
            L = self.logistic_ceiling

        # Handle sparse data
        if len(years) < 3:
            # Use default parameters
            k = 0.4
            t0 = years[0] if len(years) > 0 else 2020
            return k, t0

        def objective(params):
            k, t0 = params
            predicted = self.logistic_function(years, L, k, t0)
            return np.sum((shares - predicted) ** 2)

        # Set bounds for optimization
        bounds = [
            (0.05, 1.5),  # k bounds
            (np.min(years) - 5, np.max(years) + 10)  # t0 bounds
        ]

        try:
            result = differential_evolution(
                objective,
                bounds,
                seed=42,
                maxiter=1000,
                tol=1e-6
            )
            k, t0 = result.x
        except Exception as e:
            print(f"Warning: Logistic fit failed ({e}), using defaults")
            k, t0 = 0.4, years[0] if len(years) > 0 else 2020

        return k, t0

    def forecast_bev(
        self,
        historical_years: list,
        historical_bev: list,
        market_years: np.ndarray,
        market_demand: np.ndarray,
        tipping_point: Optional[int]
    ) -> np.ndarray:
        """
        Forecast BEV demand using logistic adoption model

        Args:
            historical_years: Historical years for BEV
            historical_bev: Historical BEV demand
            market_years: Market forecast years
            market_demand: Market forecast demand
            tipping_point: Cost parity year

        Returns:
            BEV demand forecast (aligned with market_years)
        """
        hist_years = np.array(historical_years)
        hist_bev = np.array(historical_bev)

        # Get historical market demand for share calculation
        hist_market = np.interp(hist_years, market_years, market_demand)

        # Calculate historical share (avoid division by zero)
        hist_share = np.zeros_like(hist_bev)
        mask = hist_market > 0
        hist_share[mask] = hist_bev[mask] / hist_market[mask]
        hist_share = clamp_array(hist_share, 0, 1)

        # Extend to tipping point if needed
        if tipping_point is not None and tipping_point > hist_years[-1]:
            # Linear extension to tipping
            extended_years = np.arange(hist_years[-1] + 1, tipping_point + 1)
            if len(hist_share) >= 2:
                slope = (hist_share[-1] - hist_share[-2]) / (hist_years[-1] - hist_years[-2])
                extended_share = hist_share[-1] + slope * (extended_years - hist_years[-1])
                extended_share = clamp_array(extended_share, 0, 1)

                hist_years = np.concatenate([hist_years, extended_years])
                hist_share = np.concatenate([hist_share, extended_share])

        # Fit logistic curve
        k, t0 = self.fit_logistic_curve(hist_years, hist_share)

        # Generate forecast shares
        forecast_share = self.logistic_function(market_years, self.logistic_ceiling, k, t0)
        forecast_share = clamp_array(forecast_share, 0, 1)

        # Convert to absolute demand
        bev_demand = forecast_share * market_demand
        bev_demand = clamp_array(bev_demand, 0, market_demand)

        return bev_demand

    def forecast_phev_hump(
        self,
        years: np.ndarray,
        tipping_point: Optional[int],
        market_demand: np.ndarray,
        peak_share: float = 0.15,
        decay_half_life: float = 3.0
    ) -> np.ndarray:
        """
        Generate PHEV "hump" trajectory

        Args:
            years: Array of forecast years
            tipping_point: Cost parity year
            market_demand: Market demand forecast
            peak_share: Peak PHEV share at tipping (default: 15%)
            decay_half_life: Half-life for exponential decay (default: 3 years)

        Returns:
            PHEV demand forecast
        """
        phev_demand = np.zeros_like(market_demand)

        if tipping_point is None:
            return phev_demand

        for i, year in enumerate(years):
            if year < tipping_point:
                # Rising phase: linear growth to peak
                progress = (year - years[0]) / (tipping_point - years[0])
                share = peak_share * np.clip(progress, 0, 1)
            else:
                # Decay phase: exponential decay
                years_after = year - tipping_point
                share = peak_share * np.exp(-np.log(2) * years_after / decay_half_life)

            phev_demand[i] = share * market_demand[i]

        phev_demand = clamp_array(phev_demand, 0, market_demand)

        return phev_demand

    def forecast_phev(
        self,
        historical_years: list,
        historical_phev: list,
        market_years: np.ndarray,
        market_demand: np.ndarray,
        tipping_point: Optional[int]
    ) -> np.ndarray:
        """
        Forecast PHEV demand (use historical if available, else generate hump)

        Args:
            historical_years: Historical PHEV years
            historical_phev: Historical PHEV demand
            market_years: Market forecast years
            market_demand: Market forecast demand
            tipping_point: Cost parity year

        Returns:
            PHEV demand forecast
        """
        # If we have substantial historical data, extrapolate
        if len(historical_years) >= 5:
            # Use linear extrapolation
            phev_years, phev_demand = linear_extrapolation(
                historical_years,
                historical_phev,
                self.end_year,
                max_cagr=self.max_market_cagr
            )
            # Interpolate to market years
            phev_forecast = np.interp(market_years, phev_years, phev_demand)
        else:
            # Generate hump trajectory
            phev_forecast = self.forecast_phev_hump(
                market_years,
                tipping_point,
                market_demand
            )

        phev_forecast = clamp_array(phev_forecast, 0, market_demand)

        return phev_forecast

    def forecast_ice(
        self,
        market_demand: np.ndarray,
        bev_demand: np.ndarray,
        phev_demand: np.ndarray
    ) -> np.ndarray:
        """
        Forecast ICE demand as residual

        Args:
            market_demand: Market demand forecast
            bev_demand: BEV demand forecast
            phev_demand: PHEV demand forecast

        Returns:
            ICE demand forecast
        """
        ice_demand = market_demand - bev_demand - phev_demand
        ice_demand = np.maximum(ice_demand, 0)

        return ice_demand


def run_demand_forecast(
    data_loader,
    region: str,
    tipping_point: Optional[int],
    end_year: int = 2040,
    logistic_ceiling: float = 1.0
) -> Dict[str, any]:
    """
    Run complete demand forecast for a region

    Args:
        data_loader: DataLoader instance
        region: Region name
        tipping_point: Cost parity year from cost analysis
        end_year: Final forecast year
        logistic_ceiling: Maximum EV adoption share

    Returns:
        Dictionary containing all demand forecasts
    """
    # Initialize forecaster
    forecaster = DemandForecaster(
        end_year=end_year,
        logistic_ceiling=logistic_ceiling
    )

    # Load historical data
    market_years, market_hist = data_loader.get_demand_data("Passenger_Vehicles", region)
    bev_years, bev_hist = data_loader.get_demand_data("BEV_Cars", region)
    phev_years, phev_hist = data_loader.get_demand_data("PHEV_Cars", region)

    # Forecast market
    years, market_demand = forecaster.forecast_market(market_years, market_hist)

    # Forecast BEV
    bev_demand = forecaster.forecast_bev(
        bev_years, bev_hist,
        years, market_demand,
        tipping_point
    )

    # Forecast PHEV
    phev_demand = forecaster.forecast_phev(
        phev_years, phev_hist,
        years, market_demand,
        tipping_point
    )

    # Forecast ICE
    ice_demand = forecaster.forecast_ice(market_demand, bev_demand, phev_demand)

    # Calculate EV total
    ev_demand = bev_demand + phev_demand

    # Validate
    is_valid, message = validate_forecast_consistency(
        market_demand, bev_demand, phev_demand, ice_demand
    )

    result = {
        'years': years,
        'market': market_demand,
        'bev': bev_demand,
        'phev': phev_demand,
        'ice': ice_demand,
        'ev': ev_demand,
        'validation': {'is_valid': is_valid, 'message': message},
        'historical': {
            'market_years': market_years,
            'market_demand': market_hist,
            'bev_years': bev_years,
            'bev_demand': bev_hist,
            'phev_years': phev_years,
            'phev_demand': phev_hist
        }
    }

    return result


if __name__ == "__main__":
    # Test demand forecasting
    from data_loader import DataLoader
    from cost_analysis import run_cost_analysis

    print("Testing Demand Forecasting...")

    loader = DataLoader()

    # Run cost analysis first
    cost_result = run_cost_analysis(loader, "China", end_year=2040)
    tipping_point = cost_result['tipping_point']

    print(f"\nTipping Point: {tipping_point}")

    # Run demand forecast
    demand_result = run_demand_forecast(
        loader, "China", tipping_point,
        end_year=2040, logistic_ceiling=1.0
    )

    print(f"\nValidation: {demand_result['validation']['message']}")
    print(f"Final Year (2040) Forecast:")
    print(f"  Market: {demand_result['market'][-1]:,.0f}")
    print(f"  BEV: {demand_result['bev'][-1]:,.0f}")
    print(f"  PHEV: {demand_result['phev'][-1]:,.0f}")
    print(f"  ICE: {demand_result['ice'][-1]:,.0f}")
    print(f"  EV: {demand_result['ev'][-1]:,.0f}")
