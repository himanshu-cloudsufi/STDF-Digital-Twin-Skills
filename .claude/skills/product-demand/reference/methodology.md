# Product Demand Forecasting Methodology

## Overview

This document describes the detailed algorithms and methods used for forecasting product demand across different technology types and market contexts.

## Core Forecasting Pipeline

The forecasting system follows a multi-stage pipeline:

1. **Market Context Analysis** - Determine if market is disrupted
2. **Product Classification** - Identify product type (disruptor, incumbent, chimera, market)
3. **Method Selection** - Route to appropriate forecasting algorithm
4. **Forecast Generation** - Apply selected method
5. **Validation** - Check consistency and physical plausibility

---

## 1. Cost Curve Forecasting

### Purpose
Forecast future cost trajectories for disruptor and incumbent technologies to identify cost parity (tipping point).

### Method: Log-CAGR Extrapolation

```
1. Load historical cost data (years, costs)
2. Apply 3-year rolling median smoothing to reduce noise
3. Calculate CAGR on log scale: CAGR = exp(slope(log(years), log(costs))) - 1
4. Extrapolate to end_year using log-linear relationship
5. Clamp to physically realistic bounds
```

### Smoothing Rationale
- Cost data often contains year-to-year volatility
- 3-year window balances noise reduction with trend preservation
- Rolling median more robust to outliers than moving average

### CAGR Calculation
```python
log_costs = np.log(costs)
slope = theil_sen_slope(years, log_costs)  # Robust linear regression
cagr = np.exp(slope) - 1
```

---

## 2. Tipping Point Detection

### Purpose
Identify the year when disruptor technology achieves cost parity with incumbent.

### Method: Cost Curve Intersection

```
1. Forecast both disruptor and incumbent cost curves to end_year
2. Interpolate to common annual time grid
3. Find first year where: disruptor_cost < incumbent_cost
4. Return tipping_point_year or None if no crossover by end_year
```

### Edge Cases
- **No tipping point found**: Market is not disrupted yet; use baseline forecasting
- **Historical tipping point**: Tipping point in past; use post-tipping dynamics
- **Multiple crossovers**: Take first intersection (conservative estimate)

---

## 3. Market Demand Forecast

### Purpose
Forecast total market size (denominator for share calculations).

### Method: Linear Extrapolation with CAGR Cap

```
1. Load historical market demand (years, demand)
2. Calculate robust trend using Theil-Sen estimator
3. Extrapolate linearly to end_year
4. Cap CAGR at ±5% per year (config: market_cagr_cap)
5. Clamp to non-negative values
```

### CAGR Capping Rationale
- Markets rarely grow/decline >5% annually over long periods
- Prevents unrealistic extrapolations from short-term volatility
- User-configurable via config.json

---

## 4. Disruptor Forecasting

### Purpose
Model exponential S-curve adoption of disruptor technology post-tipping.

### Method: Logistic Curve Fitting

The logistic function models adoption share:

```
s(t) = L / (1 + exp(-k * (t - t0)))

where:
  L  = ceiling (maximum adoption share, typically 1.0)
  k  = growth rate (steepness of S-curve)
  t0 = inflection point (typically near tipping point)
  t  = year
```

### Fitting Process

```
1. Calculate historical shares: share = product_demand / market_demand
2. Fit logistic curve using differential evolution optimization
3. Parameter bounds:
   - L: [0.5, 1.0] (allow for incomplete adoption)
   - k: [0.05, 1.5] (10-50 year adoption timescales)
   - t0: [tipping_year - 5, end_year + 10]
4. Use tipping_year as seed for t0
5. If fitting fails (<3 data points), fall back to linear extrapolation
```

### Share-to-Demand Conversion

```
forecast_demand(t) = forecast_share(t) × market_forecast(t)
```

### Fallback Strategy

If logistic fitting fails:
1. Try seeded parameters (k=0.4, t0=tipping_year)
2. Use linear extrapolation of historical shares
3. Cap share growth at 10% per year
4. Flag forecast as "linear_fallback" in metadata

---

## 5. Chimera Forecasting

### Purpose
Model transitional technologies that rise before disruption, then decay.

### Method: Hump Trajectory

Chimera products (e.g., PHEVs) follow a characteristic "hump" pattern:

**Pre-Tipping Phase:**
```
share(t) = peak_share × (t - t_start) / (t_tipping - t_start)

where:
  peak_share = 0.15 (15% max market share, configurable)
  t_start = first historical data year
  t_tipping = tipping point year
```

**Post-Tipping Phase (Exponential Decay):**
```
share(t) = peak_share × exp(-λ × (t - t_tipping))

where:
  λ = ln(2) / half_life
  half_life = 3 years (configurable)
```

### Demand Calculation

```
demand(t) = share(t) × market_forecast(t)
```

### Rationale
- Chimeras serve as bridge during cost gap period
- Peak near tipping point when uncertainty is highest
- Decay as disruptor proves superior and scales
- Half-life of 3 years reflects rapid technology maturation

---

## 6. Incumbent Forecasting

### Purpose
Calculate incumbent demand as residual after disruptors and chimeras capture share.

### Method: Residual Calculation

```
1. Forecast market_demand(t)
2. Forecast disruptor_demand(t) for all disruptor products
3. Forecast chimera_demand(t) for all chimera products
4. Calculate: incumbent_demand(t) = market_demand(t) - Σ(disruptors) - Σ(chimeras)
5. Clamp to non-negative: incumbent_demand(t) = max(0, incumbent_demand(t))
```

### Considerations
- **Sum constraint**: BEV + PHEV + ICE ≤ Market (enforced via max(0, ...))
- **Smooth transitions**: Validate no abrupt changes year-over-year
- **Physical bounds**: Demand cannot go negative

### Validation
```
tolerance = 0.001  # 0.1% tolerance
assert sum(components) <= market * (1 + tolerance)
assert all(components >= 0)
```

---

## 7. Baseline Forecasting (Non-Disrupted Markets)

### Purpose
Simple trend extrapolation for markets without active disruption.

### Method: Linear Bounded Extrapolation

```
1. Load historical demand data
2. Calculate Theil-Sen slope (robust linear regression)
3. Extrapolate to end_year
4. Cap CAGR at ±5% per year
5. Clamp to non-negative values
```

### When Used
- No tipping point detected
- Insufficient data for disruption analysis
- User explicitly requests baseline forecast

---

## 8. Validation and Consistency Checks

### Pre-Flight Checks
- [ ] All required data available (cost, demand, taxonomy)
- [ ] Region parameter valid
- [ ] End year reasonable (2025-2100)
- [ ] Historical data quality sufficient (≥3 points)

### Post-Forecast Checks
- [ ] No negative demand values
- [ ] Sum constraint satisfied (components ≤ market)
- [ ] Smooth year-over-year transitions (<50% jumps)
- [ ] CAGRs physically plausible (<20%)
- [ ] Logistic parameters reasonable (k ∈ [0.05, 1.5])

### Validation Actions
If validation fails:
1. Log warning with details
2. Apply correction (smoothing, clamping, interpolation)
3. Flag in output metadata
4. Optionally halt forecast (if critical error)

---

## 9. Special Cases and Edge Handling

### Sparse Data (<3 Historical Points)
- Skip logistic fitting
- Use linear extrapolation
- Flag as "insufficient_data"

### Data Gaps in Time Series
- Linear interpolation between available points
- Flag gaps in metadata
- Consider data quality score

### No Tipping Point Found
- Use conservative baseline forecast
- Report "no cost parity by [end_year]"
- Disruptor adoption remains slow (k < 0.1)

### Logistic Convergence Failure
1. Retry with seeded parameters
2. Fall back to linear trend
3. Use recent historical trend only
4. Flag as "convergence_failed"

### Unrealistic CAGR (>±20%)
- Cap at ±5% for market forecasts
- Cap at ±10% for product forecasts
- Flag anomaly in output metadata

---

## 10. Regional Aggregation (Global Forecasts)

### Method
```
1. Forecast each region independently (China, USA, Europe, Rest_of_World)
2. Sum regional forecasts by year
3. Validate sum constraints at global level
4. No double-counting (each unit sold in exactly one region)
```

### Regional Independence
- Each region has own tipping point
- Cost curves may differ by region
- Market dynamics vary (policy, infrastructure, consumer preferences)

---

## 11. Numerical Stability

### Clamping and Bounding
```python
# Share clamping
shares = np.clip(shares, 0.0, 1.0)

# Demand clamping
demand = np.clip(demand, 0.0, market_forecast)

# CAGR capping
if cagr > max_cagr:
    cagr = max_cagr
elif cagr < -max_cagr:
    cagr = -max_cagr
```

### Avoiding Division by Zero
```python
share = demand / max(market, 1e-10)  # Avoid divide-by-zero
```

### Floating Point Precision
- Use numpy arrays (float64 precision)
- Validate sum constraints with epsilon tolerance
- Round output for display, keep full precision internally

---

## 12. Algorithm Complexity

### Time Complexity
- **Cost analysis**: O(N) where N = number of historical years
- **Logistic fitting**: O(M × K) where M = differential evolution iterations, K = population size
- **Demand forecast**: O(T) where T = forecast horizon years
- **Overall**: O(T + M × K) ≈ O(100 + 100 × 15) = O(1500) operations

### Space Complexity
- O(T) for storing forecast arrays
- Minimal memory footprint (<1 MB per forecast)

---

## References

### Key Techniques
- **Theil-Sen Estimator**: Robust linear regression resistant to outliers
- **Differential Evolution**: Global optimization for nonlinear parameter fitting
- **Logistic Growth**: Classic S-curve model for technology adoption
- **Wright's Law**: Exponential cost decline with cumulative production

### Literature
- Rogers, E. (1962). *Diffusion of Innovations*
- Wright, T. (1936). *Factors Affecting the Cost of Airplanes*
- Seba, T. (2014). *Clean Disruption of Energy and Transportation*
- Farmer, J.D. & Lafond, F. (2016). *How predictable is technological progress?*

---

## Glossary

- **Tipping Point**: Year when disruptor cost < incumbent cost
- **Disruptor**: Technology that displaces incumbents via superior cost/performance
- **Incumbent**: Legacy technology being displaced
- **Chimera**: Transitional hybrid technology
- **CAGR**: Compound Annual Growth Rate
- **LCOE**: Levelized Cost of Energy
- **S-Curve**: Sigmoid adoption curve (slow → fast → slow)
