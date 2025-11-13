#!/usr/bin/env python3
"""
Solar-Wind-Battery (SWB) Energy Transition Forecasting
Models the transition from fossil fuels to renewable energy systems
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from data_loader import SWBDataLoader


class SWBTransitionForecast:
    """
    Solar-Wind-Battery energy transition forecasting model
    Analyzes cost competitiveness and displacement of coal/gas generation
    """

    def __init__(self, config_path, region='Global', scenario='baseline'):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.start_year = self.config['default_parameters']['start_year']
        self.end_year = self.config['default_parameters']['end_year']
        self.region = region
        self.scenario_name = scenario

        # Validate inputs
        if region not in self.config['regions']:
            raise ValueError(f"Invalid region: {region}")
        if scenario not in self.config['scenarios']:
            raise ValueError(f"Invalid scenario: {scenario}")

        # Load parameters
        self.scenario = self.config['scenarios'][scenario]
        self.capacity_factors = self.config['capacity_factors']
        self.battery_sizing = self.config['battery_sizing']
        self.cost_forecasting = self.config['cost_forecasting']
        self.emission_factors = self.config['emission_factors']

        # Initialize results
        self.years = list(range(self.start_year, self.end_year + 1))
        self.results = pd.DataFrame({'year': self.years})

        # Initialize data loader
        self.data_loader = SWBDataLoader()
        self.data = None

    def load_data(self):
        """Load all required data"""
        try:
            self.data = self.data_loader.load_all_data()
            print(f"✓ Data loaded for {self.region}, years {self.start_year} to {self.end_year}")
            print(f"✓ Using scenario: {self.scenario_name}")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def forecast_lcoe(self, historical_lcoe, technology):
        """
        Forecast LCOE using log-CAGR method

        Args:
            historical_lcoe: Series of historical LCOE values
            technology: Technology name for scenario parameters

        Returns:
            Series with forecasted LCOE for all years
        """
        forecasted = pd.Series(index=self.years, dtype=float)

        # Get scenario decline rate
        decline_key = f"{technology}_cost_decline_rate"
        decline_rate = self.scenario.get(decline_key, 0.05)

        # Fill historical values
        for year in self.years:
            if year in historical_lcoe.index:
                forecasted[year] = historical_lcoe[year]

        # Forward fill from last known value
        last_known_year = historical_lcoe.index.max()
        if last_known_year < self.end_year:
            last_known_value = historical_lcoe[last_known_year]

            for year in range(last_known_year + 1, self.end_year + 1):
                years_ahead = year - last_known_year
                # Exponential decline with floor
                forecasted[year] = last_known_value * ((1 - decline_rate) ** years_ahead)

                # Apply cost floor (20% of original value)
                floor = last_known_value * self.cost_forecasting['floor_cost_ratio']
                forecasted[year] = max(forecasted[year], floor)

        return forecasted

    def forecast_all_lcoe(self):
        """Forecast LCOE for all technologies"""
        lcoe_data = self.data['lcoe']

        forecasts = {}

        # Renewable technologies
        for tech in ['solar', 'onshore_wind', 'offshore_wind']:
            if self.region in lcoe_data[tech]:
                forecasts[tech] = self.forecast_lcoe(
                    lcoe_data[tech][self.region],
                    tech
                )
            else:
                # Use Global as proxy
                if 'Global' in lcoe_data[tech]:
                    forecasts[tech] = self.forecast_lcoe(
                        lcoe_data[tech]['Global'],
                        tech
                    )
                else:
                    forecasts[tech] = pd.Series(0, index=self.years)

        # Fossil fuel technologies
        for tech in ['coal', 'gas']:
            if self.region in lcoe_data[tech]:
                hist_data = lcoe_data[tech][self.region]

                # Fossil fuels may increase slightly
                change_key = f"{tech}_cost_change"
                change_rate = self.scenario.get(change_key, 0.01)

                forecasted = pd.Series(index=self.years, dtype=float)

                for year in self.years:
                    if year in hist_data.index:
                        forecasted[year] = hist_data[year]
                    else:
                        last_year = hist_data.index.max()
                        last_value = hist_data[last_year]
                        years_ahead = year - last_year
                        forecasted[year] = last_value * ((1 + change_rate) ** years_ahead)

                forecasts[tech] = forecasted
            else:
                if 'Global' in lcoe_data[tech]:
                    forecasts[tech] = self.forecast_lcoe(lcoe_data[tech]['Global'], tech)
                else:
                    forecasts[tech] = pd.Series(100, index=self.years)  # Default value

        return forecasts

    def calculate_battery_scoe(self):
        """
        Calculate Storage Cost of Energy (SCOE) for batteries
        Based on BESS turnkey costs
        """
        bess_costs = self.data['bess_costs']

        if self.region in bess_costs:
            bess_series = bess_costs[self.region]
        elif 'Global' in bess_costs:
            bess_series = bess_costs['Global']
        else:
            return pd.Series(50, index=self.years)  # Default value

        # Forecast BESS costs
        decline_rate = self.scenario.get('battery_cost_decline_rate', 0.10)

        scoe = pd.Series(index=self.years, dtype=float)

        last_known_year = bess_series.index.max()
        last_known_cost = bess_series[last_known_year]

        for year in self.years:
            if year in bess_series.index:
                capex = bess_series[year]
            else:
                years_ahead = year - last_known_year
                capex = last_known_cost * ((1 - decline_rate) ** years_ahead)

                # Floor at 20% of original
                floor = last_known_cost * 0.20
                capex = max(capex, floor)

            # Convert to $/MWh
            # Assumptions: 10-year life, 250 cycles/year, 88% round-trip efficiency
            cycles_per_year = self.battery_sizing['cycles_per_year']
            lifetime_years = 10
            efficiency = self.battery_sizing['round_trip_efficiency']

            # SCOE = capex / (cycles_per_year × lifetime_years × efficiency)
            scoe[year] = capex / (cycles_per_year * lifetime_years * efficiency)

        return scoe

    def calculate_swb_stack_cost(self, solar_lcoe, wind_lcoe, battery_scoe):
        """
        Calculate combined SWB stack cost
        Weighted average based on typical generation mix
        """
        # Typical mix: 60% solar, 30% onshore wind, 10% offshore wind
        # Plus battery storage cost

        generation_cost = (
            0.50 * solar_lcoe +
            0.35 * wind_lcoe +
            0.15 * wind_lcoe * 1.2  # Offshore premium
        )

        # Battery adds to total cost
        # Assume need 0.5 days of storage for 100% renewable
        resilience_factor = self.battery_sizing['resilience_days']
        battery_contribution = battery_scoe * resilience_factor * 0.3  # 30% of days need storage

        swb_total_cost = generation_cost + battery_contribution

        return swb_total_cost

    def detect_tipping_points(self, swb_cost, coal_lcoe, gas_lcoe):
        """
        Detect when SWB becomes cheaper than coal and gas
        """
        tipping_vs_coal = None
        tipping_vs_gas = None

        persistence = self.config['tipping_point_detection']['persistence_years']

        # Find first year where SWB is cheaper for N consecutive years
        for i, year in enumerate(self.years):
            if tipping_vs_coal is None:
                if swb_cost[year] < coal_lcoe[year]:
                    # Check persistence
                    if all(swb_cost[self.years[i + j]] < coal_lcoe[self.years[i + j]]
                           for j in range(min(persistence, len(self.years) - i))):
                        tipping_vs_coal = year

            if tipping_vs_gas is None:
                if swb_cost[year] < gas_lcoe[year]:
                    if all(swb_cost[self.years[i + j]] < gas_lcoe[self.years[i + j]]
                           for j in range(min(persistence, len(self.years) - i))):
                        tipping_vs_gas = year

        return tipping_vs_coal, tipping_vs_gas

    def calculate_generation_displacement(self, swb_cost, coal_lcoe, gas_lcoe,
                                         tipping_vs_coal, tipping_vs_gas):
        """
        Calculate how SWB displaces fossil fuel generation over time
        """
        # Get historical generation data
        generation_data = self.data['generation']
        electricity_demand = self.data['electricity_demand']

        # Initialize with historical data - handle missing data gracefully
        solar_gen = generation_data['solar'].get(self.region,
                    generation_data['solar'].get('Global', pd.Series()))
        wind_gen = generation_data['wind'].get(self.region,
                   generation_data['wind'].get('Global', pd.Series()))
        coal_gen = generation_data['coal'].get(self.region,
                   generation_data['coal'].get('Global', pd.Series()))
        gas_gen = generation_data['gas'].get(self.region,
                  generation_data['gas'].get('Global', pd.Series()))

        # Get total demand
        if self.region in electricity_demand:
            total_demand = electricity_demand[self.region]
        else:
            total_demand = electricity_demand.get('Global', pd.Series())

        # Build generation forecast
        results = {
            'solar': pd.Series(index=self.years, dtype=float),
            'wind': pd.Series(index=self.years, dtype=float),
            'coal': pd.Series(index=self.years, dtype=float),
            'gas': pd.Series(index=self.years, dtype=float),
            'total_demand': pd.Series(index=self.years, dtype=float)
        }

        # Displacement sequencing
        displacement_order = self.config['displacement_sequencing'].get(self.region, 'coal_first')
        displacement_speed = self.scenario.get('displacement_speed', 1.0)

        for year in self.years:
            # Get or project demand
            if year in total_demand.index:
                demand = total_demand[year]
            else:
                # Project demand growth (2% annually)
                last_year = total_demand.index.max()
                last_demand = total_demand[last_year]
                years_ahead = year - last_year
                demand = last_demand * (1.02 ** years_ahead)

            results['total_demand'][year] = demand

            # Before tipping point: use historical or slow growth
            if (tipping_vs_coal is None or year < tipping_vs_coal) and \
               (tipping_vs_gas is None or year < tipping_vs_gas):
                # Pre-tipping: renewables grow slowly
                if year in solar_gen.index:
                    results['solar'][year] = solar_gen[year]
                else:
                    last_year = solar_gen.index.max() if not solar_gen.empty else self.start_year
                    last_value = solar_gen[last_year] if not solar_gen.empty else 100
                    years_ahead = year - last_year
                    results['solar'][year] = last_value * (1.15 ** years_ahead)  # 15% growth

                if year in wind_gen.index:
                    results['wind'][year] = wind_gen[year]
                else:
                    last_year = wind_gen.index.max() if not wind_gen.empty else self.start_year
                    last_value = wind_gen[last_year] if not wind_gen.empty else 50
                    years_ahead = year - last_year
                    results['wind'][year] = last_value * (1.12 ** years_ahead)  # 12% growth

                # Fossil fills the rest
                swb_total = results['solar'][year] + results['wind'][year]
                fossil_needed = demand - swb_total

                if displacement_order == 'coal_first':
                    coal_share = 0.55
                    gas_share = 0.45
                else:
                    coal_share = 0.45
                    gas_share = 0.55

                results['coal'][year] = fossil_needed * coal_share
                results['gas'][year] = fossil_needed * gas_share

            else:
                # Post-tipping: rapid renewable growth
                years_since_tipping = year - min(t for t in [tipping_vs_coal, tipping_vs_gas] if t is not None)

                # S-curve adoption
                # SWB share = 1 / (1 + exp(-k * (t - t0)))
                k = 0.3 * displacement_speed  # Steepness
                t0 = 10  # Midpoint at 10 years
                swb_share = 1 / (1 + np.exp(-k * (years_since_tipping - t0)))

                # Reserve floors for reliability
                coal_floor = self.config['reserve_floors']['coal_minimum_share']
                gas_floor = self.config['reserve_floors']['gas_minimum_share']

                # Maximum SWB can reach
                max_swb_share = 1 - coal_floor - gas_floor
                swb_share = min(swb_share, max_swb_share)

                swb_generation = demand * swb_share

                # Split SWB between solar and wind (60/40)
                results['solar'][year] = swb_generation * 0.60
                results['wind'][year] = swb_generation * 0.40

                # Remaining for fossils
                fossil_needed = demand * (1 - swb_share)

                if displacement_order == 'coal_first':
                    # Displace coal first, then gas
                    coal_max_share = coal_floor
                    gas_gets_rest = True
                    results['coal'][year] = demand * coal_max_share
                    results['gas'][year] = fossil_needed - results['coal'][year]
                else:
                    # Displace gas first, then coal
                    gas_max_share = gas_floor
                    coal_gets_rest = True
                    results['gas'][year] = demand * gas_max_share
                    results['coal'][year] = fossil_needed - results['gas'][year]

        return results

    def calculate_emissions(self, generation):
        """Calculate CO2 emissions from generation mix"""
        emissions = {
            'coal': generation['coal'] * self.emission_factors['coal_kg_co2_per_mwh'] / 1e6,  # Mt
            'gas': generation['gas'] * self.emission_factors['gas_kg_co2_per_mwh'] / 1e6,
            'swb': (generation['solar'] + generation['wind']) *
                   ((self.emission_factors['solar_kg_co2_per_mwh'] +
                     self.emission_factors['wind_kg_co2_per_mwh']) / 2) / 1e6
        }

        emissions['total'] = emissions['coal'] + emissions['gas'] + emissions['swb']

        return emissions

    def forecast_transition(self):
        """Run complete SWB transition forecast"""
        print("\nForecasting LCOE for all technologies...")
        lcoe_forecasts = self.forecast_all_lcoe()

        print("Calculating battery storage costs...")
        battery_scoe = self.calculate_battery_scoe()

        print("Calculating SWB stack cost...")
        swb_stack_cost = self.calculate_swb_stack_cost(
            lcoe_forecasts['solar'],
            lcoe_forecasts['onshore_wind'],
            battery_scoe
        )

        print("Detecting tipping points...")
        tipping_vs_coal, tipping_vs_gas = self.detect_tipping_points(
            swb_stack_cost,
            lcoe_forecasts['coal'],
            lcoe_forecasts['gas']
        )

        print(f"  Tipping vs Coal: {tipping_vs_coal if tipping_vs_coal else 'Not reached'}")
        print(f"  Tipping vs Gas: {tipping_vs_gas if tipping_vs_gas else 'Not reached'}")

        print("Calculating generation displacement...")
        generation = self.calculate_generation_displacement(
            swb_stack_cost,
            lcoe_forecasts['coal'],
            lcoe_forecasts['gas'],
            tipping_vs_coal,
            tipping_vs_gas
        )

        print("Calculating emissions...")
        emissions = self.calculate_emissions(generation)

        # Store results
        self.results['region'] = self.region
        self.results['scenario'] = self.scenario_name

        # Generation (TWh)
        self.results['solar_generation_twh'] = generation['solar'].values
        self.results['wind_generation_twh'] = generation['wind'].values
        self.results['coal_generation_twh'] = generation['coal'].values
        self.results['gas_generation_twh'] = generation['gas'].values
        self.results['total_generation_twh'] = generation['total_demand'].values

        swb_gen = generation['solar'] + generation['wind']
        self.results['swb_generation_twh'] = swb_gen.values
        self.results['swb_share_pct'] = (swb_gen / generation['total_demand'] * 100).values

        # Costs ($/MWh)
        self.results['solar_lcoe_per_mwh'] = lcoe_forecasts['solar'].values
        self.results['wind_lcoe_per_mwh'] = lcoe_forecasts['onshore_wind'].values
        self.results['battery_scoe_per_mwh'] = battery_scoe.values
        self.results['swb_stack_cost_per_mwh'] = swb_stack_cost.values
        self.results['coal_lcoe_per_mwh'] = lcoe_forecasts['coal'].values
        self.results['gas_lcoe_per_mwh'] = lcoe_forecasts['gas'].values

        # Cost advantages
        self.results['swb_coal_cost_advantage'] = (lcoe_forecasts['coal'] - swb_stack_cost).values
        self.results['swb_gas_cost_advantage'] = (lcoe_forecasts['gas'] - swb_stack_cost).values

        # Tipping points
        self.results['tipping_vs_coal_year'] = tipping_vs_coal if tipping_vs_coal else np.nan
        self.results['tipping_vs_gas_year'] = tipping_vs_gas if tipping_vs_gas else np.nan

        # Emissions (Mt CO2)
        self.results['coal_co2_emissions_mt'] = emissions['coal'].values
        self.results['gas_co2_emissions_mt'] = emissions['gas'].values
        self.results['swb_co2_emissions_mt'] = emissions['swb'].values
        self.results['total_co2_emissions_mt'] = emissions['total'].values

    def print_summary(self):
        """Print forecast summary"""
        print(f"\n{'='*70}")
        print(f"SWB Transition Forecast - {self.region}")
        print(f"Scenario: {self.scenario_name}")
        print(f"Years: {self.start_year} - {self.end_year}")
        print(f"{'='*70}\n")

        # Tipping points
        tipping_coal = self.results['tipping_vs_coal_year'].iloc[0]
        tipping_gas = self.results['tipping_vs_gas_year'].iloc[0]

        print("Tipping Points (SWB becomes cheaper):")
        print(f"  vs Coal: {int(tipping_coal) if not np.isnan(tipping_coal) else 'Not reached'}")
        print(f"  vs Gas: {int(tipping_gas) if not np.isnan(tipping_gas) else 'Not reached'}\n")

        # Generation mix
        start_data = self.results.iloc[0]
        end_data = self.results.iloc[-1]

        print(f"Generation Mix:")
        print(f"\n  {self.start_year}:")
        print(f"    Total: {start_data['total_generation_twh']:.0f} TWh")
        print(f"    SWB: {start_data['swb_generation_twh']:.0f} TWh ({start_data['swb_share_pct']:.1f}%)")
        print(f"    Coal: {start_data['coal_generation_twh']:.0f} TWh")
        print(f"    Gas: {start_data['gas_generation_twh']:.0f} TWh")

        print(f"\n  {self.end_year}:")
        print(f"    Total: {end_data['total_generation_twh']:.0f} TWh")
        print(f"    SWB: {end_data['swb_generation_twh']:.0f} TWh ({end_data['swb_share_pct']:.1f}%)")
        print(f"    Coal: {end_data['coal_generation_twh']:.0f} TWh")
        print(f"    Gas: {end_data['gas_generation_twh']:.0f} TWh")

        # Costs
        print(f"\n  Cost Trajectories ($/MWh):")
        print(f"    {self.end_year} SWB Stack: ${end_data['swb_stack_cost_per_mwh']:.0f}")
        print(f"    {self.end_year} Coal: ${end_data['coal_lcoe_per_mwh']:.0f}")
        print(f"    {self.end_year} Gas: ${end_data['gas_lcoe_per_mwh']:.0f}")
        print(f"    SWB advantage vs Coal: ${end_data['swb_coal_cost_advantage']:.0f}")
        print(f"    SWB advantage vs Gas: ${end_data['swb_gas_cost_advantage']:.0f}")

        # Emissions
        emissions_reduction = start_data['total_co2_emissions_mt'] - end_data['total_co2_emissions_mt']
        emissions_reduction_pct = (emissions_reduction / start_data['total_co2_emissions_mt']) * 100

        print(f"\n  Emissions:")
        print(f"    {self.start_year}: {start_data['total_co2_emissions_mt']:.0f} Mt CO2")
        print(f"    {self.end_year}: {end_data['total_co2_emissions_mt']:.0f} Mt CO2")
        print(f"    Reduction: {emissions_reduction:.0f} Mt ({emissions_reduction_pct:.1f}%)")

    def save_results(self, output_path):
        """Save forecast results to CSV"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        self.results.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='SWB Energy Transition Forecasting')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to forecast')
    parser.add_argument('--scenario', type=str, default='baseline',
                       help='Scenario to use (baseline/accelerated/delayed)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output CSV file path')

    args = parser.parse_args()

    # Get config path
    skill_dir = Path(__file__).parent.parent
    config_path = skill_dir / 'config.json'

    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)

    # Initialize and run forecast
    print(f"Initializing SWB transition forecast for {args.region}...")
    forecast = SWBTransitionForecast(config_path, region=args.region, scenario=args.scenario)

    print("Loading data...")
    forecast.load_data()

    print("Running transition forecast...")
    forecast.forecast_transition()

    # Print summary
    forecast.print_summary()

    # Save results
    if args.output:
        output_path = args.output
    else:
        output_dir = skill_dir / 'output'
        output_path = output_dir / f'swb_transition_forecast_{args.region}_{args.scenario}.csv'

    forecast.save_results(output_path)

    print("\n✓ Forecast complete!")


if __name__ == "__main__":
    main()
