#!/usr/bin/env python3
"""
Technology Adoption Model Module
Handles S-curve adoption modeling for battery technology transition
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple, Optional


class AdoptionModel:
    """
    Models technology adoption using S-curve (logistic) functions
    """

    def __init__(self, config: Dict):
        """
        Initialize adoption model with configuration

        Args:
            config: Configuration dictionary from config.json
        """
        self.config = config
        self.s_curve_params = config['s_curve_parameters']

        # Default parameters
        self.ceiling_L = self.s_curve_params['ceiling_L']
        self.base_steepness_k0 = self.s_curve_params['base_steepness_k0']
        self.cost_sensitivity_s = self.s_curve_params['cost_sensitivity_s']
        self.calibration_method = self.s_curve_params['calibration_method']
        self.bounds = self.s_curve_params['bounds']

    @staticmethod
    def logistic_function(t: np.ndarray, L: float, t0: float, k: float) -> np.ndarray:
        """
        Standard logistic (S-curve) function

        Args:
            t: Time points (years)
            L: Ceiling (maximum adoption level)
            t0: Inflection point (year of 50% adoption)
            k: Steepness parameter

        Returns:
            Adoption share at each time point
        """
        return L / (1 + np.exp(-k * (t - t0)))

    def calculate_adoption_curve(self, years: List[int], tco_advantage: pd.Series,
                                tipping_year: Optional[int] = None,
                                scenario: Optional[Dict] = None) -> pd.Series:
        """
        Calculate technology adoption curve based on TCO advantage

        Args:
            years: List of years
            tco_advantage: Series of TCO advantages (VRLA - Li-ion) by year
            tipping_year: Year when Li-ion becomes cheaper (optional)
            scenario: Optional scenario parameters

        Returns:
            Series of Li-ion market share (0 to 1) by year
        """
        # Get scenario parameters if provided
        adoption_acceleration = 1.0
        if scenario:
            adoption_acceleration = scenario.get('adoption_acceleration', 1.0)

        # Handle case with no tipping point
        if tipping_year is None:
            # Li-ion never becomes cheaper - use slow baseline adoption
            print("Warning: No tipping point found - using slow baseline adoption")
            return pd.Series(np.linspace(0.01, 0.20, len(years)), index=years)

        # Set inflection point at tipping year
        t0 = tipping_year

        # Calculate adoption for each year
        adoption = []
        for year in years:
            # Cost-adjusted steepness
            year_advantage = tco_advantage.get(year, 0) if year in tco_advantage.index else 0
            k = self.base_steepness_k0 + self.cost_sensitivity_s * max(0, year_advantage)

            # Apply scenario acceleration factor
            k *= adoption_acceleration

            # Calculate S-curve value
            share = self.ceiling_L / (1 + np.exp(-k * (year - t0)))

            # Ensure monotonic increase (market doesn't regress)
            if adoption and share < adoption[-1]:
                share = adoption[-1]

            adoption.append(share)

        return pd.Series(adoption, index=years)

    def calibrate_parameters(self, historical_data: pd.DataFrame,
                            tco_advantage: Optional[pd.Series] = None) -> Dict:
        """
        Calibrate S-curve parameters from historical data

        Args:
            historical_data: DataFrame with columns [year, lithium_share]
            tco_advantage: Optional series of TCO advantages for economic sensitivity

        Returns:
            Dictionary of calibrated parameters
        """
        if len(historical_data) < 3:
            print("Warning: Insufficient historical data for calibration. Using defaults.")
            return {
                'L': self.ceiling_L,
                't0': None,
                'k0': self.base_steepness_k0,
                's': self.cost_sensitivity_s,
                'method': 'default'
            }

        years = historical_data['year'].values
        shares = historical_data['lithium_share'].values

        if self.calibration_method == 'least_squares':
            try:
                # Initial guess
                L_init = min(self.ceiling_L, shares.max() * 1.5)
                t0_init = years[len(years) // 2]
                k_init = self.base_steepness_k0

                # Fit basic S-curve
                popt, pcov = curve_fit(
                    self.logistic_function,
                    years,
                    shares,
                    p0=[L_init, t0_init, k_init],
                    bounds=(
                        [self.bounds['L'][0], self.bounds['t0'][0], self.bounds['k0'][0]],
                        [self.bounds['L'][1], self.bounds['t0'][1], self.bounds['k0'][1]]
                    ),
                    maxfev=5000
                )

                L_fit, t0_fit, k_fit = popt

                # If TCO advantage data available, calibrate sensitivity
                s_fit = self.cost_sensitivity_s
                if tco_advantage is not None and len(tco_advantage) > 0:
                    # Simple estimation of cost sensitivity
                    # (More sophisticated methods could be implemented)
                    s_fit = self._estimate_cost_sensitivity(
                        years, shares, tco_advantage, L_fit, t0_fit, k_fit
                    )

                return {
                    'L': L_fit,
                    't0': t0_fit,
                    'k0': k_fit,
                    's': s_fit,
                    'method': 'least_squares',
                    'r_squared': self._calculate_r_squared(years, shares, L_fit, t0_fit, k_fit)
                }

            except Exception as e:
                print(f"Warning: Calibration failed ({e}). Using heuristic method.")
                return self._heuristic_calibration(historical_data)

        elif self.calibration_method == 'heuristic':
            return self._heuristic_calibration(historical_data)

        else:  # manual
            return {
                'L': self.ceiling_L,
                't0': self.s_curve_params.get('midpoint_t0'),
                'k0': self.base_steepness_k0,
                's': self.cost_sensitivity_s,
                'method': 'manual'
            }

    def _heuristic_calibration(self, historical_data: pd.DataFrame) -> Dict:
        """
        Heuristic calibration when least squares fails

        Args:
            historical_data: Historical adoption data

        Returns:
            Heuristically determined parameters
        """
        years = historical_data['year'].values
        shares = historical_data['lithium_share'].values

        # Estimate ceiling based on trend
        if len(shares) >= 3:
            recent_growth = shares[-1] - shares[-3]
            if recent_growth > 0:
                L_est = min(0.98, shares[-1] + recent_growth * 10)
            else:
                L_est = self.ceiling_L
        else:
            L_est = self.ceiling_L

        # Estimate inflection point
        # Find year closest to L/2
        half_ceiling = L_est / 2
        closest_idx = np.argmin(np.abs(shares - half_ceiling))
        if shares[closest_idx] < half_ceiling:
            # Haven't reached midpoint yet - project forward
            if len(shares) >= 2:
                annual_growth = (shares[-1] - shares[-2])
                if annual_growth > 0:
                    years_to_midpoint = (half_ceiling - shares[-1]) / annual_growth
                    t0_est = years[-1] + years_to_midpoint
                else:
                    t0_est = years[-1] + 10  # Default 10 years ahead
            else:
                t0_est = years[-1] + 10
        else:
            t0_est = years[closest_idx]

        # Estimate steepness based on historical growth rate
        if len(shares) >= 2:
            max_growth = max(shares[i+1] - shares[i] for i in range(len(shares)-1))
            k_est = min(1.5, max(0.1, max_growth * 10))
        else:
            k_est = self.base_steepness_k0

        return {
            'L': L_est,
            't0': t0_est,
            'k0': k_est,
            's': self.cost_sensitivity_s,
            'method': 'heuristic'
        }

    def _estimate_cost_sensitivity(self, years: np.ndarray, shares: np.ndarray,
                                  tco_advantage: pd.Series, L: float, t0: float, k0: float) -> float:
        """
        Estimate cost sensitivity parameter

        Args:
            years: Historical years
            shares: Historical market shares
            tco_advantage: TCO advantage series
            L, t0, k0: Fitted S-curve parameters

        Returns:
            Estimated cost sensitivity
        """
        # Simple approach: correlate residuals with cost advantage
        predicted = self.logistic_function(years, L, t0, k0)
        residuals = shares - predicted

        # Get TCO advantages for historical years
        advantages = [tco_advantage.get(year, 0) for year in years]

        if np.std(advantages) > 0:
            # Estimate sensitivity as correlation scaled by magnitude
            correlation = np.corrcoef(residuals, advantages)[0, 1]
            if not np.isnan(correlation):
                sensitivity = abs(correlation) * 0.002  # Scale to reasonable range
                return min(self.bounds['s'][1], max(self.bounds['s'][0], sensitivity))

        return self.cost_sensitivity_s

    def _calculate_r_squared(self, years: np.ndarray, actual: np.ndarray,
                            L: float, t0: float, k: float) -> float:
        """Calculate R-squared for fitted curve"""
        predicted = self.logistic_function(years, L, t0, k)
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)

        if ss_tot == 0:
            return 0.0

        return 1 - (ss_res / ss_tot)

    def project_adoption_scenarios(self, years: List[int], base_params: Dict,
                                  scenarios: Dict[str, Dict]) -> pd.DataFrame:
        """
        Project adoption under multiple scenarios

        Args:
            years: Years to project
            base_params: Base S-curve parameters
            scenarios: Dictionary of scenario configurations

        Returns:
            DataFrame with adoption projections for each scenario
        """
        results = pd.DataFrame({'year': years})

        for scenario_name, scenario_config in scenarios.items():
            # Apply scenario modifications to base parameters
            L = scenario_config.get('ceiling_L', base_params['L'])
            t0 = scenario_config.get('midpoint_t0', base_params['t0'])
            k0 = scenario_config.get('base_steepness_k0', base_params['k0'])
            acceleration = scenario_config.get('adoption_acceleration', 1.0)

            # Calculate adoption curve
            adoption = []
            for year in years:
                k = k0 * acceleration
                share = L / (1 + np.exp(-k * (year - t0)))
                adoption.append(share)

            results[scenario_name] = adoption

        return results

    def calculate_market_shares(self, total_demand: pd.Series, lithium_adoption: pd.Series) -> Dict[str, pd.Series]:
        """
        Calculate technology-specific market shares and demands

        Args:
            total_demand: Total market demand by year
            lithium_adoption: Li-ion adoption share (0 to 1)

        Returns:
            Dictionary with demand by technology
        """
        vrla_share = 1 - lithium_adoption

        return {
            'lithium_demand': total_demand * lithium_adoption,
            'vrla_demand': total_demand * vrla_share,
            'lithium_share': lithium_adoption,
            'vrla_share': vrla_share
        }

    def analyze_adoption_dynamics(self, adoption_curve: pd.Series) -> Dict:
        """
        Analyze adoption curve dynamics

        Args:
            adoption_curve: Series of adoption shares by year

        Returns:
            Dictionary with adoption metrics
        """
        years = adoption_curve.index.tolist()
        shares = adoption_curve.values

        metrics = {
            'initial_share': shares[0],
            'final_share': shares[-1],
            'max_share': shares.max(),
            'years_to_10pct': None,
            'years_to_50pct': None,
            'years_to_90pct': None,
            'max_annual_growth': 0,
            'average_annual_growth': 0,
            'acceleration_period': None,
            'saturation_period': None
        }

        # Find milestone years
        for threshold, key in [(0.10, 'years_to_10pct'),
                               (0.50, 'years_to_50pct'),
                               (0.90, 'years_to_90pct')]:
            for i, share in enumerate(shares):
                if share >= threshold:
                    metrics[key] = years[i]
                    break

        # Calculate growth metrics
        if len(shares) > 1:
            annual_growth = [shares[i+1] - shares[i] for i in range(len(shares)-1)]
            metrics['max_annual_growth'] = max(annual_growth)
            metrics['average_annual_growth'] = np.mean(annual_growth)

            # Find acceleration period (growth increasing)
            for i in range(len(annual_growth)-1):
                if annual_growth[i+1] < annual_growth[i]:
                    metrics['acceleration_period'] = (years[0], years[i+1])
                    break

            # Find saturation period (growth < 1% per year)
            for i, growth in enumerate(annual_growth):
                if growth < 0.01:
                    metrics['saturation_period'] = (years[i], years[-1])
                    break

        return metrics

    def generate_contestable_market(self, vrla_installed_base: pd.Series,
                                   vrla_lifespan: int, lithium_adoption: pd.Series) -> pd.DataFrame:
        """
        Calculate contestable market and technology splits

        Args:
            vrla_installed_base: VRLA installed base by year
            vrla_lifespan: VRLA battery lifespan
            lithium_adoption: Li-ion adoption share

        Returns:
            DataFrame with contestable market breakdown
        """
        years = vrla_installed_base.index

        # Contestable market = VRLA reaching end-of-life
        contestable_market = vrla_installed_base / vrla_lifespan

        # Split contestable market based on adoption curve
        li_ion_retrofits = contestable_market * lithium_adoption
        vrla_for_vrla = contestable_market * (1 - lithium_adoption)

        return pd.DataFrame({
            'year': years,
            'contestable_market': contestable_market,
            'li_ion_retrofits': li_ion_retrofits,
            'vrla_for_vrla': vrla_for_vrla,
            'retrofit_rate': lithium_adoption * 100  # Percentage switching to Li-ion
        })