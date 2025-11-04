"""
Main Forecasting Module
Orchestrates the complete forecasting pipeline
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from data_loader import DataLoader
from cost_analysis import run_cost_analysis
from demand_forecast import run_demand_forecast


class ForecastOrchestrator:
    """Main class to orchestrate the forecasting process"""

    def __init__(
        self,
        end_year: int = 2040,
        logistic_ceiling: float = 1.0,
        data_dir: Optional[str] = None
    ):
        """
        Initialize forecaster

        Args:
            end_year: Final forecast year
            logistic_ceiling: Maximum EV adoption share
            data_dir: Path to data directory (if None, uses skill's data dir)
        """
        self.end_year = end_year
        self.logistic_ceiling = logistic_ceiling
        self.data_loader = DataLoader(data_dir)

    def forecast_region(self, region: str) -> Dict[str, any]:
        """
        Run complete forecast for a single region

        Args:
            region: Region name (China, USA, Europe, Rest_of_World)

        Returns:
            Dictionary containing all forecasts and analyses
        """
        print(f"\n{'='*60}")
        print(f"Forecasting for Region: {region}")
        print(f"{'='*60}")

        # Step 1: Cost Analysis
        print("\n[1/2] Running cost analysis...")
        cost_result = run_cost_analysis(
            self.data_loader,
            region,
            end_year=self.end_year
        )

        tipping_point = cost_result['tipping_point']
        print(f"  ✓ Tipping point: {tipping_point if tipping_point else 'None (ICE remains cheaper)'}")
        print(f"  ✓ EV CAGR: {cost_result['ev_cagr']:.2%}")
        print(f"  ✓ ICE CAGR: {cost_result['ice_cagr']:.2%}")

        # Step 2: Demand Forecast
        print("\n[2/2] Running demand forecast...")
        demand_result = run_demand_forecast(
            self.data_loader,
            region,
            tipping_point,
            end_year=self.end_year,
            logistic_ceiling=self.logistic_ceiling
        )

        validation = demand_result['validation']
        if validation['is_valid']:
            print(f"  ✓ Validation passed")
        else:
            print(f"  ⚠ Validation warning: {validation['message']}")

        # Print forecast summary
        final_idx = -1
        print(f"\n  Forecast for {int(demand_result['years'][final_idx])}:")
        print(f"    Market:  {demand_result['market'][final_idx]:>12,.0f}")
        print(f"    BEV:     {demand_result['bev'][final_idx]:>12,.0f} ({demand_result['bev'][final_idx]/demand_result['market'][final_idx]*100:.1f}%)")
        print(f"    PHEV:    {demand_result['phev'][final_idx]:>12,.0f} ({demand_result['phev'][final_idx]/demand_result['market'][final_idx]*100:.1f}%)")
        print(f"    ICE:     {demand_result['ice'][final_idx]:>12,.0f} ({demand_result['ice'][final_idx]/demand_result['market'][final_idx]*100:.1f}%)")
        print(f"    EV:      {demand_result['ev'][final_idx]:>12,.0f} ({demand_result['ev'][final_idx]/demand_result['market'][final_idx]*100:.1f}%)")

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
        print("\n" + "="*60)
        print("GLOBAL FORECASTING")
        print("="*60)

        regions = ["China", "USA", "Europe", "Rest_of_World"]
        regional_results = {}

        # Forecast each region
        for region in regions:
            regional_results[region] = self.forecast_region(region)

        # Aggregate to global
        print("\n" + "="*60)
        print("Aggregating to Global")
        print("="*60)

        # Get years from first region
        years = regional_results[regions[0]]['demand_forecast']['years']

        # Initialize aggregated arrays
        global_market = np.zeros_like(years, dtype=float)
        global_bev = np.zeros_like(years, dtype=float)
        global_phev = np.zeros_like(years, dtype=float)
        global_ice = np.zeros_like(years, dtype=float)

        # Sum across regions
        for region in regions:
            demand = regional_results[region]['demand_forecast']
            # Interpolate to common years if needed
            regional_years = demand['years']
            global_market += np.interp(years, regional_years, demand['market'])
            global_bev += np.interp(years, regional_years, demand['bev'])
            global_phev += np.interp(years, regional_years, demand['phev'])
            global_ice += np.interp(years, regional_years, demand['ice'])

        global_ev = global_bev + global_phev

        print(f"\n  Global Forecast for {int(years[-1])}:")
        print(f"    Market:  {global_market[-1]:>12,.0f}")
        print(f"    BEV:     {global_bev[-1]:>12,.0f} ({global_bev[-1]/global_market[-1]*100:.1f}%)")
        print(f"    PHEV:    {global_phev[-1]:>12,.0f} ({global_phev[-1]/global_market[-1]*100:.1f}%)")
        print(f"    ICE:     {global_ice[-1]:>12,.0f} ({global_ice[-1]/global_market[-1]*100:.1f}%)")
        print(f"    EV:      {global_ev[-1]:>12,.0f} ({global_ev[-1]/global_market[-1]*100:.1f}%)")

        # Create global result
        global_result = {
            'region': 'Global',
            'years': years,
            'market': global_market,
            'bev': global_bev,
            'phev': global_phev,
            'ice': global_ice,
            'ev': global_ev
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
                'BEV': result['bev'],
                'PHEV': result['phev'],
                'ICE': result['ice'],
                'EV': result['ev']
            })
        else:
            # Export regional data
            demand = result['demand_forecast']
            cost = result['cost_analysis']

            df = pd.DataFrame({
                'Year': demand['years'].astype(int),
                'Market': demand['market'],
                'BEV': demand['bev'],
                'PHEV': demand['phev'],
                'ICE': demand['ice'],
                'EV': demand['ev'],
                'EV_Cost': np.interp(demand['years'], cost['years'], cost['ev_costs']),
                'ICE_Cost': np.interp(demand['years'], cost['years'], cost['ice_costs'])
            })

        df.to_csv(output_path, index=False)
        print(f"\n✓ Exported to: {output_path}")

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

        print(f"\n✓ Exported to: {output_path}")


def main():
    """Main entry point for forecasting"""
    import argparse

    parser = argparse.ArgumentParser(description='Cost-Driven Demand Forecasting')
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
        default=1.0,
        help='Logistic ceiling for EV adoption (default: 1.0 = 100%%)'
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

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = ForecastOrchestrator(
        end_year=args.end_year,
        logistic_ceiling=args.ceiling
    )

    # Run forecast
    if args.region == "Global":
        result = orchestrator.forecast_global()
    else:
        result = orchestrator.forecast_region(args.region)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Export results
    base_filename = f"{args.region}_{args.end_year}"

    if args.output in ['csv', 'both']:
        if args.region == "Global":
            # Export global
            csv_path = os.path.join(args.output_dir, f"{base_filename}_global.csv")
            orchestrator.export_to_csv(result['global_result'], csv_path, "Global")

            # Export each region
            for region_name, region_result in result['regional_results'].items():
                csv_path = os.path.join(args.output_dir, f"{region_name}_{args.end_year}.csv")
                orchestrator.export_to_csv(region_result, csv_path, region_name)
        else:
            csv_path = os.path.join(args.output_dir, f"{base_filename}.csv")
            orchestrator.export_to_csv(result, csv_path, args.region)

    if args.output in ['json', 'both']:
        json_path = os.path.join(args.output_dir, f"{base_filename}.json")
        orchestrator.export_to_json(result, json_path)

    print("\n" + "="*60)
    print("Forecasting Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
