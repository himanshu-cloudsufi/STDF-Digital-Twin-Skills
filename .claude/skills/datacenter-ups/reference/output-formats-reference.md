# Output Formats Reference

Complete specification of output data structures, file formats, and schema definitions for the Datacenter UPS Battery Technology Transition model.

## Contents

- [Overview](#overview)
- [CSV Output Format](#csv-output-format)
- [JSON Output Format](#json-output-format)
- [Plot Output Specifications](#plot-output-specifications)
- [Aggregation Rules](#aggregation-rules)
- [File Naming Conventions](#file-naming-conventions)
- [Data Type Specifications](#data-type-specifications)
- [Example Outputs](#example-outputs)

---

## Overview

The model supports three output formats:
- **CSV**: Tabular data for spreadsheet analysis and reporting
- **JSON**: Structured data with metadata, nested objects for programmatic consumption
- **Plot**: Visualization files (PNG/SVG) for reports and presentations

Output location: `output/` directory within the skill folder

---

## CSV Output Format

### Core Columns (Always Present)

| Column Name | Type | Units | Description | Example |
|------------|------|-------|-------------|---------|
| `year` | Integer | years | Forecast year | 2025 |
| `region` | String | - | Geographic region | "China" |
| `scenario` | String | - | Scenario name | "baseline" |
| `total_demand_gwh` | Float | GWh/year | Total market demand | 45.67 |
| `vrla_demand_gwh` | Float | GWh/year | VRLA annual demand | 30.12 |
| `lithium_demand_gwh` | Float | GWh/year | Li-ion annual demand | 15.55 |
| `vrla_share_pct` | Float | % | VRLA market share | 65.9 |
| `lithium_share_pct` | Float | % | Li-ion market share | 34.1 |
| `tipping_year` | String/Integer | years | Cost parity year | 2027 or "N/A" |

### TCO Analysis Columns

| Column Name | Type | Units | Description | Example |
|------------|------|-------|-------------|---------|
| `vrla_capex_per_kwh` | Float | $/kWh | VRLA capital cost | 220.00 |
| `lithium_capex_per_kwh` | Float | $/kWh | Li-ion capital cost | 185.50 |
| `vrla_tco_per_kwh` | Float | $/kWh | VRLA total cost of ownership | 625.82 |
| `lithium_tco_per_kwh` | Float | $/kWh | Li-ion total cost of ownership | 302.81 |
| `tco_advantage` | Float | $/kWh | TCO difference (VRLA - Li-ion) | 323.01 |

### Installed Base Columns

| Column Name | Type | Units | Description | Example |
|------------|------|-------|-------------|---------|
| `vrla_installed_base_gwh` | Float | GWh | VRLA cumulative stock | 125.45 |
| `lithium_installed_base_gwh` | Float | GWh | Li-ion cumulative stock | 45.23 |
| `total_installed_base_gwh` | Float | GWh | Total installed base | 170.68 |
| `vrla_retirements_gwh` | Float | GWh/year | VRLA annual retirements | 25.09 |
| `lithium_retirements_gwh` | Float | GWh/year | Li-ion annual retirements | 3.77 |

### Market Decomposition Columns

| Column Name | Type | Units | Description | Example |
|------------|------|-------|-------------|---------|
| `new_build_demand_gwh` | Float | GWh/year | Demand from new datacenters | 8.45 |
| `replacement_demand_gwh` | Float | GWh/year | Demand from replacements | 37.22 |
| `contestable_market_gwh` | Float | GWh/year | VRLA at EoL (switchable) | 25.09 |
| `li_ion_retrofits_gwh` | Float | GWh/year | VRLA→Li-ion conversions | 18.82 |
| `vrla_for_vrla_gwh` | Float | GWh/year | VRLA→VRLA replacements | 6.27 |

### Battery Metrics Columns

| Column Name | Type | Units | Description | Example |
|------------|------|-------|-------------|---------|
| `power_capacity_mw` | Float | MW | Total power capacity | 11,417.5 |
| `vrla_power_capacity_mw` | Float | MW | VRLA power capacity | 7,530.0 |
| `lithium_power_capacity_mw` | Float | MW | Li-ion power capacity | 3,887.5 |
| `annual_throughput_gwh` | Float | GWh/year | Total energy throughput | 37,550 |
| `cycles_per_year` | Integer | cycles | Annual discharge cycles | 250 |
| `round_trip_efficiency_pct` | Float | % | RTE efficiency | 88.0 |

### Financial Columns (Optional)

| Column Name | Type | Units | Description | Example |
|------------|------|-------|-------------|---------|
| `vrla_revenue_musd` | Float | M USD | VRLA market value | 6,626.4 |
| `lithium_revenue_musd` | Float | M USD | Li-ion market value | 2,885.8 |
| `total_revenue_musd` | Float | M USD | Total market value | 9,512.2 |
| `price_vrla_per_kwh` | Float | $/kWh | VRLA selling price | 220.00 |
| `price_lithium_per_kwh` | Float | $/kWh | Li-ion selling price | 185.50 |

### CSV Format Rules

- **Encoding**: UTF-8 without BOM
- **Delimiter**: Comma (`,`)
- **Decimal**: Period (`.`)
- **Header**: First row contains column names
- **Null values**: Empty string or "N/A" for strings, empty for numbers
- **Float precision**: 2 decimal places for most values; 4 for small numbers
- **Sort order**: By year (ascending), then region (alphabetical)

### Example CSV Output

```csv
year,region,scenario,total_demand_gwh,vrla_demand_gwh,lithium_demand_gwh,vrla_share_pct,lithium_share_pct,tipping_year,vrla_tco_per_kwh,lithium_tco_per_kwh,tco_advantage
2025,China,baseline,32.45,28.19,4.26,86.9,13.1,2027,625.82,385.23,240.59
2026,China,baseline,35.37,28.83,6.54,81.5,18.5,2027,625.82,358.41,267.41
2027,China,baseline,38.55,28.91,9.64,75.0,25.0,2027,625.82,333.67,292.15
2028,China,baseline,42.01,26.73,15.28,63.6,36.4,2027,625.82,310.89,314.93
```

---

## JSON Output Format

### Root Structure

```json
{
  "metadata": {
    "model_version": "1.0.0",
    "run_timestamp": "2025-11-19T10:30:45Z",
    "region": "China",
    "scenario": "baseline",
    "parameters": { ... }
  },
  "forecast": {
    "years": [2025, 2026, ...],
    "demand": { ... },
    "costs": { ... },
    "adoption": { ... },
    "installed_base": { ... },
    "market_decomposition": { ... },
    "battery_metrics": { ... }
  },
  "analysis": {
    "tipping_point": { ... },
    "s_curve_parameters": { ... },
    "validation": { ... },
    "key_metrics": { ... }
  }
}
```

### Metadata Section

```json
{
  "metadata": {
    "model_version": "1.0.0",
    "run_timestamp": "2025-11-19T10:30:45Z",
    "region": "China",
    "scenario": "baseline",
    "parameters": {
      "start_year": 2020,
      "end_year": 2040,
      "tco_horizon": 15,
      "discount_rate": 0.08,
      "vrla_lifespan": 5,
      "lithium_lifespan": 12,
      "s_curve_ceiling": 0.95
    },
    "data_sources": {
      "vrla_demand": "Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_China",
      "lithium_demand": "Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_China",
      "bess_costs": "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_China"
    }
  }
}
```

### Forecast Section

```json
{
  "forecast": {
    "years": [2025, 2026, 2027, 2028, 2029, 2030],
    "demand": {
      "total_gwh": [32.45, 35.37, 38.55, 42.01, 45.79, 49.91],
      "vrla_gwh": [28.19, 28.83, 28.91, 26.73, 22.90, 17.47],
      "lithium_gwh": [4.26, 6.54, 9.64, 15.28, 22.89, 32.44],
      "vrla_share_pct": [86.9, 81.5, 75.0, 63.6, 50.0, 35.0],
      "lithium_share_pct": [13.1, 18.5, 25.0, 36.4, 50.0, 65.0]
    },
    "costs": {
      "vrla_capex_per_kwh": [220.0, 220.0, 220.0, 220.0, 220.0, 220.0],
      "lithium_capex_per_kwh": [195.0, 185.5, 176.2, 167.4, 159.0, 151.1],
      "vrla_tco_per_kwh": [625.82, 625.82, 625.82, 625.82, 625.82, 625.82],
      "lithium_tco_per_kwh": [385.23, 358.41, 333.67, 310.89, 290.03, 270.93],
      "tco_advantage": [240.59, 267.41, 292.15, 314.93, 335.79, 354.89]
    },
    "installed_base": {
      "vrla_gwh": [125.45, 129.37, 132.84, 133.96, 131.37, 124.42],
      "lithium_gwh": [15.23, 20.34, 27.15, 36.25, 48.39, 64.62],
      "total_gwh": [140.68, 149.71, 159.99, 170.21, 179.76, 189.04],
      "vrla_retirements_gwh": [25.09, 25.87, 26.57, 26.79, 26.27, 24.88],
      "lithium_retirements_gwh": [1.27, 1.69, 2.26, 3.02, 4.03, 5.38]
    },
    "market_decomposition": {
      "new_build_gwh": [8.45, 8.98, 9.60, 10.21, 10.78, 11.34],
      "replacement_gwh": [23.99, 26.39, 28.94, 31.79, 35.01, 38.57],
      "contestable_market_gwh": [25.09, 25.87, 26.57, 26.79, 26.27, 24.88],
      "li_ion_retrofits_gwh": [3.28, 4.79, 6.64, 9.75, 13.14, 16.17],
      "vrla_for_vrla_gwh": [21.81, 21.08, 19.93, 17.04, 13.13, 8.71]
    },
    "battery_metrics": {
      "power_capacity_mw": [8112.5, 8842.5, 9637.5, 10502.5, 11447.5, 12477.5],
      "vrla_power_mw": [7047.5, 7207.5, 7227.5, 6682.5, 5725.0, 4367.5],
      "lithium_power_mw": [1065.0, 1635.0, 2410.0, 3820.0, 5722.5, 8110.0],
      "annual_throughput_gwh": [30950, 32935, 35198, 37446, 39547, 41488]
    }
  }
}
```

### Analysis Section

```json
{
  "analysis": {
    "tipping_point": {
      "year": 2027,
      "tco_vrla": 625.82,
      "tco_lithium": 333.67,
      "advantage": 292.15,
      "confidence": "high",
      "persistence_years": 3
    },
    "s_curve_parameters": {
      "ceiling_L": 0.95,
      "inflection_t0": 2027,
      "steepness_k": 0.5,
      "cost_sensitivity_s": 0.002,
      "fit_quality": {
        "r_squared": 0.98,
        "rmse": 0.023,
        "calibration_method": "least_squares"
      }
    },
    "validation": {
      "non_negativity": "pass",
      "monotonic_adoption": "pass",
      "mass_balance": {
        "vrla_max_error": 0.0008,
        "lithium_max_error": 0.0005,
        "status": "pass"
      },
      "demand_consistency": {
        "max_error": 0.023,
        "status": "pass"
      }
    },
    "key_metrics": {
      "cagr_total_demand": 0.089,
      "2030_lithium_share": 0.65,
      "2035_lithium_share": 0.85,
      "2040_lithium_share": 0.92,
      "crossover_year": 2029,
      "peak_vrla_installed_base": {
        "year": 2027,
        "value_gwh": 132.84
      }
    }
  }
}
```

### JSON Schema Version

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Datacenter UPS Forecast Output",
  "type": "object",
  "required": ["metadata", "forecast", "analysis"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["model_version", "run_timestamp", "region", "scenario"]
    },
    "forecast": {
      "type": "object",
      "required": ["years", "demand", "costs"]
    },
    "analysis": {
      "type": "object",
      "required": ["tipping_point", "validation"]
    }
  }
}
```

---

## Plot Output Specifications

### Standard Plots

#### 1. Adoption Curve (`adoption_curve.png`)
- **X-axis**: Years
- **Y-axis**: Market share (%)
- **Series**: VRLA (declining), Li-ion (rising)
- **Markers**: Tipping point, 50% crossover, historical vs forecast boundary
- **Format**: PNG 1200x800px, SVG optional

#### 2. Demand Stack (`demand_stack.png`)
- **Type**: Stacked area chart
- **X-axis**: Years
- **Y-axis**: Annual demand (GWh)
- **Layers**: VRLA (bottom), Li-ion (top)
- **Annotations**: Total demand trend line

#### 3. TCO Trajectory (`tco_trajectory.png`)
- **Type**: Dual line chart
- **X-axis**: Years
- **Y-axis**: TCO ($/kWh)
- **Series**: VRLA TCO, Li-ion TCO
- **Highlight**: Tipping point intersection
- **Shading**: Li-ion advantage zone (green), VRLA advantage zone (red)

#### 4. Installed Base Evolution (`installed_base.png`)
- **Type**: Stacked bar chart
- **X-axis**: Years
- **Y-axis**: Installed base (GWh)
- **Components**: VRLA stock, Li-ion stock
- **Secondary axis**: Total installed base line

#### 5. Market Decomposition (`market_decomposition.png`)
- **Type**: Grouped bar chart
- **X-axis**: Years
- **Y-axis**: Demand (GWh)
- **Groups**: New-build, Replacement, Contestable
- **Colors**: Technology-coded (VRLA orange, Li-ion blue)

### Plot Configuration

```json
{
  "plot_config": {
    "dpi": 150,
    "figsize": [12, 8],
    "style": "seaborn-v0_8-darkgrid",
    "color_scheme": {
      "vrla": "#FF7F0E",
      "lithium": "#1F77B4",
      "total": "#2CA02C",
      "highlight": "#D62728"
    },
    "font_sizes": {
      "title": 16,
      "axis_label": 12,
      "tick_label": 10,
      "legend": 10
    },
    "output_formats": ["png", "svg"],
    "save_data": true
  }
}
```

---

## Aggregation Rules

### Regional to Global Aggregation

```python
# Correct aggregation
global_demand = china_demand + usa_demand + europe_demand + row_demand

# Weighted average for shares
global_lithium_share = (
    china_demand * china_lithium_share +
    usa_demand * usa_lithium_share +
    europe_demand * europe_lithium_share +
    row_demand * row_lithium_share
) / global_demand

# Do NOT sum percentages
# WRONG: global_share = china_share + usa_share + ...
```

### Temporal Aggregation

```python
# Annual to multi-year periods
period_2025_2030 = sum(annual_demand[2025:2031])

# Average annual growth rate (CAGR)
cagr = (demand_2030 / demand_2025) ** (1/5) - 1

# Cumulative metrics
cumulative_additions = sum(annual_additions[start:end+1])
```

---

## File Naming Conventions

### Pattern
```
{model}_{region}_{scenario}_{end_year}_{timestamp}.{format}

Where:
- model: "datacenter_ups"
- region: lowercase with underscores (china, usa, europe, rest_of_world, global)
- scenario: scenario name (baseline, accelerated, delayed)
- end_year: 4-digit year (2035, 2040)
- timestamp: optional ISO format (20251119_103045)
- format: csv, json, png, svg
```

### Examples
```
datacenter_ups_china_baseline_2040.csv
datacenter_ups_global_accelerated_2035_20251119_103045.json
datacenter_ups_usa_delayed_2040_adoption_curve.png
```

### Directory Structure
```
output/
├── csv/
│   ├── datacenter_ups_china_baseline_2040.csv
│   └── datacenter_ups_global_baseline_2040.csv
├── json/
│   └── datacenter_ups_china_baseline_2040.json
├── plots/
│   ├── adoption_curves/
│   ├── tco_analysis/
│   └── market_decomposition/
└── reports/
    └── summary_baseline_2040.md
```

---

## Data Type Specifications

### Numeric Precision

| Data Type | Precision | Format | Example |
|-----------|-----------|--------|---------|
| Year | Integer | %d | 2025 |
| Demand (GWh) | 2 decimal | %.2f | 45.67 |
| Share (%) | 1 decimal | %.1f | 65.9 |
| Cost ($/kWh) | 2 decimal | %.2f | 220.00 |
| TCO ($/kWh) | 2 decimal | %.2f | 625.82 |
| Growth Rate | 3 decimal | %.3f | 0.089 |
| Small values (<1) | 4 decimal | %.4f | 0.0023 |

### String Formats

| Field | Format | Examples |
|-------|--------|----------|
| Region | Title Case | "China", "Rest_of_World" |
| Scenario | lowercase | "baseline", "accelerated" |
| Technology | uppercase abbrev | "VRLA", "Li-ion" |
| Tipping Year | Integer or "N/A" | 2027, "N/A" |
| Timestamp | ISO 8601 | "2025-11-19T10:30:45Z" |

### Boolean Representations

- CSV: "true"/"false" or 1/0
- JSON: true/false (native boolean)

---

## Example Outputs

### Minimal CSV (5 years)

```csv
year,vrla_demand_gwh,lithium_demand_gwh,lithium_share_pct
2025,28.19,4.26,13.1
2026,28.83,6.54,18.5
2027,28.91,9.64,25.0
2028,26.73,15.28,36.4
2029,22.90,22.89,50.0
```

### Minimal JSON

```json
{
  "region": "China",
  "scenario": "baseline",
  "tipping_year": 2027,
  "forecast": {
    "2025": {"vrla": 28.19, "lithium": 4.26},
    "2030": {"vrla": 17.47, "lithium": 32.44},
    "2035": {"vrla": 7.82, "lithium": 56.91},
    "2040": {"vrla": 4.95, "lithium": 89.37}
  }
}
```

### Summary Report Format

```markdown
# Datacenter UPS Forecast Summary

**Region**: China
**Scenario**: Baseline
**Forecast Period**: 2025-2040

## Key Findings

- **Tipping Point**: 2027 (Li-ion TCO advantage: $292/kWh)
- **2030 Li-ion Share**: 65.0%
- **2040 Li-ion Share**: 92.0%
- **Market CAGR**: 8.9%

## Annual Forecast

| Year | Total (GWh) | VRLA (%) | Li-ion (%) |
|------|-------------|----------|------------|
| 2025 | 32.45 | 86.9 | 13.1 |
| 2030 | 49.91 | 35.0 | 65.0 |
| 2035 | 64.73 | 12.1 | 87.9 |
| 2040 | 94.32 | 5.2 | 94.8 |
```

---

## Validation Rules for Output

### Required Fields
- Every row must have: year, region, vrla_demand, lithium_demand
- JSON must have: metadata, forecast sections
- Tipping year must be integer or "N/A"

### Consistency Checks
```python
# Sum consistency
assert abs(vrla_demand + lithium_demand - total_demand) < 0.01

# Share consistency
assert abs(vrla_share + lithium_share - 100.0) < 0.1

# Monotonicity
assert all(lithium_share[i] <= lithium_share[i+1] for i in range(len(lithium_share)-1))

# Non-negativity
assert all(demand >= 0 for demand in all_demands)
```

### Output Size Limits
- CSV: Max 10,000 rows (500 years × 20 columns)
- JSON: Max 10 MB uncompressed
- Plots: Max 4000×3000 pixels

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Maintainer**: Datacenter UPS Battery Forecasting Team