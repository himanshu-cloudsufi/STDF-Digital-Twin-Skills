"""
Data Loading Utilities for Light Vehicle Demand Forecasting
Loads cost and demand curves from JSON files using taxonomy mappings
Shared by two-wheeler and three-wheeler forecasting modules
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class DataLoader:
    """Handles loading and accessing light vehicle forecasting data"""

    def __init__(self, vehicle_config, data_dir: Optional[str] = None):
        """
        Initialize data loader

        Args:
            vehicle_config: VehicleConfig instance with vehicle-specific parameters
            data_dir: Path to data directory. If None, uses config's data directory.
        """
        self.vehicle_config = vehicle_config

        if data_dir is None:
            self.data_dir = str(vehicle_config.get_data_directory())
        else:
            self.data_dir = data_dir

        self.taxonomy = self._load_taxonomy()
        self.curves_data = None  # Lazy load when needed

    def _load_taxonomy(self) -> dict:
        """Load taxonomy and dataset mappings"""
        taxonomy_path = self.vehicle_config.get_taxonomy_file_path()

        if not taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")

        with open(taxonomy_path, 'r') as f:
            return json.load(f)

    def _load_curves(self) -> dict:
        """Load all curves data (lazy loading)"""
        if self.curves_data is not None:
            return self.curves_data

        # Try all possible curves file names
        curves_paths = self.vehicle_config.get_curves_file_paths()

        for curves_path in curves_paths:
            if curves_path.exists():
                with open(curves_path, 'r') as f:
                    data = json.load(f)
                    # Handle nested structure - extract the relevant section
                    # Try vehicle-specific keys
                    display_name = self.vehicle_config.get_display_name()
                    market_product = self.vehicle_config.get_product_names()['market']

                    # Try multiple possible keys
                    possible_keys = [
                        display_name,  # "Two-Wheeler" or "Three-Wheeler"
                        display_name.replace('-', ' '),  # "Two Wheeler"
                        market_product,  # "Two_Wheelers" or "Three_Wheelers"
                    ]

                    for key in possible_keys:
                        if key in data:
                            self.curves_data = data[key]
                            return self.curves_data

                    # If no specific key found, assume data is at root level
                    self.curves_data = data
                    return self.curves_data

        print(f"Warning: Curves data file not found in: {[str(p) for p in curves_paths]}")
        print("Data loader will work with taxonomy only (for structure validation)")
        return {}

    def _get_metric_name(self, entity: str, category: str, region: str) -> str:
        """
        Get metric name from taxonomy for given entity, category, and region

        Args:
            entity: Entity name (e.g., "Two_Wheelers", "EV_2_Wheelers")
            category: Category name (e.g., "cost", "demand", "installed_base")
            region: Region name

        Returns:
            Metric name from taxonomy
        """
        data_section = self.taxonomy.get("data", {})

        if entity not in data_section:
            raise ValueError(f"Entity {entity} not found in taxonomy")

        entity_data = data_section[entity]

        if category not in entity_data:
            raise ValueError(f"Category {category} not found for entity {entity}")

        category_data = entity_data[category]

        if isinstance(category_data, dict):
            if region not in category_data:
                raise ValueError(f"Region {region} not found for {entity}.{category}")
            return category_data[region]
        else:
            return category_data

    def get_cost_data(
        self,
        cost_type: str,
        region: str
    ) -> Tuple[List[int], List[float]]:
        """
        Get cost curve for a specific cost type and region

        Args:
            cost_type: Cost type (e.g., "ev_primary", "ev_secondary", "ice")
            region: Region name

        Returns:
            Tuple of (years, costs)
        """
        # Get product names from config
        products = self.vehicle_config.get_product_names()

        # Map cost type to entity and category
        if cost_type == "ev_primary":
            entity = products['ev']
            category = "cost"
        elif cost_type == "ev_secondary":
            entity = products['ev']
            category = "cost_secondary"
        elif cost_type == "ice":
            entity = products['ice']
            category = "cost"
        else:
            raise ValueError(f"Unknown cost type: {cost_type}")

        # Get metric name from taxonomy
        metric_name = self._get_metric_name(entity, category, region)

        # Load curves data
        curves = self._load_curves()

        if not curves:
            # Return dummy data for testing/structure validation
            print(f"Warning: No curve data available, returning dummy data")
            return [2020, 2021, 2022], [1000.0, 950.0, 900.0]

        # Try to find metric in curves file
        if metric_name not in curves:
            print(f"Warning: Metric {metric_name} not found in curves data, returning dummy data")
            return [2020, 2021, 2022], [1000.0, 950.0, 900.0]

        curve = curves[metric_name]

        # Extract data based on structure
        if "regions" in curve:
            region_data = curve["regions"].get(region, {})
            if not region_data:
                raise ValueError(f"No data for region {region} in metric {metric_name}")
            years = region_data.get("X", [])
            costs = region_data.get("Y", [])
        elif "X" in curve and "Y" in curve:
            years = curve["X"]
            costs = curve["Y"]
        else:
            raise ValueError(f"Unexpected data structure for {metric_name}")

        return years, costs

    def get_demand_data(
        self,
        product: str,
        region: str
    ) -> Tuple[List[int], List[float]]:
        """
        Get demand/sales curve for a product in a region

        Args:
            product: Product name (e.g., "Two_Wheelers", "EV_2_Wheelers")
            region: Region name

        Returns:
            Tuple of (years, demand_values)
        """
        # Get metric name from taxonomy
        metric_name = self._get_metric_name(product, "demand", region)

        # Load curves data
        curves = self._load_curves()

        if not curves:
            # Return dummy data for testing/structure validation
            print(f"Warning: No curve data available, returning dummy data")
            return [2020, 2021, 2022], [1000000.0, 1050000.0, 1100000.0]

        # Try to find metric in curves file
        if metric_name not in curves:
            print(f"Warning: Metric {metric_name} not found in curves data, returning dummy data")
            return [2020, 2021, 2022], [1000000.0, 1050000.0, 1100000.0]

        curve = curves[metric_name]

        # Extract data based on structure
        if "regions" in curve:
            region_data = curve["regions"].get(region, {})
            if not region_data:
                raise ValueError(f"No data for region {region} in metric {metric_name}")

            # Handle nested structure (e.g., {"standard": {"X": [...], "Y": [...]}})
            if "X" in region_data and "Y" in region_data:
                years = region_data["X"]
                demand = region_data["Y"]
            elif "standard" in region_data:
                years = region_data["standard"]["X"]
                demand = region_data["standard"]["Y"]
            else:
                raise ValueError(f"Unexpected data structure for {metric_name}")
        elif "X" in curve and "Y" in curve:
            years = curve["X"]
            demand = curve["Y"]
        else:
            raise ValueError(f"Unexpected data structure for {metric_name}")

        return years, demand

    def get_fleet_data(
        self,
        product: str,
        region: str
    ) -> Tuple[List[int], List[float]]:
        """
        Get fleet/installed base data for a product in a region

        Args:
            product: Product name (e.g., "EV_2_Wheelers", "ICE_2_Wheelers")
            region: Region name

        Returns:
            Tuple of (years, fleet_values)
        """
        # Check if entity has installed_base category for this region
        data = self.taxonomy.get("data", {})

        if product not in data:
            print(f"Info: Product {product} not found in taxonomy")
            return [], []

        if "installed_base" not in data[product]:
            print(f"Info: No installed_base data for {product}")
            return [], []

        if region not in data[product]["installed_base"]:
            print(f"Info: No installed_base data for {product} in {region}")
            return [], []

        # Get metric name from taxonomy
        metric_name = self._get_metric_name(product, "installed_base", region)

        # Load curves data
        curves = self._load_curves()

        if not curves:
            print(f"Warning: No curve data available for fleet")
            return [], []

        # Try to find metric in curves file
        if metric_name not in curves:
            print(f"Info: Metric {metric_name} not found in curves data (fleet data is optional)")
            return [], []

        curve = curves[metric_name]

        # Extract data
        if "regions" in curve:
            region_data = curve["regions"].get(region, {})
            if not region_data:
                return [], []
            years = region_data.get("X", [])
            fleet = region_data.get("Y", [])
        elif "X" in curve and "Y" in curve:
            years = curve["X"]
            fleet = curve["Y"]
        else:
            return [], []

        return years, fleet

    def get_all_regions(self) -> List[str]:
        """Get list of all available regions from vehicle config"""
        return self.vehicle_config.get_regions()

    def list_available_datasets(self) -> List[str]:
        """List all available dataset name patterns in taxonomy"""
        datasets = []
        data = self.taxonomy.get("data", {})

        for entity_name, entity_data in data.items():
            for category_name, category_data in entity_data.items():
                if category_name == "entity_type":
                    continue
                if isinstance(category_data, dict):
                    for region, dataset_prefix in category_data.items():
                        # Build full dataset name
                        dataset_name = f"{dataset_prefix}_{region}"
                        datasets.append(dataset_name)

        return sorted(datasets)


if __name__ == "__main__":
    # Test data loader
    print("Testing Light Vehicle Data Loader...")
    print("This module is designed to be imported and used with a VehicleConfig instance.")
    print("\nExample usage:")
    print("  from vehicle_config import VehicleConfig")
    print("  from common.data_loader import DataLoader")
    print("  config = VehicleConfig('two_wheeler')")
    print("  loader = DataLoader(config)")
    print("  years, costs = loader.get_cost_data('ev_primary', 'China')")
