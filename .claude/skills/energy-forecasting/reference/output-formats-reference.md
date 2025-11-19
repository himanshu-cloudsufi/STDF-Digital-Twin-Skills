# Output Formats Reference - Energy Forecasting (SWB)

## File Naming

```
output/{Region}_{EndYear}_{Scenario}.{format}

Examples:
- output/China_2040_baseline.csv
- output/USA_2040_accelerated.json
- output/Global_2040_delayed.csv
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
  "scenario": "baseline",
  "scenario_config": {
    "description": "Current policy trajectories and cost trends",
    "solar_cost_decline_rate": 0.08,
    "wind_cost_decline_rate": 0.05,
    "battery_cost_decline_rate": 0.10,
    "displacement_speed": 1.0
  },
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
  "battery_metrics": {
    "years": [2025, 2026, ...],
    "energy_capacity_gwh": [100, 120, ...],
    "power_capacity_gw": [25, 30, ...],
    "throughput_twh_per_year": [25, 30, ...],
    "cycles_per_year": 250,
    "duration_hours": 4,
    "round_trip_efficiency": 0.88
  },
  "generation_forecasts": {
    "years": [2025, 2026, ...],
    "swb_total": [5000.0, 6200.0, ...],
    "coal": [10000.0, 9500.0, ...],
    "gas": [8000.0, 7800.0, ...],
    "non_swb": [3000.0, 3000.0, ...],
    "total_demand": [26000.0, 26500.0, ...],
    "peak_load_gw": [200, 210, ...],
    "by_technology": {
      "Solar_PV": [2000.0, 2500.0, ...],
      "Onshore_Wind": [2500.0, 3000.0, ...],
      "Offshore_Wind": [500.0, 700.0, ...],
      "Battery_Storage": [0.0, 0.0, ...],
      "Wind_Total": [3000.0, 3700.0, ...]
    }
  },
  "displacement_timeline": {
    "swb_exceeds_coal": 2032,
    "swb_exceeds_gas": 2030,
    "swb_exceeds_all_fossil": 2035,
    "coal_95_percent_displaced": 2038,
    "gas_95_percent_displaced": 2036
  },
  "emissions_trajectory": {
    "years": [2025, 2026, ...],
    "annual_emissions_mt": {
      "coal": [5000, 4800, ...],
      "gas": [1800, 1750, ...],
      "solar": [50, 60, ...],
      "wind": [12, 15, ...],
      "total": [6862, 6625, ...]
    },
    "cumulative_emissions_mt": {
      "coal": [5000, 9800, ...],
      "gas": [1800, 3550, ...],
      "total": [6862, 13487, ...]
    },
    "emissions_avoided_vs_baseline": {
      "annual_mt": [0, 175, ...],
      "cumulative_mt": [0, 175, ...]
    },
    "carbon_price_per_ton": [15, 16, ...],
    "carbon_cost_billion_usd": {
      "coal": [75, 77, ...],
      "gas": [27, 28, ...],
      "total": [102, 105, ...]
    }
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

### 3. Battery Metrics (Phase 3 Addition)

Detailed battery storage metrics:
- **energy_capacity_gwh**: Battery energy capacity (GWh)
- **power_capacity_gw**: Power capacity (GW) = Energy / Duration
- **throughput_twh_per_year**: Annual throughput (TWh/year) = Energy × Cycles / 1000
- **cycles_per_year**: Number of charge/discharge cycles annually
- **duration_hours**: Storage duration (typically 4 hours)
- **round_trip_efficiency**: Round-trip efficiency (e.g., 0.88 = 88%)

**Formula relationships:**
```
Power (GW) = Energy_Capacity (GWh) / Duration (hours)
Throughput (TWh/year) = Energy_Capacity (GWh) × Cycles_per_year / 1000
```

### 4. Generation Forecasts

Annual electricity generation in GWh:
- **swb_total**: Sum of all SWB generation
- **coal**: Coal power generation
- **gas**: Natural gas generation
- **non_swb**: Nuclear + Hydro + Other
- **total_demand**: Total electricity demand
- **peak_load_gw**: Peak load proxy in GW (Phase 3 addition)
- **by_technology**: Breakdown by individual SWB technology
  - Includes **Wind_Total** when both onshore and offshore wind present

**Peak Load Calculation (Phase 3):**
```
Peak_Load (GW) = Annual_Demand (TWh) × 1000 / 8760 × Regional_Load_Factor
```

Where Regional_Load_Factor:
- China: 1.4, USA: 1.5, Europe: 1.3, Rest_of_World: 1.4, Global: 1.4

### 5. Displacement Timeline

Key milestone years:
- **swb_exceeds_coal**: SWB generation > Coal generation
- **swb_exceeds_gas**: SWB generation > Gas generation
- **swb_exceeds_all_fossil**: SWB generation > Coal + Gas
- **coal_95_percent_displaced**: Coal drops to 5% of peak
- **gas_95_percent_displaced**: Gas drops to 5% of peak

### 6. Emissions Trajectory (Phase 2 Addition)

Complete CO2 emissions tracking:

**annual_emissions_mt**: Annual emissions in megatonnes CO2 by technology
- coal, gas, solar, wind, total

**cumulative_emissions_mt**: Cumulative emissions from base year
- coal, gas, total

**emissions_avoided_vs_baseline**: Emissions avoided vs. BAU scenario
- annual_mt: Annual avoided emissions
- cumulative_mt: Cumulative avoided emissions

**carbon_price_per_ton**: Carbon price trajectory ($/tCO2)
- Based on regional base price + annual growth + scenario multiplier

**carbon_cost_billion_usd**: Financial cost of carbon emissions
- coal, gas, total (in billion USD)

**Emission factors used:**
- Coal: 1000 kg CO2/MWh
- Gas: 450 kg CO2/MWh
- Solar: 45 kg CO2/MWh (lifecycle)
- Wind: 12 kg CO2/MWh (lifecycle)

### 7. Validation

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
| Capacity | capacity_gw, power_capacity_gw | GW |
| Energy Capacity | energy_capacity_gwh | GWh |
| Throughput | throughput_twh_per_year | TWh/year |
| Peak Load | peak_load_gw | GW |
| Costs | costs (in cost_forecasts) | $/MWh |
| Carbon Price | carbon_price_per_ton | $/tCO2 |
| Emissions | annual_emissions_mt, cumulative_emissions_mt | Mt CO2 |
| Carbon Costs | carbon_cost_billion_usd | Billion USD |
| Share | SWB_Share | Decimal (0.0-1.0) |
| Efficiency | round_trip_efficiency | Decimal (0.0-1.0) |
| Years | Year, years | Integer |
| Cycles | cycles_per_year | Integer |
