"""
Data Loader for Copper Demand Forecasting
Loads real data from curves_catalog_files and processes for forecasting
"""

import json
import pandas as pd
from pathlib import Path


class CopperDataLoader:
    """Loads and processes copper demand data from multiple sources"""

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

    def load_copper_consumption(self):
        """Load historical copper consumption data"""
        copper_file = self.base_data_path / 'Copper.json'

        try:
            with open(copper_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Copper data file not found: {copper_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in copper data file: {e}")

        # Extract Annual_Consumption metric
        consumption_data = {}
        for metric in data.get('metrics', []):
            if metric['name'] == 'Annual_Consumption':
                for series in metric['data']:
                    region = series['region']
                    # Convert to pandas Series
                    years = [point['year'] for point in series['values']]
                    values = [point['value'] for point in series['values']]
                    consumption_data[region] = pd.Series(values, index=years)
                break

        return consumption_data

    def load_segment_shares(self):
        """Load copper demand segment share data"""
        copper_file = self.base_data_path / 'Copper.json'

        try:
            with open(copper_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Copper data file not found: {copper_file}")

        # Extract segment percentages
        segment_metrics = {
            'Demand_Transportation_Percentage': 'transportation',
            'Electrical_Demand_Percentage': 'electrical',
            'EV_Demand_Percentage': 'ev',
            'Solar_Demand_Percentage': 'solar',
            'Wind_Turbines_Percentage': 'wind'
        }

        segments = {}
        for metric in data.get('metrics', []):
            if metric['name'] in segment_metrics:
                segment_name = segment_metrics[metric['name']]
                segments[segment_name] = {}
                for series in metric['data']:
                    region = series['region']
                    # Get most recent value
                    if series['values']:
                        latest_value = series['values'][-1]['value']
                        segments[segment_name][region] = latest_value / 100.0  # Convert to fraction

        return segments

    def load_vehicle_data(self, vehicle_type='Passenger_Cars'):
        """
        Load vehicle sales and fleet data

        Args:
            vehicle_type: Passenger_Cars, Commercial_Vehicle, Two_Wheeler, Three_Wheeler
        """
        vehicle_file = self.base_data_path / f'{vehicle_type}.json'

        try:
            with open(vehicle_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Vehicle data file not found: {vehicle_file}")

        # Extract sales and fleet data by powertrain
        vehicle_data = {'sales': {}, 'fleet': {}}

        for metric in data.get('metrics', []):
            metric_name = metric['name']

            # Sales data
            if 'Annual_Sales' in metric_name:
                for series in metric['data']:
                    region = series['region']
                    powertrain = series.get('powertrain', 'ICE')

                    if region not in vehicle_data['sales']:
                        vehicle_data['sales'][region] = {}

                    years = [point['year'] for point in series['values']]
                    values = [point['value'] for point in series['values']]
                    vehicle_data['sales'][region][powertrain] = pd.Series(values, index=years)

            # Fleet data
            elif 'Total_Fleet' in metric_name:
                for series in metric['data']:
                    region = series['region']
                    powertrain = series.get('powertrain', 'ICE')

                    if region not in vehicle_data['fleet']:
                        vehicle_data['fleet'][region] = {}

                    years = [point['year'] for point in series['values']]
                    values = [point['value'] for point in series['values']]
                    vehicle_data['fleet'][region][powertrain] = pd.Series(values, index=years)

        return vehicle_data

    def load_generation_capacity(self):
        """Load power generation installed capacity data"""
        energy_file = self.base_data_path / 'Energy_Generation.json'

        try:
            with open(energy_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Energy data file not found: {energy_file}")

        # Extract installed capacity by technology
        capacity_metrics = {
            'Onshore_Wind_Installed_Capacity': 'wind_onshore',
            'Offshore_Wind_Installed_Capacity': 'wind_offshore',
            'Solar_Installed_Capacity': 'solar',
            'Coal_Installed_Capacity': 'coal',
            'Natural_Gas_Installed_Capacity': 'gas'
        }

        capacity_data = {}
        for metric in data.get('metrics', []):
            if metric['name'] in capacity_metrics:
                tech_name = capacity_metrics[metric['name']]
                capacity_data[tech_name] = {}

                for series in metric['data']:
                    region = series['region']
                    years = [point['year'] for point in series['values']]
                    values = [point['value'] for point in series['values']]
                    capacity_data[tech_name][region] = pd.Series(values, index=years)

        return capacity_data

    def get_historical_baseline(self, region='Global', start_year=2020, end_year=2023):
        """
        Get historical consumption baseline for validation

        Args:
            region: Region name
            start_year: Start year for baseline
            end_year: End year for baseline

        Returns:
            pd.Series of historical consumption
        """
        consumption_data = self.load_copper_consumption()

        if region not in consumption_data:
            raise ValueError(f"Region {region} not found in consumption data")

        # Filter to requested years
        series = consumption_data[region]
        mask = (series.index >= start_year) & (series.index <= end_year)
        return series[mask]

    def aggregate_to_global(self, regional_data):
        """
        Aggregate regional data to global total

        Args:
            regional_data: Dict of region -> pd.Series

        Returns:
            pd.Series of global totals
        """
        # Sum all regions except Global if it exists
        regions_to_sum = ['China', 'USA', 'Europe', 'Rest_of_World']

        # Initialize with first region
        result = None
        for region in regions_to_sum:
            if region in regional_data:
                if result is None:
                    result = regional_data[region].copy()
                else:
                    result = result.add(regional_data[region], fill_value=0)

        return result

    def load_all_data(self, regions=None):
        """
        Load all required data for copper demand forecasting

        Args:
            regions: List of regions to load (default: all regions)

        Returns:
            dict with all loaded data
        """
        if regions is None:
            regions = self.regions

        print("Loading copper demand data...")

        all_data = {
            'consumption': self.load_copper_consumption(),
            'segment_shares': self.load_segment_shares(),
            'vehicles': {
                'passenger_cars': self.load_vehicle_data('Passenger_Cars'),
                'commercial_vehicles': self.load_vehicle_data('Commercial_Vehicle'),
                'two_wheelers': self.load_vehicle_data('Two_Wheeler'),
                'three_wheelers': self.load_vehicle_data('Three_Wheeler')
            },
            'generation': self.load_generation_capacity()
        }

        print(f"✓ Loaded consumption data for {len(all_data['consumption'])} regions")
        print(f"✓ Loaded vehicle data for 4 vehicle types")
        print(f"✓ Loaded generation capacity for 5 technologies")

        return all_data
