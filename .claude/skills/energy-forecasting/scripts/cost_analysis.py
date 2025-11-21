"""
Cost Analysis for Energy Forecasting (SWB)
Calculates LCOE, SCOE, SWB stack cost, and tipping points
"""

import numpy as np
from typing import Dict, Tuple, Optional
from utils import log_cagr_forecast, rolling_median, find_intersection
from exceptions import DataNotFoundError, DataValidationError, ConfigurationError


class CostAnalyzer:
    """Analyzes cost curves and detects tipping points for SWB vs fossil fuels"""

    def __init__(self, config: dict, data_loader):
        """
        Initialize cost analyzer

        Args:
            config: Configuration dictionary
            data_loader: DataLoader instance
        """
        self.config = config
        self.data_loader = data_loader
        self.battery_params = {
            "duration_hours": config["default_parameters"]["battery_duration_hours"],
            "cycle_life": config["default_parameters"]["battery_cycle_life"],
            "cycles_per_year": config["default_parameters"]["battery_cycles_per_year"],
            "rte": config["default_parameters"]["battery_rte"],
            "fixed_om": config["default_parameters"]["battery_fixed_om"]
        }
        self.end_year = config["default_parameters"].get("end_year", 2030)

    def calculate_scoe(
        self,
        battery_capex_per_kwh: float,
        duration_hours: Optional[float] = None
    ) -> float:
        """
        Calculate Storage Cost of Energy (SCOE) for battery

        Formula: SCOE = (Capex * 1000) / (Cycles * Duration * RTE) + Fixed_OM

        Args:
            battery_capex_per_kwh: Battery capital cost in $/kWh
            duration_hours: Battery duration (default from config)

        Returns:
            SCOE in $/MWh
        """
        if duration_hours is None:
            duration_hours = self.battery_params["duration_hours"]

        cycles = self.battery_params["cycle_life"]
        rte = self.battery_params["rte"]
        fixed_om = self.battery_params["fixed_om"]

        # SCOE calculation: (Capex * 1000) / (Cycles * Duration * RTE) + Fixed_OM
        scoe = (battery_capex_per_kwh * 1000) / (cycles * duration_hours * rte) + fixed_om

        return scoe

    def calculate_swb_stack_cost(
        self,
        solar_lcoe: float,
        wind_lcoe: float,
        battery_scoe: float,
        method: str = None
    ) -> float:
        """
        Calculate SWB stack cost using specified method

        Methods:
        - option_a (conservative): MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE
        - option_b (weighted): Solar_LCOE × w_s + Wind_LCOE × w_w + Battery_SCOE × w_b

        Args:
            solar_lcoe: Solar LCOE in $/MWh
            wind_lcoe: Wind LCOE in $/MWh (combined onshore/offshore)
            battery_scoe: Battery SCOE in $/MWh
            method: Calculation method ('option_a' or 'option_b')

        Returns:
            SWB stack cost in $/MWh
        """
        # Get method from config if not specified
        if method is None:
            method = self.config.get("swb_stack_cost", {}).get("method", "option_a")

        if method == "option_b":
            # Weighted average approach
            weights = self.config.get("swb_stack_cost", {}).get("weights", {
                "solar": 0.4,
                "wind": 0.4,
                "battery": 0.2
            })
            w_s = weights.get("solar", 0.4)
            w_w = weights.get("wind", 0.4)
            w_b = weights.get("battery", 0.2)

            # Validate weights sum to 1.0
            total_weight = w_s + w_w + w_b
            if abs(total_weight - 1.0) > 0.01:
                print(f"  WARNING: SWB weights sum to {total_weight:.2f}, normalizing to 1.0")
                w_s /= total_weight
                w_w /= total_weight
                w_b /= total_weight

            return solar_lcoe * w_s + wind_lcoe * w_w + battery_scoe * w_b
        else:
            # Option A: Conservative approach (default)
            return max(solar_lcoe, wind_lcoe) + battery_scoe

    def _calculate_fallback_lcoe(
        self,
        technology: str,
        region: str,
        end_year: int,
        base_year: int = 2020
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate fallback LCOE when dataset unavailable
        Uses regional baseline values and annual change rates
        Based on industry data and SWB v4 spec fallback values

        Args:
            technology: 'coal' or 'gas'
            region: Region name
            end_year: Final forecast year
            base_year: Base year for calculations (default 2020)

        Returns:
            Tuple of (years, lcoe_values)
        """
        fallback_config = self.config.get("fallback_lcoe_values", {}).get(technology, {})

        if not fallback_config:
            raise ConfigurationError(f"No fallback LCOE configuration for {technology}")

        baselines = fallback_config.get("baselines_2020", {})
        annual_rates = fallback_config.get("annual_change_rates", {})

        base_lcoe = baselines.get(region, baselines.get("Global", 70))
        change_rate = annual_rates.get(region, annual_rates.get("Global", 0.015))

        # Generate time series
        years = np.array(range(base_year, end_year + 1))
        lcoe = base_lcoe * ((1 + change_rate) ** (years - base_year))

        print(f"  INFO: Using fallback LCOE for {technology} in {region}")
        print(f"        Base: ${base_lcoe:.1f}/MWh, Annual change: {change_rate*100:.1f}%")

        return years, lcoe

    def apply_carbon_pricing(
        self,
        lcoe: np.ndarray,
        technology: str,
        years: np.ndarray,
        region: str,
        scenario: str
    ) -> np.ndarray:
        """
        Apply carbon pricing to fossil fuel LCOE

        Args:
            lcoe: Base LCOE array in $/MWh
            technology: 'coal' or 'gas'
            years: Years array
            region: Region name
            scenario: Scenario name

        Returns:
            Adjusted LCOE with carbon pricing
        """
        carbon_config = self.config.get("carbon_pricing", {})

        if not carbon_config.get("enabled", False):
            return lcoe

        # Get regional base carbon price ($/tonne CO2, 2020)
        base_prices = carbon_config.get("regional_base_prices_2020", {})
        base_price = base_prices.get(region, base_prices.get("Global", 15))

        # Get scenario multiplier
        scenario_multipliers = carbon_config.get("scenario_multipliers", {})
        multiplier = scenario_multipliers.get(scenario, 1.0)

        # Apply multiplier
        base_price = base_price * multiplier

        # Get annual growth rate
        growth_rate = carbon_config.get("annual_growth_rate", 0.05)

        # Calculate carbon price trajectory
        base_year = 2020
        carbon_prices = base_price * ((1 + growth_rate) ** (years - base_year))

        # Apply floor and ceiling
        floor = carbon_config.get("price_floor_per_ton", 0)
        ceiling = carbon_config.get("price_ceiling_per_ton", 300)
        carbon_prices = np.clip(carbon_prices, floor, ceiling)

        # Get emission factors
        emission_factors = self.config.get("emission_factors", {})

        if technology == 'coal':
            # Convert kg CO2/MWh to tonnes CO2/MWh
            emission_factor_tonnes = emission_factors.get("coal_kg_co2_per_mwh", 1000) / 1000
        elif technology == 'gas':
            emission_factor_tonnes = emission_factors.get("gas_kg_co2_per_mwh", 450) / 1000
        else:
            return lcoe  # No carbon pricing for clean tech

        # Calculate carbon cost ($/MWh)
        carbon_cost = carbon_prices * emission_factor_tonnes

        # Add to LCOE
        adjusted_lcoe = lcoe + carbon_cost

        print(f"  INFO: Applied carbon pricing to {technology}")
        print(f"        {years[0]}: ${carbon_prices[0]:.1f}/ton → +${carbon_cost[0]:.1f}/MWh")
        print(f"        {years[-1]}: ${carbon_prices[-1]:.1f}/ton → +${carbon_cost[-1]:.1f}/MWh")

        return adjusted_lcoe

    def calculate_integration_costs(
        self,
        swb_penetration: np.ndarray,
        region: str
    ) -> np.ndarray:
        """
        Calculate grid integration costs for high SWB penetration

        Args:
            swb_penetration: SWB share of total generation (0.0 to 1.0)
            region: Region name

        Returns:
            Integration cost in $/MWh
        """
        integration_config = self.config.get("integration_costs", {})

        if not integration_config.get("enabled", False):
            return np.zeros_like(swb_penetration)

        # Base cost (fixed cost at any penetration)
        base_cost = integration_config.get("base_cost_per_mwh", 5)

        # Maximum additional cost at high penetration
        max_additional = integration_config.get("max_additional_cost_per_mwh", 30)

        # Penetration exponent (controls how quickly costs rise)
        exponent = integration_config.get("penetration_exponent", 2)

        # Regional multiplier
        regional_multipliers = integration_config.get("regional_multipliers", {})
        multiplier = regional_multipliers.get(region, 1.0)

        # Calculate cost curve
        # Cost increases rapidly above 20% penetration
        # Formula: base + max_additional * ((penetration - 0.2) / 0.8) ^ exponent
        additional_cost = np.where(
            swb_penetration > 0.2,
            max_additional * (((swb_penetration - 0.2) / 0.8) ** exponent),
            0
        )

        # Apply regional multiplier
        total_cost = (base_cost + additional_cost) * multiplier

        # Cap at reasonable maximum
        total_cost = np.minimum(total_cost, base_cost + max_additional * multiplier)

        return total_cost

    def forecast_cost_curves(
        self,
        region: str,
        end_year: int
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Forecast all cost curves (LCOE + SCOE) through end_year

        Args:
            region: Region name
            end_year: Final forecast year

        Returns:
            Dictionary of {technology: (years, costs)}
        """
        smoothing_window = self.config["default_parameters"]["smoothing_window"]
        forecasts = {}

        # Forecast Solar LCOE
        try:
            hist_years, hist_lcoe = self.data_loader.get_lcoe_data("Solar_PV", region)
            smoothed_lcoe = rolling_median(np.array(hist_lcoe), smoothing_window)
            years, lcoe = log_cagr_forecast(hist_years, smoothed_lcoe.tolist(), end_year)
            forecasts["Solar_PV"] = (years, lcoe)
        except Exception as e:
            print(f"Warning: Could not load Solar LCOE for {region}: {e}")
            forecasts["Solar_PV"] = None

        # Forecast Onshore Wind LCOE
        try:
            hist_years, hist_lcoe = self.data_loader.get_lcoe_data("Onshore_Wind", region)
            smoothed_lcoe = rolling_median(np.array(hist_lcoe), smoothing_window)
            years, lcoe = log_cagr_forecast(hist_years, smoothed_lcoe.tolist(), end_year)
            forecasts["Onshore_Wind"] = (years, lcoe)
        except Exception as e:
            print(f"Warning: Could not load Onshore Wind LCOE for {region}: {e}")
            forecasts["Onshore_Wind"] = None

        # Forecast Offshore Wind LCOE (optional)
        try:
            hist_years, hist_lcoe = self.data_loader.get_lcoe_data("Offshore_Wind", region)
            smoothed_lcoe = rolling_median(np.array(hist_lcoe), smoothing_window)
            years, lcoe = log_cagr_forecast(hist_years, smoothed_lcoe.tolist(), end_year)
            forecasts["Offshore_Wind"] = (years, lcoe)
        except Exception:
            forecasts["Offshore_Wind"] = None

        # Calculate combined Wind LCOE (MIN of onshore/offshore if both available)
        if forecasts["Onshore_Wind"] is not None and forecasts["Offshore_Wind"] is not None:
            onshore_years, onshore_lcoe = forecasts["Onshore_Wind"]
            offshore_years, offshore_lcoe = forecasts["Offshore_Wind"]

            # Convert to numpy arrays for easier manipulation
            onshore_years = np.array(onshore_years)
            onshore_lcoe = np.array(onshore_lcoe)
            offshore_years = np.array(offshore_years)
            offshore_lcoe = np.array(offshore_lcoe)

            # Find common years (they may differ if using fallback data)
            common_years = np.intersect1d(onshore_years, offshore_years)
            if len(common_years) > 0:
                onshore_mask = np.isin(onshore_years, common_years)
                offshore_mask = np.isin(offshore_years, common_years)
                onshore_values = onshore_lcoe[onshore_mask]
                offshore_values = offshore_lcoe[offshore_mask]
                combined_lcoe = np.minimum(onshore_values, offshore_values)
                forecasts["Wind_Combined"] = (common_years.tolist(), combined_lcoe.tolist())
            else:
                # No overlap, use onshore (typically has more data)
                forecasts["Wind_Combined"] = forecasts["Onshore_Wind"]
        elif forecasts["Onshore_Wind"] is not None:
            forecasts["Wind_Combined"] = forecasts["Onshore_Wind"]
        elif forecasts["Offshore_Wind"] is not None:
            forecasts["Wind_Combined"] = forecasts["Offshore_Wind"]

        # Forecast Battery SCOE (from installed cost)
        duration = self.battery_params["duration_hours"]
        try:
            hist_years, hist_cost = self.data_loader.get_battery_cost_data(region, duration)
            # hist_cost is in $/kWh
            smoothed_cost = rolling_median(np.array(hist_cost), smoothing_window)
            years, capex_forecast = log_cagr_forecast(hist_years, smoothed_cost.tolist(), end_year)
            # Calculate SCOE from capex
            scoe_forecast = np.array([self.calculate_scoe(capex) for capex in capex_forecast])
            forecasts["Battery_Storage"] = (years, scoe_forecast)
        except DataNotFoundError as e:
            print(f"Warning: {e}. Using fallback battery cost.")
            # Fallback: reasonable baseline cost declining over time
            hist_years = [2020, 2023]
            hist_cost = [200, 150]  # $/kWh
            years, capex_forecast = log_cagr_forecast(hist_years, hist_cost, end_year)
            scoe_forecast = np.array([self.calculate_scoe(capex) for capex in capex_forecast])
            forecasts["Battery_Storage"] = (years, scoe_forecast)
        except Exception as e:
            print(f"Warning: Could not load Battery cost for {region}: {e}")
            forecasts["Battery_Storage"] = None

        # Forecast Coal LCOE
        try:
            hist_years, hist_lcoe = self.data_loader.get_lcoe_data("Coal_Power", region)
            smoothed_lcoe = rolling_median(np.array(hist_lcoe), smoothing_window)
            years, lcoe = log_cagr_forecast(hist_years, smoothed_lcoe.tolist(), end_year)
            forecasts["Coal_Power"] = (years, lcoe)
        except Exception as e:
            print(f"Warning: Could not load Coal LCOE for {region}: {e}")
            # Use fallback calculation
            try:
                years, lcoe = self._calculate_fallback_lcoe('coal', region, end_year)
                forecasts["Coal_Power"] = (years.tolist(), lcoe.tolist())
            except Exception as fallback_error:
                print(f"Error: Fallback LCOE calculation failed: {fallback_error}")
                forecasts["Coal_Power"] = None

        # Forecast Gas LCOE
        try:
            hist_years, hist_lcoe = self.data_loader.get_lcoe_data("Natural_Gas_Power", region)
            smoothed_lcoe = rolling_median(np.array(hist_lcoe), smoothing_window)
            years, lcoe = log_cagr_forecast(hist_years, smoothed_lcoe.tolist(), end_year)
            forecasts["Natural_Gas_Power"] = (years, lcoe)
        except Exception as e:
            print(f"Warning: Could not load Gas LCOE for {region}: {e}")
            # Use fallback calculation
            try:
                years, lcoe = self._calculate_fallback_lcoe('gas', region, end_year)
                forecasts["Natural_Gas_Power"] = (years.tolist(), lcoe.tolist())
            except Exception as fallback_error:
                print(f"Error: Fallback LCOE calculation failed: {fallback_error}")
                forecasts["Natural_Gas_Power"] = None

        return forecasts

    def find_tipping_points(
        self,
        cost_forecasts: Dict[str, Tuple[np.ndarray, np.ndarray]]
    ) -> Dict[str, Optional[int]]:
        """
        Find tipping points where SWB stack cost < incumbent LCOE

        Args:
            cost_forecasts: Dictionary of forecasted cost curves

        Returns:
            Dictionary with tipping_vs_coal, tipping_vs_gas, tipping_overall
        """
        # Calculate SWB stack cost
        if cost_forecasts.get("Solar_PV") and cost_forecasts.get("Wind_Combined") and cost_forecasts.get("Battery_Storage"):
            solar_years, solar_lcoe = cost_forecasts["Solar_PV"]
            wind_years, wind_lcoe = cost_forecasts["Wind_Combined"]
            battery_years, battery_scoe = cost_forecasts["Battery_Storage"]

            # Convert to numpy arrays
            solar_years = np.array(solar_years)
            solar_lcoe = np.array(solar_lcoe)
            wind_years = np.array(wind_years)
            wind_lcoe = np.array(wind_lcoe)
            battery_years = np.array(battery_years)
            battery_scoe = np.array(battery_scoe)

            # Find common year range
            min_year = max(solar_years[0], wind_years[0], battery_years[0])
            max_year = min(solar_years[-1], wind_years[-1], battery_years[-1])
            years = np.arange(int(min_year), int(max_year) + 1)

            # Interpolate all to common years
            solar_lcoe_aligned = np.interp(years, solar_years, solar_lcoe)
            wind_lcoe_aligned = np.interp(years, wind_years, wind_lcoe)
            battery_scoe_aligned = np.interp(years, battery_years, battery_scoe)

            # Calculate SWB stack cost for aligned arrays
            swb_stack_cost = np.array([
                self.calculate_swb_stack_cost(solar_lcoe_aligned[i], wind_lcoe_aligned[i], battery_scoe_aligned[i])
                for i in range(len(years))
            ])

            # Apply 3-year rolling median smoothing before tipping point detection
            # Per SWB v4 spec: "Smooth with a 3-year rolling median before intersection checks"
            smoothing_window = self.config["default_parameters"].get("smoothing_window", 3)
            swb_stack_cost_smoothed = rolling_median(swb_stack_cost, window=smoothing_window)
        else:
            return {"tipping_vs_coal": None, "tipping_vs_gas": None, "tipping_overall": None}

        # Find tipping vs Coal
        tipping_vs_coal = None
        if cost_forecasts.get("Coal_Power"):
            coal_years, coal_lcoe = cost_forecasts["Coal_Power"]
            # Apply smoothing to coal LCOE as well
            coal_lcoe_smoothed = rolling_median(np.array(coal_lcoe), window=smoothing_window)
            tipping_vs_coal = find_intersection(years, swb_stack_cost_smoothed, coal_lcoe_smoothed)

        # Find tipping vs Gas
        tipping_vs_gas = None
        if cost_forecasts.get("Natural_Gas_Power"):
            gas_years, gas_lcoe = cost_forecasts["Natural_Gas_Power"]
            # Apply smoothing to gas LCOE as well
            gas_lcoe_smoothed = rolling_median(np.array(gas_lcoe), window=smoothing_window)
            tipping_vs_gas = find_intersection(years, swb_stack_cost_smoothed, gas_lcoe_smoothed)

        # Overall tipping (first of coal or gas)
        tipping_overall = None
        if tipping_vs_coal and tipping_vs_gas:
            tipping_overall = min(tipping_vs_coal, tipping_vs_gas)
        elif tipping_vs_coal:
            tipping_overall = tipping_vs_coal
        elif tipping_vs_gas:
            tipping_overall = tipping_vs_gas

        return {
            "tipping_vs_coal": tipping_vs_coal,
            "tipping_vs_gas": tipping_vs_gas,
            "tipping_overall": tipping_overall,
            "swb_stack_cost": (years, swb_stack_cost_smoothed)
        }


if __name__ == "__main__":
    print("Cost Analysis module for SWB Energy Forecasting")
