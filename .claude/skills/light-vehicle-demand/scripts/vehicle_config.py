"""
Vehicle configuration management for light vehicle demand forecasting.

This module provides vehicle-specific parameters and configuration loading
for two-wheeler and three-wheeler demand forecasting.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any


class VehicleConfig:
    """Manages vehicle-specific configuration parameters."""

    # Core vehicle type definitions
    VEHICLE_TYPES = {
        'two_wheeler': {
            'display_name': 'Two-Wheeler',
            'display_name_plural': 'Two-Wheelers',
            'lifetime_years': 11.0,
            'regions': ['China', 'USA', 'Europe', 'Rest_of_World'],
            'market_product': 'Two_Wheelers',
            'ev_product': 'EV_2_Wheelers',
            'ice_product': 'ICE_2_Wheelers',
            'taxonomy_file': 'two_wheeler_taxonomy_and_datasets.json',
            'curves_files': ['Two_Wheeler.json', 'Two_Wheelers.json'],
            'dataset_prefix': 'Two_Wheeler_',
            'dataset_pattern': '2_Wheeler',
            'output_formats': ['csv', 'json', 'plot'],
            'config_file': 'two_wheeler_config.json',
            'data_subdirectory': 'two_wheeler',
            'output_subdirectory': 'two_wheeler'
        },
        'three_wheeler': {
            'display_name': 'Three-Wheeler',
            'display_name_plural': 'Three-Wheelers',
            'lifetime_years': 10.0,
            'regions': ['China', 'Europe', 'Rest_of_World'],
            'market_product': 'Three_Wheelers',
            'ev_product': 'EV_3_Wheelers',
            'ice_product': 'ICE_3_Wheelers',
            'taxonomy_file': 'three_wheeler_taxonomy_and_datasets.json',
            'curves_files': ['Three_Wheeler.json', 'Three_Wheelers.json'],
            'dataset_prefix': 'Three_Wheeler_',
            'dataset_pattern': '3_Wheeler',
            'output_formats': ['csv', 'json'],
            'config_file': 'three_wheeler_config.json',
            'data_subdirectory': 'three_wheeler',
            'output_subdirectory': 'three_wheeler'
        }
    }

    def __init__(self, vehicle_type: str, skill_root: Path = None):
        """
        Initialize vehicle configuration.

        Args:
            vehicle_type: Type of vehicle ('two_wheeler' or 'three_wheeler')
            skill_root: Root directory of the skill (auto-detected if None)
        """
        if vehicle_type not in self.VEHICLE_TYPES:
            raise ValueError(
                f"Invalid vehicle type: {vehicle_type}. "
                f"Must be one of {list(self.VEHICLE_TYPES.keys())}"
            )

        self.vehicle_type = vehicle_type
        self.params = self.VEHICLE_TYPES[vehicle_type].copy()

        # Determine skill root directory
        if skill_root is None:
            # Assume we're in scripts/ directory
            current_file = Path(__file__).resolve()
            self.skill_root = current_file.parent.parent
        else:
            self.skill_root = Path(skill_root)

        # Load JSON configuration if available
        config_path = self.skill_root / 'configs' / self.params['config_file']
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.json_config = json.load(f)
        else:
            self.json_config = {}

    def get_display_name(self, plural: bool = False) -> str:
        """Get human-readable vehicle name."""
        return self.params['display_name_plural'] if plural else self.params['display_name']

    def get_lifetime_years(self) -> float:
        """Get vehicle lifetime in years for fleet tracking."""
        return self.params['lifetime_years']

    def get_regions(self) -> List[str]:
        """Get list of supported regions for this vehicle type."""
        return self.params['regions'].copy()

    def is_region_supported(self, region: str) -> bool:
        """Check if a region is supported for this vehicle type."""
        return region in self.params['regions'] or region == 'Global'

    def get_product_names(self) -> Dict[str, str]:
        """Get product names for market, EV, and ICE segments."""
        return {
            'market': self.params['market_product'],
            'ev': self.params['ev_product'],
            'ice': self.params['ice_product']
        }

    def get_data_directory(self) -> Path:
        """Get data directory path for this vehicle type."""
        return self.skill_root / 'data' / self.params['data_subdirectory']

    def get_output_directory(self) -> Path:
        """Get output directory path for this vehicle type."""
        return self.skill_root / 'output' / self.params['output_subdirectory']

    def get_taxonomy_file_path(self) -> Path:
        """Get full path to taxonomy file."""
        return self.get_data_directory() / self.params['taxonomy_file']

    def get_curves_file_paths(self) -> List[Path]:
        """Get list of possible curves file paths."""
        data_dir = self.get_data_directory()
        return [data_dir / filename for filename in self.params['curves_files']]

    def get_dataset_prefix(self) -> str:
        """Get dataset name prefix for this vehicle type."""
        return self.params['dataset_prefix']

    def get_dataset_pattern(self) -> str:
        """Get dataset pattern for metric name replacement."""
        return self.params['dataset_pattern']

    def get_output_formats(self) -> List[str]:
        """Get supported output formats for this vehicle type."""
        return self.params['output_formats'].copy()

    def get_output_filename_prefix(self) -> str:
        """Get prefix for output filenames."""
        return self.vehicle_type

    def get_json_config(self) -> Dict[str, Any]:
        """Get loaded JSON configuration."""
        return self.json_config.copy()

    def get_scenario_config(self, scenario_name: str = 'baseline') -> Dict[str, Any]:
        """
        Get scenario-specific configuration.

        Args:
            scenario_name: Name of scenario ('baseline', 'accelerated_ev', 'conservative')

        Returns:
            Scenario configuration dictionary
        """
        scenarios = self.json_config.get('scenarios', {})
        if scenario_name not in scenarios:
            raise ValueError(
                f"Scenario '{scenario_name}' not found. "
                f"Available: {list(scenarios.keys())}"
            )
        return scenarios[scenario_name].copy()

    @staticmethod
    def list_vehicle_types() -> List[str]:
        """List all available vehicle types."""
        return list(VehicleConfig.VEHICLE_TYPES.keys())

    @staticmethod
    def get_vehicle_info(vehicle_type: str) -> Dict[str, Any]:
        """Get vehicle type information without loading full config."""
        if vehicle_type not in VehicleConfig.VEHICLE_TYPES:
            raise ValueError(f"Invalid vehicle type: {vehicle_type}")
        return VehicleConfig.VEHICLE_TYPES[vehicle_type].copy()


def load_vehicle_config(vehicle_type: str, skill_root: Path = None) -> VehicleConfig:
    """
    Convenience function to load vehicle configuration.

    Args:
        vehicle_type: Type of vehicle ('two_wheeler' or 'three_wheeler')
        skill_root: Root directory of the skill (auto-detected if None)

    Returns:
        VehicleConfig instance
    """
    return VehicleConfig(vehicle_type, skill_root)


if __name__ == '__main__':
    # Test vehicle configuration
    print("Testing Vehicle Configuration\n")

    for vtype in VehicleConfig.list_vehicle_types():
        print(f"\n{vtype.upper().replace('_', '-')} Configuration:")
        print("-" * 50)

        config = VehicleConfig(vtype)
        print(f"Display name: {config.get_display_name()}")
        print(f"Lifetime: {config.get_lifetime_years()} years")
        print(f"Regions: {', '.join(config.get_regions())}")
        print(f"Products: {config.get_product_names()}")
        print(f"Data directory: {config.get_data_directory()}")
        print(f"Output formats: {', '.join(config.get_output_formats())}")
