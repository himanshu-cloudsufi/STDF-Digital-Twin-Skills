#!/usr/bin/env python3
"""
Main Forecast Orchestrator for Energy Forecasting (SWB)
Coordinates cost analysis, capacity forecasting, and displacement sequencing
"""

import argparse
import json
import os
import sys
import numpy as np
from typing import Dict, Optional

# Import skill modules
from data_loader import DataLoader
from cost_analysis import CostAnalyzer
from capacity_forecast import CapacityForecaster
from displacement import DisplacementAnalyzer
from emissions import EmissionsCalculator
from utils import validate_energy_balance


class EnergyForecastOrchestrator:
    """Main orchestrator for SWB energy forecasting"""

    def __init__(self, end_year: int = 2030, battery_duration: int = 4, scenario: str = "baseline"):
        """
        Initialize orchestrator with scenario support

        Args:
            end_year: Final forecast year
            battery_duration: Battery duration in hours (2, 4, or 8)
            scenario: Scenario name (baseline, accelerated, delayed)
        """
        # Load configuration
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.json"
        )
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Validate scenario
        if scenario not in self.config.get("scenarios", {}):
            raise ValueError(f"Invalid scenario: {scenario}. Must be one of {list(self.config.get('scenarios', {}).keys())}")

        self.scenario = scenario
        self.scenario_config = self.config["scenarios"][scenario]

        # Update config with parameters
        self.config["default_parameters"]["end_year"] = end_year
        self.config["default_parameters"]["battery_duration_hours"] = battery_duration

        # Initialize components
        self.data_loader = DataLoader()
        self.cost_analyzer = CostAnalyzer(self.config, self.data_loader)
        self.capacity_forecaster = CapacityForecaster(self.config, self.data_loader)
        self.displacement_analyzer = DisplacementAnalyzer(self.config, self.data_loader)
        self.emissions_calculator = EmissionsCalculator(self.config, self.data_loader)

        self.end_year = end_year

    def forecast_region(self, region: str) -> Dict:
        """
        Run complete forecast for a single region

        Args:
            region: Region name

        Returns:
            Dictionary with all forecast results
        """
        print(f"\n{'='*60}")
        print(f"Forecasting {region} through {self.end_year}")
        print(f"Scenario: {self.scenario}")
        print(f"{'='*60}")

        # Step 1: Cost Analysis
        print("\n[1/5] Analyzing cost curves and detecting tipping points...")
        cost_forecasts = self.cost_analyzer.forecast_cost_curves(region, self.end_year)
        tipping_points = self.cost_analyzer.find_tipping_points(cost_forecasts)

        print(f"  - Tipping vs Coal: {tipping_points.get('tipping_vs_coal', 'Not found')}")
        print(f"  - Tipping vs Gas: {tipping_points.get('tipping_vs_gas', 'Not found')}")
        print(f"  - Overall Tipping: {tipping_points.get('tipping_overall', 'Not found')}")

        # Step 2: Capacity Forecasting
        print("\n[2/5] Forecasting SWB capacities...")
        swb_results = self.capacity_forecaster.forecast_swb_generation(region, self.end_year)
        capacity_forecasts = swb_results["capacities"]
        generation_forecasts = swb_results["generation"]

        # Calculate total SWB generation
        # First, find the common year range across all technologies
        years = None
        for tech, (tech_years, tech_generation) in generation_forecasts.items():
            if years is None:
                years = tech_years
            else:
                # Use the longest year range
                if len(tech_years) > len(years):
                    years = tech_years

        # Now sum generation, interpolating if necessary
        total_swb_generation = np.zeros(len(years))
        for tech, (tech_years, tech_generation) in generation_forecasts.items():
            if len(tech_years) == len(years) and np.array_equal(tech_years, years):
                # Years match, add directly
                total_swb_generation += tech_generation
            else:
                # Interpolate to match the common year range
                aligned_generation = np.interp(years, tech_years, tech_generation)
                total_swb_generation += aligned_generation

        print(f"  - Forecasted {len(capacity_forecasts)} SWB components")

        # Step 3: Calculate Non-SWB Baseline
        print("\n[3/5] Calculating non-SWB baseline (nuclear, hydro)...")
        non_swb_years, non_swb_generation = self.displacement_analyzer.calculate_non_swb_baseline(
            region, years
        )

        # Step 4: Get Total Electricity Demand and Peak Load
        print("\n[4/5] Loading total electricity demand and calculating peak load...")
        try:
            demand_years, total_demand = self.data_loader.get_electricity_demand(region)
            total_demand_forecast = np.interp(years, demand_years, total_demand)
        except Exception as e:
            print(f"  Warning: Could not load demand, using SWB+fossil estimate: {e}")
            # Fallback: estimate total as SWB + historical fossil
            total_demand_forecast = total_swb_generation * 2.0  # Rough estimate

        # Calculate peak load proxy
        # Peak Load (GW) = Annual Demand (TWh) × 1000 / 8760 × Load Factor
        load_factor = self.config["peak_load_factors"].get(region, 1.4)
        peak_load_gw = (total_demand_forecast * 1000 / 8760) * load_factor
        print(f"  - Peak load factor: {load_factor}x")
        print(f"  - Peak load range: {peak_load_gw.min():.1f} - {peak_load_gw.max():.1f} GW")

        # Step 5: Displacement Sequencing
        print("\n[5/5] Sequencing fossil fuel displacement...")
        coal_generation, gas_generation = self.displacement_analyzer.allocate_fossil_generation(
            years,
            total_demand_forecast,
            total_swb_generation,
            non_swb_generation,
            region
        )

        displacement_timeline = self.displacement_analyzer.calculate_displacement_timeline(
            years,
            coal_generation,
            gas_generation,
            total_swb_generation
        )

        print(f"  - Displacement sequence: {self.displacement_analyzer.get_displacement_sequence(region)}")
        print(f"  - Key milestones: {displacement_timeline}")

        # Step 6: Calculate Emissions
        print("\n[6/6] Calculating emissions trajectory...")

        # Extract individual technology generation
        solar_generation = generation_forecasts.get("Solar_PV", (years, np.zeros_like(years)))[1]
        wind_generation = total_swb_generation - solar_generation  # Approximation for wind

        emissions_data = self.emissions_calculator.calculate_emissions_trajectory(
            years,
            coal_generation,
            gas_generation,
            solar_generation,
            wind_generation
        )

        # Validate against actual emissions if available
        total_coal_emissions = np.array(emissions_data["annual_emissions_mt"]["coal"])
        emissions_validation = self.emissions_calculator.validate_against_actual(
            region,
            years,
            total_coal_emissions
        )

        if emissions_validation:
            emissions_data["validation"] = emissions_validation

        # Validation
        print("\n[Validation] Checking energy balance...")
        is_valid, message = validate_energy_balance(
            total_demand_forecast,
            total_swb_generation,
            coal_generation,
            gas_generation,
            non_swb_generation,
            tolerance=self.config["default_parameters"]["energy_balance_tolerance"]
        )
        print(f"  - {message}")

        # Compile results
        # Convert tipping_points numpy arrays to lists for JSON serialization
        tipping_points_serializable = {}
        for key, value in tipping_points.items():
            if key == "swb_stack_cost" and value is not None:
                years_arr, costs_arr = value
                tipping_points_serializable[key] = {
                    "years": years_arr.tolist() if hasattr(years_arr, 'tolist') else years_arr,
                    "costs": costs_arr.tolist() if hasattr(costs_arr, 'tolist') else costs_arr
                }
            else:
                tipping_points_serializable[key] = value

        # Extract battery metrics from swb_results
        battery_metrics = swb_results.get("battery_metrics")

        result = {
            "region": region,
            "end_year": self.end_year,
            "scenario": self.scenario,
            "scenario_config": self.scenario_config,
            "cost_analysis": {
                "tipping_points": tipping_points_serializable,
                "cost_forecasts": {k: {"years": v[0].tolist() if hasattr(v[0], 'tolist') else v[0],
                                       "costs": v[1].tolist() if hasattr(v[1], 'tolist') else v[1]}
                                   for k, v in cost_forecasts.items() if v is not None}
            },
            "capacity_forecasts": {k: {"years": v[0].tolist(), "capacity_gw": v[1].tolist()}
                                   for k, v in capacity_forecasts.items()},
            "battery_metrics": battery_metrics,
            "generation_forecasts": {
                "years": years.tolist(),
                "swb_total": total_swb_generation.tolist(),
                "coal": coal_generation.tolist(),
                "gas": gas_generation.tolist(),
                "non_swb": non_swb_generation.tolist(),
                "total_demand": total_demand_forecast.tolist(),
                "peak_load_gw": peak_load_gw.tolist(),
                "by_technology": {k: v[1].tolist() for k, v in generation_forecasts.items()}
            },
            "displacement_timeline": displacement_timeline,
            "emissions_trajectory": emissions_data,
            "validation": {
                "energy_balance_valid": is_valid,
                "message": message
            }
        }

        print(f"\n{'='*60}")
        print(f"Forecast complete for {region}")
        print(f"{'='*60}\n")

        return result

    def forecast_global(self) -> Dict:
        """
        Forecast all regions and aggregate to Global

        Returns:
            Dictionary with all regional + global results
        """
        print("\n" + "="*60)
        print("GLOBAL FORECAST - All Regions")
        print("="*60)

        regions = self.data_loader.get_all_regions()
        results = {}

        # Forecast each region
        for region in regions:
            results[region] = self.forecast_region(region)

        # Aggregate to Global
        print("\nAggregating to Global...")
        global_result = self._aggregate_global(results)
        results["Global"] = global_result

        return results

    def _aggregate_global(self, regional_results: Dict) -> Dict:
        """
        Aggregate regional forecasts to Global

        Args:
            regional_results: Dictionary of {region: forecast_result}

        Returns:
            Global aggregated result
        """
        # Extract years (should be same across all regions)
        first_region = list(regional_results.values())[0]
        years = np.array(first_region["generation_forecasts"]["years"])

        # Initialize aggregation arrays
        global_swb = np.zeros_like(years, dtype=float)
        global_coal = np.zeros_like(years, dtype=float)
        global_gas = np.zeros_like(years, dtype=float)
        global_non_swb = np.zeros_like(years, dtype=float)
        global_total = np.zeros_like(years, dtype=float)

        # Aggregate
        for region, result in regional_results.items():
            gen = result["generation_forecasts"]
            global_swb += np.array(gen["swb_total"])
            global_coal += np.array(gen["coal"])
            global_gas += np.array(gen["gas"])
            global_non_swb += np.array(gen["non_swb"])
            global_total += np.array(gen["total_demand"])

        # Create global result
        global_result = {
            "region": "Global",
            "end_year": self.end_year,
            "generation_forecasts": {
                "years": years.tolist(),
                "swb_total": global_swb.tolist(),
                "coal": global_coal.tolist(),
                "gas": global_gas.tolist(),
                "non_swb": global_non_swb.tolist(),
                "total_demand": global_total.tolist()
            },
            "note": "Aggregated from China, USA, Europe, Rest_of_World"
        }

        return global_result

    def export_to_csv(self, result: Dict, output_path: str, region: str):
        """Export forecast results to CSV"""
        import csv

        gen = result["generation_forecasts"]
        years = gen["years"]

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                "Year", "SWB_Generation", "Coal_Generation", "Gas_Generation",
                "Non_SWB_Generation", "Total_Demand", "SWB_Share"
            ])
            # Data
            for i, year in enumerate(years):
                swb = gen["swb_total"][i]
                coal = gen["coal"][i]
                gas = gen["gas"][i]
                non_swb = gen["non_swb"][i]
                total = gen["total_demand"][i]
                swb_share = swb / total if total > 0 else 0

                writer.writerow([
                    year, swb, coal, gas, non_swb, total, swb_share
                ])

        print(f"CSV exported to: {output_path}")

    def export_to_json(self, result: Dict, output_path: str):
        """Export forecast results to JSON"""
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"JSON exported to: {output_path}")


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Energy Forecasting for Solar-Wind-Battery (SWB) Systems"
    )
    parser.add_argument(
        "--region",
        required=True,
        choices=["China", "USA", "Europe", "Rest_of_World", "Global"],
        help="Region to forecast"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2035,
        help="Final forecast year (default: 2035)"
    )
    parser.add_argument(
        "--battery-duration",
        type=int,
        choices=[2, 4, 8],
        default=4,
        help="Battery duration in hours (default: 4)"
    )
    parser.add_argument(
        "--scenario",
        choices=["baseline", "accelerated", "delayed"],
        default="baseline",
        help="Forecast scenario (default: baseline)"
    )
    parser.add_argument(
        "--output",
        choices=["csv", "json", "both"],
        default="csv",
        help="Output format (default: csv)"
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = EnergyForecastOrchestrator(
        end_year=args.end_year,
        battery_duration=args.battery_duration,
        scenario=args.scenario
    )

    # Run forecast
    if args.region == "Global":
        results = orchestrator.forecast_global()
        result = results["Global"]
    else:
        result = orchestrator.forecast_region(args.region)

    # Export results
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output"
    )
    os.makedirs(output_dir, exist_ok=True)

    output_base = os.path.join(output_dir, f"{args.region}_{args.end_year}_{args.scenario}")

    if args.output in ["csv", "both"]:
        orchestrator.export_to_csv(result, f"{output_base}.csv", args.region)

    if args.output in ["json", "both"]:
        orchestrator.export_to_json(result, f"{output_base}.json")

    print("\nForecast complete!")


if __name__ == "__main__":
    main()
