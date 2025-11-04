# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **cost-driven demand forecasting system** for analyzing technology transitions in passenger vehicles (EV, PHEV, ICE) across global regions. The system predicts when disruptor technologies (EVs) will achieve cost parity with incumbents (ICE vehicles) and models subsequent market adoption using logistic growth curves.

## Key Concepts

- **Tipping Point**: The cost parity year when disruptor cost < incumbent cost
- **Disruptor**: Electric Vehicles (BEV)
- **Chimera**: Plug-in Hybrid Vehicles (PHEV)
- **Incumbent**: Internal Combustion Engine vehicles (ICE)
- **Regions**: China, USA, Europe, Rest_of_World, Global (aggregated)

## Data Architecture

### Curves Catalog Structure
- **Location**: `curves_catalog_files/`
- **Format**: Split by entity (20 entities, 235 metrics, 825 datasets)
- **Key Entity**: `Passenger_Cars.json` contains all cost and demand curves for vehicle forecasting
- **Index**: `_index.json` provides metadata about available entities

### Data Format
Each entity file contains:
```json
{
  "Entity Name": {
    "Metric_Name": {
      "metadata": {
        "type": "...",
        "units": "...",
        "entity_type": "disruptor|incumbent|chimera|market"
      },
      "regions": {
        "China": {"X": [years], "Y": [values]},
        "Europe": {"X": [years], "Y": [values]},
        ...
      }
    }
  }
}
```

### Taxonomy Mapping
- **File**: `passenger_vehicles_taxonomy_and_datasets.json`
- **Purpose**: Maps product types (EV_Cars, BEV_Cars, PHEV_Cars, ICE_Cars) to dataset names
- **Entity Types**: Defines whether each product is disruptor, incumbent, chimera, or market

## Core Forecasting Methodology

Located in `instructions_editable.md`, the methodology follows this pipeline:

1. **Cost Curve Forecasting**: Log-CAGR extrapolation with 3-year rolling median smoothing
2. **Tipping Point Detection**: First year when EV cost < ICE cost
3. **Market Demand Forecast**: Linear extrapolation using Theil-Sen robust regression, capped at ±5% CAGR
4. **BEV Forecast**: Logistic curve fitting post-tipping: `s(t) = L / (1 + exp(-k * (t - t₀)))`
5. **PHEV Forecast**: "Hump" trajectory rising before tipping, decaying with 3-year half-life after
6. **ICE Forecast**: Residual calculation: `ICE = max(Market - BEV - PHEV, 0)`
7. **Validation**: Ensure BEV + PHEV + ICE ≤ Market, all values ≥ 0, smooth transitions

## Demand Forecasting Skill

### Location
`.claude/skills/demand-forecasting/`

### Module Structure
- `forecast.py` - Main orchestration (ForecastOrchestrator class)
- `data_loader.py` - Data loading utilities
- `cost_analysis.py` - Cost curve analysis and tipping point detection
- `demand_forecast.py` - Demand forecasting logic (logistic curves)
- `utils.py` - Helper functions
- `data/` - Self-contained datasets (Passenger_Cars.json, taxonomy, etc.)

### Running Forecasts

**Command Line:**
```bash
# Single region forecast
python3 .claude/skills/demand-forecasting/forecast.py --region China --end-year 2040 --ceiling 1.0 --output csv

# Global forecast (all regions + aggregation)
python3 .claude/skills/demand-forecasting/forecast.py --region Global --end-year 2040 --output both

# Custom EV ceiling (90% max adoption)
python3 .claude/skills/demand-forecasting/forecast.py --region Europe --ceiling 0.9 --output json
```

**Programmatic:**
```python
from forecast import ForecastOrchestrator

forecaster = ForecastOrchestrator(end_year=2040, logistic_ceiling=1.0)
result = forecaster.forecast_region("China")
global_result = forecaster.forecast_global()
forecaster.export_to_csv(result, "output.csv", "China")
```

### Parameters
- **region** (required): China, USA, Europe, Rest_of_World, or Global
- **end_year** (optional, default: 2040): Forecast horizon
- **logistic_ceiling** (optional, default: 1.0): Maximum EV adoption share (0.0-1.0)
- **output** (optional, default: csv): csv, json, or both

### Output Structure
**CSV format**: Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost

**JSON format**: Contains region, cost_analysis (tipping_point, CAGRs), demand_forecast (years, arrays)

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r .claude/skills/demand-forecasting/requirements.txt
```

### Testing
No formal test suite exists. Validate forecasts manually by:
1. Checking BEV + PHEV + ICE ≤ Market (with small epsilon)
2. Verifying smooth transitions near tipping year
3. Ensuring no negative values
4. Confirming physically realistic growth rates

## Critical Implementation Notes

1. **Regional Independence**: Each region is analyzed separately; Global is aggregated afterward (avoid double counting)

2. **Cost Curve Smoothing**: Always apply 3-year rolling median before tipping point detection to remove noise

3. **Logistic Fitting**: Uses scipy.optimize.differential_evolution with bounds:
   - k (slope): [0.05, 1.5]
   - t₀ (inflection): [min_year-5, max_year+10]

4. **Fallback Strategy**: If logistic convergence fails (<3 data points), seed with k=0.4, t₀=tipping_year or fall back to linear trend

5. **Numerical Stability**:
   - Clamp all shares to [0, 1]
   - Clamp all demands to [0, market]
   - Ensure no negative forecasts

6. **Data Consistency**: All costs must be in real USD, normalized basis (e.g., cost per mile or per vehicle at same trim level)

## Important Constraints

- Market CAGR capped at ±5% per year to prevent unrealistic growth/decline
- PHEV decay half-life: 3 years after tipping point
- Default logistic ceiling L = 1.0 (100%); use L = 0.9 if infrastructure/policy limits exist
- Tipping point determines transition dynamics for both disruptor and chimera

## Data Loading Pattern

```python
import json
import os

# Load taxonomy
with open('passenger_vehicles_taxonomy_and_datasets.json') as f:
    taxonomy = json.load(f)

# Load curves from catalog
with open('curves_catalog_files/Passenger_Cars.json') as f:
    curves = json.load(f)['Passenger Cars']

# Access specific metric
ev_cost_china = curves['EV_Cars_Cost']['regions']['China']
years = ev_cost_china['X']
costs = ev_cost_china['Y']
```

## Dependencies

- Python 3.7+
- numpy >= 1.20.0
- scipy >= 1.7.0 (for differential_evolution, Theil-Sen)
- pandas >= 1.3.0
- matplotlib >= 3.4.0 (for visualization)

## Repository Status

- Not a git repository (based on environment scan)
- No package.json, requirements.txt at root level
- Dependencies managed at skill level (`.claude/skills/demand-forecasting/requirements.txt`)
