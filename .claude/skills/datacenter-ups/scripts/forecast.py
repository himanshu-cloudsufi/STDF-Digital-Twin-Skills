#!/usr/bin/env python3
"""
Datacenter UPS Battery Technology Transition Forecasting
Models VRLA → Li-ion transition based on TCO economics and S-curve adoption
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from scipy.optimize import curve_fit
from data_loader import DatacenterUPSDataLoader


class DatacenterUPSForecast:
    """
    Datacenter UPS battery technology transition model
    Models VRLA (lead-acid) to Li-ion transition based on Total Cost of Ownership
    """

    def __init__(self, config_path, region='Global', scenario='baseline'):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.start_year = self.config['default_parameters']['start_year']
        self.end_year = self.config['default_parameters']['end_year']
        self.tco_horizon = self.config['default_parameters']['tco_horizon_years']
        self.discount_rate = self.config['default_parameters']['discount_rate']

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

        # Cost parameters
        self.vrla_params = self.config['cost_parameters']['vrla']
        self.lithium_params = self.config['cost_parameters']['lithium']

        # Lifespans
        self.vrla_lifespan = self.config['lifespans']['vrla_years']
        self.lithium_lifespan = self.config['lifespans']['lithium_years']

        # S-curve parameters
        self.s_curve_params = self.config['s_curve_parameters']

        # Initialize results dataframe
        self.years = list(range(self.start_year, self.end_year + 1))
        self.results = pd.DataFrame({'year': self.years})

        # Initialize data loader
        self.data_loader = DatacenterUPSDataLoader()
        self.real_data = None

        # Tipping point tracking
        self.tipping_year = None

    def load_data(self):
        """Load input datasets from data sources"""
        try:
            self.real_data = self.data_loader.load_all_data()

            # Get historical data for the region
            if self.region in self.real_data['total_demand']:
                self.hist_total_demand = self.real_data['total_demand'][self.region]
                self.hist_vrla_demand = self.real_data['vrla_demand'].get(self.region, pd.Series())
                self.hist_lithium_demand = self.real_data['li_ion_demand'].get(self.region, pd.Series())
                self.hist_growth_rates = self.real_data['growth_rates'].get(self.region, pd.Series())

                # Get Li-ion costs (4-hour configuration)
                self.bess_costs = self.real_data['li_ion_costs_4h'].get(self.region, pd.Series())

                print(f"✓ Data loaded for {self.region}, years {self.start_year} to {self.end_year}")
                print(f"✓ Using scenario: {self.scenario_name}")
            else:
                raise ValueError(f"No data available for region: {self.region}")

        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def forecast_costs(self):
        """
        Forecast VRLA and Li-ion battery costs using configured methods
        Returns DataFrames with cost projections
        """
        cost_forecast = self.config['cost_forecasting']

        # VRLA costs (flat trajectory)
        vrla_capex = self.vrla_params['capex_per_kwh']
        regional_multiplier = self.vrla_params['regional_multipliers'].get(self.region, 1.0)
        vrla_capex_regional = vrla_capex * regional_multiplier

        # Apply scenario cost change if applicable
        vrla_cost_change = self.scenario.get('vrla_cost_change', 0.0)

        vrla_costs = []
        for i, year in enumerate(self.years):
            # VRLA costs are relatively flat or slightly changing
            annual_change = 1 + vrla_cost_change
            cost = vrla_capex_regional * (annual_change ** i)
            vrla_costs.append(cost)

        # Li-ion costs (declining trajectory from BESS proxy)
        lithium_costs = []

        # Get historical BESS costs
        if not self.bess_costs.empty:
            # Use log-CAGR method for projection
            hist_years = self.bess_costs.index.values
            hist_costs = self.bess_costs.values

            # Calculate historical CAGR in log space
            if len(hist_years) >= 2:
                log_costs = np.log(hist_costs)
                # Linear fit in log space
                coeffs = np.polyfit(hist_years, log_costs, 1)
                slope = coeffs[0]  # This is the log-CAGR

                # Apply scenario cost decline rate
                scenario_decline = -self.scenario.get('lithium_cost_decline_rate', 0.08)
                adjusted_slope = min(slope, scenario_decline)  # Ensure costs decline

                # Cap annual decline
                max_decline = -cost_forecast['cap_annual_decline']
                adjusted_slope = max(adjusted_slope, max_decline)

                # Project forward
                last_year = hist_years[-1]
                last_cost = hist_costs[-1]

                for year in self.years:
                    if year <= last_year and year in self.bess_costs.index:
                        # Use historical data
                        lithium_costs.append(self.bess_costs[year])
                    else:
                        # Project using log-linear trend
                        years_ahead = year - last_year
                        projected_log_cost = np.log(last_cost) + (adjusted_slope * years_ahead)
                        projected_cost = np.exp(projected_log_cost)

                        # Apply floor
                        floor = last_cost * cost_forecast['floor_cost_ratio']
                        projected_cost = max(projected_cost, floor)

                        # Cap at historical maximum to prevent cost increases
                        projected_cost = min(projected_cost, last_cost)

                        lithium_costs.append(projected_cost)
            else:
                # Fallback: use constant decline rate
                base_cost = hist_costs[0] if len(hist_costs) > 0 else 200.0
                decline_rate = self.scenario.get('lithium_cost_decline_rate', 0.08)
                for i in range(len(self.years)):
                    cost = base_cost * ((1 - decline_rate) ** i)
                    floor = base_cost * cost_forecast['floor_cost_ratio']
                    lithium_costs.append(max(cost, floor))
        else:
            # No historical data - use scenario decline from base
            base_cost = 200.0  # Default starting cost
            decline_rate = self.scenario.get('lithium_cost_decline_rate', 0.08)
            for i in range(len(self.years)):
                cost = base_cost * ((1 - decline_rate) ** i)
                lithium_costs.append(cost)

        # Apply UPS reliability premium to Li-ion
        premium = self.lithium_params['ups_reliability_premium']
        lithium_costs = [c * premium for c in lithium_costs]

        return pd.Series(vrla_costs, index=self.years), pd.Series(lithium_costs, index=self.years)

    def calculate_tco(self, capex_per_kwh, opex_per_kwh_year, lifespan_years):
        """
        Calculate Total Cost of Ownership (TCO) per kWh

        Args:
            capex_per_kwh: Capital cost per kWh
            opex_per_kwh_year: Annual operating cost per kWh
            lifespan_years: Battery lifespan in years

        Returns:
            TCO per kWh over the analysis horizon
        """
        # Use NPV calculation over full TCO horizon
        horizon = self.tco_horizon

        # Initial capex
        tco = capex_per_kwh

        # Add discounted opex over full horizon
        for year in range(1, horizon + 1):
            discount_factor = (1 + self.discount_rate) ** year
            tco += opex_per_kwh_year / discount_factor

        # Add replacement costs if needed
        if self.tco_horizon > lifespan_years:
            # Calculate number of replacements needed
            num_replacements = self.tco_horizon // lifespan_years
            for replacement in range(1, num_replacements + 1):
                replacement_year = lifespan_years * replacement
                if replacement_year < self.tco_horizon:
                    discount_factor = (1 + self.discount_rate) ** replacement_year
                    tco += capex_per_kwh / discount_factor

        # Return total NPV (not amortized - this gives true TCO comparison)
        return tco

    def calculate_s_curve(self, tco_difference):
        """
        Calculate technology adoption using S-curve based on TCO advantage

        Args:
            tco_difference: Array of (VRLA TCO - Lithium TCO) per year

        Returns:
            Array of Li-ion market share (0 to 1)
        """
        # S-curve formula: L / (1 + exp(-k * (t - t0)))
        # Where k is influenced by cost sensitivity

        L = self.s_curve_params['ceiling_L']  # Maximum adoption (e.g., 0.95)
        k0 = self.s_curve_params['base_steepness_k0']  # Base steepness
        s = self.s_curve_params['cost_sensitivity_s']  # Cost sensitivity

        # Find tipping point (first year TCO favors lithium)
        tipping_idx = None
        for i, diff in enumerate(tco_difference):
            if diff > 0:  # Lithium is cheaper
                tipping_idx = i
                break

        if tipping_idx is None:
            # Lithium never becomes cheaper - use slow adoption
            print("Warning: No tipping point found - Li-ion does not achieve cost parity")
            return np.linspace(0.01, 0.2, len(tco_difference))

        self.tipping_year = self.years[tipping_idx]
        t0 = tipping_idx  # Midpoint at tipping year

        # Calculate adoption curve
        adoption = []
        for i in range(len(self.years)):
            # Cost-adjusted steepness
            k = k0 + s * max(0, tco_difference[i])

            # Apply scenario acceleration factor
            k *= self.scenario.get('adoption_acceleration', 1.0)

            # S-curve
            t_rel = i - t0
            share = L / (1 + np.exp(-k * t_rel))

            # Ensure monotonic increase (market doesn't regress)
            if i > 0 and share < adoption[-1]:
                share = adoption[-1]

            adoption.append(share)

        return np.array(adoption)

    def forecast_demand(self):
        """
        Forecast battery demand by technology using market growth + technology transition
        """
        # Get historical growth rates
        growth_rates = self.hist_growth_rates

        # Project total market demand
        total_demand = []
        last_hist_year = self.hist_total_demand.index.max()
        last_hist_value = self.hist_total_demand.iloc[-1]

        for year in self.years:
            if year <= last_hist_year and year in self.hist_total_demand.index:
                # Use historical data
                total_demand.append(self.hist_total_demand[year])
            else:
                # Project using growth rate
                if year in growth_rates.index:
                    growth_rate = growth_rates[year] / 100.0  # Convert from percentage
                else:
                    # Use last known growth rate
                    growth_rate = growth_rates.iloc[-1] / 100.0

                # Compound from last historical value
                years_ahead = year - last_hist_year
                projected = last_hist_value * ((1 + growth_rate) ** years_ahead)
                total_demand.append(projected)

        self.total_demand_forecast = pd.Series(total_demand, index=self.years)

        # Forecast costs
        vrla_costs, lithium_costs = self.forecast_costs()

        # Calculate TCO for each technology
        vrla_opex = self.vrla_params['opex_per_kwh_year']
        lithium_opex = self.lithium_params['opex_per_kwh_year']

        vrla_tco = np.array([
            self.calculate_tco(vrla_costs[year], vrla_opex, self.vrla_lifespan)
            for year in self.years
        ])

        lithium_tco = np.array([
            self.calculate_tco(lithium_costs[year], lithium_opex, self.lithium_lifespan)
            for year in self.years
        ])

        # Calculate TCO difference (positive = lithium advantage)
        tco_difference = vrla_tco - lithium_tco

        # Calculate S-curve adoption
        lithium_share = self.calculate_s_curve(tco_difference)
        vrla_share = 1 - lithium_share

        # Split demand by technology
        lithium_demand = self.total_demand_forecast * lithium_share
        vrla_demand = self.total_demand_forecast * vrla_share

        # Store results
        self.results['total_demand_gwh'] = self.total_demand_forecast.values
        self.results['vrla_demand_gwh'] = vrla_demand.values
        self.results['lithium_demand_gwh'] = lithium_demand.values
        self.results['vrla_share_pct'] = vrla_share * 100
        self.results['lithium_share_pct'] = lithium_share * 100

        self.results['vrla_capex_per_kwh'] = vrla_costs.values
        self.results['lithium_capex_per_kwh'] = lithium_costs.values
        self.results['vrla_tco_per_kwh'] = vrla_tco
        self.results['lithium_tco_per_kwh'] = lithium_tco
        self.results['tco_advantage'] = tco_difference

        self.results['region'] = self.region
        self.results['scenario'] = self.scenario_name
        self.results['tipping_year'] = self.tipping_year if self.tipping_year else 'N/A'

    def forecast_installed_base(self):
        """
        Track installed base evolution using stock-flow accounting
        IB(t+1) = IB(t) + Adds(t) - Retirements(t)
        """
        vrla_ib = []
        lithium_ib = []

        # Initialize from historical data or zero
        if self.start_year in self.real_data['vrla_installed_base'].get(self.region, pd.Series()).index:
            vrla_ib_t = self.real_data['vrla_installed_base'][self.region][self.start_year]
        else:
            # Estimate initial installed base from demand and lifespan
            vrla_ib_t = self.results['vrla_demand_gwh'].iloc[0] * self.vrla_lifespan

        lithium_ib_t = 0  # Conservative assumption: start at zero

        for i, year in enumerate(self.years):
            # Additions = Annual demand
            vrla_adds = self.results['vrla_demand_gwh'].iloc[i]
            lithium_adds = self.results['lithium_demand_gwh'].iloc[i]

            # Retirements = IB / Lifespan (simplified exponential decay)
            vrla_retirements = vrla_ib_t / self.vrla_lifespan
            lithium_retirements = lithium_ib_t / self.lithium_lifespan

            # Update stocks
            vrla_ib_t = vrla_ib_t + vrla_adds - vrla_retirements
            lithium_ib_t = lithium_ib_t + lithium_adds - lithium_retirements

            # Ensure non-negative
            vrla_ib.append(max(0, vrla_ib_t))
            lithium_ib.append(max(0, lithium_ib_t))

        # Add to results
        self.results['vrla_installed_base_gwh'] = vrla_ib
        self.results['lithium_installed_base_gwh'] = lithium_ib
        self.results['total_installed_base_gwh'] = np.array(vrla_ib) + np.array(lithium_ib)

        # Calculate and validate mass balance
        for i in range(1, len(self.years)):
            # Mass balance: IB(t) - IB(t-1) - Adds(t) + Retirements(t) should be ~0
            vrla_delta_ib = self.results['vrla_installed_base_gwh'].iloc[i] - self.results['vrla_installed_base_gwh'].iloc[i-1]
            vrla_adds = self.results['vrla_demand_gwh'].iloc[i]
            vrla_retirements = self.results['vrla_installed_base_gwh'].iloc[i-1] / self.vrla_lifespan
            vrla_imbalance = abs(vrla_delta_ib - vrla_adds + vrla_retirements)

            if vrla_imbalance > 0.001:  # 0.1% tolerance
                print(f"⚠️  WARNING: VRLA mass balance imbalance in {self.years[i]}: {vrla_imbalance:.4f} GWh")

    def decompose_market_demand(self):
        """
        Decompose total demand into new-build and replacement segments
        New-build = Growth in market capacity
        Replacement = Retirements from installed base
        """
        new_build_demand = []
        replacement_demand = []
        contestable_market = []

        for i, year in enumerate(self.years):
            if i == 0:
                # Base year: estimate 70% replacement, 30% new-build
                total = self.results['total_demand_gwh'].iloc[i]
                new_build_demand.append(total * 0.30)
                replacement_demand.append(total * 0.70)
                contestable_market.append(0)
            else:
                # New-build demand from market growth
                # Use growth rate or calculate from demand increase
                if year in self.hist_growth_rates.index:
                    growth_rate = self.hist_growth_rates[year] / 100.0
                else:
                    growth_rate = self.hist_growth_rates.iloc[-1] / 100.0 if not self.hist_growth_rates.empty else 0.08

                # New-build is the growth portion
                prev_total_ib = self.results['total_installed_base_gwh'].iloc[i-1]
                new_build = prev_total_ib * growth_rate

                # Replacement demand from retirements
                vrla_retirements = self.results['vrla_installed_base_gwh'].iloc[i-1] / self.vrla_lifespan
                lithium_retirements = self.results['lithium_installed_base_gwh'].iloc[i-1] / self.lithium_lifespan
                replacement = vrla_retirements + lithium_retirements

                # Contestable market = VRLA reaching end-of-life (can switch to Li-ion)
                contestable = vrla_retirements

                new_build_demand.append(new_build)
                replacement_demand.append(replacement)
                contestable_market.append(contestable)

        # Add to results
        self.results['new_build_demand_gwh'] = new_build_demand
        self.results['replacement_demand_gwh'] = replacement_demand
        self.results['contestable_market_gwh'] = contestable_market

        # Validate: new-build + replacement should roughly equal total demand
        for i in range(len(self.years)):
            total_decomposed = new_build_demand[i] + replacement_demand[i]
            total_actual = self.results['total_demand_gwh'].iloc[i]
            diff = abs(total_decomposed - total_actual)
            if diff > total_actual * 0.15:  # 15% tolerance (market dynamics can vary)
                print(f"⚠️  Note: Market decomposition in {self.years[i]} differs from total by {diff/total_actual*100:.1f}%")

    def calculate_battery_metrics(self):
        """
        Calculate power capacity, throughput, and other battery metrics
        """
        battery_config = self.config['battery_metrics']
        duration_h = battery_config['duration_hours']
        cycles_per_year = battery_config['cycles_per_year']
        rte = battery_config['round_trip_efficiency']

        # Power capacity (MW) = Energy (GWh) × 1000 / Duration (h)
        self.results['power_capacity_mw'] = self.results['total_demand_gwh'] * 1000 / duration_h

        # VRLA power capacity
        self.results['vrla_power_capacity_mw'] = self.results['vrla_demand_gwh'] * 1000 / duration_h

        # Li-ion power capacity
        self.results['lithium_power_capacity_mw'] = self.results['lithium_demand_gwh'] * 1000 / duration_h

        # Annual throughput (GWh/year) = Capacity × Cycles per year × RTE
        self.results['annual_throughput_gwh'] = (
            self.results['total_installed_base_gwh'] * cycles_per_year * rte
        )

        # Cycle life utilization
        self.results['cycles_per_year'] = cycles_per_year
        self.results['round_trip_efficiency_pct'] = rte * 100

    def validate_forecast(self):
        """Validate forecast against historical data"""
        validation_rules = self.config['validation_rules']

        print("\n=== Forecast Validation ===")

        # Check non-negativity
        if validation_rules['non_negativity']:
            has_negative = (self.results['vrla_demand_gwh'] < 0).any() or (self.results['lithium_demand_gwh'] < 0).any()
            if has_negative:
                print("✗ FAIL: Negative demand values detected")
            else:
                print("✓ PASS: All demand values non-negative")

        # Check monotonic adoption
        if validation_rules['monotonic_adoption']:
            lithium_share = self.results['lithium_share_pct'].values
            is_monotonic = all(lithium_share[i] <= lithium_share[i+1] for i in range(len(lithium_share)-1))
            if is_monotonic:
                print("✓ PASS: Li-ion adoption is monotonically increasing")
            else:
                print("✗ WARNING: Li-ion adoption is not monotonic")

        # Compare to historical data for overlapping years
        hist_years = self.hist_total_demand.index
        overlap_years = [y for y in self.years if y in hist_years]

        if len(overlap_years) > 0:
            tolerance = validation_rules['total_demand_tolerance']
            for year in overlap_years:
                hist_val = self.hist_total_demand[year]
                forecast_val = self.results[self.results['year'] == year]['total_demand_gwh'].values[0]
                error = abs(forecast_val - hist_val) / hist_val

                if error <= tolerance:
                    print(f"✓ PASS: Year {year} within {tolerance*100}% tolerance (error: {error*100:.1f}%)")
                else:
                    print(f"✗ WARNING: Year {year} exceeds tolerance (error: {error*100:.1f}%)")

    def print_summary(self):
        """Print forecast summary"""
        print(f"\n{'='*70}")
        print(f"Datacenter UPS Battery Transition Forecast - {self.region}")
        print(f"Scenario: {self.scenario_name}")
        print(f"Years: {self.start_year} - {self.end_year}")
        print(f"{'='*70}\n")

        # Key findings
        start_lithium_share = self.results['lithium_share_pct'].iloc[0]
        end_lithium_share = self.results['lithium_share_pct'].iloc[-1]
        mid_lithium_share = self.results['lithium_share_pct'].iloc[len(self.results)//2]

        print(f"Li-ion Market Share:")
        print(f"  {self.start_year}: {start_lithium_share:.1f}%")
        print(f"  {self.years[len(self.years)//2]}: {mid_lithium_share:.1f}%")
        print(f"  {self.end_year}: {end_lithium_share:.1f}%\n")

        print(f"Total Market Demand:")
        print(f"  {self.start_year}: {self.results['total_demand_gwh'].iloc[0]:.2f} GWh/year")
        print(f"  {self.end_year}: {self.results['total_demand_gwh'].iloc[-1]:.2f} GWh/year")
        print(f"  CAGR: {((self.results['total_demand_gwh'].iloc[-1] / self.results['total_demand_gwh'].iloc[0]) ** (1/(self.end_year - self.start_year)) - 1) * 100:.1f}%\n")

        if self.tipping_year:
            print(f"TCO Tipping Point: {self.tipping_year}")
            tipping_idx = self.years.index(self.tipping_year)
            tipping_advantage = self.results['tco_advantage'].iloc[tipping_idx]
            print(f"  Li-ion TCO advantage: ${tipping_advantage:.2f}/kWh\n")
        else:
            print("TCO Tipping Point: Not reached in forecast period\n")

        # Final year details
        final_row = self.results.iloc[-1]
        print(f"Year {self.end_year} Breakdown:")
        print(f"  Total Demand: {final_row['total_demand_gwh']:.2f} GWh")
        print(f"  VRLA Demand: {final_row['vrla_demand_gwh']:.2f} GWh ({final_row['vrla_share_pct']:.1f}%)")
        print(f"  Li-ion Demand: {final_row['lithium_demand_gwh']:.2f} GWh ({final_row['lithium_share_pct']:.1f}%)")
        print(f"\n  VRLA TCO: ${final_row['vrla_tco_per_kwh']:.2f}/kWh")
        print(f"  Li-ion TCO: ${final_row['lithium_tco_per_kwh']:.2f}/kWh")

    def save_results(self, output_path):
        """Save forecast results to CSV"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        self.results.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Datacenter UPS Battery Transition Forecasting')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to forecast (Global, China, USA, Europe, Rest_of_World)')
    parser.add_argument('--scenario', type=str, default='baseline',
                       help='Scenario to use (baseline, accelerated, delayed, high_opex)')
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
    print(f"Initializing forecast for {args.region}...")
    forecast = DatacenterUPSForecast(config_path, region=args.region, scenario=args.scenario)

    print("Loading data...")
    forecast.load_data()

    print("Running forecast...")
    forecast.forecast_demand()

    print("Calculating installed base...")
    forecast.forecast_installed_base()

    print("Decomposing market demand...")
    forecast.decompose_market_demand()

    print("Calculating battery metrics...")
    forecast.calculate_battery_metrics()

    print("Validating forecast...")
    forecast.validate_forecast()

    # Print summary
    forecast.print_summary()

    # Save results
    if args.output:
        output_path = args.output
    else:
        output_dir = skill_dir / 'output'
        output_path = output_dir / f'datacenter_ups_forecast_{args.region}_{args.scenario}.csv'

    forecast.save_results(output_path)

    print("\n✓ Forecast complete!")


if __name__ == "__main__":
    main()
