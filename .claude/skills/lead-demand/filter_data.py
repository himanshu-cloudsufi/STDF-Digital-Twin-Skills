#!/usr/bin/env python3
"""
Script to filter time series data to remove years after 2024.
Keeps only historical data (through 2024).
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
                print(f"  Filtered {years_removed} data points after {max_year}")
        else:
            # Recursively process nested dictionaries
            for key, value in data.items():
                data[key] = filter_timeseries_data(value, max_year)

    return data


def process_json_file(file_path, max_year=2024):
    """
    Process a single JSON file to filter time series data.

    Args:
        file_path: Path to the JSON file
        max_year: Maximum year to keep (inclusive)
    """
    print(f"\nProcessing: {file_path.name}")

    # Read the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Filter the data
    filtered_data = filter_timeseries_data(data, max_year)

    # Write back to file with proper formatting
    with open(file_path, 'w') as f:
        json.dump(filtered_data, f, indent=2)

    print(f"  ✓ Completed: {file_path.name}")


def main():
    # Define the data directory
    data_dir = Path(__file__).parent / 'data'

    # List of data files to process
    data_files = [
        'Lead.json',
        'Two_Wheeler.json',
        'Three_Wheeler.json',
        'Passenger_Cars.json',
        'Commercial_Vehicle.json'
    ]

    max_year = 2024
    print(f"Filtering all data files to keep only years through {max_year}")
    print("=" * 60)

    # Process each file
    for filename in data_files:
        file_path = data_dir / filename
        if file_path.exists():
            process_json_file(file_path, max_year)
        else:
            print(f"  ⚠ Warning: {filename} not found")

    print("\n" + "=" * 60)
    print("✓ All files processed successfully!")


if __name__ == '__main__':
    main()
