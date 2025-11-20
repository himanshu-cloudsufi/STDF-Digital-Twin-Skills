"""
Data Loader for Datacenter UPS Battery Transition Forecasting
Uses taxonomy-based approach for all data access
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List


class DatacenterUPSDataLoader:
    """Loads datacenter UPS battery data using taxonomy-based approach"""

    def __init__(self, base_data_path: Optional[Path] = None):
        """
        Initialize data loader with taxonomy

        Args:
            base_data_path: Path to data directory (defaults to skill's local data/ folder)
        """
        if base_data_path is None:
            skill_dir = Path(__file__).parent.parent
            self.base_data_path = skill_dir / 'data'
        else:
            self.base_data_path = Path(base_data_path)

        # Load taxonomy
        self.taxonomy = self._load_taxonomy()

        # Extract configuration from taxonomy
        self.regions = self.taxonomy.get('metadata', {}).get('regions',
                                         ['China', 'USA', 'Europe', 'Rest_of_World', 'Global'])
        self.entities = list(self.taxonomy.get('data', {}).keys())

        # Cache for loaded data files
        self._data_cache = {}

    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load taxonomy and dataset mappings"""
        taxonomy_path = self.base_data_path / 'datacenter_ups_taxonomy_and_datasets.json'
        try:
            with open(taxonomy_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in taxonomy file: {e}")

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load and cache JSON data file"""
        if filename in self._data_cache:
            return self._data_cache[filename]

        filepath = self.base_data_path / filename
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self._data_cache[filename] = data
                return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filepath}: {e}")

    def get_dataset_name(self, entity: str, category: str, region: str,
                        subcategory: Optional[str] = None) -> Optional[str]:
        """
        Get dataset name from taxonomy

        Args:
            entity: Entity name (e.g., 'VRLA', 'Li_ion', 'Datacenter_UPS')
            category: Category type (e.g., 'demand', 'cost', 'installed_base')
            region: Region name (e.g., 'China', 'Global')
            subcategory: Optional subcategory (e.g., '4h_turnkey' for cost)

        Returns:
            Dataset name or None if not found
        """
        data = self.taxonomy.get('data', {})

        if entity not in data:
            return None

        entity_data = data[entity]

        if category not in entity_data:
            return None

        category_data = entity_data[category]

        # Handle nested subcategories
        if subcategory and isinstance(category_data, dict):
            if subcategory in category_data:
                category_data = category_data[subcategory]
            else:
                return None

        # Get region-specific dataset
        if isinstance(category_data, dict) and region in category_data:
            return category_data[region]
        elif isinstance(category_data, str):
            # Single dataset for all regions
            return category_data

        return None

    def _extract_time_series(self, data_dict: Dict, metric_name: str,
                            region: Optional[str] = None) -> pd.Series:
        """
        Extract time series from data structure

        Args:
            data_dict: Dictionary containing the metric data
            metric_name: Name of the metric to extract
            region: Specific region to extract (if None, returns first available)

        Returns:
            Pandas Series with years as index
        """
        if metric_name not in data_dict:
            return pd.Series()

        metric_data = data_dict[metric_name]

        # Handle regional data
        if 'regions' in metric_data:
            regions_data = metric_data['regions']
            if region and region in regions_data:
                region_data = regions_data[region]
            else:
                # Return first available region if not specified
                region_data = next(iter(regions_data.values())) if regions_data else {}

            if 'X' in region_data and 'Y' in region_data:
                return pd.Series(region_data['Y'], index=region_data['X'], name=metric_name)

        # Handle direct X/Y format
        elif 'X' in metric_data and 'Y' in metric_data:
            return pd.Series(metric_data['Y'], index=metric_data['X'], name=metric_name)

        return pd.Series()

    def load_data(self, entity: str, category: str,
                  subcategory: Optional[str] = None,
                  regions: Optional[List[str]] = None) -> Dict[str, pd.Series]:
        """
        Load data for given entity and category using taxonomy

        Args:
            entity: Entity name from taxonomy
            category: Category type from taxonomy
            subcategory: Optional subcategory
            regions: List of regions to load (default: all)

        Returns:
            Dictionary of region -> pandas Series
        """
        if regions is None:
            regions = self.regions

        result = {}

        # Get base dataset name from first available region
        base_dataset_name = None
        for region in regions:
            dataset_name = self.get_dataset_name(entity, category, region, subcategory)
            if dataset_name:
                # Remove region suffix if present
                for r in self.regions:
                    if dataset_name.endswith(f'_{r}'):
                        base_dataset_name = dataset_name[:-len(f'_{r}')]
                        break
                else:
                    base_dataset_name = dataset_name
                break

        if not base_dataset_name:
            return {}

        # Determine source file
        if 'Battery_Energy_Storage' in base_dataset_name:
            data = self._load_json_file('Energy_Storage.json')
            root_key = 'Energy Storage'
        else:
            data = self._load_json_file('Datacenter_UPS.json')
            root_key = 'Datacenter UPS'

        # Extract data for each region
        root_data = data.get(root_key, {})
        if base_dataset_name in root_data:
            metric_data = root_data[base_dataset_name]
            if 'regions' in metric_data:
                for region in regions:
                    if region in metric_data['regions']:
                        series = self._extract_time_series(root_data, base_dataset_name, region)
                        if not series.empty:
                            result[region] = series

        return result

    # Convenience methods for common data access patterns
    def load_demand(self, entity: str) -> Dict[str, pd.Series]:
        """Load demand data for an entity"""
        return self.load_data(entity, 'demand')

    def load_cost(self, entity: str, subcategory: Optional[str] = None) -> Dict[str, pd.Series]:
        """Load cost data for an entity"""
        return self.load_data(entity, 'cost', subcategory)

    def load_installed_base(self, entity: str) -> Dict[str, pd.Series]:
        """Load installed base data for an entity"""
        return self.load_data(entity, 'installed_base')

    def load_drivers(self, entity: str = 'Datacenter_UPS') -> Dict[str, pd.Series]:
        """Load market driver data"""
        return self.load_data(entity, 'drivers')

    def load_intensity(self, entity: str) -> Dict[str, pd.Series]:
        """Load intensity/content data for an entity"""
        return self.load_data(entity, 'intensity')

    def load_lifetime(self, entity: str) -> Dict[str, pd.Series]:
        """Load lifetime/replacement cycle data for an entity"""
        return self.load_data(entity, 'lifetime')

    def get_entity_type(self, entity: str) -> Optional[str]:
        """
        Get entity type from taxonomy

        Args:
            entity: Entity name

        Returns:
            Entity type ('incumbent', 'disruptor', 'market') or None
        """
        data = self.taxonomy.get('data', {})
        if entity in data:
            return data[entity].get('entity_type')
        return None

    def get_available_categories(self, entity: str) -> List[str]:
        """Get available data categories for an entity"""
        data = self.taxonomy.get('data', {})
        if entity in data:
            return list(data[entity].keys())
        return []

    def calculate_technology_shares(self,
                                   vrla_demand: Dict[str, pd.Series],
                                   li_ion_demand: Dict[str, pd.Series]) -> Dict[str, Dict[str, pd.Series]]:
        """
        Calculate market share of each technology

        Args:
            vrla_demand: VRLA demand by region
            li_ion_demand: Li-ion demand by region

        Returns:
            Dict with 'vrla_share' and 'li_ion_share' by region
        """
        shares = {'vrla_share': {}, 'li_ion_share': {}}

        common_regions = set(vrla_demand.keys()) & set(li_ion_demand.keys())

        for region in common_regions:
            vrla = vrla_demand[region]
            li_ion = li_ion_demand[region]

            # Align indices
            combined_index = vrla.index.union(li_ion.index)
            vrla_aligned = vrla.reindex(combined_index, fill_value=0)
            li_ion_aligned = li_ion.reindex(combined_index, fill_value=0)

            total = vrla_aligned + li_ion_aligned

            # Calculate shares (avoid division by zero)
            vrla_share = np.where(total > 0, vrla_aligned / total, 0)
            li_ion_share = np.where(total > 0, li_ion_aligned / total, 0)

            shares['vrla_share'][region] = pd.Series(vrla_share, index=combined_index,
                                                    name=f'VRLA_Share_{region}')
            shares['li_ion_share'][region] = pd.Series(li_ion_share, index=combined_index,
                                                      name=f'Li_ion_Share_{region}')

        return shares

    def load_all_data(self) -> Dict[str, Any]:
        """
        Load all available data using taxonomy

        Returns:
            Dictionary with all loaded data organized by category
        """
        print("Loading datacenter UPS battery data using taxonomy...")

        # Load demand data
        vrla_demand = self.load_demand('VRLA')
        li_ion_demand = self.load_demand('Li_ion')
        total_demand = self.load_demand('Datacenter_UPS')

        # Load other data categories
        all_data = {
            'total_demand': total_demand,
            'vrla_demand': vrla_demand,
            'li_ion_demand': li_ion_demand,
            'vrla_installed_base': self.load_installed_base('VRLA'),
            'growth_rates': self.load_drivers(),
            'li_ion_intensity': self.load_intensity('Li_ion'),
            'vrla_lifetime': self.load_lifetime('VRLA'),
            'li_ion_lifetime': self.load_lifetime('Li_ion'),
            'vrla_costs': self.load_cost('VRLA'),
            'li_ion_costs_4h': self.load_cost('Li_ion', '4h_turnkey'),
            'li_ion_costs_2h': self.load_cost('Li_ion', '2h_turnkey'),
            'li_ion_power_costs': self.load_cost('Li_ion', 'power_basis'),
            'technology_shares': self.calculate_technology_shares(vrla_demand, li_ion_demand)
        }

        # Print summary
        print(f"✓ Loaded total demand for {len(all_data['total_demand'])} regions")
        print(f"✓ Loaded VRLA demand for {len(all_data['vrla_demand'])} regions")
        print(f"✓ Loaded Li-ion demand for {len(all_data['li_ion_demand'])} regions")
        print(f"✓ Loaded cost data for Li-ion ({len(all_data['li_ion_costs_4h'])} regions)")
        print(f"✓ Loaded growth projections for {len(all_data['growth_rates'])} regions")
        print(f"✓ Calculated technology shares for {len(all_data['technology_shares']['li_ion_share'])} regions")

        return all_data

    def get_summary(self, region: str = 'Global') -> Dict[str, Any]:
        """
        Get summary statistics for a specific region

        Args:
            region: Region to summarize

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'region': region,
            'available_entities': self.entities,
            'entity_types': {}
        }

        # Get entity types
        for entity in self.entities:
            summary['entity_types'][entity] = self.get_entity_type(entity)

        # Load key metrics
        vrla_demand = self.load_demand('VRLA')
        li_ion_demand = self.load_demand('Li_ion')

        if region in vrla_demand:
            vrla = vrla_demand[region]
            summary['vrla_demand_2024'] = vrla.get(2024, None)
            summary['vrla_demand_range'] = (vrla.min(), vrla.max())

        if region in li_ion_demand:
            li_ion = li_ion_demand[region]
            summary['li_ion_demand_2024'] = li_ion.get(2024, None)
            summary['li_ion_demand_range'] = (li_ion.min(), li_ion.max())

            # Calculate share
            if region in vrla_demand:
                total_2024 = vrla.get(2024, 0) + li_ion.get(2024, 0)
                if total_2024 > 0:
                    summary['li_ion_share_2024'] = li_ion.get(2024, 0) / total_2024

        return summary


# Example usage
if __name__ == "__main__":
    loader = DatacenterUPSDataLoader()

    # Show available entities and their data
    print("\n=== Datacenter UPS Data Loader (Taxonomy-based) ===\n")
    print(f"Available entities: {', '.join(loader.entities)}")
    print(f"Available regions: {', '.join(loader.regions)}")

    # Get entity types
    print("\nEntity Types:")
    for entity in loader.entities:
        entity_type = loader.get_entity_type(entity)
        categories = loader.get_available_categories(entity)
        print(f"  {entity}: {entity_type} - Categories: {', '.join(categories)}")

    # Load and show summary for Global
    print("\n=== Global Summary ===")
    summary = loader.get_summary('Global')

    if 'vrla_demand_2024' in summary:
        print(f"VRLA Demand (2024): {summary['vrla_demand_2024']:.2f} MWh")
    if 'li_ion_demand_2024' in summary:
        print(f"Li-ion Demand (2024): {summary['li_ion_demand_2024']:.2f} MWh")
    if 'li_ion_share_2024' in summary:
        print(f"Li-ion Market Share (2024): {summary['li_ion_share_2024']*100:.1f}%")

    # Load specific data using taxonomy
    print("\n=== Loading Specific Data ===")

    # Load Li-ion 4-hour costs
    li_ion_costs = loader.load_cost('Li_ion', '4h_turnkey')
    print(f"\nLi-ion 4-hour costs loaded for regions: {', '.join(li_ion_costs.keys())}")
    if 'USA' in li_ion_costs:
        usa_costs = li_ion_costs['USA']
        print(f"USA costs in 2024: ${usa_costs.get(2024, 'N/A')}/kWh")