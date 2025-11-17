#!/usr/bin/env python3
"""
Sensitivity Analysis and Stress Testing for Lead Demand Forecasting
Tests forecast robustness to parameter variations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from datetime import datetime
from copy import deepcopy

# Import the forecasting engine
sys.path.append(str(Path(__file__).parent))
from forecast import LeadDemandForecast


class SensitivityAnalyzer:
    """Perform sensitivity analysis and stress testing"""

    def __init__(self, config_path, data_dir):
        """Initialize with config and data directory"""
        with open(config_path, 'r') as f:
            self.base_config = json.load(f)

        self.data_dir = Path(data_dir)
        self.config_path = Path(config_path)
        self.sensitivity_results = {}

    def run_baseline(self, region='Global', scenario='baseline'):
        """Run baseline forecast for comparison"""
        print(f"\n{'='*70}")
        print(f"Running Baseline Scenario")
        print(f"{'='*70}\n")

        forecaster = LeadDemandForecast(
            config_path=str(self.config_path),
            region=region,
            scenario=scenario
        )

        forecaster.load_data()
        forecaster.forecast_demand()

        baseline_demand = forecaster.results['total_lead_demand_kt'].iloc[-1]
        print(f"Baseline final year demand: {baseline_demand:.1f} kt\n")

        return forecaster.results, baseline_demand

    def test_parameter_sensitivity(self, region, scenario, parameter_path, variations):
        """
        Test sensitivity to a specific parameter

        Args:
            region: Region to forecast
            scenario: Scenario name
            parameter_path: Path to parameter in config (e.g., ['lead_coefficients', 'sli_batteries', 'passenger_car', 'ice'])
            variations: List of variation factors (e.g., [0.8, 0.9, 1.1, 1.2] for ±20%)

        Returns:
            dict: Sensitivity test results
        """
        param_name = "_".join(parameter_path)
        print(f"\nTesting sensitivity to: {param_name}")

        results = {
            'parameter': param_name,
            'variations': [],
            'demands': [],
            'changes_pct': []
        }

        # Get baseline value
        baseline_value = self.base_config
        for key in parameter_path:
            baseline_value = baseline_value[key]

        print(f"Baseline value: {baseline_value}")

        for variation in variations:
            # Create modified config
            modified_config = deepcopy(self.base_config)
            config_ref = modified_config
            for key in parameter_path[:-1]:
                config_ref = config_ref[key]
            config_ref[parameter_path[-1]] = baseline_value * variation

            new_value = baseline_value * variation
            print(f"\n  Testing {variation:.0%} variation ({new_value:.2f})...")

            # Save temporary config
            temp_config_path = Path(self.config_path).parent / 'temp_config.json'
            with open(temp_config_path, 'w') as f:
                json.dump(modified_config, f, indent=2)

            # Run forecast
            try:
                forecaster = LeadDemandForecast(
                    config_path=str(temp_config_path),
                    region=region,
                    scenario=scenario
                )

                forecaster.load_data()
                forecaster.forecast_demand()

                final_demand = forecaster.results['total_lead_demand_kt'].iloc[-1]
                results['variations'].append(variation)
                results['demands'].append(final_demand)

                print(f"    Final demand: {final_demand:.1f} kt")

            except Exception as e:
                print(f"    Error: {e}")

            # Clean up temp config
            if temp_config_path.exists():
                temp_config_path.unlink()

        # Calculate baseline impact
        if results['demands'] and 1.0 in variations:
            baseline_idx = variations.index(1.0)
            baseline_demand = results['demands'][baseline_idx]

            for demand in results['demands']:
                change_pct = ((demand - baseline_demand) / baseline_demand) * 100
                results['changes_pct'].append(change_pct)

        return results

    def run_stress_tests(self, region='Global', scenario='baseline'):
        """
        Run comprehensive stress tests on key parameters

        Returns:
            dict: Stress test results
        """
        print(f"\n{'='*70}")
        print(f"STRESS TESTING AND SENSITIVITY ANALYSIS")
        print(f"{'='*70}\n")

        # Run baseline
        baseline_results, baseline_demand = self.run_baseline(region, scenario)

        stress_tests = {}

        # Define stress test scenarios
        test_parameters = [
            {
                'name': 'Passenger Car ICE Coefficient',
                'path': ['lead_coefficients', 'sli_batteries', 'passenger_car', 'ice'],
                'variations': [0.8, 0.9, 1.0, 1.1, 1.2]  # ±20%
            },
            {
                'name': 'Passenger Car BEV Coefficient',
                'path': ['lead_coefficients', 'sli_batteries', 'passenger_car', 'bev'],
                'variations': [0.8, 0.9, 1.0, 1.1, 1.2]
            },
            {
                'name': 'SLI Battery Lifetime',
                'path': ['battery_lifetimes', 'sli_years'],
                'variations': [0.8, 0.9, 1.0, 1.1, 1.2]  # 3.6 to 5.4 years
            },
            {
                'name': 'Passenger Car Asset Lifetime',
                'path': ['asset_lifetimes', 'passenger_car_years'],
                'variations': [0.8, 0.9, 1.0, 1.1, 1.2]  # 14.4 to 21.6 years
            },
            {
                'name': 'Industrial Motive Coefficient',
                'path': ['lead_coefficients', 'industrial_batteries', 'motive_kg_per_unit'],
                'variations': [0.8, 0.9, 1.0, 1.1, 1.2]
            },
            {
                'name': 'Other Uses Price Elasticity',
                'path': ['econometric_parameters', 'other_uses_price_elasticity'],
                'variations': [0.5, 0.75, 1.0, 1.25, 1.5]  # -0.15 to -0.45
            }
        ]

        # Run tests
        for test_spec in test_parameters:
            results = self.test_parameter_sensitivity(
                region,
                scenario,
                test_spec['path'],
                test_spec['variations']
            )
            stress_tests[test_spec['name']] = results

        # Store results
        self.sensitivity_results = {
            'baseline_demand': baseline_demand,
            'tests': stress_tests
        }

        return self.sensitivity_results

    def generate_sensitivity_report(self, output_path=None):
        """Generate sensitivity analysis report"""
        if not self.sensitivity_results:
            print("⚠️  No sensitivity results available")
            return

        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("SENSITIVITY ANALYSIS AND STRESS TESTING REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Baseline Final Year Demand: {self.sensitivity_results['baseline_demand']:.1f} kt")
        report_lines.append("")

        # Summary of sensitivity
        report_lines.append("PARAMETER SENSITIVITY SUMMARY:")
        report_lines.append("-" * 80)

        for param_name, results in self.sensitivity_results['tests'].items():
            if not results['changes_pct']:
                continue

            # Calculate elasticity: % change in output / % change in input
            max_change = max(abs(c) for c in results['changes_pct'])
            max_input_variation = max(abs(v - 1.0) for v in results['variations']) * 100

            if max_input_variation > 0:
                elasticity = max_change / max_input_variation
            else:
                elasticity = 0

            report_lines.append(f"\n{param_name}:")
            report_lines.append(f"  Max impact: {max_change:+.1f}% change in final demand")
            report_lines.append(f"  Elasticity: {elasticity:.2f}")

            sensitivity_category = "HIGH" if elasticity > 0.5 else "MEDIUM" if elasticity > 0.2 else "LOW"
            report_lines.append(f"  Sensitivity: {sensitivity_category}")

        # Detailed results
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("DETAILED STRESS TEST RESULTS:")
        report_lines.append("-" * 80)

        for param_name, results in self.sensitivity_results['tests'].items():
            report_lines.append(f"\n{param_name}:")
            report_lines.append(f"  Parameter: {results['parameter']}")

            for variation, demand, change_pct in zip(
                results['variations'],
                results['demands'],
                results['changes_pct'] if results['changes_pct'] else [0] * len(results['demands'])
            ):
                report_lines.append(f"    {variation:>5.0%} variation → {demand:>8.1f} kt ({change_pct:>+6.1f}% vs baseline)")

        report_lines.append("\n" + "=" * 80)

        report_text = "\n".join(report_lines)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"\n✓ Sensitivity report saved to: {output_file}")
        else:
            print("\n" + report_text)

        return report_text

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Sensitivity Analysis and Stress Testing')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file (defaults to ../config.json)')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Path to data directory (defaults to ../data)')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to forecast (default: Global)')
    parser.add_argument('--scenario', type=str, default='baseline',
                       help='Scenario name (default: baseline)')
    parser.add_argument('--output-report', type=str, default=None,
                       help='Output path for sensitivity report')

    args = parser.parse_args()

    # Get config path
    if args.config:
        config_path = args.config
    else:
        skill_dir = Path(__file__).parent.parent
        config_path = skill_dir / 'config.json'

    if not Path(config_path).exists():
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)

    # Get data directory
    if args.data_dir:
        data_dir = args.data_dir
    else:
        skill_dir = Path(__file__).parent.parent
        data_dir = skill_dir / 'data'

    if not Path(data_dir).exists():
        print(f"Error: Data directory not found at {data_dir}")
        sys.exit(1)

    # Create analyzer
    analyzer = SensitivityAnalyzer(config_path, data_dir)

    # Run stress tests
    analyzer.run_stress_tests(region=args.region, scenario=args.scenario)

    # Generate report
    if args.output_report:
        analyzer.generate_sensitivity_report(args.output_report)
    else:
        skill_dir = Path(__file__).parent.parent
        default_report = skill_dir / 'output' / f'sensitivity_report_{args.region}_{args.scenario}.txt'
        analyzer.generate_sensitivity_report(default_report)


if __name__ == "__main__":
    main()
