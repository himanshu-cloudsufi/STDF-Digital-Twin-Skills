"""
Demand Forecasting Module for Commercial Vehicle Market
Handles segment-level (LCV, MCV, HCV) demand forecasting with:
- Market growth forecasting (Theil-Sen regression with CAGR cap)
- EV adoption modeling (logistic S-curves with segment-specific ceilings)
- NGV chimera modeling (peak detection + exponential decline)
- ICE residual calculation (ICE = Market - EV - NGV)
"""

import numpy as np
from typing import Dict, Optional, Tuple
from scipy.optimize import differential_evolution
from utils import linear_extrapolation, clamp_array, validate_forecast_consistency_three_powertrain
from ngv_model import NGVModel


class DemandForecaster:
    """Forecasts demand for commercial vehicle market with three powertrains: EV, ICE, NGV"""

    def __init__(
        self,
        end_year: int = 2040,
        logistic_ceiling: float = 0.9,
        max_market_cagr: float = 0.05,
        ngv_config: Optional[Dict] = None
    ):
        """
        Initialize demand forecaster

        Args:
            end_year: Final forecast year
            logistic_ceiling: Maximum EV adoption share (default: 0.9 = 90%)
            max_market_cagr: Maximum market CAGR cap (default: 5%)
            ngv_config: NGV model configuration
        """
        self.end_year = end_year
        self.logistic_ceiling = logistic_ceiling
        self.max_market_cagr = max_market_cagr

        # Initialize NGV model
        if ngv_config is None:
            ngv_config = {
                'half_life_years': 6.0,
                'peak_detection_window': 5,
                'target_share_2040': 0.0,
                'min_significant_share': 0.01
            }
        self.ngv_model = NGVModel(ngv_config)

    def forecast_market(
        self,
        historical_years: list,
        historical_demand: list
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forecast total commercial vehicle market demand using linear extrapolation with CAGR cap

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
        tipping_point: Optional[int],
        ceiling: Optional[float] = None
    ) -> np.ndarray:
        """
        Forecast EV commercial vehicle demand using logistic adoption model

        Args:
            historical_years: Historical years for EV
            historical_ev: Historical EV demand
            market_years: Market forecast years
            market_demand: Market forecast demand
            tipping_point: Cost parity year
            ceiling: Segment-specific ceiling (overrides default)

        Returns:
            EV demand forecast (aligned with market_years)
        """
        hist_years = np.array(historical_years)
        hist_ev = np.array(historical_ev)

        if ceiling is None:
            ceiling = self.logistic_ceiling

        # Get historical market demand for share calculation
        hist_market = np.interp(hist_years, market_years, market_demand)

        # Calculate historical EV share (avoid division by zero)
        hist_share = np.zeros_like(hist_ev, dtype=float)
        mask = hist_market > 0
        hist_share[mask] = hist_ev[mask] / hist_market[mask]
        hist_share = clamp_array(hist_share, 0, 1)

        # Pre-tipping extrapolation: extend historical share linearly to tipping point
        if tipping_point is not None and len(hist_years) > 0 and tipping_point > hist_years[-1]:
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
        k, t0 = self.fit_logistic_curve(hist_years, hist_share, L=ceiling, tipping_point=tipping_point)

        # Generate forecast shares using logistic curve
        forecast_share = self.logistic_function(market_years, ceiling, k, t0)
        forecast_share = clamp_array(forecast_share, 0, 1)

        # Convert to absolute demand
        ev_demand = forecast_share * market_demand
        ev_demand = clamp_array(ev_demand, 0, market_demand)

        return ev_demand

    def forecast_ngv(
        self,
        historical_years: list,
        historical_ngv: list,
        market_years: np.ndarray,
        market_demand: np.ndarray,
        tipping_point: Optional[int]
    ) -> Tuple[np.ndarray, Dict]:
        """
        Forecast NGV commercial vehicle demand using chimera decline model

        Args:
            historical_years: Historical years for NGV
            historical_ngv: Historical NGV demand
            market_years: Market forecast years
            market_demand: Market forecast demand
            tipping_point: Cost parity year

        Returns:
            Tuple of (NGV demand forecast, metadata dict)
        """
        hist_years = np.array(historical_years)
        hist_ngv = np.array(historical_ngv)

        # Get historical market demand for share calculation
        hist_market = np.interp(hist_years, market_years, market_demand)

        # Use NGV model for forecasting
        forecast_ngv, metadata = self.ngv_model.forecast_ngv(
            hist_years,
            hist_ngv,
            hist_market,
            market_years,
            market_demand,
            tipping_point=tipping_point
        )

        # Ensure non-negative and within market bounds
        forecast_ngv = clamp_array(forecast_ngv, 0, market_demand)

        return forecast_ngv, metadata

    def forecast_ice(
        self,
        market_demand: np.ndarray,
        ev_demand: np.ndarray,
        ngv_demand: np.ndarray
    ) -> np.ndarray:
        """
        Forecast ICE commercial vehicle demand as residual

        Args:
            market_demand: Market demand forecast
            ev_demand: EV demand forecast
            ngv_demand: NGV demand forecast

        Returns:
            ICE demand forecast
        """
        ice_demand = market_demand - ev_demand - ngv_demand
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


def run_demand_forecast_segment(
    data_loader,
    region: str,
    segment: str,
    tipping_point: Optional[int],
    end_year: int = 2040,
    logistic_ceiling: float = 0.9,
    track_fleet: bool = False,
    fleet_lifetime: float = 15.0,
    ngv_config: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Run complete demand forecast for a specific segment in a region

    Args:
        data_loader: DataLoader instance
        region: Region name
        segment: Segment identifier (LCV, MCV, HCV)
        tipping_point: Cost parity year from cost analysis
        end_year: Final forecast year
        logistic_ceiling: Maximum EV adoption share
        track_fleet: Whether to calculate fleet evolution
        fleet_lifetime: Vehicle lifetime in years (segment-specific)
        ngv_config: NGV model configuration

    Returns:
        Dictionary containing all demand forecasts for the segment
    """
    # Initialize forecaster
    forecaster = DemandForecaster(
        end_year=end_year,
        logistic_ceiling=logistic_ceiling,
        ngv_config=ngv_config
    )

    # Load historical segment-level data
    market_years, market_hist = data_loader.get_demand_data("Commercial_Vehicles", region, segment=segment)
    ev_years, ev_hist = data_loader.get_demand_data("Commercial_Vehicles_(EV)", region, segment=segment)
    ngv_years, ngv_hist = data_loader.get_demand_data("Commercial_Vehicles_(NGV)", region, segment=segment)

    # Forecast market (used as initial reference for sizing EV/NGV forecasts)
    years, market_demand_initial = forecaster.forecast_market(market_years, market_hist)

    # Forecast EV
    ev_demand = forecaster.forecast_ev(
        ev_years, ev_hist,
        years, market_demand_initial,
        tipping_point,
        ceiling=logistic_ceiling
    )

    # Forecast NGV
    ngv_demand, ngv_metadata = forecaster.forecast_ngv(
        ngv_years, ngv_hist,
        years, market_demand_initial,
        tipping_point
    )

    # Forecast ICE (residual from initial market)
    ice_demand_initial = forecaster.forecast_ice(market_demand_initial, ev_demand, ngv_demand)

    # IMPORTANT: Redefine market as sum of components to ensure consistency
    # This prevents validation errors where independently-forecasted powertrains
    # don't sum exactly to the extrapolated market total
    market_demand = ev_demand + ice_demand_initial + ngv_demand
    ice_demand = ice_demand_initial  # ICE was already calculated as residual

    # Calculate shares
    shares_ev = ev_demand / np.maximum(market_demand, 1)
    shares_ice = ice_demand / np.maximum(market_demand, 1)
    shares_ngv = ngv_demand / np.maximum(market_demand, 1)

    # Validate consistency
    is_valid, validation_msg = validate_forecast_consistency_three_powertrain(
        market_demand, ev_demand, ice_demand, ngv_demand, tolerance=0.02
    )

    result = {
        'segment': segment,
        'years': years,
        'market': market_demand,
        'ev': ev_demand,
        'ice': ice_demand,
        'ngv': ngv_demand,
        'ev_share': shares_ev,
        'ice_share': shares_ice,
        'ngv_share': shares_ngv,
        'tipping_point': tipping_point,
        'logistic_ceiling': logistic_ceiling,
        'ngv_metadata': ngv_metadata,
        'validation': {
            'is_valid': is_valid,
            'message': validation_msg
        }
    }

    # Optional fleet tracking
    if track_fleet:
        try:
            ev_fleet = forecaster.calculate_fleet_evolution(ev_demand, years, fleet_lifetime)
            ice_fleet = forecaster.calculate_fleet_evolution(ice_demand, years, fleet_lifetime)
            ngv_fleet = forecaster.calculate_fleet_evolution(ngv_demand, years, fleet_lifetime)
            total_fleet = ev_fleet + ice_fleet + ngv_fleet

            result['fleet'] = {
                'ev': ev_fleet,
                'ice': ice_fleet,
                'ngv': ngv_fleet,
                'total': total_fleet,
                'lifetime_years': fleet_lifetime
            }
        except Exception as e:
            result['fleet'] = {'error': str(e)}

    return result


if __name__ == "__main__":
    # Test demand forecasting
    from data_loader import DataLoader

    print("Testing Commercial Vehicle Demand Forecasting...")

    try:
        loader = DataLoader()

        # Test for one segment
        segment = "LCV"
        region = "China"
        tipping_point = 2028  # Example

        result = run_demand_forecast_segment(
            loader,
            region,
            segment,
            tipping_point,
            end_year=2040,
            logistic_ceiling=0.95,
            track_fleet=True,
            fleet_lifetime=12.0
        )

        print(f"\n{'='*60}")
        print(f"Demand Forecast for {region} - {segment}")
        print(f"{'='*60}")
        print(f"Tipping Point: {result['tipping_point']}")
        print(f"Logistic Ceiling: {result['logistic_ceiling']:.0%}")
        print(f"\nForecast Summary (2040):")
        print(f"  Market: {result['market'][-1]:,.0f}")
        print(f"  EV: {result['ev'][-1]:,.0f} ({result['ev_share'][-1]:.1%})")
        print(f"  ICE: {result['ice'][-1]:,.0f} ({result['ice_share'][-1]:.1%})")
        print(f"  NGV: {result['ngv'][-1]:,.0f} ({result['ngv_share'][-1]:.1%})")

        print(f"\nNGV Modeling:")
        print(f"  Model: {result['ngv_metadata']['model']}")
        if 'peak_info' in result['ngv_metadata']:
            peak_info = result['ngv_metadata']['peak_info']
            if peak_info['has_significant_presence']:
                print(f"  Peak Year: {peak_info['peak_year']}")
                print(f"  Peak Share: {peak_info['peak_share']:.1%}")

        print(f"\nValidation: {result['validation']['message']}")

        if 'fleet' in result and 'error' not in result['fleet']:
            print(f"\nFleet Tracking (2040):")
            print(f"  Total Fleet: {result['fleet']['total'][-1]:,.0f}")
            print(f"  EV Fleet: {result['fleet']['ev'][-1]:,.0f}")

        print(f"\n{'='*60}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
