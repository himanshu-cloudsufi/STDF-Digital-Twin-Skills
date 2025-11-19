"""
Data Loading Utilities for Three-Wheeler Demand Forecasting
Loads cost and demand curves from JSON files using taxonomy mappings
"""

import json
import os
from typing import Dict, List, Tuple, Optional


class DataLoader:
    """Handles loading and accessing three-wheeler forecasting data"""

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
        self.curves_data = None  # Lazy load when needed

    def _load_taxonomy(self) -> dict:
        """Load taxonomy and dataset mappings"""
        taxonomy_path = os.path.join(
            self.data_dir,
            "three_wheeler_taxonomy_and_datasets.json"
        )

        if not os.path.exists(taxonomy_path):
            raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")

        with open(taxonomy_path, 'r') as f:
            return json.load(f)

    def _load_curves(self) -> dict:
        """Load all curves data (lazy loading)"""
        if self.curves_data is not None:
            return self.curves_data

        # Try Three_Wheeler.json first (from curves catalog)
        curves_path = os.path.join(self.data_dir, "Three_Wheeler.json")

        if not os.path.exists(curves_path):
            # Fallback to Three_Wheelers.json
            curves_path = os.path.join(self.data_dir, "Three_Wheelers.json")

        if not os.path.exists(curves_path):
            print(f"Warning: Curves data file not found: {curves_path}")
            print("Data loader will work with taxonomy only (for structure validation)")
            return {}

        with open(curves_path, 'r') as f:
            data = json.load(f)
            # Handle nested structure - try both "Three Wheeler" (with space) and "Three_Wheelers"
            self.curves_data = data.get("Three Wheeler", data.get("Three_Wheelers", data))
            return self.curves_data

    def _get_metric_name(self, entity: str, category: str, region: str) -> str:
        """
        Get metric name from taxonomy for given entity, category, and region

        Args:
            entity: Entity name (e.g., "EV_3_Wheelers", "ICE_3_Wheelers", "Three_Wheelers")
            category: Category name (e.g., "cost", "demand", "installed_base")
            region: Region name (e.g., "China", "Europe", "Rest_of_World")

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
            region: Region name (e.g., "China", "Europe", "Rest_of_World")

        Returns:
            Tuple of (years, costs)
        """
        # Map cost type to entity and category
        if cost_type == "ev_primary":
            entity = "EV_3_Wheelers"
            category = "cost"
        elif cost_type == "ev_secondary":
            entity = "EV_3_Wheelers"
            category = "cost_secondary"
        elif cost_type == "ice":
            entity = "ICE_3_Wheelers"
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
            product: Product name (e.g., "Three_Wheelers", "EV_3_Wheelers", "ICE_3_Wheelers")
            region: Region name

        Returns:
            Tuple of (years, demand_values)
        """
        # Product is the entity name in the new structure
        entity = product
        category = "demand"

        # Get metric name from taxonomy
        metric_name = self._get_metric_name(entity, category, region)

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
            product: Product name (e.g., "EV_3_Wheelers", "ICE_3_Wheelers")
            region: Region name

        Returns:
            Tuple of (years, fleet_values)
        """
        # Product is the entity name in the new structure
        entity = product
        category = "installed_base"

        # Check if entity and category exist in taxonomy
        data_section = self.taxonomy.get("data", {})
        if entity not in data_section or category not in data_section[entity]:
            print(f"Info: No installed_base data for {entity} in taxonomy (fleet data is optional)")
            return [], []

        # Get metric name from taxonomy
        try:
            metric_name = self._get_metric_name(entity, category, region)
        except ValueError:
            print(f"Info: Region {region} not found for {entity}.{category} (fleet data is optional)")
            return [], []

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
        """Get list of all available regions (excluding Global)"""
        # Extract from taxonomy data section
        regions = set()
        data_section = self.taxonomy.get("data", {})

        # Look through all entities for region keys
        for entity_name, entity_data in data_section.items():
            for category_name, category_data in entity_data.items():
                if category_name == "entity_type":
                    continue
                if isinstance(category_data, dict):
                    for region in category_data.keys():
                        if region != "Global" and not isinstance(category_data[region], dict):
                            regions.add(region)

        return sorted(list(regions))

    def get_market_name(self) -> str:
        """Get the market name from taxonomy"""
        return self.taxonomy.get("market", "Three_Wheelers")


if __name__ == "__main__":
    # Test data loader
    print("Testing Three-Wheeler Data Loader...")

    try:
        loader = DataLoader()
        print(f"\n✓ Data loader initialized")
        print(f"Market: {loader.get_market_name()}")
        print(f"Available regions: {loader.get_all_regions()}")

        # Test loading cost data
        try:
            years, costs = loader.get_cost_data("ev_primary", "China")
            print(f"\n✓ EV Primary Cost Data for China:")
            print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
            print(f"  Costs: {costs[:3] if len(costs) > 0 else 'No data'}")
        except Exception as e:
            print(f"\n⚠ EV cost data: {e}")

        # Test loading demand data
        try:
            years, demand = loader.get_demand_data("Three_Wheelers", "China")
            print(f"\n✓ Market Demand Data for China:")
            print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
            print(f"  Demand: {demand[:3] if len(demand) > 0 else 'No data'}")
        except Exception as e:
            print(f"\n⚠ Market demand data: {e}")

        # Test loading EV demand data
        try:
            years, demand = loader.get_demand_data("EV_3_Wheelers", "China")
            print(f"\n✓ EV Demand Data for China:")
            print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
            print(f"  Demand: {demand[:3] if len(demand) > 0 else 'No data'}")
        except Exception as e:
            print(f"\n⚠ EV demand data: {e}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
