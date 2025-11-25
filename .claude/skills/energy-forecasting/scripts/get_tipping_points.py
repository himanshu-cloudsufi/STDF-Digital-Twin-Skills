#!/usr/bin/env python3
"""
Simple script to extract SWB vs Coal tipping points for all regions
"""

import sys
import os

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from cost_analysis import CostAnalyzer
from data_loader import DataLoader
import json

# Load configuration
skill_dir = os.path.dirname(scripts_dir)
config_path = os.path.join(skill_dir, 'config.json')
with open(config_path) as f:
    config = json.load(f)

# Initialize components
data_loader = DataLoader()  # Uses default data directory
cost_analyzer = CostAnalyzer(config, data_loader)

regions = ["China", "USA", "Europe", "Germany", "Rest_of_World"]

print("=" * 70)
print("SWB vs Coal Tipping Points by Region")
print("=" * 70)
print()

for region in regions:
    try:
        # Get cost forecasts
        cost_forecasts = cost_analyzer.forecast_cost_curves(region, 2040)

        # Find tipping points
        tipping_points = cost_analyzer.find_tipping_points(cost_forecasts)

        tipping_vs_coal = tipping_points.get('tipping_vs_coal', 'Not found')
        tipping_vs_gas = tipping_points.get('tipping_vs_gas', 'Not found')
        overall_tipping = tipping_points.get('tipping_overall', 'Not found')

        print(f"{region}:")
        print(f"  SWB vs Coal: {tipping_vs_coal}")
        print(f"  SWB vs Gas:  {tipping_vs_gas}")
        print(f"  Overall:     {overall_tipping}")
        print()

    except Exception as e:
        print(f"{region}: ERROR - {e}")
        print()

print("=" * 70)
print()
print("Note: The tipping point is the year when SWB stack cost")
print("(MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE) becomes less than")
print("the incumbent technology (Coal or Gas LCOE).")
print("=" * 70)
