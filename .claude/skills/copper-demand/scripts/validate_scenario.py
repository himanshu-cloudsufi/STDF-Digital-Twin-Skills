#!/usr/bin/env python3
"""
Validate scenario parameters before running forecast
"""

import json
import sys
from pathlib import Path


def validate_scenario(config_path, scenario_name):
    """
    Validate that scenario exists and has required parameters

    Returns: (valid, error_message)
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        return False, f"Config file not found: {config_path}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in config file: {e}"

    # Check scenario exists
    if 'scenarios' not in config:
        return False, "No 'scenarios' section in config"

    scenarios = config['scenarios']
    if scenario_name not in scenarios:
        available = ', '.join(scenarios.keys())
        return False, f"Scenario '{scenario_name}' not found. Available: {available}"

    scenario = scenarios[scenario_name]

    # Validate required parameters
    errors = []

    # Check EV adoption (look for year-specific key or default 2045 key)
    ev_key = None
    for key in scenario.keys():
        if key.startswith('ev_adoption_'):
            ev_key = key
            break

    if ev_key:
        ev_adoption = scenario[ev_key]
        if not (0 <= ev_adoption <= 1):
            errors.append(f"EV adoption must be 0-1, got {ev_adoption}")
    else:
        errors.append("Missing EV adoption parameter (expected 'ev_adoption_YEAR')")

    # Check renewable capacity (look for year-specific key or default 2045 key)
    renewable_key = None
    for key in scenario.keys():
        if key.startswith('renewable_capacity_') and key.endswith('_tw'):
            renewable_key = key
            break

    if renewable_key:
        renewable_tw = scenario[renewable_key]
        if renewable_tw < 0:
            errors.append(f"Renewable capacity must be positive, got {renewable_tw}")
        if renewable_tw > 30:
            errors.append(f"Warning: Renewable capacity {renewable_tw} TW seems very high (>30 TW)")
    else:
        errors.append("Missing renewable capacity parameter (expected 'renewable_capacity_YEAR_tw')")

    # Check optional parameters
    if 'demand_multiplier' in scenario:
        multiplier = scenario['demand_multiplier']
        if multiplier <= 0:
            errors.append(f"Demand multiplier must be positive, got {multiplier}")
        if multiplier > 2.0:
            errors.append(f"Warning: Demand multiplier {multiplier} seems very high (>2.0x)")

    if 'coefficient_reduction' in scenario:
        reduction = scenario['coefficient_reduction']
        if not (0 <= reduction <= 1):
            errors.append(f"Coefficient reduction must be 0-1, got {reduction}")

    if errors:
        return False, "\n".join(errors)

    # Print validation summary
    print(f"✓ Scenario '{scenario_name}' validation passed")
    if ev_key:
        year = ev_key.split('_')[-1]
        print(f"  EV Adoption {year}: {scenario[ev_key]:.1%}")
    if renewable_key:
        year = renewable_key.split('_')[-2]  # Get year from renewable_capacity_YEAR_tw
        print(f"  Renewable Capacity {year}: {scenario[renewable_key]} TW")
    if 'demand_multiplier' in scenario:
        print(f"  Demand Multiplier: {scenario['demand_multiplier']:.2f}x")
    if 'coefficient_reduction' in scenario:
        print(f"  Coefficient Reduction: {scenario['coefficient_reduction']:.1%}")

    return True, "Scenario valid"


def main():
    if len(sys.argv) != 3:
        print("Usage: python validate_scenario.py <config_path> <scenario_name>")
        print("\nExample:")
        print("  python validate_scenario.py config.json baseline")
        return 1

    config_path = sys.argv[1]
    scenario_name = sys.argv[2]

    valid, message = validate_scenario(config_path, scenario_name)

    if not valid:
        print(f"✗ Scenario validation failed:")
        print(f"  {message}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
