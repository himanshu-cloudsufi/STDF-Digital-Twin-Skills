# Forecasting Parameters Reference

## Overview

This document describes all configurable parameters used in the product demand forecasting system, including their meanings, typical ranges, and effects on forecast outputs.

---

## Configuration Parameters

### Location
`.claude/skills/product-demand/config.json`

---

## 1. Core Forecast Parameters

### `end_year`

**Type**: Integer
**Default**: `2040`
**Range**: `2025` to `2100`
**Units**: Year

**Description**:
The final year of the forecast horizon. All forecasts extend from the most recent historical data year to `end_year`.

**Effect on Output**:
- Longer horizons increase uncertainty
- Computational cost scales linearly: O(end_year - start_year)
- Typical range: 15-30 years ahead

**Usage**:
```bash
python product_forecast.py --end-year 2050
```

**Recommendations**:
- **Short-term (5-10 years)**: Higher confidence, useful for near-term planning
- **Medium-term (10-20 years)**: Balance of confidence and strategic insight
- **Long-term (20+ years)**: Scenario planning, low confidence on specifics

---

### `logistic_ceiling` (L)

**Type**: Float
**Default**: `1.0`
**Range**: `0.5` to `1.0`
**Units**: Fraction (share)

**Description**:
Maximum market share a disruptor technology can achieve. Represents the ceiling of the logistic S-curve.

**Mathematical Role**:
```
s(t) = L / (1 + exp(-k * (t - t0)))
```

**Effect on Output**:
- **L = 1.0** (100%): Complete market takeover (incumbent goes to zero)
- **L = 0.9** (90%): 10% niche remains for incumbent (e.g., collectors, specific use cases)
- **L = 0.8** (80%): 20% incumbent share persists indefinitely

**When to Adjust**:
- **Reduce L** if:
  - Niche segments cannot adopt disruptor (e.g., classic car enthusiasts)
  - Infrastructure limits exist (e.g., grid capacity for EVs)
  - Regulatory barriers persist
  - Geographic constraints apply

- **Keep L = 1.0** if:
  - Disruptor has universal applicability
  - No fundamental adoption barriers exist
  - Cost advantage is overwhelming and permanent

**Examples**:
```json
// EVs in developed markets (excellent infrastructure)
"logistic_ceiling": 0.95

// EVs in developing markets (infrastructure constraints)
"logistic_ceiling": 0.85

// Solar PV (can't provide 100% baseload without storage)
"logistic_ceiling": 0.70
```

---

### `market_cagr_cap`

**Type**: Float
**Default**: `0.05` (5% per year)
**Range**: `0.01` to `0.15`
**Units**: Decimal (0.05 = 5%)

**Description**:
Maximum compound annual growth rate (CAGR) allowed for market demand forecasts. Prevents unrealistic exponential extrapolations.

**Effect on Output**:
- **Cap = 0.05** (5%): Conservative, suitable for mature markets
- **Cap = 0.10** (10%): Moderate, for growing markets
- **Cap = 0.15** (15%): Aggressive, for emerging high-growth markets

**Application**:
```
If calculated_cagr > market_cagr_cap:
    cagr = market_cagr_cap
elif calculated_cagr < -market_cagr_cap:
    cagr = -market_cagr_cap
```

**Rationale**:
- Historical vehicle markets rarely sustain >5% growth over decades
- Prevents short-term trends from dominating long-term forecasts
- Ensures physical and economic realism

**When to Adjust**:
- **Increase cap** for:
  - Emerging markets with rapid urbanization
  - New product categories in early growth phase
  - Short-term forecasts (5-10 years) where trends may persist

- **Decrease cap** for:
  - Saturated markets (e.g., developed country passenger vehicles)
  - Long-term forecasts (20+ years) requiring conservatism
  - Declining markets (use negative cap)

**Examples**:
```json
// Mature passenger vehicle market (USA, Europe)
"market_cagr_cap": 0.03

// Growing commercial vehicle market (India, Southeast Asia)
"market_cagr_cap": 0.08

// Declining incumbent energy market (coal in OECD)
"market_cagr_cap": -0.05
```

---

### `smoothing_window`

**Type**: Integer
**Default**: `3`
**Range**: `1` to `7`
**Units**: Years

**Description**:
Size of the rolling median window for cost curve smoothing. Reduces year-to-year noise in historical data.

**Effect on Output**:
- **Window = 1**: No smoothing (use raw data)
- **Window = 3**: Moderate smoothing (default)
- **Window = 5**: Heavy smoothing (for very noisy data)
- **Window = 7**: Very heavy smoothing (may lose real trends)

**Trade-offs**:
- **Larger window**: More noise reduction, but lags recent changes
- **Smaller window**: More responsive to recent trends, but noisier

**When to Adjust**:
- **Increase window** if:
  - Historical data is very noisy (annual volatility >20%)
  - One-time shocks distort trends (e.g., COVID-19, supply chain disruptions)
  - Long-term trend matters more than recent fluctuations

- **Decrease window** if:
  - Data is already smooth
  - Recent structural changes are important (e.g., policy shift)
  - Forecast horizon is short (5-10 years)

**Examples**:
```json
// Clean, well-documented cost data
"smoothing_window": 3

// Noisy commodity price data
"smoothing_window": 5

// Recent data reflects structural change
"smoothing_window": 1
```

---

## 2. Disruption-Specific Parameters

### `chimera_decay_half_life`

**Type**: Float
**Default**: `3.0`
**Range**: `1.0` to `10.0`
**Units**: Years

**Description**:
Number of years for chimera technology market share to decay to half its peak value after tipping point. Controls the "hump" decay rate.

**Mathematical Role**:
```
share_post_tipping(t) = peak_share × exp(-λ × (t - t_tipping))

where λ = ln(2) / half_life
```

**Effect on Output**:
- **Half-life = 1 year**: Rapid decay (chimera quickly irrelevant)
- **Half-life = 3 years**: Moderate decay (default for PHEVs)
- **Half-life = 5 years**: Slow decay (chimera persists longer)
- **Half-life = 10 years**: Very slow decay (chimera coexists with disruptor)

**Interpretation**:
- Year 0 (tipping): Chimera at peak share
- Year 3: Chimera at 50% of peak
- Year 6: Chimera at 25% of peak
- Year 9: Chimera at 12.5% of peak

**When to Adjust**:
- **Shorten half-life** if:
  - Disruptor clearly superior to chimera (no trade-offs)
  - Technology matures rapidly
  - Consumer preference shifts quickly

- **Lengthen half-life** if:
  - Chimera has persistent advantages (e.g., PHEV range flexibility)
  - Slow infrastructure rollout favors hybrid solutions
  - Market segmentation supports multiple technologies

**Examples**:
```json
// PHEVs (clear trend toward BEVs)
"chimera_decay_half_life": 3.0

// Natural gas vehicles (lingering infrastructure)
"chimera_decay_half_life": 5.0

// Hybrid powertrains in commercial vehicles
"chimera_decay_half_life": 7.0
```

---

### `phev_peak_share`

**Type**: Float
**Default**: `0.15` (15%)
**Range**: `0.05` to `0.30`
**Units**: Fraction (market share)

**Description**:
Maximum market share chimera technology achieves at tipping point. Represents the peak of the "hump" trajectory.

**Effect on Output**:
- **Peak = 0.10** (10%): Chimera is niche solution
- **Peak = 0.15** (15%): Moderate chimera role (default for PHEVs)
- **Peak = 0.25** (25%): Chimera is significant competitor
- **Peak = 0.30** (30%): Chimera nearly matches disruptor temporarily

**When to Adjust**:
- **Increase peak** if:
  - Chimera addresses major disruptor weakness (e.g., PHEV range anxiety)
  - Regulatory support for chimera (subsidies, HOV lane access)
  - Slow infrastructure rollout creates demand for bridge solution

- **Decrease peak** if:
  - Chimera offers minimal advantages
  - High cost or complexity limits adoption
  - Disruptor achieves early cost parity

**Examples**:
```json
// PHEVs in Europe (strong diesel legacy, gradual EV shift)
"phev_peak_share": 0.20

// PHEVs in China (rapid BEV adoption, less PHEV interest)
"phev_peak_share": 0.10

// Natural gas commercial vehicles (niche fleet use)
"phev_peak_share": 0.08
```

---

## 3. Logistic Curve Parameters

These parameters are **optimized automatically** by the fitting algorithm, but understanding them helps interpret results.

### `k` (Growth Rate)

**Type**: Float
**Fit Range**: `0.05` to `1.5`
**Units**: 1/year (inverse time)

**Description**:
Steepness of the logistic S-curve. Higher k = faster adoption transition.

**Interpretation**:
```
Adoption speed (years to go from 10% to 90%):
Δt = ln(81) / k ≈ 4.4 / k

k = 0.1  → ~44 years (very slow)
k = 0.2  → ~22 years (slow)
k = 0.4  → ~11 years (moderate)
k = 0.6  → ~7 years (fast)
k = 1.0  → ~4 years (very fast)
```

**Typical Values**:
- **Passenger EVs**: k ≈ 0.3-0.5 (10-15 year adoption post-tipping)
- **Solar PV**: k ≈ 0.4-0.6 (7-11 year adoption)
- **Commercial EVs**: k ≈ 0.2-0.4 (11-22 year adoption, slower due to fleet turnover)

**Not Configurable**: Automatically fitted from historical data.

---

### `t0` (Inflection Point)

**Type**: Float
**Fit Range**: `[tipping_year - 5, end_year + 10]`
**Units**: Year

**Description**:
Year when adoption rate is maximum (midpoint of S-curve). Typically occurs 1-5 years after tipping point.

**Interpretation**:
- If `t0 = tipping_year + 2`: Rapid acceleration after cost parity
- If `t0 = tipping_year + 5`: Slow initial uptake, then acceleration
- If `t0 < tipping_year`: Adoption accelerating before cost parity (policy-driven or anticipation)

**Not Configurable**: Automatically fitted from historical data.

---

## 4. Regional Parameters

### `regions`

**Type**: List of strings
**Default**: `["China", "USA", "Europe", "Rest_of_World", "Global"]`

**Description**:
Supported region codes for forecasting.

**Usage**:
```bash
python product_forecast.py --region China
```

**Notes**:
- "Global" is computed as sum of other regions, not forecasted independently
- "India" is included for two-wheeler and three-wheeler markets

---

## 5. Output Parameters

### `output_formats`

**Type**: List of strings
**Default**: `["csv", "json", "both"]`

**Description**:
Supported output formats.

**Options**:
- **csv**: Comma-separated values, easy to import into Excel/Sheets
- **json**: Full metadata, validation results, intermediate calculations
- **both**: Generate both CSV and JSON outputs

**Usage**:
```bash
python product_forecast.py --output both
```

---

## 6. Advanced Parameters (Internal)

These parameters are **not user-configurable** but are important for understanding the system.

### Logistic Fitting Convergence

**max_iterations**: 100
**population_size**: 15
**tolerance**: 1e-6

Differential evolution parameters for logistic curve optimization.

### CAGR Bounds for Product Forecasts

**max_product_cagr**: 0.20 (20% per year)
Used to prevent absurd extrapolations in product demand.

### Validation Tolerances

**sum_constraint_tolerance**: 0.001 (0.1%)
**smoothness_threshold**: 0.50 (50% year-over-year change)
**negative_value_tolerance**: 1e-10 (essentially zero)

---

## 7. Parameter Tuning Guidelines

### Calibration Process

1. **Start with defaults**: Most users should not change config.json
2. **Validate with known cases**: Test against existing EV forecasts
3. **Adjust conservatively**: Change one parameter at a time
4. **Document changes**: Keep notes on why parameters were modified
5. **Sensitivity analysis**: Test impact of ±20% parameter changes

### Common Adjustments

| Scenario | Parameter | Suggested Value |
|----------|-----------|-----------------|
| Emerging high-growth market | market_cagr_cap | 0.10 (10%) |
| Mature saturated market | market_cagr_cap | 0.02 (2%) |
| Infrastructure constraints | logistic_ceiling | 0.85 (85%) |
| Rapid technology maturation | chimera_decay_half_life | 2.0 years |
| Noisy historical cost data | smoothing_window | 5 years |
| Short-term forecast (5-10y) | end_year | 2030 |
| Long-term scenario (20-30y) | end_year | 2050 |

---

## 8. Parameter Interactions

### Ceiling vs. Growth Rate

Higher ceiling (L) + higher growth rate (k) = aggressive forecast
Lower ceiling (L) + lower growth rate (k) = conservative forecast

**Balanced defaults**: L=1.0, k fitted from data (typically 0.3-0.5)

### Market Cap vs. Smoothing

Higher market_cagr_cap + lower smoothing_window = more responsive to recent trends
Lower market_cagr_cap + higher smoothing_window = more stable long-term view

**Balanced defaults**: cap=0.05, window=3

---

## 9. Validation and Bounds

### Automatic Validation

The system enforces these constraints automatically:

```python
# Shares bounded to [0, 1]
share = np.clip(share, 0.0, 1.0)

# Demand bounded to [0, market]
demand = np.clip(demand, 0.0, market_forecast)

# CAGR bounded by config
if cagr > config['market_cagr_cap']:
    cagr = config['market_cagr_cap']

# Logistic parameters bounded during fitting
bounds = {
    'L': [0.5, 1.0],
    'k': [0.05, 1.5],
    't0': [min_year - 5, max_year + 10]
}
```

---

## 10. Parameter Effects Summary Table

| Parameter | ↑ Increase Effect | ↓ Decrease Effect |
|-----------|-------------------|-------------------|
| **end_year** | Longer horizon, more uncertainty | Shorter horizon, higher confidence |
| **logistic_ceiling** | Higher disruptor peak share | More persistent incumbent share |
| **market_cagr_cap** | Faster market growth allowed | More conservative market growth |
| **smoothing_window** | Smoother trends, less noise | More responsive to recent data |
| **chimera_decay_half_life** | Chimera persists longer | Chimera fades faster |
| **phev_peak_share** | Chimera more important at peak | Chimera niche role only |

---

## Examples

### Conservative Forecast (Mature Market)

```json
{
  "default_parameters": {
    "end_year": 2035,
    "logistic_ceiling": 0.90,
    "market_cagr_cap": 0.03,
    "smoothing_window": 5,
    "chimera_decay_half_life": 5.0,
    "phev_peak_share": 0.12
  }
}
```

### Aggressive Forecast (Emerging Market)

```json
{
  "default_parameters": {
    "end_year": 2045,
    "logistic_ceiling": 0.98,
    "market_cagr_cap": 0.10,
    "smoothing_window": 2,
    "chimera_decay_half_life": 2.0,
    "phev_peak_share": 0.08
  }
}
```

---

For usage examples with these parameters, see [examples.md](examples.md).
