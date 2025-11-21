"""
Main Forecasting Module for Light Vehicle Demand
Orchestrates the complete forecasting pipeline for two-wheelers and three-wheelers
"""

import json
import os
import sys
import pandas as pd
import numpy as np
import argparse
from typing import Dict, Optional, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_config import VehicleConfig
from common.data_loader import DataLoader
from common.cost_analysis import run_cost_analysis
from common.demand_forecast import run_demand_forecast


class ForecastOrchestrator:
    """Main class to orchestrate the light vehicle forecasting process"""

    def __init__(
        self,
        vehicle_type: str,
        end_year: int = 2040,
        logistic_ceiling: float = 0.9,
        track_fleet: bool = False
    ):
        """
        Initialize forecaster

        Args:
            vehicle_type: Type of vehicle ('two_wheeler' or 'three_wheeler')
            end_year: Final forecast year
            logistic_ceiling: Maximum EV adoption share (0.9 = 90%)
            track_fleet: Whether to track fleet evolution
        """
        self.vehicle_type = vehicle_type
        self.end_year = end_year
        self.logistic_ceiling = logistic_ceiling
        self.track_fleet = track_fleet

        # Initialize vehicle configuration
        self.vehicle_config = VehicleConfig(vehicle_type)
        self.data_loader = DataLoader(self.vehicle_config)

    def forecast_region(self, region: str) -> Dict[str, any]:
        """
        Run complete forecast for a single region

        Args:
            region: Region name

        Returns:
            Dictionary containing all forecasts and analyses
        """
        display_name = self.vehicle_config.get_display_name()

        print(f"\n{'='*70}")
        print(f"{display_name} Demand Forecast for Region: {region}")
        print(f"{'='*70}")

        # Validate region
        if not self.vehicle_config.is_region_supported(region):
            raise ValueError(
                f"Region {region} not supported for {display_name}. "
                f"Supported regions: {', '.join(self.vehicle_config.get_regions())}"
            )

        # Step 1: Cost Analysis & Tipping Point Detection
        print("\n[1/2] Running cost analysis and tipping point detection...")
        cost_result = run_cost_analysis(
            self.data_loader,
            region,
            end_year=self.end_year,
            include_sensitivity=False,
            vehicle_type=display_name
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
        print(f"    Market:  {demand_result['market'][final_idx]:>12,.0f} units")

        ev_share = demand_result['ev'][final_idx] / demand_result['market'][final_idx] * 100
        ice_share = demand_result['ice'][final_idx] / demand_result['market'][final_idx] * 100

        print(f"    EV:      {demand_result['ev'][final_idx]:>12,.0f} units ({ev_share:.1f}%)")
        print(f"    ICE:     {demand_result['ice'][final_idx]:>12,.0f} units ({ice_share:.1f}%)")

        if self.track_fleet and 'ev_fleet' in demand_result:
            print(f"\n  Fleet Evolution for {final_year}:")
            print(f"    EV Fleet:    {demand_result['ev_fleet'][final_idx]:>12,.0f} units")
            print(f"    ICE Fleet:   {demand_result['ice_fleet'][final_idx]:>12,.0f} units")
            print(f"    Total Fleet: {demand_result['total_fleet'][final_idx]:>12,.0f} units")

        print(f"{'='*70}\n")

        # Combine results
        result = {
            'region': region,
            'vehicle_type': self.vehicle_type,
            'cost_analysis': cost_result,
            'demand_forecast': demand_result
        }

        return result

    def forecast_global(self) -> Dict[str, any]:
        """
        Run forecast for all regions and aggregate to global totals

        Returns:
            Dictionary with regional and global forecasts
        """
        display_name = self.vehicle_config.get_display_name(plural=True)
        regions = self.vehicle_config.get_regions()

        print(f"\n{'='*70}")
        print(f"Global {display_name} Demand Forecast")
        print(f"Regions: {', '.join(regions)}")
        print(f"{'='*70}\n")

        regional_results = {}
        for region in regions:
            regional_results[region] = self.forecast_region(region)

        # Aggregate to global
        print(f"\nAggregating regional forecasts to global totals...")

        years = regional_results[regions[0]]['demand_forecast']['years']
        global_market = np.zeros_like(years, dtype=float)
        global_ev = np.zeros_like(years, dtype=float)
        global_ice = np.zeros_like(years, dtype=float)

        for region in regions:
            demand = regional_results[region]['demand_forecast']
            global_market += demand['market']
            global_ev += demand['ev']
            global_ice += demand['ice']

        # Create global forecast result
        global_result = {
            'years': years,
            'market': global_market,
            'ev': global_ev,
            'ice': global_ice
        }

        print(f"✓ Global aggregation complete\n")

        return {
            'vehicle_type': self.vehicle_type,
            'regional': regional_results,
            'global': global_result
        }

    def export_to_csv(self, result: Dict, output_path: Path):
        """Export forecast result to CSV"""
        demand = result['demand_forecast']
        cost = result['cost_analysis']
        region = result['region']

        # Build DataFrame
        data = {
            'Year': demand['years'].astype(int),
            'Market': demand['market'].astype(int),
            'EV': demand['ev'].astype(int),
            'ICE': demand['ice'].astype(int),
            'EV_Share': (demand['ev'] / demand['market'] * 100).round(2),
            'ICE_Share': (demand['ice'] / demand['market'] * 100).round(2),
            'EV_Cost': np.interp(demand['years'], cost['years'], cost['ev_costs']).round(2),
            'ICE_Cost': np.interp(demand['years'], cost['years'], cost['ice_costs']).round(2)
        }

        if self.track_fleet and 'ev_fleet' in demand:
            data['EV_Fleet'] = demand['ev_fleet'].astype(int)
            data['ICE_Fleet'] = demand['ice_fleet'].astype(int)
            data['Total_Fleet'] = demand['total_fleet'].astype(int)

        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        print(f"✓ CSV exported: {output_path}")

    def export_to_json(self, result: Dict, output_path: Path):
        """Export forecast result to JSON"""
        # Convert numpy arrays to lists for JSON serialization
        def convert_arrays(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_arrays(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_arrays(item) for item in obj]
            else:
                return obj

        json_data = convert_arrays(result)

        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)

        print(f"✓ JSON exported: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Light Vehicle Demand Forecasting Tool'
    )

    parser.add_argument(
        '--vehicle-type',
        type=str,
        required=True,
        choices=['two_wheeler', 'three_wheeler'],
        help='Type of vehicle to forecast'
    )

    parser.add_argument(
        '--region',
        type=str,
        required=True,
        help='Region name (or "Global" for all regions)'
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
        help='Maximum EV adoption share, 0.0-1.0 (default: 0.9)'
    )

    parser.add_argument(
        '--output',
        type=str,
        choices=['csv', 'json', 'both'],
        default='csv',
        help='Output format (default: csv)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: ./output/{vehicle_type})'
    )

    parser.add_argument(
        '--track-fleet',
        action='store_true',
        help='Enable fleet evolution tracking'
    )

    args = parser.parse_args()

    # Initialize forecaster
    forecaster = ForecastOrchestrator(
        vehicle_type=args.vehicle_type,
        end_year=args.end_year,
        logistic_ceiling=args.ceiling,
        track_fleet=args.track_fleet
    )

    # Set output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = forecaster.vehicle_config.get_output_directory()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Run forecast
    if args.region.lower() == 'global':
        result = forecaster.forecast_global()

        # Export regional CSVs
        if args.output in ['csv', 'both']:
            for region, regional_result in result['regional'].items():
                filename = f"{args.vehicle_type}_{region}_{args.end_year}.csv"
                forecaster.export_to_csv(regional_result, output_dir / filename)

            # Export global CSV
            global_csv_data = {
                'Year': result['global']['years'].astype(int),
                'Market': result['global']['market'].astype(int),
                'EV': result['global']['ev'].astype(int),
                'ICE': result['global']['ice'].astype(int),
                'EV_Share': (result['global']['ev'] / result['global']['market'] * 100).round(2),
                'ICE_Share': (result['global']['ice'] / result['global']['market'] * 100).round(2)
            }
            df_global = pd.DataFrame(global_csv_data)
            global_filename = f"{args.vehicle_type}_Global_{args.end_year}_global.csv"
            df_global.to_csv(output_dir / global_filename, index=False)
            print(f"✓ Global CSV exported: {output_dir / global_filename}")

        if args.output in ['json', 'both']:
            filename = f"{args.vehicle_type}_Global_{args.end_year}.json"
            forecaster.export_to_json(result, output_dir / filename)

    else:
        result = forecaster.forecast_region(args.region)

        filename_prefix = f"{args.vehicle_type}_{args.region}_{args.end_year}"

        if args.output in ['csv', 'both']:
            csv_path = output_dir / f"{filename_prefix}.csv"
            forecaster.export_to_csv(result, csv_path)

        if args.output in ['json', 'both']:
            json_path = output_dir / f"{filename_prefix}.json"
            forecaster.export_to_json(result, json_path)

    print(f"\n✓ Forecast complete!")


if __name__ == "__main__":
    main()
