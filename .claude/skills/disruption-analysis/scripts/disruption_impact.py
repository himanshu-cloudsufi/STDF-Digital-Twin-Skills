"""
Disruption Impact Analysis

Analyzes cross-market disruption impacts and displacement timelines.
Synthesizes product and commodity forecasts to answer questions about
disruption, displacement, and peak demand years.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../_forecasting_core'))

from core.utils import calculate_cagr
from core.validators import validate_non_negative

import json
import argparse
import numpy as np
from typing import Dict, List, Optional, Any, Union


class DisruptionAnalyzer:
    """Analyze cross-market disruption impacts"""

    def __init__(self, event_description: str, region: str,
                 forecasts_dir: Optional[str] = None,
                 config_path: Optional[str] = None):
        """
        Initialize disruption analyzer.

        Args:
            event_description: Description of disruption event (e.g., "EV disruption")
            region: Geographic region to analyze
            forecasts_dir: Optional directory containing pre-computed forecasts
            config_path: Path to config.json file
        """
        self.event_description = event_description
        self.region = region
        self.forecasts_dir = forecasts_dir

        # Load config
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../config.json')
        self.config = self._load_config(config_path)

        # Load disruption mappings
        mappings_path = os.path.join(os.path.dirname(__file__), '../data/disruption_mappings.json')
        self.mappings = self._load_disruption_mappings(mappings_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def _load_disruption_mappings(self, mappings_path: str) -> Dict[str, Any]:
        """Load disruption relationship mappings"""
        with open(mappings_path, 'r') as f:
            return json.load(f)

    def analyze(self) -> Dict[str, Any]:
        """
        Main analysis pipeline.

        Returns:
            Dictionary containing disruption analysis results
        """
        # Step 1: Parse event description
        disruption_info = self._parse_event(self.event_description)

        if disruption_info is None:
            return {
                'error': f'Could not identify disruption pattern from: {self.event_description}',
                'available_patterns': list(self.mappings.keys())
            }

        # Step 2: Load relevant forecasts
        try:
            disruptor_forecast = self._load_forecast(disruption_info['disruptor'])
            impacted_forecast = self._load_forecast(disruption_info['impacted'])
        except Exception as e:
            return {
                'error': f'Failed to load forecast data: {str(e)}',
                'disruption_info': disruption_info
            }

        # Step 3: Calculate displacement
        displacement_timeline = self._calculate_displacement(
            disruptor_forecast,
            impacted_forecast,
            disruption_info
        )

        # Step 4: Find key milestones
        milestones = self._find_milestones(displacement_timeline)

        # Step 5: Generate report
        return {
            'event': self.event_description,
            'region': self.region,
            'disruptor': disruption_info['disruptor'],
            'impacted': disruption_info['impacted'],
            'conversion_factor': disruption_info['conversion_factor'],
            'units': disruption_info['units'],
            'displacement_timeline': displacement_timeline,
            'milestones': milestones,
            'summary': self._generate_summary(milestones, disruption_info)
        }

    def _parse_event(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Parse event description to identify disruptor and impacted.

        Args:
            description: Natural language description of disruption event

        Returns:
            Dictionary with disruptor, impacted, conversion_factor, and metadata
        """
        description_lower = description.lower()

        # Try to match against known disruption patterns
        best_match = None
        best_score = 0

        for pattern_id, pattern_info in self.mappings.items():
            # Count keyword matches
            keywords = pattern_info['keywords']
            matches = sum(1 for kw in keywords if kw.lower() in description_lower)

            if matches > best_score:
                best_score = matches
                best_match = pattern_id

        if best_match and best_score > 0:
            pattern = self.mappings[best_match]
            return {
                'pattern_id': best_match,
                'disruptor': pattern['disruptor'],
                'impacted': pattern['impacted'],
                'conversion_factor': pattern['conversion_factor'],
                'units': pattern['units'],
                'description': pattern['description']
            }

        return None

    def _load_forecast(self, product_or_commodity: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Load forecast data for a product or commodity.

        Args:
            product_or_commodity: Product/commodity name or list of names

        Returns:
            Dictionary with years and demand arrays
        """
        if self.forecasts_dir:
            # Load from provided directory
            if isinstance(product_or_commodity, list):
                # Aggregate multiple products (e.g., SWB = Solar + Wind + Battery)
                forecasts = []
                for product in product_or_commodity:
                    forecast_path = os.path.join(
                        self.forecasts_dir,
                        f'{product}_{self.region}.json'
                    )
                    if os.path.exists(forecast_path):
                        with open(forecast_path, 'r') as f:
                            forecasts.append(json.load(f))

                if forecasts:
                    # Aggregate by summing demand across products
                    return self._aggregate_forecasts(forecasts)
            else:
                # Single product
                forecast_path = os.path.join(
                    self.forecasts_dir,
                    f'{product_or_commodity}_{self.region}.json'
                )
                if os.path.exists(forecast_path):
                    with open(forecast_path, 'r') as f:
                        return json.load(f)

        # Fall back to internal estimation (placeholder)
        return self._estimate_simple_trend(product_or_commodity)

    def _estimate_simple_trend(self, product_or_commodity: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Simple trend estimation when no forecast data available.

        This is a placeholder - in production, this would use historical
        data to extrapolate a basic trend.
        """
        # Generate placeholder data
        end_year = self.config['default_parameters']['end_year']
        years = list(range(2020, end_year + 1))

        # Simple linear trend (placeholder)
        if isinstance(product_or_commodity, list):
            name = '+'.join(product_or_commodity)
        else:
            name = product_or_commodity

        demand = [100 + i * 10 for i in range(len(years))]  # Placeholder

        return {
            'product': name,
            'years': years,
            'demand': demand,
            'note': 'Estimated using simple trend (no historical data available)'
        }

    def _aggregate_forecasts(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple product forecasts.

        Args:
            forecasts: List of forecast dictionaries

        Returns:
            Aggregated forecast dictionary
        """
        if not forecasts:
            raise ValueError("No forecasts to aggregate")

        # Use years from first forecast
        years = forecasts[0].get('years', forecasts[0].get('forecast', {}).get('years', []))

        # Initialize aggregated demand
        aggregated_demand = np.zeros(len(years))

        # Sum demand from all forecasts
        for forecast in forecasts:
            demand = forecast.get('demand', forecast.get('forecast', {}).get('demand', []))
            if len(demand) == len(years):
                aggregated_demand += np.array(demand)

        return {
            'years': years,
            'demand': aggregated_demand.tolist(),
            'aggregated_from': [f.get('product', 'unknown') for f in forecasts]
        }

    def _calculate_displacement(self, disruptor: Dict[str, Any],
                                impacted: Dict[str, Any],
                                info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate how disruptor displaces incumbent over time.

        Args:
            disruptor: Disruptor forecast data
            impacted: Impacted (incumbent) forecast data
            info: Disruption metadata (conversion_factor, etc.)

        Returns:
            List of displacement data points by year
        """
        conversion_factor = info['conversion_factor']

        # Extract years and demand arrays
        disruptor_years = disruptor.get('years', disruptor.get('forecast', {}).get('years', []))
        disruptor_demand = disruptor.get('demand', disruptor.get('forecast', {}).get('demand', []))

        impacted_years = impacted.get('years', impacted.get('forecast', {}).get('years', []))
        impacted_demand = impacted.get('demand', impacted.get('forecast', {}).get('demand', []))

        # Find common years
        common_years = sorted(set(disruptor_years) & set(impacted_years))

        if not common_years:
            raise ValueError("No overlapping years between disruptor and impacted forecasts")

        displacement = []

        for year in common_years:
            # Get demand values for this year
            disruptor_idx = disruptor_years.index(year)
            impacted_idx = impacted_years.index(year)

            disruptor_level = disruptor_demand[disruptor_idx]
            baseline = impacted_demand[impacted_idx]

            # Displaced demand = disruptor_units × conversion_factor
            displaced = disruptor_level * conversion_factor

            # Remaining demand = baseline - displaced (non-negative)
            remaining = max(0, baseline - displaced)

            # Displacement rate
            displacement_rate = displaced / baseline if baseline > 0 else 0
            displacement_rate = min(1.0, max(0, displacement_rate))  # Clamp to [0, 1]

            displacement.append({
                'year': int(year),
                'disruptor_level': float(disruptor_level),
                'baseline_demand': float(baseline),
                'displaced_demand': float(displaced),
                'remaining_demand': float(remaining),
                'displacement_rate': float(displacement_rate)
            })

        return displacement

    def _find_milestones(self, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find key years: peak, 50%, 95%, 100% displacement.

        Args:
            timeline: Displacement timeline data

        Returns:
            Dictionary of milestone years
        """
        milestones = {}

        if not timeline:
            return milestones

        # Peak year (maximum baseline demand)
        baseline_demands = [t['baseline_demand'] for t in timeline]
        peak_idx = np.argmax(baseline_demands)
        milestones['peak_year'] = timeline[peak_idx]['year']
        milestones['peak_demand'] = timeline[peak_idx]['baseline_demand']

        # Displacement thresholds
        thresholds = self.config['default_parameters']['displacement_thresholds']

        for threshold in thresholds:
            threshold_pct = int(threshold * 100)
            key = f'{threshold_pct}_percent_displacement'

            for t in timeline:
                if t['displacement_rate'] >= threshold:
                    milestones[key] = t['year']
                    break

        # Find year when remaining demand drops to near zero
        for t in timeline:
            if t['remaining_demand'] < 0.01 * t['baseline_demand']:  # <1% remaining
                milestones['near_complete_displacement'] = t['year']
                break

        return milestones

    def _generate_summary(self, milestones: Dict[str, Any],
                         disruption_info: Dict[str, Any]) -> str:
        """
        Generate human-readable summary.

        Args:
            milestones: Dictionary of milestone years
            disruption_info: Disruption metadata

        Returns:
            Summary string
        """
        summary = []

        # Description
        summary.append(disruption_info['description'])

        # Peak year
        if 'peak_year' in milestones:
            peak_demand = milestones.get('peak_demand', 'N/A')
            summary.append(f"Peak demand occurs in {milestones['peak_year']}")

        # Displacement milestones
        if '50_percent_displacement' in milestones:
            summary.append(f"50% displaced by {milestones['50_percent_displacement']}")

        if '95_percent_displacement' in milestones:
            summary.append(f"95% displaced by {milestones['95_percent_displacement']}")

        if '100_percent_displacement' in milestones:
            summary.append(f"Complete displacement by {milestones['100_percent_displacement']}")
        elif 'near_complete_displacement' in milestones:
            summary.append(f"Near-complete displacement by {milestones['near_complete_displacement']}")

        return '; '.join(summary)


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Analyze disruption impact',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--event', required=True,
                       help='Disruption event description (e.g., "EV disruption")')
    parser.add_argument('--region', required=True,
                       help='Region (China, USA, Europe, Rest_of_World, Global)')
    parser.add_argument('--forecasts-dir', default=None,
                       help='Directory with pre-computed forecast data')
    parser.add_argument('--output', choices=['json', 'text'], default='json',
                       help='Output format')
    parser.add_argument('--output-dir', default='./output',
                       help='Output directory for results')

    args = parser.parse_args()

    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)

    # Run analysis
    analyzer = DisruptionAnalyzer(args.event, args.region, args.forecasts_dir)
    result = analyzer.analyze()

    # Output results
    if args.output == 'json':
        output_path = os.path.join(args.output_dir, 'disruption_analysis.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Analysis saved to {output_path}")

        # Also print summary
        if 'summary' in result:
            print(f"\nSummary: {result['summary']}")
    else:
        # Text output
        if 'error' in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"Disruption Analysis: {result['event']}")
            print(f"Region: {result['region']}")
            print(f"{'='*60}\n")

            print(f"Disruptor: {result['disruptor']}")
            print(f"Impacted: {result['impacted']}")
            print(f"Conversion: {result['conversion_factor']} {result['units']}\n")

            print(f"Summary:")
            print(f"  {result['summary']}\n")

            if 'milestones' in result:
                print(f"Key Milestones:")
                for key, value in result['milestones'].items():
                    print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
