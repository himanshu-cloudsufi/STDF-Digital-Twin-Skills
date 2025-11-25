#!/usr/bin/env python3
"""
Data inspection script to understand what's in the data files
"""

import json
from pathlib import Path


def inspect_generation_data():
    """Inspect what's actually in the data files"""
    skill_dir = Path(__file__).parent.parent
    data_path = skill_dir / 'data' / 'Energy_Generation.json'

    with open(data_path, 'r') as f:
        data = json.load(f)

    gen_data = data.get('Energy Generation', {})

    # Check what technologies exist
    print("=" * 70)
    print("AVAILABLE METRICS IN Energy_Generation.json")
    print("=" * 70)

    lcoe_metrics = []
    generation_metrics = []
    capacity_metrics = []

    for key in sorted(gen_data.keys()):
        if 'LCOE' in key:
            lcoe_metrics.append(key)
        elif 'Generation' in key:
            generation_metrics.append(key)
        elif 'Capacity' in key:
            capacity_metrics.append(key)

    print("\n--- LCOE Metrics ---")
    for metric in lcoe_metrics:
        print(f"\n{metric}:")
        if 'regions' in gen_data[metric]:
            regions = list(gen_data[metric]['regions'].keys())
            print(f"  Regions: {', '.join(regions)}")

            # Check sample data for each region
            for region in ['China', 'USA', 'Europe', 'Global']:
                if region in gen_data[metric]['regions']:
                    region_data = gen_data[metric]['regions'][region]
                    if 'X' in region_data and 'Y' in region_data:
                        years = region_data['X']
                        values = region_data['Y']
                        if len(years) > 0:
                            print(f"  {region}: {len(years)} data points, "
                                  f"years {min(years)}-{max(years)}, "
                                  f"values {min(values):.1f}-{max(values):.1f}")
                            # Show 2020 value if available
                            if 2020 in years:
                                idx = years.index(2020)
                                print(f"    2020 value: {values[idx]:.1f}")

    print("\n--- Generation Metrics ---")
    for metric in generation_metrics[:10]:  # Show first 10
        if 'regions' in gen_data[metric]:
            regions = list(gen_data[metric]['regions'].keys())
            print(f"{metric}: {', '.join(regions)}")

    print("\n--- Capacity Metrics ---")
    for metric in capacity_metrics[:10]:  # Show first 10
        if 'regions' in gen_data[metric]:
            regions = list(gen_data[metric]['regions'].keys())
            print(f"{metric}: {', '.join(regions)}")

    # Specific check for China 2020 generation mix
    print("\n" + "=" * 70)
    print("CHINA 2020 GENERATION MIX CHECK")
    print("=" * 70)

    china_gen_2020 = {}
    for tech_key in ['Coal_Annual_Power_Generation',
                     'Natural_Gas_Annual_Power_Generation',
                     'Nuclear_Annual_Power_Generation',
                     'Hydro_Annual_Power_Generation',
                     'Solar_Annual_Power_Generation',
                     'Wind_Annual_Power_Generation']:
        if tech_key in gen_data:
            regions_data = gen_data[tech_key].get('regions', {})
            if 'China' in regions_data:
                region_data = regions_data['China']
                if 'X' in region_data and 'Y' in region_data:
                    years = region_data['X']
                    values = region_data['Y']
                    if 2020 in years:
                        idx = years.index(2020)
                        china_gen_2020[tech_key] = values[idx]

    if china_gen_2020:
        total = sum(china_gen_2020.values())
        print("\nChina 2020 generation:")
        for tech, value in sorted(china_gen_2020.items()):
            tech_name = tech.replace('_Annual_Power_Generation', '')
            share = (value / total * 100) if total > 0 else 0
            print(f"  {tech_name:20s}: {value:8.1f} TWh ({share:5.1f}%)")
        print(f"  {'Total':20s}: {total:8.1f} TWh")

        # Expected values
        print("\nExpected China 2020:")
        print("  Coal: ~65%, Gas: ~5%, Hydro: ~18%, Wind: ~9%, Solar: ~3%")


if __name__ == "__main__":
    inspect_generation_data()
