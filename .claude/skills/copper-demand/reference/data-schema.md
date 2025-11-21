# Data Schema Reference

## Output Data Structure

### CSV Format

**Filename:** `copper_demand_{region}_{scenario}_{year}.csv`

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| year | int | Forecast year (2020-2040) |
| auto_total | float | Total automotive copper (tonnes) |
| auto_oem | float | Automotive OEM demand |
| auto_repl | float | Automotive replacement |
| auto_ice | float | ICE vehicle copper |
| auto_bev | float | BEV vehicle copper |
| grid_generation_oem | float | Grid generation copper |
| grid_gen_wind | float | Wind generation copper |
| grid_gen_solar | float | Solar generation copper |
| grid_gen_fossil | float | Fossil fuel generation copper |
| construction_total | float | Construction segment total |
| construction_oem | float | New construction |
| construction_repl | float | Retrofit/replacement |
| grid_td_total | float | Grid T&D total |
| grid_td_oem | float | Grid T&D new infrastructure |
| grid_td_repl | float | Grid T&D replacement |
| industrial_total | float | Industrial segment total |
| industrial_oem | float | Industrial OEM |
| industrial_repl | float | Industrial replacement |
| electronics_total | float | Electronics segment |
| electronics_oem | float | Electronics OEM |
| electronics_repl | float | Electronics replacement (typically 0) |
| other_uses | float | Other uses (alloys, chemicals, misc) |
| total_demand | float | Total copper consumption (tonnes) |
| share_transport_calc | float | Transportation as % of total (0-1) |
| share_ev_calc | float | EV as % of total (0-1) |
| automotive_confidence | string | Confidence tag for automotive |
| grid_generation_confidence | string | Confidence tag for generation |
| construction_confidence | string | Confidence tag for construction |
| grid_td_confidence | string | Confidence tag for grid T&D |
| industrial_confidence | string | Confidence tag for industrial |
| electronics_confidence | string | Confidence tag for electronics |
| other_uses_confidence | string | Confidence tag for other uses |
| total_oem | float | Sum of all OEM demand |
| total_replacement | float | Sum of all replacement demand |

### JSON Format

**Filename:** `copper_demand_{region}_{scenario}_{year}.json`

**Structure:** Array of yearly objects

```json
[
  {
    "year": 2020,
    "auto_total": 1694000.0,
    "auto_oem": 1694000.0,
    "auto_repl": 0,
    "auto_ice": 1577800.0,
    "auto_bev": 116200.0,
    ...
  },
  {
    "year": 2021,
    ...
  }
]
```

## Configuration Schema

### config.json Structure

```json
{
  "skill_name": "copper-demand",
  "version": "1.0.0",
  "description": "...",

  "default_parameters": {
    "start_year": 2020,
    "end_year": 2030,
    "smoothing_window": 3,
    "force_reconciliation": true,
    "confidence_tagging": true,
    "scenario": "baseline"
  },

  "regions": ["China", "USA", "Europe", "Rest_of_World", "Global"],

  "copper_coefficients": {
    "automotive": {
      "car_ice": 23.0,          // kg per vehicle
      "car_bev": 83.0,
      "car_phev": 60.0,
      "car_hev": 35.0,
      "cv_ice": 35.0,           // commercial vehicle
      "cv_ev": 120.0,
      "cv_ngv": 38.0,           // natural gas vehicle
      "two_wheeler_ice": 3.0,
      "two_wheeler_ev": 4.0,
      "three_wheeler_ice": 4.0,
      "three_wheeler_ev": 5.0
    },
    "grid_generation": {
      "per_mw_wind_onshore": 6.0,     // tonnes per MW
      "per_mw_wind_offshore": 10.0,
      "per_mw_solar_pv": 5.0,
      "per_mw_gas_ccgt": 1.0,
      "per_mw_coal": 1.0
    }
  },

  "segment_allocation": {
    "electrical_segments": {
      "construction_pct": 0.48,
      "grid_pct": 0.35,
      "industrial_pct": 0.17
    },
    "direct_shares": {
      "electronics_pct": 0.11,
      "other_uses_target_pct": 0.12
    }
  },

  "scenarios": {
    "baseline": {
      "ev_adoption_2035": 0.75,
      "renewable_capacity_2035_tw": 15
    },
    "accelerated": {
      "ev_adoption_2035": 0.92,
      "renewable_capacity_2035_tw": 20,
      "demand_multiplier": 1.25
    },
    "delayed": {
      "ev_adoption_2035": 0.55,
      "renewable_capacity_2035_tw": 11,
      "demand_multiplier": 0.85
    },
    "substitution": {
      "ev_adoption_2035": 0.75,
      "renewable_capacity_2035_tw": 15,
      "coefficient_reduction": 0.15,
      "annual_thrifting": 0.007
    }
  }
}
```

## Input Data Schema

### Vehicle Data Format

**Source Files:**
- `Passenger_Cars.json`
- `Commercial_Vehicle.json`
- `Two_Wheeler.json`
- `Three_Wheeler.json`

**Structure:**

```json
{
  "metrics": [
    {
      "name": "Passenger_Vehicle_Annual_Sales",
      "data": [
        {
          "region": "China",
          "powertrain": "ICE",
          "values": [
            {"year": 2020, "value": 15.2},
            {"year": 2021, "value": 16.1}
          ]
        },
        {
          "region": "China",
          "powertrain": "BEV",
          "values": [
            {"year": 2020, "value": 1.2},
            {"year": 2021, "value": 2.9}
          ]
        }
      ]
    }
  ]
}
```

### Generation Capacity Data Format

**Source File:** `Energy_Generation.json`

**Structure:**

```json
{
  "metrics": [
    {
      "name": "Onshore_Wind_Installed_Capacity",
      "data": [
        {
          "region": "China",
          "values": [
            {"year": 2020, "value": 281.0},
            {"year": 2021, "value": 329.0}
          ]
        }
      ]
    }
  ]
}
```

### Copper Consumption Data Format

**Source File:** `Copper.json`

**Structure:**

```json
{
  "metrics": [
    {
      "name": "Annual_Consumption",
      "data": [
        {
          "region": "Global",
          "values": [
            {"year": 2020, "value": 25000000},
            {"year": 2021, "value": 25200000}
          ]
        }
      ]
    },
    {
      "name": "Demand_Transportation_Percentage",
      "data": [
        {
          "region": "Global",
          "values": [
            {"year": 2020, "value": 12.0},
            {"year": 2021, "value": 12.2}
          ]
        }
      ]
    }
  ]
}
```

## Confidence Tags

| Tag | Meaning | Used For |
|-----|---------|----------|
| HIGH_BOTTOM_UP | Full driver data available, direct calculation | Automotive |
| MEDIUM_BOTTOM_UP | Partial driver data, some assumptions | Grid Generation |
| LOW_ALLOCATED | No driver data, allocated by share | Construction, Industrial, Electronics |
| LOW_RESIDUAL | Calculated as remainder after other segments | Grid T&D, Other Uses |

## Units

- **Copper Demand:** Tonnes (metric tons)
- **Vehicle Copper Intensity:** Kilograms (kg)
- **Generation Copper Intensity:** Tonnes per Megawatt (t/MW)
- **Generation Capacity:** Megawatts (MW) or Gigawatts (GW)
- **Vehicle Sales:** Millions of units
- **Shares/Percentages:** Decimal (0.12 = 12%)

## Regional Codes

| Code | Description |
|------|-------------|
| China | People's Republic of China |
| USA | United States of America |
| Europe | European Union + UK + Norway + Switzerland |
| Rest_of_World | All other countries |
| Global | Aggregated total (sum of regions or independent calculation) |
