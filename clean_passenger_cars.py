#!/usr/bin/env python3
"""
Clean Passenger_Cars.json by removing all data after 2025.

This script truncates forecast data in the curves catalog to keep only
historical/baseline data through 2025, removing projections for 2026-2040.
"""

import json
import sys
from pathlib import Path


def truncate_timeseries(region_data, cutoff_year=2025):
    """
    Truncate X and Y arrays at cutoff_year.

    Args:
        region_data: Dictionary with 'X' and 'Y' keys
        cutoff_year: Maximum year to keep (inclusive)

    Returns:
        True if data was truncated, False otherwise
    """
    if 'X' not in region_data or 'Y' not in region_data:
        return False

    years = region_data['X']
    values = region_data['Y']

    if not years:
        return False

    # Find cutoff index
    cutoff_idx = None
    for i, year in enumerate(years):
        if year > cutoff_year:
            cutoff_idx = i
            break

    # Truncate if needed
    if cutoff_idx is not None:
        original_len = len(years)
        region_data['X'] = years[:cutoff_idx]
        region_data['Y'] = values[:cutoff_idx]
        new_len = len(region_data['X'])
        print(f"    Truncated from {original_len} to {new_len} points (was {years[0]}-{years[-1]}, now {region_data['X'][0]}-{region_data['X'][-1]})")
        return True

    return False


def clean_metric_regions(metric_data, cutoff_year=2025):
    """
    Clean all regions within a metric.

    Args:
        metric_data: Metric dictionary containing 'regions' key
        cutoff_year: Maximum year to keep

    Returns:
        True if any region was cleaned
    """
    if 'regions' not in metric_data:
        return False

    any_cleaned = False
    regions = metric_data['regions']

    for region_name, region_data in regions.items():
        # Handle nested structures (like China's BEV data with 'standard' and 'TaaSAdj')
        if isinstance(region_data, dict):
            if 'X' in region_data and 'Y' in region_data:
                # Direct X/Y structure
                if truncate_timeseries(region_data, cutoff_year):
                    if not any_cleaned:
                        any_cleaned = True
                    print(f"  Region: {region_name}")
            else:
                # Check for nested structures
                for sub_key, sub_data in region_data.items():
                    if isinstance(sub_data, dict) and 'X' in sub_data and 'Y' in sub_data:
                        if truncate_timeseries(sub_data, cutoff_year):
                            if not any_cleaned:
                                any_cleaned = True
                            print(f"  Region: {region_name} (sub-key: {sub_key})")

    return any_cleaned


def main():
    # File paths
    input_file = Path('.claude/skills/demand-forecasting/data/Passenger_Cars.json')
    backup_file = input_file.with_suffix('.json.backup2')

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)

    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Create backup
    print(f"Creating backup at {backup_file}...")
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Clean the data
    print("\nCleaning data (removing years > 2025)...")
    print("=" * 70)

    metrics_cleaned = 0

    for entity_name, entity_data in data.items():
        print(f"\nProcessing entity: {entity_name}")

        for metric_name, metric_data in entity_data.items():
            if clean_metric_regions(metric_data, cutoff_year=2025):
                print(f"Metric: {metric_name}")
                metrics_cleaned += 1

    print("\n" + "=" * 70)
    print(f"\nCleaned {metrics_cleaned} metrics")

    # Write cleaned data
    print(f"\nWriting cleaned data to {input_file}...")
    with open(input_file, 'w') as f:
        json.dump(data, f, indent=2)

    print("\n✓ Successfully cleaned Passenger_Cars.json")
    print(f"✓ Original backed up to {backup_file}")

    # Validation
    print("\nValidating...")
    max_year_found = 0
    issues = []

    for entity_name, entity_data in data.items():
        for metric_name, metric_data in entity_data.items():
            if 'regions' in metric_data:
                for region_name, region_data in metric_data['regions'].items():
                    # Check direct X/Y
                    if 'X' in region_data and region_data['X']:
                        region_max = max(region_data['X'])
                        if region_max > 2025:
                            issues.append(f"{metric_name} -> {region_name}: {region_max}")
                        max_year_found = max(max_year_found, region_max)

                    # Check nested structures
                    for sub_key, sub_data in region_data.items():
                        if isinstance(sub_data, dict) and 'X' in sub_data and sub_data['X']:
                            sub_max = max(sub_data['X'])
                            if sub_max > 2025:
                                issues.append(f"{metric_name} -> {region_name}.{sub_key}: {sub_max}")
                            max_year_found = max(max_year_found, sub_max)

    if not issues:
        print(f"✓ Validation passed: Maximum year in file is {max_year_found}")
    else:
        print(f"✗ Validation failed: Found {len(issues)} regions with data beyond 2025:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == '__main__':
    main()
