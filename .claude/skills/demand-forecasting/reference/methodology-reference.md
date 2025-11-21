# Cost-Driven Demand Forecasting Methodology

Complete algorithm details, mathematical formulas, and implementation guidance for passenger vehicle demand forecasting.

## Contents
- Scope and Regional Analysis
- Step 1: Tipping Point Detection
- Step 2: Market Demand Forecasting
- Step 3: BEV Demand Forecasting
- Step 4: PHEV Demand Forecasting
- Step 5: ICE Demand Forecasting
- Step 6: EV Aggregation
- Validation Rules
- Edge Cases and Fallback Strategies
- Best Practices

---

## Scope and Regional Analysis

### Regional Independence
- Treat each region (China, USA, Europe, Rest_of_World) independently
- Compute regional demand forecasts separately
- Each region has its own cost curves and tipping point

### Global Aggregation
- If Global forecast is requested, sum regions carefully
- Avoid double counting
- Global = China + USA + Europe + Rest_of_World

### Tipping Point Definition
**Tipping Point = Cost Parity Year** when disruptor cost < incumbent cost for the first time.

---

## Step 1: Tipping Point Detection

### Data Sources
- **Disruptor cost**: EV_Cars_Cost dataset for the region
- **Incumbent cost**: ICE_Cars_Cost dataset for the region

### Cost Curve Preparation

**1. Apply 3-Year Rolling Median Smoothing**
- Smooth noisy cost curves before comparison
- Window size: 3 years (configurable)
- Formula: For each point, take median of [i-1, i, i+1]

**2. Forecast Cost Curves (Log-CAGR Method)**

Steps for each cost series (EV and ICE):
1. Convert cost time series to logarithmic form: `log(cost)`
2. Compute long-term CAGR (compound annual growth rate) on log-transformed series
3. Forecast log series forward using computed CAGR until end_year
4. Convert forecasted log series back to normal values: `exp(log_forecast)`
5. Combine historical and forecasted series

Mathematical formula:
```
log_cost(t) = log_cost(t-1) + CAGR_log
cost(t) = exp(log_cost(t))
```

Where:
- `CAGR_log` is computed from historical log(cost) series
- Extrapolation continues until `end_year` (default 2030)

### Intersection Detection Logic

**Case 1: Disruptor crosses below incumbent**
- Tipping point = first year when EV cost < ICE cost
- Use smoothed, forecasted curves for comparison
- Identify first intersection year

**Case 2: Disruptor always cheaper**
- If EV cost < ICE cost for all historical years
- Tipping point = first year in historical series
- EV already has cost advantage

**Case 3: Incumbent always cheaper**
- If ICE cost < EV cost for all years (including forecast)
- Tipping point = None
- Fall back to slow/baseline adoption pattern

---

## Step 2: Market Demand Forecasting

### Data Source
- Historical dataset: `Passenger_Vehicle_Annual_Sales_<Region>`

### Forecasting Method

**Linear Extrapolation with Robust Slope**
- Use Theil-Sen or median regression for long-term slope
- Extrapolate to end_year (default 2030)
- More robust than ordinary least squares

Mathematical formula:
```
market(t) = market(t_last) + slope × (t - t_last)
```

### Constraints

**1. Non-negativity**
```
market_forecast(y) ≥ 0 for all years
```

**2. CAGR Capping (Optional but Recommended)**
- Cap annual CAGR between –5% and +5%
- Prevents unrealistic growth or decline
- Configurable parameter: `max_market_cagr = 0.05`

Formula:
```
If CAGR > max_market_cagr:
    CAGR = max_market_cagr
If CAGR < -max_market_cagr:
    CAGR = -max_market_cagr
```

---

## Step 3: BEV Demand Forecasting

### Historical Share Calculation

**Compute share for historical years:**
```
share(y) = BEV_sales(y) / Market_sales(y)
```

Skip years where Market_sales = 0 to avoid division by zero.

### Pre-Tipping Extension

**If tipping point is in the future:**
- Extend recent share trend linearly to tipping year
- Clamp between 0 and 1
- Maintains smooth transition to post-tipping growth

### Post-Tipping Forecast: Logistic Curve

**Logistic Growth Formula:**
```
s(t) = L / (1 + exp(-k × (t - t₀)))
```

Where:
- `s(t)` = BEV market share at year t
- `L` = Logistic ceiling (maximum adoption, default 1.0 = 100%)
- `k` = Growth rate parameter (slope steepness)
- `t₀` = Inflection point year (typically near tipping point)

### Parameter Fitting

**Use scipy.optimize.differential_evolution**

**Parameter bounds:**
- `k` ∈ [0.05, 1.5] (from config)
- `t₀` ∈ [min(years) - 5, max(years) + 10] (from config)
- `L` is fixed (user-provided ceiling, default 1.0)

**Objective function:**
Minimize sum of squared errors between fitted curve and historical shares.

**Fallback strategy if convergence fails:**
1. Check if historical data has < 3 points
2. Seed with default values:
   - k = 0.4
   - t₀ = tipping_year
3. If still fails, fall back to linear trend bounded by market forecast

### Convert Share to Absolute Demand

```
BEV_forecast(y) = share_forecast(y) × market_forecast(y)
```

**Clamp to valid range:**
```
BEV_forecast(y) = clamp(BEV_forecast(y), 0, market_forecast(y))
```

---

## Step 4: PHEV Demand Forecasting

### Strategy

**Option 1: Use Historical/External Forecast** (if available)
- If PHEV dataset exists with future projections, use directly

**Option 2: Generate "Hump" Trajectory** (if no forecast)
- PHEVs rise before tipping, decline after tipping
- Models transition technology behavior

### Hump Trajectory Model

**Rising Phase (before tipping):**
- Grow PHEV share linearly or logistically
- Peak around tipping year
- Typical peak share: 10-15% of market

**Decaying Phase (after tipping):**
- Exponential decay with half-life ≈ 3 years (configurable)
- Formula:
```
PHEV(t) = PHEV(tipping) × exp(-λ × (t - tipping))
```

Where:
- λ = ln(2) / half_life
- half_life = 3 years (from config: `phev_decay_half_life`)

**Continuity requirement:**
- No sharp drops or jumps at tipping year
- Smooth transition between rising and decaying phases

---

## Step 5: ICE Demand Forecasting

### Residual Calculation

ICE vehicles fill remaining market demand after BEV and PHEV:

```
ICE(y) = max(market_forecast(y) - BEV(y) - PHEV(y), 0)
```

**Non-negativity guarantee:**
- If BEV + PHEV exceed market, ICE = 0
- Never allow negative ICE demand

---

## Step 6: EV Aggregation

### Combined EV Sales

Aggregate BEV and PHEV into total EV sales:

```
EV(y) = BEV(y) + PHEV(y)
```

**Clamp to valid range:**
```
EV(y) = clamp(EV(y), 0, market_forecast(y))
```

---

## Validation Rules

### Rule 1: Non-Negative Demand
```
BEV(y) ≥ 0
PHEV(y) ≥ 0
ICE(y) ≥ 0
Market(y) ≥ 0
```

### Rule 2: Sum Consistency
```
BEV(y) + PHEV(y) + ICE(y) ≤ Market(y) + ε
```

Where ε is a small tolerance (e.g., 0.01% of market) for floating-point rounding.

### Rule 3: Share Bounds
```
BEV_share(y) ∈ [0, 1]
PHEV_share(y) ∈ [0, 1]
ICE_share(y) ∈ [0, 1]
```

### Rule 4: Smooth Transitions
- No unrealistic jumps near tipping year
- Growth should be gradual and continuous

---

## Edge Cases and Fallback Strategies

### Sparse Historical Data

**If < 3 historical data points:**
- Cannot reliably fit logistic curve
- Seed logistic parameters:
  - k = 0.4 (moderate growth rate)
  - t₀ = tipping_year
- Alternative: Use linear extrapolation instead

### Logistic Convergence Failure

**If differential_evolution fails to converge:**
1. Try with seeded initial values
2. Reduce parameter bounds
3. Fall back to linear trend:
   ```
   share(t) = share(t_last) + slope × (t - t_last)
   ```
   Bounded by [0, logistic_ceiling]

### No Tipping Point Detected

**If tipping_point = None (ICE always cheaper):**
- Use slow adoption baseline
- Apply very conservative growth rate (k < 0.1)
- Or maintain current share with minimal growth

### Historical Data Gaps

**If historical series has gaps:**
- Interpolate linearly between available points
- Flag interpolated regions for user awareness
- Use only non-interpolated points for slope calculation

---

## Best Practices

### Data Consistency

**Ensure consistent cost basis:**
- All costs in real USD (inflation-adjusted)
- Normalized for product configuration (same trim level)
- Or use cost per mile/km for fair comparison

**Apply smoothing:**
- Always use 3-year rolling median before tipping point detection
- Removes noise and outliers
- Makes intersection detection robust

### Numerical Stability

**Clamping strategy:**
- Clamp all shares to [0, 1] after computation
- Clamp all demands to [0, market] after computation
- Check sum consistency and adjust proportionally if needed

**Floating-point considerations:**
- Use epsilon tolerance for equality checks
- Avoid exact zero comparisons
- Sum consistency check should allow small epsilon

### Regional Analysis

**Regional boundaries:**
- Treat each region independently
- Do not share parameters across regions
- Each region has unique tipping point and growth trajectory

**Rest of World calculation:**
```
Rest_of_World = World_Total − (China + USA + Europe)
```

### Adoption Ceilings

**When to use L < 1.0:**
- Physical infrastructure limits (charging network gaps)
- Policy constraints (regulations, incentives)
- Market segments that resist electrification (rural, commercial)

**Common ceiling values:**
- L = 1.0 (100%): Full market electrification possible
- L = 0.9 (90%): Realistic with good infrastructure
- L = 0.8 (80%): Conservative scenario with constraints

### Parameter Sensitivity

**Key parameters that affect results:**
- `logistic_ceiling`: Higher ceiling = more aggressive EV adoption
- `k bounds`: Wider range = more flexible fitting, but less stability
- `phev_decay_half_life`: Shorter = faster PHEV phase-out
- `max_market_cagr`: Lower cap = more conservative market growth

**Recommended approach:**
- Use defaults for most analyses
- Adjust ceiling based on regional infrastructure
- Keep other parameters stable unless specific reason to change

---

## Recommended Default Values

From config.json:

- **Forecast horizon**: 2040 (`end_year`)
- **Logistic ceiling**: 1.0 (`logistic_ceiling`)
- **Smoothing window**: 3 years (`smoothing_window`)
- **Market CAGR cap**: ±5% (`max_market_cagr`)
- **PHEV peak share**: 15% (`phev_peak_share`)
- **PHEV decay half-life**: 3 years (`phev_decay_half_life`)
- **Logistic k bounds**: [0.05, 1.5] (`logistic_k_bounds`)
- **Logistic t₀ offset**: [-5, 10] years from min/max (`logistic_t0_offset`)

---

## Example Flow Summary

**Complete forecasting sequence:**

1. **Select region** (e.g., China)
2. **Forecast cost curves** for EV and ICE using log-CAGR method
3. **Compute tipping point** = first intersection year of EV vs ICE cost curves
4. **Forecast market demand** using linear extrapolation with CAGR cap
5. **Compute EV historical share** and fit logistic curve to project future EV sales
6. **Use PHEV forecast** from data or generate hump model
7. **Derive ICE** = Market − BEV − PHEV (clamped to ≥ 0)
8. **Aggregate EV** = BEV + PHEV
9. **Validate**:
   - BEV + PHEV + ICE ≤ Market
   - All values ≥ 0
   - Smooth transitions near tipping year
   - Shares in [0, 1]

**For Global forecast:**
1. Run steps 1-9 for each region independently
2. Sum regional demands to get global totals
3. Validate global aggregates

---

## Implementation Notes

### Python Libraries Used

- **numpy**: Array operations, interpolation
- **scipy.optimize.differential_evolution**: Logistic curve fitting
- **scipy.stats.theilslopes**: Robust linear regression (Theil-Sen)
- **pandas**: Data handling and CSV export
- **matplotlib**: Visualization (optional)

### Key Functions

Located in `scripts/` directory:

- **scripts/utils.py**:
  - `rolling_median()`: 3-year rolling median smoothing
  - `log_cagr_forecast()`: Log-CAGR cost curve forecasting
  - `find_intersection()`: Cost curve intersection detection
  - `linear_extrapolation()`: Theil-Sen linear forecasting
  - `clamp_array()`: Array clamping to valid ranges
  - `validate_forecast_consistency()`: Sum consistency validation

- **scripts/cost_analysis.py**:
  - `CostAnalyzer`: Handles cost curve preparation and tipping point detection

- **scripts/demand_forecast.py**:
  - `DemandForecaster`: Handles all demand forecasting logic (market, BEV, PHEV, ICE)

- **scripts/forecast.py**:
  - `ForecastOrchestrator`: Main orchestration class that runs complete pipeline

### Configuration

All default parameters are defined in `config.json`. Reference that file for current values.
