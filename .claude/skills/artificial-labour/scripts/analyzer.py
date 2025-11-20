"""
Analyzer for Artificial Labour Trends
Performs trend analysis, growth rate calculations, and statistical summaries
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
from scipy import stats
from data_loader import ALDataLoader


class ALAnalyzer:
    """Analyze artificial labour trends and patterns"""

    def __init__(self, data_loader: Optional[ALDataLoader] = None):
        """
        Initialize analyzer

        Args:
            data_loader: ALDataLoader instance. If None, creates new one.
        """
        self.loader = data_loader if data_loader else ALDataLoader()

    def calculate_cagr(
        self,
        category: str,
        dataset: str,
        region: str = 'Global',
        start_year: Optional[float] = None,
        end_year: Optional[float] = None
    ) -> float:
        """
        Calculate Compound Annual Growth Rate

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name
            start_year: Start year (None = first available)
            end_year: End year (None = last available)

        Returns:
            CAGR as decimal (e.g., 0.25 = 25% growth)
        """
        X, Y = self.loader.get_time_series(category, dataset, region)

        # Filter by date range if specified
        if start_year is not None:
            mask = X >= start_year
            X, Y = X[mask], Y[mask]
        if end_year is not None:
            mask = X <= end_year
            X, Y = X[mask], Y[mask]

        if len(X) < 2:
            raise ValueError("Need at least 2 data points to calculate CAGR")

        n_years = X[-1] - X[0]
        cagr = (Y[-1] / Y[0]) ** (1 / n_years) - 1

        return cagr

    def calculate_growth_rate_series(
        self,
        category: str,
        dataset: str,
        region: str = 'Global'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate year-over-year growth rates

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name

        Returns:
            Tuple of (years, growth_rates) - years array is shortened by 1
        """
        X, Y = self.loader.get_time_series(category, dataset, region)

        if len(X) < 2:
            raise ValueError("Need at least 2 data points")

        growth_rates = np.diff(Y) / Y[:-1]
        years = X[1:]  # Growth rate for year N is based on change from N-1 to N

        return years, growth_rates

    def fit_trend_line(
        self,
        category: str,
        dataset: str,
        region: str = 'Global',
        method: str = 'linear'
    ) -> Dict:
        """
        Fit a trend line to the data

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name
            method: 'linear' or 'log' (for exponential trends)

        Returns:
            Dict with slope, intercept, r_squared, and trend description
        """
        X, Y = self.loader.get_time_series(category, dataset, region)

        if method == 'log':
            # Log transform for exponential trends
            Y_log = np.log(Y)
            slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y_log)
            r_squared = r_value ** 2

            return {
                'method': 'exponential',
                'slope': slope,  # Growth rate in log space
                'intercept': intercept,
                'r_squared': r_squared,
                'p_value': p_value,
                'description': f'Exponential: Y = exp({intercept:.2f} + {slope:.2f}*X)'
            }
        else:
            # Linear trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
            r_squared = r_value ** 2

            return {
                'method': 'linear',
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_squared,
                'p_value': p_value,
                'description': f'Linear: Y = {intercept:.2f} + {slope:.2f}*X'
            }

    def extrapolate(
        self,
        category: str,
        dataset: str,
        target_year: float,
        region: str = 'Global',
        method: str = 'cagr'
    ) -> float:
        """
        Extrapolate to a future year

        Args:
            category: Category name
            dataset: Dataset name
            target_year: Year to extrapolate to
            region: Region name
            method: 'cagr' (compound growth) or 'linear' (linear trend)

        Returns:
            Extrapolated value
        """
        X, Y = self.loader.get_time_series(category, dataset, region)
        last_year = X[-1]
        last_value = Y[-1]

        if target_year <= last_year:
            # Interpolate if within data range
            return np.interp(target_year, X, Y)

        years_ahead = target_year - last_year

        if method == 'cagr':
            cagr = self.calculate_cagr(category, dataset, region)
            return last_value * (1 + cagr) ** years_ahead
        elif method == 'linear':
            trend = self.fit_trend_line(category, dataset, region, method='linear')
            return trend['intercept'] + trend['slope'] * target_year
        else:
            raise ValueError(f"Unknown method: {method}")

    def detect_inflection_point(
        self,
        category: str,
        dataset: str,
        region: str = 'Global'
    ) -> Optional[float]:
        """
        Detect inflection point in S-curve adoption

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name

        Returns:
            Year of inflection point, or None if not detected
        """
        X, Y = self.loader.get_time_series(category, dataset, region)

        if len(X) < 5:
            return None

        # Calculate second derivative (acceleration)
        first_diff = np.diff(Y)
        second_diff = np.diff(first_diff)

        # Find where second derivative changes sign (from positive to negative)
        sign_changes = np.where(np.diff(np.sign(second_diff)))[0]

        if len(sign_changes) > 0:
            # Return year closest to middle of dataset (most likely inflection)
            inflection_idx = sign_changes[len(sign_changes) // 2] + 2  # +2 due to double diff
            return X[inflection_idx]

        return None

    def compare_datasets(
        self,
        dataset1: Tuple[str, str],
        dataset2: Tuple[str, str],
        region: str = 'Global'
    ) -> Dict:
        """
        Compare two datasets

        Args:
            dataset1: Tuple of (category, dataset)
            dataset2: Tuple of (category, dataset)
            region: Region name

        Returns:
            Dict with comparison metrics
        """
        X1, Y1 = self.loader.get_time_series(dataset1[0], dataset1[1], region)
        X2, Y2 = self.loader.get_time_series(dataset2[0], dataset2[1], region)

        cagr1 = self.calculate_cagr(dataset1[0], dataset1[1], region)
        cagr2 = self.calculate_cagr(dataset2[0], dataset2[1], region)

        return {
            'dataset1': {
                'name': dataset1[1],
                'latest_value': Y1[-1],
                'latest_year': X1[-1],
                'cagr': cagr1
            },
            'dataset2': {
                'name': dataset2[1],
                'latest_value': Y2[-1],
                'latest_year': X2[-1],
                'cagr': cagr2
            },
            'relative_cagr': cagr1 / cagr2 if cagr2 != 0 else float('inf')
        }

    def summary_statistics(
        self,
        category: str,
        dataset: str,
        region: str = 'Global'
    ) -> Dict:
        """
        Calculate summary statistics for a dataset

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name

        Returns:
            Dict with various statistics
        """
        X, Y = self.loader.get_time_series(category, dataset, region)
        metadata = self.loader.get_metadata(category, dataset)

        cagr = self.calculate_cagr(category, dataset, region)
        trend = self.fit_trend_line(category, dataset, region, method='log')

        return {
            'dataset': dataset,
            'category': category,
            'region': region,
            'units': metadata.get('units', 'N/A'),
            'source': metadata.get('source', 'N/A'),
            'date_range': (float(X[0]), float(X[-1])),
            'num_points': len(X),
            'latest_value': float(Y[-1]),
            'min_value': float(Y.min()),
            'max_value': float(Y.max()),
            'mean_value': float(Y.mean()),
            'median_value': float(np.median(Y)),
            'cagr': float(cagr),
            'total_growth': float((Y[-1] / Y[0] - 1) * 100),  # Percentage
            'trend_r_squared': float(trend['r_squared'])
        }


if __name__ == "__main__":
    # Example usage
    analyzer = ALAnalyzer()

    # Analyze MMLU accuracy
    stats = analyzer.summary_statistics(
        'Artificial Intelligence',
        'Artificial_Intelligence_MMLU_Accuracy'
    )
    print("MMLU Accuracy Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Calculate CAGR
    cagr = analyzer.calculate_cagr(
        'Artificial Intelligence',
        'Artificial_Intelligence_Traning_Dataset_Size'
    )
    print(f"\nTraining Data Size CAGR: {cagr*100:.1f}%")

    # Extrapolate
    future_value = analyzer.extrapolate(
        'Artificial Intelligence',
        'Artificial_Intelligence_MMLU_Accuracy',
        2026
    )
    print(f"Projected MMLU Accuracy in 2026: {future_value:.1f}%")
