"""
Main Forecasting Module for Commercial Vehicle Demand
Orchestrates the complete forecasting pipeline with segment-level analysis
Supports LCV, MCV, HCV segments and three powertrains (EV, ICE, NGV)
"""

import json
import os
import sys
import pandas as pd
import numpy as np
import argparse
from typing import Dict, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from cost_analysis import run_cost_analysis
from demand_forecast import run_demand_forecast_segment


class ForecastOrchestrator:
    """Main class to orchestrate the commercial vehicle forecasting process"""

    def __init__(
        self,
        end_year: int = 2040,
        segment_ceilings: Optional[Dict[str, float]] = None,
        data_dir: Optional[str] = None,
        track_fleet: bool = False,
        fleet_lifetimes: Optional[Dict[str, float]] = None,
        ngv_half_life: float = 6.0
    ):
        """
        Initialize forecaster

        Args:
            end_year: Final forecast year
            segment_ceilings: Dict of segment-specific EV ceilings {"LCV": 0.95, "MCV": 0.85, "HCV": 0.75}
            data_dir: Path to data directory (if None, uses skill's data dir)
            track_fleet: Whether to track fleet evolution
            fleet_lifetimes: Dict of segment-specific lifetimes {"LCV": 12, "MCV": 15, "HCV": 18}
            ngv_half_life: NGV decline half-life in years
        """
        self.end_year = end_year
        self.track_fleet = track_fleet
        self.data_loader = DataLoader(data_dir)

        # Set default segment-specific ceilings
        if segment_ceilings is None:
            segment_ceilings = {
                "LCV": 0.95,  # Light duty - easier to electrify
                "MCV": 0.85,  # Medium duty
                "HCV": 0.75   # Heavy duty - harder due to range/weight
            }
        self.segment_ceilings = segment_ceilings

        # Set default fleet lifetimes
        if fleet_lifetimes is None:
            fleet_lifetimes = {
                "LCV": 12.0,
                "MCV": 15.0,
                "HCV": 18.0
            }
        self.fleet_lifetimes = fleet_lifetimes

        # NGV configuration
        self.ngv_config = {
            'half_life_years': ngv_half_life,
            'peak_detection_window': 5,
            'target_share_2040': 0.0,
            'min_significant_share': 0.01
        }

    def forecast_segment(self, region: str, segment: str) -> Dict[str, any]:
        """
        Run complete forecast for a single segment in a region

        Args:
            region: Region name (China, USA, Europe, Rest_of_World)
            segment: Segment identifier (LCV, MCV, HCV)

        Returns:
            Dictionary containing all forecasts and analyses for the segment
        """
        print(f"\n{'-'*70}")
        print(f"  Segment: {segment}")
        print(f"{'-'*70}")

        # Step 1: Cost Analysis & Tipping Point Detection
        print(f"  [1/2] Cost analysis for {segment}...")
        cost_result = run_cost_analysis(
            self.data_loader,
            region,
            segments=[segment],
            end_year=self.end_year
        )

        segment_cost = cost_result[segment]
        tipping_point = segment_cost['tipping_point']

        if tipping_point:
            print(f"    ✓ Tipping point: {tipping_point}")
        else:
            print(f"    ⚠ No tipping point found")

        print(f"    ✓ EV CAGR: {segment_cost['ev_cagr']:.2%}")
        print(f"    ✓ ICE CAGR: {segment_cost['ice_cagr']:.2%}")

        # Step 2: Demand Forecast
        print(f"  [2/2] Demand forecast for {segment}...")
        demand_result = run_demand_forecast_segment(
            self.data_loader,
            region,
            segment,
            tipping_point,
            end_year=self.end_year,
            logistic_ceiling=self.segment_ceilings.get(segment, 0.9),
            track_fleet=self.track_fleet,
            fleet_lifetime=self.fleet_lifetimes.get(segment, 15.0),
            ngv_config=self.ngv_config
        )

        validation = demand_result['validation']
        if validation['is_valid']:
            print(f"    ✓ Validation passed")
        else:
            print(f"    ⚠ Validation warning: {validation['message']}")

        # Print forecast summary
        final_idx = -1
        final_year = int(demand_result['years'][final_idx])
        print(f"\n    Forecast Summary for {final_year}:")
        print(f"      Market:  {demand_result['market'][final_idx]:>12,.0f} units")
        print(f"      EV:      {demand_result['ev'][final_idx]:>12,.0f} units ({demand_result['ev_share'][final_idx]:>5.1%})")
        print(f"      ICE:     {demand_result['ice'][final_idx]:>12,.0f} units ({demand_result['ice_share'][final_idx]:>5.1%})")
        print(f"      NGV:     {demand_result['ngv'][final_idx]:>12,.0f} units ({demand_result['ngv_share'][final_idx]:>5.1%})")

        # Combine results
        result = {
            'segment': segment,
            'cost_analysis': segment_cost,
            'demand_forecast': demand_result
        }

        return result

    def forecast_region(self, region: str, segments: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Run complete forecast for a region (all segments or specified segments)

        Args:
            region: Region name
            segments: List of segments to forecast (None = all segments)

        Returns:
            Dictionary containing segment-level and aggregated forecasts
        """
        if segments is None:
            segments = ["LCV", "MCV", "HCV"]

        print(f"\n{'='*70}")
        print(f"Commercial Vehicle Demand Forecast for Region: {region}")
        print(f"{'='*70}")

        segment_results = {}

        # Forecast each segment
        for segment in segments:
            try:
                segment_results[segment] = self.forecast_segment(region, segment)
            except Exception as e:
                print(f"\n✗ Error forecasting {segment}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Aggregate segments to total CV
        print(f"\n{'-'*70}")
        print(f"  Aggregating Segments to Total Commercial Vehicles")
        print(f"{'-'*70}")

        if not segment_results:
            print("  ✗ No segment results to aggregate")
            return {'region': region, 'segment_results': {}, 'total_cv': None}

        # Get years from first segment
        first_segment = list(segment_results.values())[0]
        years = first_segment['demand_forecast']['years']

        # Initialize aggregated arrays
        total_market = np.zeros_like(years, dtype=float)
        total_ev = np.zeros_like(years, dtype=float)
        total_ice = np.zeros_like(years, dtype=float)
        total_ngv = np.zeros_like(years, dtype=float)

        # Sum across segments
        for segment, result in segment_results.items():
            demand = result['demand_forecast']
            seg_years = demand['years']
            # Interpolate to common years if needed
            total_market += np.interp(years, seg_years, demand['market'])
            total_ev += np.interp(years, seg_years, demand['ev'])
            total_ice += np.interp(years, seg_years, demand['ice'])
            total_ngv += np.interp(years, seg_years, demand['ngv'])

        final_year = int(years[-1])
        print(f"\n  Total CV Forecast for {final_year}:")
        print(f"    Market:  {total_market[-1]:>15,.0f} units")
        print(f"    EV:      {total_ev[-1]:>15,.0f} units ({total_ev[-1]/total_market[-1]:>5.1%})")
        print(f"    ICE:     {total_ice[-1]:>15,.0f} units ({total_ice[-1]/total_market[-1]:>5.1%})")
        print(f"    NGV:     {total_ngv[-1]:>15,.0f} units ({total_ngv[-1]/total_market[-1]:>5.1%})")

        # Create total CV result
        total_cv_result = {
            'region': region,
            'years': years,
            'market': total_market,
            'ev': total_ev,
            'ice': total_ice,
            'ngv': total_ngv,
            'ev_share': total_ev / np.maximum(total_market, 1),
            'ice_share': total_ice / np.maximum(total_market, 1),
            'ngv_share': total_ngv / np.maximum(total_market, 1)
        }

        return {
            'region': region,
            'segment_results': segment_results,
            'total_cv': total_cv_result
        }

    def export_to_csv(self, result: Dict, output_path: str):
        """
        Export forecast results to CSV format

        Args:
            result: Forecast result dictionary
            output_path: Path to output CSV file
        """
        rows = []

        region = result['region']
        total_cv = result.get('total_cv')

        # Export segment-level data
        for segment, seg_result in result.get('segment_results', {}).items():
            demand = seg_result['demand_forecast']
            years = demand['years']

            for i, year in enumerate(years):
                row = {
                    'Region': region,
                    'Segment': segment,
                    'Year': int(year),
                    'Market': demand['market'][i],
                    'EV': demand['ev'][i],
                    'ICE': demand['ice'][i],
                    'NGV': demand['ngv'][i],
                    'EV_Share': demand['ev_share'][i],
                    'ICE_Share': demand['ice_share'][i],
                    'NGV_Share': demand['ngv_share'][i]
                }

                # Add fleet data if available
                if 'fleet' in demand and 'error' not in demand['fleet']:
                    fleet = demand['fleet']
                    row['EV_Fleet'] = fleet['ev'][i]
                    row['ICE_Fleet'] = fleet['ice'][i]
                    row['NGV_Fleet'] = fleet['ngv'][i]
                    row['Total_Fleet'] = fleet['total'][i]

                rows.append(row)

        # Export total CV aggregated data
        if total_cv:
            years = total_cv['years']
            for i, year in enumerate(years):
                row = {
                    'Region': region,
                    'Segment': 'Total_CV',
                    'Year': int(year),
                    'Market': total_cv['market'][i],
                    'EV': total_cv['ev'][i],
                    'ICE': total_cv['ice'][i],
                    'NGV': total_cv['ngv'][i],
                    'EV_Share': total_cv['ev_share'][i],
                    'ICE_Share': total_cv['ice_share'][i],
                    'NGV_Share': total_cv['ngv_share'][i]
                }
                rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        print(f"\n✓ Results exported to: {output_path}")

    def export_to_json(self, result: Dict, output_path: str):
        """
        Export forecast results to JSON format

        Args:
            result: Forecast result dictionary
            output_path: Path to output JSON file
        """
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            else:
                return obj

        result_json = convert_numpy(result)

        with open(output_path, 'w') as f:
            json.dump(result_json, f, indent=2)

        print(f"\n✓ Results exported to: {output_path}")


def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Commercial Vehicle Demand Forecasting with EV Disruption Analysis"
    )

    parser.add_argument(
        "--region",
        type=str,
        required=True,
        help="Region to forecast (China, USA, Europe, Rest_of_World, Global)"
    )

    parser.add_argument(
        "--segment",
        type=str,
        default=None,
        help="Specific segment to forecast (LCV, MCV, HCV). If not specified, forecasts all segments."
    )

    parser.add_argument(
        "--all-segments",
        action="store_true",
        help="Forecast all segments (LCV, MCV, HCV)"
    )

    parser.add_argument(
        "--end-year",
        type=int,
        default=2040,
        help="Final forecast year (default: 2040)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="csv",
        choices=["csv", "json", "both"],
        help="Output format (default: csv)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results"
    )

    parser.add_argument(
        "--track-fleet",
        action="store_true",
        help="Enable fleet tracking (vehicle stock evolution)"
    )

    parser.add_argument(
        "--ngv-half-life",
        type=float,
        default=6.0,
        help="NGV decline half-life in years (default: 6.0)"
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir is None:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        skill_dir = os.path.dirname(scripts_dir)
        output_dir = os.path.join(skill_dir, "output")
    else:
        output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    # Determine segments to forecast
    if args.segment:
        segments = [args.segment.upper()]
    elif args.all_segments:
        segments = ["LCV", "MCV", "HCV"]
    else:
        segments = ["LCV", "MCV", "HCV"]  # Default: all segments

    # Initialize orchestrator
    orchestrator = ForecastOrchestrator(
        end_year=args.end_year,
        track_fleet=args.track_fleet,
        ngv_half_life=args.ngv_half_life
    )

    # Run forecast
    result = orchestrator.forecast_region(args.region, segments=segments)

    # Export results
    base_filename = f"commercial_vehicle_{args.region}_{args.end_year}"

    if args.output in ["csv", "both"]:
        csv_path = os.path.join(output_dir, f"{base_filename}.csv")
        orchestrator.export_to_csv(result, csv_path)

    if args.output in ["json", "both"]:
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        orchestrator.export_to_json(result, json_path)

    print(f"\n{'='*70}")
    print("Forecast Complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
