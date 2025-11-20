#!/usr/bin/env python3
"""
Total Cost of Ownership (TCO) Analysis Module
Handles all TCO calculations for datacenter UPS batteries
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List


class TCOAnalyzer:
    """
    Calculates and analyzes Total Cost of Ownership for battery technologies
    """

    def __init__(self, config: Dict):
        """
        Initialize TCO analyzer with configuration

        Args:
            config: Configuration dictionary from config.json
        """
        self.config = config
        self.tco_horizon = config['default_parameters']['tco_horizon_years']
        self.discount_rate = config['default_parameters']['discount_rate']

        # Cost parameters
        self.vrla_params = config['cost_parameters']['vrla']
        self.lithium_params = config['cost_parameters']['lithium']

        # Lifespans
        self.vrla_lifespan = config['lifespans']['vrla_years']
        self.lithium_lifespan = config['lifespans']['lithium_years']

        # Cost forecasting parameters
        self.cost_forecast_params = config['cost_forecasting']

    def calculate_tco(self, capex_per_kwh: float, opex_per_kwh_year: float,
                     lifespan_years: int, discount_rate: Optional[float] = None) -> float:
        """
        Calculate Total Cost of Ownership per kWh

        Args:
            capex_per_kwh: Capital cost per kWh
            opex_per_kwh_year: Annual operating cost per kWh
            lifespan_years: Battery lifespan in years
            discount_rate: Optional override for discount rate

        Returns:
            TCO per kWh over the analysis horizon
        """
        if discount_rate is None:
            discount_rate = self.discount_rate

        # Initial capex
        tco = capex_per_kwh

        # Add discounted opex over horizon
        for year in range(1, self.tco_horizon + 1):
            discount_factor = (1 + discount_rate) ** year
            tco += opex_per_kwh_year / discount_factor

        # Add replacement costs if needed
        if self.tco_horizon > lifespan_years:
            num_replacements = self.tco_horizon // lifespan_years
            for replacement in range(1, num_replacements + 1):
                replacement_year = lifespan_years * replacement
                if replacement_year < self.tco_horizon:
                    discount_factor = (1 + discount_rate) ** replacement_year
                    tco += capex_per_kwh / discount_factor

        return tco

    def forecast_vrla_costs(self, years: List[int], region: str = 'Global',
                          scenario: Optional[Dict] = None) -> pd.Series:
        """
        Forecast VRLA capital costs

        Args:
            years: List of years to forecast
            region: Geographic region for regional multipliers
            scenario: Optional scenario parameters

        Returns:
            Series of VRLA costs by year
        """
        # Base VRLA cost
        vrla_capex = self.vrla_params['capex_per_kwh']

        # Apply regional multiplier
        regional_multiplier = self.vrla_params['regional_multipliers'].get(region, 1.0)
        vrla_capex_regional = vrla_capex * regional_multiplier

        # Apply scenario cost change if applicable
        vrla_cost_change = 0.0
        if scenario:
            vrla_cost_change = scenario.get('vrla_cost_change', 0.0)

        # Generate cost trajectory
        vrla_costs = []
        for i, year in enumerate(years):
            if self.vrla_params['capex_trajectory'] == 'flat':
                # Flat or slightly changing trajectory
                annual_change = 1 + vrla_cost_change
                cost = vrla_capex_regional * (annual_change ** i)
            else:
                # Could implement declining trajectory if needed
                cost = vrla_capex_regional

            vrla_costs.append(cost)

        return pd.Series(vrla_costs, index=years)

    def forecast_lithium_costs(self, years: List[int], historical_costs: Optional[pd.Series] = None,
                             region: str = 'Global', scenario: Optional[Dict] = None) -> pd.Series:
        """
        Forecast Li-ion capital costs using log-CAGR method

        Args:
            years: List of years to forecast
            historical_costs: Historical BESS cost data (optional)
            region: Geographic region
            scenario: Optional scenario parameters

        Returns:
            Series of Li-ion costs by year
        """
        lithium_costs = []

        if historical_costs is not None and not historical_costs.empty:
            # Use log-CAGR method for projection
            hist_years = historical_costs.index.values
            hist_costs = historical_costs.values

            # Calculate historical CAGR in log space
            if len(hist_years) >= 2:
                log_costs = np.log(hist_costs)
                # Linear fit in log space
                coeffs = np.polyfit(hist_years, log_costs, 1)
                slope = coeffs[0]  # This is the log-CAGR

                # Apply scenario cost decline rate if specified
                if scenario:
                    scenario_decline = -scenario.get('lithium_cost_decline_rate', 0.08)
                    adjusted_slope = min(slope, scenario_decline)  # Ensure costs decline
                else:
                    adjusted_slope = slope

                # Cap annual decline
                max_decline = -self.cost_forecast_params['cap_annual_decline']
                adjusted_slope = max(adjusted_slope, max_decline)

                # Project forward
                last_year = hist_years[-1]
                last_cost = hist_costs[-1]

                for year in years:
                    if year <= last_year and year in historical_costs.index:
                        # Use historical data
                        lithium_costs.append(historical_costs[year])
                    else:
                        # Project using log-linear trend
                        years_ahead = year - last_year
                        projected_log_cost = np.log(last_cost) + (adjusted_slope * years_ahead)
                        projected_cost = np.exp(projected_log_cost)

                        # Apply floor
                        floor = last_cost * self.cost_forecast_params['floor_cost_ratio']
                        projected_cost = max(projected_cost, floor)

                        # Cap at historical maximum to prevent cost increases
                        projected_cost = min(projected_cost, last_cost)

                        lithium_costs.append(projected_cost)
            else:
                # Fallback: use constant decline rate
                base_cost = hist_costs[0] if len(hist_costs) > 0 else 200.0
                decline_rate = 0.08
                if scenario:
                    decline_rate = scenario.get('lithium_cost_decline_rate', 0.08)

                for i in range(len(years)):
                    cost = base_cost * ((1 - decline_rate) ** i)
                    floor = base_cost * self.cost_forecast_params['floor_cost_ratio']
                    lithium_costs.append(max(cost, floor))
        else:
            # No historical data - use scenario decline from base
            base_cost = 200.0  # Default starting cost
            decline_rate = 0.08
            if scenario:
                decline_rate = scenario.get('lithium_cost_decline_rate', 0.08)

            for i in range(len(years)):
                cost = base_cost * ((1 - decline_rate) ** i)
                lithium_costs.append(cost)

        # Apply UPS reliability premium to Li-ion costs
        premium = self.lithium_params['ups_reliability_premium']
        lithium_costs = [c * premium for c in lithium_costs]

        return pd.Series(lithium_costs, index=years)

    def calculate_tco_trajectories(self, years: List[int], vrla_costs: pd.Series,
                                  lithium_costs: pd.Series) -> Dict[str, pd.Series]:
        """
        Calculate TCO trajectories for both technologies

        Args:
            years: List of years
            vrla_costs: VRLA capital costs by year
            lithium_costs: Li-ion capital costs by year

        Returns:
            Dictionary with TCO trajectories and metrics
        """
        # Get OpEx parameters
        vrla_opex = self.vrla_params['opex_per_kwh_year']
        lithium_opex = self.lithium_params['opex_per_kwh_year']

        # Calculate TCO for each year
        vrla_tco = pd.Series(
            [self.calculate_tco(vrla_costs[year], vrla_opex, self.vrla_lifespan) for year in years],
            index=years
        )

        lithium_tco = pd.Series(
            [self.calculate_tco(lithium_costs[year], lithium_opex, self.lithium_lifespan) for year in years],
            index=years
        )

        # Calculate TCO advantage (positive = Li-ion favorable)
        tco_advantage = vrla_tco - lithium_tco

        return {
            'vrla_tco': vrla_tco,
            'lithium_tco': lithium_tco,
            'tco_advantage': tco_advantage,
            'vrla_capex': vrla_costs,
            'lithium_capex': lithium_costs,
            'vrla_opex': vrla_opex,
            'lithium_opex': lithium_opex
        }

    def find_tipping_point(self, tco_trajectories: Dict[str, pd.Series],
                         persistence_years: Optional[int] = None) -> Optional[int]:
        """
        Find the tipping point year when Li-ion becomes sustainably cheaper

        Args:
            tco_trajectories: Dictionary with TCO data from calculate_tco_trajectories
            persistence_years: Years of sustained advantage required

        Returns:
            Tipping point year or None
        """
        if persistence_years is None:
            persistence_years = self.config['default_parameters'].get('tipping_persistence_years', 3)

        tco_advantage = tco_trajectories['tco_advantage']
        years = tco_advantage.index.tolist()

        for i, year in enumerate(years[:-persistence_years+1]):
            # Check if advantage is positive for persistence_years consecutive years
            window = tco_advantage[year:years[i+persistence_years-1]]
            if all(window > 0):
                return year

        return None

    def tco_breakdown(self, capex: float, opex: float, lifespan: int,
                     discount_rate: Optional[float] = None) -> Dict:
        """
        Generate detailed TCO breakdown

        Args:
            capex: Capital cost per kWh
            opex: Annual operating cost per kWh
            lifespan: Battery lifespan in years
            discount_rate: Optional override for discount rate

        Returns:
            Detailed breakdown of TCO components
        """
        if discount_rate is None:
            discount_rate = self.discount_rate

        breakdown = {
            'initial_capex': capex,
            'npv_opex': 0,
            'npv_replacements': 0,
            'replacements': [],
            'annual_opex': []
        }

        # Calculate NPV of OpEx
        for year in range(1, self.tco_horizon + 1):
            discount_factor = (1 + discount_rate) ** year
            annual_npv = opex / discount_factor
            breakdown['npv_opex'] += annual_npv
            breakdown['annual_opex'].append({
                'year': year,
                'nominal': opex,
                'npv': annual_npv
            })

        # Calculate replacement costs
        num_replacements = self.tco_horizon // lifespan
        for replacement in range(1, num_replacements + 1):
            replacement_year = lifespan * replacement
            if replacement_year < self.tco_horizon:
                discount_factor = (1 + discount_rate) ** replacement_year
                replacement_npv = capex / discount_factor
                breakdown['npv_replacements'] += replacement_npv
                breakdown['replacements'].append({
                    'year': replacement_year,
                    'nominal_cost': capex,
                    'npv': replacement_npv
                })

        breakdown['total_tco'] = (breakdown['initial_capex'] +
                                 breakdown['npv_opex'] +
                                 breakdown['npv_replacements'])

        return breakdown

    def sensitivity_analysis(self, base_params: Dict, sensitivity_params: Dict,
                           years: List[int]) -> pd.DataFrame:
        """
        Perform TCO sensitivity analysis

        Args:
            base_params: Base case parameters
            sensitivity_params: Parameters to vary with their ranges
            years: Years to analyze

        Returns:
            DataFrame with sensitivity results
        """
        results = []

        for param_name, param_values in sensitivity_params.items():
            for value in param_values:
                # Create modified parameters
                modified_params = base_params.copy()
                modified_params[param_name] = value

                # Calculate TCO with modified parameters
                if param_name in ['vrla_capex', 'vrla_opex', 'vrla_lifespan']:
                    vrla_tco = self.calculate_tco(
                        modified_params.get('vrla_capex', base_params['vrla_capex']),
                        modified_params.get('vrla_opex', base_params['vrla_opex']),
                        modified_params.get('vrla_lifespan', base_params['vrla_lifespan'])
                    )
                    lithium_tco = self.calculate_tco(
                        base_params['lithium_capex'],
                        base_params['lithium_opex'],
                        base_params['lithium_lifespan']
                    )
                else:
                    vrla_tco = self.calculate_tco(
                        base_params['vrla_capex'],
                        base_params['vrla_opex'],
                        base_params['vrla_lifespan']
                    )
                    lithium_tco = self.calculate_tco(
                        modified_params.get('lithium_capex', base_params['lithium_capex']),
                        modified_params.get('lithium_opex', base_params['lithium_opex']),
                        modified_params.get('lithium_lifespan', base_params['lithium_lifespan'])
                    )

                tco_advantage = vrla_tco - lithium_tco

                results.append({
                    'parameter': param_name,
                    'value': value,
                    'vrla_tco': vrla_tco,
                    'lithium_tco': lithium_tco,
                    'tco_advantage': tco_advantage,
                    'lithium_favorable': tco_advantage > 0
                })

        return pd.DataFrame(results)

    def calculate_levelized_cost(self, capex: float, opex: float, lifespan: int,
                                cycles_per_year: int = 250, efficiency: float = 0.88) -> float:
        """
        Calculate levelized cost of storage (LCOS)

        Args:
            capex: Capital cost per kWh
            opex: Annual operating cost per kWh
            lifespan: Battery lifespan in years
            cycles_per_year: Annual discharge cycles
            efficiency: Round-trip efficiency

        Returns:
            Levelized cost per kWh cycled
        """
        # Total energy throughput over lifespan
        total_throughput = cycles_per_year * lifespan * efficiency

        # Total cost (simplified - ignoring time value of money for LCOS)
        total_cost = capex + (opex * lifespan)

        # Levelized cost
        lcos = total_cost / total_throughput if total_throughput > 0 else float('inf')

        return lcos