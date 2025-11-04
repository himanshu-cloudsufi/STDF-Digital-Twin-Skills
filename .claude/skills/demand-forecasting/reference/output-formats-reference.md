# Output Formats Reference

Complete specification of all output formats (CSV, JSON, plots) including column descriptions, structure, and usage examples.

## Contents
- Output Format Overview
- CSV Format Specification
- JSON Format Specification
- File Naming Conventions
- Regional vs Global Outputs
- Example Outputs

---

## Output Format Overview

### Available Formats

**1. CSV** (Comma-Separated Values)
- Human-readable tabular format
- Excel and spreadsheet compatible
- Easy to plot and analyze
- Best for: Quick analysis, visualization, sharing with non-technical users

**2. JSON** (JavaScript Object Notation)
- Machine-readable structured format
- Includes full metadata (tipping point, CAGRs, validation status)
- Preserves all analysis details
- Best for: Programmatic access, archiving complete results, further processing

**3. Both** (CSV + JSON)
- Exports both formats simultaneously
- CSV for analysis, JSON for metadata
- Best for: Comprehensive documentation

### Command-Line Selection

```bash
# CSV only (default)
python3 scripts/forecast.py --region China --output csv

# JSON only
python3 scripts/forecast.py --region USA --output json

# Both formats
python3 scripts/forecast.py --region Europe --output both
```

---

## CSV Format Specification

### Regional Forecast CSV

**Columns (8 total)**:

1. **Year** (integer)
   - Forecast year
   - Ranges from first historical year to end_year
   - Example: 2015, 2016, ..., 2040

2. **Market** (float)
   - Total passenger vehicle demand (all types)
   - Units: Number of vehicles (annual sales)
   - Formula: BEV + PHEV + ICE

3. **BEV** (float)
   - Battery Electric Vehicle demand
   - Units: Number of vehicles (annual sales)
   - Forecasted using logistic curve post-tipping

4. **PHEV** (float)
   - Plug-in Hybrid Electric Vehicle demand
   - Units: Number of vehicles (annual sales)
   - Hump trajectory: rises before tipping, decays after

5. **ICE** (float)
   - Internal Combustion Engine vehicle demand
   - Units: Number of vehicles (annual sales)
   - Formula: max(Market − BEV − PHEV, 0)

6. **EV** (float)
   - Total Electric Vehicle demand (BEV + PHEV)
   - Units: Number of vehicles (annual sales)
   - Formula: BEV + PHEV

7. **EV_Cost** (float)
   - EV cost curve value for this year
   - Units: USD (real)
   - Interpolated from cost forecast to match demand years

8. **ICE_Cost** (float)
   - ICE cost curve value for this year
   - Units: USD (real)
   - Interpolated from cost forecast to match demand years

### Example Regional CSV

```csv
Year,Market,BEV,PHEV,ICE,EV,EV_Cost,ICE_Cost
2015,17500000,150000,80000,17270000,230000,35000,28000
2016,18000000,250000,120000,17630000,370000,32000,27500
2017,18500000,400000,180000,17920000,580000,29000,27000
2018,19000000,600000,250000,18150000,850000,26000,26500
2019,19500000,950000,350000,18200000,1300000,23000,26000
2020,20000000,1200000,480000,18320000,1680000,20000,25500
2021,20500000,1800000,650000,18050000,2450000,18000,25000
2022,21000000,2500000,850000,17650000,3350000,16000,24500
2023,21500000,3200000,1100000,17200000,4300000,14500,24000
2024,22000000,4100000,1400000,16500000,5500000,13200,23500
2025,22500000,5300000,1750000,15450000,7050000,12000,23000
...
2040,28000000,24500000,500000,3000000,25000000,5000,20000
```

### Global Forecast CSV

**Format**: Same 6 demand columns, but NO cost columns

**Columns (6 total)**:

1. **Year** (integer)
2. **Market** (float) - Sum of all regional markets
3. **BEV** (float) - Sum of all regional BEV
4. **PHEV** (float) - Sum of all regional PHEV
5. **ICE** (float) - Sum of all regional ICE
6. **EV** (float) - Sum of all regional EV

**Note**: Global aggregates do not include cost data because costs vary by region (different currencies, price levels).

### Example Global CSV

```csv
Year,Market,BEV,PHEV,ICE,EV
2015,70000000,500000,300000,69200000,800000
2016,72000000,850000,450000,70700000,1300000
2017,74000000,1400000,670000,71930000,2070000
...
2040,105000000,85000000,2000000,18000000,87000000
```

### CSV File Naming

**Regional forecasts**:
```
{Region}_{EndYear}.csv
```
Examples:
- `China_2040.csv`
- `USA_2050.csv`
- `Europe_2035.csv`
- `Rest_of_World_2040.csv`

**Global forecast**:
```
Global_{EndYear}_global.csv
```
Example:
- `Global_2040_global.csv`

**Note**: When using `--region Global`, the tool exports both:
- One global aggregate CSV (`Global_2040_global.csv`)
- Four regional CSVs (one for each region)

---

## JSON Format Specification

### Regional Forecast JSON

**Top-level structure**:

```json
{
  "region": "China",
  "cost_analysis": { ... },
  "demand_forecast": { ... }
}
```

### Cost Analysis Section

Contains cost curve data and tipping point detection results:

```json
"cost_analysis": {
  "tipping_point": 2024,
  "years": [2015, 2016, 2017, ..., 2040],
  "ev_costs": [35000, 32000, 29000, ..., 5000],
  "ice_costs": [28000, 27500, 27000, ..., 20000],
  "ev_cagr": -0.085,
  "ice_cagr": -0.015,
  "ev_smoothed": [35000, 32000, 29000, ...],
  "ice_smoothed": [28000, 27500, 27000, ...]
}
```

**Fields**:

- **tipping_point** (integer | null)
  - Year when EV cost < ICE cost for first time
  - `null` if no tipping point detected

- **years** (array of integers)
  - Years for cost curves
  - Combined historical + forecasted

- **ev_costs** (array of floats)
  - EV cost values (USD)
  - Includes forecasted values

- **ice_costs** (array of floats)
  - ICE cost values (USD)
  - Includes forecasted values

- **ev_cagr** (float)
  - Compound annual growth rate for EV costs
  - Negative indicates declining costs
  - Example: -0.085 = -8.5% per year

- **ice_cagr** (float)
  - Compound annual growth rate for ICE costs
  - Typically small negative or near zero

- **ev_smoothed** (array of floats)
  - 3-year rolling median smoothed EV costs
  - Used for tipping point detection

- **ice_smoothed** (array of floats)
  - 3-year rolling median smoothed ICE costs
  - Used for tipping point detection

### Demand Forecast Section

Contains all demand forecasts and validation results:

```json
"demand_forecast": {
  "years": [2015, 2016, 2017, ..., 2040],
  "market": [17500000, 18000000, 18500000, ..., 28000000],
  "bev": [150000, 250000, 400000, ..., 24500000],
  "phev": [80000, 120000, 180000, ..., 500000],
  "ice": [17270000, 17630000, 17920000, ..., 3000000],
  "ev": [230000, 370000, 580000, ..., 25000000],
  "logistic_params": {
    "L": 1.0,
    "k": 0.45,
    "t0": 2024.5
  },
  "validation": {
    "is_valid": true,
    "message": "Forecast passed all validation checks",
    "max_sum_error": 0.0001
  }
}
```

**Fields**:

- **years** (array of integers)
  - Years for demand forecasts
  - Same range as cost analysis years

- **market** (array of floats)
  - Total market demand (all vehicle types)
  - Units: vehicles per year

- **bev** (array of floats)
  - BEV demand forecast
  - Units: vehicles per year

- **phev** (array of floats)
  - PHEV demand forecast
  - Units: vehicles per year

- **ice** (array of floats)
  - ICE demand forecast (residual)
  - Units: vehicles per year

- **ev** (array of floats)
  - Total EV demand (BEV + PHEV)
  - Units: vehicles per year

- **logistic_params** (object)
  - **L** (float): Logistic ceiling (max adoption share)
  - **k** (float): Growth rate parameter (steepness)
  - **t0** (float): Inflection point year

- **validation** (object)
  - **is_valid** (boolean): True if all checks passed
  - **message** (string): Validation status description
  - **max_sum_error** (float): Maximum error in BEV+PHEV+ICE vs Market

### Global Forecast JSON

**Structure for Global region**:

```json
{
  "regional_results": {
    "China": {
      "region": "China",
      "cost_analysis": { ... },
      "demand_forecast": { ... }
    },
    "USA": { ... },
    "Europe": { ... },
    "Rest_of_World": { ... }
  },
  "global_result": {
    "region": "Global",
    "years": [2015, 2016, ..., 2040],
    "market": [70000000, 72000000, ..., 105000000],
    "bev": [500000, 850000, ..., 85000000],
    "phev": [300000, 450000, ..., 2000000],
    "ice": [69200000, 70700000, ..., 18000000],
    "ev": [800000, 1300000, ..., 87000000]
  }
}
```

**Note**: Global JSON includes full details for each region plus global aggregates.

### JSON File Naming

**Regional forecasts**:
```
{Region}_{EndYear}.json
```
Examples:
- `China_2040.json`
- `USA_2050.json`

**Global forecast**:
```
Global_{EndYear}.json
```
Example:
- `Global_2040.json`

**Note**: Global JSON is a single file containing all regional results + global aggregate.

---

## File Naming Conventions

### Output Directory Structure

Default output directory: `./output`

Customizable via `--output-dir` flag:
```bash
python3 scripts/forecast.py --region China --output-dir ./forecasts/2024_analysis
```

### Generated Files

**Single region with CSV output**:
```
output/
└── China_2040.csv
```

**Single region with JSON output**:
```
output/
└── China_2040.json
```

**Single region with both outputs**:
```
output/
├── China_2040.csv
└── China_2040.json
```

**Global forecast with CSV output**:
```
output/
├── China_2040.csv
├── USA_2040.csv
├── Europe_2040.csv
├── Rest_of_World_2040.csv
└── Global_2040_global.csv
```

**Global forecast with JSON output**:
```
output/
└── Global_2040.json  # Contains all regional data + global aggregate
```

**Global forecast with both outputs**:
```
output/
├── China_2040.csv
├── USA_2040.csv
├── Europe_2040.csv
├── Rest_of_World_2040.csv
├── Global_2040_global.csv
└── Global_2040.json
```

---

## Regional vs Global Outputs

### Key Differences

| Aspect | Regional Output | Global Output |
|--------|----------------|---------------|
| **CSV columns** | 8 (includes cost data) | 6 (demand only) |
| **JSON structure** | Single region object | Nested with all regions |
| **File count (CSV)** | 1 file | 5 files (4 regions + global) |
| **File count (JSON)** | 1 file | 1 file (contains all data) |
| **Cost data** | Included | Not included in aggregate |
| **Tipping point** | Per region | Per region (in nested data) |

### When to Use Each

**Regional forecast**:
- Analyze single market
- Include cost dynamics
- Smaller file sizes
- Focused analysis

**Global forecast**:
- Compare across regions
- Get worldwide totals
- Comprehensive analysis
- Policy/strategy planning

---

## Example Outputs

### Example 1: China 2040 CSV (excerpt)

```csv
Year,Market,BEV,PHEV,ICE,EV,EV_Cost,ICE_Cost
2015,17500000,150000,80000,17270000,230000,35000,28000
2023,21500000,3200000,1100000,17200000,4300000,14500,24000
2024,22000000,4100000,1400000,16500000,5500000,13200,23500
2030,25000000,12000000,2200000,10800000,14200000,8500,22000
2035,26500000,19000000,1200000,6300000,20200000,6500,21000
2040,28000000,24500000,500000,3000000,25000000,5000,20000
```

### Example 2: USA 2040 JSON (excerpt)

```json
{
  "region": "USA",
  "cost_analysis": {
    "tipping_point": 2026,
    "ev_cagr": -0.072,
    "ice_cagr": -0.008
  },
  "demand_forecast": {
    "years": [2015, 2016, ..., 2040],
    "market": [17200000, 17500000, ..., 19500000],
    "bev": [100000, 150000, ..., 15000000],
    "logistic_params": {
      "L": 0.9,
      "k": 0.38,
      "t0": 2027.2
    },
    "validation": {
      "is_valid": true,
      "message": "Forecast passed all validation checks"
    }
  }
}
```

### Example 3: Global 2040 JSON (structure)

```json
{
  "regional_results": {
    "China": { "region": "China", "cost_analysis": {...}, "demand_forecast": {...} },
    "USA": { "region": "USA", "cost_analysis": {...}, "demand_forecast": {...} },
    "Europe": { "region": "Europe", "cost_analysis": {...}, "demand_forecast": {...} },
    "Rest_of_World": { "region": "Rest_of_World", "cost_analysis": {...}, "demand_forecast": {...} }
  },
  "global_result": {
    "region": "Global",
    "years": [2015, 2016, ..., 2040],
    "market": [70000000, 72000000, ..., 105000000],
    "bev": [500000, 850000, ..., 85000000],
    "phev": [300000, 450000, ..., 2000000],
    "ice": [69200000, 70700000, ..., 18000000],
    "ev": [800000, 1300000, ..., 87000000]
  }
}
```

---

## Using Output Data

### Loading CSV in Python

```python
import pandas as pd

# Load regional forecast
df = pd.read_csv('output/China_2040.csv')

# Access columns
years = df['Year']
bev_demand = df['BEV']
market = df['Market']

# Calculate EV share
ev_share = df['EV'] / df['Market'] * 100

# Plot
import matplotlib.pyplot as plt
plt.plot(years, ev_share)
plt.xlabel('Year')
plt.ylabel('EV Market Share (%)')
plt.title('China EV Adoption Forecast')
plt.show()
```

### Loading JSON in Python

```python
import json

# Load regional forecast
with open('output/China_2040.json') as f:
    result = json.load(f)

# Access data
tipping_point = result['cost_analysis']['tipping_point']
bev_forecast = result['demand_forecast']['bev']
logistic_k = result['demand_forecast']['logistic_params']['k']

print(f"Tipping point: {tipping_point}")
print(f"Growth rate k: {logistic_k:.3f}")
```

### Loading JSON in Excel

1. Open Excel
2. Data → Get Data → From File → From JSON
3. Select `China_2040.json`
4. Power Query Editor opens
5. Expand nested objects (click expand icon next to column names)
6. Convert lists to tables
7. Load into worksheet

---

## Column Descriptions Summary

### CSV Columns

| Column | Type | Units | Description |
|--------|------|-------|-------------|
| Year | int | - | Forecast year |
| Market | float | vehicles/year | Total passenger vehicle demand |
| BEV | float | vehicles/year | Battery Electric Vehicle demand |
| PHEV | float | vehicles/year | Plug-in Hybrid demand |
| ICE | float | vehicles/year | Internal Combustion Engine demand |
| EV | float | vehicles/year | Total EV demand (BEV + PHEV) |
| EV_Cost | float | USD | EV cost curve value (regional only) |
| ICE_Cost | float | USD | ICE cost curve value (regional only) |

### JSON Fields

| Field | Type | Description |
|-------|------|-------------|
| region | string | Region name |
| tipping_point | int/null | Year of cost parity |
| ev_cagr | float | EV cost growth rate |
| ice_cagr | float | ICE cost growth rate |
| logistic_params.L | float | Maximum adoption share |
| logistic_params.k | float | Growth rate steepness |
| logistic_params.t0 | float | Inflection point year |
| validation.is_valid | boolean | Validation status |
| validation.message | string | Validation details |

---

## Best Practices

**For analysis**:
- Use CSV for quick visualization and Excel work
- Use JSON for programmatic processing
- Export both for comprehensive documentation

**For archiving**:
- Always include JSON to preserve metadata
- Tipping point and CAGRs are critical context
- Validation status documents forecast quality

**For sharing**:
- CSV is more accessible for non-technical stakeholders
- Include methodology documentation alongside outputs
- Clearly label forecast horizon and assumptions (e.g., "China_2040_ceiling_0.9.csv")

---

## Summary

**Key points**:
- Three output formats: CSV, JSON, both
- Regional CSV has 8 columns (includes cost data)
- Global CSV has 6 columns (demand only)
- JSON includes full metadata and validation results
- File naming follows pattern: `{Region}_{EndYear}.{ext}`
- Global exports create multiple CSVs but single JSON
- Always validate outputs: BEV + PHEV + ICE ≈ Market
