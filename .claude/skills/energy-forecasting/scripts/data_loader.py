"""
Data Loading Utilities for Energy Forecasting (SWB)
Loads cost, capacity, generation, and CF data from multiple JSON entity files
"""

import json
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
from exceptions import DataNotFoundError, DataValidationError


class DataLoader:
    """Handles loading and accessing SWB forecasting data"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader

        Args:
            data_dir: Path to data directory. If None, uses skill's data dir.
        """
        if data_dir is None:
            # Default to skill's data directory (parent of scripts dir)
            scripts_dir = os.path.dirname(os.path.abspath(__file__))
            skill_dir = os.path.dirname(scripts_dir)
            data_dir = os.path.join(skill_dir, "data")

        self.data_dir = data_dir
        self.taxonomy = self._load_taxonomy()
        self.curves_data = self._load_all_curves()

    def _load_taxonomy(self) -> dict:
        """Load SWB taxonomy and dataset mappings"""
        taxonomy_path = os.path.join(
            self.data_dir,
            "swb_taxonomy_and_datasets.json"
        )
        with open(taxonomy_path, 'r') as f:
            return json.load(f)

    def _load_all_curves(self) -> dict:
        """
        Load all curves data from multiple entity files

        Returns:
            Combined dictionary with all datasets from all entity files
        """
        entity_files = [
            "Energy_Generation.json",
            "Energy_Storage.json",
            "Electricity.json"
        ]

        combined_data = {}

        for entity_file in entity_files:
            file_path = os.path.join(self.data_dir, entity_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Extract the entity data (skip the top-level entity name key)
                    for entity_name, entity_datasets in data.items():
                        if isinstance(entity_datasets, dict):
                            combined_data.update(entity_datasets)

        return combined_data

    def get_lcoe_data(self, technology: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get LCOE (Levelized Cost of Energy) curve for a technology

        Args:
            technology: Technology name (e.g., "Solar_PV", "Coal_Power")
            region: Region name (e.g., "China", "USA", "Europe", "Rest_of_World")

        Returns:
            Tuple of (years, lcoe_values) in $/MWh
        """
        # Get dataset name from taxonomy
        if technology not in self.taxonomy["products"]:
            raise ValueError(f"Technology {technology} not found in taxonomy")

        lcoe_mapping = self.taxonomy["products"][technology].get("lcoe", {})

        if isinstance(lcoe_mapping, dict):
            dataset_name = lcoe_mapping.get(region)
        else:
            dataset_name = lcoe_mapping

        if not dataset_name:
            raise ValueError(f"No LCOE dataset for {technology} in region {region}")

        years, lcoe_values = self._get_curve_data(dataset_name, region)

        # Convert units to $/MWh if needed
        # Check metadata for units field
        if dataset_name in self.curves_data:
            metadata = self.curves_data[dataset_name].get("metadata", {})
            units = metadata.get("units", "").upper()

            # Convert $/kWh to $/MWh (multiply by 1000)
            # Note: Some datasets incorrectly label LCOE as "$/kW" when they mean "$/kWh"
            if units in ["$/KWH", "USD/KWH", "$/KILOWATTHOUR", "$/KW", "USD/KW"]:
                lcoe_values = [val * 1000.0 for val in lcoe_values]

        return years, lcoe_values

    def get_capacity_data(self, technology: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get installed capacity curve for a technology

        Args:
            technology: Technology name
            region: Region name

        Returns:
            Tuple of (years, capacity_values) in GW
        """
        if technology not in self.taxonomy["products"]:
            raise ValueError(f"Technology {technology} not found in taxonomy")

        capacity_mapping = self.taxonomy["products"][technology].get("capacity", {})

        if isinstance(capacity_mapping, dict):
            dataset_name = capacity_mapping.get(region)
        else:
            dataset_name = capacity_mapping

        if not dataset_name:
            raise ValueError(f"No capacity dataset for {technology} in region {region}")

        years, capacity_values = self._get_curve_data(dataset_name, region)

        # Convert units to GW if needed
        # Check metadata for units field
        if dataset_name in self.curves_data:
            metadata = self.curves_data[dataset_name].get("metadata", {})
            units = metadata.get("units", "").upper()

            # Convert MW to GW
            if units == "MW":
                capacity_values = [val / 1000.0 for val in capacity_values]

        return years, capacity_values

    def get_generation_data(self, technology: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get electricity generation curve for a technology

        Args:
            technology: Technology name
            region: Region name

        Returns:
            Tuple of (years, generation_values) in GWh
        """
        if technology not in self.taxonomy["products"]:
            raise ValueError(f"Technology {technology} not found in taxonomy")

        generation_mapping = self.taxonomy["products"][technology].get("generation", {})

        if isinstance(generation_mapping, dict):
            dataset_name = generation_mapping.get(region)
        else:
            dataset_name = generation_mapping

        if not dataset_name:
            raise ValueError(f"No generation dataset for {technology} in region {region}")

        return self._get_curve_data(dataset_name, region)

    def get_capacity_factor_data(self, technology: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get capacity factor curve for a technology

        Args:
            technology: Technology name
            region: Region name

        Returns:
            Tuple of (years, cf_values) as decimals (0.0 to 1.0)
        """
        if technology not in self.taxonomy["products"]:
            raise ValueError(f"Technology {technology} not found in taxonomy")

        cf_mapping = self.taxonomy["products"][technology].get("capacity_factor", {})

        if isinstance(cf_mapping, dict):
            dataset_name = cf_mapping.get(region)
        else:
            dataset_name = cf_mapping

        if not dataset_name:
            # Return None for fallback handling
            return None, None

        return self._get_curve_data(dataset_name, region)

    def get_electricity_demand(self, region: str) -> Tuple[List[int], List[float]]:
        """
        Get total electricity demand/consumption

        Args:
            region: Region name

        Returns:
            Tuple of (years, demand_values) in GWh
        """
        electricity_demand_mapping = self.taxonomy.get("electricity_system", {}).get("demand", {})

        if isinstance(electricity_demand_mapping, dict):
            dataset_name = electricity_demand_mapping.get(region)
        else:
            dataset_name = electricity_demand_mapping

        if not dataset_name:
            raise ValueError(f"No electricity demand dataset for region {region}")

        years, demand_values = self._get_curve_data(dataset_name, region)

        # Convert units to GWh if needed
        # Check metadata for units field
        if dataset_name in self.curves_data:
            metadata = self.curves_data[dataset_name].get("metadata", {})
            units = metadata.get("units", "").upper()

            # Convert TWh to GWh (multiply by 1000)
            if units == "TWH":
                demand_values = [val * 1000.0 for val in demand_values]

        return years, demand_values

    def get_battery_cost_data(self, region: str, duration: int = 4) -> Tuple[List[int], List[float]]:
        """
        Load battery cost data by duration and region

        Args:
            region: Region name
            duration: Battery duration in hours (2, 4, or 8)

        Returns:
            Tuple of (years, costs) in $/kWh
        """
        # Map duration to dataset suffix
        dataset_map = {
            2: "Battery_Energy_Storage_System_(2-hour_Turnkey)_Cost",
            4: "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost",
            8: "Battery_Energy_Storage_System_(8-hour_Turnkey)_Cost"
        }

        if duration not in dataset_map:
            raise ValueError(f"Invalid duration: {duration}. Must be 2, 4, or 8.")

        dataset_name = dataset_map[duration]

        # Load with fallback hierarchy: Regional → Global → Error
        try:
            years, costs = self._get_curve_data(dataset_name, region, fallback_to_global=False)
        except (ValueError, KeyError):
            if region != "Global":
                try:
                    years, costs = self._get_curve_data(dataset_name, "Global")
                    print(f"  Note: Using Global battery cost data for {region}")
                except (ValueError, KeyError):
                    raise DataNotFoundError(f"Battery cost data not found for {region} or Global")
            else:
                raise DataNotFoundError(f"Battery cost data not found for {region}")

        # Validate cost range ($/kWh should be 50-500)
        costs_array = np.array(costs)
        if np.any(costs_array < 10) or np.any(costs_array > 1000):
            raise DataValidationError(f"Battery costs out of reasonable range: {costs_array}")

        return years, costs

    def get_coal_emissions(self, region: str) -> Tuple[List[int], List[float]]:
        """
        Load actual CO2 emissions from Coal.json

        Args:
            region: Region name

        Returns:
            Tuple of (years, emissions) in tonnes CO2
        """
        try:
            with open(os.path.join(self.data_dir, "Coal.json")) as f:
                data = json.load(f)

            coal_data = data["Coal"]["Annual_CO2_Emission"]["regions"].get(region)
            if not coal_data:
                raise DataNotFoundError(f"Coal emissions not found for {region}")

            years = coal_data["X"]
            emissions = coal_data["Y"]  # In tonnes CO2

            return years, emissions
        except FileNotFoundError:
            raise DataNotFoundError("Coal.json file not found")
        except KeyError as e:
            raise DataNotFoundError(f"Could not load coal emissions: {e}")

    def _get_curve_data(self, dataset_name: str, region: str, fallback_to_global: bool = True) -> Tuple[List[int], List[float]]:
        """
        Helper to extract X, Y data from a dataset

        Args:
            dataset_name: Name of the dataset in curves_data
            region: Region name
            fallback_to_global: If True, use Global data if region data not found

        Returns:
            Tuple of (years, values)
        """
        if dataset_name not in self.curves_data:
            raise ValueError(f"Dataset {dataset_name} not found in curves data")

        curve = self.curves_data[dataset_name]
        region_data = curve.get("regions", {}).get(region, {})

        # Fallback to Global if region not found and fallback enabled
        if not region_data and fallback_to_global and region != "Global":
            region_data = curve.get("regions", {}).get("Global", {})
            if region_data:
                print(f"  Note: Using Global data for {dataset_name} (region-specific data for {region} not available)")

        if not region_data:
            raise ValueError(f"No data for region {region} in dataset {dataset_name}")

        # Handle nested structure (e.g., {"standard": {"X": [...], "Y": [...]}, "Prosperity": {...}})
        if "X" in region_data and "Y" in region_data:
            years = region_data["X"]
            values = region_data["Y"]
        elif "standard" in region_data:
            years = region_data["standard"]["X"]
            values = region_data["standard"]["Y"]
        else:
            raise ValueError(f"Unexpected data structure for {dataset_name} in region {region}")

        return years, values

    def get_all_regions(self) -> List[str]:
        """Get list of all available regions (excluding Global)"""
        # Standard regions for SWB forecasting
        return ["China", "USA", "Europe", "Germany", "Rest_of_World"]

    def get_entity_type(self, technology: str) -> str:
        """
        Get entity type for a technology

        Args:
            technology: Technology name

        Returns:
            Entity type: "disruptor", "incumbent", "chimera", or "market"
        """
        if technology not in self.taxonomy["products"]:
            return "unknown"

        return self.taxonomy["products"][technology].get("entity_type", "unknown")

    def get_swb_components(self) -> List[str]:
        """Get list of SWB component technologies"""
        swb_components = []
        for tech, info in self.taxonomy["products"].items():
            if info.get("entity_type") == "disruptor":
                swb_components.append(tech)
        return swb_components

    def get_incumbent_technologies(self) -> List[str]:
        """Get list of incumbent (fossil fuel) technologies"""
        incumbents = []
        for tech, info in self.taxonomy["products"].items():
            if info.get("entity_type") == "incumbent":
                incumbents.append(tech)
        return incumbents


if __name__ == "__main__":
    # Test data loader
    loader = DataLoader()

    print("Testing SWB Data Loader...")
    print(f"Available regions: {loader.get_all_regions()}")
    print(f"SWB components: {loader.get_swb_components()}")
    print(f"Incumbents: {loader.get_incumbent_technologies()}")

    # Test loading LCOE data
    try:
        years, lcoe = loader.get_lcoe_data("Solar_PV", "China")
        print(f"\nSolar PV LCOE for China:")
        print(f"Years: {years[:5]}...")
        print(f"LCOE: {lcoe[:5]}...")
    except Exception as e:
        print(f"Error loading Solar LCOE: {e}")

    # Test loading capacity data
    try:
        years, capacity = loader.get_capacity_data("Onshore_Wind", "China")
        print(f"\nOnshore Wind Capacity for China:")
        print(f"Years: {years[:5]}...")
        print(f"Capacity (GW): {capacity[:5]}...")
    except Exception as e:
        print(f"Error loading Wind capacity: {e}")

    # Test loading generation data
    try:
        years, generation = loader.get_generation_data("Coal_Power", "China")
        print(f"\nCoal Power Generation for China:")
        print(f"Years: {years[:5]}...")
        print(f"Generation (GWh): {generation[:5]}...")
    except Exception as e:
        print(f"Error loading Coal generation: {e}")
