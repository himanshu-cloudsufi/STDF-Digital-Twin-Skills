#!/usr/bin/env python3
"""
Multi-Scenario Comparison Framework for Lead Demand Forecasting
Compares multiple scenarios side-by-side with differential analysis
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


class ScenarioComparator:
    """Compare multiple forecast scenarios"""

    def __init__(self, config_path, data_dir):
        """Initialize with config and data directory"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.data_dir = Path(data_dir)
        self.config_path = Path(config_path)
        self.scenario_results = {}

    def run_scenario(self, region, scenario_name, scenario_config=None):
        """
        Run a single scenario

        Args:
            region: Region to forecast
            scenario_name: Name of the scenario
            scenario_config: Optional scenario-specific config overrides

        Returns:
            pd.DataFrame: Forecast results for the scenario
        """
        print(f"\n{'='*70}")
        print(f"Running Scenario: {scenario_name}")
        print(f"{'='*70}\n")

        # Create forecast instance
        forecaster = LeadDemandForecast(
            config_path=str(self.config_path),
            region=region,
            scenario=scenario_name
        )

        # Apply scenario-specific config overrides if provided
        if scenario_config:
            for key, value in scenario_config.items():
                if key in forecaster.config:
                    forecaster.config[key] = value
                    print(f"  Override: {key}")

        # Load data and run forecast
        forecaster.load_data()
        forecaster.forecast_demand()

        # Store results
        self.scenario_results[scenario_name] = forecaster.results.copy()

        print(f"\n✓ Scenario '{scenario_name}' complete")

        return forecaster.results

    def compare_scenarios(self, scenarios, region='Global'):
        """
        Compare multiple scenarios

        Args:
            scenarios: List of scenario names or dict of {name: config_overrides}
            region: Region to forecast

        Returns:
            dict: Comparison results
        """
        # Run all scenarios
        for scenario in scenarios:
            if isinstance(scenario, dict):
                scenario_name = scenario['name']
                scenario_config = scenario.get('config', None)
            else:
                scenario_name = scenario
                scenario_config = None

            self.run_scenario(region, scenario_name, scenario_config)

        # Generate comparison analysis
        comparison = self.generate_comparison_analysis()

        return comparison

    def generate_comparison_analysis(self):
        """Generate comprehensive comparison analysis"""
        if len(self.scenario_results) < 2:
            print("⚠️  Need at least 2 scenarios for comparison")
            return None

        print(f"\n{'='*70}")
        print(f"SCENARIO COMPARISON ANALYSIS")
        print(f"{'='*70}\n")

        comparison = {
            'scenarios': list(self.scenario_results.keys()),
            'metrics': {},
            'differences': {}
        }

        scenario_names = list(self.scenario_results.keys())
        baseline_scenario = scenario_names[0]

        # Key metrics to compare
        metrics_to_compare = [
            'total_lead_demand_kt',
            'sli_demand_kt',
            'sli_oem_kt',
            'sli_replacement_kt',
            'industrial_demand_kt',
            'other_uses_kt'
        ]

        # Extract final year values
        print("FINAL YEAR COMPARISON:")
        print("-" * 70)

        for metric in metrics_to_compare:
            if metric in self.scenario_results[baseline_scenario].columns:
                print(f"\n{metric.replace('_', ' ').title()}:")

                for scenario_name in scenario_names:
                    results = self.scenario_results[scenario_name]
                    final_value = results[metric].iloc[-1]

                    comparison['metrics'].setdefault(metric, {})[scenario_name] = final_value

                    # Calculate difference from baseline
                    baseline_value = self.scenario_results[baseline_scenario][metric].iloc[-1]
                    diff = final_value - baseline_value
                    diff_pct = (diff / baseline_value * 100) if baseline_value != 0 else 0

                    print(f"  {scenario_name:20s}: {final_value:>8.1f} kt ({diff_pct:+6.1f}% vs baseline)")

                    if scenario_name != baseline_scenario:
                        comparison['differences'].setdefault(metric, {})[scenario_name] = {
                            'absolute': diff,
                            'percent': diff_pct
                        }

        # Period-over-period growth comparison
        print(f"\n{'='*70}")
        print("PERIOD GROWTH RATES:")
        print("-" * 70)

        for scenario_name in scenario_names:
            results = self.scenario_results[scenario_name]
            start_value = results['total_lead_demand_kt'].iloc[0]
            end_value = results['total_lead_demand_kt'].iloc[-1]
            growth = ((end_value / start_value) - 1) * 100

            comparison['metrics'].setdefault('total_growth_pct', {})[scenario_name] = growth

            print(f"{scenario_name:20s}: {growth:+.1f}%")

        # SLI share comparison
        print(f"\n{'='*70}")
        print("SLI SHARE OF TOTAL DEMAND (Final Year):")
        print("-" * 70)

        for scenario_name in scenario_names:
            results = self.scenario_results[scenario_name]
            if 'sli_share_pct' in results.columns:
                sli_share = results['sli_share_pct'].iloc[-1]
                comparison['metrics'].setdefault('sli_share_pct', {})[scenario_name] = sli_share
                print(f"{scenario_name:20s}: {sli_share:.1f}%")

        return comparison

    def generate_comparison_report(self, comparison, output_path=None):
        """Generate detailed comparison report"""
        if not comparison:
            print("⚠️  No comparison data available")
            return

        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("MULTI-SCENARIO COMPARISON REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Scenarios: {', '.join(comparison['scenarios'])}")
        report_lines.append("")

        # Metrics comparison table
        report_lines.append("FINAL YEAR METRICS:")
        report_lines.append("-" * 80)

        for metric, scenario_values in comparison['metrics'].items():
            report_lines.append(f"\n{metric.replace('_', ' ').title()}:")
            for scenario_name, value in scenario_values.items():
                report_lines.append(f"  {scenario_name:20s}: {value:>10.2f}")

        # Differences from baseline
        if comparison['differences']:
            report_lines.append("\n\n" + "=" * 80)
            report_lines.append("DIFFERENCES FROM BASELINE:")
            report_lines.append("-" * 80)

            for metric, scenario_diffs in comparison['differences'].items():
                report_lines.append(f"\n{metric.replace('_', ' ').title()}:")
                for scenario_name, diff_info in scenario_diffs.items():
                    report_lines.append(f"  {scenario_name:20s}: {diff_info['absolute']:>+8.1f} kt ({diff_info['percent']:>+6.1f}%)")

        report_lines.append("\n" + "=" * 80)

        report_text = "\n".join(report_lines)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"\n✓ Comparison report saved to: {output_file}")
        else:
            print("\n" + report_text)

        return report_text


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Multi-Scenario Comparison for Lead Demand Forecast')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file (defaults to ../config.json)')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Path to data directory (defaults to ../data)')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to forecast (default: Global)')
    parser.add_argument('--scenarios', type=str, nargs='+', required=True,
                       help='List of scenario names to compare')
    parser.add_argument('--output-report', type=str, default=None,
                       help='Output path for comparison report')

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

    # Create comparator
    comparator = ScenarioComparator(config_path, data_dir)

    # Run comparison
    comparison = comparator.compare_scenarios(args.scenarios, region=args.region)

    if comparison:
        # Generate report
        if args.output_report:
            comparator.generate_comparison_report(comparison, args.output_report)
        else:
            skill_dir = Path(__file__).parent.parent
            default_report = skill_dir / 'output' / f'scenario_comparison_{args.region}.txt'
            comparator.generate_comparison_report(comparison, default_report)


if __name__ == "__main__":
    main()
