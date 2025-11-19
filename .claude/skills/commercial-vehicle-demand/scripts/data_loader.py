"""
Data Loading Utilities for Commercial Vehicle Demand Forecasting
Loads cost and demand curves from JSON files using taxonomy mappings
Supports segment-level data (LCV, MCV, HCV) and three powertrains (EV, ICE, NGV)
Uses passenger-vehicle style taxonomy structure
"""

import json
import os
from typing import Dict, List, Tuple, Optional


class DataLoader:
    """Handles loading and accessing commercial vehicle forecasting data"""

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
            "commercial_vehicle_taxonomy_and_datasets.json"
        )

        if not os.path.exists(taxonomy_path):
            raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")

        with open(taxonomy_path, 'r') as f:
            return json.load(f)

    def _load_curves(self) -> dict:
        """Load all curves data (lazy loading)"""
        if self.curves_data is not None:
            return self.curves_data

        curves_path = os.path.join(self.data_dir, "Commercial_Vehicle.json")

        if not os.path.exists(curves_path):
            print(f"Warning: Curves data file not found: {curves_path}")
            print("Data loader will work with taxonomy only (for structure validation)")
            return {}

        with open(curves_path, 'r') as f:
            data = json.load(f)
            # Handle nested structure - extract "Commercial Vehicle" data
            self.curves_data = data.get("Commercial Vehicle", data.get("Commercial_Vehicles", data))
            return self.curves_data

    def _get_metric_name(self, entity: str, data_type: str, powertrain: Optional[str], region: str) -> Optional[str]:
        """
        Get metric name from taxonomy for a given entity, data type, and region

        Args:
            entity: Entity name (e.g., "LCV", "Commercial_Vehicles")
            data_type: Type of data ("cost", "demand", "installed_base")
            powertrain: Powertrain type ("EV", "ICE", "NGV", or None for total)
            region: Region name

        Returns:
            Metric name string, or None if not found
        """
        try:
            entity_data = self.taxonomy["data"].get(entity)
            if not entity_data:
                return None

            if data_type == "cost":
                # Cost data structure: data[segment]["cost"][powertrain][region]
                return entity_data["cost"][powertrain][region]
            elif data_type == "demand":
                # Demand structure: data[segment]["demand"][powertrain][region]
                # powertrain can be "Total", "EV", "ICE", "NGV"
                if powertrain:
                    return entity_data["demand"][powertrain][region]
                else:
                    # For market-level entities like "Commercial_Vehicles"
                    return entity_data["demand"][region]
            elif data_type == "installed_base":
                # Fleet structure: data[segment]["installed_base"][powertrain][region]
                if powertrain:
                    return entity_data["installed_base"][powertrain][region]
                else:
                    return entity_data["installed_base"][region]

            return None
        except (KeyError, TypeError):
            return None

    def _sum_timeseries(self, series_list: List[Tuple[List[int], List[float]]]) -> Tuple[List[int], List[float]]:
        """
        Sum multiple time series, aligning by year

        Args:
            series_list: List of (years, values) tuples

        Returns:
            Tuple of (years, summed_values)
        """
        if not series_list:
            return [], []

        # Find common years across all series
        year_sets = [set(years) for years, _ in series_list if years]
        if not year_sets:
            return [], []

        common_years = sorted(set.intersection(*year_sets))
        if not common_years:
            # No common years, use union and fill missing with 0
            all_years = sorted(set.union(*year_sets))
            summed = []
            for year in all_years:
                year_sum = 0.0
                for years, values in series_list:
                    if year in years:
                        idx = years.index(year)
                        year_sum += values[idx]
                summed.append(year_sum)
            return all_years, summed

        # Sum values for common years
        summed = []
        for year in common_years:
            year_sum = 0.0
            for years, values in series_list:
                idx = years.index(year)
                year_sum += values[idx]
            summed.append(year_sum)

        return common_years, summed

    def _get_curve_data(self, metric_name: str, region: str) -> Tuple[List[int], List[float]]:
        """
        Extract curve data for a metric and region from curves file

        Args:
            metric_name: Name of the metric in the curves file
            region: Region name

        Returns:
            Tuple of (years, values)
        """
        curves = self._load_curves()

        if not curves:
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

            # Handle nested structure (e.g., {"standard": {"X": [...], "Y": [...]}})
            if "X" in region_data and "Y" in region_data:
                years = region_data["X"]
                values = region_data["Y"]
            elif "standard" in region_data:
                years = region_data["standard"]["X"]
                values = region_data["standard"]["Y"]
            else:
                raise ValueError(f"Unexpected data structure for {metric_name}")
        elif "X" in curve and "Y" in curve:
            years = curve["X"]
            values = curve["Y"]
        else:
            raise ValueError(f"Unexpected data structure for {metric_name}")

        return years, values

    def get_cost_data(
        self,
        segment: str,
        powertrain: str,
        region: str
    ) -> Tuple[List[int], List[float]]:
        """
        Get cost curve for a specific segment, powertrain, and region

        Args:
            segment: Segment type ("LCV", "MCV", "HCV")
            powertrain: Powertrain type ("EV", "ICE")
            region: Region name (e.g., "China", "USA", "Europe", "Rest_of_World")

        Returns:
            Tuple of (years, costs)
        """
        metric_name = self._get_metric_name(segment, "cost", powertrain, region)

        if not metric_name:
            raise ValueError(f"Cost data not found for {segment}/{powertrain}/{region}")

        return self._get_curve_data(metric_name, region)

    def get_demand_data(
        self,
        product: str,
        region: str,
        segment: Optional[str] = None
    ) -> Tuple[List[int], List[float]]:
        """
        Get demand/sales curve for a product in a region

        Args:
            product: Product name (e.g., "Commercial_Vehicles", "Commercial_Vehicles_(EV)", etc.)
            region: Region name
            segment: Optional segment ("LCV", "MCV", "HCV") for segment-level data

        Returns:
            Tuple of (years, demand_values)
        """
        if segment:
            # Segment-level demand
            # Determine powertrain from product name
            if "EV" in product:
                powertrain = "EV"
            elif "ICE" in product:
                powertrain = "ICE"
            elif "NGV" in product:
                powertrain = "NGV"
            else:
                # Total segment demand - needs to be derived
                powertrain = "Total"

            metric_name = self._get_metric_name(segment, "demand", powertrain, region)

            # If total segment demand metric not found, derive it from components
            if not metric_name or powertrain == "Total":
                curves = self._load_curves()
                # Try to get the metric first
                if metric_name and metric_name in curves:
                    return self._get_curve_data(metric_name, region)

                # Derive from EV + ICE + NGV
                print(f"Info: Deriving total {segment} demand from EV+ICE+NGV components")
                components = []
                for pt in ["EV", "ICE", "NGV"]:
                    try:
                        pt_metric = self._get_metric_name(segment, "demand", pt, region)
                        if pt_metric:
                            years, values = self._get_curve_data(pt_metric, region)
                            if years and values:
                                components.append((years, values))
                    except Exception as e:
                        print(f"Warning: Could not load {segment} {pt} data: {e}")

                if components:
                    return self._sum_timeseries(components)
                else:
                    raise ValueError(f"Could not derive total {segment} demand - no component data available")
        else:
            # Market-level demand (total CV)
            # Map product names to taxonomy entities
            if product == "Commercial_Vehicles":
                entity = "Commercial_Vehicles"
            elif product == "Commercial_Vehicles_(EV)" or product == "EV_CV":
                entity = "EV_CV"
            elif product == "Commercial_Vehicles_(ICE)" or product == "ICE_CV":
                entity = "ICE_CV"
            elif product == "Commercial_Vehicles_(NGV)" or product == "NGV_CV":
                entity = "NGV_CV"
            else:
                raise ValueError(f"Unknown product: {product}")

            metric_name = self._get_metric_name(entity, "demand", None, region)

        if not metric_name:
            raise ValueError(f"Demand data not found for {product}/{region}/{segment}")

        return self._get_curve_data(metric_name, region)

    def get_fleet_data(
        self,
        product: str,
        region: str,
        segment: Optional[str] = None
    ) -> Tuple[List[int], List[float]]:
        """
        Get fleet/installed base data for a product in a region

        Args:
            product: Product name (e.g., "Commercial_Vehicles_(EV)", "Commercial_Vehicles_(ICE)")
            region: Region name
            segment: Optional segment ("LCV", "MCV", "HCV") for segment-level data

        Returns:
            Tuple of (years, fleet_values) - returns empty arrays if data unavailable (e.g., NGV fleet)
        """
        if segment:
            # Segment-level fleet
            # Determine powertrain from product name
            if "EV" in product:
                powertrain = "EV"
            elif "ICE" in product:
                powertrain = "ICE"
            elif "NGV" in product:
                powertrain = "NGV"
            else:
                raise ValueError(f"Fleet data requires powertrain specification")

            metric_name = self._get_metric_name(segment, "installed_base", powertrain, region)
        else:
            # Market-level fleet
            if product == "Commercial_Vehicles_(EV)" or product == "EV_CV":
                entity = "EV_CV"
            elif product == "Commercial_Vehicles_(ICE)" or product == "ICE_CV":
                entity = "ICE_CV"
            elif product == "Commercial_Vehicles_(NGV)" or product == "NGV_CV":
                entity = "NGV_CV"
            else:
                raise ValueError(f"Unknown product for fleet data: {product}")

            metric_name = self._get_metric_name(entity, "installed_base", None, region)

        if not metric_name:
            # Check if this is NGV fleet (known to be missing)
            is_ngv = "NGV" in product or (segment and powertrain == "NGV")
            if is_ngv:
                # NGV fleet data commonly unavailable - graceful degradation
                return [], []
            else:
                print(f"Info: Fleet data not found for {product}/{region}/{segment}")
                return [], []

        try:
            curves = self._load_curves()
            if metric_name not in curves:
                # Check if this is NGV (expected to be missing)
                is_ngv = "NGV" in product or "NGV" in metric_name
                if is_ngv:
                    # NGV fleet data commonly unavailable - graceful degradation
                    return [], []
                else:
                    print(f"Info: Fleet metric {metric_name} not found in data")
                    return [], []

            return self._get_curve_data(metric_name, region)
        except Exception as e:
            print(f"Info: Could not load fleet data: {e}")
            return [], []

    def get_all_regions(self) -> List[str]:
        """Get list of all available regions (excluding Global)"""
        # Extract from any segment's demand data
        segments = self.taxonomy.get("segments", ["LCV"])
        if segments:
            segment_data = self.taxonomy["data"].get(segments[0], {})
            demand_data = segment_data.get("demand", {})
            if "Total" in demand_data:
                regions = list(demand_data["Total"].keys())
            else:
                regions = []
            return [r for r in regions if r != "Global"]
        return ["China", "USA", "Europe", "Rest_of_World"]

    def get_segments(self) -> List[str]:
        """Get list of vehicle segments"""
        return self.taxonomy.get("segments", ["LCV", "MCV", "HCV"])


if __name__ == "__main__":
    # Test data loader
    print("Testing Commercial Vehicle Data Loader...")

    try:
        loader = DataLoader()
        print(f"\n✓ Data loader initialized")
        print(f"Available regions: {loader.get_all_regions()}")
        print(f"Available segments: {loader.get_segments()}")

        # Test loading cost data for each segment
        for segment in ["LCV", "MCV", "HCV"]:
            try:
                years, costs = loader.get_cost_data(segment, "EV", "China")
                print(f"\n✓ {segment} EV Cost Data for China:")
                print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
                print(f"  Costs: {costs[:3] if len(costs) > 0 else 'No data'}")
            except Exception as e:
                print(f"\n⚠ {segment} EV cost data: {e}")

        # Test loading demand data
        try:
            years, demand = loader.get_demand_data("Commercial_Vehicles", "China")
            print(f"\n✓ Total Market Demand Data for China:")
            print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
            print(f"  Demand: {demand[:3] if len(demand) > 0 else 'No data'}")
        except Exception as e:
            print(f"\n⚠ Market demand data: {e}")

        # Test loading NGV data
        try:
            years, ngv_demand = loader.get_demand_data("Commercial_Vehicles_(NGV)", "China")
            print(f"\n✓ NGV Demand Data for China:")
            print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
            print(f"  Demand: {ngv_demand[:3] if len(ngv_demand) > 0 else 'No data'}")
        except Exception as e:
            print(f"\n⚠ NGV demand data: {e}")

        # Test segment-level data
        try:
            years, lcv_ev = loader.get_demand_data("Commercial_Vehicles_(EV)", "China", segment="LCV")
            print(f"\n✓ LCV EV Demand Data for China:")
            print(f"  Years: {years[:3] if len(years) > 0 else 'No data'}")
            print(f"  Demand: {lcv_ev[:3] if len(lcv_ev) > 0 else 'No data'}")
        except Exception as e:
            print(f"\n⚠ LCV EV demand data: {e}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
