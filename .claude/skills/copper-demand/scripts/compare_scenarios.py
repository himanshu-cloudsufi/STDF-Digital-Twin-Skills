#!/usr/bin/env python3
"""
Compare multiple scenario forecast outputs
"""

import json
import sys
import pandas as pd
from pathlib import Path


def compare_scenarios(filepaths, output_format='table'):
    """
    Compare multiple scenario outputs

    Args:
        filepaths: List of paths to forecast output files
        output_format: 'table' or 'json'
    """
    # Load all scenarios
    scenarios = {}
    for filepath in filepaths:
        # Extract scenario name from filename
        # Format: copper_demand_{region}_{scenario}_{year}.{ext}
        filename = Path(filepath).stem
        parts = filename.split('_')
        if len(parts) >= 4:
            scenario_name = parts[3]  # Get scenario from filename
        else:
            scenario_name = Path(filepath).stem

        try:
            if filepath.endswith('.csv'):
                data = pd.read_csv(filepath)
            elif filepath.endswith('.json'):
                data = pd.read_json(filepath)
            else:
                print(f"Skipping {filepath}: unsupported format")
                continue

            scenarios[scenario_name] = data
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            continue

    if len(scenarios) < 2:
        print("Need at least 2 scenarios to compare")
        return 1

    # Extract key years for comparison (use available years from data)
    # Get all unique years across scenarios
    all_years = set()
    for data in scenarios.values():
        all_years.update(data['year'].tolist())

    # Select key milestone years for comparison (every 5 years, up to max available)
    max_year = max(all_years)
    min_year = min(all_years)
    comparison_years = [y for y in range(min_year, max_year + 1, 5) if y in all_years]

    # If we have fewer than 5 comparison years, add the max year
    if len(comparison_years) < 5 and max_year not in comparison_years:
        comparison_years.append(max_year)
    comparison_years = sorted(comparison_years)

    # Build comparison data
    comparison = []
    for year in comparison_years:
        year_data = {'year': year}

        for scenario_name, data in scenarios.items():
            year_row = data[data['year'] == year]
            if len(year_row) == 0:
                continue

            row = year_row.iloc[0]
            year_data[f'{scenario_name}_total'] = row['total_demand']
            year_data[f'{scenario_name}_auto'] = row['auto_total']
            year_data[f'{scenario_name}_auto_share'] = row['auto_total'] / row['total_demand']

            if 'auto_bev' in row:
                year_data[f'{scenario_name}_ev'] = row['auto_bev']
                year_data[f'{scenario_name}_ev_share'] = row['auto_bev'] / row['total_demand']

            if 'grid_gen_wind' in row and 'grid_gen_solar' in row:
                green_copper = row['auto_bev'] + row['grid_gen_wind'] + row['grid_gen_solar']
                year_data[f'{scenario_name}_green'] = green_copper
                year_data[f'{scenario_name}_green_share'] = green_copper / row['total_demand']

        comparison.append(year_data)

    # Print comparison
    if output_format == 'table':
        print_table_comparison(scenarios, comparison)
    elif output_format == 'json':
        print(json.dumps(comparison, indent=2))

    return 0


def print_table_comparison(scenarios, comparison):
    """Print formatted table comparison"""
    scenario_names = list(scenarios.keys())
    baseline_name = scenario_names[0]  # Use first as baseline for % comparisons

    print("\n" + "=" * 80)
    print("SCENARIO COMPARISON REPORT")
    print("=" * 80)

    # Summary table
    print("\nTotal Copper Demand (Million Tonnes)")
    print("-" * 80)
    print(f"{'Year':<8}", end='')
    for name in scenario_names:
        print(f"{name:<15}", end='')
    print()

    for row in comparison:
        year = row['year']
        print(f"{year:<8}", end='')
        for name in scenario_names:
            total_key = f'{name}_total'
            if total_key in row:
                value = row[total_key] / 1_000_000  # Convert to Mt
                print(f"{value:>14.1f}", end='')
            else:
                print(f"{'N/A':>14}", end='')
        print()

    # Difference from baseline
    print(f"\nDifference from {baseline_name} (%)")
    print("-" * 80)
    print(f"{'Year':<8}", end='')
    for name in scenario_names:
        if name != baseline_name:
            print(f"{name:<15}", end='')
    print()

    for row in comparison:
        year = row['year']
        baseline_key = f'{baseline_name}_total'
        if baseline_key not in row:
            continue

        baseline_value = row[baseline_key]
        print(f"{year:<8}", end='')

        for name in scenario_names:
            if name == baseline_name:
                continue
            total_key = f'{name}_total'
            if total_key in row:
                diff = (row[total_key] - baseline_value) / baseline_value * 100
                print(f"{diff:>+14.1f}", end='')
            else:
                print(f"{'N/A':>14}", end='')
        print()

    # Green copper comparison
    print("\nGreen Copper (EV + Solar + Wind) Share of Total (%)")
    print("-" * 80)
    print(f"{'Year':<8}", end='')
    for name in scenario_names:
        print(f"{name:<15}", end='')
    print()

    for row in comparison:
        year = row['year']
        print(f"{year:<8}", end='')
        for name in scenario_names:
            share_key = f'{name}_green_share'
            if share_key in row:
                value = row[share_key] * 100
                print(f"{value:>14.1f}", end='')
            else:
                print(f"{'N/A':>14}", end='')
        print()

    # Automotive share comparison
    print("\nAutomotive Share of Total (%)")
    print("-" * 80)
    print(f"{'Year':<8}", end='')
    for name in scenario_names:
        print(f"{name:<15}", end='')
    print()

    for row in comparison:
        year = row['year']
        print(f"{year:<8}", end='')
        for name in scenario_names:
            share_key = f'{name}_auto_share'
            if share_key in row:
                value = row[share_key] * 100
                print(f"{value:>14.1f}", end='')
            else:
                print(f"{'N/A':>14}", end='')
        print()

    print("\n" + "=" * 80)


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_scenarios.py <file1> <file2> [file3...] [--format table|json]")
        print("\nExample:")
        print("  python compare_scenarios.py output/copper_demand_Global_baseline_2040.csv \\")
        print("                              output/copper_demand_Global_accelerated_2040.csv")
        return 1

    # Parse arguments
    filepaths = []
    output_format = 'table'

    for arg in sys.argv[1:]:
        if arg == '--format':
            continue
        elif arg in ['table', 'json']:
            output_format = arg
        else:
            filepaths.append(arg)

    if len(filepaths) < 2:
        print("Error: Need at least 2 files to compare")
        return 1

    return compare_scenarios(filepaths, output_format)


if __name__ == '__main__':
    sys.exit(main())
