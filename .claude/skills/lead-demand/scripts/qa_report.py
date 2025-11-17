#!/usr/bin/env python3
"""
QA Report Generator for Lead Demand Forecasting
Generates comprehensive quality assurance reports including:
- Validation summary
- Parameter table
- Sensitivity analysis
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from datetime import datetime


class QAReportGenerator:
    """Generate QA reports for lead demand forecasts"""

    def __init__(self, config_path, results_path):
        """Initialize with config and results"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Load results (support CSV, JSON, Parquet)
        results_file = Path(results_path)
        if results_file.suffix == '.csv':
            self.results = pd.read_csv(results_file)
        elif results_file.suffix == '.json':
            self.results = pd.read_json(results_file)
        elif results_file.suffix == '.parquet':
            self.results = pd.read_parquet(results_file)
        else:
            raise ValueError(f"Unsupported file format: {results_file.suffix}")

        self.region = self.results['region'].iloc[0] if 'region' in self.results.columns else 'Global'
        self.scenario = self.results['scenario'].iloc[0] if 'scenario' in self.results.columns else 'baseline'

    def generate_parameter_table(self):
        """Generate table of all parameters used in the forecast"""
        params = {
            'Parameter': [],
            'Value': [],
            'Unit': [],
            'Source/Notes': []
        }

        # SLI battery coefficients
        sli_coeffs = self.config['lead_coefficients']['sli_batteries']
        for vehicle_type, powertrains in sli_coeffs.items():
            for powertrain, value in powertrains.items():
                if powertrain != 'phev_fallback':
                    params['Parameter'].append(f'Lead coefficient: {vehicle_type} {powertrain}')
                    params['Value'].append(value)
                    params['Unit'].append('kg/vehicle')
                    params['Source/Notes'].append('Config file / Industry data')

        # Industrial coefficients
        ind_coeffs = self.config['lead_coefficients']['industrial_batteries']
        params['Parameter'].append('Lead coefficient: Motive power')
        params['Value'].append(ind_coeffs['motive_kg_per_unit'])
        params['Unit'].append('kg/unit')
        params['Source/Notes'].append('Industry standard (forklifts)')

        params['Parameter'].append('Lead coefficient: Stationary')
        params['Value'].append(ind_coeffs['stationary_kg_per_mwh'])
        params['Unit'].append('kg/MWh')
        params['Source/Notes'].append('UPS systems standard')

        # Battery lifetimes
        batt_lifetimes = self.config['battery_lifetimes']
        for batt_type, years in batt_lifetimes.items():
            params['Parameter'].append(f'Battery lifetime: {batt_type}')
            params['Value'].append(years)
            params['Unit'].append('years')
            params['Source/Notes'].append('Industry average / Literature')

        # Asset lifetimes
        asset_lifetimes = self.config['asset_lifetimes']
        for asset_type, years in asset_lifetimes.items():
            params['Parameter'].append(f'Asset lifetime: {asset_type}')
            params['Value'].append(years)
            params['Unit'].append('years')
            params['Source/Notes'].append('Vehicle fleet data / Literature')

        return pd.DataFrame(params)

    def generate_validation_summary(self):
        """Generate validation summary from results"""
        summary = []

        # Check for validation variance columns
        variance_cols = [col for col in self.results.columns if 'variance_pct' in col]

        if variance_cols:
            summary.append("=== Validation Against Direct Demand Datasets ===\n")
            for col in variance_cols:
                variance = self.results[col].iloc[0] if not pd.isna(self.results[col].iloc[0]) else None
                if variance is not None:
                    status = "✓ PASS" if abs(variance) <= 10 else "⚠️  WARNING"
                    segment = col.replace('_variance_pct', '').replace('_', ' ').upper()
                    summary.append(f"{status}: {segment} - Variance: {variance:.1f}%")

        return "\n".join(summary) if summary else "No validation data available"

    def calculate_sensitivity_metrics(self):
        """Calculate key sensitivity metrics"""
        metrics = {}

        # Total demand change
        if 'total_lead_demand_kt' in self.results.columns:
            start_val = self.results['total_lead_demand_kt'].iloc[0]
            end_val = self.results['total_lead_demand_kt'].iloc[-1]
            metrics['Total demand change (%)'] = ((end_val / start_val) - 1) * 100

        # SLI share change
        if 'sli_share_pct' in self.results.columns:
            start_share = self.results['sli_share_pct'].iloc[0]
            end_share = self.results['sli_share_pct'].iloc[-1]
            metrics['SLI share change (pp)'] = end_share - start_share

        # Battery vs non-battery split
        if 'battery_share_pct' in self.results.columns:
            avg_battery_share = self.results['battery_share_pct'].mean()
            metrics['Average battery share (%)'] = avg_battery_share

        return metrics

    def generate_report(self, output_path=None):
        """Generate complete QA report"""
        report_lines = []

        # Header
        report_lines.append("="*80)
        report_lines.append("LEAD DEMAND FORECASTING - QA REPORT")
        report_lines.append("="*80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Region: {self.region}")
        report_lines.append(f"Scenario: {self.scenario}")
        report_lines.append("")

        # Parameter Table
        report_lines.append("\n" + "="*80)
        report_lines.append("1. PARAMETER TABLE")
        report_lines.append("="*80 + "\n")
        param_table = self.generate_parameter_table()
        report_lines.append(param_table.to_string(index=False))

        # Validation Summary
        report_lines.append("\n" + "="*80)
        report_lines.append("2. VALIDATION SUMMARY")
        report_lines.append("="*80 + "\n")
        report_lines.append(self.generate_validation_summary())

        # Sensitivity Metrics
        report_lines.append("\n" + "="*80)
        report_lines.append("3. KEY SENSITIVITY METRICS")
        report_lines.append("="*80 + "\n")
        metrics = self.calculate_sensitivity_metrics()
        for metric_name, metric_value in metrics.items():
            report_lines.append(f"{metric_name}: {metric_value:.2f}")

        # Forecast Summary
        report_lines.append("\n" + "="*80)
        report_lines.append("4. FORECAST SUMMARY")
        report_lines.append("="*80 + "\n")

        if 'year' in self.results.columns:
            start_year = self.results['year'].iloc[0]
            end_year = self.results['year'].iloc[-1]
            report_lines.append(f"Forecast period: {start_year} - {end_year}")

            if 'total_lead_demand_kt' in self.results.columns:
                start_demand = self.results['total_lead_demand_kt'].iloc[0]
                end_demand = self.results['total_lead_demand_kt'].iloc[-1]
                report_lines.append(f"\nTotal Lead Demand:")
                report_lines.append(f"  {start_year}: {start_demand:.0f} kt")
                report_lines.append(f"  {end_year}: {end_demand:.0f} kt")
                report_lines.append(f"  Change: {((end_demand/start_demand)-1)*100:+.1f}%")

        report_lines.append("\n" + "="*80)

        # Combine report
        report_text = "\n".join(report_lines)

        # Save or print
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"✓ QA Report saved to: {output_file}")
        else:
            print(report_text)

        return report_text


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Generate QA Report for Lead Demand Forecast')
    parser.add_argument('--results', type=str, required=True,
                       help='Path to forecast results file (CSV, JSON, or Parquet)')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file (defaults to ../config.json)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output path for QA report (defaults to stdout)')

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

    if not Path(args.results).exists():
        print(f"Error: Results file not found at {args.results}")
        sys.exit(1)

    # Generate report
    generator = QAReportGenerator(config_path, args.results)
    generator.generate_report(args.output)


if __name__ == "__main__":
    main()
