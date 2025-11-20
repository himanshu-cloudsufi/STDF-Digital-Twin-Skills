"""
Data Loader for Artificial Labour Analysis
Loads and queries AL_JSON.json dataset
"""

import json
import os
from typing import Dict, List, Optional, Tuple
import numpy as np


class ALDataLoader:
    """Load and query artificial labour data"""

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize data loader

        Args:
            data_path: Path to AL_JSON.json. If None, uses skill's data directory
        """
        if data_path is None:
            # Default to skill's data directory
            skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(skill_dir, 'data', 'AL_JSON.json')

        self.data_path = data_path
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load JSON data file"""
        with open(self.data_path, 'r') as f:
            return json.load(f)

    def get_categories(self) -> List[str]:
        """Get all top-level categories"""
        return list(self.data.keys())

    def get_datasets(self, category: str) -> List[str]:
        """
        Get all dataset names in a category

        Args:
            category: Category name (e.g., 'Artificial Intelligence')

        Returns:
            List of dataset names
        """
        if category not in self.data:
            raise ValueError(f"Category '{category}' not found")
        return list(self.data[category].keys())

    def get_metadata(self, category: str, dataset: str) -> Dict:
        """
        Get metadata for a dataset

        Args:
            category: Category name
            dataset: Dataset name

        Returns:
            Metadata dictionary
        """
        if category not in self.data:
            raise ValueError(f"Category '{category}' not found")
        if dataset not in self.data[category]:
            raise ValueError(f"Dataset '{dataset}' not found in '{category}'")

        return self.data[category][dataset].get('metadata', {})

    def get_time_series(
        self,
        category: str,
        dataset: str,
        region: str = 'Global'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get time series data (X, Y) for a dataset

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name (default: 'Global')

        Returns:
            Tuple of (years, values) as numpy arrays
        """
        if category not in self.data:
            raise ValueError(f"Category '{category}' not found")
        if dataset not in self.data[category]:
            raise ValueError(f"Dataset '{dataset}' not found")

        regions_data = self.data[category][dataset].get('regions', {})
        if region not in regions_data:
            available = list(regions_data.keys())
            raise ValueError(f"Region '{region}' not found. Available: {available}")

        region_data = regions_data[region]
        X = np.array([float(x) for x in region_data['X']])
        Y = np.array(region_data['Y'])

        return X, Y

    def get_regions(self, category: str, dataset: str) -> List[str]:
        """
        Get available regions for a dataset

        Args:
            category: Category name
            dataset: Dataset name

        Returns:
            List of region names
        """
        if category not in self.data:
            raise ValueError(f"Category '{category}' not found")
        if dataset not in self.data[category]:
            raise ValueError(f"Dataset '{dataset}' not found")

        return list(self.data[category][dataset].get('regions', {}).keys())

    def search_datasets(self, keyword: str) -> List[Dict]:
        """
        Search for datasets containing keyword

        Args:
            keyword: Search term (case-insensitive)

        Returns:
            List of dicts with category, dataset, and metadata
        """
        results = []
        keyword_lower = keyword.lower()

        for category in self.data:
            for dataset in self.data[category]:
                if keyword_lower in dataset.lower():
                    results.append({
                        'category': category,
                        'dataset': dataset,
                        'metadata': self.get_metadata(category, dataset)
                    })

        return results

    def get_latest_value(
        self,
        category: str,
        dataset: str,
        region: str = 'Global'
    ) -> Tuple[float, float]:
        """
        Get the most recent (year, value) pair

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name

        Returns:
            Tuple of (latest_year, latest_value)
        """
        X, Y = self.get_time_series(category, dataset, region)
        return X[-1], Y[-1]

    def get_date_range(
        self,
        category: str,
        dataset: str,
        region: str = 'Global'
    ) -> Tuple[float, float]:
        """
        Get the (min_year, max_year) for a dataset

        Args:
            category: Category name
            dataset: Dataset name
            region: Region name

        Returns:
            Tuple of (min_year, max_year)
        """
        X, Y = self.get_time_series(category, dataset, region)
        return X[0], X[-1]

    def summary(self) -> str:
        """
        Generate a summary of available data

        Returns:
            Formatted string with data overview
        """
        lines = ["Artificial Labour Data Summary", "=" * 40, ""]

        for category in self.get_categories():
            datasets = self.get_datasets(category)
            lines.append(f"{category}: {len(datasets)} datasets")
            for ds in datasets[:3]:
                lines.append(f"  - {ds}")
            if len(datasets) > 3:
                lines.append(f"  ... and {len(datasets) - 3} more")
            lines.append("")

        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    loader = ALDataLoader()
    print(loader.summary())

    # Example: Get AI MMLU accuracy
    X, Y = loader.get_time_series('Artificial Intelligence', 'Artificial_Intelligence_MMLU_Accuracy')
    print(f"\nMMLU Accuracy over time:")
    for year, acc in zip(X, Y):
        print(f"  {int(year)}: {acc}%")
