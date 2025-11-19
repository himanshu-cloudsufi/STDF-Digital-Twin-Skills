# Output Formats Reference - Energy Forecasting (SWB)

## File Naming

```
output/{Region}_{EndYear}.{format}

Examples:
- output/China_2040.csv
- output/USA_2040.json
- output/Global_2040.csv
```

## CSV Format

### Structure

| Column | Units | Description |
|--------|-------|-------------|
| Year | Integer | Forecast year |
| SWB_Generation | GWh | Total SWB generation (Solar + Wind + Battery) |
| Coal_Generation | GWh | Coal power generation |
| Gas_Generation | GWh | Natural gas generation |
| Non_SWB_Generation | GWh | Nuclear + Hydro + Other |
| Total_Demand | GWh | Total electricity demand/production |
| SWB_Share | Decimal | SWB share of total (0.0 to 1.0) |

### Example

```csv
Year,SWB_Generation,Coal_Generation,Gas_Generation,Non_SWB_Generation,Total_Demand,SWB_Share
2025,5000.0,10000.0,8000.0,3000.0,26000.0,0.192
2030,12000.0,6000.0,6000.0,3000.0,27000.0,0.444
2035,20000.0,3000.0,4000.0,3000.0,30000.0,0.667
2040,28000.0,1500.0,2000.0,3000.0,34500.0,0.812
```

## JSON Format

### Structure

```json
{
  "region": "China",
  "end_year": 2040,
  "cost_analysis": {
    "tipping_points": {
      "tipping_vs_coal": 2028,
      "tipping_vs_gas": 2026,
      "tipping_overall": 2026,
      "swb_stack_cost": {
        "years": [2025, 2026, ...],
        "costs": [85.2, 78.3, ...]
      }
    },
    "cost_forecasts": {
      "Solar_PV": {"years": [...], "costs": [...]},
      "Wind_Combined": {"years": [...], "costs": [...]},
      "Battery_Storage": {"years": [...], "costs": [...]},
      "Coal_Power": {"years": [...], "costs": [...]},
      "Natural_Gas_Power": {"years": [...], "costs": [...]}
    }
  },
  "capacity_forecasts": {
    "Solar_PV": {"years": [...], "capacity_gw": [...]},
    "Onshore_Wind": {"years": [...], "capacity_gw": [...]},
    "Offshore_Wind": {"years": [...], "capacity_gw": [...]},
    "Battery_Storage": {"years": [...], "capacity_gw": [...]}
  },
  "generation_forecasts": {
    "years": [2025, 2026, ...],
    "swb_total": [5000.0, 6200.0, ...],
    "coal": [10000.0, 9500.0, ...],
    "gas": [8000.0, 7800.0, ...],
    "non_swb": [3000.0, 3000.0, ...],
    "total_demand": [26000.0, 26500.0, ...],
    "by_technology": {
      "Solar_PV": [2000.0, 2500.0, ...],
      "Onshore_Wind": [2500.0, 3000.0, ...],
      "Offshore_Wind": [500.0, 700.0, ...],
      "Battery_Storage": [0.0, 0.0, ...]
    }
  },
  "displacement_timeline": {
    "swb_exceeds_coal": 2032,
    "swb_exceeds_gas": 2030,
    "swb_exceeds_all_fossil": 2035,
    "coal_95_percent_displaced": 2038,
    "gas_95_percent_displaced": 2036
  },
  "validation": {
    "energy_balance_valid": true,
    "message": "Energy balance validation passed"
  }
}
```

## Output Sections

### 1. Cost Analysis

**tipping_points**: Years when SWB becomes cheaper than incumbents
- `tipping_vs_coal`: SWB stack cost < Coal LCOE
- `tipping_vs_gas`: SWB stack cost < Gas LCOE
- `tipping_overall`: First tipping point (min of coal/gas)

**cost_forecasts**: LCOE and SCOE forecasts for all technologies
- Arrays of years and costs in $/MWh

### 2. Capacity Forecasts

Installed capacity in GW for each SWB component:
- Solar_PV, CSP (if included), Onshore_Wind, Offshore_Wind, Battery_Storage

### 3. Generation Forecasts

Annual electricity generation in GWh:
- **swb_total**: Sum of all SWB generation
- **coal**: Coal power generation
- **gas**: Natural gas generation
- **non_swb**: Nuclear + Hydro + Other
- **total_demand**: Total electricity demand
- **by_technology**: Breakdown by individual SWB technology

### 4. Displacement Timeline

Key milestone years:
- **swb_exceeds_coal**: SWB generation > Coal generation
- **swb_exceeds_gas**: SWB generation > Gas generation
- **swb_exceeds_all_fossil**: SWB generation > Coal + Gas
- **coal_95_percent_displaced**: Coal drops to 5% of peak
- **gas_95_percent_displaced**: Gas drops to 5% of peak

### 5. Validation

**energy_balance_valid**: Boolean indicating if energy balance check passed
**message**: Validation result message

## Global Aggregation (JSON only)

When forecasting Global region, JSON includes:
```json
{
  "region": "Global",
  "end_year": 2040,
  "generation_forecasts": {
    "years": [...],
    "swb_total": [...],
    "coal": [...],
    "gas": [...],
    "non_swb": [...],
    "total_demand": [...]
  },
  "note": "Aggregated from China, USA, Europe, Rest_of_World"
}
```

**Note**: Global aggregation sums regional forecasts (no cost analysis or capacity breakdown).

## Reading Outputs

### CSV (Python pandas)
```python
import pandas as pd
df = pd.read_csv("output/China_2040.csv")
print(df[["Year", "SWB_Generation", "SWB_Share"]])
```

### JSON (Python)
```python
import json
with open("output/China_2040.json") as f:
    result = json.load(f)

tipping = result["cost_analysis"]["tipping_points"]["tipping_overall"]
print(f"Tipping point: {tipping}")

years = result["generation_forecasts"]["years"]
swb_gen = result["generation_forecasts"]["swb_total"]
```

## Units Summary

| Metric | CSV Column / JSON Key | Units |
|--------|----------------------|-------|
| Generation | *_Generation, swb_total, coal, gas | GWh |
| Capacity | capacity_gw | GW |
| Costs | costs (in cost_forecasts) | $/MWh |
| Share | SWB_Share | Decimal (0.0-1.0) |
| Years | Year, years | Integer |
