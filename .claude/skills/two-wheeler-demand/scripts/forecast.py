"""
Main Forecasting Module for Two-Wheeler Demand
Orchestrates the complete forecasting pipeline
"""

import json
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from cost_analysis import run_cost_analysis
from demand_forecast import run_demand_forecast


class ForecastOrchestrator:
    """Main class to orchestrate the two-wheeler forecasting process"""

    def __init__(
        self,
        end_year: int = 2040,
        logistic_ceiling: float = 0.9,
        data_dir: Optional[str] = None,
        track_fleet: bool = False
    ):
        """
        Initialize forecaster

        Args:
            end_year: Final forecast year
            logistic_ceiling: Maximum EV adoption share (0.9 = 90%)
            data_dir: Path to data directory (if None, uses skill's data dir)
            track_fleet: Whether to track fleet evolution
        """
        self.end_year = end_year
        self.logistic_ceiling = logistic_ceiling
        self.track_fleet = track_fleet
        self.data_loader = DataLoader(data_dir)

    def forecast_region(self, region: str) -> Dict[str, any]:
        """
        Run complete forecast for a single region

        Args:
            region: Region name (China, USA, Europe, Rest_of_World)

        Returns:
            Dictionary containing all forecasts and analyses
        """
        print(f"\n{'='*70}")
        print(f"Two-Wheeler Demand Forecast for Region: {region}")
        print(f"{'='*70}")

        # Step 1: Cost Analysis & Tipping Point Detection
        print("\n[1/2] Running cost analysis and tipping point detection...")
        cost_result = run_cost_analysis(
            self.data_loader,
            region,
            end_year=self.end_year,
            include_sensitivity=False
        )

        tipping_point = cost_result['tipping_point']
        if tipping_point:
            print(f"  ✓ Tipping point detected: {tipping_point}")
            if cost_result.get('years_to_parity'):
                print(f"    Years to parity from 2024: {cost_result['years_to_parity']}")
        else:
            print(f"  ⚠ No tipping point found (ICE remains cheaper)")

        print(f"  ✓ EV cost CAGR: {cost_result['ev_cagr']:.2%}")
        print(f"  ✓ ICE cost CAGR: {cost_result['ice_cagr']:.2%}")
        print(f"  ✓ Current cost gap: ${cost_result['current_cost_gap']:.2f} (ICE - EV)")

        # Step 2: Demand Forecast
        print("\n[2/2] Running demand forecast...")
        demand_result = run_demand_forecast(
            self.data_loader,
            region,
            tipping_point,
            end_year=self.end_year,
            logistic_ceiling=self.logistic_ceiling,
            track_fleet=self.track_fleet
        )

        validation = demand_result['validation']
        if validation['is_valid']:
            print(f"  ✓ Validation passed")
        else:
            print(f"  ⚠ Validation warning: {validation['message']}")

        # Print forecast summary
        final_idx = -1
        final_year = int(demand_result['years'][final_idx])
        print(f"\n  Forecast Summary for {final_year}:")
        print(f"    Market:  {demand_result['market'][final_idx]:>15,.0f} units")
        print(f"    EV:      {demand_result['ev'][final_idx]:>15,.0f} units ({demand_result['ev'][final_idx]/demand_result['market'][final_idx]*100:>5.1f}%)")
        print(f"    ICE:     {demand_result['ice'][final_idx]:>15,.0f} units ({demand_result['ice'][final_idx]/demand_result['market'][final_idx]*100:>5.1f}%)")

        if 'ev_fleet' in demand_result:
            print(f"\n  Fleet Evolution for {final_year}:")
            print(f"    EV Fleet:    {demand_result['ev_fleet'][final_idx]:>15,.0f} units")
            print(f"    ICE Fleet:   {demand_result['ice_fleet'][final_idx]:>15,.0f} units")
            print(f"    Total Fleet: {demand_result['total_fleet'][final_idx]:>15,.0f} units")

        # Combine results
        result = {
            'region': region,
            'cost_analysis': cost_result,
            'demand_forecast': demand_result
        }

        return result

    def forecast_global(self) -> Dict[str, any]:
        """
        Run forecast for all regions and aggregate to global

        Returns:
            Dictionary containing regional and global forecasts
        """
        print("\n" + "="*70)
        print("GLOBAL TWO-WHEELER DEMAND FORECASTING")
        print("="*70)

        regions = ["China", "USA", "Europe", "Rest_of_World"]
        regional_results = {}

        # Forecast each region
        for region in regions:
            try:
                regional_results[region] = self.forecast_region(region)
            except Exception as e:
                print(f"\n✗ Error forecasting {region}: {e}")
                continue

        # Aggregate to global
        print("\n" + "="*70)
        print("Aggregating to Global")
        print("="*70)

        if not regional_results:
            print("  ✗ No regional results to aggregate")
            return {'regional_results': {}, 'global_result': None}

        # Get years from first region
        first_region = list(regional_results.values())[0]
        years = first_region['demand_forecast']['years']

        # Initialize aggregated arrays
        global_market = np.zeros_like(years, dtype=float)
        global_ev = np.zeros_like(years, dtype=float)
        global_ice = np.zeros_like(years, dtype=float)

        # Sum across regions
        for region, result in regional_results.items():
            demand = result['demand_forecast']
            regional_years = demand['years']
            # Interpolate to common years if needed
            global_market += np.interp(years, regional_years, demand['market'])
            global_ev += np.interp(years, regional_years, demand['ev'])
            global_ice += np.interp(years, regional_years, demand['ice'])

        final_year = int(years[-1])
        print(f"\n  Global Forecast for {final_year}:")
        print(f"    Market:  {global_market[-1]:>15,.0f} units")
        print(f"    EV:      {global_ev[-1]:>15,.0f} units ({global_ev[-1]/global_market[-1]*100:>5.1f}%)")
        print(f"    ICE:     {global_ice[-1]:>15,.0f} units ({global_ice[-1]/global_market[-1]*100:>5.1f}%)")

        # Create global result
        global_result = {
            'region': 'Global',
            'years': years,
            'market': global_market,
            'ev': global_ev,
            'ice': global_ice
        }

        result = {
            'regional_results': regional_results,
            'global_result': global_result
        }

        return result

    def export_to_csv(self, result: Dict, output_path: str, region: str):
        """
        Export forecast results to CSV

        Args:
            result: Forecast result dictionary
            output_path: Path to output CSV file
            region: Region name
        """
        if region == "Global":
            # Export global aggregated data
            df = pd.DataFrame({
                'Year': result['years'].astype(int),
                'Market': result['market'],
                'EV': result['ev'],
                'ICE': result['ice'],
                'EV_Share': result['ev'] / result['market'] * 100,
                'ICE_Share': result['ice'] / result['market'] * 100
            })
        else:
            # Export regional data
            demand = result['demand_forecast']
            cost = result['cost_analysis']

            df_data = {
                'Year': demand['years'].astype(int),
                'Market': demand['market'],
                'EV': demand['ev'],
                'ICE': demand['ice'],
                'EV_Share': demand['ev'] / demand['market'] * 100,
                'ICE_Share': demand['ice'] / demand['market'] * 100,
                'EV_Cost': np.interp(demand['years'], cost['years'], cost['ev_costs']),
                'ICE_Cost': np.interp(demand['years'], cost['years'], cost['ice_costs'])
            }

            # Add fleet data if available
            if 'ev_fleet' in demand:
                df_data['EV_Fleet'] = demand['ev_fleet']
                df_data['ICE_Fleet'] = demand['ice_fleet']
                df_data['Total_Fleet'] = demand['total_fleet']

            df = pd.DataFrame(df_data)

        df.to_csv(output_path, index=False)
        print(f"\n✓ Exported CSV to: {output_path}")

    def export_to_json(self, result: Dict, output_path: str):
        """
        Export forecast results to JSON

        Args:
            result: Forecast result dictionary
            output_path: Path to output JSON file
        """
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj

        json_data = convert_numpy(result)

        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)

        print(f"✓ Exported JSON to: {output_path}")


def main():
    """Main entry point for two-wheeler demand forecasting"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Two-Wheeler Demand Forecasting with EV Disruption Analysis'
    )
    parser.add_argument(
        '--region',
        type=str,
        required=True,
        choices=['China', 'USA', 'Europe', 'Rest_of_World', 'Global'],
        help='Region to forecast'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2040,
        help='Final forecast year (default: 2040)'
    )
    parser.add_argument(
        '--ceiling',
        type=float,
        default=0.9,
        help='Logistic ceiling for EV adoption (default: 0.9 = 90%%)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='csv',
        choices=['csv', 'json', 'both'],
        help='Output format (default: csv)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./output',
        help='Output directory (default: ./output)'
    )
    parser.add_argument(
        '--track-fleet',
        action='store_true',
        help='Track fleet evolution (stock-flow accounting)'
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = ForecastOrchestrator(
        end_year=args.end_year,
        logistic_ceiling=args.ceiling,
        track_fleet=args.track_fleet
    )

    # Run forecast
    if args.region == "Global":
        result = orchestrator.forecast_global()
    else:
        result = orchestrator.forecast_region(args.region)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Export results
    base_filename = f"two_wheeler_{args.region}_{args.end_year}"

    if args.output in ['csv', 'both']:
        if args.region == "Global":
            # Export global
            csv_path = os.path.join(args.output_dir, f"{base_filename}_global.csv")
            orchestrator.export_to_csv(result['global_result'], csv_path, "Global")

            # Export each region
            for region_name, region_result in result['regional_results'].items():
                csv_path = os.path.join(args.output_dir, f"two_wheeler_{region_name}_{args.end_year}.csv")
                orchestrator.export_to_csv(region_result, csv_path, region_name)
        else:
            csv_path = os.path.join(args.output_dir, f"{base_filename}.csv")
            orchestrator.export_to_csv(result, csv_path, args.region)

    if args.output in ['json', 'both']:
        json_path = os.path.join(args.output_dir, f"{base_filename}.json")
        orchestrator.export_to_json(result, json_path)

    print("\n" + "="*70)
    print("Two-Wheeler Demand Forecasting Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
