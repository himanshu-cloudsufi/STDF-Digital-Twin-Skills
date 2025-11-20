#!/usr/bin/env python3
"""
TCO (Total Cost of Ownership) Validation Script
Validates TCO calculations for VRLA and Li-ion batteries
"""

import json
import sys
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional


class TCOValidator:
    """Validates Total Cost of Ownership calculations"""

    def __init__(self, config_path: str = None):
        """Initialize with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config.json'

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.tco_horizon = self.config['default_parameters']['tco_horizon_years']
        self.discount_rate = self.config['default_parameters']['discount_rate']
        self.vrla_params = self.config['cost_parameters']['vrla']
        self.lithium_params = self.config['cost_parameters']['lithium']
        self.vrla_lifespan = self.config['lifespans']['vrla_years']
        self.lithium_lifespan = self.config['lifespans']['lithium_years']

    def calculate_tco(self, capex: float, opex: float, lifespan: int) -> float:
        """
        Calculate Total Cost of Ownership

        Args:
            capex: Capital expenditure per kWh
            opex: Annual operating expenditure per kWh
            lifespan: Battery lifespan in years

        Returns:
            Total cost of ownership per kWh
        """
        # Initial capex
        tco = capex

        # Add discounted opex over horizon
        for year in range(1, self.tco_horizon + 1):
            discount_factor = (1 + self.discount_rate) ** year
            tco += opex / discount_factor

        # Add replacement costs
        num_replacements = self.tco_horizon // lifespan
        for replacement in range(1, num_replacements + 1):
            replacement_year = lifespan * replacement
            if replacement_year < self.tco_horizon:
                discount_factor = (1 + self.discount_rate) ** replacement_year
                tco += capex / discount_factor

        return tco

    def validate_tco_calculation(self) -> Dict[str, any]:
        """Validate TCO calculations with detailed breakdown"""
        results = {}

        # Calculate VRLA TCO
        vrla_capex = self.vrla_params['capex_per_kwh']
        vrla_opex = self.vrla_params['opex_per_kwh_year']
        vrla_tco = self.calculate_tco(vrla_capex, vrla_opex, self.vrla_lifespan)

        # Calculate Li-ion TCO (using base cost for validation)
        lithium_capex = 200.0  # Example base cost
        lithium_opex = self.lithium_params['opex_per_kwh_year']
        lithium_tco = self.calculate_tco(lithium_capex, lithium_opex, self.lithium_lifespan)

        results['vrla'] = {
            'capex': vrla_capex,
            'opex': vrla_opex,
            'lifespan': self.vrla_lifespan,
            'tco': vrla_tco,
            'breakdown': self._tco_breakdown('VRLA', vrla_capex, vrla_opex, self.vrla_lifespan)
        }

        results['lithium'] = {
            'capex': lithium_capex,
            'opex': lithium_opex,
            'lifespan': self.lithium_lifespan,
            'tco': lithium_tco,
            'breakdown': self._tco_breakdown('Li-ion', lithium_capex, lithium_opex, self.lithium_lifespan)
        }

        results['advantage'] = vrla_tco - lithium_tco
        results['advantage_pct'] = (vrla_tco - lithium_tco) / vrla_tco * 100

        return results

    def _tco_breakdown(self, tech: str, capex: float, opex: float, lifespan: int) -> Dict:
        """Generate detailed TCO breakdown"""
        breakdown = {
            'technology': tech,
            'initial_capex': capex,
            'npv_opex': 0,
            'npv_replacements': 0,
            'replacements': []
        }

        # Calculate NPV of OpEx
        for year in range(1, self.tco_horizon + 1):
            discount_factor = (1 + self.discount_rate) ** year
            breakdown['npv_opex'] += opex / discount_factor

        # Calculate replacement costs
        num_replacements = self.tco_horizon // lifespan
        for replacement in range(1, num_replacements + 1):
            replacement_year = lifespan * replacement
            if replacement_year < self.tco_horizon:
                discount_factor = (1 + self.discount_rate) ** replacement_year
                replacement_cost = capex / discount_factor
                breakdown['npv_replacements'] += replacement_cost
                breakdown['replacements'].append({
                    'year': replacement_year,
                    'cost': capex,
                    'npv': replacement_cost
                })

        breakdown['total_tco'] = (breakdown['initial_capex'] +
                                   breakdown['npv_opex'] +
                                   breakdown['npv_replacements'])

        return breakdown

    def sensitivity_analysis(self, parameter: str, values: list) -> Dict:
        """
        Perform sensitivity analysis on a specific parameter

        Args:
            parameter: Parameter to vary ('capex', 'opex', 'lifespan', 'discount_rate')
            values: List of values to test

        Returns:
            Sensitivity results
        """
        results = {'parameter': parameter, 'values': values, 'tco_results': []}

        base_vrla_capex = self.vrla_params['capex_per_kwh']
        base_vrla_opex = self.vrla_params['opex_per_kwh_year']
        base_lithium_capex = 200.0
        base_lithium_opex = self.lithium_params['opex_per_kwh_year']

        for value in values:
            # Modify the parameter
            if parameter == 'vrla_capex':
                vrla_tco = self.calculate_tco(value, base_vrla_opex, self.vrla_lifespan)
                lithium_tco = self.calculate_tco(base_lithium_capex, base_lithium_opex, self.lithium_lifespan)
            elif parameter == 'vrla_opex':
                vrla_tco = self.calculate_tco(base_vrla_capex, value, self.vrla_lifespan)
                lithium_tco = self.calculate_tco(base_lithium_capex, base_lithium_opex, self.lithium_lifespan)
            elif parameter == 'lithium_capex':
                vrla_tco = self.calculate_tco(base_vrla_capex, base_vrla_opex, self.vrla_lifespan)
                lithium_tco = self.calculate_tco(value, base_lithium_opex, self.lithium_lifespan)
            elif parameter == 'lithium_opex':
                vrla_tco = self.calculate_tco(base_vrla_capex, base_vrla_opex, self.vrla_lifespan)
                lithium_tco = self.calculate_tco(base_lithium_capex, value, self.lithium_lifespan)
            elif parameter == 'vrla_lifespan':
                vrla_tco = self.calculate_tco(base_vrla_capex, base_vrla_opex, int(value))
                lithium_tco = self.calculate_tco(base_lithium_capex, base_lithium_opex, self.lithium_lifespan)
            elif parameter == 'lithium_lifespan':
                vrla_tco = self.calculate_tco(base_vrla_capex, base_vrla_opex, self.vrla_lifespan)
                lithium_tco = self.calculate_tco(base_lithium_capex, base_lithium_opex, int(value))
            elif parameter == 'discount_rate':
                # Temporarily modify discount rate
                original_rate = self.discount_rate
                self.discount_rate = value
                vrla_tco = self.calculate_tco(base_vrla_capex, base_vrla_opex, self.vrla_lifespan)
                lithium_tco = self.calculate_tco(base_lithium_capex, base_lithium_opex, self.lithium_lifespan)
                self.discount_rate = original_rate
            else:
                raise ValueError(f"Unknown parameter: {parameter}")

            advantage = vrla_tco - lithium_tco

            results['tco_results'].append({
                'value': value,
                'vrla_tco': vrla_tco,
                'lithium_tco': lithium_tco,
                'advantage': advantage,
                'lithium_favorable': advantage > 0
            })

        return results

    def find_tipping_point(self, cost_trajectory_vrla: Dict[int, float],
                            cost_trajectory_lithium: Dict[int, float]) -> Optional[int]:
        """
        Find the tipping point year when Li-ion becomes cheaper

        Args:
            cost_trajectory_vrla: VRLA costs by year
            cost_trajectory_lithium: Li-ion costs by year

        Returns:
            Tipping point year or None
        """
        years = sorted(set(cost_trajectory_vrla.keys()) & set(cost_trajectory_lithium.keys()))

        for year in years:
            vrla_tco = self.calculate_tco(
                cost_trajectory_vrla[year],
                self.vrla_params['opex_per_kwh_year'],
                self.vrla_lifespan
            )

            lithium_tco = self.calculate_tco(
                cost_trajectory_lithium[year],
                self.lithium_params['opex_per_kwh_year'],
                self.lithium_lifespan
            )

            if lithium_tco < vrla_tco:
                # Check persistence (3 consecutive years)
                persistence_years = self.config['default_parameters'].get('tipping_persistence_years', 3)
                if self._check_persistence(year, years, cost_trajectory_vrla, cost_trajectory_lithium, persistence_years):
                    return year

        return None

    def _check_persistence(self, start_year: int, years: list, vrla_costs: Dict, lithium_costs: Dict,
                           persistence: int) -> bool:
        """Check if advantage persists for required years"""
        start_idx = years.index(start_year)
        if start_idx + persistence > len(years):
            return False  # Not enough future years to check

        for i in range(persistence):
            year = years[start_idx + i]
            vrla_tco = self.calculate_tco(vrla_costs[year], self.vrla_params['opex_per_kwh_year'], self.vrla_lifespan)
            lithium_tco = self.calculate_tco(lithium_costs[year], self.lithium_params['opex_per_kwh_year'],
                                              self.lithium_lifespan)
            if lithium_tco >= vrla_tco:
                return False

        return True

    def validate_regional_tco(self, region: str) -> Dict:
        """Validate TCO for a specific region"""
        regional_multiplier = self.vrla_params['regional_multipliers'].get(region, 1.0)

        vrla_capex_regional = self.vrla_params['capex_per_kwh'] * regional_multiplier
        vrla_tco = self.calculate_tco(vrla_capex_regional, self.vrla_params['opex_per_kwh_year'], self.vrla_lifespan)

        # Li-ion costs would come from regional data
        lithium_capex = 200.0  # Placeholder - should load from regional data
        lithium_tco = self.calculate_tco(lithium_capex, self.lithium_params['opex_per_kwh_year'],
                                          self.lithium_lifespan)

        return {
            'region': region,
            'vrla_capex': vrla_capex_regional,
            'vrla_tco': vrla_tco,
            'lithium_capex': lithium_capex,
            'lithium_tco': lithium_tco,
            'advantage': vrla_tco - lithium_tco,
            'multiplier_applied': regional_multiplier
        }

    def print_validation_report(self, results: Dict):
        """Print formatted validation report"""
        print("\n" + "=" * 70)
        print("TCO VALIDATION REPORT")
        print("=" * 70)

        print(f"\nConfiguration:")
        print(f"  TCO Horizon: {self.tco_horizon} years")
        print(f"  Discount Rate: {self.discount_rate * 100:.1f}%")

        if 'vrla' in results:
            print(f"\nVRLA Technology:")
            print(f"  CapEx: ${results['vrla']['capex']:.2f}/kWh")
            print(f"  OpEx: ${results['vrla']['opex']:.2f}/kWh-year")
            print(f"  Lifespan: {results['vrla']['lifespan']} years")
            print(f"  TCO: ${results['vrla']['tco']:.2f}/kWh")

            breakdown = results['vrla']['breakdown']
            print(f"  Breakdown:")
            print(f"    Initial CapEx: ${breakdown['initial_capex']:.2f}")
            print(f"    NPV OpEx: ${breakdown['npv_opex']:.2f}")
            print(f"    NPV Replacements: ${breakdown['npv_replacements']:.2f}")
            if breakdown['replacements']:
                print(f"    Replacements: {len(breakdown['replacements'])} " +
                      f"(Years: {', '.join(str(r['year']) for r in breakdown['replacements'])})")

        if 'lithium' in results:
            print(f"\nLi-ion Technology:")
            print(f"  CapEx: ${results['lithium']['capex']:.2f}/kWh")
            print(f"  OpEx: ${results['lithium']['opex']:.2f}/kWh-year")
            print(f"  Lifespan: {results['lithium']['lifespan']} years")
            print(f"  TCO: ${results['lithium']['tco']:.2f}/kWh")

            breakdown = results['lithium']['breakdown']
            print(f"  Breakdown:")
            print(f"    Initial CapEx: ${breakdown['initial_capex']:.2f}")
            print(f"    NPV OpEx: ${breakdown['npv_opex']:.2f}")
            print(f"    NPV Replacements: ${breakdown['npv_replacements']:.2f}")
            if breakdown['replacements']:
                print(f"    Replacements: {len(breakdown['replacements'])} " +
                      f"(Years: {', '.join(str(r['year']) for r in breakdown['replacements'])})")

        if 'advantage' in results:
            print(f"\nTCO Comparison:")
            print(f"  Li-ion Advantage: ${results['advantage']:.2f}/kWh")
            print(f"  Advantage %: {results['advantage_pct']:.1f}%")
            if results['advantage'] > 0:
                print(f"  ✓ Li-ion is more economical")
            else:
                print(f"  ✗ VRLA is more economical")

        print("\n" + "=" * 70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Validate TCO calculations for datacenter UPS batteries')
    parser.add_argument('--config', type=str, help='Path to config.json')
    parser.add_argument('--region', type=str, help='Validate for specific region')
    parser.add_argument('--sensitivity', type=str, help='Run sensitivity analysis on parameter')
    parser.add_argument('--sensitivity-values', type=str, help='Comma-separated values for sensitivity')
    parser.add_argument('--output', type=str, help='Save results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Initialize validator
    validator = TCOValidator(args.config)

    # Run validation
    results = validator.validate_tco_calculation()

    # Regional validation if specified
    if args.region:
        regional_results = validator.validate_regional_tco(args.region)
        results['regional'] = regional_results

    # Sensitivity analysis if requested
    if args.sensitivity:
        values = [float(v) for v in args.sensitivity_values.split(',')] if args.sensitivity_values else None
        if values:
            sensitivity_results = validator.sensitivity_analysis(args.sensitivity, values)
            results['sensitivity'] = sensitivity_results

            print(f"\nSensitivity Analysis: {args.sensitivity}")
            print("-" * 50)
            for item in sensitivity_results['tco_results']:
                print(f"  {args.sensitivity}={item['value']}: " +
                      f"Advantage=${item['advantage']:.2f} " +
                      f"({'Li-ion favorable' if item['lithium_favorable'] else 'VRLA favorable'})")

    # Print report
    validator.print_validation_report(results)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {output_path}")

    # Return status
    if 'advantage' in results:
        return 0 if results['advantage'] > 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())