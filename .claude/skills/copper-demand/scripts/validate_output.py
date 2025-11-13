#!/usr/bin/env python3
"""
Validate forecast output for data quality and consistency
"""

import json
import sys
import pandas as pd
from pathlib import Path


def validate_output(filepath, config_path='config.json'):
    """
    Validate forecast output file

    Checks:
    - Reconciliation (sum of segments = total)
    - Segment shares within expected ranges
    - No negative values
    - Growth rates within bounds
    - Data completeness
    """
    errors = []
    warnings = []

    # Load config for validation rules
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        validation_rules = config.get('validation_rules', {})
    except:
        validation_rules = {}
        warnings.append("Could not load validation rules from config")

    # Load data
    try:
        if filepath.endswith('.csv'):
            data = pd.read_csv(filepath)
        elif filepath.endswith('.json'):
            data = pd.read_json(filepath)
        else:
            return False, "File must be .csv or .json"
    except Exception as e:
        return False, f"Could not read file: {e}"

    # Check required columns
    required_cols = ['year', 'total_demand', 'auto_total', 'construction_total',
                    'grid_generation_oem', 'grid_td_total', 'industrial_total',
                    'electronics_total', 'other_uses']

    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, "\n".join(errors)

    # Validate each year
    for idx, row in data.iterrows():
        year = row['year']

        # 1. Reconciliation check
        segments_sum = (row['auto_total'] +
                       row['grid_generation_oem'] +
                       row['construction_total'] +
                       row['grid_td_total'] +
                       row['industrial_total'] +
                       row['electronics_total'] +
                       row['other_uses'])

        total = row['total_demand']
        reconciliation_error = abs(segments_sum - total) / total if total > 0 else 0

        if reconciliation_error > 0.001:  # 0.1% tolerance
            errors.append(f"Year {year}: Reconciliation error {reconciliation_error:.4%} (segments sum: {segments_sum:,.0f}, total: {total:,.0f})")

        # 2. Check for negative values
        for col in required_cols[1:]:  # Skip 'year'
            if row[col] < 0:
                errors.append(f"Year {year}: Negative value in {col}: {row[col]}")

        # 3. Check segment shares
        if total > 0:
            auto_share = row['auto_total'] / total
            if 'share_transport_calc' in data.columns:
                if abs(auto_share - row['share_transport_calc']) > 0.01:
                    warnings.append(f"Year {year}: Transport share mismatch (calculated: {auto_share:.3f}, reported: {row['share_transport_calc']:.3f})")

        # 4. Check for unrealistic values
        if total > 100_000_000:  # 100 Mt seems unrealistic
            warnings.append(f"Year {year}: Very high total demand {total:,.0f} tonnes")

        if total < 10_000_000 and year > 2020:  # 10 Mt seems too low
            warnings.append(f"Year {year}: Very low total demand {total:,.0f} tonnes")

    # 5. Check growth rates
    if len(data) > 1:
        data_sorted = data.sort_values('year')
        for i in range(1, len(data_sorted)):
            prev_total = data_sorted.iloc[i-1]['total_demand']
            curr_total = data_sorted.iloc[i]['total_demand']

            if prev_total > 0:
                growth = (curr_total - prev_total) / prev_total

                # Check against growth guards if available
                max_growth = validation_rules.get('growth_guards', {}).get('max_yoy_growth_pct', 50) / 100
                max_decline = validation_rules.get('growth_guards', {}).get('max_yoy_decline_pct', -30) / 100

                if growth > max_growth:
                    warnings.append(f"Year {data_sorted.iloc[i]['year']}: High growth {growth:.1%} (max: {max_growth:.1%})")

                if growth < max_decline:
                    warnings.append(f"Year {data_sorted.iloc[i]['year']}: Large decline {growth:.1%} (min: {max_decline:.1%})")

    # 6. Check data completeness
    if len(data) < 20:
        warnings.append(f"Short forecast period: only {len(data)} years")

    # Summary
    print("=" * 60)
    print(f"VALIDATION REPORT: {Path(filepath).name}")
    print("=" * 60)

    if not errors and not warnings:
        print("✓ All validation checks passed")
        print(f"\nSummary Statistics:")
        print(f"  Years: {int(data['year'].min())} - {int(data['year'].max())}")
        print(f"  Total Demand Range: {data['total_demand'].min():,.0f} - {data['total_demand'].max():,.0f} tonnes")
        print(f"  CAGR: {((data['total_demand'].iloc[-1] / data['total_demand'].iloc[0]) ** (1/len(data)) - 1):.2%}")
        if 'share_transport_calc' in data.columns:
            print(f"  Transport Share Range: {data['share_transport_calc'].min():.1%} - {data['share_transport_calc'].max():.1%}")
        return True, "Validation passed"

    if errors:
        print(f"\n✗ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print(f"\n⚠ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    print("\n" + "=" * 60)

    if errors:
        return False, f"Validation failed with {len(errors)} error(s)"
    else:
        return True, f"Validation passed with {len(warnings)} warning(s)"


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <output_file> [config_file]")
        print("\nExample:")
        print("  python validate_output.py output/copper_demand_Global_baseline_2045.csv")
        print("  python validate_output.py output/forecast.json config.json")
        return 1

    filepath = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else 'config.json'

    valid, message = validate_output(filepath, config_path)

    return 0 if valid else 1


if __name__ == '__main__':
    sys.exit(main())
