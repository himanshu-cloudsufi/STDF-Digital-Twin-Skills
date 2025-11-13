"""
Data Loader for Lead Demand Forecasting
Loads lead demand data and vehicle fleet data for SLI battery calculations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path


class LeadDataLoader:
    """Loads and processes lead demand and vehicle data"""

    def __init__(self, base_data_path=None):
        """
        Initialize data loader

        Args:
            base_data_path: Path to data directory (defaults to skill's local data/ folder)
        """
        if base_data_path is None:
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
        """Extract regional time series from nested data structure"""
        result = {}

        if metric_name in data_dict:
            regions_data = data_dict[metric_name].get('regions', {})
            for region, region_data in regions_data.items():
                if 'X' in region_data and 'Y' in region_data:
                    years = region_data['X']
                    values = region_data['Y']
                    result[region] = pd.Series(values, index=years, name=metric_name)

        return result

    def load_total_lead_demand(self):
        """Load total annual implied lead demand"""
        data = self._load_json_file('Lead.json')
        lead_data = data.get('Lead', {})
        return self._extract_regional_series(lead_data, 'Annual_Implied_Demand')

    def load_industrial_battery_demand(self):
        """Load industrial battery lead demand (motive + stationary)"""
        data = self._load_json_file('Lead.json')
        lead_data = data.get('Lead', {})

        motive = self._extract_regional_series(lead_data, 'Annual_Implied_Demand-Industrial_batteries_motive_power')
        stationary = self._extract_regional_series(lead_data, 'Annual_Implied_Demand-Industrial_batteries_stationary')

        return {'motive': motive, 'stationary': stationary}

    def load_non_battery_demand(self):
        """Load non-battery uses of lead"""
        data = self._load_json_file('Lead.json')
        lead_data = data.get('Lead', {})
        return self._extract_regional_series(lead_data, 'Annual_Implied_Demand-Non-battery_uses')

    def load_lead_cost(self):
        """Load lead commodity cost"""
        data = self._load_json_file('Lead.json')
        lead_data = data.get('Lead', {})
        return self._extract_regional_series(lead_data, 'Cost')

    def _extract_vehicle_series(self, metric_data, scenario='standard'):
        """
        Extract vehicle time series from nested scenario structure

        Args:
            metric_data: Metric dictionary with regions->scenario->X/Y structure
            scenario: Which scenario to extract ('standard' or 'TaaSAdj')

        Returns:
            Dict of region -> pandas Series
        """
        import re

        result = {}
        regions_data = metric_data.get('regions', {})

        for region, scenarios in regions_data.items():
            # Handle both direct X/Y structure and scenario-nested structure
            if 'X' in scenarios and 'Y' in scenarios:
                # Direct structure (like Lead.json)
                years = scenarios['X']
                values = scenarios['Y']
            elif scenario in scenarios:
                # Scenario-nested structure (like vehicle data)
                scenario_data = scenarios[scenario]
                years = scenario_data.get('X', [])
                values = scenario_data.get('Y', [])
            else:
                # Try 'standard' as fallback
                scenario_data = scenarios.get('standard', {})
                years = scenario_data.get('X', [])
                values = scenario_data.get('Y', [])

            if years and values:
                result[region] = pd.Series(values, index=years)

        return result

    def load_vehicle_data(self, vehicle_type='Passenger_Cars', scenario='standard'):
        """
        Load vehicle sales and fleet data

        Args:
            vehicle_type: Passenger_Cars, Commercial_Vehicle, Two_Wheeler, Three_Wheeler
            scenario: 'standard' or 'TaaSAdj' (Transport-as-a-Service adjusted)

        Returns:
            dict with 'sales' and 'fleet' data by region and powertrain
        """
        import re

        vehicle_file = self.base_data_path / f'{vehicle_type}.json'

        try:
            with open(vehicle_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Vehicle data file not found: {vehicle_file}")

        # Extract sales and fleet data by powertrain
        vehicle_data = {'sales': {}, 'fleet': {}, 'lead_content': {}}

        # Get the vehicle category (first key in the JSON)
        # e.g., "Passenger Cars", "Commercial Vehicle", etc.
        vehicle_category = None
        for key in data.keys():
            if key not in ['metadata', 'config']:
                vehicle_category = key
                break

        if not vehicle_category:
            # Fallback: use the vehicle_type mapping
            category_map = {
                'Passenger_Cars': 'Passenger Cars',
                'Commercial_Vehicle': 'Commercial Vehicle',
                'Two_Wheeler': 'Two Wheeler',
                'Three_Wheeler': 'Three Wheeler'
            }
            vehicle_category = category_map.get(vehicle_type, vehicle_type)

        vehicle_category_data = data.get(vehicle_category, {})

        # Iterate through all metrics in the vehicle category
        for metric_name, metric_data in vehicle_category_data.items():
            # Extract powertrain from metric name using regex: (ICE), (BEV), (PHEV), (EV), (NGV), (HEV)
            powertrain_match = re.search(r'\(([A-Z]+)\)', metric_name)
            powertrain = powertrain_match.group(1) if powertrain_match else 'ICE'

            # Handle Annual Sales metrics
            if 'Annual_Sales' in metric_name:
                regional_series = self._extract_vehicle_series(metric_data, scenario)
                for region, series in regional_series.items():
                    if region not in vehicle_data['sales']:
                        vehicle_data['sales'][region] = {}
                    vehicle_data['sales'][region][powertrain] = series

            # Handle Total Fleet metrics
            elif 'Total_Fleet' in metric_name:
                regional_series = self._extract_vehicle_series(metric_data, scenario)
                for region, series in regional_series.items():
                    if region not in vehicle_data['fleet']:
                        vehicle_data['fleet'][region] = {}
                    # Convert from units to millions for consistency
                    vehicle_data['fleet'][region][powertrain] = series / 1_000_000

            # Handle lead content coefficient (e.g., PHEV average lead content)
            elif 'lead_content' in metric_name.lower():
                regional_series = self._extract_vehicle_series(metric_data, scenario)
                for region, series in regional_series.items():
                    if region not in vehicle_data['lead_content']:
                        vehicle_data['lead_content'][region] = {}
                    vehicle_data['lead_content'][region][powertrain] = series

        return vehicle_data

    def calculate_sli_demand_from_fleet(self, fleet_by_powertrain, lead_coefficients, battery_lifetime=4.5):
        """
        Calculate SLI battery lead demand from vehicle fleet

        Args:
            fleet_by_powertrain: Dict of powertrain -> Series (fleet size in millions)
            lead_coefficients: Dict of powertrain -> kg lead per vehicle
            battery_lifetime: Battery replacement cycle in years

        Returns:
            Annual SLI lead demand in tonnes
        """
        total_demand = None

        for powertrain, fleet_series in fleet_by_powertrain.items():
            if powertrain in lead_coefficients:
                coeff = lead_coefficients[powertrain]  # kg per vehicle
                # Annual replacement = fleet / lifetime
                replacements_per_year = fleet_series / battery_lifetime  # millions
                annual_demand = replacements_per_year * coeff  # millions * kg = thousands of tonnes
                annual_demand = annual_demand * 1000  # convert to tonnes

                if total_demand is None:
                    total_demand = annual_demand
                else:
                    total_demand = total_demand.add(annual_demand, fill_value=0)

        return total_demand if total_demand is not None else pd.Series()

    def load_all_data(self, regions=None, scenario='standard'):
        """
        Load all required data for lead demand forecasting

        Args:
            regions: List of regions to load (default: all regions)
            scenario: Vehicle data scenario ('standard' or 'TaaSAdj')

        Returns:
            dict with all loaded data
        """
        if regions is None:
            regions = self.regions

        print(f"Loading lead demand data (scenario: {scenario})...")

        all_data = {
            'total_demand': self.load_total_lead_demand(),
            'industrial_batteries': self.load_industrial_battery_demand(),
            'non_battery_uses': self.load_non_battery_demand(),
            'lead_cost': self.load_lead_cost(),
            'vehicles': {
                'passenger_cars': self.load_vehicle_data('Passenger_Cars', scenario),
                'commercial_vehicles': self.load_vehicle_data('Commercial_Vehicle', scenario),
                'two_wheelers': self.load_vehicle_data('Two_Wheeler', scenario),
                'three_wheelers': self.load_vehicle_data('Three_Wheeler', scenario)
            }
        }

        print(f"✓ Loaded total lead demand for {len(all_data['total_demand'])} regions")
        print(f"✓ Loaded industrial battery demand (motive + stationary)")
        print(f"✓ Loaded vehicle data for 4 vehicle types")
        print(f"✓ Loaded lead cost data")

        return all_data

    def summarize_data(self, all_data, region='Global'):
        """Print summary statistics for loaded data"""
        print(f"\n=== Data Summary for {region} ===\n")

        if region in all_data['total_demand']:
            total = all_data['total_demand'][region]
            print(f"Total Lead Demand:")
            print(f"  Years: {total.index.min()} - {total.index.max()}")
            print(f"  Range: {total.min():.0f} - {total.max():.0f} kt")
            print(f"  2024: {total.get(2024, 'N/A')} kt")
            print(f"  2030: {total.get(2030, 'N/A')} kt")
            print(f"  2040: {total.get(2040, 'N/A')} kt")

        if region in all_data['industrial_batteries']['motive']:
            motive = all_data['industrial_batteries']['motive'][region]
            print(f"\nIndustrial Motive Power Batteries:")
            print(f"  2024: {motive.get(2024, 'N/A')} kt")
            print(f"  2040: {motive.get(2040, 'N/A')} kt")

        if region in all_data['industrial_batteries']['stationary']:
            stat = all_data['industrial_batteries']['stationary'][region]
            print(f"\nIndustrial Stationary Batteries:")
            print(f"  2024: {stat.get(2024, 'N/A')} kt")
            print(f"  2040: {stat.get(2040, 'N/A')} kt")

        # Vehicle fleet summary
        if region in all_data['vehicles']['passenger_cars']['fleet']:
            fleet_data = all_data['vehicles']['passenger_cars']['fleet'][region]
            print(f"\nPassenger Car Fleet ({region}):")
            for powertrain, series in fleet_data.items():
                if 2024 in series.index:
                    print(f"  {powertrain} (2024): {series[2024]:.1f}M units")


# Example usage
if __name__ == "__main__":
    loader = LeadDataLoader()
    all_data = loader.load_all_data()
    loader.summarize_data(all_data, region='Global')
