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
        Forecast capacity for a single technology using YoY growth averaging

        Args:
            technology: Technology name (e.g., "Solar_PV", "Onshore_Wind")
            region: Region name
            end_year: Final forecast year

        Returns:
            Tuple of (years, capacity_gw)
        """
        try:
            hist_years, hist_capacity = self.data_loader.get_capacity_data(technology, region)
            years, capacity = yoy_growth_average(
                hist_years,
                hist_capacity,
                end_year,
                self.max_yoy_growth
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
                # Interpolate/extrapolate to match forecast years
                cfs = np.interp(years, hist_years, hist_cfs)
                return cfs
        except Exception:
            pass

        # Fallback to default CF
        default_cf = self.default_cfs.get(technology, 0.25)
        # Apply gradual improvement (0.3% per year)
        cf_improvement = self.config["default_parameters"]["capacity_factor_improvement"]
        base_year = years[0]
        cfs = np.array([default_cf * (1 + cf_improvement) ** (year - base_year) for year in years])

        # Clamp to valid range
        min_cf = self.config["default_parameters"]["min_capacity_factor"]
        max_cf = self.config["default_parameters"]["max_capacity_factor"]
        cfs = np.clip(cfs, min_cf, max_cf)

        return cfs

    def forecast_swb_capacities(
        self,
        region: str,
        end_year: int
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Forecast capacities for all SWB components

        Args:
            region: Region name
            end_year: Final forecast year

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
        years, capacity = self.forecast_component_capacity("Battery_Storage", region, end_year)
        if years is not None:
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

        Args:
            capacity_forecasts: Dictionary of {technology: (years, capacity_gw)}
            region: Region name

        Returns:
            Dictionary of {technology: (years, generation_gwh)}
        """
        generation_forecasts = {}

        for technology, (years, capacity_gw) in capacity_forecasts.items():
            # Get capacity factors
            cfs = self.get_capacity_factor(technology, region, years)

            # Convert to generation
            generation_gwh = convert_capacity_to_generation(capacity_gw, cfs)

            generation_forecasts[technology] = (years, generation_gwh)

        return generation_forecasts

    def forecast_swb_generation(
        self,
        region: str,
        end_year: int
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Complete SWB generation forecast (capacity + conversion)

        Args:
            region: Region name
            end_year: Final forecast year

        Returns:
            Dictionary with capacity and generation forecasts
        """
        # Forecast capacities
        capacity_forecasts = self.forecast_swb_capacities(region, end_year)

        # Convert to generation
        generation_forecasts = self.convert_to_generation(capacity_forecasts, region)

        # Combine results
        results = {
            "capacities": capacity_forecasts,
            "generation": generation_forecasts
        }

        return results


if __name__ == "__main__":
    print("Capacity Forecasting module for SWB")
