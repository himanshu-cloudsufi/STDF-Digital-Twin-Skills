"""
Data Loading Utilities for Demand Forecasting
Loads cost and demand curves from JSON files in the skill's data directory
"""

import json
import os
from typing import Dict, List, Tuple, Optional


class DataLoader:
    """Handles loading and accessing forecasting data"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader

        Args:
            data_dir: Path to data directory. If None, uses skill's data dir.
        """
        if data_dir is None:
            # Default to skill's data directory
            skill_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(skill_dir, "data")

        self.data_dir = data_dir
        self.taxonomy = self._load_taxonomy()
        self.curves_data = self._load_curves()

    def _load_taxonomy(self) -> dict:
        """Load taxonomy and dataset mappings"""
        taxonomy_path = os.path.join(
            self.data_dir,
            "passenger_vehicles_taxonomy_and_datasets.json"
        )
        with open(taxonomy_path, 'r') as f:
            return json.load(f)

    def _load_curves(self) -> dict:
        """Load all curves data"""
        curves_path = os.path.join(self.data_dir, "Passenger_Cars.json")
        with open(curves_path, 'r') as f:
            data = json.load(f)
            return data.get("Passenger Cars", data)

    def get_cost_data(self, product: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get cost curve for a product in a region

        Args:
            product: Product name (e.g., "EV_Cars", "ICE_Cars")
            region: Region name (e.g., "China", "USA", "Europe", "Rest_of_World")

        Returns:
            Tuple of (years, costs)
        """
        # Get dataset name from taxonomy
        dataset_name = self.taxonomy["data"][product]["cost"][region]

        # Find the curve in the data
        if dataset_name not in self.curves_data:
            raise ValueError(f"Dataset {dataset_name} not found in curves data")

        curve = self.curves_data[dataset_name]
        region_data = curve["regions"].get(region, {})

        if not region_data:
            raise ValueError(f"No data for region {region} in dataset {dataset_name}")

        years = region_data["X"]
        costs = region_data["Y"]

        return years, costs

    def get_demand_data(self, product: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Get demand/sales curve for a product in a region

        Args:
            product: Product name (e.g., "Passenger_Vehicles", "BEV_Cars", "PHEV_Cars", "ICE_Cars")
            region: Region name

        Returns:
            Tuple of (years, demand_values)
        """
        # Get dataset name from taxonomy
        demand_mapping = self.taxonomy["data"][product]["demand"]

        if isinstance(demand_mapping, dict):
            dataset_name = demand_mapping[region]
        else:
            dataset_name = demand_mapping

        # Find the curve in the data
        if dataset_name not in self.curves_data:
            raise ValueError(f"Dataset {dataset_name} not found in curves data")

        curve = self.curves_data[dataset_name]
        region_data = curve["regions"].get(region, {})

        if not region_data:
            raise ValueError(f"No data for region {region} in dataset {dataset_name}")

        # Handle nested structure (e.g., {"standard": {"X": [...], "Y": [...]}, "TaaSAdj": {...}})
        if "X" in region_data and "Y" in region_data:
            years = region_data["X"]
            demand = region_data["Y"]
        elif "standard" in region_data:
            years = region_data["standard"]["X"]
            demand = region_data["standard"]["Y"]
        else:
            raise ValueError(f"Unexpected data structure for {dataset_name} in region {region}")

        return years, demand

    def get_all_regions(self) -> List[str]:
        """Get list of all available regions (excluding Global)"""
        # Extract from taxonomy
        example_product = list(self.taxonomy["data"].keys())[0]
        regions = list(self.taxonomy["data"][example_product].get("demand", {}).keys())

        # Remove Global if present
        return [r for r in regions if r != "Global"]

    def get_entity_type(self, product: str) -> str:
        """
        Get entity type for a product

        Args:
            product: Product name

        Returns:
            Entity type: "disruptor", "incumbent", "chimera", or "market"
        """
        return self.taxonomy["data"][product].get("entity_type", "unknown")


if __name__ == "__main__":
    # Test data loader
    loader = DataLoader()

    print("Testing Data Loader...")
    print(f"Available regions: {loader.get_all_regions()}")

    # Test loading cost data
    try:
        years, costs = loader.get_cost_data("EV_Cars", "China")
        print(f"\nEV Cost Data for China:")
        print(f"Years: {years}")
        print(f"Costs: {costs}")
    except Exception as e:
        print(f"Error loading EV cost data: {e}")

    # Test loading demand data
    try:
        years, demand = loader.get_demand_data("Passenger_Vehicles", "China")
        print(f"\nMarket Demand Data for China:")
        print(f"Years: {years[:5]}...")
        print(f"Demand: {demand[:5]}...")
    except Exception as e:
        print(f"Error loading market demand data: {e}")
