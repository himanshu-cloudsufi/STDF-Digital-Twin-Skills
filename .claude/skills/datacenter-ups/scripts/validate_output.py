#!/usr/bin/env python3
"""
Output Validation Script
Validates forecast output files for consistency, completeness, and correctness
"""

import json
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


class OutputValidator:
    """Validates forecast output files"""

    def __init__(self, config_path: str = None):
        """Initialize with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config.json'

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.required_columns = self._get_required_columns()
        self.validation_rules = self.config['validation_rules']

    def _get_required_columns(self) -> Dict[str, List[str]]:
        """Define required columns for different output types"""
        return {
            'core': [
                'year', 'region', 'scenario',
                'total_demand_gwh', 'vrla_demand_gwh', 'lithium_demand_gwh',
                'vrla_share_pct', 'lithium_share_pct'
            ],
            'tco': [
                'vrla_capex_per_kwh', 'lithium_capex_per_kwh',
                'vrla_tco_per_kwh', 'lithium_tco_per_kwh',
                'tco_advantage'
            ],
            'installed_base': [
                'vrla_installed_base_gwh', 'lithium_installed_base_gwh',
                'total_installed_base_gwh'
            ],
            'market_decomposition': [
                'new_build_demand_gwh', 'replacement_demand_gwh',
                'contestable_market_gwh'
            ],
            'battery_metrics': [
                'power_capacity_mw', 'annual_throughput_gwh'
            ]
        }

    def validate_csv_output(self, file_path: str) -> Dict:
        """
        Validate CSV output file

        Args:
            file_path: Path to CSV file

        Returns:
            Validation results
        """
        results = {
            'file_path': file_path,
            'format': 'csv',
            'checks': {},
            'overall_passed': True
        }

        try:
            # Load CSV
            df = pd.read_csv(file_path)
            results['rows'] = len(df)
            results['columns'] = list(df.columns)

            # Check required columns
            results['checks']['required_columns'] = self._check_required_columns(df)

            # Check data types
            results['checks']['data_types'] = self._check_data_types(df)

            # Check value ranges
            results['checks']['value_ranges'] = self._check_value_ranges(df)

            # Check consistency rules
            results['checks']['consistency'] = self._check_consistency(df)

            # Check monotonicity
            results['checks']['monotonicity'] = self._check_monotonicity(df)

            # Check non-negativity
            results['checks']['non_negativity'] = self._check_non_negativity(df)

            # Calculate overall status
            results['overall_passed'] = all(
                check['passed'] for check in results['checks'].values()
            )

        except Exception as e:
            results['error'] = str(e)
            results['overall_passed'] = False

        return results

    def validate_json_output(self, file_path: str) -> Dict:
        """
        Validate JSON output file

        Args:
            file_path: Path to JSON file

        Returns:
            Validation results
        """
        results = {
            'file_path': file_path,
            'format': 'json',
            'checks': {},
            'overall_passed': True
        }

        try:
            # Load JSON
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Check required sections
            results['checks']['required_sections'] = self._check_json_sections(data)

            # Check metadata
            results['checks']['metadata'] = self._check_json_metadata(data)

            # Check forecast data
            if 'forecast' in data:
                results['checks']['forecast_data'] = self._validate_json_forecast(data['forecast'])

            # Check analysis section
            if 'analysis' in data:
                results['checks']['analysis'] = self._validate_json_analysis(data['analysis'])

            # Calculate overall status
            results['overall_passed'] = all(
                check['passed'] for check in results['checks'].values()
            )

        except Exception as e:
            results['error'] = str(e)
            results['overall_passed'] = False

        return results

    def _check_required_columns(self, df: pd.DataFrame) -> Dict:
        """Check if required columns are present"""
        missing_core = []
        for col in self.required_columns['core']:
            if col not in df.columns:
                missing_core.append(col)

        optional_missing = {}
        for category in ['tco', 'installed_base', 'market_decomposition', 'battery_metrics']:
            missing = [col for col in self.required_columns[category] if col not in df.columns]
            if missing:
                optional_missing[category] = missing

        return {
            'core_columns_present': len(missing_core) == 0,
            'missing_core': missing_core,
            'optional_missing': optional_missing,
            'passed': len(missing_core) == 0
        }

    def _check_data_types(self, df: pd.DataFrame) -> Dict:
        """Check data types of columns"""
        issues = []

        # Check year is integer or can be converted
        if 'year' in df.columns:
            try:
                df['year'].astype(int)
            except:
                issues.append("'year' column cannot be converted to integer")

        # Check numeric columns
        numeric_columns = [col for col in df.columns if col.endswith(('_gwh', '_mwh', '_mw', '_pct', '_per_kwh'))]
        for col in numeric_columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    issues.append(f"'{col}' is not numeric")

        # Check string columns
        string_columns = ['region', 'scenario', 'tipping_year']
        for col in string_columns:
            if col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]) and col != 'tipping_year':
                    issues.append(f"'{col}' should be string")

        return {
            'issues': issues,
            'passed': len(issues) == 0
        }

    def _check_value_ranges(self, df: pd.DataFrame) -> Dict:
        """Check if values are within expected ranges"""
        issues = []

        # Check percentages (0-100)
        pct_columns = [col for col in df.columns if col.endswith('_pct')]
        for col in pct_columns:
            if col in df.columns:
                if df[col].min() < 0 or df[col].max() > 100:
                    issues.append(f"'{col}' has values outside 0-100 range")

        # Check shares sum to 100%
        if 'vrla_share_pct' in df.columns and 'lithium_share_pct' in df.columns:
            share_sum = df['vrla_share_pct'] + df['lithium_share_pct']
            if abs(share_sum - 100).max() > 0.1:
                issues.append("VRLA + Li-ion shares don't sum to 100%")

        # Check years are reasonable
        if 'year' in df.columns:
            if df['year'].min() < 2010 or df['year'].max() > 2050:
                issues.append(f"Years outside reasonable range (2010-2050)")

        # Check demand values are reasonable (0-10000 GWh)
        demand_columns = [col for col in df.columns if 'demand_gwh' in col]
        for col in demand_columns:
            if col in df.columns:
                if df[col].min() < 0:
                    issues.append(f"'{col}' has negative values")
                if df[col].max() > 10000:
                    issues.append(f"'{col}' has unreasonably large values (>10,000 GWh)")

        return {
            'issues': issues,
            'passed': len(issues) == 0
        }

    def _check_consistency(self, df: pd.DataFrame) -> Dict:
        """Check internal consistency of data"""
        issues = []

        # Check demand consistency
        if all(col in df.columns for col in ['total_demand_gwh', 'vrla_demand_gwh', 'lithium_demand_gwh']):
            calculated_total = df['vrla_demand_gwh'] + df['lithium_demand_gwh']
            error = abs(calculated_total - df['total_demand_gwh']) / df['total_demand_gwh']
            max_error = error.max()
            tolerance = self.validation_rules.get('total_demand_tolerance', 0.05)

            if max_error > tolerance:
                issues.append(f"Demand consistency error: max {max_error*100:.1f}% exceeds {tolerance*100}% tolerance")

        # Check installed base consistency
        if all(col in df.columns for col in ['total_installed_base_gwh', 'vrla_installed_base_gwh', 'lithium_installed_base_gwh']):
            calculated_ib = df['vrla_installed_base_gwh'] + df['lithium_installed_base_gwh']
            error = abs(calculated_ib - df['total_installed_base_gwh']) / df['total_installed_base_gwh']
            if error.max() > 0.01:
                issues.append(f"Installed base sum error: max {error.max()*100:.1f}%")

        # Check market decomposition consistency
        if all(col in df.columns for col in ['total_demand_gwh', 'new_build_demand_gwh', 'replacement_demand_gwh']):
            decomposed = df['new_build_demand_gwh'] + df['replacement_demand_gwh']
            error = abs(decomposed - df['total_demand_gwh']) / df['total_demand_gwh']
            if error.max() > 0.15:  # 15% tolerance for market decomposition
                issues.append(f"Market decomposition error: max {error.max()*100:.1f}% exceeds 15% tolerance")

        # Check TCO advantage calculation
        if all(col in df.columns for col in ['vrla_tco_per_kwh', 'lithium_tco_per_kwh', 'tco_advantage']):
            calculated_advantage = df['vrla_tco_per_kwh'] - df['lithium_tco_per_kwh']
            error = abs(calculated_advantage - df['tco_advantage'])
            if error.max() > 1.0:  # $1/kWh tolerance
                issues.append(f"TCO advantage calculation error: max ${error.max():.2f}/kWh")

        return {
            'issues': issues,
            'passed': len(issues) == 0
        }

    def _check_monotonicity(self, df: pd.DataFrame) -> Dict:
        """Check if adoption is monotonically increasing"""
        issues = []

        if 'lithium_share_pct' in df.columns:
            # Sort by year to ensure proper order
            df_sorted = df.sort_values('year')
            lithium_shares = df_sorted['lithium_share_pct'].values

            # Check monotonicity
            is_monotonic = all(lithium_shares[i] <= lithium_shares[i+1] for i in range(len(lithium_shares)-1))

            if not is_monotonic and self.validation_rules.get('monotonic_adoption', True):
                # Find where it decreases
                for i in range(len(lithium_shares)-1):
                    if lithium_shares[i] > lithium_shares[i+1]:
                        year_curr = df_sorted['year'].iloc[i]
                        year_next = df_sorted['year'].iloc[i+1]
                        issues.append(f"Li-ion share decreases from {lithium_shares[i]:.1f}% ({year_curr}) to {lithium_shares[i+1]:.1f}% ({year_next})")

        return {
            'is_monotonic': len(issues) == 0,
            'issues': issues,
            'passed': len(issues) == 0 or not self.validation_rules.get('monotonic_adoption', True)
        }

    def _check_non_negativity(self, df: pd.DataFrame) -> Dict:
        """Check if all values that should be non-negative are"""
        negative_columns = []

        # Check all numeric columns except those that can be negative (like tco_advantage)
        exclude_columns = ['tco_advantage', 'error', 'difference']
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            if col not in exclude_columns and any(df[col] < 0):
                negative_values = df[col][df[col] < 0]
                negative_columns.append({
                    'column': col,
                    'count': len(negative_values),
                    'min_value': negative_values.min()
                })

        return {
            'negative_columns': negative_columns,
            'passed': len(negative_columns) == 0 or not self.validation_rules.get('non_negativity', True)
        }

    def _check_json_sections(self, data: Dict) -> Dict:
        """Check required JSON sections"""
        required_sections = ['metadata', 'forecast']
        optional_sections = ['analysis']

        missing_required = [sec for sec in required_sections if sec not in data]
        missing_optional = [sec for sec in optional_sections if sec not in data]

        return {
            'required_present': len(missing_required) == 0,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'passed': len(missing_required) == 0
        }

    def _check_json_metadata(self, data: Dict) -> Dict:
        """Check JSON metadata section"""
        issues = []

        if 'metadata' in data:
            metadata = data['metadata']
            required_fields = ['model_version', 'region', 'scenario']

            for field in required_fields:
                if field not in metadata:
                    issues.append(f"Missing metadata field: {field}")

        return {
            'issues': issues,
            'passed': len(issues) == 0
        }

    def _validate_json_forecast(self, forecast: Dict) -> Dict:
        """Validate JSON forecast section"""
        issues = []

        # Check for required subsections
        required_subsections = ['years', 'demand']
        for subsec in required_subsections:
            if subsec not in forecast:
                issues.append(f"Missing forecast subsection: {subsec}")

        # Check array lengths match
        if 'years' in forecast and 'demand' in forecast:
            years_len = len(forecast['years'])
            for key, values in forecast['demand'].items():
                if len(values) != years_len:
                    issues.append(f"Length mismatch: {key} has {len(values)} values but {years_len} years")

        return {
            'issues': issues,
            'passed': len(issues) == 0
        }

    def _validate_json_analysis(self, analysis: Dict) -> Dict:
        """Validate JSON analysis section"""
        issues = []

        # Check tipping point
        if 'tipping_point' in analysis:
            tp = analysis['tipping_point']
            if 'year' in tp and tp['year'] != 'N/A':
                if not (2010 <= tp['year'] <= 2050):
                    issues.append(f"Tipping point year {tp['year']} outside reasonable range")

        # Check validation status
        if 'validation' in analysis:
            val = analysis['validation']
            for check, status in val.items():
                if isinstance(status, dict) and 'status' in status:
                    if status['status'] not in ['pass', 'fail']:
                        issues.append(f"Invalid validation status for {check}: {status['status']}")

        return {
            'issues': issues,
            'passed': len(issues) == 0
        }

    def compare_outputs(self, file1: str, file2: str) -> Dict:
        """
        Compare two output files

        Args:
            file1: Path to first file
            file2: Path to second file

        Returns:
            Comparison results
        """
        results = {'file1': file1, 'file2': file2, 'differences': {}}

        # Load both files
        if file1.endswith('.csv') and file2.endswith('.csv'):
            df1 = pd.read_csv(file1)
            df2 = pd.read_csv(file2)

            # Compare shapes
            results['shape_match'] = df1.shape == df2.shape

            # Compare columns
            cols1 = set(df1.columns)
            cols2 = set(df2.columns)
            results['columns_only_in_file1'] = list(cols1 - cols2)
            results['columns_only_in_file2'] = list(cols2 - cols1)
            results['common_columns'] = list(cols1 & cols2)

            # Compare values for common columns
            for col in results['common_columns']:
                if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                    diff = abs(df1[col] - df2[col])
                    results['differences'][col] = {
                        'max_diff': float(diff.max()),
                        'mean_diff': float(diff.mean()),
                        'max_pct_diff': float((diff / df1[col].abs()).max() * 100) if df1[col].abs().max() > 0 else 0
                    }

        return results

    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for output data"""
        stats = {}

        # Basic info
        stats['rows'] = len(df)
        stats['years'] = {'min': int(df['year'].min()), 'max': int(df['year'].max())} if 'year' in df.columns else None

        # Demand statistics
        if 'total_demand_gwh' in df.columns:
            stats['total_demand'] = {
                'min': float(df['total_demand_gwh'].min()),
                'max': float(df['total_demand_gwh'].max()),
                'mean': float(df['total_demand_gwh'].mean()),
                'final': float(df['total_demand_gwh'].iloc[-1])
            }

        # Li-ion adoption statistics
        if 'lithium_share_pct' in df.columns:
            stats['lithium_adoption'] = {
                'initial': float(df['lithium_share_pct'].iloc[0]),
                'final': float(df['lithium_share_pct'].iloc[-1]),
                'max': float(df['lithium_share_pct'].max()),
                'years_to_50pct': None
            }

            # Find year when Li-ion crosses 50%
            for i, share in enumerate(df['lithium_share_pct']):
                if share >= 50:
                    stats['lithium_adoption']['years_to_50pct'] = int(df['year'].iloc[i])
                    break

        # TCO statistics
        if 'tco_advantage' in df.columns:
            stats['tco_advantage'] = {
                'min': float(df['tco_advantage'].min()),
                'max': float(df['tco_advantage'].max()),
                'final': float(df['tco_advantage'].iloc[-1])
            }

        # Tipping point
        if 'tipping_year' in df.columns:
            unique_tipping = df['tipping_year'].unique()
            if len(unique_tipping) == 1:
                stats['tipping_year'] = unique_tipping[0] if unique_tipping[0] != 'N/A' else None

        return stats

    def print_validation_report(self, results: Dict):
        """Print formatted validation report"""
        print("\n" + "=" * 70)
        print("OUTPUT VALIDATION REPORT")
        print("=" * 70)

        print(f"\nFile: {results['file_path']}")
        print(f"Format: {results['format']}")

        if 'error' in results:
            print(f"\n✗ ERROR: {results['error']}")
        else:
            if 'rows' in results:
                print(f"Rows: {results['rows']}")
            if 'columns' in results:
                print(f"Columns: {len(results['columns'])}")

            print("\n" + "-" * 70)
            print("VALIDATION CHECKS")
            print("-" * 70)

            for check_name, check_result in results['checks'].items():
                status = "✓ PASS" if check_result['passed'] else "✗ FAIL"
                print(f"\n{check_name.replace('_', ' ').title()}: {status}")

                if not check_result['passed']:
                    if 'issues' in check_result:
                        for issue in check_result['issues']:
                            print(f"  • {issue}")
                    elif 'missing_core' in check_result:
                        for col in check_result['missing_core']:
                            print(f"  • Missing: {col}")

        if 'summary_stats' in results:
            print("\n" + "-" * 70)
            print("SUMMARY STATISTICS")
            print("-" * 70)

            stats = results['summary_stats']
            if 'lithium_adoption' in stats:
                print(f"\nLi-ion Adoption:")
                print(f"  Initial: {stats['lithium_adoption']['initial']:.1f}%")
                print(f"  Final: {stats['lithium_adoption']['final']:.1f}%")
                if stats['lithium_adoption']['years_to_50pct']:
                    print(f"  50% Crossover: {stats['lithium_adoption']['years_to_50pct']}")

            if 'tipping_year' in stats and stats['tipping_year']:
                print(f"\nTipping Point: {stats['tipping_year']}")

        print("\n" + "=" * 70)
        overall_status = "✓ VALIDATION PASSED" if results.get('overall_passed', False) else "✗ VALIDATION FAILED"
        print(f"OVERALL STATUS: {overall_status}")
        print("=" * 70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Validate datacenter UPS forecast output files')
    parser.add_argument('input', type=str, help='Path to output file (CSV or JSON)')
    parser.add_argument('--config', type=str, help='Path to config.json')
    parser.add_argument('--compare', type=str, help='Compare with another output file')
    parser.add_argument('--summary-stats', action='store_true', help='Generate summary statistics')
    parser.add_argument('--output', type=str, help='Save validation results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Initialize validator
    validator = OutputValidator(args.config)

    # Determine file format and validate
    if args.input.endswith('.csv'):
        results = validator.validate_csv_output(args.input)
    elif args.input.endswith('.json'):
        results = validator.validate_json_output(args.input)
    else:
        print(f"Error: Unsupported file format. Use .csv or .json")
        return 1

    # Generate summary statistics if requested
    if args.summary_stats and args.input.endswith('.csv'):
        df = pd.read_csv(args.input)
        results['summary_stats'] = validator.generate_summary_statistics(df)

    # Compare with another file if requested
    if args.compare:
        comparison = validator.compare_outputs(args.input, args.compare)
        results['comparison'] = comparison

        print("\n" + "-" * 70)
        print("FILE COMPARISON")
        print("-" * 70)
        print(f"File 1: {args.input}")
        print(f"File 2: {args.compare}")

        if comparison.get('shape_match'):
            print("✓ Shape matches")
        else:
            print("✗ Shape mismatch")

        if comparison.get('columns_only_in_file1'):
            print(f"\nColumns only in file 1: {', '.join(comparison['columns_only_in_file1'])}")
        if comparison.get('columns_only_in_file2'):
            print(f"Columns only in file 2: {', '.join(comparison['columns_only_in_file2'])}")

        if comparison.get('differences'):
            print("\nValue differences (max):")
            for col, diff in comparison['differences'].items():
                if diff['max_pct_diff'] > 1.0:  # Show differences > 1%
                    print(f"  {col}: {diff['max_pct_diff']:.1f}%")

    # Print validation report
    validator.print_validation_report(results)

    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✓ Results saved to: {output_path}")

    # Return status
    return 0 if results.get('overall_passed', False) else 1


if __name__ == "__main__":
    sys.exit(main())