#!/usr/bin/env python3
"""
Copper Demand Forecasting - Main Script
Implements hybrid bottom-up + top-down methodology
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from data_loader import CopperDataLoader

class CopperDemandForecast:
    """
    Hybrid copper demand forecasting model
    TIER 1: Bottom-up for Automotive and Grid Generation
    TIER 2: Top-down allocation for Construction, Industrial, Electronics
    """

    def __init__(self, config_path, region='Global', scenario='baseline'):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.start_year = self.config['default_parameters']['start_year']
        self.end_year = self.config['default_parameters']['end_year']
        self.coefficients = self.config['copper_coefficients']
        self.allocation = self.config['segment_allocation']
        self.lifespans = self.config['lifespans']
        self.region = region
        self.scenario_name = scenario

        # Validate region
        if region not in self.config['regions']:
            raise ValueError(f"Invalid region: {region}. Must be one of {self.config['regions']}")

        # Validate scenario
        if scenario not in self.config['scenarios']:
            raise ValueError(f"Invalid scenario: {scenario}. Must be one of {list(self.config['scenarios'].keys())}")

        # Load scenario parameters
        self.scenario = self.config['scenarios'][scenario]

        # Initialize results dataframe
        self.years = list(range(self.start_year, self.end_year + 1))
        self.results = pd.DataFrame({'year': self.years})

        # Initialize data loader
        self.data_loader = CopperDataLoader()
        self.real_data = None

        # Confidence tags for transparency
        self.confidence = {
            'automotive': 'HIGH_BOTTOM_UP',
            'grid_generation': 'MEDIUM_BOTTOM_UP',
            'construction': 'LOW_ALLOCATED',
            'grid_td': 'LOW_RESIDUAL',
            'industrial': 'LOW_ALLOCATED',
            'electronics': 'LOW_ALLOCATED',
            'other_uses': 'LOW_RESIDUAL'
        }

    def load_data(self):
        """Load input datasets from real data sources"""
        try:
            # Load all data
            self.real_data = self.data_loader.load_all_data()

            # Get historical consumption baseline
            consumption_data = self.real_data['consumption']

            # Use historical data for baseline years, project forward
            if self.region in consumption_data:
                hist_series = consumption_data[self.region]

                # Get most recent historical value
                last_hist_year = hist_series.index.max()
                last_hist_value = hist_series.iloc[-1]

                # Create consumption series
                consumption_values = []
                for year in self.years:
                    if year <= last_hist_year and year in hist_series.index:
                        # Use historical data
                        consumption_values.append(hist_series[year])
                    else:
                        # Project forward with growth rate from scenario
                        years_ahead = year - last_hist_year
                        # Assume ~1.5% annual growth for baseline
                        growth_rate = 0.015
                        projected = last_hist_value * ((1 + growth_rate) ** years_ahead)
                        consumption_values.append(projected)

                self.total_consumption = pd.Series(consumption_values, index=self.years)
            else:
                # Fallback if region not found
                print(f"Warning: No consumption data for {self.region}, using estimated values")
                self.total_consumption = pd.Series(
                    np.linspace(25000000, 30000000, len(self.years)),
                    index=self.years
                )

            # Load segment shares from data
            segments = self.real_data['segment_shares']
            self.share_transport = segments.get('transportation', {}).get(self.region, 0.12)
            self.share_electrical = segments.get('electrical', {}).get(self.region, 0.68)
            self.share_ev = segments.get('ev', {}).get(self.region, 0.02)

            print(f"✓ Data loaded for {self.region}, years {self.start_year} to {self.end_year}")
            print(f"✓ Using scenario: {self.scenario_name}")

        except Exception as e:
            print(f"Error loading data: {e}")
            print("Falling back to synthetic data...")
            # Fallback to simple synthetic data
            self.total_consumption = pd.Series(
                np.linspace(25000000, 30000000, len(self.years)),
                index=self.years
            )
            self.share_transport = 0.12
            self.share_electrical = 0.68
            self.share_ev = 0.02

    def calculate_automotive(self, year):
        """
        TIER 1: Bottom-up calculation for automotive segment
        Uses vehicle sales × copper coefficients with scenario-driven EV adoption
        """
        year_idx = year - self.start_year

        try:
            # Get vehicle data from real data
            vehicle_data = self.real_data['vehicles']['passenger_cars']

            # Get sales for region
            if self.region in vehicle_data['sales']:
                sales_data = vehicle_data['sales'][self.region]

                # Use historical data if available
                ice_sales = 0
                bev_sales = 0
                phev_sales = 0

                if 'ICE' in sales_data and year in sales_data['ICE'].index:
                    ice_sales = sales_data['ICE'][year]
                if 'BEV' in sales_data and year in sales_data['BEV'].index:
                    bev_sales = sales_data['BEV'][year]
                if 'PHEV' in sales_data and year in sales_data['PHEV'].index:
                    phev_sales = sales_data['PHEV'][year]

                # If no data for this year, project using scenario
                if ice_sales == 0 and bev_sales == 0:
                    # Get last known year
                    all_ice = sales_data.get('ICE', pd.Series())
                    all_bev = sales_data.get('BEV', pd.Series())

                    if len(all_ice) > 0:
                        last_year = max(all_ice.index.max(), all_bev.index.max())
                        last_ice = all_ice.get(last_year, 0)
                        last_bev = all_bev.get(last_year, 0)
                        last_total = last_ice + last_bev

                        # Project using scenario EV adoption target
                        target_ev_share = self.scenario['ev_adoption_2045']
                        years_to_target = 2045 - last_year
                        years_from_last = year - last_year

                        if years_to_target > 0:
                            # Logistic curve for EV adoption
                            current_ev_share = last_bev / last_total if last_total > 0 else 0.02
                            progress = years_from_last / years_to_target
                            ev_share = current_ev_share + (target_ev_share - current_ev_share) * progress
                        else:
                            ev_share = target_ev_share

                        # Project total sales with modest growth
                        total_sales = last_total * (1.01 ** years_from_last)
                        bev_sales = total_sales * ev_share
                        ice_sales = total_sales * (1 - ev_share)
                    else:
                        # Complete fallback
                        total_sales = 70 + (year_idx * 0.5)
                        ev_share_fallback = 0.02 + (year_idx * 0.03)
                        bev_sales = total_sales * ev_share_fallback
                        ice_sales = total_sales * (1 - ev_share_fallback)

            else:
                # Fallback calculation
                total_sales = 70 + (year_idx * 0.5)
                ev_share_fallback = 0.02 + (year_idx * 0.03)
                bev_sales = total_sales * ev_share_fallback
                ice_sales = total_sales * (1 - ev_share_fallback)
                phev_sales = 0

            # Calculate copper demand (sales in millions, convert to tonnes)
            ice_demand = ice_sales * self.coefficients['automotive']['car_ice'] * 1000000 / 1000
            bev_demand = bev_sales * self.coefficients['automotive']['car_bev'] * 1000000 / 1000
            phev_demand = phev_sales * self.coefficients['automotive']['car_phev'] * 1000000 / 1000 if phev_sales else 0

            auto_total = ice_demand + bev_demand + phev_demand

            return {
                'auto_total': auto_total,
                'auto_oem': auto_total,
                'auto_repl': 0,
                'auto_ice': ice_demand,
                'auto_bev': bev_demand
            }

        except Exception as e:
            print(f"Warning: Error in automotive calculation for {year}: {e}")
            # Fallback calculation
            ev_share = 0.02 + (year_idx * 0.03)
            total_sales = 70 + (year_idx * 0.5)
            ice_demand = total_sales * (1 - ev_share) * self.coefficients['automotive']['car_ice'] * 1000000 / 1000
            bev_demand = total_sales * ev_share * self.coefficients['automotive']['car_bev'] * 1000000 / 1000

            return {
                'auto_total': ice_demand + bev_demand,
                'auto_oem': ice_demand + bev_demand,
                'auto_repl': 0,
                'auto_ice': ice_demand,
                'auto_bev': bev_demand
            }

    def calculate_grid_generation(self, year):
        """
        TIER 1: Bottom-up calculation for grid generation
        Uses new capacity additions × copper coefficients with scenario-driven renewables buildout
        """
        year_idx = year - self.start_year

        try:
            # Get generation capacity data
            capacity_data = self.real_data['generation']

            # Calculate capacity additions (new capacity = delta from previous year)
            new_wind_onshore = 0
            new_wind_offshore = 0
            new_solar = 0
            new_gas = 0
            new_coal = 0

            if self.region in capacity_data.get('wind_onshore', {}):
                wind_series = capacity_data['wind_onshore'][self.region]
                if year in wind_series.index and year - 1 in wind_series.index:
                    new_wind_onshore = max(0, wind_series[year] - wind_series[year-1])
                elif year > wind_series.index.max():
                    # Project using scenario
                    last_year = wind_series.index.max()
                    last_value = wind_series.iloc[-1]
                    # Accelerated growth for renewables in accelerated scenario
                    if 'renewable_capacity_2045_tw' in self.scenario:
                        target_tw = self.scenario['renewable_capacity_2045_tw']
                        growth_factor = target_tw / 15.0  # Baseline is 15 TW
                        new_wind_onshore = 50 * growth_factor + (year_idx * 5 * growth_factor)
                    else:
                        new_wind_onshore = 50 + (year_idx * 5)

            if self.region in capacity_data.get('solar', {}):
                solar_series = capacity_data['solar'][self.region]
                if year in solar_series.index and year - 1 in solar_series.index:
                    new_solar = max(0, solar_series[year] - solar_series[year-1])
                elif year > solar_series.index.max():
                    # Project using scenario
                    if 'renewable_capacity_2045_tw' in self.scenario:
                        target_tw = self.scenario['renewable_capacity_2045_tw']
                        growth_factor = target_tw / 15.0
                        new_solar = 100 * growth_factor + (year_idx * 10 * growth_factor)
                    else:
                        new_solar = 100 + (year_idx * 10)

            # Fossil fuels declining
            new_gas = max(0, 20 - (year_idx * 0.5))
            new_coal = max(0, 10 - (year_idx * 0.3))

            # If no real data, use scenario-based projections
            if new_wind_onshore == 0 and new_solar == 0:
                if 'renewable_capacity_2045_tw' in self.scenario:
                    target_tw = self.scenario['renewable_capacity_2045_tw']
                    growth_factor = target_tw / 15.0
                    new_wind_onshore = 50 * growth_factor + (year_idx * 5 * growth_factor)
                    new_solar = 100 * growth_factor + (year_idx * 10 * growth_factor)
                else:
                    new_wind_onshore = 50 + (year_idx * 5)
                    new_solar = 100 + (year_idx * 10)

        except Exception as e:
            print(f"Warning: Error in generation calculation for {year}: {e}")
            # Fallback
            new_wind_onshore = 50 + (year_idx * 5)
            new_wind_offshore = 0
            new_solar = 100 + (year_idx * 10)
            new_gas = max(0, 20 - (year_idx * 0.5))
            new_coal = max(0, 10 - (year_idx * 0.3))

        # Calculate copper demand (GW to MW, then × coefficients)
        wind_copper = (new_wind_onshore * 1000 * self.coefficients['grid_generation']['per_mw_wind_onshore'] +
                      new_wind_offshore * 1000 * self.coefficients['grid_generation']['per_mw_wind_offshore'])
        solar_copper = new_solar * 1000 * self.coefficients['grid_generation']['per_mw_solar_pv']
        gas_copper = new_gas * 1000 * self.coefficients['grid_generation']['per_mw_gas_ccgt']
        coal_copper = new_coal * 1000 * self.coefficients['grid_generation']['per_mw_coal']

        grid_gen_total = wind_copper + solar_copper + gas_copper + coal_copper

        return {
            'grid_generation_oem': grid_gen_total,
            'grid_gen_wind': wind_copper,
            'grid_gen_solar': solar_copper,
            'grid_gen_fossil': gas_copper + coal_copper
        }

    def allocate_tier2_segments(self, year, total_consumption, auto_total, grid_gen_total):
        """
        TIER 2: Top-down allocation for Construction, Industrial, Electronics
        Uses segment shares when driver data unavailable
        """
        # Calculate electrical segment total
        electrical_total = total_consumption * self.share_electrical

        # Allocate within electrical segment
        construction_total = electrical_total * self.allocation['electrical_segments']['construction_pct']
        grid_total_allocated = electrical_total * self.allocation['electrical_segments']['grid_pct']
        industrial_total = electrical_total * self.allocation['electrical_segments']['industrial_pct']

        # Grid T&D is residual after generation
        grid_td_total = max(0, grid_total_allocated - grid_gen_total)

        # Electronics as fixed share
        electronics_total = total_consumption * self.allocation['direct_shares']['electronics_pct']

        # Apply OEM/Replacement splits
        construction_oem = construction_total * self.config['oem_replacement_splits']['construction_oem_pct']
        construction_repl = construction_total - construction_oem

        grid_td_oem = grid_td_total * self.config['oem_replacement_splits']['grid_td_oem_pct']
        grid_td_repl = grid_td_total - grid_td_oem

        industrial_oem = industrial_total * self.config['oem_replacement_splits']['industrial_oem_pct']
        industrial_repl = industrial_total - industrial_oem

        # Other uses as bounded residual
        other_uses_raw = total_consumption - (auto_total + construction_total +
                                              grid_gen_total + grid_td_total +
                                              industrial_total + electronics_total)

        # Apply bounds
        other_uses_min = total_consumption * self.allocation['other_uses_bounds']['min_pct']
        other_uses_max = total_consumption * self.allocation['other_uses_bounds']['max_pct']
        other_uses = np.clip(other_uses_raw, other_uses_min, other_uses_max)

        return {
            'construction_total': construction_total,
            'construction_oem': construction_oem,
            'construction_repl': construction_repl,
            'grid_td_total': grid_td_total,
            'grid_td_oem': grid_td_oem,
            'grid_td_repl': grid_td_repl,
            'industrial_total': industrial_total,
            'industrial_oem': industrial_oem,
            'industrial_repl': industrial_repl,
            'electronics_total': electronics_total,
            'electronics_oem': electronics_total,  # All OEM for electronics
            'electronics_repl': 0,
            'other_uses': other_uses
        }

    def reconcile_and_validate(self, year_results, total_consumption):
        """
        Force reconciliation to match total consumption
        Apply scenario demand multipliers
        Validate against segment shares
        """
        # Apply scenario demand multiplier if specified
        if 'demand_multiplier' in self.scenario:
            multiplier = self.scenario['demand_multiplier']
            total_consumption *= multiplier

        # Apply substitution scenario coefficient reductions if specified
        if 'coefficient_reduction' in self.scenario:
            reduction = self.scenario['coefficient_reduction']
            # Reduce construction and grid T&D (vulnerable to substitution)
            year_results['construction_total'] *= (1 - reduction)
            year_results['construction_oem'] *= (1 - reduction)
            year_results['construction_repl'] *= (1 - reduction)
            year_results['grid_td_total'] *= (1 - reduction)
            year_results['grid_td_oem'] *= (1 - reduction)
            year_results['grid_td_repl'] *= (1 - reduction)

        # Calculate total from segments
        total_calculated = (
            year_results['auto_total'] +
            year_results['construction_total'] +
            year_results['grid_generation_oem'] +
            year_results['grid_td_total'] +
            year_results['industrial_total'] +
            year_results['electronics_total'] +
            year_results['other_uses']
        )

        # Force reconciliation if needed
        if abs(total_calculated - total_consumption) > total_consumption * 0.001:
            # Adjust TIER 2 segments proportionally
            tier2_total = (year_results['construction_total'] +
                          year_results['grid_td_total'] +
                          year_results['industrial_total'] +
                          year_results['electronics_total'] +
                          year_results['other_uses'])

            tier1_total = year_results['auto_total'] + year_results['grid_generation_oem']

            if tier2_total > 0:
                adjustment_factor = (total_consumption - tier1_total) / tier2_total

                # Apply adjustment
                for key in ['construction_total', 'construction_oem', 'construction_repl',
                           'grid_td_total', 'grid_td_oem', 'grid_td_repl',
                           'industrial_total', 'industrial_oem', 'industrial_repl',
                           'electronics_total', 'electronics_oem',
                           'other_uses']:
                    if key in year_results:
                        year_results[key] *= adjustment_factor

        # Calculate validation metrics
        year_results['total_demand'] = total_consumption
        year_results['share_transport_calc'] = year_results['auto_total'] / total_consumption if total_consumption > 0 else 0
        year_results['share_ev_calc'] = year_results.get('auto_bev', 0) / total_consumption if total_consumption > 0 else 0

        return year_results

    def run_forecast(self):
        """Run the complete forecast"""
        self.load_data()

        all_results = []

        for year in self.years:
            print(f"Processing year {year}...")

            # Get total consumption for this year
            total_consumption = self.total_consumption[year]

            # TIER 1: Bottom-up calculations
            auto_results = self.calculate_automotive(year)
            grid_gen_results = self.calculate_grid_generation(year)

            # TIER 2: Top-down allocation
            tier2_results = self.allocate_tier2_segments(
                year,
                total_consumption,
                auto_results['auto_total'],
                grid_gen_results['grid_generation_oem']
            )

            # Combine results
            year_results = {
                'year': year,
                **auto_results,
                **grid_gen_results,
                **tier2_results
            }

            # Reconcile and validate
            year_results = self.reconcile_and_validate(year_results, total_consumption)

            # Add confidence tags
            for segment, confidence in self.confidence.items():
                year_results[f'{segment}_confidence'] = confidence

            all_results.append(year_results)

        # Create results dataframe
        self.results = pd.DataFrame(all_results)

        # Add aggregate columns
        self.results['total_oem'] = (
            self.results['auto_oem'] +
            self.results['grid_generation_oem'] +
            self.results['grid_td_oem'] +
            self.results['construction_oem'] +
            self.results['industrial_oem'] +
            self.results['electronics_oem']
        )

        self.results['total_replacement'] = (
            self.results['grid_td_repl'] +
            self.results['construction_repl'] +
            self.results['industrial_repl']
        )

        print(f"Forecast complete for {len(self.years)} years")

        return self.results

    def save_results(self, output_path, format='csv'):
        """Save results to file"""
        if format == 'csv':
            self.results.to_csv(output_path, index=False)
            print(f"Results saved to {output_path}")
        elif format == 'json':
            self.results.to_json(output_path, orient='records', indent=2)
            print(f"Results saved to {output_path}")

    def generate_summary(self):
        """Generate summary statistics"""
        summary = {
            'region': self.region,
            'scenario': self.scenario_name,
            'total_demand_2045': self.results[self.results['year'] == self.end_year]['total_demand'].values[0],
            'auto_share_2045': self.results[self.results['year'] == self.end_year]['share_transport_calc'].values[0],
            'ev_share_2045': self.results[self.results['year'] == self.end_year]['share_ev_calc'].values[0],
            'cagr': (self.results['total_demand'].iloc[-1] / self.results['total_demand'].iloc[0]) ** (1/len(self.years)) - 1
        }
        return summary


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Copper Demand Forecast')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--region', default='Global', help='Region: China, USA, Europe, Rest_of_World, Global')
    parser.add_argument('--end-year', type=int, default=2045, help='End year for forecast')
    parser.add_argument('--scenario', default='baseline', help='Scenario: baseline, accelerated, delayed, substitution')
    parser.add_argument('--output-format', default='csv', choices=['csv', 'json'], help='Output format')
    parser.add_argument('--validate', type=bool, default=False, help='Run validation')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    # Run forecast with region and scenario
    try:
        model = CopperDemandForecast(args.config, region=args.region, scenario=args.scenario)
        model.end_year = args.end_year

        results = model.run_forecast()

        # Save results with region and scenario in filename
        output_file = output_dir / f'copper_demand_{args.region}_{args.scenario}_{args.end_year}.{args.output_format}'
        model.save_results(output_file, format=args.output_format)

        # Generate summary
        summary = model.generate_summary()
        print("\n=== FORECAST SUMMARY ===")
        print(f"Region: {summary['region']}")
        print(f"Scenario: {summary['scenario']}")
        print(f"Total Demand {args.end_year}: {summary['total_demand_2045']:,.0f} tonnes")
        print(f"Automotive Share {args.end_year}: {summary['auto_share_2045']:.1%}")
        print(f"EV Demand Share {args.end_year}: {summary['ev_share_2045']:.1%}")
        print(f"CAGR: {summary['cagr']:.2%}")

        return 0

    except Exception as e:
        print(f"Error running forecast: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())