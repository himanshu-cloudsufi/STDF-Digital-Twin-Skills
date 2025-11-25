# Two-Wheeler Demand Forecasting Methodology Reference

## Overview

This document provides detailed methodology for cost-driven two-wheeler demand forecasting with EV disruption analysis.

## 1. Cost Analysis and Tipping Point Detection

### 1.1 Cost Data Preparation

**Input Data:**
- EV Primary: `EV_2_Wheeler_(Range-100_KM)_Lowest_Cost_{Region}`
- ICE Baseline: `Two_Wheeler_(ICE)_Median_Cost_{Region}`

**Smoothing Algorithm:**
```
For each data point i:
  window = [i - floor(w/2), i + floor(w/2)]
  smoothed[i] = median(raw_data[window])
where w = smoothing_window (default: 3)
```

### 1.2 Cost Forecasting

**Log-CAGR Method:**
```
Step 1: Transform to log scale
  log_costs = ln(costs)

Step 2: Calculate CAGR
  CAGR = (costs[-1] / costs[0]) ^ (1 / n_years) - 1

Step 3: Extrapolate in log space
  For year y > last_historical_year:
    log_forecast[y] = log_costs[-1] + ln(1 + CAGR) × (y - last_year)

Step 4: Convert back to normal scale
  forecast[y] = exp(log_forecast[y])
```

### 1.3 Tipping Point Detection

**Algorithm:**
```
For each year y in forecast_years:
  diff[y] = EV_cost[y] - ICE_cost[y]

If all(diff > 0):
  tipping_point = None  # ICE always cheaper

Else if all(diff <= 0):
  tipping_point = first_year  # EV already cheaper

Else:
  Find first year where diff changes from positive to negative
  Linear interpolation for exact crossing year
```

## 2. Market Demand Forecasting

### 2.1 Trend Fitting

**Theil-Sen Robust Regression:**
```
Step 1: For all pairs of historical points (i, j):
  Calculate slope[i,j] = (demand[j] - demand[i]) / (year[j] - year[i])

Step 2: Robust slope estimate
  slope_fit = median(all slopes)
  intercept_fit = median(demand - slope_fit × year)

Step 3: Generate forecast
  For year y:
    demand_forecast[y] = slope_fit × y + intercept_fit
```

### 2.2 CAGR Constraint

**Application:**
```
For each forecast year y > last_historical_year:
  years_ahead = y - last_historical_year
  max_value = last_demand × (1 + max_cagr) ^ years_ahead
  min_value = last_demand × (1 - max_cagr) ^ years_ahead

  demand_forecast[y] = clip(demand_forecast[y], min_value, max_value)
  demand_forecast[y] = max(demand_forecast[y], 0)

where max_cagr = 0.05 (5% default)
```

## 3. EV Demand Forecasting

### 3.1 Historical Share Calculation

```
For each historical year:
  EV_share[y] = EV_sales[y] / Total_market[y]
  EV_share[y] = clip(EV_share[y], 0, 1)
```

### 3.2 Pre-Tipping Extrapolation

**Applicable when:** `tipping_year > last_historical_year`

```
Recent trend (last 5 years):
  slope = (share[-1] - share[-5]) / (year[-1] - year[-5])

For year y in [last_historical_year + 1, tipping_year]:
  extended_share[y] = share[-1] + slope × (y - last_historical_year)
  extended_share[y] = clip(extended_share[y], 0, 1)
```

### 3.3 Logistic S-Curve Fitting

**Logistic Function:**
```
s(t) = L / (1 + exp(-k × (t - t0)))

where:
  L = ceiling (max EV share, default: 0.9)
  k = growth rate (fitted, bounds: [0.05, 1.5])
  t0 = inflection point year (fitted, anchored near tipping)
```

**Fitting Algorithm (Differential Evolution):**
```
Objective function:
  minimize: Σ(historical_share - s(historical_year))²

Bounds:
  k ∈ [0.05, 1.5]
  t0 ∈ [tipping_year - 5, tipping_year + 10]

Optimization:
  Method: Differential Evolution
  Max iterations: 1000
  Tolerance: 1e-6
```

**Fallback for Sparse Data:**
```
If len(historical_share) < 3:
  Use default parameters:
    k = 0.4
    t0 = tipping_point (or year of max historical share)
```

### 3.4 EV Demand Conversion

```
For each forecast year y:
  EV_share[y] = s(y, L, k, t0)  # from logistic curve
  EV_demand[y] = EV_share[y] × Market_demand[y]
  EV_demand[y] = clip(EV_demand[y], 0, Market_demand[y])
```

## 4. ICE Demand Forecasting

**Residual Calculation:**
```
For each forecast year y:
  ICE_demand[y] = Market_demand[y] - EV_demand[y]
  ICE_demand[y] = max(ICE_demand[y], 0)
```

## 5. Fleet Evolution (Optional)

**Stock-Flow Accounting:**
```
Initialize:
  Fleet[0] = initial_fleet + Sales[0]

For year y = 1, 2, ..., n:
  Scrappage[y] = Fleet[y-1] / lifetime_years
  Fleet[y] = Fleet[y-1] + Sales[y] - Scrappage[y]

where:
  lifetime_years = 11 (two-wheelers)
```

## 6. Validation Framework

### 6.1 Sum Consistency Check

```
For each forecast year:
  total = EV_demand + ICE_demand
  relative_diff = |total - Market_demand| / Market_demand

  Pass if: relative_diff < 0.01 (1% tolerance)
```

### 6.2 Non-Negativity Check

```
Pass if:
  all(Market_demand >= 0)
  all(EV_demand >= 0)
  all(ICE_demand >= 0)
```

### 6.3 Share Bounds Check

```
For each forecast year:
  EV_share = EV_demand / Market_demand

  Pass if: 0 <= EV_share <= 1
```

### 6.4 Fleet Consistency (if tracking enabled)

```
For each year:
  Check: Fleet[y] >= 0
  Check: Scrappage[y] >= 0
  Check: |Fleet[y] - (Fleet[y-1] + Sales[y] - Scrappage[y])| < 0.01
```

## 7. Regional Aggregation

**Global Calculation:**
```
For each year y:
  Global_Market[y] = Σ(Regional_Market[region, y])
  Global_EV[y] = Σ(Regional_EV[region, y])
  Global_ICE[y] = Σ(Regional_ICE[region, y])

where regions = {China, USA, Europe, Rest_of_World}
```

## 8. Key Assumptions

1. **Cost Parity Drives Adoption**: EV share accelerates after tipping point
2. **Logistic Growth**: Market adoption follows S-curve pattern
3. **Market Independence**: Regional markets evolve independently
4. **11-Year Vehicle Life**: Average lifetime for fleet calculations
5. **No Supply Constraints**: Demand-side modeling only
6. **Comparable Segments**: EV-100km range comparable to mainstream ICE

## 9. Uncertainty Considerations

- **High Confidence**: China market (extensive historical data)
- **Medium Confidence**: Europe, USA (moderate data coverage)
- **Lower Confidence**: Rest_of_World (aggregated, varied data quality)
- **Forecast Uncertainty**: Increases with time horizon (±10% by 2030, ±15% by 2030, ±20% by 2035)

## 10. Model Limitations

1. Does not account for:
   - Policy interventions (subsidies, bans)
   - Infrastructure constraints (charging, battery swapping)
   - Supply chain disruptions
   - Technological breakthroughs (battery improvements)
   - Consumer preference shifts unrelated to cost

2. Assumes:
   - Continuous market evolution
   - No discontinuous shocks
   - Cost forecasts materialize as predicted
   - Historical relationships persist

## References

- Logistic Growth Models: Bass (1969), Rogers (2003)
- Theil-Sen Regression: Theil (1950), Sen (1968)
- Technology Adoption: Moore (2014), Christensen (1997)
- Two-Wheeler Market Analysis: Industry reports (2020-2024)
