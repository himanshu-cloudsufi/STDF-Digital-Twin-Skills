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


    def __init__(self, config_path, region='Global', scenario='baseline', start_year=None, end_year=None):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Use provided years or fall back to config defaults
        self.start_year = start_year if start_year is not None else self.config['default_parameters']['start_year']
        self.end_year = end_year if end_year is not None else self.config['default_parameters']['end_year']
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

    def initialize_and_evolve_installed_base(self):
        """
        Initialize and evolve installed base using equation:
        IB_A(t+1) = IB_A(t) + Adds_A(t) - Scrappage_A(t)
        where Scrappage_A(t) ≈ IB_A(t) / Life_Asset_A

        Returns:
            dict: Evolved installed base by vehicle type and powertrain
        """
        vehicle_types = {
            'passenger_cars': ('passenger_car', ['ICE', 'BEV', 'PHEV', 'HEV']),
            'two_wheelers': ('two_wheeler', ['ICE', 'EV']),
            'three_wheelers': ('three_wheeler', ['ICE', 'EV']),
            'commercial_vehicles': ('commercial_vehicle', ['ICE', 'EV', 'NGV'])
        }

        # Asset lifetime mapping
        asset_life_map = {
            'passenger_cars': self.asset_lifetimes['passenger_car_years'],
            'two_wheelers': self.asset_lifetimes['two_wheeler_years'],
            'three_wheelers': self.asset_lifetimes['three_wheeler_years'],
            'commercial_vehicles': self.asset_lifetimes['commercial_vehicle_years']
        }

        evolved_ib = {}

        for vehicle_key, (coeff_key, powertrains) in vehicle_types.items():
            vehicle_data = self.real_data['vehicles'][vehicle_key]
            asset_life = asset_life_map[vehicle_key]

            if self.region not in vehicle_data['fleet'] or self.region not in vehicle_data['sales']:
                continue

            fleet_by_powertrain = vehicle_data['fleet'][self.region]
            sales_by_powertrain = vehicle_data['sales'][self.region]

            for powertrain in powertrains:
                if powertrain not in fleet_by_powertrain or powertrain not in sales_by_powertrain:
                    continue

                fleet_series = fleet_by_powertrain[powertrain]
                sales_series = sales_by_powertrain[powertrain]

                # Initialize IB with first available fleet data
                ib_by_year = {}

                for year in self.years:
                    if year in fleet_series.index:
                        # Use historical fleet data as IB
                        ib_by_year[year] = fleet_series[year]
                    else:
                        # Evolve IB forward
                        prev_year = year - 1
                        if prev_year in ib_by_year:
                            # Get previous IB (in millions)
                            ib_prev = ib_by_year[prev_year]

                            # Get adds (sales) for current year
                            # Sales are in units, convert to millions to match IB units
                            adds_units = sales_series.get(year, sales_series.iloc[-1] if not sales_series.empty else 0)
                            adds = adds_units / 1_000_000  # Convert to millions

                            # Calculate scrappage (in millions)
                            scrappage = ib_prev / asset_life

                            # Update IB (in millions)
                            ib_current = ib_prev + adds - scrappage
                            ib_by_year[year] = max(0, ib_current)  # Non-negative
                        else:
                            # No previous IB, use sales or zero
                            ib_by_year[year] = 0

                # Store evolved IB
                key = f"{vehicle_key}_{powertrain}"
                evolved_ib[key] = pd.Series(ib_by_year)

        return evolved_ib

    def calculate_sli_oem_demand(self):
        """
        Calculate SLI OEM battery lead demand from vehicle sales
        Formula: SLI_OEM(t) = Σ Sales(t) × k_v,p (kg)
        """
        oem_demand_by_type = {}

        # Process each vehicle type
        vehicle_types = {
            'passenger_cars': ('passenger_car', ['ICE', 'BEV', 'PHEV', 'HEV']),
            'two_wheelers': ('two_wheeler', ['ICE', 'EV']),
            'three_wheelers': ('three_wheeler', ['ICE', 'EV']),
            'commercial_vehicles': ('commercial_vehicle', ['ICE', 'EV', 'NGV'])
        }

        total_oem_demand = pd.Series(0, index=self.years)

        for vehicle_key, (coeff_key, powertrains) in vehicle_types.items():
            vehicle_data = self.real_data['vehicles'][vehicle_key]

            if self.region in vehicle_data['sales']:
                sales_by_powertrain = vehicle_data['sales'][self.region]

                # Get lead coefficients for this vehicle type
                sli_coeffs = self.lead_coeffs['sli_batteries'][coeff_key]

                # Calculate OEM demand for each powertrain
                for powertrain in powertrains:
                    if powertrain in sales_by_powertrain:
                        sales_series = sales_by_powertrain[powertrain]

                        # Get coefficient (in kg)
                        pt_lower = powertrain.lower()
                        if pt_lower in sli_coeffs:
                            coeff = sli_coeffs[pt_lower]

                            # Special handling for PHEV
                            if pt_lower == 'phev' and coeff == "dataset":
                                phev_coeff_loaded = False
                                if 'lead_content' in vehicle_data and self.region in vehicle_data['lead_content']:
                                    if 'PHEV' in vehicle_data['lead_content'][self.region]:
                                        phev_series = vehicle_data['lead_content'][self.region]['PHEV']
                                        if not phev_series.empty:
                                            coeff = phev_series.iloc[-1]
                                            phev_coeff_loaded = True

                                if not phev_coeff_loaded:
                                    coeff = sli_coeffs.get('phev_fallback', 10.5)
                        else:
                            continue

                        # Calculate annual OEM demand
                        # Sales are in units per year (from metadata: 'vehicles/year')
                        # Convert to millions, then multiply by coefficient
                        # (units / 1,000,000) × kg = thousands of tonnes (kt)
                        annual_oem = (sales_series / 1_000_000) * coeff  # thousands of tonnes (kt)

                        # Reindex to our forecast years
                        # Use forward-fill for years beyond available data (maintains last known value)
                        annual_oem = annual_oem.reindex(self.years).ffill().fillna(0)

                        # Add to total
                        total_oem_demand = total_oem_demand.add(annual_oem, fill_value=0)

                        # Store by type
                        key = f"{vehicle_key}_{powertrain}_oem"
                        oem_demand_by_type[key] = annual_oem

        return total_oem_demand, oem_demand_by_type

    def calculate_sli_replacement_demand(self):
        """
        Calculate SLI replacement battery lead demand using evolved installed base
        Formula: SLI_Repl(t) = Σ (IB(t) / Life_Battery) × k_v,p (kg)
        Uses bottom-up installed-base accounting with IB evolution
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

            # Get lead coefficients for this vehicle type
            sli_coeffs = self.lead_coeffs['sli_batteries'][coeff_key]

            # Calculate demand for each powertrain
            for powertrain in powertrains:
                # Use evolved IB if available, otherwise fall back to fleet data
                ib_key = f"{vehicle_key}_{powertrain}"

                if hasattr(self, 'evolved_ib') and ib_key in self.evolved_ib:
                    ib_series = self.evolved_ib[ib_key]
                elif self.region in vehicle_data['fleet'] and powertrain in vehicle_data['fleet'][self.region]:
                    # Fallback to fleet data
                    ib_series = vehicle_data['fleet'][self.region][powertrain]
                else:
                    continue

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

                # Calculate annual replacement demand (contestable demand)
                # IB is in millions of units (converted by data_loader.py line 256)
                # Contestable = IB / Battery_Lifetime
                battery_life = self.battery_lifetimes['sli_years']
                scenario_life_improvement = self.scenario.get('battery_life_improvement', 1.0)
                effective_life = battery_life * scenario_life_improvement

                contestable_per_year = ib_series / effective_life  # millions/year

                # Lead demand = contestable × coefficient
                # millions/year × kg = thousands of tonnes (kt)
                annual_demand = contestable_per_year * coeff  # thousands of tonnes (kt)

                # Reindex to our forecast years
                annual_demand = annual_demand.reindex(self.years, fill_value=0)

                # Add to total
                total_sli_demand = total_sli_demand.add(annual_demand, fill_value=0)

                # Store by type
                key = f"{vehicle_key}_{powertrain}_replacement"
                sli_demand_by_type[key] = annual_demand

        return total_sli_demand, sli_demand_by_type

    def calculate_sli_demand(self):
        """
        Calculate total SLI battery lead demand (OEM + Replacement)
        """
        # Calculate OEM demand from sales
        oem_total, oem_by_type = self.calculate_sli_oem_demand()

        # Calculate replacement demand from fleet
        replacement_total, replacement_by_type = self.calculate_sli_replacement_demand()

        # Combine
        total_sli = oem_total + replacement_total

        # Merge breakdown dictionaries
        sli_by_type = {**oem_by_type, **replacement_by_type}

        return total_sli, oem_total, replacement_total, sli_by_type

    def calculate_industrial_demand(self):
        """
        Calculate industrial battery lead demand
        Uses aggregate data with historical trends and projections
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
        Uses econometric approach with price elasticity when data available,
        otherwise uses simple trend projection
        """
        method = self.config['calculation_methods'].get('other_uses_method', 'econometric_or_fixed')

        other_uses_data = self.real_data['non_battery_uses']

        if 'Global' in other_uses_data:
            hist_data = other_uses_data['Global']

            # Try econometric approach if lead cost data available
            if method in ['econometric_or_fixed', 'econometric'] and 'Global' in self.real_data['lead_cost']:
                lead_cost = self.real_data['lead_cost']['Global']

                # Get econometric parameters
                price_elasticity = self.config['econometric_parameters'].get('other_uses_price_elasticity', -0.3)
                base_growth = self.config['econometric_parameters'].get('base_growth_rate', 0.015)

                other_uses = []
                last_hist_year = hist_data.index.max()
                last_hist_value = hist_data.iloc[-1]

                for year in self.years:
                    if year in hist_data.index:
                        other_uses.append(hist_data[year])
                    else:
                        # Econometric projection
                        years_ahead = year - last_hist_year

                        # Base trend component (linear decline/growth)
                        trend_factor = (1 + base_growth) ** years_ahead

                        # Price effect (if price data available)
                        price_factor = 1.0
                        if year in lead_cost.index and last_hist_year in lead_cost.index:
                            price_current = lead_cost[year]
                            price_base = lead_cost[last_hist_year]
                            if price_base > 0:
                                price_change = price_current / price_base
                                # Apply price elasticity: demand change = elasticity × price change
                                price_factor = price_change ** price_elasticity

                        projected = last_hist_value * trend_factor * price_factor
                        other_uses.append(max(0, projected))

                print(f"✓ Using econometric projection for Other Uses (price elasticity: {price_elasticity})")
                return pd.Series(other_uses, index=self.years)

            else:
                # Fallback to simple trend
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

        # Initialize and evolve installed base
        print("\nInitializing installed base evolution...")
        self.evolved_ib = self.initialize_and_evolve_installed_base()

        # Calculate each segment
        print("Calculating SLI battery demand...")
        sli_total, sli_oem, sli_replacement, sli_by_type = self.calculate_sli_demand()

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

        # Store core results
        self.results['total_lead_demand_kt'] = total_demand.values
        self.results['battery_demand_kt'] = total_battery_demand.values
        self.results['sli_demand_kt'] = sli_total.values
        self.results['sli_oem_kt'] = sli_oem.values
        self.results['sli_replacement_kt'] = sli_replacement.values
        self.results['industrial_demand_kt'] = industrial_total.values
        self.results['industrial_motive_kt'] = motive.values
        self.results['industrial_stationary_kt'] = stationary.values
        self.results['other_uses_kt'] = other_uses.values

        # Add detailed SLI breakdowns by vehicle type
        # Aggregate by vehicle type from sli_by_type dict
        for vehicle_type in ['passenger_cars', 'two_wheelers', 'three_wheelers', 'commercial_vehicles']:
            # OEM by vehicle type
            oem_cols = [k for k in sli_by_type.keys() if vehicle_type in k and '_oem' in k]
            if oem_cols:
                self.results[f'sli_oem_{vehicle_type}_kt'] = sum(
                    sli_by_type[col].reindex(self.years, fill_value=0).values for col in oem_cols
                )

            # Replacement by vehicle type
            repl_cols = [k for k in sli_by_type.keys() if vehicle_type in k and '_replacement' in k]
            if repl_cols:
                self.results[f'sli_replacement_{vehicle_type}_kt'] = sum(
                    sli_by_type[col].reindex(self.years, fill_value=0).values for col in repl_cols
                )

        # Add detailed breakdowns by powertrain for each vehicle type
        for key, series in sli_by_type.items():
            # Clean up the key name for column
            col_name = key.replace('_', '_').replace('passenger_cars', 'cars').replace('two_wheelers', '2w').replace('three_wheelers', '3w').replace('commercial_vehicles', 'cv') + '_kt'
            self.results[col_name] = series.reindex(self.years, fill_value=0).values

        # Add IB tracking columns
        if hasattr(self, 'evolved_ib'):
            for ib_key, ib_series in self.evolved_ib.items():
                # Convert key to column name
                col_name = f"ib_{ib_key.replace('_', '_')}_million_units"
                col_name = col_name.replace('passenger_cars', 'cars').replace('two_wheelers', '2w').replace('three_wheelers', '3w').replace('commercial_vehicles', 'cv')
                self.results[col_name] = ib_series.reindex(self.years, fill_value=0).values

        # Add sales/adds columns from vehicle data
        for vehicle_key in ['passenger_cars', 'two_wheelers', 'three_wheelers', 'commercial_vehicles']:
            if vehicle_key in self.real_data['vehicles']:
                vehicle_data = self.real_data['vehicles'][vehicle_key]
                if self.region in vehicle_data.get('sales', {}):
                    sales_by_powertrain = vehicle_data['sales'][self.region]
                    for powertrain, sales_series in sales_by_powertrain.items():
                        col_name = f"sales_{vehicle_key}_{powertrain.lower()}_million_units"
                        col_name = col_name.replace('passenger_cars', 'cars').replace('two_wheelers', '2w').replace('three_wheelers', '3w').replace('commercial_vehicles', 'cv')
                        self.results[col_name] = sales_series.reindex(self.years, fill_value=0).values

        # Add parameter columns (coefficients)
        vehicle_type_map = {
            'passenger_car': 'cars',
            'two_wheeler': '2w',
            'three_wheeler': '3w',
            'commercial_vehicle': 'cv'
        }
        for vehicle_key, short_name in vehicle_type_map.items():
            if vehicle_key in self.lead_coeffs['sli_batteries']:
                coeffs = self.lead_coeffs['sli_batteries'][vehicle_key]
                for powertrain, coeff in coeffs.items():
                    if powertrain not in ['phev_fallback'] and coeff != "dataset":
                        col_name = f"coeff_{short_name}_{powertrain}_kg"
                        self.results[col_name] = coeff

        # Add lifetime parameters
        self.results['life_battery_sli_years'] = self.battery_lifetimes['sli_years']
        self.results['life_battery_motive_years'] = self.battery_lifetimes['motive_years']
        self.results['life_battery_stationary_years'] = self.battery_lifetimes['stationary_years']
        self.results['life_asset_car_years'] = self.asset_lifetimes['passenger_car_years']
        self.results['life_asset_2w_years'] = self.asset_lifetimes['two_wheeler_years']
        self.results['life_asset_3w_years'] = self.asset_lifetimes['three_wheeler_years']
        self.results['life_asset_cv_years'] = self.asset_lifetimes['commercial_vehicle_years']

        # Calculate and add validation variance metrics
        print("Calculating validation variance...")
        validation_variance = self.calculate_validation_variance(sli_by_type)
        for metric_name, variance_value in validation_variance.items():
            self.results[metric_name] = variance_value
            if variance_value is not None:
                print(f"  {metric_name}: {variance_value:.1f}%")
            else:
                print(f"  {metric_name}: N/A (no validation data)")

        # Calculate market shares
        self.results['battery_share_pct'] = (total_battery_demand / total_demand * 100).values
        self.results['sli_share_pct'] = (sli_total / total_demand * 100).values

        # Add metadata columns
        self.results['region'] = self.region
        self.results['scenario'] = self.scenario_name

        # Apply smoothing to demand columns
        self.apply_smoothing()

    def apply_smoothing(self):
        """
        Apply rolling median smoothing to demand columns
        Uses window size from config (default: 3 years)
        """
        smoothing_window = self.config['default_parameters'].get('smoothing_window', 3)

        # List of columns to smooth (all demand columns in kt)
        demand_columns = [col for col in self.results.columns if col.endswith('_kt')]

        print(f"\nApplying {smoothing_window}-year rolling median smoothing...")

        for col in demand_columns:
            if col in self.results.columns:
                # Apply rolling median
                smoothed = self.results[col].rolling(window=smoothing_window, center=True, min_periods=1).median()
                self.results[col] = smoothed

        print(f"✓ Smoothed {len(demand_columns)} demand columns")

    def calculate_validation_variance(self, sli_by_type):
        """
        Compare calculated demand against validation datasets and compute variance
        Returns dict of variance metrics by vehicle type
        """
        validation_results = {}

        # Map vehicle types
        vehicle_map = {
            'passenger_cars': 'cars',
            'two_wheelers': '2w',
            'three_wheelers': '3w'
        }

        # Initialize all expected variance columns with None
        # This ensures consistent CSV structure even when validation data is missing
        for short_name in vehicle_map.values():
            validation_results[f'{short_name}_oem_variance_pct'] = None
            validation_results[f'{short_name}_replacement_variance_pct'] = None

        if 'validation' not in self.real_data:
            print("⚠️  No validation data available - variance columns set to None")
            return validation_results

        validation_data = self.real_data['validation']

        for vehicle_key, short_name in vehicle_map.items():
            # Check OEM demand variance
            oem_key = f"{short_name}_oem"
            if oem_key in validation_data and self.region in validation_data[oem_key]:
                validation_series = validation_data[oem_key][self.region]

                # Get calculated OEM demand for this vehicle type
                calc_cols = [k for k in sli_by_type.keys() if vehicle_key in k and '_oem' in k]
                if calc_cols:
                    calculated_series = sum(
                        sli_by_type[col] for col in calc_cols
                    )

                    # Calculate variance for overlapping years
                    overlap_years = set(validation_series.index) & set(calculated_series.index)
                    if overlap_years:
                        variances = []
                        for year in overlap_years:
                            val_demand = validation_series[year]
                            calc_demand = calculated_series[year]
                            if val_demand > 0:
                                variance_pct = ((calc_demand - val_demand) / val_demand) * 100
                                variances.append(variance_pct)

                        if variances:
                            avg_variance = np.mean(variances)
                            validation_results[f'{short_name}_oem_variance_pct'] = avg_variance

            # Check replacement demand variance
            repl_key = f"{short_name}_replacement"
            if repl_key in validation_data and self.region in validation_data[repl_key]:
                validation_series = validation_data[repl_key][self.region]

                # Get calculated replacement demand for this vehicle type
                calc_cols = [k for k in sli_by_type.keys() if vehicle_key in k and '_replacement' in k]
                if calc_cols:
                    calculated_series = sum(
                        sli_by_type[col] for col in calc_cols
                    )

                    # Calculate variance for overlapping years
                    overlap_years = set(validation_series.index) & set(calculated_series.index)
                    if overlap_years:
                        variances = []
                        for year in overlap_years:
                            val_demand = validation_series[year]
                            calc_demand = calculated_series[year]
                            if val_demand > 0:
                                variance_pct = ((calc_demand - val_demand) / val_demand) * 100
                                variances.append(variance_pct)

                        if variances:
                            avg_variance = np.mean(variances)
                            validation_results[f'{short_name}_replacement_variance_pct'] = avg_variance

        return validation_results

    def validate_forecast(self):
        """Validate forecast against historical data"""
        print("\n=== Forecast Validation ===")

        # Check non-negativity
        has_negative = (self.results[['total_lead_demand_kt', 'battery_demand_kt', 'sli_demand_kt']] < 0).any().any()
        if has_negative:
            print("✗ FAIL: Negative demand values detected")
        else:
            print("✓ PASS: All demand values non-negative")

        # Check growth rate anomalies (YoY > 20%)
        print("\n--- Growth Rate Checks ---")
        key_columns = ['total_lead_demand_kt', 'sli_demand_kt', 'industrial_demand_kt']
        anomalies_found = False

        for col in key_columns:
            if col in self.results.columns:
                # Calculate YoY growth rates
                values = self.results[col].values
                for i in range(1, len(values)):
                    if values[i-1] > 0:
                        growth_rate = ((values[i] / values[i-1]) - 1) * 100
                        if abs(growth_rate) > 20:
                            year = self.years[i]
                            print(f"⚠️  WARNING: {col} YoY growth at year {year}: {growth_rate:+.1f}% (exceeds ±20% threshold)")
                            anomalies_found = True

        if not anomalies_found:
            print("✓ PASS: All YoY growth rates within ±20% threshold")

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

    def validate_stock_flow_consistency(self):
        """
        Validate stock-flow consistency for installed base evolution
        Checks that IB(t+1) = IB(t) + Adds(t) - Scrappage(t) holds
        """
        print("\n=== Stock-Flow Consistency Validation ===")

        if not hasattr(self, 'evolved_ib') or not self.evolved_ib:
            print("⚠️  No evolved IB data available for validation")
            return

        consistency_errors = []
        max_tolerance = 0.01  # 1% tolerance for numerical errors

        # Vehicle type mappings
        vehicle_types = {
            'cars': ['ICE', 'BEV', 'PHEV'],
            '2w': ['ICE', 'EV'],
            '3w': ['ICE', 'EV'],
            'cv': ['ICE', 'EV', 'NGV']
        }

        asset_lifetime_map = {
            'cars': self.asset_lifetimes.get('passenger_car_years', 18),
            '2w': self.asset_lifetimes.get('two_wheeler_years', 11),
            '3w': self.asset_lifetimes.get('three_wheeler_years', 9),
            'cv': self.asset_lifetimes.get('commercial_vehicle_years', 20)
        }

        # Check each vehicle type and powertrain
        for vehicle_abbr, powertrains in vehicle_types.items():
            asset_lifetime = asset_lifetime_map.get(vehicle_abbr, 15)

            for powertrain in powertrains:
                ib_key = f'{vehicle_abbr}_{powertrain}'

                if ib_key not in self.evolved_ib:
                    continue

                ib_series = self.evolved_ib[ib_key]

                # Get sales data
                if vehicle_abbr == 'cars':
                    sales_key = f'Passenger_Vehicle_({powertrain})_Annual_Sales_{self.region}'
                elif vehicle_abbr == '2w':
                    sales_key = f'Two_Wheeler_({powertrain})_Annual_Sales_{self.region}'
                elif vehicle_abbr == '3w':
                    sales_key = f'Three_Wheeler_({powertrain})_Annual_Sales_{self.region}'
                elif vehicle_abbr == 'cv':
                    sales_key = f'Commercial_Vehicle_({powertrain})_Annual_Sales_{self.region}'
                else:
                    continue

                if sales_key not in self.real_data:
                    continue

                sales_series = self.real_data[sales_key]

                # Validate stock-flow equation for each year
                for i, year in enumerate(self.years[:-1]):  # Skip last year (no t+1)
                    if year not in ib_series.index or (year + 1) not in ib_series.index:
                        continue

                    if year not in sales_series.index:
                        continue

                    # IB values
                    ib_t = ib_series[year]
                    ib_t1 = ib_series[year + 1]

                    # Adds (sales)
                    adds_t = sales_series[year]

                    # Scrappage
                    scrappage_t = ib_t / asset_lifetime

                    # Expected IB(t+1)
                    expected_ib_t1 = ib_t + adds_t - scrappage_t

                    # Check consistency
                    if expected_ib_t1 > 0:
                        relative_error = abs(ib_t1 - expected_ib_t1) / expected_ib_t1

                        if relative_error > max_tolerance:
                            consistency_errors.append({
                                'segment': f'{vehicle_abbr}_{powertrain}',
                                'year': year,
                                'ib_t': ib_t,
                                'adds_t': adds_t,
                                'scrappage_t': scrappage_t,
                                'expected_ib_t1': expected_ib_t1,
                                'actual_ib_t1': ib_t1,
                                'error_pct': relative_error * 100
                            })

        # Report results
        if consistency_errors:
            print(f"⚠️  WARNING: {len(consistency_errors)} stock-flow inconsistencies detected")
            print(f"\nShowing first 5 inconsistencies:")
            for error in consistency_errors[:5]:
                print(f"\n  Segment: {error['segment']}, Year: {error['year']}")
                print(f"    IB(t):          {error['ib_t']:.2f} million units")
                print(f"    Adds(t):        {error['adds_t']:.2f} million units")
                print(f"    Scrappage(t):   {error['scrappage_t']:.2f} million units")
                print(f"    Expected IB(t+1): {error['expected_ib_t1']:.2f} million units")
                print(f"    Actual IB(t+1):   {error['actual_ib_t1']:.2f} million units")
                print(f"    Error:          {error['error_pct']:.2f}%")
        else:
            print("✓ PASS: All stock-flow equations consistent within tolerance")

        return consistency_errors

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
        """Save forecast results in multiple formats (CSV, JSON, Parquet)"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Get output formats from config
        output_formats = self.config.get('output_formats', ['csv'])

        saved_files = []

        # Save CSV (default)
        if 'csv' in output_formats:
            csv_file = output_file.with_suffix('.csv')
            self.results.to_csv(csv_file, index=False)
            saved_files.append(csv_file)

        # Save JSON with nice formatting
        if 'json' in output_formats:
            json_file = output_file.with_suffix('.json')
            # Convert to records format for better readability
            self.results.to_json(json_file, orient='records', indent=2)
            saved_files.append(json_file)

        # Save Parquet for efficient storage
        if 'parquet' in output_formats:
            parquet_file = output_file.with_suffix('.parquet')
            try:
                self.results.to_parquet(parquet_file, index=False, engine='pyarrow')
                saved_files.append(parquet_file)
            except ImportError:
                print("⚠️  Parquet export requires pyarrow. Install with: pip install pyarrow")

        # Print saved files
        print(f"\n✓ Results saved:")
        for file in saved_files:
            print(f"  - {file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Lead Demand Forecasting')
    parser.add_argument('--region', type=str, default='Global',
                       help='Region to forecast')
    parser.add_argument('--scenario', type=str, default='baseline',
                       help='Scenario to use')
    parser.add_argument('--start-year', type=int, default=None,
                       help='Start year for forecast (overrides config default)')
    parser.add_argument('--end-year', type=int, default=None,
                       help='End year for forecast (overrides config default)')
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
    forecast = LeadDemandForecast(config_path, region=args.region, scenario=args.scenario,
                                   start_year=args.start_year, end_year=args.end_year)

    print("Loading data...")
    forecast.load_data()

    print("Running forecast...")
    forecast.forecast_demand()

    print("Validating forecast...")
    forecast.validate_forecast()

    print("\nValidating stock-flow consistency...")
    forecast.validate_stock_flow_consistency()

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
