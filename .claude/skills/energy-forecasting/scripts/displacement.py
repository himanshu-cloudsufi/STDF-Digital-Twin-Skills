"""
Displacement Logic for SWB vs Fossil Fuels
Handles sequenced coal-first or gas-first displacement with reserve floors
"""

import numpy as np
from typing import Dict, Tuple


class DisplacementAnalyzer:
    """Analyzes and models displacement of fossil fuels by SWB"""

    def __init__(self, config: dict, data_loader):
        """
        Initialize displacement analyzer

        Args:
            config: Configuration dictionary
            data_loader: DataLoader instance
        """
        self.config = config
        self.data_loader = data_loader
        self.displacement_sequences = config["displacement_sequence"]
        self.coal_reserve_floor = config["default_parameters"]["coal_reserve_floor"]
        self.gas_reserve_floor = config["default_parameters"]["gas_reserve_floor"]

    def calculate_non_swb_baseline(
        self,
        region: str,
        years: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate non-SWB generation baseline (nuclear + hydro + other)
        Multi-level fallback strategy due to missing datasets

        Args:
            region: Region name
            years: Array of forecast years

        Returns:
            Tuple of (years, non_swb_generation_gwh)
        """
        # Method 1: Try loading actual nuclear + hydro data
        try:
            nuclear_years, nuclear_gen = self.data_loader.get_generation_data("Nuclear", region)
            hydro_years, hydro_gen = self.data_loader.get_generation_data("Hydro", region)

            # Interpolate to forecast years
            nuclear_forecast = np.interp(years, nuclear_years, nuclear_gen)
            hydro_forecast = np.interp(years, hydro_years, hydro_gen)

            # Apply decline rate for nuclear retirement
            decline_rate = self.config.get("non_swb_decline_rate", 0.01)  # 1% per year
            base_year = years[0]
            decline_factor = (1 - decline_rate) ** (years - base_year)

            nuclear_forecast = nuclear_forecast * decline_factor
            hydro_forecast = hydro_forecast  # Hydro assumed stable

            non_swb_gen = nuclear_forecast + hydro_forecast

            print(f"  INFO: Using actual nuclear + hydro data for non-SWB baseline")
            return years, non_swb_gen

        except Exception as e:
            print(f"  WARNING: Could not load nuclear/hydro data: {e}")

        # Method 2: Derive from total generation residual
        try:
            total_years, total_gen = self.data_loader.get_electricity_demand(region)

            # Get historical fossil + SWB generation
            coal_years, coal_gen = self.data_loader.get_generation_data("Coal_Power", region)
            gas_years, gas_gen = self.data_loader.get_generation_data("Natural_Gas_Power", region)

            # Get SWB generation (with fallback for missing data)
            try:
                solar_years, solar_gen = self.data_loader.get_generation_data("Solar_PV", region)
            except:
                solar_years, solar_gen = coal_years, np.zeros_like(coal_gen)

            try:
                wind_years, wind_gen = self.data_loader.get_generation_data("Onshore_Wind", region)
            except:
                wind_years, wind_gen = coal_years, np.zeros_like(coal_gen)

            # Find common historical period
            common_years = np.intersect1d(total_years, coal_years)
            common_years = np.intersect1d(common_years, gas_years)

            if len(common_years) > 0:
                # Calculate residual for common period
                total_hist = np.interp(common_years, total_years, total_gen)
                coal_hist = np.interp(common_years, coal_years, coal_gen)
                gas_hist = np.interp(common_years, gas_years, gas_gen)
                solar_hist = np.interp(common_years, solar_years, solar_gen)
                wind_hist = np.interp(common_years, wind_years, wind_gen)

                non_swb_hist = total_hist - coal_hist - gas_hist - solar_hist - wind_hist
                non_swb_hist = np.maximum(non_swb_hist, 0)  # Ensure non-negative

                # Calculate average non-SWB percentage
                non_swb_pct = np.mean(non_swb_hist / total_hist)

                # Apply to forecast period
                total_forecast = np.interp(years, total_years, total_gen)
                non_swb_gen = total_forecast * non_swb_pct

                print(f"  INFO: Derived non-SWB baseline from residual ({non_swb_pct*100:.1f}%)")
                return years, non_swb_gen

        except Exception as e:
            print(f"  WARNING: Could not derive non-SWB from residual: {e}")

        # Method 3: Regional percentage estimates (last resort)
        baseline_pct = self.config.get("non_swb_baseline_percentages", {})
        pct = baseline_pct.get(region, 0.20)

        # Estimate total demand for forecast period
        try:
            total_years, total_gen = self.data_loader.get_electricity_demand(region)
            total_forecast = np.interp(years, total_years, total_gen)
        except:
            # Ultimate fallback: use 2020 baseline × growth
            total_2020 = 8000  # TWh (rough global estimate)
            growth_rate = 0.02  # 2% per year
            total_forecast = total_2020 * ((1 + growth_rate) ** (years - 2020))

        non_swb_gen = total_forecast * pct

        print(f"  WARNING: Using fallback non-SWB baseline ({pct*100:.0f}% of total demand)")
        print(f"            No nuclear/hydro datasets available for {region}")

        return years, non_swb_gen

    def get_displacement_sequence(self, region: str) -> str:
        """
        Get displacement sequence for a region

        Args:
            region: Region name

        Returns:
            "coal_first" or "gas_first"
        """
        return self.displacement_sequences.get(region, "coal_first")

    def allocate_fossil_generation(
        self,
        years: np.ndarray,
        total_demand: np.ndarray,
        swb_generation: np.ndarray,
        non_swb_generation: np.ndarray,
        region: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Allocate remaining generation to coal and gas using displacement sequence

        Args:
            years: Array of years
            total_demand: Total electricity demand in GWh
            swb_generation: SWB generation in GWh
            non_swb_generation: Non-SWB (nuclear/hydro) generation in GWh
            region: Region name

        Returns:
            Tuple of (coal_generation, gas_generation) in GWh
        """
        # Calculate residual available for fossil fuels
        residual = total_demand - swb_generation - non_swb_generation
        residual = np.maximum(residual, 0)  # Ensure non-negative

        # Get displacement sequence
        sequence = self.get_displacement_sequence(region)

        # Initialize arrays
        coal_generation = np.zeros_like(residual)
        gas_generation = np.zeros_like(residual)

        # Calculate reserve floors (minimum absolute generation)
        coal_floor = total_demand * self.coal_reserve_floor
        gas_floor = total_demand * self.gas_reserve_floor

        if sequence == "coal_first":
            # Displace coal first, then gas
            for i, year in enumerate(years):
                remaining = residual[i]

                # Allocate to gas first (up to floor)
                gas_allocation = min(remaining, gas_floor[i])
                gas_generation[i] = gas_allocation
                remaining -= gas_allocation

                # Rest goes to coal
                coal_generation[i] = remaining

        else:  # gas_first
            # Displace gas first, then coal
            for i, year in enumerate(years):
                remaining = residual[i]

                # Allocate to coal first (up to floor)
                coal_allocation = min(remaining, coal_floor[i])
                coal_generation[i] = coal_allocation
                remaining -= coal_allocation

                # Rest goes to gas
                gas_generation[i] = remaining

        return coal_generation, gas_generation

    def calculate_displacement_timeline(
        self,
        years: np.ndarray,
        coal_generation: np.ndarray,
        gas_generation: np.ndarray,
        swb_generation: np.ndarray
    ) -> Dict[str, int]:
        """
        Calculate key displacement milestones

        Args:
            years: Array of years
            coal_generation: Coal generation array
            gas_generation: Gas generation array
            swb_generation: SWB generation array

        Returns:
            Dictionary with milestone years
        """
        milestones = {}

        # Find year when SWB > Coal
        coal_displaced_idx = np.where(swb_generation > coal_generation)[0]
        if len(coal_displaced_idx) > 0:
            milestones["swb_exceeds_coal"] = int(years[coal_displaced_idx[0]])

        # Find year when SWB > Gas
        gas_displaced_idx = np.where(swb_generation > gas_generation)[0]
        if len(gas_displaced_idx) > 0:
            milestones["swb_exceeds_gas"] = int(years[gas_displaced_idx[0]])

        # Find year when SWB > Coal + Gas
        fossil_total = coal_generation + gas_generation
        fossil_displaced_idx = np.where(swb_generation > fossil_total)[0]
        if len(fossil_displaced_idx) > 0:
            milestones["swb_exceeds_all_fossil"] = int(years[fossil_displaced_idx[0]])

        # Find year when Coal reaches 95% reduction from peak
        coal_peak = np.max(coal_generation)
        coal_95_reduction_idx = np.where(coal_generation < 0.05 * coal_peak)[0]
        if len(coal_95_reduction_idx) > 0:
            milestones["coal_95_percent_displaced"] = int(years[coal_95_reduction_idx[0]])

        # Find year when Gas reaches 95% reduction from peak
        gas_peak = np.max(gas_generation)
        gas_95_reduction_idx = np.where(gas_generation < 0.05 * gas_peak)[0]
        if len(gas_95_reduction_idx) > 0:
            milestones["gas_95_percent_displaced"] = int(years[gas_95_reduction_idx[0]])

        return milestones


if __name__ == "__main__":
    print("Displacement Analysis module for SWB")
