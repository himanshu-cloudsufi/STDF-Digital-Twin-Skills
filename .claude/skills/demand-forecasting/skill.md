# Cost-Driven Demand Forecasting Skill

## Description
This skill performs cost-driven demand forecasting for passenger vehicles (EV, PHEV, ICE) across different regions using a logistic adoption model anchored to cost parity tipping points.

## Purpose
Use this skill when you need to:
- Forecast demand for EVs, PHEVs, and ICE vehicles by region
- Calculate cost parity tipping points between disruptor (EV) and incumbent (ICE) technologies
- Generate regional or global demand forecasts through 2040
- Analyze technology transition scenarios based on cost curves

## Instructions

When this skill is invoked, you will:

1. **Load datasets from the skill's data directory** (`.claude/skills/demand-forecasting/data/`)
   - `Passenger_Cars.json` - Contains all cost and demand curves
   - `passenger_vehicles_taxonomy_and_datasets.json` - Defines the taxonomy and dataset mappings
   - `instructions_editable.md` - Full methodology documentation

2. **Ask the user for parameters:**
   - **Region** (required): China, USA, Europe, Rest_of_World, or Global
   - **End Year** (optional, default: 2040): The forecast horizon
   - **Logistic Ceiling** (optional, default: 1.0): Maximum EV adoption share (0.0-1.0)
   - **Output Format** (optional, default: csv): csv, json, or plot

3. **Execute the forecasting pipeline:**

   ### Step 1: Load and Prepare Cost Data
   - Extract EV and ICE cost curves for the specified region from `Passenger_Cars.json`
   - Apply 3-year rolling median smoothing to remove noise
   - Convert to real USD if needed

   ### Step 2: Forecast Cost Curves
   - Transform cost series to log scale: `log(cost)`
   - Calculate long-term CAGR on log-transformed series
   - Forecast log series to end_year using CAGR
   - Convert back to normal scale via exponentiation
   - Combine historical and forecasted series

   ### Step 3: Determine Tipping Point
   - Find first year where EV cost < ICE cost
   - If EV always cheaper → tipping = first historical year
   - If ICE always cheaper → tipping = None (use baseline adoption)

   ### Step 4: Forecast Market Demand
   - Load historical market sales from `Passenger_Cars.json`
   - Use linear extrapolation (Theil-Sen robust regression) to end_year
   - Enforce: market_forecast ≥ 0
   - Optional: cap CAGR at ±5% per year

   ### Step 5: Forecast BEV Demand
   - Calculate historical BEV share: BEV_sales / Market_sales
   - If tipping in future: linearly extend recent share to tipping
   - Fit logistic curve post-tipping: `share(t) = L / (1 + exp(-k*(t-t₀)))`
     - Use scipy.optimize.differential_evolution
     - Bounds: k ∈ [0.05, 1.5], t₀ ∈ [min_year-5, max_year+10]
   - Convert to absolute: BEV_forecast = share × market_forecast
   - Clamp to [0, market_forecast]

   ### Step 6: Forecast PHEV Demand
   - Load historical PHEV data if available
   - Generate "hump" trajectory:
     - Rising phase before tipping
     - Decay after tipping with half-life ≈ 3 years
   - Keep continuous and smooth

   ### Step 7: Forecast ICE Demand
   - Residual calculation: ICE = max(Market - BEV - PHEV, 0)

   ### Step 8: Compute EV Demand
   - Aggregate: EV = BEV + PHEV
   - Clamp to [0, market_forecast]

   ### Step 9: Validate and Export
   - Ensure: BEV + PHEV + ICE ≤ Market (with small epsilon)
   - Ensure: all values ≥ 0
   - Validate smooth transitions near tipping year
   - Export results in requested format

4. **For Global Region:**
   - Run analysis for all individual regions (China, USA, Europe, Rest_of_World)
   - Report individual tipping points and cost curves
   - Aggregate demand forecasts: Global = sum of regions
   - Return both regional and global datasets

5. **Return the following outputs:**
   - Cost data (historical + forecasted) for EV and ICE
   - Demand data (historical + forecasted) for Market, BEV, PHEV, ICE, EV
   - Tipping point year
   - Summary statistics and validation checks
   - Visualizations (if requested)

## Implementation Details

### Data Loading
All data files are located in: `.claude/skills/demand-forecasting/data/`

Use the taxonomy file to map product types to dataset names:
```python
import json
import os

skill_dir = os.path.dirname(__file__)
data_dir = os.path.join(skill_dir, "data")

# Load taxonomy
with open(os.path.join(data_dir, "passenger_vehicles_taxonomy_and_datasets.json")) as f:
    taxonomy = json.load(f)

# Load curves
with open(os.path.join(data_dir, "Passenger_Cars.json")) as f:
    curves_data = json.load(f)["Passenger Cars"]
```

### Key Algorithms

**Cost Forecast (Log-CAGR Method):**
```python
import numpy as np

# Transform to log scale
log_costs = np.log(historical_costs)

# Calculate CAGR
years = np.array(historical_years)
slope, _ = np.polyfit(years, log_costs, 1)  # Linear fit on log scale
cagr = slope

# Forecast
future_years = np.arange(historical_years[-1] + 1, end_year + 1)
log_forecast = log_costs[-1] + cagr * (future_years - historical_years[-1])
forecast = np.exp(log_forecast)
```

**Tipping Point Detection:**
```python
def find_tipping_point(ev_costs, ice_costs, years):
    """Find first year where EV cost < ICE cost"""
    for i, year in enumerate(years):
        if ev_costs[i] < ice_costs[i]:
            return year
    return None
```

**Logistic Share Forecast:**
```python
from scipy.optimize import differential_evolution

def logistic(t, L, k, t0):
    return L / (1 + np.exp(-k * (t - t0)))

def fit_logistic(years, shares, L=1.0):
    def objective(params):
        k, t0 = params
        predicted = logistic(years, L, k, t0)
        return np.sum((shares - predicted) ** 2)

    bounds = [(0.05, 1.5), (min(years) - 5, max(years) + 10)]
    result = differential_evolution(objective, bounds)
    return result.x  # Returns [k, t0]
```

### Error Handling
- If convergence fails, fall back to linear trend (bounded by market)
- If history sparse (<3 points), seed with k=0.4, t₀=tipping_year
- Handle missing data gracefully with warnings
- Validate all outputs for physical consistency

## Usage Examples

### Example 1: Regional Forecast
```
User: "Run demand forecasting for China through 2040"

Expected behavior:
- Ask for any optional parameters (or use defaults)
- Load China cost and demand data
- Calculate tipping point
- Generate forecasts for Market, BEV, PHEV, ICE, EV
- Return results as CSV
```

### Example 2: Global Forecast
```
User: "Forecast global passenger vehicle demand with 90% EV ceiling"

Expected behavior:
- Set logistic ceiling L = 0.9
- Run analysis for all 4 regions
- Aggregate to global level
- Return regional and global datasets
```

### Example 3: Custom Analysis
```
User: "Show me the tipping point for Europe and plot the transition"

Expected behavior:
- Load Europe data
- Calculate and report tipping point year
- Generate visualization showing:
  - Cost parity crossover
  - Market share evolution
  - Demand trajectories
```

## Constraints and Best Practices

1. **Data Consistency:**
   - Ensure all costs in real USD
   - Use 3-year rolling median for smoothing
   - Validate region names match taxonomy

2. **Numerical Stability:**
   - Clamp all shares to [0, 1]
   - Clamp all demands to [0, market]
   - Ensure BEV + PHEV + ICE ≤ Market + ε

3. **Physical Realism:**
   - Cap market CAGR at ±5%
   - Use L < 1.0 if infrastructure/policy limits exist
   - PHEV decay half-life ≈ 3 years

4. **Performance:**
   - Cache intermediate results
   - Use vectorized numpy operations
   - Minimize file I/O

## Dependencies

Required Python packages:
- numpy
- scipy
- pandas
- matplotlib (for plotting)
- json (built-in)

## Notes

- All data is self-contained within the skill directory
- Taxonomy defines the mapping between product types and dataset names
- Cost curves must be forecasted before tipping point analysis
- Regional analysis is independent; global is an aggregation
- Follow the methodology exactly as described in `instructions_editable.md`
