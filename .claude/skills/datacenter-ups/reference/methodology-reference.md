# Datacenter UPS Battery Technology Transition Methodology

Complete algorithm details, mathematical formulas, and implementation guidance for VRLA → Li-ion technology transition forecasting.

## Contents

- [Overview](#overview)
- [Step 1: Cost Forecasting](#step-1-cost-forecasting)
- [Step 2: Total Cost of Ownership (TCO) Calculation](#step-2-total-cost-of-ownership-tco-calculation)
- [Step 3: Tipping Point Detection](#step-3-tipping-point-detection)
- [Step 4: S-Curve Adoption Modeling](#step-4-s-curve-adoption-modeling)
- [Step 5: Market Demand Forecasting](#step-5-market-demand-forecasting)
- [Step 6: Technology Split](#step-6-technology-split)
- [Step 7: Installed Base Accounting](#step-7-installed-base-accounting)
- [Step 8: Market Decomposition](#step-8-market-decomposition)
- [Step 9: Battery Metrics Calculation](#step-9-battery-metrics-calculation)
- [Validation Framework](#validation-framework)
- [Mathematical Notation](#mathematical-notation)

---

## Overview

The Datacenter UPS Battery Transition model forecasts the economic-driven shift from VRLA (Valve-Regulated Lead-Acid) to Lithium-ion batteries in datacenter UPS systems. The model operates through a sequential pipeline:

```
Cost Forecasting → TCO Calculation → Tipping Point → S-Curve Adoption →
Market Forecast → Technology Split → Installed Base → Market Decomposition
```

**Key Principles:**
- **Economic Rationality**: Adoption driven by Total Cost of Ownership (TCO) advantage
- **Technology Dynamics**: VRLA (incumbent, 5-year life) vs Li-ion (disruptor, 12-year life)
- **Regional Independence**: Each region computed separately; Global = sum of regions
- **Time Horizon**: 2020-2030 (extended: 2035, configurable), annual time steps
- **Primary Units**: GWh/year (demand flows), GWh (installed base stocks), $/kWh (costs)

---

## Step 1: Cost Forecasting

### 1.1 VRLA Cost Trajectory

**Method**: Flat or slow-changing trajectory (mature technology)

**Implementation**:
```python
# Base cost with regional multipliers
VRLA_Cost(region, t) = Base_CapEx × Regional_Multiplier(region) × (1 + annual_change)^(t - t0)

Where:
- Base_CapEx = $220/kWh (configurable)
- Regional_Multiplier: {China: 0.9, USA: 1.0, Europe: 1.15, RoW: 1.0}
- annual_change = scenario.vrla_cost_change (typically 0% for baseline)
- t0 = start year
```

**Rationale**: VRLA technology is mature with limited room for cost reduction. Regional multipliers account for manufacturing costs, labor, and logistics.

### 1.2 Li-ion Cost Trajectory

**Method**: Log-linear (log-CAGR) forecasting from BESS 4-hour turnkey proxy data

**Algorithm**:

**Step 1.2.1 - Historical CAGR Calculation**:
```
Given historical BESS costs: {(year₁, cost₁), (year₂, cost₂), ..., (yearₙ, costₙ)}

1. Transform to log space: log_cost_i = ln(cost_i)
2. Fit linear regression: log_cost = slope × year + intercept
3. Extract slope (this is the log-CAGR): λ = slope
```

**Step 1.2.2 - Scenario Adjustment**:
```
λ_adjusted = min(λ_historical, -scenario.lithium_cost_decline_rate)
λ_capped = max(λ_adjusted, -cap_annual_decline)

Where:
- scenario.lithium_cost_decline_rate: target decline (e.g., 0.08 = 8%/year)
- cap_annual_decline: 0.30 (30% max decline per year prevents unrealistic drops)
```

**Step 1.2.3 - Forward Projection**:
```
For each forecast year t > last_historical_year:
    years_ahead = t - last_historical_year
    log_cost(t) = ln(last_cost) + λ_adjusted × years_ahead
    cost(t) = exp(log_cost(t))

    # Apply floor and ceiling constraints
    cost(t) = max(cost(t), last_cost × floor_cost_ratio)  # Floor at 20% of last cost
    cost(t) = min(cost(t), last_cost)  # Ceiling at last cost (prevent increases)
```

**Step 1.2.4 - UPS Reliability Premium**:
```
Li_ion_UPS_Cost(t) = cost(t) × UPS_reliability_premium

Where:
- UPS_reliability_premium = 1.08 (8% premium for higher reliability requirements)
```

**Rationale**: Using BESS costs as proxy is justified because:
- Both are 4-hour duration systems
- UPS batteries cycle less (250/year vs 365+/year for grid BESS) → longer life
- Directional trends matter more than absolute levels for tipping point detection
- 8% premium accounts for stricter UPS reliability standards

---

## Step 2: Total Cost of Ownership (TCO) Calculation

### 2.1 TCO Formula

**Definition**: Net Present Value (NPV) of all costs over analysis horizon (15 years default)

**Complete TCO Equation**:
```
TCO(tech, t) = CapEx(t) + NPV_OpEx(t) + NPV_Replacements(t)

Where for technology 'tech' purchased in year t:

NPV_OpEx(t) = Σ(i=1 to H) [OpEx_per_kWh_year / (1 + r)^i]

NPV_Replacements(t) = Σ(j=1 to N_replacements) [CapEx(t) / (1 + r)^(j × Lifespan)]

Parameters:
- H = TCO horizon (15 years)
- r = discount rate (8% = 0.08)
- Lifespan: VRLA = 5 years, Li-ion = 12 years
- N_replacements = floor(H / Lifespan)
```

### 2.2 VRLA TCO Calculation

**Example** (15-year horizon, 8% discount rate):

```
CapEx = $220/kWh
OpEx = $18/kWh-year
Lifespan = 5 years

Initial CapEx: $220

Discounted OpEx:
    Year 1: $18 / 1.08^1 = $16.67
    Year 2: $18 / 1.08^2 = $15.43
    ...
    Year 15: $18 / 1.08^15 = $5.68
    Total NPV_OpEx ≈ $154.10

Replacements:
    Year 5: $220 / 1.08^5 = $149.78
    Year 10: $220 / 1.08^10 = $101.94
    Total NPV_Replacements = $251.72

VRLA TCO = $220 + $154.10 + $251.72 = $625.82/kWh
```

### 2.3 Li-ion TCO Calculation

**Example** (15-year horizon, 8% discount rate):

```
CapEx = $180/kWh (declining over time)
OpEx = $6/kWh-year
Lifespan = 12 years

Initial CapEx: $180

Discounted OpEx:
    Year 1-15: Σ($6 / 1.08^i) ≈ $51.37

Replacements:
    Year 12: $180 / 1.08^12 = $71.44
    (No second replacement within 15-year horizon)
    Total NPV_Replacements = $71.44

Li-ion TCO = $180 + $51.37 + $71.44 = $302.81/kWh
```

### 2.4 TCO Advantage Metric

```
TCO_Advantage(t) = TCO_VRLA(t) - TCO_Li_ion(t)

Interpretation:
- TCO_Advantage > 0 → Li-ion is cheaper (favorable for adoption)
- TCO_Advantage = 0 → Cost parity
- TCO_Advantage < 0 → VRLA is cheaper (slows adoption)
```

---

## Step 3: Tipping Point Detection

### 3.1 Tipping Point Definition

**Tipping Point** = First year when Li-ion TCO becomes sustainably cheaper than VRLA TCO

**Detection Algorithm**:

```python
def detect_tipping_point(tco_vrla, tco_li_ion, years, persistence=3):
    """
    Find first year where Li-ion advantage persists

    Args:
        tco_vrla: Array of VRLA TCO values by year
        tco_li_ion: Array of Li-ion TCO values by year
        years: Array of years
        persistence: Number of consecutive years required (default 3)

    Returns:
        tipping_year: First year of sustained advantage, or None
    """
    tco_advantage = tco_vrla - tco_li_ion

    for i in range(len(years) - persistence + 1):
        # Check if advantage is positive for 'persistence' consecutive years
        if all(tco_advantage[i:i+persistence] > 0):
            return years[i]

    return None  # No tipping point found
```

### 3.2 Handling Edge Cases

**Case 1: Li-ion Always Cheaper**
- If tco_advantage > 0 for all historical years
- Tipping point = first year in dataset
- Indicates Li-ion already achieved cost parity before forecast period

**Case 2: VRLA Always Cheaper**
- If tco_advantage < 0 for all years (including forecast)
- Tipping point = None
- Model falls back to slow baseline adoption (see §4.4)

**Case 3: Multiple Crossings**
- If costs fluctuate (unusual for smoothed data)
- First sustained crossing (3+ years) is used
- Guards against noise and temporary shocks

### 3.3 Tipping Year Persistence Rationale

**Why 3 years?**
- Market inertia: Procurement cycles typically 2-3 years for datacenter infrastructure
- Risk aversion: Organizations wait to confirm cost advantage is durable
- Contractual lock-in: Existing VRLA contracts must expire before switching
- Supply chain validation: Li-ion supply must prove reliable at scale

**Sensitivity**: Can be adjusted via `tipping_persistence_years` parameter (range: 1-5 years)

---

## Step 4: S-Curve Adoption Modeling

### 4.1 Logistic Function Core

**Standard Logistic (Sigmoid) Function**:
```
S(t) = L / (1 + exp(-k × (t - t₀)))

Where:
- S(t) = Li-ion market share at time t (0 to 1)
- L = ceiling (maximum adoption, e.g., 0.95 = 95%)
- t₀ = inflection point (year of 50% adoption)
- k = steepness parameter (controls adoption rate)
- t = time (years from start)
```

**Properties**:
- **S-shaped curve**: Slow start → Rapid middle → Slow saturation
- **Bounded**: 0 ≤ S(t) ≤ L (never exceeds ceiling)
- **Monotonic**: Always increasing (never decreases)
- **Inflection at t₀**: Maximum adoption rate occurs at midpoint

### 4.2 Economic-Linked Steepness

**Innovation**: Link adoption rate to cost advantage magnitude

**Enhanced Formula**:
```
k(t) = k₀ + s × max(0, TCO_Advantage(t))

Where:
- k₀ = base steepness (0.5 default) - non-price adoption drivers
- s = cost sensitivity (0.002 default) - price responsiveness
- TCO_Advantage(t) = VRLA_TCO(t) - Li_ion_TCO(t)
```

**Interpretation**:
- **k₀** captures non-economic factors:
  - Space savings (Li-ion is more compact)
  - Thermal management (Li-ion generates less heat)
  - Reliability improvements
  - Environmental/sustainability mandates

- **s × TCO_Advantage** captures economic acceleration:
  - Larger cost savings → Faster adoption
  - Small advantage → Cautious, slow uptake
  - Massive advantage → Rapid transition

**Example Calculation**:
```
Given:
- k₀ = 0.5
- s = 0.002
- TCO_Advantage(2027) = $323/kWh (Li-ion $323/kWh cheaper)

k(2027) = 0.5 + 0.002 × 323 = 0.5 + 0.646 = 1.146

This means adoption rate in 2027 is ~130% faster than baseline (k₀ alone)
```

### 4.3 Scenario Acceleration Multiplier

**Purpose**: Adjust adoption speed for different scenarios without re-calibrating entire model

**Implementation**:
```
k_final(t) = [k₀ + s × TCO_Advantage(t)] × adoption_acceleration

Where adoption_acceleration:
- Baseline: 1.0 (no adjustment)
- Accelerated: 1.5 (50% faster adoption - aggressive sustainability push)
- Delayed: 0.7 (30% slower - supply chain constraints, risk aversion)
- High OpEx: 1.2 (20% faster - emphasize operational cost savings)
```

### 4.4 Tipping Point Alignment

**Setting t₀ (Inflection Point)**:

```python
if tipping_year is not None:
    # Align inflection to tipping year
    t₀_index = years.index(tipping_year)
else:
    # No tipping: use slow baseline adoption
    # Return minimal adoption curve (1% → 20% over forecast period)
    return np.linspace(0.01, 0.20, len(years))
```

**Rationale**: The year of cost parity (tipping) should correspond to the inflection point where adoption accelerates most rapidly. Before tipping, adoption is slow (early adopters only); after tipping, economics drive mainstream adoption.

### 4.5 Monotonicity Enforcement

**Problem**: k(t) varies with TCO_Advantage(t), which can fluctuate, potentially causing S(t) to decrease

**Solution**: Enforce monotonic increase (markets don't regress)

```python
adoption = []
for i in range(len(years)):
    k = k₀ + s × max(0, tco_advantage[i])
    k *= scenario.adoption_acceleration

    t_rel = i - t₀_index
    share = L / (1 + np.exp(-k × t_rel))

    # Monotonicity check
    if i > 0 and share < adoption[-1]:
        share = adoption[-1]  # Hold at previous level

    adoption.append(share)
```

### 4.6 Ceiling Interpretation

**L Parameter (Typical: 0.90 - 0.99)**

**Why not 100%?**
- **Legacy systems**: Some old datacenters never upgrade (sunk costs)
- **Niche use cases**: Extreme cold environments (VRLA tolerates better)
- **Supply constraints**: Li-ion shortages during transition
- **Vendor lock-in**: Proprietary VRLA systems with no Li-ion equivalent
- **Grid-edge applications**: Remote sites where Li-ion supply chain unavailable

**Regional Variation**:
- China: L ≈ 0.98 (aggressive tech adoption, manufacturing capacity)
- USA: L ≈ 0.95 (balanced, some legacy infrastructure)
- Europe: L ≈ 0.92 (regulatory caution, VRLA recycling mandates)
- RoW: L ≈ 0.90 (supply chain limitations, cost sensitivity)

---

## Step 5: Market Demand Forecasting

### 5.1 Total Market Growth

**Data Source**: `Datacenter_capacity_growth_projections_<region>` (annual growth rates)

**Projection Method**: Compound growth from last historical value

**Algorithm**:
```python
For each year t:
    if t ≤ last_historical_year:
        Total_Demand(t) = Historical_Data(t)
    else:
        years_ahead = t - last_historical_year
        growth_rate = Growth_Rate(t) if available else Last_Known_Growth_Rate
        Total_Demand(t) = Last_Historical_Value × (1 + growth_rate)^years_ahead
```

**Example**:
```
Given:
- Last historical year: 2023
- Last historical demand: 10 GWh
- 2024-2030 growth rate: 9% per year

Year 2027 forecast:
    years_ahead = 2027 - 2023 = 4
    Total_Demand(2027) = 10 × (1.09)^4 = 10 × 1.411 = 14.11 GWh
```

### 5.2 Growth Rate Handling

**If growth rate series is incomplete**:
```python
if year not in growth_rate_series:
    # Use last known growth rate
    growth_rate = growth_rate_series.iloc[-1]
else:
    growth_rate = growth_rate_series[year]

# Convert from percentage to decimal
growth_rate = growth_rate / 100.0
```

**Typical Growth Rates by Region**:
- China: 10-12% (rapid digitalization, AI infrastructure)
- USA: 7-9% (cloud expansion, edge computing)
- Europe: 6-8% (moderate growth, energy constraints)
- RoW: 8-10% (varied, led by emerging markets)
- Global: 8-10% (weighted average)

### 5.3 Growth Rate Validation

**Sanity Checks**:
```python
# Cap annual growth at ±5% CAGR to prevent blow-ups
if abs(growth_rate) > 0.05:
    print(f"Warning: Growth rate {growth_rate:.1%} exceeds ±5% cap")
    growth_rate = np.clip(growth_rate, -0.05, 0.05)
```

---

## Step 6: Technology Split

### 6.1 Demand Allocation Formula

**Using S-curve adoption share**:

```
Li_ion_Demand(t) = Total_Demand(t) × S(t)
VRLA_Demand(t) = Total_Demand(t) × (1 - S(t))

Where:
- S(t) = Li-ion market share from S-curve (0 to L)
- Total_Demand(t) = Total market demand in GWh/year
```

### 6.2 Share Calculation

**Market Shares**:
```
Li_ion_Share(t) = S(t) × 100%
VRLA_Share(t) = (1 - S(t)) × 100%

Constraint: Li_ion_Share(t) + VRLA_Share(t) = 100%
```

---

## Step 7: Installed Base Accounting

### 7.1 Stock-Flow Dynamics

**Governing Equations**:

```
IB_VRLA(t+1) = IB_VRLA(t) + Adds_VRLA(t) - Retirements_VRLA(t)
IB_Li_ion(t+1) = IB_Li_ion(t) + Adds_Li_ion(t) - Retirements_Li_ion(t)

Where:
- IB = Installed Base (stock, GWh)
- Adds = Annual demand (flow, GWh/year)
- Retirements = End-of-life replacements (flow, GWh/year)
```

### 7.2 Retirement Calculation

**Simplified Exponential Decay Model**:

```
Retirements_tech(t) = IB_tech(t) / Lifespan_tech

Where:
- VRLA: Lifespan = 5 years → Annual retirement rate = 20%
- Li-ion: Lifespan = 12 years → Annual retirement rate = 8.3%
```

**Rationale**: Assumes batteries are replaced uniformly over their lifespan (exponential decay approximation). More sophisticated models could use vintaged cohorts, but this is sufficient for macro forecasts.

### 7.3 Initial Installed Base

**VRLA Initialization**:
```python
if start_year in historical_vrla_installed_base:
    IB_VRLA(start_year) = Historical_Data(start_year)
else:
    # Estimate from demand and lifespan
    IB_VRLA(start_year) = VRLA_Demand(start_year) × Lifespan_VRLA
```

**Li-ion Initialization**:
```python
# Conservative assumption: Li-ion starts at zero
IB_Li_ion(start_year) = 0

# Alternative: Derive from historical demand
if historical_li_ion_demand available:
    IB_Li_ion(start_year) = sum(last_12_years_demand)
```

### 7.4 Mass Balance Validation

**Check Equation**:
```
For each year t:
    ΔIB_tech = IB_tech(t) - IB_tech(t-1)
    Expected_ΔIB = Adds_tech(t) - Retirements_tech(t)

    Imbalance = |ΔIB_tech - Expected_ΔIB|

    if Imbalance > 0.001 × IB_tech(t):  # 0.1% tolerance
        print(f"Warning: Mass balance error in year {t}")
```

**Why 0.1% tolerance?**
- Numerical precision limits
- Rounding in retirement calculations
- Historical data inconsistencies
- Small errors compound over time → tight tolerance essential

---

## Step 8: Market Decomposition

### 8.1 Demand Components

**Identity**:
```
Total_Demand(t) = New_Build_Demand(t) + Replacement_Demand(t)

Where:
- New_Build = Batteries for newly constructed datacenters
- Replacement = Batteries to replace end-of-life systems
```

### 8.2 New-Build Demand

**Calculation from Growth Rate**:
```
New_Build(t) = IB_Total(t-1) × Growth_Rate(t)

Where:
- IB_Total(t-1) = Total installed base in previous year
- Growth_Rate(t) = Annual datacenter capacity growth rate
```

**Rationale**: New datacenters require batteries; amount proportional to expansion rate

### 8.3 Replacement Demand

**Calculation from Retirements**:
```
Replacement(t) = Retirements_VRLA(t) + Retirements_Li_ion(t)

Where:
- Retirements_VRLA(t) = IB_VRLA(t-1) / Lifespan_VRLA
- Retirements_Li_ion(t) = IB_Li_ion(t-1) / Lifespan_Li_ion
```

### 8.4 Contestable Market

**Definition**: VRLA batteries reaching end-of-life that can switch to Li-ion

**Calculation**:
```
Contestable_Market(t) = Retirements_VRLA(t) = IB_VRLA(t-1) / Lifespan_VRLA
```

**Adoption Logic**:
```
Li_ion_Retrofits(t) = Contestable_Market(t) × S(t)
VRLA_for_VRLA(t) = Contestable_Market(t) × (1 - S(t))

Where S(t) is the Li-ion adoption share from S-curve
```

**Significance**: The contestable market is the "battleground" for technology transition. As VRLA systems retire every 5 years, operators choose VRLA replacement or Li-ion upgrade based on economics.

### 8.5 Validation Check

**Reconciliation**:
```
Total_Decomposed(t) = New_Build(t) + Replacement(t)
Total_Actual(t) = VRLA_Demand(t) + Li_ion_Demand(t)

Difference = |Total_Decomposed(t) - Total_Actual(t)|

if Difference > 0.15 × Total_Actual(t):  # 15% tolerance
    print(f"Note: Decomposition differs from total by {Difference/Total_Actual*100:.1f}%")
```

**Why 15% tolerance?**
- Market dynamics vary (new-build can slow while replacements surge)
- Growth rate estimates have uncertainty
- Installed base data may be incomplete
- This is a modeling check, not a hard constraint

---

## Step 9: Battery Metrics Calculation

### 9.1 Power Capacity

**Energy-to-Power Conversion**:
```
Power_MW(t) = Energy_GWh(t) × 1000 / Duration_hours

Where:
- Duration = 4 hours (default for UPS systems)
- Energy in GWh, Power in MW
```

**Example**:
```
Total demand: 10 GWh
Duration: 4 hours
Power capacity = 10 × 1000 / 4 = 2,500 MW
```

### 9.2 Annual Throughput

**Throughput Calculation**:
```
Throughput_GWh(t) = IB_GWh(t) × Cycles_per_year × Round_Trip_Efficiency

Where:
- Cycles_per_year = 250 (typical for backup UPS duty cycle)
- Round_Trip_Efficiency = 0.88 (88% for Li-ion)
```

**Example**:
```
Installed base: 50 GWh
Cycles/year: 250
RTE: 0.88

Annual throughput = 50 × 250 × 0.88 = 11,000 GWh = 11 TWh
```

### 9.3 Cycle Life Implications

**VRLA vs Li-ion Duty Cycle**:

| Metric | VRLA | Li-ion |
|--------|------|--------|
| Cycle life (total) | 1,250 cycles | 5,000+ cycles |
| Annual cycles (UPS) | 250 | 250 |
| Calendar life | 5 years | 10-15 years |
| **Limiting factor** | **Calendar** | **Cycles or calendar** |

**Key Insight**: For low-cycle UPS applications (250/year), **calendar aging dominates**. Li-ion's superior cycle life (5,000+) is not fully utilized, but its 12-year calendar life still provides 2.4× lifespan advantage over VRLA.

---

## Validation Framework

### V.1 Non-Negativity

**Rule**: All demand values must be ≥ 0

```python
if (results['vrla_demand_gwh'] < 0).any() or (results['lithium_demand_gwh'] < 0).any():
    raise ValueError("Negative demand values detected")
```

### V.2 Monotonic Adoption

**Rule**: Li-ion market share must monotonically increase

```python
lithium_share = results['lithium_share_pct'].values
is_monotonic = all(lithium_share[i] <= lithium_share[i+1] for i in range(len(lithium_share)-1))

if not is_monotonic:
    print("Warning: Non-monotonic adoption detected")
```

### V.3 Total Demand Consistency

**Rule**: VRLA + Li-ion ≈ Total Market Demand (±5%)

```python
for year in years:
    vrla = results.loc[year, 'vrla_demand_gwh']
    li_ion = results.loc[year, 'lithium_demand_gwh']
    total_calc = vrla + li_ion
    total_market = results.loc[year, 'total_demand_gwh']

    error = abs(total_calc - total_market) / total_market
    if error > 0.05:
        print(f"Warning: Year {year} demand split error: {error*100:.1f}%")
```

### V.4 Mass Balance

**Rule**: IB changes must equal net flows (±0.1%)

```python
for t in range(1, len(years)):
    delta_ib = results['vrla_installed_base_gwh'].iloc[t] - results['vrla_installed_base_gwh'].iloc[t-1]
    adds = results['vrla_demand_gwh'].iloc[t]
    retirements = results['vrla_installed_base_gwh'].iloc[t-1] / lifespan_vrla

    imbalance = abs(delta_ib - adds + retirements)
    if imbalance > 0.001 * results['vrla_installed_base_gwh'].iloc[t]:
        print(f"Warning: Mass balance imbalance in year {years[t]}")
```

### V.5 Historical Backtest

**Rule**: Forecasts for historical years should match actual data (±5%)

```python
for year in overlap_years:
    forecast_val = results.loc[year, 'total_demand_gwh']
    historical_val = historical_data.loc[year]
    error = abs(forecast_val - historical_val) / historical_val

    if error > 0.05:
        print(f"Warning: Year {year} backtest error: {error*100:.1f}%")
```

---

## Mathematical Notation

### Symbols

| Symbol | Description | Units |
|--------|-------------|-------|
| t | Time (year) | years |
| t₀ | Inflection point year | years |
| H | TCO horizon | years (15 default) |
| r | Discount rate | decimal (0.08 = 8%) |
| L | Adoption ceiling | decimal (0.95 = 95%) |
| k | Steepness parameter | 1/years |
| k₀ | Base steepness | 1/years |
| s | Cost sensitivity | 1/USD |
| S(t) | Li-ion market share | 0 to 1 |
| TCO | Total Cost of Ownership | $/kWh |
| IB | Installed Base | GWh |
| λ | Log-CAGR | 1/years |

### Subscripts

- `tech`: Technology (VRLA or Li-ion)
- `region`: Geographic region (China, USA, Europe, RoW, Global)
- `t`: Time period (year)

### Key Equations Summary

```
1. TCO(tech, t) = CapEx(t) + Σᵢ₌₁ᴴ [OpEx / (1+r)ⁱ] + Σⱼ [CapEx / (1+r)^(j×Lifespan)]

2. S(t) = L / (1 + exp(-k(t) × (t - t₀)))

3. k(t) = [k₀ + s × max(0, TCO_VRLA(t) - TCO_Li(t))] × adoption_acceleration

4. IB(t+1) = IB(t) + Adds(t) - Retirements(t)

5. Retirements(t) = IB(t) / Lifespan

6. Total_Demand(t) = New_Build(t) + Replacement(t)
```

---

## Implementation Notes

### Numerical Stability

- Use log-space for cost projections to avoid numerical overflow
- Enforce bounds on all parameters (k ∈ [0.05, 2.0], L ∈ [0.90, 0.99])
- Apply 3-year rolling median smoothing to historical cost data before fitting

### Performance Optimization

- Vectorize S-curve calculations using NumPy
- Pre-compute TCO arrays for all years before demand loop
- Cache intermediate results (cost forecasts, growth rates)

### Edge Case Handling

- If tipping point not found → use baseline adoption (1% → 20%)
- If growth rate missing → use last known rate with warning
- If initial IB unknown → estimate from demand × lifespan

---

## References

- Bass Diffusion Model (1969) - Technology adoption foundations
- NPV/DCF methodology - TCO calculation framework
- Logistic growth models - S-curve adoption dynamics
- Battery industry cost curves - BNEF, IEA, NREL data sources

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Maintainer**: Datacenter UPS Battery Forecasting Team
