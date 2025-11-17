#!/usr/bin/env python3
"""
Universal script to filter time series data in skill JSON files to remove years after 2024.
"""

import json
import sys
from pathlib import Path


def filter_timeseries_data(data, max_year=2024):
    """
    Recursively filters time series data to keep only years <= max_year.

    Args:
        data: Dictionary containing the JSON data structure
        max_year: Maximum year to keep (inclusive)

    Returns:
        Filtered data dictionary
    """
    if isinstance(data, dict):
        # Check if this dict has X and Y arrays (time series data)
        if 'X' in data and 'Y' in data and isinstance(data['X'], list) and isinstance(data['Y'], list):
            # Filter X and Y arrays
            x_array = data['X']
            y_array = data['Y']

            # Find indices where X <= max_year
            filtered_indices = [i for i, year in enumerate(x_array) if year <= max_year]

            # Create filtered arrays
            data['X'] = [x_array[i] for i in filtered_indices]
            data['Y'] = [y_array[i] for i in filtered_indices]

            years_removed = len(x_array) - len(data['X'])
            if years_removed > 0:
                return years_removed
        else:
            # Recursively process nested dictionaries
            total_removed = 0
            for key, value in data.items():
                result = filter_timeseries_data(value, max_year)
                if isinstance(result, int):
                    total_removed += result
            return total_removed if total_removed > 0 else None

    return None


def process_json_file(file_path, max_year=2024):
    """
    Process a single JSON file to filter time series data.

    Args:
        file_path: Path to the JSON file
        max_year: Maximum year to keep (inclusive)
    """
    # Read the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Filter the data
    result = filter_timeseries_data(data, max_year)

    # Write back to file with proper formatting
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    return result


def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("Usage: python3 filter_skill_data.py <skill_name>")
        print("Example: python3 filter_skill_data.py copper-demand")
        sys.exit(1)

    skill_name = sys.argv[1]
    skills_dir = Path(__file__).parent
    skill_dir = skills_dir / skill_name
    data_dir = skill_dir / 'data'

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    # Get all JSON files
    json_files = list(data_dir.glob('*.json'))

    if not json_files:
        print(f"No JSON files found in {data_dir}")
        sys.exit(1)

    max_year = 2024
    print(f"Filtering {skill_name} data files to keep only years through {max_year}")
    print("=" * 60)

    # Process each file
    total_files = 0
    total_metrics = 0

    for file_path in json_files:
        print(f"\nProcessing: {file_path.name}")
        result = process_json_file(file_path, max_year)
        if result:
            print(f"  ✓ Filtered {result} data points after {max_year}")
            total_metrics += 1
        else:
            print(f"  ✓ No data after {max_year}")
        total_files += 1

    print("\n" + "=" * 60)
    print(f"✓ Processed {total_files} files in {skill_name}")
    print(f"✓ Modified {total_metrics} files with data after {max_year}")


if __name__ == '__main__':
    main()
