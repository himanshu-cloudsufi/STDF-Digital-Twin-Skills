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

        Args:
            region: Region name
            years: Array of forecast years

        Returns:
            Tuple of (years, non_swb_generation_gwh)
        """
        # Try to load historical nuclear + hydro generation
        # If not available, estimate as residual from total - fossil - renewable

        try:
            # Load total electricity generation
            total_years, total_gen = self.data_loader.get_electricity_demand(region)

            # Estimate non-SWB as constant fraction of total (conservative assumption)
            # Or use historical data if available
            non_swb_gen = np.interp(years, total_years, total_gen) * 0.15  # Assume 15% baseline

            return years, non_swb_gen
        except Exception as e:
            print(f"Warning: Could not calculate non-SWB baseline for {region}: {e}")
            # Fallback: assume zero non-SWB (SWB + coal + gas = total)
            return years, np.zeros_like(years)

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
