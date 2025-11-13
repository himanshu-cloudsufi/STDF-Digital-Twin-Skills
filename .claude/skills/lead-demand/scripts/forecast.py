#!/usr/bin/env python3
"""
Lead Demand Forecasting - Bottom-up Installed-Base Accounting
Models impact of vehicle electrification on SLI battery lead demand
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from data_loader import LeadDataLoader


class LeadDemandForecast:
    """
    Lead demand forecasting model using bottom-up fleet accounting
    Focuses on SLI (Starting-Lighting-Ignition) battery impact from vehicle electrification
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
        self.lead_coeffs = self.config['lead_coefficients']
        self.battery_lifetimes = self.config['battery_lifetimes']
        self.asset_lifetimes = self.config['asset_lifetimes']

        # Initialize results
        self.years = list(range(self.start_year, self.end_year + 1))
        self.results = pd.DataFrame({'year': self.years})

        # Initialize data loader
        self.data_loader = LeadDataLoader()
        self.real_data = None

    def load_data(self):
        """Load all required data"""
        try:
            # Get vehicle data scenario from config
            vehicle_scenario = self.config['default_parameters'].get('vehicle_data_scenario', 'standard')
            self.real_data = self.data_loader.load_all_data(scenario=vehicle_scenario)

            if self.region in self.real_data['total_demand']:
                self.hist_total_demand = self.real_data['total_demand'][self.region]
                print(f"✓ Data loaded for {self.region}, years {self.start_year} to {self.end_year}")
                print(f"✓ Using scenario: {self.scenario_name}")
            else:
                # For regions without Global data, estimate from other sources
                print(f"Warning: Limited historical data for {self.region}")
                self.hist_total_demand = pd.Series()

        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def calculate_sli_demand(self):
        """
        Calculate SLI battery lead demand from vehicle fleet
        Uses bottom-up installed-base accounting
        """
        sli_demand_by_type = {}

        # Process each vehicle type
        vehicle_types = {
            'passenger_cars': ('passenger_car', ['ICE', 'BEV', 'PHEV', 'HEV']),
            'two_wheelers': ('two_wheeler', ['ICE', 'EV']),
            'three_wheelers': ('three_wheeler', ['ICE', 'EV']),
            'commercial_vehicles': ('commercial_vehicle', ['ICE', 'EV', 'NGV'])
        }

        total_sli_demand = pd.Series(0, index=self.years)

        for vehicle_key, (coeff_key, powertrains) in vehicle_types.items():
            vehicle_data = self.real_data['vehicles'][vehicle_key]

            if self.region in vehicle_data['fleet']:
                fleet_by_powertrain = vehicle_data['fleet'][self.region]

                # Get lead coefficients for this vehicle type
                sli_coeffs = self.lead_coeffs['sli_batteries'][coeff_key]

                # Calculate demand for each powertrain
                for powertrain in powertrains:
                    if powertrain in fleet_by_powertrain:
                        fleet_series = fleet_by_powertrain[powertrain]

                        # Get coefficient (in kg)
                        pt_lower = powertrain.lower()
                        if pt_lower in sli_coeffs:
                            coeff = sli_coeffs[pt_lower]

                            # Special handling for PHEV: may use dataset or fallback
                            if pt_lower == 'phev' and coeff == "dataset":
                                # Try to load PHEV coefficient from vehicle data
                                phev_coeff_loaded = False
                                if 'lead_content' in vehicle_data and self.region in vehicle_data['lead_content']:
                                    if 'PHEV' in vehicle_data['lead_content'][self.region]:
                                        phev_series = vehicle_data['lead_content'][self.region]['PHEV']
                                        # Use the last available value or interpolate
                                        if not phev_series.empty:
                                            # Get value for current year or use last known
                                            last_known_value = phev_series.iloc[-1]
                                            coeff = last_known_value
                                            phev_coeff_loaded = True

                                # If dataset loading failed, use fallback from config
                                if not phev_coeff_loaded:
                                    coeff = sli_coeffs.get('phev_fallback', 10.5)
                                    if not phev_coeff_loaded:
                                        print(f"⚠️  PHEV dataset unavailable, using fallback coefficient: {coeff} kg")
                        else:
                            continue  # Skip if no coefficient

                        # Calculate annual replacement demand
                        # Fleet is in millions of units
                        # Replacement = Fleet / Battery_Lifetime
                        battery_life = self.battery_lifetimes['sli_years']
                        scenario_life_improvement = self.scenario.get('battery_life_improvement', 1.0)
                        effective_life = battery_life * scenario_life_improvement

                        replacements_per_year = fleet_series / effective_life  # millions/year

                        # Lead demand = replacements × coefficient
                        # millions × kg = thousands of tonnes
                        annual_demand = replacements_per_year * coeff  # thousands of tonnes

                        # Reindex to our forecast years
                        annual_demand = annual_demand.reindex(self.years, fill_value=0)

                        # Add to total
                        total_sli_demand = total_sli_demand.add(annual_demand, fill_value=0)

                        # Store by type
                        key = f"{vehicle_key}_{powertrain}"
                        sli_demand_by_type[key] = annual_demand

        return total_sli_demand, sli_demand_by_type

    def calculate_industrial_demand(self):
        """
        Calculate industrial battery lead demand
        Uses aggregate data with historical trends
        """
        industrial_data = self.real_data['industrial_batteries']

        # Get historical data for Global (most complete)
        if 'Global' in industrial_data['motive']:
            motive_hist = industrial_data['motive']['Global']
            stationary_hist = industrial_data['stationary']['Global']

            # Project forward using trend
            motive_demand = []
            stationary_demand = []

            for year in self.years:
                if year in motive_hist.index:
                    motive_demand.append(motive_hist[year])
                else:
                    # Simple linear projection from last known values
                    last_year = motive_hist.index.max()
                    last_value = motive_hist.iloc[-1]
                    # Assume slight decline due to electrification
                    years_ahead = year - last_year
                    projected = last_value * (0.97 ** years_ahead)  # 3% annual decline
                    motive_demand.append(projected)

                if year in stationary_hist.index:
                    stationary_demand.append(stationary_hist[year])
                else:
                    last_year = stationary_hist.index.max()
                    last_value = stationary_hist.iloc[-1]
                    years_ahead = year - last_year
                    projected = last_value * (0.95 ** years_ahead)  # 5% annual decline (Li-ion replacement)
                    stationary_demand.append(projected)

            motive_series = pd.Series(motive_demand, index=self.years)
            stationary_series = pd.Series(stationary_demand, index=self.years)

            total_industrial = motive_series + stationary_series

            return total_industrial, motive_series, stationary_series
        else:
            # Fallback: use historical shares
            return pd.Series(0, index=self.years), pd.Series(0, index=self.years), pd.Series(0, index=self.years)

    def calculate_other_uses(self):
        """
        Calculate non-battery lead uses
        Assumes relatively stable with modest decline
        """
        other_uses_data = self.real_data['non_battery_uses']

        if 'Global' in other_uses_data:
            hist_data = other_uses_data['Global']

            other_uses = []
            for year in self.years:
                if year in hist_data.index:
                    other_uses.append(hist_data[year])
                else:
                    # Project with slow decline
                    last_year = hist_data.index.max()
                    last_value = hist_data.iloc[-1]
                    years_ahead = year - last_year
                    projected = last_value * (0.99 ** years_ahead)  # 1% annual decline
                    other_uses.append(projected)

            return pd.Series(other_uses, index=self.years)
        else:
            # Estimate as 15% of total if no data
            return pd.Series(0, index=self.years)

    def forecast_demand(self):
        """Run complete lead demand forecast"""

        # Calculate each segment
        print("\nCalculating SLI battery demand...")
        sli_total, sli_by_type = self.calculate_sli_demand()

        # Check if SLI calculation failed or returned suspiciously low values
        # Expected: SLI should be ~8,000-10,000 kt for Global, ~100+ kt minimum
        max_sli = sli_total.max()
        if max_sli < 100:
            print(f"⚠️  WARNING: Bottom-up SLI calculation returned very low values (max: {max_sli:.1f} kt)")
            print("⚠️  Attempting aggregate fallback...")

            # Try to load aggregate SLI demand data
            try:
                passenger_cars_data = self.real_data['vehicles']['passenger_cars']

                # Load aggregate demand datasets
                # These are in Passenger_Cars.json but at the root level
                from pathlib import Path
                data_path = self.data_loader.base_data_path / 'Passenger_Cars.json'
                with open(data_path, 'r') as f:
                    import json
                    pc_data = json.load(f)
                    pc_category = pc_data.get('Passenger Cars', {})

                # Extract aggregate SLI demand
                sales_demand_metric = 'Lead_Annual_Implied_Demand-Sales_Cars'
                replacement_demand_metric = 'Lead_Annual_Implied_Demand-Vehicle_replacement_Cars'

                if sales_demand_metric in pc_category:
                    sales_regional = self.data_loader._extract_regional_series(pc_category, sales_demand_metric)
                    replacement_regional = self.data_loader._extract_regional_series(pc_category, replacement_demand_metric)

                    if self.region in sales_regional and self.region in replacement_regional:
                        sales_series = sales_regional[self.region].reindex(self.years, fill_value=0)
                        replacement_series = replacement_regional[self.region].reindex(self.years, fill_value=0)
                        sli_total_aggregate = sales_series + replacement_series

                        print(f"✓ Using aggregate SLI data: {sli_total_aggregate.get(2024, 'N/A'):.1f} kt (2024)")
                        sli_total = sli_total_aggregate
                    else:
                        print(f"✗ Aggregate data not available for region {self.region}")
                else:
                    print("✗ Aggregate SLI demand metrics not found in data")

            except Exception as e:
                print(f"✗ Aggregate fallback failed: {e}")
                print("⚠️  Proceeding with bottom-up results (may be inaccurate)")

        print("Calculating industrial battery demand...")
        industrial_total, motive, stationary = self.calculate_industrial_demand()

        print("Calculating other uses...")
        other_uses = self.calculate_other_uses()

        # Apply scenario demand multiplier
        multiplier = self.scenario.get('demand_multiplier', 1.0)
        sli_total = sli_total * multiplier
        industrial_total = industrial_total * multiplier

        # Total demand
        total_battery_demand = sli_total + industrial_total
        total_demand = total_battery_demand + other_uses

        # Store results
        self.results['total_lead_demand_kt'] = total_demand.values
        self.results['battery_demand_kt'] = total_battery_demand.values
        self.results['sli_demand_kt'] = sli_total.values
        self.results['industrial_demand_kt'] = industrial_total.values
        self.results['industrial_motive_kt'] = motive.values
        self.results['industrial_stationary_kt'] = stationary.values
        self.results['other_uses_kt'] = other_uses.values

        # Calculate market shares
        self.results['battery_share_pct'] = (total_battery_demand / total_demand * 100).values
        self.results['sli_share_pct'] = (sli_total / total_demand * 100).values

        self.results['region'] = self.region
        self.results['scenario'] = self.scenario_name

    def validate_forecast(self):
        """Validate forecast against historical data"""
        print("\n=== Forecast Validation ===")

        # Check non-negativity
        has_negative = (self.results[['total_lead_demand_kt', 'battery_demand_kt', 'sli_demand_kt']] < 0).any().any()
        if has_negative:
            print("✗ FAIL: Negative demand values detected")
        else:
            print("✓ PASS: All demand values non-negative")

        # Compare to historical where available
        if not self.hist_total_demand.empty:
            hist_years = self.hist_total_demand.index
            overlap_years = [y for y in self.years if y in hist_years]

            if len(overlap_years) > 0:
                tolerance = self.config['validation_rules']['tolerance_percent'] / 100.0

                errors = []
                for year in overlap_years[:min(5, len(overlap_years))]:  # Check first 5 overlap years
                    hist_val = self.hist_total_demand[year]
                    forecast_val = self.results[self.results['year'] == year]['total_lead_demand_kt'].values[0]
                    error = abs(forecast_val - hist_val) / hist_val if hist_val > 0 else 0

                    errors.append(error)
                    if error <= tolerance:
                        print(f"✓ PASS: Year {year} within {tolerance*100:.0f}% tolerance (error: {error*100:.1f}%)")
                    else:
                        print(f"✗ WARNING: Year {year} exceeds tolerance (error: {error*100:.1f}%)")

                avg_error = np.mean(errors) * 100 if errors else 0
                print(f"\nAverage error for overlap period: {avg_error:.1f}%")

                # Enhanced reconciliation reporting for large errors
                if avg_error > 50:
                    print(f"\n{'='*60}")
                    print("✗ CRITICAL: Forecast variance exceeds 50%")
                    print(f"{'='*60}")
                    print("\nDiagnostic Analysis:")

                    # Analyze which components are problematic
                    test_year = overlap_years[0] if overlap_years else 2024
                    if test_year in self.results['year'].values:
                        idx = self.results[self.results['year'] == test_year].index[0]
                        sli_val = self.results.loc[idx, 'sli_demand_kt']
                        ind_val = self.results.loc[idx, 'industrial_demand_kt']
                        other_val = self.results.loc[idx, 'other_uses_kt']
                        total_val = self.results.loc[idx, 'total_lead_demand_kt']
                        hist_val = self.hist_total_demand.get(test_year, 0)

                        print(f"  Year {test_year} Breakdown:")
                        print(f"    SLI demand:        {sli_val:>8.1f} kt ({sli_val/total_val*100:>5.1f}%)")
                        print(f"    Industrial demand: {ind_val:>8.1f} kt ({ind_val/total_val*100:>5.1f}%)")
                        print(f"    Other uses:        {other_val:>8.1f} kt ({other_val/total_val*100:>5.1f}%)")
                        print(f"    ─────────────────────────────────")
                        print(f"    Calculated total:  {total_val:>8.1f} kt")
                        print(f"    Historical total:  {hist_val:>8.1f} kt")
                        print(f"    Difference:        {total_val - hist_val:>8.1f} kt")

                        # Identify problematic component
                        if sli_val < 100:
                            print(f"\n  ⚠️  SLI demand suspiciously low (expected ~8,000 kt for Global)")
                            print(f"      Root cause: Vehicle fleet data not loading properly")
                            print(f"      Solution: Check data_loader.py vehicle data parsing")

                        if abs(total_val - hist_val) / hist_val > 0.5:
                            print(f"\n  Recommendation:")
                            print(f"    • Use aggregate fallback data when available")
                            print(f"    • Investigate vehicle fleet data loading issues")
                            print(f"    • Verify powertrain coefficients are being applied")
                    print(f"{'='*60}\n")

    def print_summary(self):
        """Print forecast summary"""
        print(f"\n{'='*70}")
        print(f"Lead Demand Forecast - {self.region}")
        print(f"Scenario: {self.scenario_name}")
        print(f"Years: {self.start_year} - {self.end_year}")
        print(f"{'='*70}\n")

        # Key metrics
        start_demand = self.results['total_lead_demand_kt'].iloc[0]
        end_demand = self.results['total_lead_demand_kt'].iloc[-1]
        decline_pct = ((end_demand / start_demand) - 1) * 100

        print(f"Total Lead Demand:")
        print(f"  {self.start_year}: {start_demand:.0f} kt")
        print(f"  {self.end_year}: {end_demand:.0f} kt")
        print(f"  Change: {decline_pct:+.1f}%\n")

        # Breakdown at final year
        final = self.results.iloc[-1]
        print(f"Year {self.end_year} Breakdown:")
        print(f"  Total Demand: {final['total_lead_demand_kt']:.0f} kt")
        print(f"    Battery Uses: {final['battery_demand_kt']:.0f} kt ({final['battery_share_pct']:.1f}%)")
        print(f"      - SLI Batteries: {final['sli_demand_kt']:.0f} kt")
        print(f"      - Industrial Motive: {final['industrial_motive_kt']:.0f} kt")
        print(f"      - Industrial Stationary: {final['industrial_stationary_kt']:.0f} kt")
        print(f"    Other Uses: {final['other_uses_kt']:.0f} kt")

        # Key insight
        start_sli_share = self.results['sli_share_pct'].iloc[0]
        end_sli_share = self.results['sli_share_pct'].iloc[-1]
        print(f"\nSLI Battery Share of Total Demand:")
        print(f"  {self.start_year}: {start_sli_share:.1f}%")
        print(f"  {self.end_year}: {end_sli_share:.1f}%")
        print(f"  Change: {end_sli_share - start_sli_share:+.1f} percentage points")

    def save_results(self, output_path):
        """Save forecast results to CSV"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        self.results.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Lead Demand Forecasting')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to forecast')
    parser.add_argument('--scenario', type=str, default='baseline',
                       help='Scenario to use')
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
    forecast = LeadDemandForecast(config_path, region=args.region, scenario=args.scenario)

    print("Loading data...")
    forecast.load_data()

    print("Running forecast...")
    forecast.forecast_demand()

    print("Validating forecast...")
    forecast.validate_forecast()

    # Print summary
    forecast.print_summary()

    # Save results
    if args.output:
        output_path = args.output
    else:
        output_dir = skill_dir / 'output'
        output_path = output_dir / f'lead_demand_forecast_{args.region}_{args.scenario}.csv'

    forecast.save_results(output_path)

    print("\n✓ Forecast complete!")


if __name__ == "__main__":
    main()
