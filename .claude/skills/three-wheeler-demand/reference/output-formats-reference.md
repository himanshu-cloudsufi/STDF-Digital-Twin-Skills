# Output Formats Reference - Three-Wheeler Demand Forecasting

## CSV Output Format

### File Naming Convention

**Single Region:**
```
three_wheeler_{Region}_{EndYear}.csv
```
Example: `three_wheeler_China_2030.csv`

**Global:**
```
three_wheeler_Global_{EndYear}_global.csv  # Aggregated global
three_wheeler_{Region}_{EndYear}.csv        # Individual regions
```

### Standard CSV Schema (without --track-fleet)

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| Year | int | year | Forecast year |
| Market | float | units | Total three-wheeler demand (all powertrains) |
| EV | float | units | EV three-wheeler demand |
| ICE | float | units | ICE three-wheeler demand |
| EV_Share | float | % | EV market share (0-100) |
| ICE_Share | float | % | ICE market share (0-100) |
| EV_Cost | float | USD | EV cost per vehicle (real terms) |
| ICE_Cost | float | USD | ICE cost per vehicle (real terms) |

**Example:**
```csv
Year,Market,EV,ICE,EV_Share,ICE_Share,EV_Cost,ICE_Cost
2020,25000000,8000000,17000000,32.0,68.0,1200.50,1500.00
2025,26500000,12000000,14500000,45.3,54.7,1050.25,1520.00
2030,28000000,19000000,9000000,67.9,32.1,900.00,1550.00
2035,29000000,24500000,4500000,84.5,15.5,825.00,1590.00
2040,30000000,27000000,3000000,90.0,10.0,800.00,1650.00
```

### Extended CSV Schema (with --track-fleet)

**Additional Columns:**

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| EV_Fleet | float | units | Cumulative EV three-wheeler fleet (installed base) |
| ICE_Fleet | float | units | Cumulative ICE three-wheeler fleet (installed base) |
| Total_Fleet | float | units | Total three-wheeler fleet (EV + ICE) |

**Example:**
```csv
Year,Market,EV,ICE,EV_Share,ICE_Share,EV_Cost,ICE_Cost,EV_Fleet,ICE_Fleet,Total_Fleet
2020,25000000,8000000,17000000,32.0,68.0,1200.50,1500.00,45000000,185000000,230000000
2025,26500000,12000000,14500000,45.3,54.7,1050.25,1520.00,65000000,175000000,240000000
2030,28000000,19000000,9000000,67.9,32.1,900.00,1550.00,95000000,140000000,235000000
2035,29000000,24500000,4500000,84.5,15.5,825.00,1590.00,135000000,90000000,225000000
2040,30000000,27000000,3000000,90.0,10.0,800.00,1650.00,175000000,50000000,225000000
```

## JSON Output Format

### File Naming Convention

```
three_wheeler_{Region}_{EndYear}.json
```

### JSON Schema

```json
{
  "region": "string",
  "cost_analysis": {
    "years": [int],
    "ev_costs": [float],
    "ice_costs": [float],
    "tipping_point": int | null,
    "years_to_parity": int | null,
    "ev_cagr": float,
    "ice_cagr": float,
    "current_ev_cost": float,
    "current_ice_cost": float,
    "current_cost_gap": float,
    "years_with_ev_advantage": int,
    "max_ev_cost_advantage": float,
    "ev_cost_at_parity": float | null,
    "ice_cost_at_parity": float | null,
    "ev_historical_years": [int],
    "ev_historical_costs": [float],
    "ice_historical_years": [int],
    "ice_historical_costs": [float]
  },
  "demand_forecast": {
    "years": [int],
    "market": [float],
    "ev": [float],
    "ice": [float],
    "validation": {
      "is_valid": bool,
      "message": "string"
    },
    "historical": {
      "market_years": [int],
      "market_demand": [float],
      "ev_years": [int],
      "ev_demand": [float]
    },
    "parameters": {
      "tipping_point": int | null,
      "logistic_ceiling": float,
      "end_year": int
    },
    "ev_fleet": [float],    // optional, if --track-fleet
    "ice_fleet": [float],   // optional, if --track-fleet
    "total_fleet": [float]  // optional, if --track-fleet
  }
}
```

### Example JSON Output

```json
{
  "region": "China",
  "cost_analysis": {
    "years": [2020, 2021, ..., 2040],
    "ev_costs": [1200.5, 1150.2, ..., 800.0],
    "ice_costs": [1500.0, 1510.5, ..., 1650.0],
    "tipping_point": 2026,
    "years_to_parity": 2,
    "ev_cagr": -0.0215,
    "ice_cagr": 0.0048,
    "current_ev_cost": 1050.25,
    "current_ice_cost": 1520.00,
    "current_cost_gap": 469.75,
    "years_with_ev_advantage": 15,
    "max_ev_cost_advantage": 850.0,
    "ev_cost_at_parity": 980.0,
    "ice_cost_at_parity": 980.0
  },
  "demand_forecast": {
    "years": [2020, 2021, ..., 2040],
    "market": [25000000, 25500000, ..., 30000000],
    "ev": [8000000, 9500000, ..., 27000000],
    "ice": [17000000, 16000000, ..., 3000000],
    "validation": {
      "is_valid": true,
      "message": "All validation checks passed"
    },
    "parameters": {
      "tipping_point": 2026,
      "logistic_ceiling": 0.9,
      "end_year": 2030
    }
  }
}
```

## Global Output (Region=Global)

### Structure

When forecasting with `--region Global`, the output includes:

**CSV Files:**
- `three_wheeler_Global_2040_global.csv` - Aggregated global totals
- `three_wheeler_China_2030.csv` - China regional forecast
- `three_wheeler_Europe_2030.csv` - Europe regional forecast
- `three_wheeler_Rest_of_World_2030.csv` - Rest_of_World regional forecast

**JSON File:**
- `three_wheeler_Global_2030.json` - Contains all regional forecasts + global

### Global JSON Schema

```json
{
  "regional_results": {
    "China": { /* full regional result */ },
    "Europe": { /* full regional result */ },
    "Rest_of_World": { /* full regional result */ }
  },
  "global_result": {
    "region": "Global",
    "years": [int],
    "market": [float],
    "ev": [float],
    "ice": [float]
  }
}
```

## Data Types and Precision

### Numeric Types

- **Integers**: Year (4 digits, e.g., 2040)
- **Floats**: Demand, costs (rounded to 2 decimal places in CSV)
- **Percentages**: Share values (1 decimal place, e.g., 45.3%)

### Units

- **Demand**: Units (vehicles) per year
- **Fleet**: Units (vehicles) - cumulative installed base
- **Cost**: USD per vehicle (real terms, base year in data)
- **Share**: Percentage (0-100)
- **CAGR**: Decimal (e.g., 0.05 for 5%)

## Reading Output Files

### Python Example

```python
import pandas as pd
import json

# Read CSV
df = pd.read_csv('output/three_wheeler_China_2030.csv')
print(df[['Year', 'Market', 'EV', 'ICE']])

# Read JSON
with open('output/three_wheeler_China_2030.json', 'r') as f:
    result = json.load(f)
    tipping = result['cost_analysis']['tipping_point']
    print(f"Tipping point: {tipping}")
```

### Excel Import

1. Open Excel
2. Data → From Text/CSV
3. Select the CSV file
4. Delimiter: Comma
5. Data type detection: Automatic

### R Example

```r
# Read CSV
df <- read.csv('output/three_wheeler_China_2030.csv')
head(df)

# Read JSON
library(jsonlite)
result <- fromJSON('output/three_wheeler_China_2030.json')
tipping <- result$cost_analysis$tipping_point
```

## Output Directory Structure

```
.claude/skills/three-wheeler-demand/output/
├── three_wheeler_China_2030.csv
├── three_wheeler_China_2030.json
├── three_wheeler_Europe_2030.csv
├── three_wheeler_Rest_of_World_2030.csv
├── three_wheeler_Global_2040_global.csv
└── three_wheeler_Global_2030.json
```

## Notes

1. **Missing Values**: Represented as empty cells in CSV, `null` in JSON
2. **Precision**: Floats rounded to 2 decimals for readability (full precision in JSON)
3. **Timestamp**: Files do not include generation timestamp (use file metadata)
4. **Overwriting**: Output files are overwritten if they exist
5. **Encoding**: UTF-8 for all text files
