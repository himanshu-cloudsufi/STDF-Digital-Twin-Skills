#!/usr/bin/env python3
"""
Metrics Extraction Script
Extracts key metrics from forecast output files
"""

import json
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any


class MetricsExtractor:
    """Extract and analyze key metrics from forecast results"""

    def __init__(self):
        self.data = None
        self.metrics = {}

    def load_data(self, file_path: str):
        """
        Load forecast data from file

        Args:
            file_path: Path to forecast output file (CSV or JSON)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix == '.csv':
            self.data = pd.read_csv(file_path)
        elif file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                json_data = json.load(f)

            # Extract forecast data from JSON structure
            if 'forecast' in json_data:
                forecast = json_data['forecast']
                self.data = pd.DataFrame({
                    'year': forecast['years'],
                    'total_demand_gwh': forecast['demand'].get('total_gwh', []),
                    'vrla_demand_gwh': forecast['demand'].get('vrla_gwh', []),
                    'lithium_demand_gwh': forecast['demand'].get('lithium_gwh', [])
                })

                # Add shares if available
                if 'shares' in forecast:
                    self.data['vrla_share_pct'] = forecast['shares'].get('vrla_pct', [])
                    self.data['lithium_share_pct'] = forecast['shares'].get('lithium_pct', [])

                # Add TCO data if available
                if 'tco' in forecast:
                    self.data['vrla_tco_per_kwh'] = forecast['tco'].get('vrla_per_kwh', [])
                    self.data['lithium_tco_per_kwh'] = forecast['tco'].get('lithium_per_kwh', [])
                    self.data['tco_advantage'] = forecast['tco'].get('advantage', [])

                # Add installed base if available
                if 'installed_base' in forecast:
                    self.data['vrla_installed_base_gwh'] = forecast['installed_base'].get('vrla_gwh', [])
                    self.data['lithium_installed_base_gwh'] = forecast['installed_base'].get('lithium_gwh', [])
            else:
                self.data = pd.DataFrame(json_data)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def extract_tipping_point(self) -> Optional[int]:
        """
        Extract tipping point year

        Returns:
            Tipping point year or None
        """
        # Check if explicitly stored
        if 'tipping_year' in self.data.columns:
            tipping = self.data['tipping_year'].iloc[0]
            if tipping != 'N/A':
                return int(tipping) if not pd.isna(tipping) else None

        # Try to detect from TCO advantage
        if 'tco_advantage' in self.data.columns:
            # Find first year where Li-ion has sustained advantage
            advantages = self.data['tco_advantage'].values
            years = self.data['year'].values

            for i in range(len(advantages) - 2):
                # Check for 3 consecutive years of positive advantage
                if all(advantages[i:i+3] > 0):
                    return int(years[i])

        return None

    def extract_adoption_metrics(self) -> Dict[str, Any]:
        """
        Extract adoption-related metrics

        Returns:
            Dictionary of adoption metrics
        """
        metrics = {}

        if 'lithium_share_pct' not in self.data.columns:
            return metrics

        shares = self.data['lithium_share_pct'].values
        years = self.data['year'].values

        # Initial and final shares
        metrics['initial_lithium_share'] = shares[0]
        metrics['final_lithium_share'] = shares[-1]

        # Key milestone years
        for threshold, key in [(10, 'year_10pct'), (25, 'year_25pct'),
                               (50, 'year_50pct'), (75, 'year_75pct'),
                               (90, 'year_90pct')]:
            for i, share in enumerate(shares):
                if share >= threshold:
                    metrics[key] = int(years[i])
                    break

        # Growth rates
        if len(shares) > 1:
            # Maximum annual growth
            annual_growth = [shares[i+1] - shares[i] for i in range(len(shares)-1)]
            metrics['max_annual_growth_pp'] = max(annual_growth)

            # Average annual growth
            metrics['avg_annual_growth_pp'] = np.mean(annual_growth)

            # Years to reach certain shares
            for year_target in [2030, 2035, 2040]:
                if year_target in years:
                    idx = list(years).index(year_target)
                    metrics[f'lithium_share_{year_target}'] = shares[idx]

        return metrics

    def extract_demand_metrics(self) -> Dict[str, Any]:
        """
        Extract demand-related metrics

        Returns:
            Dictionary of demand metrics
        """
        metrics = {}

        # Total market metrics
        if 'total_demand_gwh' in self.data.columns:
            total_demand = self.data['total_demand_gwh'].values
            years = self.data['year'].values

            metrics['initial_total_demand'] = total_demand[0]
            metrics['final_total_demand'] = total_demand[-1]

            # CAGR
            if len(total_demand) > 1 and total_demand[0] > 0:
                n_years = len(total_demand) - 1
                cagr = (total_demand[-1] / total_demand[0]) ** (1/n_years) - 1
                metrics['total_demand_cagr'] = cagr

            # Peak demand year
            peak_idx = np.argmax(total_demand)
            metrics['peak_demand_year'] = int(years[peak_idx])
            metrics['peak_demand_gwh'] = total_demand[peak_idx]

        # Technology-specific demand
        for tech in ['vrla', 'lithium']:
            col = f'{tech}_demand_gwh'
            if col in self.data.columns:
                demand = self.data[col].values

                metrics[f'{tech}_initial_demand'] = demand[0]
                metrics[f'{tech}_final_demand'] = demand[-1]
                metrics[f'{tech}_peak_demand'] = demand.max()

                # Cumulative demand
                metrics[f'{tech}_cumulative_demand'] = demand.sum()

        return metrics

    def extract_installed_base_metrics(self) -> Dict[str, Any]:
        """
        Extract installed base metrics

        Returns:
            Dictionary of installed base metrics
        """
        metrics = {}

        for tech in ['vrla', 'lithium']:
            col = f'{tech}_installed_base_gwh'
            if col in self.data.columns:
                ib = self.data[col].values
                years = self.data['year'].values

                metrics[f'{tech}_initial_ib'] = ib[0]
                metrics[f'{tech}_final_ib'] = ib[-1]
                metrics[f'{tech}_peak_ib'] = ib.max()

                # Find peak year
                peak_idx = np.argmax(ib)
                metrics[f'{tech}_peak_ib_year'] = int(years[peak_idx])

                # Growth/decline
                if ib[0] > 0:
                    metrics[f'{tech}_ib_change_pct'] = (ib[-1] - ib[0]) / ib[0] * 100

        # Total installed base
        if 'total_installed_base_gwh' in self.data.columns:
            total_ib = self.data['total_installed_base_gwh'].values
            metrics['total_initial_ib'] = total_ib[0]
            metrics['total_final_ib'] = total_ib[-1]
            metrics['total_ib_growth_pct'] = (total_ib[-1] - total_ib[0]) / total_ib[0] * 100 if total_ib[0] > 0 else 0

        return metrics

    def extract_economic_metrics(self) -> Dict[str, Any]:
        """
        Extract economic/TCO metrics

        Returns:
            Dictionary of economic metrics
        """
        metrics = {}

        # TCO values
        for tech in ['vrla', 'lithium']:
            col = f'{tech}_tco_per_kwh'
            if col in self.data.columns:
                tco = self.data[col].values
                metrics[f'{tech}_initial_tco'] = tco[0]
                metrics[f'{tech}_final_tco'] = tco[-1]
                metrics[f'{tech}_tco_change'] = tco[-1] - tco[0]
                metrics[f'{tech}_tco_change_pct'] = (tco[-1] - tco[0]) / tco[0] * 100 if tco[0] > 0 else 0

        # TCO advantage
        if 'tco_advantage' in self.data.columns:
            advantage = self.data['tco_advantage'].values
            metrics['initial_tco_advantage'] = advantage[0]
            metrics['final_tco_advantage'] = advantage[-1]
            metrics['max_tco_advantage'] = advantage.max()
            metrics['min_tco_advantage'] = advantage.min()

            # Years with positive advantage
            positive_years = sum(advantage > 0)
            metrics['years_lithium_favorable'] = positive_years

        # Capital costs
        for tech in ['vrla', 'lithium']:
            col = f'{tech}_capex_per_kwh'
            if col in self.data.columns:
                capex = self.data[col].values
                metrics[f'{tech}_initial_capex'] = capex[0]
                metrics[f'{tech}_final_capex'] = capex[-1]
                metrics[f'{tech}_capex_decline_pct'] = (capex[-1] - capex[0]) / capex[0] * 100 if capex[0] > 0 else 0

        return metrics

    def extract_market_decomposition_metrics(self) -> Dict[str, Any]:
        """
        Extract market decomposition metrics

        Returns:
            Dictionary of market decomposition metrics
        """
        metrics = {}

        # New build vs replacement
        if 'new_build_demand_gwh' in self.data.columns:
            new_build = self.data['new_build_demand_gwh'].values
            metrics['total_new_build'] = new_build.sum()
            metrics['avg_new_build'] = new_build.mean()
            metrics['peak_new_build'] = new_build.max()

        if 'replacement_demand_gwh' in self.data.columns:
            replacement = self.data['replacement_demand_gwh'].values
            metrics['total_replacement'] = replacement.sum()
            metrics['avg_replacement'] = replacement.mean()
            metrics['peak_replacement'] = replacement.max()

            # Replacement share of total
            if 'total_demand_gwh' in self.data.columns:
                total = self.data['total_demand_gwh'].values
                replacement_share = replacement / total * 100
                metrics['avg_replacement_share'] = replacement_share.mean()
                metrics['final_replacement_share'] = replacement_share[-1]

        # Contestable market
        if 'contestable_market_gwh' in self.data.columns:
            contestable = self.data['contestable_market_gwh'].values
            metrics['total_contestable'] = contestable.sum()
            metrics['peak_contestable'] = contestable.max()

        return metrics

    def extract_all_metrics(self) -> Dict[str, Any]:
        """
        Extract all available metrics

        Returns:
            Comprehensive dictionary of all metrics
        """
        all_metrics = {
            'tipping_point': self.extract_tipping_point(),
            'adoption': self.extract_adoption_metrics(),
            'demand': self.extract_demand_metrics(),
            'installed_base': self.extract_installed_base_metrics(),
            'economic': self.extract_economic_metrics(),
            'market_decomposition': self.extract_market_decomposition_metrics()
        }

        # Flatten the structure for easier access
        flattened = {}
        for category, metrics in all_metrics.items():
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    flattened[f"{category}.{key}"] = value
            else:
                flattened[category] = metrics

        self.metrics = flattened
        return flattened

    def filter_metrics(self, pattern: str) -> Dict[str, Any]:
        """
        Filter metrics by pattern

        Args:
            pattern: Pattern to match metric names

        Returns:
            Filtered metrics dictionary
        """
        if not self.metrics:
            self.extract_all_metrics()

        filtered = {}
        for key, value in self.metrics.items():
            if pattern.lower() in key.lower():
                filtered[key] = value

        return filtered

    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Get key summary metrics

        Returns:
            Dictionary of summary metrics
        """
        if not self.metrics:
            self.extract_all_metrics()

        summary_keys = [
            'tipping_point',
            'adoption.final_lithium_share',
            'adoption.year_50pct',
            'adoption.lithium_share_2030',
            'adoption.lithium_share_2035',
            'adoption.lithium_share_2040',
            'demand.total_demand_cagr',
            'demand.lithium_cumulative_demand',
            'economic.final_tco_advantage',
            'installed_base.total_final_ib'
        ]

        summary = {}
        for key in summary_keys:
            if key in self.metrics:
                summary[key] = self.metrics[key]

        return summary

    def export_metrics(self, output_path: str, format: str = 'json'):
        """
        Export metrics to file

        Args:
            output_path: Path to save metrics
            format: Output format ('json', 'csv', 'txt')
        """
        if not self.metrics:
            self.extract_all_metrics()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        elif format == 'csv':
            df = pd.DataFrame([self.metrics])
            df.to_csv(output_path, index=False)
        elif format == 'txt':
            with open(output_path, 'w') as f:
                for key, value in self.metrics.items():
                    f.write(f"{key}: {value}\n")
        else:
            raise ValueError(f"Unsupported format: {format}")

        print(f"✓ Metrics exported to: {output_path}")

    def print_report(self, detailed: bool = False):
        """
        Print metrics report

        Args:
            detailed: Whether to print all metrics or just summary
        """
        if not self.metrics:
            self.extract_all_metrics()

        print("\n" + "=" * 70)
        print("METRICS EXTRACTION REPORT")
        print("=" * 70)

        if detailed:
            # Print all metrics grouped by category
            categories = {}
            for key, value in self.metrics.items():
                if '.' in key:
                    category, metric = key.split('.', 1)
                else:
                    category, metric = 'general', key

                if category not in categories:
                    categories[category] = []
                categories[category].append((metric, value))

            for category, metrics in sorted(categories.items()):
                print(f"\n{category.upper()} METRICS:")
                print("-" * 40)
                for metric, value in sorted(metrics):
                    if value is not None:
                        if isinstance(value, float):
                            if 'pct' in metric or 'share' in metric or 'cagr' in metric:
                                print(f"  {metric}: {value:.1f}%")
                            else:
                                print(f"  {metric}: {value:.2f}")
                        else:
                            print(f"  {metric}: {value}")
        else:
            # Print summary only
            summary = self.get_summary_metrics()
            print("\nKEY METRICS:")
            print("-" * 40)

            # Tipping point
            if 'tipping_point' in summary:
                print(f"  Tipping Point: {summary['tipping_point']}")

            # Adoption metrics
            print("\nAdoption:")
            for key, value in summary.items():
                if 'adoption.' in key and value is not None:
                    metric_name = key.replace('adoption.', '')
                    if 'share' in metric_name:
                        print(f"  {metric_name}: {value:.1f}%")
                    else:
                        print(f"  {metric_name}: {value}")

            # Demand metrics
            print("\nDemand:")
            for key, value in summary.items():
                if 'demand.' in key and value is not None:
                    metric_name = key.replace('demand.', '')
                    if 'cagr' in metric_name:
                        print(f"  {metric_name}: {value*100:.1f}%")
                    else:
                        print(f"  {metric_name}: {value:.2f}")

            # Economic metrics
            print("\nEconomic:")
            for key, value in summary.items():
                if 'economic.' in key and value is not None:
                    metric_name = key.replace('economic.', '')
                    print(f"  {metric_name}: ${value:.2f}/kWh")

        print("\n" + "=" * 70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Extract metrics from datacenter UPS forecast results')
    parser.add_argument('input', type=str, help='Path to forecast output file (CSV or JSON)')
    parser.add_argument('--metrics', type=str, help='Comma-separated list of specific metrics to extract')
    parser.add_argument('--filter', type=str, help='Filter metrics by pattern')
    parser.add_argument('--summary', action='store_true', help='Extract summary metrics only')
    parser.add_argument('--output', type=str, help='Save metrics to file')
    parser.add_argument('--format', type=str, default='json',
                       choices=['json', 'csv', 'txt'],
                       help='Output format')
    parser.add_argument('--detailed', action='store_true', help='Print detailed report')

    args = parser.parse_args()

    # Initialize extractor
    extractor = MetricsExtractor()

    # Load data
    try:
        extractor.load_data(args.input)
        print(f"✓ Loaded data from: {args.input}")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return 1

    # Extract metrics
    if args.metrics:
        # Extract specific metrics
        metric_names = args.metrics.split(',')
        all_metrics = extractor.extract_all_metrics()
        selected_metrics = {}
        for name in metric_names:
            if name in all_metrics:
                selected_metrics[name] = all_metrics[name]
            else:
                print(f"Warning: Metric '{name}' not found")

        if selected_metrics:
            print("\nSelected Metrics:")
            for key, value in selected_metrics.items():
                print(f"  {key}: {value}")

    elif args.filter:
        # Filter metrics by pattern
        filtered = extractor.filter_metrics(args.filter)
        print(f"\nMetrics matching '{args.filter}':")
        for key, value in filtered.items():
            if value is not None:
                print(f"  {key}: {value}")

    elif args.summary:
        # Get summary metrics
        summary = extractor.get_summary_metrics()
        print("\nSummary Metrics:")
        for key, value in summary.items():
            if value is not None:
                print(f"  {key}: {value}")
    else:
        # Extract all metrics
        extractor.extract_all_metrics()

    # Export if requested
    if args.output:
        extractor.export_metrics(args.output, args.format)

    # Print report
    extractor.print_report(detailed=args.detailed)

    return 0


if __name__ == "__main__":
    sys.exit(main())