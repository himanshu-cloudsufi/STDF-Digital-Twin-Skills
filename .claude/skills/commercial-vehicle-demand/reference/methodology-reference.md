# Commercial Vehicle Demand Forecasting - Methodology Reference

## Overview

This document provides detailed algorithms for commercial vehicle demand forecasting with segment-level analysis (LCV, MCV, HCV) and three-powertrain modeling (EV, ICE, NGV).

## 1. Cost Curve Forecasting

### Algorithm
```
For each segment S in {LCV, MCV, HCV}:
  1. Load historical cost data:
     - EV: segment-specific range cost (LCV: 100km, MCV: 200km, HCV: 400km)
     - ICE: segment price data

  2. Apply smoothing:
     smoothed_cost[i] = median(cost[i-1:i+2])  // 3-year rolling window

  3. Forecast using log-CAGR:
     log_cost_future = log_cost_last + log(1 + CAGR) * years_ahead
     cost_future = exp(log_cost_future)

  4. Find tipping point:
     tipping_year[S] = min{t : EV_cost[S,t] < ICE_cost[S,t]}
```

### Key Parameters
- Smoothing window: 3 years (configurable)
- Log-scale extrapolation reduces wild swings
- Segment-specific tipping points expected

## 2. Market Demand Forecasting

### Algorithm
```
For each segment S:
  1. Load historical market data (total CV sales for segment)

  2. Fit Theil-Sen robust regression:
     market[t] = a + b*t
     where (a,b) minimize median absolute deviation

  3. Apply CAGR cap:
     CAGR = (market[last] / market[first])^(1/years) - 1
     if |CAGR| > max_CAGR:
        CAGR = sign(CAGR) * max_CAGR

  4. Extrapolate forward:
     market[t_future] = market[last] * (1 + CAGR)^(t_future - t_last)
```

### Key Parameters
- Max CAGR: ±5% (prevents unrealistic growth)
- Theil-Sen: robust to outliers

## 3. EV Adoption Modeling

### Algorithm
```
For each segment S with ceiling L[S]:
  1. Calculate historical EV share:
     share[t] = EV[t] / Market[t]

  2. Pre-tipping extrapolation (if tipping > hist_last):
     Extend share linearly to tipping point

  3. Fit logistic curve:
     share(t) = L[S] / (1 + exp(-k * (t - t0)))

     Optimize (k, t0) to minimize:
     sum((historical_share - predicted_share)^2)

     Bounds:
     - k ∈ [0.05, 1.5]  // growth rate
     - t0 ∈ [tipping-5, tipping+10]  // inflection point

  4. Generate forecast:
     EV[S,t] = share(t) * Market[S,t]
```

### Segment-Specific Ceilings
- LCV: 95% (easier to electrify, shorter routes)
- MCV: 85% (moderate challenges)
- HCV: 75% (range/weight constraints)

## 4. NGV Chimera Modeling

### Algorithm
```
For each segment S:
  1. Peak detection:
     peak_year = argmax(NGV_share[t])
     peak_share = max(NGV_share)

  2. Check significance:
     if peak_share < min_threshold (1%):
        return NGV = 0  (no significant presence)

  3. Determine decline start:
     decline_start = max(peak_year, tipping_point[S])

  4. Model decline:
     For t <= decline_start:
        NGV_share[t] = peak_share

     For t > decline_start:
        years_since = t - decline_start
        decay = exp(-log(2) * years_since / half_life)
        NGV_share[t] = peak_share * decay

  5. Apply 2035 constraint:
     if t >= 2035:
        NGV_share[t] = min(NGV_share[t], target_2035)  // typically 0%

  6. Convert to absolute:
     NGV[S,t] = NGV_share[t] * Market[S,t]
```

### Key Parameters
- Half-life: 6 years (default)
- Peak detection window: 5 years (smoothing)
- Target 2035 share: 0% (near-zero)
- Min significant share: 1%

### Rationale
NGV acts as a bridge technology:
- Policy-driven adoption (subsidies, clean air mandates)
- Peaks as infrastructure builds out
- Declines as EV TCO becomes competitive
- Near-zero by 2035 due to EV dominance

## 5. ICE Residual Calculation

### Algorithm
```
For each segment S and year t:
  ICE[S,t] = Market[S,t] - EV[S,t] - NGV[S,t]
  ICE[S,t] = max(0, ICE[S,t])  // enforce non-negativity
```

### Interpretation
- ICE is the "residual" after EV adoption and NGV decline
- Represents conventional diesel/gasoline vehicles
- Gradually declines as EV share grows
- May persist longer in HCV due to range needs

## 6. Multi-Level Aggregation

### Segment to Total CV
```
For each year t:
  Total_Market[t] = LCV_Market[t] + MCV_Market[t] + HCV_Market[t]
  Total_EV[t] = LCV_EV[t] + MCV_EV[t] + HCV_EV[t]
  Total_ICE[t] = LCV_ICE[t] + MCV_ICE[t] + HCV_ICE[t]
  Total_NGV[t] = LCV_NGV[t] + MCV_NGV[t] + HCV_NGV[t]
```

### Regional to Global
```
For each year t:
  Global_Market[t] = China[t] + USA[t] + Europe[t] + RoW[t]
  // Same for EV, ICE, NGV
```

## 7. Fleet Evolution (Optional)

### Stock-Flow Accounting
```
For each powertrain P and segment S:
  Fleet[P,S,t=0] = initial_fleet

  For t = 1 to T:
    scrappage[t] = Fleet[P,S,t-1] / lifetime[S]
    Fleet[P,S,t] = Fleet[P,S,t-1] + Sales[P,S,t] - scrappage[t]
```

### Segment-Specific Lifetimes
- LCV: 12 years (delivery vans, light trucks)
- MCV: 15 years (medium trucks)
- HCV: 18 years (heavy haulers, long-haul)

## 8. Validation Rules

### Three-Powertrain Consistency
```
For each segment S and year t:
  assert: EV[S,t] + ICE[S,t] + NGV[S,t] ≈ Market[S,t]
  tolerance: ±2%
```

### Segment Aggregation
```
For each year t:
  assert: sum(LCV, MCV, HCV) ≈ Total_CV
  tolerance: ±2%
```

### Non-Negativity
```
assert: all values >= 0
```

### Share Bounds
```
For all powertrains P:
  assert: 0 <= share[P] <= 1.0
  assert: sum(EV_share, ICE_share, NGV_share) ≈ 1.0
```

### NGV Decline
```
assert: NGV_share[2035] near zero
assert: NGV declining after peak/tipping
```

## 9. Sensitivity Analysis

### Key Sensitivities
1. **Segment Ceilings**: ±5% impacts final EV share by ±3-5%
2. **Tipping Point**: ±2 years shifts adoption curve by 1-3 years
3. **NGV Half-Life**: ±1 year changes 2030 NGV share by ±15-20%
4. **Market Growth Rate**: ±1% CAGR changes 2030 market size by ±8-12%

### Robustness
- Theil-Sen regression robust to outliers
- Log-CAGR prevents exponential explosion
- CAGR caps prevent unrealistic growth
- Residual ICE calculation ensures consistency

## 10. Computational Complexity

- Cost analysis: O(S * R) where S=segments, R=regions
- Demand forecast: O(S * R * T) where T=time steps
- Logistic fitting: O(iterations) ≈ 1000 per segment
- Total runtime: ~30-60 seconds for full global forecast

## References

1. Theil-Sen Regression: Non-parametric robust regression
2. Differential Evolution: Global optimization for logistic fitting
3. Stock-Flow Accounting: System dynamics modeling
4. Exponential Decay: Half-life modeling for chimera technologies

## See Also

- `SKILL.md`: User guide and usage examples
- `parameters-reference.md`: Complete parameter catalog
- `output-formats-reference.md`: Output schema details
- `data-schema-reference.md`: Input data requirements
