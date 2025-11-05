"""
Product Demand Forecasting Module
Generic product forecasting for all product types (vehicles, energy, batteries, etc.)
"""

import sys
import os
import json
import argparse
import numpy as np
from typing import Dict, Optional, Tuple, List

from lib.utils import calculate_cagr, rolling_median, linear_extrapolation, find_intersection, clamp_array
from lib.cost_analyzer import CostAnalyzer
from lib.logistic_models import fit_logistic_curve, forecast_logistic_share, logistic_function
from lib.data_loader import DataLoader
from lib.validators import validate_forecast_consistency


class ProductForecaster:
    """Main orchestrator for product demand forecasting"""

    def __init__(self, product_name: str, region: str, end_year: int = 2040,
                 config_path: Optional[str] = None):
        """
        Initialize product forecaster

        Args:
            product_name: Product name (e.g., "EV_Cars", "Solar_PV")
            region: Region name (e.g., "China", "USA", "Europe")
            end_year: Forecast end year
            config_path: Path to config.json file
        """
        self.product_name = product_name
        self.region = region
        self.end_year = end_year

        # Load config
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.json')
        with open(config_path) as f:
            self.config = json.load(f)['default_parameters']

        # Load product catalog
        catalog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '../data/products_catalog_index.json')
        with open(catalog_path) as f:
            catalog = json.load(f)

        if product_name not in catalog['products']:
            raise ValueError(f"Product '{product_name}' not found in catalog")

        self.product_info = catalog['products'][product_name]
        self.entity_name = self.product_info['entity']
        self.product_type = self.product_info['type']

        # Initialize data loader
        entity_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   f'../data/{self.entity_name}.json')
        taxonomy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     f'../data/{self.entity_name}_taxonomy.json')

        self.data_loader = DataLoader(entity_path, taxonomy_path)

    def forecast(self) -> Dict:
        """
        Main forecasting pipeline

        Returns:
            Dictionary containing forecast results
        """
        print(f"\nForecasting {self.product_name} in {self.region}")
        print(f"Product type: {self.product_type}")
        print(f"Entity: {self.entity_name}")

        # Get market context
        market_context = self._get_market_context()

        # Route to appropriate forecasting method based on product type
        if market_context['disrupted']:
            if self.product_type == 'disruptor':
                forecast = self._forecast_disruptor(market_context)
            elif self.product_type == 'chimera':
                forecast = self._forecast_chimera(market_context)
            elif self.product_type == 'incumbent':
                forecast = self._forecast_incumbent(market_context)
            elif self.product_type == 'market':
                forecast = self._forecast_market(market_context)
            else:
                raise ValueError(f"Unknown product type: {self.product_type}")
        else:
            # Non-disrupted market: baseline linear forecast
            forecast = self._forecast_baseline(market_context)

        # Validate forecast
        validation = self._validate_forecast(forecast, market_context)

        # Package results
        result = {
            'product': self.product_name,
            'region': self.region,
            'entity': self.entity_name,
            'product_type': self.product_type,
            'market_context': market_context,
            'forecast': forecast,
            'validation': validation
        }

        return result

    def _get_market_context(self) -> Dict:
        """
        Retrieve market context: disruption state, tipping point, products

        Returns:
            Dictionary with market context information
        """
        # Load taxonomy to understand market structure
        taxonomy = self.data_loader.taxonomy

        # Check if this is a disrupted market
        # A market is disrupted if it has both disruptor and incumbent products
        has_disruptor = False
        has_incumbent = False

        # Scan products in taxonomy
        if 'data' in taxonomy:
            for prod_name, prod_data in taxonomy['data'].items():
                if 'entity_type' in prod_data:
                    if prod_data['entity_type'] == 'disruptor':
                        has_disruptor = True
                    elif prod_data['entity_type'] == 'incumbent':
                        has_incumbent = True

        disrupted = has_disruptor and has_incumbent

        context = {
            'disrupted': disrupted,
            'tipping_point': None,
            'disruptor_products': [],
            'incumbent_products': [],
            'chimera_products': [],
            'market_product': None
        }

        # If disrupted, find tipping point and categorize products
        if disrupted:
            # Find tipping point from cost analysis
            context['tipping_point'] = self._find_tipping_point()

            # Categorize products
            if 'data' in taxonomy:
                for prod_name, prod_data in taxonomy['data'].items():
                    if 'entity_type' in prod_data:
                        prod_type = prod_data['entity_type']
                        if prod_type == 'disruptor':
                            context['disruptor_products'].append(prod_name)
                        elif prod_type == 'incumbent':
                            context['incumbent_products'].append(prod_name)
                        elif prod_type == 'chimera':
                            context['chimera_products'].append(prod_name)
                        elif prod_type == 'market':
                            context['market_product'] = prod_name

        return context

    def _find_tipping_point(self) -> Optional[int]:
        """
        Find tipping point year (cost parity)

        Returns:
            Tipping point year or None if not found
        """
        try:
            # Load cost data for disruptor and incumbent
            # This is a simplified version - in reality we'd need to identify
            # which specific products to compare

            # For now, look for cost data with standard naming patterns
            entity_data = self.data_loader.entity_data
            entity_key = list(entity_data.keys())[0]

            # Look for cost datasets
            disruptor_cost = None
            incumbent_cost = None

            for metric_name, metric_data in entity_data[entity_key].items():
                if 'cost' in metric_name.lower() and self.region in metric_data.get('regions', {}):
                    if 'EV' in metric_name or 'Solar' in metric_name or 'Wind' in metric_name:
                        if disruptor_cost is None:
                            region_data = metric_data['regions'][self.region]
                            disruptor_cost = (region_data['X'], region_data['Y'])
                    elif 'ICE' in metric_name or 'Coal' in metric_name or 'Gas' in metric_name:
                        if incumbent_cost is None:
                            region_data = metric_data['regions'][self.region]
                            incumbent_cost = (region_data['X'], region_data['Y'])

            if disruptor_cost and incumbent_cost:
                # Find intersection point
                years = np.arange(min(disruptor_cost[0][0], incumbent_cost[0][0]),
                                 self.end_year + 1)

                # Interpolate to common years
                disruptor_interp = np.interp(years, disruptor_cost[0], disruptor_cost[1])
                incumbent_interp = np.interp(years, incumbent_cost[0], incumbent_cost[1])

                # Find first year where disruptor < incumbent
                for i, year in enumerate(years):
                    if disruptor_interp[i] < incumbent_interp[i]:
                        return int(year)

            return None

        except Exception as e:
            print(f"Warning: Could not find tipping point: {e}")
            return None

    def _forecast_disruptor(self, context: Dict) -> Dict:
        """
        Forecast disruptor product using logistic S-curve adoption

        Args:
            context: Market context dictionary

        Returns:
            Forecast dictionary
        """
        # Load historical demand data
        demand_data = self.data_loader.get_demand_data(self.product_name, self.region)

        if demand_data is None:
            return self._forecast_baseline(context)

        hist_years = np.array(demand_data['X'])
        hist_demand = np.array(demand_data['Y'])

        # Load market data
        market_product = context.get('market_product')
        if market_product:
            market_data = self.data_loader.get_demand_data(market_product, self.region)
            if market_data:
                market_years = np.array(market_data['X'])
                market_demand = np.array(market_data['Y'])
            else:
                # Estimate market from historical product demand
                market_years = hist_years
                market_demand = hist_demand * 1.5  # Rough estimate
        else:
            market_years = hist_years
            market_demand = hist_demand * 1.5

        # Forecast market demand
        forecast_years = np.arange(hist_years[0], self.end_year + 1)
        market_forecast = linear_extrapolation(
            market_years, market_demand, self.end_year,
            max_cagr=self.config['market_cagr_cap']
        )

        # Calculate historical shares
        common_years = np.intersect1d(hist_years, market_years)
        hist_shares = []
        for year in common_years:
            demand_val = hist_demand[hist_years == year][0]
            market_val = market_demand[market_years == year][0]
            if market_val > 0:
                hist_shares.append(demand_val / market_val)
            else:
                hist_shares.append(0)

        hist_shares = np.array(hist_shares)

        # Fit logistic curve if we have tipping point
        tipping_point = context.get('tipping_point')

        if tipping_point and len(hist_shares) >= 3:
            # Fit logistic curve
            try:
                L, k, t0 = fit_logistic_curve(
                    common_years, hist_shares,
                    initial_guess={'L': self.config['logistic_ceiling'],
                                 'k': 0.4,
                                 't0': tipping_point}
                )

                # Generate forecast shares
                forecast_shares = forecast_logistic_share(
                    forecast_years, L, k, t0, self.end_year
                )
            except Exception as e:
                print(f"Warning: Logistic fitting failed, using linear extrapolation: {e}")
                forecast_shares = linear_extrapolation(
                    common_years, hist_shares, self.end_year, max_cagr=0.1
                )
        else:
            # No tipping point or insufficient data: linear extrapolation
            forecast_shares = linear_extrapolation(
                common_years, hist_shares, self.end_year, max_cagr=0.1
            )

        # Clamp shares to [0, 1]
        forecast_shares = clamp_array(forecast_shares, 0.0, 1.0)

        # Calculate demand forecast
        forecast_demand = forecast_shares * market_forecast

        return {
            'years': forecast_years.tolist(),
            'demand': forecast_demand.tolist(),
            'shares': forecast_shares.tolist(),
            'market': market_forecast.tolist(),
            'method': 'logistic' if tipping_point else 'linear',
            'tipping_point': tipping_point
        }

    def _forecast_chimera(self, context: Dict) -> Dict:
        """
        Forecast chimera product using hump trajectory

        Args:
            context: Market context dictionary

        Returns:
            Forecast dictionary
        """
        # Load historical demand data
        demand_data = self.data_loader.get_demand_data(self.product_name, self.region)

        if demand_data is None:
            return self._forecast_baseline(context)

        hist_years = np.array(demand_data['X'])
        hist_demand = np.array(demand_data['Y'])

        # Get tipping point
        tipping_point = context.get('tipping_point')

        if not tipping_point:
            # No disruption yet, use linear extrapolation
            return self._forecast_baseline(context)

        # Chimera rises before tipping, peaks near tipping, then decays
        forecast_years = np.arange(hist_years[0], self.end_year + 1)
        forecast_demand = []

        # Get peak share from config
        peak_share = self.config.get('phev_peak_share', 0.15)
        half_life = self.config.get('chimera_decay_half_life', 3.0)

        # Load market forecast
        market_product = context.get('market_product')
        if market_product:
            market_data = self.data_loader.get_demand_data(market_product, self.region)
            if market_data:
                market_years = np.array(market_data['X'])
                market_demand = np.array(market_data['Y'])
                market_forecast = linear_extrapolation(
                    market_years, market_demand, self.end_year,
                    max_cagr=self.config['market_cagr_cap']
                )
            else:
                market_forecast = np.ones(len(forecast_years)) * np.mean(hist_demand) * 3
        else:
            market_forecast = np.ones(len(forecast_years)) * np.mean(hist_demand) * 3

        # Calculate shares
        for i, year in enumerate(forecast_years):
            if year <= tipping_point:
                # Before tipping: linear growth to peak
                progress = (year - hist_years[0]) / (tipping_point - hist_years[0])
                share = peak_share * progress
            else:
                # After tipping: exponential decay
                years_after = year - tipping_point
                share = peak_share * np.exp(-years_after * np.log(2) / half_life)

            share = np.clip(share, 0.0, 1.0)
            forecast_demand.append(share * market_forecast[i])

        forecast_demand = np.array(forecast_demand)

        return {
            'years': forecast_years.tolist(),
            'demand': forecast_demand.tolist(),
            'market': market_forecast.tolist(),
            'method': 'chimera_hump',
            'tipping_point': tipping_point,
            'peak_share': peak_share
        }

    def _forecast_incumbent(self, context: Dict) -> Dict:
        """
        Forecast incumbent product as residual

        Args:
            context: Market context dictionary

        Returns:
            Forecast dictionary
        """
        # For incumbent, we need to forecast disruptor and chimera first,
        # then calculate residual: Incumbent = Market - Disruptor - Chimera

        # Load market forecast
        market_product = context.get('market_product')
        if not market_product:
            return self._forecast_baseline(context)

        market_data = self.data_loader.get_demand_data(market_product, self.region)
        if not market_data:
            return self._forecast_baseline(context)

        market_years = np.array(market_data['X'])
        market_demand = np.array(market_data['Y'])
        forecast_years = np.arange(market_years[0], self.end_year + 1)
        market_forecast = linear_extrapolation(
            market_years, market_demand, self.end_year,
            max_cagr=self.config['market_cagr_cap']
        )

        # Forecast disruptor products
        disruptor_total = np.zeros(len(forecast_years))
        for disruptor_name in context['disruptor_products']:
            try:
                disruptor_forecaster = ProductForecaster(disruptor_name, self.region,
                                                        self.end_year)
                disruptor_result = disruptor_forecaster.forecast()
                disruptor_demand = np.array(disruptor_result['forecast']['demand'])
                disruptor_total += disruptor_demand
            except Exception as e:
                print(f"Warning: Could not forecast {disruptor_name}: {e}")

        # Forecast chimera products
        chimera_total = np.zeros(len(forecast_years))
        for chimera_name in context['chimera_products']:
            try:
                chimera_forecaster = ProductForecaster(chimera_name, self.region,
                                                      self.end_year)
                chimera_result = chimera_forecaster.forecast()
                chimera_demand = np.array(chimera_result['forecast']['demand'])
                chimera_total += chimera_demand
            except Exception as e:
                print(f"Warning: Could not forecast {chimera_name}: {e}")

        # Calculate residual
        incumbent_forecast = market_forecast - disruptor_total - chimera_total
        incumbent_forecast = np.maximum(incumbent_forecast, 0)  # No negatives

        return {
            'years': forecast_years.tolist(),
            'demand': incumbent_forecast.tolist(),
            'market': market_forecast.tolist(),
            'method': 'residual',
            'disruptor_total': disruptor_total.tolist(),
            'chimera_total': chimera_total.tolist()
        }

    def _forecast_market(self, context: Dict) -> Dict:
        """
        Forecast total market demand using linear extrapolation

        Args:
            context: Market context dictionary

        Returns:
            Forecast dictionary
        """
        demand_data = self.data_loader.get_demand_data(self.product_name, self.region)

        if demand_data is None:
            raise ValueError(f"No demand data found for {self.product_name} in {self.region}")

        hist_years = np.array(demand_data['X'])
        hist_demand = np.array(demand_data['Y'])

        # Linear extrapolation with CAGR cap
        forecast_years = np.arange(hist_years[0], self.end_year + 1)
        forecast_demand = linear_extrapolation(
            hist_years, hist_demand, self.end_year,
            max_cagr=self.config['market_cagr_cap']
        )

        return {
            'years': forecast_years.tolist(),
            'demand': forecast_demand.tolist(),
            'method': 'linear_bounded',
            'max_cagr': self.config['market_cagr_cap']
        }

    def _forecast_baseline(self, context: Dict) -> Dict:
        """
        Baseline forecast for non-disrupted products

        Args:
            context: Market context dictionary

        Returns:
            Forecast dictionary
        """
        demand_data = self.data_loader.get_demand_data(self.product_name, self.region)

        if demand_data is None:
            raise ValueError(f"No demand data found for {self.product_name} in {self.region}")

        hist_years = np.array(demand_data['X'])
        hist_demand = np.array(demand_data['Y'])

        # Simple linear extrapolation
        forecast_years = np.arange(hist_years[0], self.end_year + 1)
        forecast_demand = linear_extrapolation(
            hist_years, hist_demand, self.end_year,
            max_cagr=self.config['market_cagr_cap']
        )

        return {
            'years': forecast_years.tolist(),
            'demand': forecast_demand.tolist(),
            'method': 'baseline_linear'
        }

    def _validate_forecast(self, forecast: Dict, context: Dict) -> Dict:
        """
        Validate forecast consistency

        Args:
            forecast: Forecast dictionary
            context: Market context

        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }

        demand = np.array(forecast['demand'])

        # Check for negative values
        if np.any(demand < 0):
            validation['errors'].append('Negative demand values found')
            validation['is_valid'] = False

        # Check for unrealistic jumps
        if len(demand) > 1:
            diffs = np.diff(demand)
            rel_changes = np.abs(diffs[:-1] / (demand[:-2] + 1e-10))
            if np.any(rel_changes > 0.5):
                validation['warnings'].append('Large year-over-year changes detected')

        # Check sum constraint if market product
        if self.product_type == 'market' and context.get('disrupted'):
            # Market should equal sum of components (if we have them)
            pass  # Complex check, skipping for now

        return validation


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='Forecast product demand')
    parser.add_argument('--product', required=True, help='Product name')
    parser.add_argument('--region', required=True, help='Region name')
    parser.add_argument('--end-year', type=int, default=2040, help='Forecast end year')
    parser.add_argument('--output', choices=['csv', 'json', 'both'], default='csv',
                       help='Output format')
    parser.add_argument('--output-dir', default='../output', help='Output directory')

    args = parser.parse_args()

    # Create forecaster and run
    forecaster = ProductForecaster(args.product, args.region, args.end_year)
    result = forecaster.forecast()

    # Create output directory if needed
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Export results
    if args.output in ['json', 'both']:
        output_path = os.path.join(output_dir,
                                   f'{args.product}_{args.region}_{args.end_year}.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nJSON output: {output_path}")

    if args.output in ['csv', 'both']:
        # Convert to CSV format
        import pandas as pd

        df = pd.DataFrame({
            'Year': result['forecast']['years'],
            'Demand': result['forecast']['demand']
        })

        if 'market' in result['forecast']:
            df['Market'] = result['forecast']['market']

        if 'shares' in result['forecast']:
            df['Share'] = result['forecast']['shares']

        output_path = os.path.join(output_dir,
                                   f'{args.product}_{args.region}_{args.end_year}.csv')
        df.to_csv(output_path, index=False)
        print(f"CSV output: {output_path}")

    # Print summary
    print(f"\nForecast Summary:")
    print(f"  Product: {result['product']}")
    print(f"  Region: {result['region']}")
    print(f"  Type: {result['product_type']}")
    print(f"  Method: {result['forecast']['method']}")

    if result['market_context']['disrupted']:
        print(f"  Market Status: Disrupted")
        if result['market_context']['tipping_point']:
            print(f"  Tipping Point: {result['market_context']['tipping_point']}")
    else:
        print(f"  Market Status: Non-disrupted")

    # Print validation
    if result['validation']['is_valid']:
        print(f"  Validation: ✓ Passed")
    else:
        print(f"  Validation: ✗ Failed")
        for error in result['validation']['errors']:
            print(f"    Error: {error}")

    for warning in result['validation']['warnings']:
        print(f"    Warning: {warning}")


if __name__ == '__main__':
    main()
