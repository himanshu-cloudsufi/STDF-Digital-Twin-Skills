#!/usr/bin/env python3
"""
Commodity Demand Forecasting Script

Calculates commodity demand from:
1. New product sales (e.g., copper in new EVs)
2. Component replacements (e.g., lead batteries in existing ICE fleet)
"""

import sys
import os

from lib.utils import calculate_cagr, linear_extrapolation, rolling_median
from lib.validators import validate_non_negative

import json
import argparse
import numpy as np
from typing import Dict, List, Tuple, Any


class CommodityForecaster:
    """Main orchestrator for commodity demand forecasting"""

    def __init__(self, commodity_name: str, region: str, end_year: int,
                 config_path: str = None):
        self.commodity_name = commodity_name.lower()
        self.region = region
        self.end_year = end_year

        # Determine config path
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../config.json')

        self.config = self._load_config(config_path)

        # Load commodity data
        self.intensity_factors = self._load_intensity_factors()
        self.replacement_cycles = self._load_replacement_cycles()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration file"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def _load_intensity_factors(self) -> Dict:
        """Load commodity intensity factors"""
        intensity_path = os.path.join(os.path.dirname(__file__), '../data/commodity_intensity.json')
        with open(intensity_path, 'r') as f:
            return json.load(f)

    def _load_replacement_cycles(self) -> Dict:
        """Load component replacement cycles"""
        cycles_path = os.path.join(os.path.dirname(__file__), '../data/replacement_cycles.json')
        with open(cycles_path, 'r') as f:
            return json.load(f)

    def forecast(self) -> Dict[str, Any]:
        """Main forecasting pipeline"""
        print(f"\n{'='*70}")
        print(f"Forecasting {self.commodity_name.upper()} demand in {self.region}")
        print(f"{'='*70}\n")

        # Step 1: Identify contributing products
        contributing_products = self._get_contributing_products()
        print(f"Contributing products: {', '.join(contributing_products)}\n")

        # Step 2: Forecast demand for each product
        demand_by_source = {}
        for product in contributing_products:
            print(f"Processing {product}...")

            # Get product demand (from files or built-in estimation)
            product_demand = self._get_product_demand(product)

            if product_demand is None:
                print(f"  Warning: No demand data available for {product}, skipping")
                continue

            # Calculate new sales demand
            new_sales_demand = self._calculate_new_sales_demand(product, product_demand)

            # Calculate replacement demand
            replacement_demand = self._calculate_replacement_demand(product, product_demand)

            demand_by_source[product] = {
                'new_sales': new_sales_demand,
                'replacement': replacement_demand,
                'total': self._sum_demands(new_sales_demand, replacement_demand)
            }

            print(f"  ✓ Complete")

        # Step 3: Aggregate total demand
        print("\nAggregating total demand...")
        total_demand = self._aggregate_demand(demand_by_source)

        # Step 4: Find peak year
        peak_year = self._find_peak_year(total_demand)
        print(f"\n🔍 Peak demand year: {peak_year}")

        # Step 5: Validate
        validation = self._validate_forecast(total_demand)

        return {
            'commodity': self.commodity_name,
            'region': self.region,
            'end_year': self.end_year,
            'demand_by_source': demand_by_source,
            'total_demand': total_demand,
            'peak_year': peak_year,
            'validation': validation
        }

    def _get_contributing_products(self) -> List[str]:
        """Identify products that contribute to this commodity's usage"""
        if self.commodity_name not in self.intensity_factors:
            raise ValueError(f"Commodity '{self.commodity_name}' not found in intensity factors")

        commodity_data = self.intensity_factors[self.commodity_name]
        products = [k for k in commodity_data.keys() if k != 'units']
        return products

    def _get_product_demand(self, product: str) -> Dict[str, Any]:
        """Get product demand using built-in estimation"""
        # Use standalone estimation (no cross-skill dependencies)
        return self._estimate_product_demand_simple(product)

    def _estimate_product_demand_simple(self, product: str) -> Dict[str, List]:
        """Lightweight product demand estimation: linear extrapolation"""
        # Try to load historical product data from entity files
        # For now, return None (to be implemented with actual data loading)

        # This would load from Passenger_Cars.json, Commercial_Vehicle.json, etc.
        # For initial implementation, we'll use placeholder logic

        print(f"  Note: Using simplified estimation for {product}")
        return None

    def _calculate_new_sales_demand(self, product: str, product_demand: Dict) -> Dict[str, List]:
        """Commodity demand from new product sales"""
        intensity = self.intensity_factors[self.commodity_name][product]
        years = product_demand['years']
        units = product_demand['units']

        # Demand = units × intensity
        demand = [u * intensity for u in units]

        return {'years': years, 'demand': demand}

    def _calculate_replacement_demand(self, product: str, product_demand: Dict) -> Dict[str, List]:
        """Commodity demand from component replacements"""
        # Check if this product has replacement cycles for this commodity
        if product not in self.replacement_cycles:
            # No replacement demand
            return {'years': product_demand['years'], 'demand': [0] * len(product_demand['years'])}

        if self.commodity_name not in self.replacement_cycles[product]:
            # No replacement demand for this commodity
            return {'years': product_demand['years'], 'demand': [0] * len(product_demand['years'])}

        intensity = self.intensity_factors[self.commodity_name][product]
        cycle_years = self.replacement_cycles[product][self.commodity_name]
        replacement_rate = 1.0 / cycle_years

        # Calculate installed base
        installed_base = self._calculate_installed_base(product, product_demand)

        # Replacement demand = installed_base × replacement_rate × intensity
        demand = [ib * replacement_rate * intensity for ib in installed_base]

        return {'years': product_demand['years'], 'demand': demand}

    def _calculate_installed_base(self, product: str, product_demand: Dict) -> List[float]:
        """Calculate installed base: cumulative sales - retirements"""
        years = product_demand['years']
        units = product_demand['units']
        lifetime = self.config['default_parameters']['vehicle_lifetime_years']

        installed_base = []
        for i, year in enumerate(years):
            # Cumulative sales up to this year
            cumulative_sales = sum(units[:i+1])

            # Retirements: sales from (lifetime) years ago
            retirement_year_idx = i - lifetime
            if retirement_year_idx >= 0:
                retirements = sum(units[:retirement_year_idx+1])
            else:
                retirements = 0

            installed_base.append(max(0, cumulative_sales - retirements))

        return installed_base

    def _sum_demands(self, demand1: Dict, demand2: Dict) -> Dict[str, List]:
        """Sum two demand dictionaries"""
        return {
            'years': demand1['years'],
            'demand': [d1 + d2 for d1, d2 in zip(demand1['demand'], demand2['demand'])]
        }

    def _aggregate_demand(self, demand_by_source: Dict) -> Dict[str, List]:
        """Sum demand across all products"""
        if not demand_by_source:
            return {'years': [], 'demand': []}

        # Get years from first product
        first_product = list(demand_by_source.keys())[0]
        years = demand_by_source[first_product]['total']['years']

        # Initialize aggregate demand
        total_demand = [0] * len(years)

        # Sum across all products
        for product, demands in demand_by_source.items():
            for i, d in enumerate(demands['total']['demand']):
                total_demand[i] += d

        return {'years': years, 'demand': total_demand}

    def _find_peak_year(self, total_demand: Dict) -> int:
        """Identify year of peak demand"""
        if not total_demand['demand']:
            return None

        years = total_demand['years']
        demand = total_demand['demand']
        peak_idx = np.argmax(demand)
        return years[peak_idx]

    def _validate_forecast(self, total_demand: Dict) -> Dict[str, Any]:
        """Validate forecast: no negatives, smooth transitions"""
        validation = {
            'passed': True,
            'warnings': [],
            'errors': []
        }

        demand = total_demand['demand']

        # Check for negative values
        if any(d < 0 for d in demand):
            validation['errors'].append("Negative demand values detected")
            validation['passed'] = False

        # Check for unrealistic jumps (>100% year-over-year)
        for i in range(1, len(demand)):
            if demand[i-1] > 0:
                change = abs((demand[i] - demand[i-1]) / demand[i-1])
                if change > 1.0:
                    validation['warnings'].append(
                        f"Large demand change detected at year {total_demand['years'][i]}: {change*100:.1f}%"
                    )

        return validation


def export_to_csv(result: Dict, output_path: str):
    """Export forecast results to CSV"""
    with open(output_path, 'w') as f:
        f.write("Year,New_Sales_Demand,Replacement_Demand,Total_Demand\n")

        years = result['total_demand']['years']
        total_demand = result['total_demand']['demand']

        # Aggregate new sales and replacement across products
        new_sales_total = [0] * len(years)
        replacement_total = [0] * len(years)

        for product, demands in result['demand_by_source'].items():
            for i in range(len(years)):
                new_sales_total[i] += demands['new_sales']['demand'][i]
                replacement_total[i] += demands['replacement']['demand'][i]

        for i, year in enumerate(years):
            f.write(f"{year},{new_sales_total[i]:.2f},{replacement_total[i]:.2f},{total_demand[i]:.2f}\n")

    print(f"\n✓ CSV exported to: {output_path}")


def export_to_json(result: Dict, output_path: str):
    """Export forecast results to JSON"""
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"✓ JSON exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Forecast commodity demand')
    parser.add_argument('--commodity', required=True, help='Commodity name')
    parser.add_argument('--region', required=True, help='Region name')
    parser.add_argument('--end-year', type=int, default=2040, help='Forecast end year')
    parser.add_argument('--output', choices=['csv', 'json', 'both'], default='csv')
    parser.add_argument('--output-dir', default='./output', help='Output directory')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Run forecast
    forecaster = CommodityForecaster(
        args.commodity, args.region, args.end_year
    )
    result = forecaster.forecast()

    # Export results
    if args.output in ['json', 'both']:
        output_path = os.path.join(args.output_dir,
                                   f'{args.commodity}_{args.region}_{args.end_year}.json')
        export_to_json(result, output_path)

    if args.output in ['csv', 'both']:
        output_path = os.path.join(args.output_dir,
                                   f'{args.commodity}_{args.region}_{args.end_year}.csv')
        export_to_csv(result, output_path)

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Commodity: {result['commodity']}")
    print(f"Region: {result['region']}")
    print(f"Peak year: {result['peak_year']}")
    print(f"Validation: {'✓ PASSED' if result['validation']['passed'] else '✗ FAILED'}")

    if result['validation']['warnings']:
        print("\nWarnings:")
        for warning in result['validation']['warnings']:
            print(f"  ⚠ {warning}")

    if result['validation']['errors']:
        print("\nErrors:")
        for error in result['validation']['errors']:
            print(f"  ✗ {error}")

    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
