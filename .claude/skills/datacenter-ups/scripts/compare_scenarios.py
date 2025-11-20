#!/usr/bin/env python3
"""
Scenario Comparison Script
Compares forecast results across multiple scenarios
"""

import json
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional


class ScenarioComparator:
    """Compare and analyze multiple forecast scenarios"""

    def __init__(self):
        self.scenarios_data = {}
        self.comparison_metrics = None

    def load_scenario(self, file_path: str, scenario_name: Optional[str] = None):
        """
        Load scenario data from file

        Args:
            file_path: Path to scenario output file (CSV or JSON)
            scenario_name: Optional name for the scenario
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if scenario_name is None:
            # Extract scenario name from filename
            scenario_name = file_path.stem.split('_')[-1]

        if file_path.suffix == '.csv':
            data = pd.read_csv(file_path)
        elif file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            # Extract forecast data from JSON
            if 'forecast' in json_data:
                forecast = json_data['forecast']
                data = pd.DataFrame({
                    'year': forecast['years'],
                    'total_demand_gwh': forecast['demand'].get('total_gwh', []),
                    'vrla_demand_gwh': forecast['demand'].get('vrla_gwh', []),
                    'lithium_demand_gwh': forecast['demand'].get('lithium_gwh', []),
                    'vrla_share_pct': forecast['shares'].get('vrla_pct', []),
                    'lithium_share_pct': forecast['shares'].get('lithium_pct', [])
                })
                # Add TCO data if available
                if 'tco' in forecast:
                    data['vrla_tco_per_kwh'] = forecast['tco'].get('vrla_per_kwh', [])
                    data['lithium_tco_per_kwh'] = forecast['tco'].get('lithium_per_kwh', [])
                    data['tco_advantage'] = forecast['tco'].get('advantage', [])
            else:
                data = pd.DataFrame(json_data)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        self.scenarios_data[scenario_name] = data

    def compare_key_metrics(self, metrics: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compare key metrics across scenarios

        Args:
            metrics: List of metrics to compare (default: standard set)

        Returns:
            DataFrame with comparison results
        """
        if not self.scenarios_data:
            raise ValueError("No scenarios loaded")

        if metrics is None:
            metrics = [
                'tipping_year',
                'lithium_share_2030',
                'lithium_share_2035',
                'lithium_share_2040',
                'total_demand_cagr',
                'peak_annual_growth',
                'years_to_50pct_adoption'
            ]

        comparison = {}

        for scenario_name, data in self.scenarios_data.items():
            scenario_metrics = {}

            # Tipping year
            if 'tipping_year' in data.columns:
                tipping = data['tipping_year'].iloc[0]
                scenario_metrics['tipping_year'] = tipping if tipping != 'N/A' else None
            else:
                # Try to detect from TCO advantage
                if 'tco_advantage' in data.columns:
                    positive_advantage = data[data['tco_advantage'] > 0]
                    if not positive_advantage.empty:
                        scenario_metrics['tipping_year'] = positive_advantage['year'].iloc[0]
                    else:
                        scenario_metrics['tipping_year'] = None
                else:
                    scenario_metrics['tipping_year'] = None

            # Li-ion share at key years
            for year in [2030, 2035, 2040]:
                key = f'lithium_share_{year}'
                if key in metrics:
                    year_data = data[data['year'] == year]
                    if not year_data.empty and 'lithium_share_pct' in data.columns:
                        scenario_metrics[key] = year_data['lithium_share_pct'].iloc[0]
                    else:
                        scenario_metrics[key] = None

            # Total demand CAGR
            if 'total_demand_cagr' in metrics and 'total_demand_gwh' in data.columns:
                start_demand = data['total_demand_gwh'].iloc[0]
                end_demand = data['total_demand_gwh'].iloc[-1]
                years = len(data) - 1
                if years > 0 and start_demand > 0:
                    cagr = (end_demand / start_demand) ** (1 / years) - 1
                    scenario_metrics['total_demand_cagr'] = cagr * 100
                else:
                    scenario_metrics['total_demand_cagr'] = None

            # Peak annual growth
            if 'peak_annual_growth' in metrics and 'lithium_demand_gwh' in data.columns:
                demand = data['lithium_demand_gwh'].values
                if len(demand) > 1:
                    growth_rates = [(demand[i+1] - demand[i]) / demand[i] * 100
                                  for i in range(len(demand)-1) if demand[i] > 0]
                    scenario_metrics['peak_annual_growth'] = max(growth_rates) if growth_rates else None
                else:
                    scenario_metrics['peak_annual_growth'] = None

            # Years to 50% adoption
            if 'years_to_50pct_adoption' in metrics and 'lithium_share_pct' in data.columns:
                crossed_50 = data[data['lithium_share_pct'] >= 50]
                if not crossed_50.empty:
                    scenario_metrics['years_to_50pct_adoption'] = crossed_50['year'].iloc[0]
                else:
                    scenario_metrics['years_to_50pct_adoption'] = None

            comparison[scenario_name] = scenario_metrics

        self.comparison_metrics = pd.DataFrame(comparison).T
        return self.comparison_metrics

    def calculate_differences(self, base_scenario: str) -> pd.DataFrame:
        """
        Calculate differences relative to base scenario

        Args:
            base_scenario: Name of base scenario for comparison

        Returns:
            DataFrame with differences
        """
        if base_scenario not in self.scenarios_data:
            raise ValueError(f"Base scenario '{base_scenario}' not found")

        base_data = self.scenarios_data[base_scenario]
        differences = {}

        for scenario_name, scenario_data in self.scenarios_data.items():
            if scenario_name == base_scenario:
                continue

            diff = {}

            # Align years
            common_years = set(base_data['year']) & set(scenario_data['year'])

            for year in [2030, 2035, 2040]:
                if year in common_years:
                    base_year = base_data[base_data['year'] == year]
                    scenario_year = scenario_data[scenario_data['year'] == year]

                    if not base_year.empty and not scenario_year.empty:
                        # Li-ion share difference
                        if 'lithium_share_pct' in base_data.columns and 'lithium_share_pct' in scenario_data.columns:
                            diff[f'lithium_share_{year}_diff'] = (
                                scenario_year['lithium_share_pct'].iloc[0] -
                                base_year['lithium_share_pct'].iloc[0]
                            )

                        # Total demand difference
                        if 'total_demand_gwh' in base_data.columns and 'total_demand_gwh' in scenario_data.columns:
                            diff[f'total_demand_{year}_diff'] = (
                                scenario_year['total_demand_gwh'].iloc[0] -
                                base_year['total_demand_gwh'].iloc[0]
                            )

            differences[scenario_name] = diff

        return pd.DataFrame(differences).T

    def generate_comparison_table(self, output_format: str = 'markdown') -> str:
        """
        Generate formatted comparison table

        Args:
            output_format: 'markdown', 'html', or 'latex'

        Returns:
            Formatted table string
        """
        if self.comparison_metrics is None:
            self.compare_key_metrics()

        if output_format == 'markdown':
            return self._format_markdown_table()
        elif output_format == 'html':
            return self.comparison_metrics.to_html()
        elif output_format == 'latex':
            return self.comparison_metrics.to_latex()
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_markdown_table(self) -> str:
        """Format comparison as markdown table"""
        df = self.comparison_metrics

        # Create header
        lines = ["| Metric | " + " | ".join(df.index) + " |"]
        lines.append("|" + "---|" * (len(df.index) + 1))

        # Add rows
        for col in df.columns:
            row_values = []
            for idx in df.index:
                value = df.loc[idx, col]
                if pd.isna(value):
                    row_values.append("N/A")
                elif isinstance(value, (int, np.integer)):
                    row_values.append(str(value))
                elif isinstance(value, (float, np.floating)):
                    if col.endswith('_pct') or col.endswith('share') or col.endswith('cagr'):
                        row_values.append(f"{value:.1f}%")
                    else:
                        row_values.append(f"{value:.2f}")
                else:
                    row_values.append(str(value))

            lines.append(f"| {col} | " + " | ".join(row_values) + " |")

        return "\n".join(lines)

    def plot_adoption_curves(self, save_path: Optional[str] = None):
        """
        Plot adoption curves for all scenarios

        Args:
            save_path: Optional path to save plot
        """
        plt.figure(figsize=(12, 8))

        for scenario_name, data in self.scenarios_data.items():
            if 'lithium_share_pct' in data.columns:
                plt.plot(data['year'], data['lithium_share_pct'],
                        label=scenario_name, linewidth=2)

        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Li-ion Market Share (%)', fontsize=12)
        plt.title('Li-ion Adoption Comparison Across Scenarios', fontsize=14)
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        plt.xlim(data['year'].min(), data['year'].max())
        plt.ylim(0, 100)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✓ Plot saved to: {save_path}")
        else:
            plt.show()

    def plot_demand_comparison(self, technology: str = 'lithium',
                              save_path: Optional[str] = None):
        """
        Plot demand comparison for specific technology

        Args:
            technology: 'lithium', 'vrla', or 'total'
            save_path: Optional path to save plot
        """
        column_map = {
            'lithium': 'lithium_demand_gwh',
            'vrla': 'vrla_demand_gwh',
            'total': 'total_demand_gwh'
        }

        column = column_map.get(technology)
        if not column:
            raise ValueError(f"Unknown technology: {technology}")

        plt.figure(figsize=(12, 8))

        for scenario_name, data in self.scenarios_data.items():
            if column in data.columns:
                plt.plot(data['year'], data[column],
                        label=scenario_name, linewidth=2)

        plt.xlabel('Year', fontsize=12)
        plt.ylabel(f'{technology.title()} Demand (GWh)', fontsize=12)
        plt.title(f'{technology.title()} Demand Comparison Across Scenarios', fontsize=14)
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✓ Plot saved to: {save_path}")
        else:
            plt.show()

    def plot_tco_comparison(self, save_path: Optional[str] = None):
        """
        Plot TCO comparison across scenarios

        Args:
            save_path: Optional path to save plot
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Plot TCO trajectories
        for scenario_name, data in self.scenarios_data.items():
            if 'vrla_tco_per_kwh' in data.columns and 'lithium_tco_per_kwh' in data.columns:
                ax1.plot(data['year'], data['vrla_tco_per_kwh'],
                        linestyle='--', label=f'{scenario_name} - VRLA')
                ax1.plot(data['year'], data['lithium_tco_per_kwh'],
                        linestyle='-', label=f'{scenario_name} - Li-ion')

        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('TCO ($/kWh)', fontsize=12)
        ax1.set_title('TCO Trajectories', fontsize=14)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # Plot TCO advantage
        for scenario_name, data in self.scenarios_data.items():
            if 'tco_advantage' in data.columns:
                ax2.plot(data['year'], data['tco_advantage'],
                        label=scenario_name, linewidth=2)

        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('Year', fontsize=12)
        ax2.set_ylabel('TCO Advantage ($/kWh)', fontsize=12)
        ax2.set_title('Li-ion TCO Advantage (VRLA TCO - Li-ion TCO)', fontsize=14)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✓ Plot saved to: {save_path}")
        else:
            plt.show()

    def export_comparison(self, output_path: str):
        """
        Export comparison results to file

        Args:
            output_path: Path to save comparison results
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.comparison_metrics is None:
            self.compare_key_metrics()

        if output_path.suffix == '.csv':
            self.comparison_metrics.to_csv(output_path)
        elif output_path.suffix == '.json':
            self.comparison_metrics.to_json(output_path, orient='index', indent=2)
        elif output_path.suffix == '.xlsx':
            with pd.ExcelWriter(output_path) as writer:
                self.comparison_metrics.to_excel(writer, sheet_name='Comparison')

                # Add individual scenario sheets
                for name, data in self.scenarios_data.items():
                    data.to_excel(writer, sheet_name=name[:31], index=False)  # Excel sheet name limit
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")

        print(f"✓ Comparison exported to: {output_path}")

    def print_summary(self):
        """Print comparison summary"""
        print("\n" + "=" * 70)
        print("SCENARIO COMPARISON SUMMARY")
        print("=" * 70)

        if self.comparison_metrics is None:
            self.compare_key_metrics()

        print(f"\nScenarios loaded: {', '.join(self.scenarios_data.keys())}")

        # Print key differences
        if 'baseline' in self.scenarios_data and len(self.scenarios_data) > 1:
            print("\n" + "-" * 70)
            print("Key Differences from Baseline")
            print("-" * 70)

            differences = self.calculate_differences('baseline')
            for scenario in differences.index:
                print(f"\n{scenario}:")
                for col in differences.columns:
                    value = differences.loc[scenario, col]
                    if not pd.isna(value):
                        if 'share' in col:
                            print(f"  {col}: {value:+.1f} pp")
                        else:
                            print(f"  {col}: {value:+.2f}")

        # Print comparison table
        print("\n" + "-" * 70)
        print("Comparison Table")
        print("-" * 70)
        print(self._format_markdown_table())

        print("\n" + "=" * 70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Compare datacenter UPS forecast scenarios')
    parser.add_argument('scenarios', nargs='+', help='Paths to scenario output files')
    parser.add_argument('--names', type=str, help='Comma-separated scenario names')
    parser.add_argument('--base', type=str, default='baseline', help='Base scenario for comparison')
    parser.add_argument('--metrics', type=str, help='Comma-separated metrics to compare')
    parser.add_argument('--plot', action='store_true', help='Generate comparison plots')
    parser.add_argument('--plot-type', type=str, default='adoption',
                       choices=['adoption', 'demand', 'tco', 'all'],
                       help='Type of plot to generate')
    parser.add_argument('--output', type=str, help='Save comparison to file')
    parser.add_argument('--format', type=str, default='markdown',
                       choices=['markdown', 'html', 'latex'],
                       help='Table output format')

    args = parser.parse_args()

    # Initialize comparator
    comparator = ScenarioComparator()

    # Load scenarios
    scenario_names = args.names.split(',') if args.names else None
    for i, scenario_path in enumerate(args.scenarios):
        name = scenario_names[i] if scenario_names and i < len(scenario_names) else None
        try:
            comparator.load_scenario(scenario_path, name)
            print(f"✓ Loaded scenario: {name or Path(scenario_path).stem}")
        except Exception as e:
            print(f"✗ Error loading {scenario_path}: {e}")

    # Compare metrics
    if args.metrics:
        metrics = args.metrics.split(',')
    else:
        metrics = None

    comparison = comparator.compare_key_metrics(metrics)

    # Generate plots if requested
    if args.plot:
        if args.plot_type in ['adoption', 'all']:
            plot_path = 'output/adoption_comparison.png' if args.output else None
            comparator.plot_adoption_curves(plot_path)

        if args.plot_type in ['demand', 'all']:
            plot_path = 'output/demand_comparison.png' if args.output else None
            comparator.plot_demand_comparison('lithium', plot_path)

        if args.plot_type in ['tco', 'all']:
            plot_path = 'output/tco_comparison.png' if args.output else None
            comparator.plot_tco_comparison(plot_path)

    # Export comparison if requested
    if args.output:
        comparator.export_comparison(args.output)

    # Print summary
    comparator.print_summary()


if __name__ == "__main__":
    sys.exit(main())