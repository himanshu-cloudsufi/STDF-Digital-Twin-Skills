# Cost-Driven Demand Forecasting Skill

This skill performs comprehensive cost-driven demand forecasting for passenger vehicles, analyzing the transition from ICE (Internal Combustion Engine) to EV (Electric Vehicle) technology across different global regions.

## Overview

The skill implements a sophisticated forecasting methodology that:
- Analyzes cost curves to determine technology tipping points
- Forecasts market demand using robust statistical methods
- Models technology adoption using logistic growth curves
- Generates forecasts for BEV, PHEV, ICE, and total EV demand
- Supports both regional and global analyses

## Directory Structure

```
demand-forecasting/
├── skill.md                    # Main skill instructions for Claude
├── README.md                   # This file
├── config.json                 # Configuration parameters
├── requirements.txt            # Python dependencies
├── forecast.py                 # Main orchestration module
├── data_loader.py              # Data loading utilities
├── cost_analysis.py            # Cost curve analysis and tipping points
├── demand_forecast.py          # Demand forecasting logic
├── utils.py                    # Helper functions
└── data/                       # Self-contained datasets
    ├── Passenger_Cars.json                              # Cost and demand curves
    ├── passenger_vehicles_taxonomy_and_datasets.json    # Taxonomy definitions
    ├── instructions_editable.md                         # Full methodology
    └── [other curve catalog files]
```

## Data Sources

All data is self-contained within the `data/` directory:

1. **Passenger_Cars.json**: Contains historical cost and demand curves for:
   - EV costs (by region)
   - ICE costs (by region)
   - Market sales (by region)
   - BEV sales (by region)
   - PHEV sales (by region)
   - ICE sales (by region)

2. **passenger_vehicles_taxonomy_and_datasets.json**: Maps product types to dataset names

3. **instructions_editable.md**: Complete methodology documentation

## Usage

### As a Claude Code Skill

Simply invoke the skill in Claude Code:

```
Use the demand-forecasting skill to forecast EV adoption in China through 2040
```

Claude will:
1. Load the skill instructions
2. Ask for necessary parameters
3. Execute the forecasting pipeline
4. Return comprehensive results

### Command Line Usage

You can also run the forecaster directly from the command line:

```bash
# Forecast for a single region
python3 forecast.py --region China --end-year 2040 --ceiling 1.0 --output csv

# Forecast for global (all regions + aggregation)
python3 forecast.py --region Global --end-year 2040 --output both --output-dir ./results

# Custom EV ceiling (90% max adoption)
python3 forecast.py --region Europe --ceiling 0.9 --output json
```

### Programmatic Usage

```python
from forecast import ForecastOrchestrator

# Initialize orchestrator
forecaster = ForecastOrchestrator(
    end_year=2040,
    logistic_ceiling=1.0
)

# Forecast a single region
result = forecaster.forecast_region("China")

# Forecast global (all regions)
global_result = forecaster.forecast_global()

# Export results
forecaster.export_to_csv(result, "china_forecast.csv", "China")
```

## Methodology

### 1. Cost Analysis

- Loads EV and ICE cost curves for the specified region
- Applies 3-year rolling median smoothing
- Forecasts costs using log-CAGR method
- Determines tipping point (cost parity year)

### 2. Market Forecast

- Extrapolates total market demand using Theil-Sen robust regression
- Caps growth at ±5% CAGR
- Ensures non-negative forecasts

### 3. BEV Forecast

- Calculates historical market share
- Extends share to tipping point if needed
- Fits logistic curve for post-tipping adoption
- Converts share to absolute demand

### 4. PHEV Forecast

- Uses historical data if available
- Otherwise generates "hump" trajectory
- Rises before tipping, decays exponentially after

### 5. ICE Forecast

- Calculated as residual: ICE = Market - BEV - PHEV
- Ensures non-negative values

### 6. Validation

- Ensures BEV + PHEV + ICE ≤ Market
- Validates smooth transitions
- Checks for physical consistency

## Parameters

### Required
- **region**: China, USA, Europe, Rest_of_World, or Global

### Optional
- **end_year**: Forecast horizon (default: 2040)
- **logistic_ceiling**: Maximum EV adoption share, 0-1 (default: 1.0)
- **output**: csv, json, or both (default: csv)

## Output Format

### CSV Output
```csv
Year,Market,BEV,PHEV,ICE,EV,EV_Cost,ICE_Cost
2020,20000000,1000000,500000,18500000,1500000,35000,25000
2025,22000000,3000000,800000,18200000,3800000,28000,26000
...
```

### JSON Output
```json
{
  "region": "China",
  "cost_analysis": {
    "tipping_point": 2023,
    "ev_cagr": -0.08,
    "ice_cagr": 0.02,
    ...
  },
  "demand_forecast": {
    "years": [...],
    "market": [...],
    "bev": [...],
    ...
  }
}
```

## Dependencies

- Python 3.7+
- numpy >= 1.20.0
- scipy >= 1.7.0
- pandas >= 1.3.0
- matplotlib >= 3.4.0

Install with:
```bash
pip install -r requirements.txt
```

## Key Features

1. **Self-Contained**: All data included in skill directory
2. **Robust Methods**: Uses Theil-Sen regression, rolling medians
3. **Validated**: Extensive consistency checks
4. **Flexible**: Configurable parameters and ceilings
5. **Regional & Global**: Supports both individual and aggregated analyses
6. **Production-Ready**: Error handling, logging, and validation

## Examples

### Example 1: Basic Regional Forecast
```python
forecaster = ForecastOrchestrator()
result = forecaster.forecast_region("USA")
```

### Example 2: Conservative Forecast (90% ceiling)
```python
forecaster = ForecastOrchestrator(logistic_ceiling=0.9)
result = forecaster.forecast_region("Europe")
```

### Example 3: Global Analysis
```python
forecaster = ForecastOrchestrator(end_year=2050)
global_result = forecaster.forecast_global()
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install dependencies with `pip install -r requirements.txt`
2. **FileNotFoundError**: Ensure you're running from the skill directory
3. **ValueError (missing region)**: Check region name matches exactly (case-sensitive)

### Validation Warnings

- "Sum exceeds market": Usually due to historical data inconsistencies, forecasts are automatically adjusted
- "Logistic fit failed": Falls back to linear trend with sensible defaults

## Version History

- **v1.0.0** (2024): Initial release with full methodology implementation

## License

This skill is provided as-is for forecasting purposes. Data sources and methodology are documented in `instructions_editable.md`.

## Support

For questions about the methodology, refer to `data/instructions_editable.md`.
For implementation questions, review the inline documentation in the Python modules.
