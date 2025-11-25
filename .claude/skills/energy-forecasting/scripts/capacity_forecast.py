"""
Capacity Forecasting for SWB Components
Uses YoY growth averaging method to forecast capacity and generation
"""

import numpy as np
from typing import Dict, Tuple
from utils import yoy_growth_average, convert_capacity_to_generation


class CapacityForecaster:
    """Forecasts capacity and generation for SWB components"""

    def __init__(self, config: dict, data_loader):
        """
        Initialize capacity forecaster

        Args:
            config: Configuration dictionary
            data_loader: DataLoader instance
        """
        self.config = config
        self.data_loader = data_loader
        self.default_cfs = config["capacity_factors"]["default"]
        self.max_yoy_growth = config["default_parameters"]["max_yoy_growth"]

    def forecast_component_capacity(
        self,
        technology: str,
        region: str,
        end_year: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forecast capacity for a single technology using YoY growth averaging with decay.

        Growth rate decay prevents unrealistic compounding where SWB exceeds demand.

        Args:
            technology: Technology name (e.g., "Solar_PV", "Onshore_Wind")
            region: Region name
            end_year: Final forecast year

        Returns:
            Tuple of (years, capacity_gw)
        """
        try:
            hist_years, hist_capacity = self.data_loader.get_capacity_data(technology, region)

            # Get growth decay settings from config
            decay_config = self.config.get("growth_decay_parameters", {})
            if decay_config.get("enabled", False):
                decay_rate = decay_config.get("time_decay_rate", 0.05)
                floor_growth_rate = decay_config.get("floor_growth_rate", 0.02)
            else:
                decay_rate = 0.0
                floor_growth_rate = 0.02

            years, capacity = yoy_growth_average(
                hist_years,
                hist_capacity,
                end_year,
                self.max_yoy_growth,
                decay_rate=decay_rate,
                floor_growth_rate=floor_growth_rate
            )
            return years, capacity
        except Exception as e:
            print(f"Warning: Could not forecast {technology} capacity for {region}: {e}")
            return None, None

    def get_capacity_factor(
        self,
        technology: str,
        region: str,
        years: np.ndarray
    ) -> np.ndarray:
        """
        Get capacity factor for a technology (historical data or default)

        Args:
            technology: Technology name
            region: Region name
            years: Array of years

        Returns:
            Array of capacity factors (one per year)
        """
        try:
            # Try to load historical CF data
            hist_years, hist_cfs = self.data_loader.get_capacity_factor_data(technology, region)
            if hist_years is not None and hist_cfs is not None:
                # Convert from percentage to decimal if needed
                # CF data can be in percentage format (16.08) or decimal format (0.1608)
                if np.any(hist_cfs > 1.0):
                    hist_cfs = hist_cfs / 100.0

                # Interpolate/extrapolate to match forecast years
                cfs = np.interp(years, hist_years, hist_cfs)
                return cfs
        except Exception:
            pass

        # Fallback to regional CF, then global, then default
        regional_cfs = self.config.get("capacity_factors", {}).get("regional", {})

        # Try regional CF first
        if region in regional_cfs and technology in regional_cfs[region]:
            default_cf = regional_cfs[region][technology]
        # Try Global CF next
        elif "Global" in regional_cfs and technology in regional_cfs["Global"]:
            default_cf = regional_cfs["Global"][technology]
        # Finally use default
        else:
            default_cf = self.default_cfs.get(technology, 0.25)
        # Apply gradual improvement (ADDITIVE: +0.003 per year = 0.3 percentage points/year)
        # Per SWB v4 spec: modest improvement ≤0.3 percentage points per year
        cf_improvement = self.config["default_parameters"]["capacity_factor_improvement"]
        base_year = years[0]

        # ADDITIVE improvement: CF_year = CF_base + improvement × (year - base_year)
        cfs = np.array([default_cf + cf_improvement * (year - base_year) for year in years])

        # Clamp to valid range
        min_cf = self.config["default_parameters"]["min_capacity_factor"]
        max_cf = self.config["default_parameters"]["max_capacity_factor"]
        cfs = np.clip(cfs, min_cf, max_cf)

        return cfs

    def calculate_battery_capacity_option_a(
        self,
        peak_load_gw: np.ndarray,
        years: np.ndarray
    ) -> np.ndarray:
        """
        Calculate battery energy capacity using Option A (resilience days heuristic)

        Formula: Energy_Capacity (GWh) = k_days × Peak_Load (GW) × 24 hours

        Args:
            peak_load_gw: Peak load in GW for each year
            years: Array of years

        Returns:
            Battery energy capacity in GWh for each year
        """
        # Get resilience days from config (default: 2 days)
        k_days = self.config["battery_parameters"].get("resilience_days", 2)

        # Calculate battery energy capacity
        # Energy_Capacity (GWh) = k_days × Peak_Load (GW) × 24 hours
        battery_capacity_gwh = k_days * peak_load_gw * 24

        print(f"  INFO: Battery capacity calculated using Option A (resilience days heuristic)")
        print(f"        Resilience days: {k_days}, Peak load range: {peak_load_gw.min():.1f}-{peak_load_gw.max():.1f} GW")

        return battery_capacity_gwh

    def forecast_swb_capacities(
        self,
        region: str,
        end_year: int,
        peak_load_gw: np.ndarray = None
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Forecast capacities for all SWB components

        Args:
            region: Region name
            end_year: Final forecast year
            peak_load_gw: Optional peak load (GW) for battery sizing Option A

        Returns:
            Dictionary of {technology: (years, capacity_gw)}
        """
        capacities = {}

        # Forecast Solar PV
        years, capacity = self.forecast_component_capacity("Solar_PV", region, end_year)
        if years is not None:
            capacities["Solar_PV"] = (years, capacity)

        # Forecast Onshore Wind
        years, capacity = self.forecast_component_capacity("Onshore_Wind", region, end_year)
        if years is not None:
            capacities["Onshore_Wind"] = (years, capacity)

        # Forecast Offshore Wind
        years, capacity = self.forecast_component_capacity("Offshore_Wind", region, end_year)
        if years is not None:
            capacities["Offshore_Wind"] = (years, capacity)

        # Forecast Battery Storage
        # Try Option B first (historical trends), fallback to Option A (resilience days)
        years, capacity = self.forecast_component_capacity("Battery_Storage", region, end_year)
        if years is not None:
            capacities["Battery_Storage"] = (years, capacity)
        elif peak_load_gw is not None:
            # Fallback to Option A: resilience days heuristic
            print(f"  WARNING: No historical battery data for {region}, using Option A sizing")
            # Get years from other components
            if "Solar_PV" in capacities:
                years = capacities["Solar_PV"][0]
            elif "Onshore_Wind" in capacities:
                years = capacities["Onshore_Wind"][0]
            else:
                years = np.arange(2020, end_year + 1)

            capacity = self.calculate_battery_capacity_option_a(peak_load_gw, years)
            capacities["Battery_Storage"] = (years, capacity)

        # CSP (conditional - include if capacity > 1% of solar)
        try:
            csp_threshold = self.config["default_parameters"]["csp_threshold"]
            years, csp_capacity = self.forecast_component_capacity("CSP", region, end_year)
            if years is not None and capacities.get("Solar_PV"):
                solar_years, solar_capacity = capacities["Solar_PV"]
                # Check if CSP is significant (> 1% of solar in any year)
                csp_ratio = csp_capacity / np.maximum(solar_capacity, 1.0)
                if np.any(csp_ratio > csp_threshold):
                    capacities["CSP"] = (years, csp_capacity)
        except Exception:
            pass  # CSP optional

        return capacities

    def convert_to_generation(
        self,
        capacity_forecasts: Dict[str, Tuple[np.ndarray, np.ndarray]],
        region: str
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Convert capacity forecasts to generation using capacity factors
        Handles Wind_Mix datasets (combined onshore + offshore wind)

        Args:
            capacity_forecasts: Dictionary of {technology: (years, capacity_gw)}
            region: Region name

        Returns:
            Dictionary of {technology: (years, generation_gwh)}
        """
        generation_forecasts = {}

        for technology, (years, capacity_gw) in capacity_forecasts.items():
            # Skip Battery_Storage - it's an energy storage system, not a generator
            # Battery metrics (throughput, etc.) are calculated separately in calculate_battery_metrics()
            if technology == "Battery_Storage":
                continue

            # Get capacity factors
            cfs = self.get_capacity_factor(technology, region, years)

            # Convert to generation
            generation_gwh = convert_capacity_to_generation(capacity_gw, cfs)

            generation_forecasts[technology] = (years, generation_gwh)

        # Validate wind generation if both onshore and offshore are present
        # Wind_Mix datasets represent combined onshore + offshore wind
        if "Onshore_Wind" in generation_forecasts and "Offshore_Wind" in generation_forecasts:
            onshore_years, onshore_gen = generation_forecasts["Onshore_Wind"]
            offshore_years, offshore_gen = generation_forecasts["Offshore_Wind"]

            # Calculate combined wind generation
            if len(onshore_years) == len(offshore_years) and np.array_equal(onshore_years, offshore_years):
                combined_wind_gen = onshore_gen + offshore_gen
                generation_forecasts["Wind_Total"] = (onshore_years, combined_wind_gen)
                print(f"  INFO: Combined wind generation calculated (Onshore + Offshore)")

        return generation_forecasts

    def calculate_battery_metrics(
        self,
        battery_capacity_gwh: np.ndarray,
        years: np.ndarray
    ) -> Dict:
        """
        Calculate detailed battery storage metrics

        Args:
            battery_capacity_gwh: Battery energy capacity in GWh
            years: Array of years

        Returns:
            Dictionary with battery metrics:
            - energy_capacity_gwh: Energy capacity (GWh)
            - power_capacity_gw: Power capacity (GW)
            - throughput_twh: Annual throughput (TWh/year)
            - cycles_per_year: Battery utilization (cycles/year)
            - duration_hours: Storage duration (hours)
            - round_trip_efficiency: Round-trip efficiency (decimal)
        """
        # Get battery parameters from config
        battery_params = self.config["battery_parameters"]
        duration_hours = battery_params["duration_hours"]
        cycles_per_year = battery_params["cycles_per_year"]
        round_trip_efficiency = battery_params["round_trip_efficiency"]

        # Calculate power capacity from energy capacity and duration
        # Power (GW) = Energy (GWh) / Duration (hours)
        power_capacity_gw = battery_capacity_gwh / duration_hours

        # Calculate annual throughput
        # Throughput (TWh) = Energy_Capacity (GWh) × cycles_per_year / 1000
        throughput_twh = battery_capacity_gwh * cycles_per_year / 1000

        return {
            "years": years.tolist(),
            "energy_capacity_gwh": battery_capacity_gwh.tolist(),
            "power_capacity_gw": power_capacity_gw.tolist(),
            "throughput_twh_per_year": throughput_twh.tolist(),
            "cycles_per_year": cycles_per_year,
            "duration_hours": duration_hours,
            "round_trip_efficiency": round_trip_efficiency
        }

    def forecast_swb_generation(
        self,
        region: str,
        end_year: int,
        peak_load_gw: np.ndarray = None
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Complete SWB generation forecast (capacity + conversion)

        Args:
            region: Region name
            end_year: Final forecast year
            peak_load_gw: Optional peak load (GW) for battery sizing Option A

        Returns:
            Dictionary with capacity, generation, and battery metrics
        """
        # Forecast capacities
        capacity_forecasts = self.forecast_swb_capacities(region, end_year, peak_load_gw)

        # Convert to generation
        generation_forecasts = self.convert_to_generation(capacity_forecasts, region)

        # Calculate battery metrics if battery capacity is forecasted
        battery_metrics = None
        if "Battery_Storage" in capacity_forecasts:
            years, battery_capacity_gwh = capacity_forecasts["Battery_Storage"]
            battery_metrics = self.calculate_battery_metrics(battery_capacity_gwh, years)

        # Combine results
        results = {
            "capacities": capacity_forecasts,
            "generation": generation_forecasts,
            "battery_metrics": battery_metrics
        }

        return results


if __name__ == "__main__":
    print("Capacity Forecasting module for SWB")
