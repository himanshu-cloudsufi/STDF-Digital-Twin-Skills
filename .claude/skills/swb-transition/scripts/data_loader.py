"""
Data Loader for SWB Transition Forecasting
Loads LCOE, capacity, and generation data for energy transition analysis
"""

import json
import pandas as pd
from pathlib import Path


class SWBDataLoader:
    """Loads energy generation, storage, and electricity data"""

    def __init__(self, base_data_path=None):
        if base_data_path is None:
            skill_dir = Path(__file__).parent.parent
            self.base_data_path = skill_dir / 'data'
        else:
            self.base_data_path = Path(base_data_path)

        self.regions = ['China', 'USA', 'Europe', 'Rest_of_World', 'Global']

    def _load_json(self, filename):
        filepath = self.base_data_path / filename
        with open(filepath, 'r') as f:
            return json.load(f)

    def _extract_series(self, data_dict, metric_name):
        result = {}
        if metric_name in data_dict:
            regions_data = data_dict[metric_name].get('regions', {})
            for region, region_data in regions_data.items():
                if 'X' in region_data and 'Y' in region_data:
                    result[region] = pd.Series(region_data['Y'], index=region_data['X'], name=metric_name)
        return result

    def load_lcoe_data(self):
        """Load LCOE data for all technologies

        Note: Data in files is in $/kWh, converted to $/MWh here
        """
        data = self._load_json('Energy_Generation.json')
        gen_data = data.get('Energy Generation', {})

        lcoe = {
            'solar': self._extract_series(gen_data, 'Solar_Photovoltaic_LCOE'),
            'onshore_wind': self._extract_series(gen_data, 'Onshore_Wind_LCOE'),
            'offshore_wind': self._extract_series(gen_data, 'Offshore_Wind_LCOE'),
            'coal': self._extract_series(gen_data, 'Coal_Power_LCOE_Derived'),
            'gas': self._extract_series(gen_data, 'Gas_Power_LCOE_Derived')
        }

        # Convert $/kWh to $/MWh (multiply by 1000)
        for tech, region_dict in lcoe.items():
            for region, series in region_dict.items():
                if not series.empty:
                    lcoe[tech][region] = series * 1000

        return lcoe

    def load_capacity_data(self):
        """Load installed capacity data for all technologies

        Note: Data in files is in MW, converted to GW here
        """
        data = self._load_json('Energy_Generation.json')
        gen_data = data.get('Energy Generation', {})

        capacity = {
            'solar': self._extract_series(gen_data, 'Solar_Installed_Capacity'),
            'onshore_wind': self._extract_series(gen_data, 'Onshore_Wind_Installed_Capacity'),
            'offshore_wind': self._extract_series(gen_data, 'Offshore_Wind_Installed_Capacity'),
            'coal': self._extract_series(gen_data, 'Coal_Installed_Capacity'),
            'gas': self._extract_series(gen_data, 'Natural_Gas_Installed_Capacity'),
            # Baseline technologies
            'nuclear': self._extract_series(gen_data, 'Nuclear_Installed_Capacity'),
            'hydro': self._extract_series(gen_data, 'Hydro_Installed_Capacity'),
            'geothermal': self._extract_series(gen_data, 'Geothermal_Installed_Capacity'),
            'biomass': self._extract_series(gen_data, 'Biomass_Installed_Capacity')
        }

        # Convert MW to GW (divide by 1000)
        for tech, region_dict in capacity.items():
            for region, series in region_dict.items():
                if not series.empty:
                    capacity[tech][region] = series / 1000

        return capacity

    def load_generation_data(self):
        """Load power generation data for all technologies

        Note: Data in files is in GWh, converted to TWh here
        """
        data = self._load_json('Energy_Generation.json')
        gen_data = data.get('Energy Generation', {})

        generation = {
            'solar': self._extract_series(gen_data, 'Solar_Annual_Power_Generation'),
            'wind': self._extract_series(gen_data, 'Wind_Annual_Power_Generation'),
            'coal': self._extract_series(gen_data, 'Coal_Annual_Power_Generation'),
            'gas': self._extract_series(gen_data, 'Natural_Gas_Annual_Power_Generation'),
            # Baseline technologies - try to load, empty dict if not available
            'nuclear': self._extract_series(gen_data, 'Nuclear_Annual_Power_Generation'),
            'hydro': self._extract_series(gen_data, 'Hydro_Annual_Power_Generation'),
            'geothermal': self._extract_series(gen_data, 'Geothermal_Annual_Power_Generation'),
            'biomass': self._extract_series(gen_data, 'Biomass_Annual_Power_Generation'),
            'other_renewables': self._extract_series(gen_data, 'Other_Renewables_Annual_Power_Generation')
        }

        # Convert GWh to TWh (divide by 1000)
        for tech, region_dict in generation.items():
            for region, series in region_dict.items():
                if not series.empty:
                    generation[tech][region] = series / 1000

        return generation

    def load_bess_costs(self):
        """Load battery storage costs"""
        data = self._load_json('Energy_Storage.json')
        storage_data = data.get('Energy Storage', {})
        return self._extract_series(storage_data, 'Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost')

    def load_electricity_demand(self):
        """Load electricity consumption data

        Note: Data in files is already in TWh (no conversion needed)
        """
        data = self._load_json('Electricity.json')
        elec_data = data.get('Electricity', {})
        return self._extract_series(elec_data, 'Annual_Domestic_Consumption')

    def load_all_data(self):
        """Load all required data"""
        print("Loading SWB transition data...")

        all_data = {
            'lcoe': self.load_lcoe_data(),
            'capacity': self.load_capacity_data(),
            'generation': self.load_generation_data(),
            'bess_costs': self.load_bess_costs(),
            'electricity_demand': self.load_electricity_demand()
        }

        print(f"✓ Loaded LCOE data for 5 technologies")
        print(f"✓ Loaded capacity and generation data")
        print(f"✓ Loaded BESS costs and electricity demand")

        return all_data


if __name__ == "__main__":
    loader = SWBDataLoader()
    data = loader.load_all_data()
    print("\n=== Sample Data (Global) ===")
    if 'Global' in data['lcoe']['solar']:
        print(f"Solar LCOE (2024): ${data['lcoe']['solar']['Global'].get(2024, 'N/A')}/MWh")
