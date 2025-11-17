"""
Data Loader for Datacenter UPS Battery Transition Forecasting
Loads data for VRLA and Li-ion battery adoption in datacenter UPS systems
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path


class DatacenterUPSDataLoader:
    """Loads and processes datacenter UPS battery data from multiple sources"""

    def __init__(self, base_data_path=None):
        """
        Initialize data loader

        Args:
            base_data_path: Path to data directory (defaults to skill's local data/ folder)
        """
        if base_data_path is None:
            # Default to skill's local data directory
            skill_dir = Path(__file__).parent.parent
            self.base_data_path = skill_dir / 'data'
        else:
            self.base_data_path = Path(base_data_path)

        self.regions = ['China', 'USA', 'Europe', 'Rest_of_World', 'Global']

    def _load_json_file(self, filename):
        """Helper to load and parse JSON file"""
        filepath = self.base_data_path / filename
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filepath}: {e}")

    def _extract_regional_series(self, data_dict, metric_name):
        """
        Extract regional time series from nested data structure

        Args:
            data_dict: Dictionary containing the metric data
            metric_name: Name of the metric to extract

        Returns:
            dict: Region -> pandas Series mapping
        """
        result = {}

        if metric_name in data_dict:
            regions_data = data_dict[metric_name].get('regions', {})
            for region, region_data in regions_data.items():
                if 'X' in region_data and 'Y' in region_data:
                    years = region_data['X']
                    values = region_data['Y']
                    result[region] = pd.Series(values, index=years, name=metric_name)

        return result

    def load_total_battery_demand(self):
        """Load total datacenter UPS battery demand (all chemistries)"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Data_Center_Battery_Demand_Annual_Capacity_Demand'
        )

    def load_vrla_demand(self):
        """Load VRLA (lead-acid battery) demand data"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand'
        )

    def load_lithium_demand(self):
        """Load Li-ion battery demand data"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand'
        )

    def load_vrla_installed_base(self):
        """Load VRLA installed base (cumulative capacity)"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Lead_acid_batteries_UPS_Datacenter_Installed_Base'
        )

    def load_datacenter_growth_rates(self):
        """Load datacenter capacity growth projections"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Datacenter_capacity_growth_projections'
        )

    def load_lithium_content(self):
        """Load lithium content coefficients for Li-ion batteries"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Data_Center_UPS_Battery_(Li-Ion)_Average_Lithium_content'
        )

    def load_replacement_cycle(self):
        """Load battery replacement cycle data"""
        data = self._load_json_file('Datacenter_UPS.json')
        datacenter_data = data.get('Datacenter UPS', {})

        return self._extract_regional_series(
            datacenter_data,
            'Lead_acid_batteries_UPS_Datacenter_Replacement_cycle_Battery_Replacement_cycle'
        )

    def load_bess_costs(self, duration='4-hour'):
        """
        Load Battery Energy Storage System costs (proxy for Li-ion costs)

        Args:
            duration: '2-hour' or '4-hour'
        """
        data = self._load_json_file('Energy_Storage.json')
        storage_data = data.get('Energy Storage', {})

        if duration == '4-hour':
            metric_name = 'Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost'
        elif duration == '2-hour':
            metric_name = 'Battery_Energy_Storage_System_(2-hour_Turnkey)_Cost'
        else:
            raise ValueError(f"Invalid duration: {duration}. Must be '2-hour' or '4-hour'")

        return self._extract_regional_series(storage_data, metric_name)

    def load_bess_installed_capacity(self):
        """Load BESS installed capacity for context"""
        data = self._load_json_file('Energy_Storage.json')
        storage_data = data.get('Energy Storage', {})

        capacity_data = {}
        metric_data = storage_data.get('Battery_Energy_Storage_System_Installed_Capacity', {})

        if 'regions' in metric_data:
            for region, scenarios in metric_data['regions'].items():
                # Use 'standard' scenario if available
                if 'standard' in scenarios:
                    scenario_data = scenarios['standard']
                    if 'X' in scenario_data and 'Y' in scenario_data:
                        years = scenario_data['X']
                        values = scenario_data['Y']
                        capacity_data[region] = pd.Series(values, index=years, name='BESS_Capacity')

        return capacity_data

    def calculate_technology_shares(self, vrla_demand, lithium_demand):
        """
        Calculate market share of each technology

        Args:
            vrla_demand: dict of region -> Series
            lithium_demand: dict of region -> Series

        Returns:
            dict with 'vrla_share' and 'lithium_share' by region
        """
        shares = {'vrla_share': {}, 'lithium_share': {}}

        for region in self.regions:
            if region in vrla_demand and region in lithium_demand:
                vrla_series = vrla_demand[region]
                lithium_series = lithium_demand[region]

                # Align indices
                combined_index = vrla_series.index.union(lithium_series.index)
                vrla_aligned = vrla_series.reindex(combined_index, fill_value=0)
                lithium_aligned = lithium_series.reindex(combined_index, fill_value=0)

                total = vrla_aligned + lithium_aligned

                # Avoid division by zero
                vrla_share = np.where(total > 0, vrla_aligned / total, 0)
                lithium_share = np.where(total > 0, lithium_aligned / total, 0)

                shares['vrla_share'][region] = pd.Series(vrla_share, index=combined_index, name='VRLA_Share')
                shares['lithium_share'][region] = pd.Series(lithium_share, index=combined_index, name='Lithium_Share')

        return shares

    def get_historical_baseline(self, region='Global', start_year=2020, end_year=2024):
        """
        Get historical baseline for validation

        Args:
            region: Region name
            start_year: Start year for baseline
            end_year: End year for baseline

        Returns:
            dict with VRLA and Li-ion demand baselines
        """
        vrla_demand = self.load_vrla_demand()
        lithium_demand = self.load_lithium_demand()

        baseline = {}

        if region in vrla_demand:
            series = vrla_demand[region]
            mask = (series.index >= start_year) & (series.index <= end_year)
            baseline['vrla'] = series[mask]

        if region in lithium_demand:
            series = lithium_demand[region]
            mask = (series.index >= start_year) & (series.index <= end_year)
            baseline['lithium'] = series[mask]

        return baseline

    def load_all_data(self, regions=None):
        """
        Load all required data for datacenter UPS transition forecasting

        Args:
            regions: List of regions to load (default: all regions)

        Returns:
            dict with all loaded data
        """
        if regions is None:
            regions = self.regions

        print("Loading datacenter UPS battery transition data...")

        # Load all datasets
        vrla_demand = self.load_vrla_demand()
        lithium_demand = self.load_lithium_demand()

        all_data = {
            'total_demand': self.load_total_battery_demand(),
            'vrla_demand': vrla_demand,
            'lithium_demand': lithium_demand,
            'vrla_installed_base': self.load_vrla_installed_base(),
            'growth_rates': self.load_datacenter_growth_rates(),
            'lithium_content': self.load_lithium_content(),
            'replacement_cycle': self.load_replacement_cycle(),
            'bess_costs_4h': self.load_bess_costs('4-hour'),
            'bess_costs_2h': self.load_bess_costs('2-hour'),
            'bess_capacity': self.load_bess_installed_capacity(),
            'technology_shares': self.calculate_technology_shares(vrla_demand, lithium_demand)
        }

        print(f"✓ Loaded battery demand data for {len(all_data['total_demand'])} regions")
        print(f"✓ Loaded VRLA demand for {len(all_data['vrla_demand'])} regions")
        print(f"✓ Loaded Li-ion demand for {len(all_data['lithium_demand'])} regions")
        print(f"✓ Loaded BESS cost data for {len(all_data['bess_costs_4h'])} regions")
        print(f"✓ Loaded datacenter growth projections")

        return all_data

    def summarize_data(self, all_data, region='Global'):
        """
        Print summary statistics for loaded data

        Args:
            all_data: Dictionary from load_all_data()
            region: Region to summarize
        """
        print(f"\n=== Data Summary for {region} ===\n")

        if region in all_data['total_demand']:
            total = all_data['total_demand'][region]
            print(f"Total Battery Demand:")
            print(f"  Years: {total.index.min()} - {total.index.max()}")
            print(f"  Range: {total.min():.2f} - {total.max():.2f} GWh/year")
            print(f"  Latest (2024): {total.get(2024, 'N/A')} GWh/year")

        if region in all_data['vrla_demand']:
            vrla = all_data['vrla_demand'][region]
            print(f"\nVRLA Demand:")
            print(f"  Years: {vrla.index.min()} - {vrla.index.max()}")
            print(f"  Range: {vrla.min():.2f} - {vrla.max():.2f} GWh/year")
            print(f"  Latest (2024): {vrla.get(2024, 'N/A')} GWh/year")

        if region in all_data['lithium_demand']:
            li = all_data['lithium_demand'][region]
            print(f"\nLi-ion Demand:")
            print(f"  Years: {li.index.min()} - {li.index.max()}")
            print(f"  Range: {li.min():.2f} - {li.max():.2f} GWh/year")
            print(f"  Latest (2024): {li.get(2024, 'N/A')} GWh/year")

        if region in all_data['technology_shares']['lithium_share']:
            share = all_data['technology_shares']['lithium_share'][region]
            print(f"\nLi-ion Market Share:")
            print(f"  2020: {share.get(2020, 0)*100:.1f}%")
            print(f"  2024: {share.get(2024, 0)*100:.1f}%")

        if region in all_data['bess_costs_4h']:
            costs = all_data['bess_costs_4h'][region]
            print(f"\nBESS 4-hour Costs ($/kWh):")
            print(f"  Years: {costs.index.min()} - {costs.index.max()}")
            print(f"  Range: ${costs.min():.0f} - ${costs.max():.0f}")
            print(f"  Latest (2024): ${costs.get(2024, 'N/A')}")


# Example usage
if __name__ == "__main__":
    loader = DatacenterUPSDataLoader()

    # Load all data
    all_data = loader.load_all_data()

    # Print summary for Global
    loader.summarize_data(all_data, region='Global')

    # Print summary for USA
    print("\n" + "="*60)
    loader.summarize_data(all_data, region='USA')
