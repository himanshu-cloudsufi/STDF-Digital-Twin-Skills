"""
Disruption Analysis for Artificial Labour
Implements Seba framework: cost + capability → tipping points → S-curves
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from data_loader import ALDataLoader
from analyzer import ALAnalyzer


class DisruptorAnalysis:
    """Analyze disruption timing and adoption patterns"""

    def __init__(self, data_loader: Optional[ALDataLoader] = None):
        """
        Initialize disruptor analysis

        Args:
            data_loader: ALDataLoader instance
        """
        self.loader = data_loader if data_loader else ALDataLoader()
        self.analyzer = ALAnalyzer(self.loader)

    def detect_cost_parity(
        self,
        disruptor: Tuple[str, str],
        incumbent: Tuple[str, str],
        region: str = 'Global',
        threshold: float = 1.0
    ) -> Optional[float]:
        """
        Detect year when disruptor reaches cost parity with incumbent

        Args:
            disruptor: Tuple of (category, dataset) for disruptor
            incumbent: Tuple of (category, dataset) for incumbent
            region: Region name
            threshold: Cost ratio threshold (1.0 = exact parity)

        Returns:
            Year of cost parity, or None if not yet reached
        """
        try:
            X_d, Y_d = self.loader.get_time_series(disruptor[0], disruptor[1], region)
            X_i, Y_i = self.loader.get_time_series(incumbent[0], incumbent[1], region)

            # Find common years
            common_years = np.intersect1d(X_d, X_i)
            if len(common_years) == 0:
                return None

            # Get values for common years
            Y_d_common = np.array([Y_d[X_d == year][0] for year in common_years])
            Y_i_common = np.array([Y_i[X_i == year][0] for year in common_years])

            # Calculate cost ratio
            cost_ratio = Y_d_common / Y_i_common

            # Find first year where ratio <= threshold
            parity_mask = cost_ratio <= threshold
            if np.any(parity_mask):
                parity_idx = np.where(parity_mask)[0][0]
                return float(common_years[parity_idx])

            return None
        except Exception:
            return None

    def estimate_tipping_point(
        self,
        disruptor: Tuple[str, str],
        incumbent: Optional[Tuple[str, str]] = None,
        region: str = 'Global',
        method: str = 'inflection'
    ) -> Dict:
        """
        Estimate tipping point for disruptor adoption

        Args:
            disruptor: Tuple of (category, dataset) for disruptor
            incumbent: Optional tuple for incumbent (for cost parity analysis)
            region: Region name
            method: 'inflection' (S-curve inflection) or 'cost_parity'

        Returns:
            Dict with tipping point estimate and confidence
        """
        result = {
            'disruptor': disruptor[1],
            'region': region,
            'method': method,
            'tipping_year': None,
            'confidence': 'low',
            'reasoning': ''
        }

        if method == 'inflection':
            # Detect inflection point in adoption curve
            inflection = self.analyzer.detect_inflection_point(
                disruptor[0], disruptor[1], region
            )
            if inflection:
                result['tipping_year'] = inflection
                result['confidence'] = 'medium'
                result['reasoning'] = 'Inflection point detected in adoption curve'
            else:
                result['reasoning'] = 'No clear inflection point detected yet'

        elif method == 'cost_parity' and incumbent:
            # Use cost parity as tipping indicator
            parity_year = self.detect_cost_parity(disruptor, incumbent, region)
            if parity_year:
                result['tipping_year'] = parity_year
                result['confidence'] = 'medium'
                result['reasoning'] = 'Cost parity achieved with incumbent'
            else:
                result['reasoning'] = 'Cost parity not yet achieved'

        return result

    def forecast_adoption_milestones(
        self,
        category: str,
        dataset: str,
        region: str = 'Global',
        milestones: List[float] = [0.1, 0.5, 0.8],
        end_year: float = 2030
    ) -> Dict:
        """
        Forecast when adoption reaches key milestones (10%, 50%, 80%)

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name
            milestones: List of adoption share milestones (0.0-1.0)
            end_year: Latest year to project to

        Returns:
            Dict with milestone years and adoption trajectory
        """
        X, Y = self.loader.get_time_series(category, dataset, region)

        # Normalize to 0-1 scale if needed (assume max value is ceiling)
        Y_max = Y.max()
        Y_norm = Y / Y_max

        # Simple projection using CAGR
        cagr = self.analyzer.calculate_cagr(category, dataset, region)
        last_year = X[-1]
        last_value = Y[-1]

        # Project forward
        future_years = np.arange(last_year + 1, end_year + 1)
        future_values = last_value * (1 + cagr) ** (future_years - last_year)

        # Cap at reasonable maximum
        future_values = np.minimum(future_values, Y_max * 1.2)

        # Find milestone years
        milestone_years = {}
        all_years = np.concatenate([X, future_years])
        all_values = np.concatenate([Y, future_values])
        all_values_norm = all_values / Y_max

        for milestone in milestones:
            # Find first year where normalized value >= milestone
            idx = np.where(all_values_norm >= milestone)[0]
            if len(idx) > 0:
                milestone_years[f"{int(milestone*100)}%"] = float(all_years[idx[0]])
            else:
                milestone_years[f"{int(milestone*100)}%"] = None

        return {
            'dataset': dataset,
            'region': region,
            'cagr': cagr,
            'latest_year': float(last_year),
            'latest_value': float(last_value),
            'milestone_years': milestone_years,
            'projection_end': float(end_year)
        }

    def create_disruption_timeline(
        self,
        disruptor: Tuple[str, str],
        incumbent: Optional[Tuple[str, str]] = None,
        region: str = 'Global',
        scenarios: List[str] = ['Base']
    ) -> Dict:
        """
        Create comprehensive disruption timeline

        Args:
            disruptor: Tuple of (category, dataset) for disruptor
            incumbent: Optional tuple for incumbent
            region: Region name
            scenarios: List of scenario names

        Returns:
            Dict with disruption timeline including parity, tipping, and milestones
        """
        timeline = {
            'disruptor': disruptor[1],
            'incumbent': incumbent[1] if incumbent else None,
            'region': region,
            'scenarios': {}
        }

        # Get current stats
        stats = self.analyzer.summary_statistics(disruptor[0], disruptor[1], region)

        # Detect cost parity if incumbent provided
        cost_parity = None
        if incumbent:
            cost_parity = self.detect_cost_parity(disruptor, incumbent, region)

        # Estimate tipping point
        tipping = self.estimate_tipping_point(disruptor, incumbent, region)

        # Forecast milestones
        milestones = self.forecast_adoption_milestones(
            disruptor[0], disruptor[1], region
        )

        # Build timeline for each scenario
        for scenario in scenarios:
            timeline['scenarios'][scenario] = {
                'cost_parity_year': cost_parity,
                'tipping_point': tipping,
                'adoption_milestones': milestones['milestone_years'],
                'cagr': stats['cagr'],
                'current_value': stats['latest_value'],
                'current_year': stats['date_range'][1]
            }

        return timeline

    def analyze_capability_trajectory(
        self,
        category: str,
        dataset: str,
        region: str = 'Global',
        benchmark_value: Optional[float] = None
    ) -> Dict:
        """
        Analyze capability improvement trajectory

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name
            benchmark_value: Target capability value (e.g., 100% for human-level)

        Returns:
            Dict with capability analysis
        """
        X, Y = self.loader.get_time_series(category, dataset, region)
        stats = self.analyzer.summary_statistics(category, dataset, region)

        result = {
            'dataset': dataset,
            'current_value': float(Y[-1]),
            'current_year': float(X[-1]),
            'improvement_rate': stats['cagr'],
            'years_of_data': len(X),
            'benchmark': benchmark_value
        }

        # Estimate when benchmark is reached
        if benchmark_value and Y[-1] < benchmark_value:
            # Project using CAGR
            cagr = stats['cagr']
            if cagr > 0:
                years_to_benchmark = np.log(benchmark_value / Y[-1]) / np.log(1 + cagr)
                result['benchmark_year'] = float(X[-1] + years_to_benchmark)
            else:
                result['benchmark_year'] = None
        elif benchmark_value and Y[-1] >= benchmark_value:
            # Already reached
            reached_idx = np.where(Y >= benchmark_value)[0]
            if len(reached_idx) > 0:
                result['benchmark_year'] = float(X[reached_idx[0]])

        return result


if __name__ == "__main__":
    # Example usage
    analysis = DisruptorAnalysis()

    # Analyze AI capability trajectory
    capability = analysis.analyze_capability_trajectory(
        'Artificial Intelligence',
        'Artificial_Intelligence_MMLU_Accuracy',
        benchmark_value=90.0
    )
    print("AI Capability Analysis (MMLU):")
    for key, value in capability.items():
        print(f"  {key}: {value}")

    # Forecast adoption milestones
    milestones = analysis.forecast_adoption_milestones(
        'Industrial Robot',
        'Industrial_Robot_Annual_Installation'
    )
    print("\nRobot Installation Milestones:")
    print(f"  Milestone years: {milestones['milestone_years']}")
