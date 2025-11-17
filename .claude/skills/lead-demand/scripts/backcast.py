#!/usr/bin/env python3
"""
Back-casting Framework for Lead Demand Forecasting
Validates forecast accuracy by comparing historical forecasts against actual data
Calculates MAPE (Mean Absolute Percentage Error) and other accuracy metrics
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from datetime import datetime

# Import the forecasting engine
sys.path.append(str(Path(__file__).parent))
from forecast import LeadDemandForecast


class BackcastValidator:
    """Validate forecast accuracy using historical back-casting"""

    def __init__(self, config_path, data_dir):
        """Initialize with config and data directory"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.data_dir = Path(data_dir)
        self.config_path = Path(config_path)
        self.backcast_results = []

    def identify_historical_period(self, validation_data):
        """
        Identify the period with sufficient historical data for back-casting

        Returns:
            tuple: (start_year, end_year, validation_years)
        """
        # Find years with validation data
        years_with_data = set()

        for segment_key, region_data in validation_data.items():
            for region, series in region_data.items():
                if isinstance(series, pd.Series):
                    years_with_data.update(series.index)

        if not years_with_data:
            return None, None, []

        validation_years = sorted(list(years_with_data))
        start_year = min(validation_years)
        end_year = max(validation_years)

        return start_year, end_year, validation_years

    def run_backcast(self, region='Global', scenario='baseline', backcast_start=None, backcast_end=None):
        """
        Run back-cast: forecast over historical period and compare with actuals

        Args:
            region: Region to forecast
            scenario: Scenario name
            backcast_start: Start year for back-casting (if None, use earliest available data)
            backcast_end: End year for back-casting (if None, use latest available data)

        Returns:
            dict: Back-cast validation results with MAPE and other metrics
        """
        print(f"\n{'='*70}")
        print(f"BACK-CASTING VALIDATION: {region} - {scenario}")
        print(f"{'='*70}\n")

        # Create forecast instance
        forecaster = LeadDemandForecast(
            config_path=str(self.config_path),
            region=region,
            scenario=scenario
        )

        # Load data to identify historical period
        forecaster.load_data()

        if 'validation' not in forecaster.real_data:
            print("⚠️  No validation data available for back-casting")
            return None

        validation_data = forecaster.real_data['validation']

        # Identify historical period
        start_year, end_year, validation_years = self.identify_historical_period(validation_data)

        if not validation_years:
            print("⚠️  No validation years found")
            return None

        # Use provided years or defaults
        if backcast_start is None:
            backcast_start = start_year
        if backcast_end is None:
            backcast_end = end_year

        print(f"Historical period identified: {backcast_start} - {backcast_end}")
        print(f"Validation years available: {len(validation_years)} years\n")

        # Run forecast over historical period
        print("Running forecast over historical period...")
        forecaster.forecast_demand(start_year=backcast_start, end_year=backcast_end)

        # Extract forecasted values
        forecast_results = forecaster.results

        # Compare with validation data
        comparison_results = {
            'region': region,
            'scenario': scenario,
            'backcast_period': f"{backcast_start}-{backcast_end}",
            'segments': {}
        }

        # Segment mapping
        segment_map = {
            'cars_oem': 'sli_oem_passenger_cars_kt',
            'cars_replacement': 'sli_replacement_passenger_cars_kt',
            '2w_oem': 'sli_oem_two_wheelers_kt',
            '2w_replacement': 'sli_replacement_two_wheelers_kt',
            '3w_oem': 'sli_oem_three_wheelers_kt',
            '3w_replacement': 'sli_replacement_three_wheelers_kt'
        }

        print("\nCalculating accuracy metrics...\n")

        for validation_key, forecast_col in segment_map.items():
            if validation_key in validation_data and region in validation_data[validation_key]:
                actual_series = validation_data[validation_key][region]

                if forecast_col in forecast_results.columns:
                    forecast_series = forecast_results.set_index('year')[forecast_col]

                    # Find overlapping years
                    overlap_years = sorted(set(actual_series.index) & set(forecast_series.index))

                    if overlap_years:
                        # Extract values for overlapping years
                        actuals = [actual_series[y] for y in overlap_years]
                        forecasts = [forecast_series[y] for y in overlap_years]

                        # Calculate error metrics
                        errors = [(f - a) for f, a in zip(forecasts, actuals)]
                        abs_errors = [abs(e) for e in errors]
                        pct_errors = [(abs(f - a) / a * 100) if a != 0 else 0 for f, a in zip(forecasts, actuals)]

                        # MAPE (Mean Absolute Percentage Error)
                        mape = np.mean(pct_errors)

                        # MAE (Mean Absolute Error)
                        mae = np.mean(abs_errors)

                        # RMSE (Root Mean Squared Error)
                        rmse = np.sqrt(np.mean([e**2 for e in errors]))

                        # Bias (mean error)
                        bias = np.mean(errors)

                        # R-squared
                        ss_res = sum([e**2 for e in errors])
                        ss_tot = sum([(a - np.mean(actuals))**2 for a in actuals])
                        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

                        # Store results
                        comparison_results['segments'][validation_key] = {
                            'forecast_column': forecast_col,
                            'n_years': len(overlap_years),
                            'years': overlap_years,
                            'actuals': actuals,
                            'forecasts': forecasts,
                            'mape': round(mape, 2),
                            'mae': round(mae, 2),
                            'rmse': round(rmse, 2),
                            'bias': round(bias, 2),
                            'r_squared': round(r_squared, 3)
                        }

                        # Print results
                        status = "✓ EXCELLENT" if mape < 5 else "✓ GOOD" if mape < 10 else "⚠️  FAIR" if mape < 20 else "❌ POOR"
                        print(f"{status} {validation_key}")
                        print(f"   MAPE: {mape:.2f}%")
                        print(f"   MAE: {mae:.2f} kt")
                        print(f"   RMSE: {rmse:.2f} kt")
                        print(f"   Bias: {bias:+.2f} kt")
                        print(f"   R²: {r_squared:.3f}")
                        print(f"   Years: {len(overlap_years)}")
                        print()

        # Calculate overall metrics
        if comparison_results['segments']:
            all_mapes = [seg['mape'] for seg in comparison_results['segments'].values()]
            comparison_results['overall_mape'] = round(np.mean(all_mapes), 2)

            all_r2 = [seg['r_squared'] for seg in comparison_results['segments'].values()]
            comparison_results['overall_r2'] = round(np.mean(all_r2), 3)

            print(f"{'='*70}")
            print(f"OVERALL BACK-CAST ACCURACY")
            print(f"{'='*70}")
            print(f"Average MAPE: {comparison_results['overall_mape']:.2f}%")
            print(f"Average R²: {comparison_results['overall_r2']:.3f}")
            print(f"Segments evaluated: {len(comparison_results['segments'])}")
            print()

        return comparison_results

    def generate_backcast_report(self, backcast_results, output_path=None):
        """Generate detailed back-cast validation report"""
        if not backcast_results:
            print("⚠️  No back-cast results to report")
            return

        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("BACK-CASTING VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Region: {backcast_results['region']}")
        report_lines.append(f"Scenario: {backcast_results['scenario']}")
        report_lines.append(f"Back-cast Period: {backcast_results['backcast_period']}")
        report_lines.append("")

        # Overall metrics
        if 'overall_mape' in backcast_results:
            report_lines.append("OVERALL ACCURACY METRICS:")
            report_lines.append("-" * 80)
            report_lines.append(f"Average MAPE: {backcast_results['overall_mape']:.2f}%")
            report_lines.append(f"Average R²: {backcast_results['overall_r2']:.3f}")
            report_lines.append(f"Segments Evaluated: {len(backcast_results['segments'])}")
            report_lines.append("")

        # Segment-by-segment results
        report_lines.append("SEGMENT-BY-SEGMENT ACCURACY:")
        report_lines.append("-" * 80)

        for segment_key, metrics in backcast_results['segments'].items():
            report_lines.append(f"\n{segment_key.upper()}")
            report_lines.append(f"  Forecast Column: {metrics['forecast_column']}")
            report_lines.append(f"  Years Evaluated: {metrics['n_years']}")
            report_lines.append(f"  MAPE: {metrics['mape']:.2f}%")
            report_lines.append(f"  MAE: {metrics['mae']:.2f} kt")
            report_lines.append(f"  RMSE: {metrics['rmse']:.2f} kt")
            report_lines.append(f"  Bias: {metrics['bias']:+.2f} kt")
            report_lines.append(f"  R²: {metrics['r_squared']:.3f}")

        report_lines.append("\n" + "=" * 80)

        report_text = "\n".join(report_lines)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"✓ Back-cast report saved to: {output_file}")
        else:
            print("\n" + report_text)

        return report_text

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Back-cast Validation for Lead Demand Forecast')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file (defaults to ../config.json)')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Path to data directory (defaults to ../data)')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to back-cast (default: Global)')
    parser.add_argument('--scenario', type=str, default='baseline',
                       help='Scenario name (default: baseline)')
    parser.add_argument('--start-year', type=int, default=None,
                       help='Back-cast start year (default: auto-detect)')
    parser.add_argument('--end-year', type=int, default=None,
                       help='Back-cast end year (default: auto-detect)')
    parser.add_argument('--output-report', type=str, default=None,
                       help='Output path for back-cast report')

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

    # Create validator
    validator = BackcastValidator(config_path, data_dir)

    # Run back-cast
    results = validator.run_backcast(
        region=args.region,
        scenario=args.scenario,
        backcast_start=args.start_year,
        backcast_end=args.end_year
    )

    if results:
        # Generate report
        if args.output_report:
            validator.generate_backcast_report(results, args.output_report)
        else:
            skill_dir = Path(__file__).parent.parent
            default_report = skill_dir / 'output' / f'backcast_report_{args.region}_{args.scenario}.txt'
            validator.generate_backcast_report(results, default_report)


if __name__ == "__main__":
    main()
