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
        self.carbon_pricing = self.config.get('carbon_pricing', {'enabled': False})
        self.swb_generation_mix = self.config['swb_generation_mix']
        self.integration_costs = self.config.get('integration_costs', {'enabled': False})

        # Load scenario-specific reserve floors
        reserve_floors_config = self.config['reserve_floors']
        if scenario in reserve_floors_config:
            self.reserve_floors = reserve_floors_config[scenario]
        else:
            # Fallback to baseline if scenario not found
            self.reserve_floors = reserve_floors_config.get('baseline', {
                'coal_minimum_share': 0.10,
                'gas_minimum_share': 0.15
            })

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

    def get_regional_fossil_lcoe_defaults(self, technology):
        """
        Get reasonable default LCOE values for fossil fuels by region
        Based on industry data and regional characteristics

        Args:
            technology: 'coal' or 'gas'

        Returns:
            dict with 'base_2020' ($/MWh) and 'annual_change_rate'
        """
        # Regional defaults based on fuel costs, plant efficiency, carbon regulations
        defaults = {
            'coal': {
                'China': {'base_2020': 65, 'annual_change': 0.015},  # Lower coal costs, older fleet
                'USA': {'base_2020': 75, 'annual_change': 0.020},    # Aging plants, rising costs
                'Europe': {'base_2020': 85, 'annual_change': 0.025}, # High carbon costs, retiring
                'Rest_of_World': {'base_2020': 70, 'annual_change': 0.015},
                'Global': {'base_2020': 70, 'annual_change': 0.018}
            },
            'gas': {
                'China': {'base_2020': 90, 'annual_change': 0.010},  # Imported LNG, high cost
                'USA': {'base_2020': 60, 'annual_change': 0.012},    # Abundant domestic gas
                'Europe': {'base_2020': 110, 'annual_change': 0.015},# Import dependence, high costs
                'Rest_of_World': {'base_2020': 80, 'annual_change': 0.012},
                'Global': {'base_2020': 80, 'annual_change': 0.012}
            }
        }

        if technology in defaults and self.region in defaults[technology]:
            return defaults[technology][self.region]
        elif technology in defaults and 'Global' in defaults[technology]:
            return defaults[technology]['Global']
        else:
            # Ultimate fallback
            return {'base_2020': 80, 'annual_change': 0.015}

    def forecast_fossil_lcoe_from_defaults(self, technology):
        """
        Forecast fossil fuel LCOE using regional defaults

        Args:
            technology: 'coal' or 'gas'

        Returns:
            pd.Series with forecasted LCOE
        """
        defaults = self.get_regional_fossil_lcoe_defaults(technology)
        base_2020 = defaults['base_2020']
        annual_change = defaults['annual_change']

        # Override with scenario-specific change rate if available
        change_key = f"{technology}_cost_change"
        if change_key in self.scenario:
            annual_change = self.scenario[change_key]

        forecasted = pd.Series(index=self.years, dtype=float)

        for year in self.years:
            years_from_2020 = year - 2020
            # Compound growth from 2020 baseline
            forecasted[year] = base_2020 * ((1 + annual_change) ** years_from_2020)

        return forecasted

    def calculate_carbon_price_trajectory(self):
        """
        Calculate carbon price trajectory over forecast period

        Returns:
            pd.Series with carbon price ($/ton CO2) by year
        """
        if not self.carbon_pricing.get('enabled', False):
            return pd.Series(0, index=self.years)

        # Get regional base price (2020)
        regional_prices = self.carbon_pricing.get('regional_base_prices_2020', {})
        base_price_2020 = regional_prices.get(self.region,
                                              regional_prices.get('Global', 10))

        # Get growth rate
        base_growth_rate = self.carbon_pricing.get('base_annual_growth_rate', 0.05)

        # Apply scenario multiplier
        scenario_multipliers = self.carbon_pricing.get('scenario_multipliers', {})
        scenario_multiplier = scenario_multipliers.get(self.scenario_name, 1.0)

        effective_growth_rate = base_growth_rate * scenario_multiplier

        # Get price limits
        price_floor = self.carbon_pricing.get('price_floor_per_ton', 0)
        price_ceiling = self.carbon_pricing.get('price_ceiling_per_ton', 300)

        # Calculate trajectory
        carbon_price = pd.Series(index=self.years, dtype=float)

        for year in self.years:
            years_from_2020 = year - 2020
            price = base_price_2020 * ((1 + effective_growth_rate) ** years_from_2020)

            # Apply bounds
            price = max(price, price_floor)
            price = min(price, price_ceiling)

            carbon_price[year] = price

        return carbon_price

    def add_carbon_price_to_lcoe(self, lcoe, technology, carbon_price):
        """
        Add carbon pricing to fossil fuel LCOE

        Formula: LCOE_with_carbon = LCOE_base + (Carbon_Price × Emission_Factor / 1000)
        Where emission factor is in kg/MWh, carbon price in $/ton, result in $/MWh

        Args:
            lcoe: Base LCOE series ($/MWh)
            technology: 'coal' or 'gas'
            carbon_price: Carbon price series ($/ton CO2)

        Returns:
            pd.Series with LCOE including carbon price
        """
        # Get emission factor (kg CO2 per MWh)
        emission_factor_key = f"{technology}_kg_co2_per_mwh"
        emission_factor = self.emission_factors.get(emission_factor_key, 0)

        # Convert: ($/ton CO2) × (kg CO2/MWh) × (1 ton / 1000 kg) = $/MWh
        carbon_cost_per_mwh = carbon_price * emission_factor / 1000

        return lcoe + carbon_cost_per_mwh

    def forecast_all_lcoe(self):
        """Forecast LCOE for all technologies, including carbon pricing for fossils"""
        lcoe_data = self.data['lcoe']

        forecasts = {}

        # Renewable technologies
        for tech in ['solar', 'onshore_wind', 'offshore_wind']:
            if self.region in lcoe_data[tech] and len(lcoe_data[tech][self.region]) > 0:
                forecasts[tech] = self.forecast_lcoe(
                    lcoe_data[tech][self.region],
                    tech
                )
            else:
                # Use Global as proxy
                if 'Global' in lcoe_data[tech] and len(lcoe_data[tech]['Global']) > 0:
                    print(f"ℹ️  Using Global {tech} LCOE data for {self.region}")
                    forecasts[tech] = self.forecast_lcoe(
                        lcoe_data[tech]['Global'],
                        tech
                    )
                else:
                    print(f"⚠️  WARNING: No {tech} LCOE data found, using zero")
                    forecasts[tech] = pd.Series(0, index=self.years)

        # Calculate carbon price trajectory
        carbon_price = self.calculate_carbon_price_trajectory()

        if self.carbon_pricing.get('enabled', False):
            print(f"ℹ️  Carbon pricing enabled: ${carbon_price[2020]:.1f}/ton (2020) → "
                  f"${carbon_price[self.end_year]:.1f}/ton ({self.end_year})")

        # Fossil fuel technologies
        for tech in ['coal', 'gas']:
            if self.region in lcoe_data[tech] and len(lcoe_data[tech][self.region]) > 0:
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
                # Try Global data
                if 'Global' in lcoe_data[tech] and len(lcoe_data[tech]['Global']) > 0:
                    print(f"ℹ️  Using Global {tech} LCOE data for {self.region}")
                    hist_data = lcoe_data[tech]['Global']
                    forecasts[tech] = self.forecast_lcoe(hist_data, tech)
                else:
                    # Use regional defaults based on known industry costs
                    print(f"⚠️  WARNING: No {tech} LCOE data found in files")
                    defaults = self.get_regional_fossil_lcoe_defaults(tech)
                    print(f"   Using regional default: {defaults['base_2020']} $/MWh (2020) "
                          f"with {defaults['annual_change']*100:.1f}% annual change")
                    forecasts[tech] = self.forecast_fossil_lcoe_from_defaults(tech)

            # Add carbon pricing to fossil fuel LCOE
            forecasts[tech] = self.add_carbon_price_to_lcoe(forecasts[tech], tech, carbon_price)

        return forecasts

    def get_regional_baseline_generation(self, technology, year=2020):
        """
        Get reasonable baseline generation estimates by region and technology
        Based on known 2020 data

        Args:
            technology: 'nuclear', 'hydro', 'geothermal', 'biomass', 'other'
            year: Base year for estimates (default 2020)

        Returns:
            Generation in TWh
        """
        # Based on IEA and other sources for 2020 data
        baselines = {
            'nuclear': {
                'China': 370,
                'USA': 840,
                'Europe': 780,
                'Rest_of_World': 720,
                'Global': 2700
            },
            'hydro': {
                'China': 1360,
                'USA': 290,
                'Europe': 380,
                'Rest_of_World': 2270,
                'Global': 4300
            },
            'geothermal': {
                'China': 0.2,
                'USA': 17,
                'Europe': 7,
                'Rest_of_World': 60,
                'Global': 94
            },
            'biomass': {
                'China': 130,
                'USA': 60,
                'Europe': 180,
                'Rest_of_World': 300,
                'Global': 670
            }
        }

        if technology in baselines and self.region in baselines[technology]:
            return baselines[technology][self.region]
        elif technology in baselines and 'Global' in baselines[technology]:
            # Scale Global down proportionally if specific region not available
            return baselines[technology]['Global'] * 0.2  # Conservative estimate
        else:
            return 0

    def calculate_baseline_trajectory(self):
        """
        Calculate generation trajectory for non-SWB, non-fossil technologies
        Nuclear: slight decline or flat (aging plants, few new builds)
        Hydro: stable (capacity-constrained, limited sites)
        Others: slight growth
        """
        generation_data = self.data['generation']
        baseline = {
            'nuclear': pd.Series(index=self.years, dtype=float),
            'hydro': pd.Series(index=self.years, dtype=float),
            'geothermal': pd.Series(index=self.years, dtype=float),
            'biomass': pd.Series(index=self.years, dtype=float),
            'other': pd.Series(index=self.years, dtype=float)
        }

        # Growth rates by technology
        growth_rates = {
            'nuclear': -0.01,  # Slight decline: plant retirements exceed new builds
            'hydro': 0.005,    # Very slow growth: limited sites available
            'geothermal': 0.03, # Modest growth
            'biomass': 0.02,   # Slight growth
            'other': 0.02      # Slight growth
        }

        for tech in ['nuclear', 'hydro', 'geothermal', 'biomass']:
            # Try to load historical data
            if tech in generation_data and self.region in generation_data[tech]:
                hist = generation_data[tech][self.region]
                if len(hist) > 0:
                    # Use historical data as base
                    base_year = hist.index.max()
                    base_value = hist[base_year]
                else:
                    # Use defaults
                    base_year = 2020
                    base_value = self.get_regional_baseline_generation(tech, 2020)
            else:
                # Use defaults
                base_year = 2020
                base_value = self.get_regional_baseline_generation(tech, 2020)

            # Forecast forward from base
            growth_rate = growth_rates[tech]
            for year in self.years:
                if year <= base_year and tech in generation_data and self.region in generation_data[tech]:
                    # Use historical if available
                    hist = generation_data[tech][self.region]
                    if year in hist.index:
                        baseline[tech][year] = hist[year]
                    else:
                        years_from_base = year - base_year
                        baseline[tech][year] = base_value * ((1 + growth_rate) ** years_from_base)
                else:
                    years_from_base = year - base_year
                    baseline[tech][year] = base_value * ((1 + growth_rate) ** years_from_base)

        # Aggregate 'other' renewables
        baseline['other'] = baseline['geothermal'] + baseline['biomass']

        return baseline

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

            # SCOE = capex ($/kWh) / (cycles_per_year × lifetime_years × efficiency) × 1000
            # Factor of 1000 converts $/kWh to $/MWh
            scoe[year] = (capex / (cycles_per_year * lifetime_years * efficiency)) * 1000

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

    def calculate_integration_cost(self, swb_share):
        """
        Calculate grid integration costs for variable renewables

        Integration costs increase non-linearly with SWB penetration due to:
        - Grid reinforcement and balancing requirements
        - Curtailment and storage needs
        - Transmission and distribution upgrades

        Formula: integration_cost = base_cost × regional_multiplier × (swb_share ^ exponent)
        Capped at max_additional_cost_per_mwh

        Args:
            swb_share: SWB share of total generation (0-1)

        Returns:
            Integration cost ($/MWh)
        """
        if not self.integration_costs.get('enabled', False):
            return 0

        base_cost = self.integration_costs['base_cost_per_mwh']
        exponent = self.integration_costs['penetration_exponent']
        max_cost = self.integration_costs['max_additional_cost_per_mwh']

        # Get regional multiplier
        regional_multipliers = self.integration_costs['regional_multipliers']
        regional_multiplier = regional_multipliers.get(self.region, 1.0)

        # Calculate integration cost
        # Cost increases non-linearly with penetration
        integration_cost = base_cost * regional_multiplier * (swb_share ** exponent)

        # Cap at maximum
        integration_cost = min(integration_cost, max_cost)

        return integration_cost

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
        Now accounts for baseline technologies (nuclear, hydro, etc.)
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

        # Calculate baseline technology trajectories
        baseline = self.calculate_baseline_trajectory()

        # Build generation forecast
        results = {
            'solar': pd.Series(index=self.years, dtype=float),
            'wind': pd.Series(index=self.years, dtype=float),
            'coal': pd.Series(index=self.years, dtype=float),
            'gas': pd.Series(index=self.years, dtype=float),
            'nuclear': pd.Series(index=self.years, dtype=float),
            'hydro': pd.Series(index=self.years, dtype=float),
            'geothermal': pd.Series(index=self.years, dtype=float),
            'biomass': pd.Series(index=self.years, dtype=float),
            'total_demand': pd.Series(index=self.years, dtype=float),
            'residual_demand': pd.Series(index=self.years, dtype=float)
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

            # Add baseline technology generation
            for tech in ['nuclear', 'hydro', 'geothermal', 'biomass']:
                if year in baseline[tech].index:
                    results[tech][year] = baseline[tech][year]
                else:
                    results[tech][year] = 0

            # Calculate residual demand (total - baseline)
            baseline_total = sum(results[tech][year] for tech in ['nuclear', 'hydro', 'geothermal', 'biomass'])
            residual_demand = demand - baseline_total
            results['residual_demand'][year] = residual_demand

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

                # Fossil fills the rest of residual demand (after baseline and SWB)
                swb_total = results['solar'][year] + results['wind'][year]
                fossil_needed = residual_demand - swb_total

                if displacement_order == 'coal_first':
                    coal_share = 0.55
                    gas_share = 0.45
                else:
                    coal_share = 0.45
                    gas_share = 0.55

                results['coal'][year] = fossil_needed * coal_share
                results['gas'][year] = fossil_needed * gas_share

            else:
                # Post-tipping: rapid renewable growth (competing for residual demand)
                years_since_tipping = year - min(t for t in [tipping_vs_coal, tipping_vs_gas] if t is not None)

                # S-curve adoption
                # SWB share = 1 / (1 + exp(-k * (t - t0)))
                k = 0.3 * displacement_speed  # Steepness
                t0 = 10  # Midpoint at 10 years
                swb_share = 1 / (1 + np.exp(-k * (years_since_tipping - t0)))

                # Reserve floors for reliability (scenario-specific)
                coal_floor = self.reserve_floors['coal_minimum_share']
                gas_floor = self.reserve_floors['gas_minimum_share']

                # Maximum SWB can reach (of residual demand)
                max_swb_share = 1 - coal_floor - gas_floor
                swb_share = min(swb_share, max_swb_share)

                swb_generation = residual_demand * swb_share

                # Split SWB between solar and wind using configurable mix
                solar_share = self.swb_generation_mix['solar_share']
                onshore_wind_share = self.swb_generation_mix['onshore_wind_share']
                offshore_wind_share = self.swb_generation_mix['offshore_wind_share']

                results['solar'][year] = swb_generation * solar_share
                # Wind is split between onshore and offshore
                total_wind = swb_generation * (onshore_wind_share + offshore_wind_share)
                results['wind'][year] = total_wind

                # Remaining residual for fossils
                fossil_needed = residual_demand * (1 - swb_share)

                if displacement_order == 'coal_first':
                    # Displace coal first, then gas
                    coal_max_share = coal_floor
                    gas_gets_rest = True
                    results['coal'][year] = residual_demand * coal_max_share
                    results['gas'][year] = fossil_needed - results['coal'][year]
                else:
                    # Displace gas first, then coal
                    gas_max_share = gas_floor
                    coal_gets_rest = True
                    results['gas'][year] = residual_demand * gas_max_share
                    results['coal'][year] = fossil_needed - results['gas'][year]

        return results

    def get_capacity_factor(self, technology, year):
        """
        Get capacity factor for a technology with temporal evolution

        Args:
            technology: Technology name ('solar', 'onshore_wind', 'offshore_wind', 'coal', 'gas')
            year: Year to calculate capacity factor for

        Returns:
            Capacity factor (0-1)
        """
        cf_config = self.capacity_factors.get(technology, {})

        if 'base' in cf_config:
            # Renewable technologies with improvement over time
            base_cf = cf_config['base']
            improvement_rate = cf_config.get('improvement_per_year', 0)
            max_cf = cf_config.get('max', base_cf)

            # Calculate improvement from base year (2020)
            years_since_base = year - 2020
            improved_cf = base_cf + (improvement_rate * years_since_base)

            # Cap at maximum
            return min(improved_cf, max_cf)
        elif 'typical' in cf_config:
            # Fossil technologies with regional variation
            return cf_config['typical']
        else:
            # Fallback defaults
            defaults = {
                'solar': 0.20,
                'onshore_wind': 0.30,
                'offshore_wind': 0.40,
                'coal': 0.60,
                'gas': 0.40,
                'nuclear': 0.85,
                'hydro': 0.45,
                'geothermal': 0.75,
                'biomass': 0.70
            }
            return defaults.get(technology, 0.30)

    def calculate_capacity(self, generation):
        """
        Calculate installed capacity (GW) from generation (TWh) using capacity factors

        Formula: Capacity (GW) = Generation (TWh) / (Capacity Factor × 8760 hours/year)

        Args:
            generation: Dict of technology: pd.Series(generation_twh)

        Returns:
            Dict of technology: pd.Series(capacity_gw)
        """
        capacity = {}

        # Map generation tech names to capacity factor names
        tech_mapping = {
            'solar': 'solar',
            'wind': 'onshore_wind',  # Assume wind is mostly onshore
            'coal': 'coal',
            'gas': 'gas',
            'nuclear': 'nuclear',
            'hydro': 'hydro',
            'geothermal': 'geothermal',
            'biomass': 'biomass'
        }

        for gen_tech, cf_tech in tech_mapping.items():
            if gen_tech not in generation:
                continue

            gen_series = generation[gen_tech]
            cap_series = pd.Series(index=gen_series.index, dtype=float)

            for year in gen_series.index:
                cf = self.get_capacity_factor(cf_tech, year)
                gen_twh = gen_series[year]

                # Capacity (GW) = Generation (TWh) / (CF × 8760 h/year) × 1e6 GWh/TWh / 1000 GWh/GW
                # Simplifies to: GW = TWh × 1000 / (CF × 8760)
                cap_series[year] = gen_twh * 1000 / (cf * 8760)

            capacity[gen_tech] = cap_series

        # Split wind into onshore/offshore (80% onshore, 20% offshore)
        if 'wind' in capacity:
            capacity['onshore_wind'] = capacity['wind'] * 0.80
            capacity['offshore_wind'] = capacity['wind'] * 0.20

        return capacity

    def calculate_battery_capacity(self, generation):
        """
        Calculate required battery storage capacity (GWh) for SWB system

        Formula: Battery Capacity (GWh) = Daily SWB Generation × Resilience Days

        Where:
        - Daily SWB Generation = Annual SWB Generation (TWh) / 365 days × 1000 GWh/TWh
        - Resilience Days = days of storage needed for grid stability

        Args:
            generation: Dict with 'solar' and 'wind' Series (TWh)

        Returns:
            pd.Series of battery capacity (GWh) by year
        """
        resilience_days = self.battery_sizing['resilience_days']

        # Calculate SWB generation (solar + wind)
        swb_generation = generation['solar'] + generation['wind']  # TWh

        # Calculate battery capacity
        # Daily generation (GWh/day) = Annual (TWh) / 365 days × 1000 GWh/TWh
        # Battery capacity (GWh) = Daily generation × resilience_days
        battery_capacity = swb_generation / 365 * 1000 * resilience_days

        return battery_capacity

    def calculate_emissions(self, generation):
        """
        Calculate CO2 emissions from generation mix

        Formula: emissions_mt = generation_twh * emission_factor_kg_per_mwh / 1000
        Explanation:
        - TWh × 1e6 MWh/TWh = MWh
        - MWh × kg/MWh = kg
        - kg / 1e9 kg/Mt = Mt
        - Simplifies to: TWh × kg/MWh / 1000
        """
        emissions = {}

        # Convert TWh to MWh, multiply by kg/MWh, divide by 1000 to get Mt
        for tech, emission_factor_key in [
            ('coal', 'coal_kg_co2_per_mwh'),
            ('gas', 'gas_kg_co2_per_mwh'),
            ('solar', 'solar_kg_co2_per_mwh'),
            ('wind', 'wind_kg_co2_per_mwh'),
            ('nuclear', 'nuclear_kg_co2_per_mwh'),
            ('hydro', 'hydro_kg_co2_per_mwh'),
            ('geothermal', 'geothermal_kg_co2_per_mwh'),
            ('biomass', 'biomass_kg_co2_per_mwh')
        ]:
            if tech in generation:
                gen_twh = generation[tech]
                emission_factor = self.emission_factors[emission_factor_key]
                # TWh × 1e6 MWh/TWh × kg/MWh / 1e9 kg/Mt = TWh × kg/MWh / 1000
                emissions[tech] = gen_twh * emission_factor / 1000  # Mt

        # Calculate SWB emissions (solar + wind)
        emissions['swb'] = emissions.get('solar', 0) + emissions.get('wind', 0)

        # Calculate fossil emissions
        emissions['fossil'] = emissions.get('coal', 0) + emissions.get('gas', 0)

        # Calculate baseline emissions (nuclear + hydro + geothermal + biomass)
        emissions['baseline'] = (emissions.get('nuclear', 0) +
                                 emissions.get('hydro', 0) +
                                 emissions.get('geothermal', 0) +
                                 emissions.get('biomass', 0))

        # Total emissions (all sources)
        emissions['total'] = emissions['fossil'] + emissions['swb'] + emissions['baseline']

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

        print("Calculating installed capacity...")
        capacity = self.calculate_capacity(generation)

        print("Calculating battery storage capacity...")
        battery_capacity = self.calculate_battery_capacity(generation)

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
        self.results['nuclear_generation_twh'] = generation['nuclear'].values
        self.results['hydro_generation_twh'] = generation['hydro'].values
        self.results['geothermal_generation_twh'] = generation['geothermal'].values
        self.results['biomass_generation_twh'] = generation['biomass'].values
        self.results['total_generation_twh'] = generation['total_demand'].values

        swb_gen = generation['solar'] + generation['wind']
        baseline_gen = (generation['nuclear'] + generation['hydro'] +
                       generation['geothermal'] + generation['biomass'])
        self.results['swb_generation_twh'] = swb_gen.values
        self.results['baseline_generation_twh'] = baseline_gen.values
        swb_share_series = swb_gen / generation['total_demand']
        self.results['swb_share_pct'] = (swb_share_series * 100).values

        # Calculate integration costs based on SWB penetration
        print("Calculating integration costs...")
        integration_costs_series = pd.Series(index=self.years, dtype=float)
        for year in self.years:
            swb_share = swb_share_series[year]
            integration_costs_series[year] = self.calculate_integration_cost(swb_share)

        self.results['integration_cost_per_mwh'] = integration_costs_series.values

        # Total SWB system cost including integration
        swb_total_system_cost = swb_stack_cost + integration_costs_series
        self.results['swb_total_system_cost_per_mwh'] = swb_total_system_cost.values

        # Capacity (GW)
        self.results['solar_capacity_gw'] = capacity['solar'].values
        if 'onshore_wind' in capacity:
            self.results['onshore_wind_capacity_gw'] = capacity['onshore_wind'].values
            self.results['offshore_wind_capacity_gw'] = capacity['offshore_wind'].values
        self.results['coal_capacity_gw'] = capacity['coal'].values
        self.results['gas_capacity_gw'] = capacity['gas'].values

        # Battery storage capacity (GWh)
        self.results['battery_capacity_gwh'] = battery_capacity.values

        # Total capacity
        total_capacity = (capacity['solar'] +
                         capacity.get('onshore_wind', 0) +
                         capacity.get('offshore_wind', 0) +
                         capacity['coal'] +
                         capacity['gas'])
        self.results['total_capacity_gw'] = total_capacity.values

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
        self.results['nuclear_co2_emissions_mt'] = emissions['nuclear'].values
        self.results['hydro_co2_emissions_mt'] = emissions['hydro'].values
        self.results['geothermal_co2_emissions_mt'] = emissions['geothermal'].values
        self.results['biomass_co2_emissions_mt'] = emissions['biomass'].values
        self.results['baseline_co2_emissions_mt'] = emissions['baseline'].values
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
