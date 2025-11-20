#!/usr/bin/env python3
"""
Mass Balance Validation Script
Validates stock-flow accounting for installed base calculations
"""

import json
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class MassBalanceValidator:
    """Validates mass balance in installed base accounting"""

    def __init__(self, config_path: str = None):
        """Initialize with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config.json'

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.vrla_lifespan = self.config['lifespans']['vrla_years']
        self.lithium_lifespan = self.config['lifespans']['lithium_years']
        self.tolerance = self.config['validation_rules']['mass_balance_tolerance']

    def validate_mass_balance(self, demand_data: pd.DataFrame,
                             installed_base_data: pd.DataFrame) -> Dict:
        """
        Validate mass balance equation: IB(t+1) = IB(t) + Adds(t) - Retirements(t)

        Args:
            demand_data: DataFrame with columns [year, vrla_demand_gwh, lithium_demand_gwh]
            installed_base_data: DataFrame with columns [year, vrla_installed_base_gwh, lithium_installed_base_gwh]

        Returns:
            Validation results dictionary
        """
        results = {
            'vrla': {'checks': [], 'max_error': 0, 'passed': True},
            'lithium': {'checks': [], 'max_error': 0, 'passed': True},
            'overall_passed': True
        }

        # Validate VRLA mass balance
        vrla_results = self._validate_technology_balance(
            demand_data['vrla_demand_gwh'].values,
            installed_base_data['vrla_installed_base_gwh'].values,
            self.vrla_lifespan,
            demand_data['year'].values,
            'VRLA'
        )
        results['vrla'] = vrla_results

        # Validate Li-ion mass balance
        lithium_results = self._validate_technology_balance(
            demand_data['lithium_demand_gwh'].values,
            installed_base_data['lithium_installed_base_gwh'].values,
            self.lithium_lifespan,
            demand_data['year'].values,
            'Li-ion'
        )
        results['lithium'] = lithium_results

        results['overall_passed'] = vrla_results['passed'] and lithium_results['passed']

        return results

    def _validate_technology_balance(self, demand: np.ndarray, installed_base: np.ndarray,
                                    lifespan: int, years: np.ndarray, tech_name: str) -> Dict:
        """Validate mass balance for a single technology"""
        checks = []
        max_error = 0
        max_error_year = None

        for i in range(1, len(years)):
            year = years[i]

            # Calculate components
            ib_start = installed_base[i-1]
            ib_end = installed_base[i]
            adds = demand[i]
            retirements = ib_start / lifespan  # Simple exponential decay assumption

            # Expected vs actual
            expected_ib_end = ib_start + adds - retirements
            actual_ib_end = ib_end

            # Calculate error
            if actual_ib_end > 0:
                error = abs(expected_ib_end - actual_ib_end) / actual_ib_end
            else:
                error = abs(expected_ib_end - actual_ib_end)

            # Track maximum error
            if error > max_error:
                max_error = error
                max_error_year = year

            # Check if within tolerance
            passed = error <= self.tolerance

            checks.append({
                'year': int(year),
                'ib_start': float(ib_start),
                'adds': float(adds),
                'retirements': float(retirements),
                'expected_ib_end': float(expected_ib_end),
                'actual_ib_end': float(actual_ib_end),
                'error': float(error),
                'error_pct': float(error * 100),
                'passed': passed
            })

        overall_passed = all(check['passed'] for check in checks)

        return {
            'technology': tech_name,
            'lifespan': lifespan,
            'checks': checks,
            'max_error': float(max_error),
            'max_error_pct': float(max_error * 100),
            'max_error_year': int(max_error_year) if max_error_year else None,
            'passed': overall_passed,
            'tolerance': self.tolerance
        }

    def check_retirement_rates(self, installed_base_data: pd.DataFrame) -> Dict:
        """
        Validate retirement rates are consistent with lifespans

        Args:
            installed_base_data: DataFrame with installed base data

        Returns:
            Retirement rate validation results
        """
        results = {}

        # VRLA retirement rate check
        vrla_ib = installed_base_data['vrla_installed_base_gwh'].values
        vrla_retirements = vrla_ib[:-1] / self.vrla_lifespan
        expected_rate = 1.0 / self.vrla_lifespan

        results['vrla'] = {
            'expected_rate': expected_rate,
            'expected_rate_pct': expected_rate * 100,
            'actual_rates': [],
            'lifespan': self.vrla_lifespan
        }

        for i in range(len(vrla_retirements)):
            if vrla_ib[i] > 0:
                actual_rate = vrla_retirements[i] / vrla_ib[i]
                results['vrla']['actual_rates'].append({
                    'year': int(installed_base_data['year'].iloc[i]),
                    'rate': float(actual_rate),
                    'rate_pct': float(actual_rate * 100),
                    'retirements': float(vrla_retirements[i]),
                    'installed_base': float(vrla_ib[i])
                })

        # Li-ion retirement rate check
        lithium_ib = installed_base_data['lithium_installed_base_gwh'].values
        lithium_retirements = lithium_ib[:-1] / self.lithium_lifespan
        expected_rate = 1.0 / self.lithium_lifespan

        results['lithium'] = {
            'expected_rate': expected_rate,
            'expected_rate_pct': expected_rate * 100,
            'actual_rates': [],
            'lifespan': self.lithium_lifespan
        }

        for i in range(len(lithium_retirements)):
            if lithium_ib[i] > 0:
                actual_rate = lithium_retirements[i] / lithium_ib[i]
                results['lithium']['actual_rates'].append({
                    'year': int(installed_base_data['year'].iloc[i]),
                    'rate': float(actual_rate),
                    'rate_pct': float(actual_rate * 100),
                    'retirements': float(lithium_retirements[i]),
                    'installed_base': float(lithium_ib[i])
                })

        return results

    def check_stock_flow_consistency(self, demand_data: pd.DataFrame,
                                    installed_base_data: pd.DataFrame) -> Dict:
        """
        Check if cumulative flows match stock changes

        Args:
            demand_data: Demand (flow) data
            installed_base_data: Installed base (stock) data

        Returns:
            Stock-flow consistency results
        """
        results = {}

        # VRLA stock-flow check
        vrla_demand_cumulative = demand_data['vrla_demand_gwh'].cumsum().iloc[-1]
        vrla_ib_change = (installed_base_data['vrla_installed_base_gwh'].iloc[-1] -
                         installed_base_data['vrla_installed_base_gwh'].iloc[0])

        # Estimate total retirements (simplified)
        avg_vrla_ib = installed_base_data['vrla_installed_base_gwh'].mean()
        years_span = len(installed_base_data)
        estimated_vrla_retirements = (avg_vrla_ib / self.vrla_lifespan) * years_span

        results['vrla'] = {
            'cumulative_demand': float(vrla_demand_cumulative),
            'stock_change': float(vrla_ib_change),
            'estimated_retirements': float(estimated_vrla_retirements),
            'implied_retirements': float(vrla_demand_cumulative - vrla_ib_change),
            'consistency_check': abs(vrla_demand_cumulative - vrla_ib_change - estimated_vrla_retirements) <
                               vrla_demand_cumulative * 0.1
        }

        # Li-ion stock-flow check
        lithium_demand_cumulative = demand_data['lithium_demand_gwh'].cumsum().iloc[-1]
        lithium_ib_change = (installed_base_data['lithium_installed_base_gwh'].iloc[-1] -
                           installed_base_data['lithium_installed_base_gwh'].iloc[0])

        avg_lithium_ib = installed_base_data['lithium_installed_base_gwh'].mean()
        estimated_lithium_retirements = (avg_lithium_ib / self.lithium_lifespan) * years_span if avg_lithium_ib > 0 else 0

        results['lithium'] = {
            'cumulative_demand': float(lithium_demand_cumulative),
            'stock_change': float(lithium_ib_change),
            'estimated_retirements': float(estimated_lithium_retirements),
            'implied_retirements': float(lithium_demand_cumulative - lithium_ib_change),
            'consistency_check': abs(lithium_demand_cumulative - lithium_ib_change - estimated_lithium_retirements) <
                                lithium_demand_cumulative * 0.1 if lithium_demand_cumulative > 0 else True
        }

        return results

    def identify_imbalance_sources(self, validation_results: Dict) -> List[Dict]:
        """
        Identify potential sources of mass balance errors

        Args:
            validation_results: Results from validate_mass_balance

        Returns:
            List of identified issues with recommendations
        """
        issues = []

        # Check VRLA issues
        if not validation_results['vrla']['passed']:
            vrla_checks = validation_results['vrla']['checks']

            # Look for systematic errors
            errors = [check['error_pct'] for check in vrla_checks]
            if all(e > 0 for e in errors):
                issues.append({
                    'technology': 'VRLA',
                    'issue': 'Systematic overestimation',
                    'description': 'Installed base consistently higher than expected',
                    'recommendation': 'Check if retirement rate is too low or demand is underestimated'
                })
            elif all(e < 0 for e in errors):
                issues.append({
                    'technology': 'VRLA',
                    'issue': 'Systematic underestimation',
                    'description': 'Installed base consistently lower than expected',
                    'recommendation': 'Check if retirement rate is too high or demand is overestimated'
                })

            # Check for large jumps
            for i in range(1, len(vrla_checks)):
                if abs(vrla_checks[i]['error_pct'] - vrla_checks[i-1]['error_pct']) > 5:
                    issues.append({
                        'technology': 'VRLA',
                        'issue': f"Large error jump in year {vrla_checks[i]['year']}",
                        'description': f"Error changed from {vrla_checks[i-1]['error_pct']:.1f}% to {vrla_checks[i]['error_pct']:.1f}%",
                        'recommendation': 'Check data quality for this specific year'
                    })

        # Check Li-ion issues
        if not validation_results['lithium']['passed']:
            lithium_checks = validation_results['lithium']['checks']

            # Check for early-stage issues (common with Li-ion)
            early_errors = [check['error_pct'] for check in lithium_checks[:3]]
            if any(e > 10 for e in early_errors):
                issues.append({
                    'technology': 'Li-ion',
                    'issue': 'Early-stage initialization error',
                    'description': 'Large errors in initial years when installed base is small',
                    'recommendation': 'Consider initializing Li-ion IB from historical demand or use relative tolerance'
                })

        return issues

    def generate_reconciliation_adjustments(self, validation_results: Dict) -> Dict:
        """
        Generate adjustments to reconcile mass balance

        Args:
            validation_results: Results from validation

        Returns:
            Suggested adjustments
        """
        adjustments = {'vrla': [], 'lithium': []}

        for tech in ['vrla', 'lithium']:
            if not validation_results[tech]['passed']:
                for check in validation_results[tech]['checks']:
                    if not check['passed']:
                        # Calculate adjustment needed
                        adjustment = check['actual_ib_end'] - check['expected_ib_end']

                        adjustments[tech].append({
                            'year': check['year'],
                            'current_ib': check['actual_ib_end'],
                            'expected_ib': check['expected_ib_end'],
                            'adjustment_needed': adjustment,
                            'adjustment_pct': (adjustment / check['actual_ib_end'] * 100) if check['actual_ib_end'] > 0 else 0
                        })

        return adjustments

    def print_validation_report(self, results: Dict):
        """Print formatted validation report"""
        print("\n" + "=" * 70)
        print("MASS BALANCE VALIDATION REPORT")
        print("=" * 70)

        for tech in ['vrla', 'lithium']:
            if tech in results:
                tech_results = results[tech]
                status = "✓ PASS" if tech_results['passed'] else "✗ FAIL"

                print(f"\n{tech_results['technology']} Technology: {status}")
                print(f"  Lifespan: {tech_results['lifespan']} years")
                print(f"  Tolerance: {tech_results['tolerance']*100:.1f}%")
                print(f"  Max Error: {tech_results['max_error_pct']:.2f}% (Year {tech_results['max_error_year']})")

                if not tech_results['passed']:
                    print(f"\n  Failed Years:")
                    for check in tech_results['checks']:
                        if not check['passed']:
                            print(f"    Year {check['year']}: Error {check['error_pct']:.2f}%")
                            print(f"      Expected IB: {check['expected_ib_end']:.2f} GWh")
                            print(f"      Actual IB: {check['actual_ib_end']:.2f} GWh")

        if 'retirement_rates' in results:
            print("\n" + "-" * 70)
            print("RETIREMENT RATE ANALYSIS")
            print("-" * 70)

            for tech in ['vrla', 'lithium']:
                if tech in results['retirement_rates']:
                    rates = results['retirement_rates'][tech]
                    print(f"\n{tech.upper()}:")
                    print(f"  Expected Rate: {rates['expected_rate_pct']:.1f}%/year")
                    if rates['actual_rates']:
                        actual_rates = [r['rate_pct'] for r in rates['actual_rates']]
                        print(f"  Actual Rates: {min(actual_rates):.1f}% - {max(actual_rates):.1f}%/year")

        if 'stock_flow' in results:
            print("\n" + "-" * 70)
            print("STOCK-FLOW CONSISTENCY")
            print("-" * 70)

            for tech in ['vrla', 'lithium']:
                if tech in results['stock_flow']:
                    sf = results['stock_flow'][tech]
                    status = "✓" if sf['consistency_check'] else "✗"
                    print(f"\n{tech.upper()}: {status}")
                    print(f"  Cumulative Demand: {sf['cumulative_demand']:.2f} GWh")
                    print(f"  Stock Change: {sf['stock_change']:.2f} GWh")
                    print(f"  Implied Retirements: {sf['implied_retirements']:.2f} GWh")

        if 'issues' in results and results['issues']:
            print("\n" + "-" * 70)
            print("IDENTIFIED ISSUES")
            print("-" * 70)

            for issue in results['issues']:
                print(f"\n• {issue['technology']}: {issue['issue']}")
                print(f"  {issue['description']}")
                print(f"  → {issue['recommendation']}")

        print("\n" + "=" * 70)

        overall_status = "✓ VALIDATION PASSED" if results.get('overall_passed', False) else "✗ VALIDATION FAILED"
        print(f"OVERALL STATUS: {overall_status}")
        print("=" * 70)


def load_forecast_data(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load forecast data from CSV file"""
    df = pd.read_csv(file_path)

    # Extract demand data
    demand_cols = ['year', 'vrla_demand_gwh', 'lithium_demand_gwh']
    demand_data = df[demand_cols].copy()

    # Extract installed base data
    ib_cols = ['year', 'vrla_installed_base_gwh', 'lithium_installed_base_gwh']
    if all(col in df.columns for col in ib_cols[1:]):
        ib_data = df[ib_cols].copy()
    else:
        # If IB columns don't exist, create placeholder
        ib_data = pd.DataFrame({
            'year': df['year'],
            'vrla_installed_base_gwh': 0,
            'lithium_installed_base_gwh': 0
        })

    return demand_data, ib_data


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Validate mass balance in datacenter UPS forecasts')
    parser.add_argument('--input', type=str, help='Path to forecast CSV file')
    parser.add_argument('--config', type=str, help='Path to config.json')
    parser.add_argument('--check-retirement', action='store_true', help='Check retirement rates')
    parser.add_argument('--check-stock-flow', action='store_true', help='Check stock-flow consistency')
    parser.add_argument('--identify-issues', action='store_true', help='Identify imbalance sources')
    parser.add_argument('--suggest-adjustments', action='store_true', help='Generate reconciliation adjustments')
    parser.add_argument('--output', type=str, help='Save results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Initialize validator
    validator = MassBalanceValidator(args.config)

    # Load forecast data
    if args.input:
        demand_data, ib_data = load_forecast_data(args.input)

        # Run validation
        results = validator.validate_mass_balance(demand_data, ib_data)

        # Additional checks if requested
        if args.check_retirement:
            results['retirement_rates'] = validator.check_retirement_rates(ib_data)

        if args.check_stock_flow:
            results['stock_flow'] = validator.check_stock_flow_consistency(demand_data, ib_data)

        if args.identify_issues:
            results['issues'] = validator.identify_imbalance_sources(results)

        if args.suggest_adjustments:
            results['adjustments'] = validator.generate_reconciliation_adjustments(results)

        # Print report
        validator.print_validation_report(results)

        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=lambda x: float(x) if isinstance(x, np.number) else x)
            print(f"\n✓ Results saved to: {output_path}")

        # Return status
        return 0 if results.get('overall_passed', False) else 1
    else:
        print("Error: Please provide input file with --input")
        return 1


if __name__ == "__main__":
    sys.exit(main())