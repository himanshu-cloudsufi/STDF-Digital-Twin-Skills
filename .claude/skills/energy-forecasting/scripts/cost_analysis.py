"""
Cost Analysis for Energy Forecasting (SWB)
Calculates LCOE, SCOE, SWB stack cost, and tipping points
"""

import numpy as np
from typing import Dict, Tuple, Optional
from utils import log_cagr_forecast, rolling_median, find_intersection


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
        battery_scoe: float
    ) -> float:
        """
        Calculate SWB stack cost

        Formula: MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE

        Args:
            solar_lcoe: Solar LCOE in $/MWh
            wind_lcoe: Wind LCOE in $/MWh (combined onshore/offshore)
            battery_scoe: Battery SCOE in $/MWh

        Returns:
            SWB stack cost in $/MWh
        """
        return max(solar_lcoe, wind_lcoe) + battery_scoe

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
            combined_lcoe = np.minimum(onshore_lcoe, offshore_lcoe)
            forecasts["Wind_Combined"] = (onshore_years, combined_lcoe)
        elif forecasts["Onshore_Wind"] is not None:
            forecasts["Wind_Combined"] = forecasts["Onshore_Wind"]
        elif forecasts["Offshore_Wind"] is not None:
            forecasts["Wind_Combined"] = forecasts["Offshore_Wind"]

        # Forecast Battery SCOE (from installed cost)
        try:
            hist_years, hist_cost = self.data_loader.get_capacity_data("Battery_Storage", region)
            # Assume installed cost is in $/kWh
            smoothed_cost = rolling_median(np.array(hist_cost), smoothing_window)
            years, capex_forecast = log_cagr_forecast(hist_years, smoothed_cost.tolist(), end_year)
            # Calculate SCOE from capex
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
            # Fallback using multiplier
            forecasts["Coal_Power"] = None

        # Forecast Gas LCOE
        try:
            hist_years, hist_lcoe = self.data_loader.get_lcoe_data("Natural_Gas_Power", region)
            smoothed_lcoe = rolling_median(np.array(hist_lcoe), smoothing_window)
            years, lcoe = log_cagr_forecast(hist_years, smoothed_lcoe.tolist(), end_year)
            forecasts["Natural_Gas_Power"] = (years, lcoe)
        except Exception as e:
            print(f"Warning: Could not load Gas LCOE for {region}: {e}")
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

            # All should have same years
            years = solar_years
            swb_stack_cost = np.array([
                self.calculate_swb_stack_cost(solar_lcoe[i], wind_lcoe[i], battery_scoe[i])
                for i in range(len(years))
            ])
        else:
            return {"tipping_vs_coal": None, "tipping_vs_gas": None, "tipping_overall": None}

        # Find tipping vs Coal
        tipping_vs_coal = None
        if cost_forecasts.get("Coal_Power"):
            coal_years, coal_lcoe = cost_forecasts["Coal_Power"]
            tipping_vs_coal = find_intersection(years, swb_stack_cost, coal_lcoe)

        # Find tipping vs Gas
        tipping_vs_gas = None
        if cost_forecasts.get("Natural_Gas_Power"):
            gas_years, gas_lcoe = cost_forecasts["Natural_Gas_Power"]
            tipping_vs_gas = find_intersection(years, swb_stack_cost, gas_lcoe)

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
            "swb_stack_cost": (years, swb_stack_cost)
        }


if __name__ == "__main__":
    print("Cost Analysis module for SWB Energy Forecasting")
