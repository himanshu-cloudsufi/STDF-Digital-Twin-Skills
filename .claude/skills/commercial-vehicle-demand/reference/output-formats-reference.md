# Commercial Vehicle Demand Forecasting - Output Formats Reference

## CSV Format

### Structure
Segment-level rows + Total_CV aggregated rows

### Columns (Without Fleet Tracking)
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Region | string | Geographic region | China |
| Segment | string | LCV, MCV, HCV, or Total_CV | LCV |
| Year | int | Calendar year | 2030 |
| Market | float | Total segment demand (units) | 1500000 |
| EV | float | EV demand (units) | 450000 |
| ICE | float | ICE demand (units) | 900000 |
| NGV | float | NGV demand (units) | 150000 |
| EV_Share | float | EV share (0-1) | 0.30 |
| ICE_Share | float | ICE share (0-1) | 0.60 |
| NGV_Share | float | NGV share (0-1) | 0.10 |

### Columns (With Fleet Tracking)
Additional columns when `--track-fleet` is enabled:
| Column | Type | Description |
|--------|------|-------------|
| EV_Fleet | float | Cumulative EV fleet (units) |
| ICE_Fleet | float | Cumulative ICE fleet (units) |
| NGV_Fleet | float | Cumulative NGV fleet (units) |
| Total_Fleet | float | Total fleet (units) |

### Example CSV
```csv
Region,Segment,Year,Market,EV,ICE,NGV,EV_Share,ICE_Share,NGV_Share
China,LCV,2025,1500000,150000,1200000,150000,0.10,0.80,0.10
China,LCV,2030,1600000,500000,950000,150000,0.31,0.59,0.09
China,LCV,2040,1700000,1500000,180000,20000,0.88,0.11,0.01
China,MCV,2025,800000,50000,600000,150000,0.06,0.75,0.19
China,MCV,2030,850000,200000,550000,100000,0.24,0.65,0.12
China,MCV,2040,900000,650000,230000,20000,0.72,0.26,0.02
China,Total_CV,2025,5000000,400000,4200000,400000,0.08,0.84,0.08
China,Total_CV,2040,8000000,5600000,2200000,200000,0.70,0.28,0.03
```

## JSON Format

### Structure
Nested dictionary with regional, segment, and forecast data

### Top Level
```json
{
  "region": "China",
  "segment_results": { ... },
  "total_cv": { ... }
}
```

### Segment Results
```json
{
  "segment_results": {
    "LCV": {
      "cost_analysis": { ... },
      "demand_forecast": { ... }
    },
    "MCV": { ... },
    "HCV": { ... }
  }
}
```

### Cost Analysis
```json
{
  "cost_analysis": {
    "segment": "LCV",
    "tipping_point": 2028,
    "years_to_parity": 4,
    "ev_cagr": -0.048,
    "ice_cagr": 0.012,
    "current_ev_cost": 42000.0,
    "current_ice_cost": 38000.0,
    "current_cost_gap": -4000.0,
    "ev_cost_at_parity": 36500.0,
    "ice_cost_at_parity": 36800.0
  }
}
```

### Demand Forecast
```json
{
  "demand_forecast": {
    "segment": "LCV",
    "years": [2020, 2021, ..., 2040],
    "market": [1200000, 1250000, ..., 1700000],
    "ev": [80000, 100000, ..., 1500000],
    "ice": [1000000, 1050000, ..., 180000],
    "ngv": [120000, 100000, ..., 20000],
    "ev_share": [0.067, 0.080, ..., 0.882],
    "ice_share": [0.833, 0.840, ..., 0.106],
    "ngv_share": [0.100, 0.080, ..., 0.012],
    "tipping_point": 2028,
    "logistic_ceiling": 0.95,
    "ngv_metadata": {
      "model": "exponential_decline",
      "peak_info": {
        "peak_year": 2022,
        "peak_share": 0.12,
        "has_significant_presence": true
      },
      "decline_start_year": 2028,
      "half_life_years": 6.0,
      "final_share_2040": 0.012
    },
    "validation": {
      "is_valid": true,
      "message": "All validation checks passed"
    },
    "fleet": {
      "ev": [960000, 1100000, ..., 18000000],
      "ice": [12000000, 12500000, ..., 2000000],
      "ngv": [1440000, 1400000, ..., 180000],
      "total": [14400000, 15000000, ..., 20180000],
      "lifetime_years": 12.0
    }
  }
}
```

### Total CV Aggregated
```json
{
  "total_cv": {
    "region": "China",
    "years": [2020, 2021, ..., 2040],
    "market": [5000000, 5200000, ..., 8000000],
    "ev": [300000, 400000, ..., 5600000],
    "ice": [4300000, 4500000, ..., 2200000],
    "ngv": [400000, 300000, ..., 200000],
    "ev_share": [0.060, 0.077, ..., 0.700],
    "ice_share": [0.860, 0.865, ..., 0.275],
    "ngv_share": [0.080, 0.058, ..., 0.025]
  }
}
```

## Usage Examples

### Export Both Formats
```bash
python3 scripts/forecast.py --region China --all-segments --output both
```

Output:
- `output/commercial_vehicle_China_2040.csv`
- `output/commercial_vehicle_China_2040.json`

### Load CSV in Python
```python
import pandas as pd

df = pd.read_csv('output/commercial_vehicle_China_2040.csv')

# Filter for single segment
lcv_data = df[df['Segment'] == 'LCV']

# Filter for total CV
total_cv = df[df['Segment'] == 'Total_CV']

# Plot EV share over time
import matplotlib.pyplot as plt
plt.plot(lcv_data['Year'], lcv_data['EV_Share'], label='LCV')
plt.xlabel('Year')
plt.ylabel('EV Share')
plt.legend()
plt.show()
```

### Load JSON in Python
```python
import json

with open('output/commercial_vehicle_China_2040.json', 'r') as f:
    data = json.load(f)

# Access segment results
lcv_result = data['segment_results']['LCV']
tipping_point = lcv_result['cost_analysis']['tipping_point']

# Access time series
years = lcv_result['demand_forecast']['years']
ev_demand = lcv_result['demand_forecast']['ev']

# Access NGV metadata
ngv_metadata = lcv_result['demand_forecast']['ngv_metadata']
peak_year = ngv_metadata['peak_info']['peak_year']
```

## Data Validation

### CSV Validation
```python
# Check sum consistency
df['Sum'] = df['EV'] + df['ICE'] + df['NGV']
df['Diff'] = abs(df['Sum'] - df['Market']) / df['Market']
assert df['Diff'].max() < 0.02, "Sum consistency violated"

# Check share bounds
assert (df[['EV_Share', 'ICE_Share', 'NGV_Share']] >= 0).all().all()
assert (df[['EV_Share', 'ICE_Share', 'NGV_Share']] <= 1).all().all()

# Check non-negativity
assert (df[['Market', 'EV', 'ICE', 'NGV']] >= 0).all().all()
```

## See Also

- `SKILL.md`: Usage guide
- `methodology-reference.md`: Algorithm details
- `data-schema-reference.md`: Input data format
