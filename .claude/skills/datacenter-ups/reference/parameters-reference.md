# Parameters Reference Guide

Complete catalog of all configurable parameters for the Datacenter UPS Battery Technology Transition model, including descriptions, valid ranges, defaults, sensitivities, and calibration guidance.

## Contents

- [Overview](#overview)
- [Time Parameters](#time-parameters)
- [Regional Parameters](#regional-parameters)
- [Cost Parameters](#cost-parameters)
- [Lifespan Parameters](#lifespan-parameters)
- [S-Curve Parameters](#s-curve-parameters)
- [Financial Parameters](#financial-parameters)
- [Battery Metrics Parameters](#battery-metrics-parameters)
- [Validation Parameters](#validation-parameters)
- [Scenario Parameters](#scenario-parameters)
- [Data Source Parameters](#data-source-parameters)
- [Parameter Sensitivity Analysis](#parameter-sensitivity-analysis)

---

## Overview

Parameters are organized in `config.json` with the following structure:

```json
{
  "default_parameters": { ... },
  "regions": [ ... ],
  "cost_parameters": { ... },
  "lifespans": { ... },
  "s_curve_parameters": { ... },
  "battery_metrics": { ... },
  "validation_rules": { ... },
  "scenarios": { ... }
}
```

**Parameter Types**:
- **Fixed**: Hardcoded values (change rarely)
- **Scenario**: Varies by scenario (baseline, accelerated, delayed)
- **Regional**: Different values by geography
- **Calibrated**: Fitted from historical data
- **Sensitivity**: Used for uncertainty analysis

---

## Time Parameters

### `start_year`
- **Type**: Integer
- **Default**: `2020`
- **Range**: 2010-2025
- **Description**: First year of forecast horizon
- **Usage**: Sets t=0 for all time series
- **Notes**: Should align with earliest available historical data

### `end_year`
- **Type**: Integer
- **Default**: `2035`
- **Range**: 2025-2050
- **Description**: Final year of forecast horizon
- **Usage**: Determines forecast length and projection requirements
- **Sensitivity**: No direct impact on results; only affects forecast coverage
- **Recommended**: 2035 (standard), 2040 (extended), 2050 (long-term planning)

### `tco_horizon_years`
- **Type**: Integer
- **Default**: `15`
- **Range**: 10-20 years
- **Description**: Time horizon for Total Cost of Ownership (TCO) analysis
- **Usage**: NPV calculation window for comparing VRLA vs Li-ion
- **Sensitivity**:
  - **High**: ±2 years → ±5% TCO impact → ±1 year tipping point shift
  - Longer horizons favor Li-ion (longer life, lower OpEx)
- **Rationale**: 15 years captures 3 VRLA cycles (5y each) and 1.25 Li-ion cycles (12y each)
- **Best Practice**: Use 15 years for standard analysis; 10 years for conservative estimates

### `smoothing_window`
- **Type**: Integer
- **Default**: `3`
- **Range**: 1-5 years
- **Description**: Rolling median window for smoothing historical cost data
- **Usage**: Reduce noise in cost curves before log-CAGR calculation
- **Sensitivity**: **Low** (affects curve smoothness, not direction)
- **Recommended**: 3 years (balances noise reduction and responsiveness)

### `tipping_persistence_years`
- **Type**: Integer
- **Default**: `3`
- **Range**: 1-5 years
- **Description**: Consecutive years required for sustained tipping point
- **Usage**: Guards against temporary cost fluctuations
- **Sensitivity**: **Medium** (±1 year → ±1-2 year tipping detection)
- **Rationale**: 3 years aligns with typical datacenter procurement cycles
- **Notes**: Higher values = more conservative tipping detection

---

## Regional Parameters

### `regions`
- **Type**: Array of strings
- **Default**: `["China", "USA", "Europe", "Rest_of_World", "Global"]`
- **Description**: Supported geographic regions for analysis
- **Usage**: Each region forecasted independently; Global = sum of others
- **Notes**:
  - Never run "Global" and individual regions in same aggregation (double-counting)
  - Regional results should sum to Global within ±2% tolerance

### Regional Cost Multipliers (VRLA)

#### `vrla.regional_multipliers.China`
- **Default**: `0.9`
- **Range**: 0.7-1.0
- **Description**: VRLA cost adjustment for China relative to global baseline
- **Rationale**: Lower manufacturing costs, local production

#### `vrla.regional_multipliers.USA`
- **Default**: `1.0`
- **Range**: 0.9-1.1
- **Description**: VRLA cost for USA (baseline region)
- **Rationale**: Reference region; moderate costs

#### `vrla.regional_multipliers.Europe`
- **Default**: `1.15`
- **Range**: 1.1-1.3
- **Description**: VRLA cost adjustment for Europe
- **Rationale**: Higher labor costs, stricter regulations, import duties

#### `vrla.regional_multipliers.Rest_of_World`
- **Default**: `1.0`
- **Range**: 0.9-1.2
- **Description**: VRLA cost for Rest of World
- **Rationale**: Weighted average; varies widely by country

---

## Cost Parameters

### VRLA Cost Parameters

#### `cost_parameters.vrla.capex_per_kwh`
- **Type**: Float ($/kWh)
- **Default**: `220.0`
- **Range**: 180-260 $/kWh
- **Description**: VRLA battery capital cost per kWh (base year)
- **Usage**: Initial cost before regional multipliers
- **Sensitivity**: **High** (±$20 → ±$20-50 TCO → ±1-2 year tipping shift)
- **Calibration**: From vendor quotes, industry reports (BNEF, IEA)
- **Notes**: Relatively stable (mature technology); ~2% annual decline typical

#### `cost_parameters.vrla.opex_per_kwh_year`
- **Type**: Float ($/kWh-year)
- **Default**: `18.0`
- **Range**: 12-24 $/kWh-year
- **Description**: VRLA annual operating expenditure per kWh installed
- **Components**:
  - Maintenance/testing: $12/kWh-year (67%)
  - Cooling/HVAC: $4/kWh-year (22%)
  - Space/footprint: $2/kWh-year (11%)
- **Sensitivity**: **Very High** (±$3 → ±$25 TCO → ±2-3 year tipping shift)
- **Rationale**: VRLA requires frequent maintenance, generates more heat
- **Regional Variation**: USA 1.0×, Europe 1.2× (higher labor), China 0.8× (lower labor)

#### `cost_parameters.vrla.capex_trajectory`
- **Type**: String
- **Default**: `"flat"`
- **Options**: `"flat"`, `"declining"`
- **Description**: VRLA cost evolution pattern
- **Usage**: "flat" applies scenario.vrla_cost_change; "declining" uses log-CAGR
- **Recommended**: "flat" (mature technology has limited cost reduction potential)

### Li-ion Cost Parameters

#### `cost_parameters.lithium.capex_source`
- **Type**: String
- **Default**: `"bess_proxy"`
- **Options**: `"bess_proxy"`, `"direct"`
- **Description**: Source for Li-ion CapEx data
- **Usage**: "bess_proxy" uses grid-scale BESS costs; "direct" uses UPS-specific data
- **Notes**: BESS proxy is standard due to limited UPS-specific historical data

#### `cost_parameters.lithium.opex_per_kwh_year`
- **Type**: Float ($/kWh-year)
- **Default**: `6.0`
- **Range**: 4-10 $/kWh-year
- **Description**: Li-ion annual operating expenditure per kWh installed
- **Components**:
  - Maintenance/monitoring: $4/kWh-year (67%)
  - Cooling: $1.5/kWh-year (25%)
  - Space: $0.5/kWh-year (8%)
- **Sensitivity**: **High** (±$1.5 → ±$12 TCO → ±1 year tipping shift)
- **Rationale**: Li-ion requires less maintenance, generates less heat, more compact
- **Li-ion Advantage**: 67% lower OpEx than VRLA ($6 vs $18)

#### `cost_parameters.lithium.capex_trajectory`
- **Type**: String
- **Default**: `"declining"`
- **Description**: Li-ion cost evolution pattern (always declining)
- **Usage**: Uses log-CAGR from historical BESS data
- **Notes**: Decline driven by learning rate (15-20% per doubling of cumulative capacity)

#### `cost_parameters.lithium.ups_reliability_premium`
- **Type**: Float (multiplier)
- **Default**: `1.08`
- **Range**: 1.0-1.15
- **Description**: Cost premium for UPS-grade Li-ion vs grid-scale BESS
- **Rationale**:
  - Higher reliability standards (99.999% uptime)
  - More stringent safety certifications (UL 1973, IEC 62619)
  - Enhanced BMS (Battery Management System) features
- **Sensitivity**: **Low** (±0.05 → ±$10-15 CapEx → minimal tipping impact)
- **Calibration**: From datacenter procurement data vs BESS benchmarks

#### `cost_parameters.lithium.learning_rate`
- **Type**: Float (decimal)
- **Default**: `0.15`
- **Range**: 0.10-0.20
- **Description**: Cost reduction per doubling of cumulative production
- **Usage**: Alternative to log-CAGR if using Wright's Law for cost forecasting
- **Notes**: 15-20% is typical for battery technologies; not directly used in current model (log-CAGR preferred)

---

## Lifespan Parameters

### `lifespans.vrla_years`
- **Type**: Integer
- **Default**: `5`
- **Range**: 3-7 years
- **Description**: VRLA battery operational lifespan
- **Usage**:
  - TCO replacement frequency
  - Installed base retirement rate (20%/year)
  - Contestable market calculation
- **Sensitivity**: **Very High** (±1 year → ±$50-100 TCO → ±2-4 year tipping shift)
- **Factors Affecting Lifespan**:
  - Operating temperature (higher temp → shorter life)
  - Depth of discharge (deeper cycles → shorter life)
  - Float voltage management
- **Regional Variation**: Warmer climates may see 4-year life; cooler climates 6-year
- **Best Practice**: Use 5 years for global average; adjust for climate sensitivity analysis

### `lifespans.lithium_years`
- **Type**: Integer
- **Default**: `12`
- **Range**: 10-15 years
- **Description**: Li-ion battery operational lifespan
- **Usage**:
  - TCO replacement frequency
  - Installed base retirement rate (8.3%/year)
- **Sensitivity**: **High** (±2 years → ±$20-40 TCO → ±1-2 year tipping shift)
- **Factors Affecting Lifespan**:
  - Chemistry (LFP > NMC for calendar life)
  - Thermal management quality
  - State of charge management (avoid 100%/0% extremes)
  - Cycle depth (shallow cycles extend life)
- **Typical Ranges by Chemistry**:
  - LFP (LiFePO₄): 12-15 years
  - NMC: 10-12 years
  - NCA: 8-10 years
- **Notes**: UPS duty cycle (low cycles/year) means calendar aging dominates over cycle aging

---

## S-Curve Parameters

### `s_curve_parameters.ceiling_L`
- **Type**: Float (decimal)
- **Default**: `0.95`
- **Range**: 0.85-0.99
- **Description**: Maximum Li-ion market share (L in logistic function)
- **Usage**: S(t) = L / (1 + exp(-k×(t-t₀))) asymptotes to L
- **Sensitivity**: **Medium** (±0.05 → ±5 pp final adoption)
- **Interpretation**: 0.95 = 95% max adoption; 5% residual VRLA niche
- **Reasons for L < 1.0**:
  - Legacy systems (sunk costs, never upgraded)
  - Extreme environments (very cold/hot where VRLA performs better)
  - Supply chain constraints (Li-ion shortages during peak transition)
  - Regulatory niches (recycling mandates favor VRLA in some regions)
- **Regional Recommendations**:
  - China: 0.97-0.98 (aggressive tech adoption)
  - USA: 0.94-0.96 (moderate, some legacy infrastructure)
  - Europe: 0.90-0.93 (cautious, recycling regulations)
  - RoW: 0.85-0.92 (supply constraints)

### `s_curve_parameters.base_steepness_k0`
- **Type**: Float (1/years)
- **Default**: `0.5`
- **Range**: 0.2-0.8
- **Description**: Baseline adoption rate (non-economic factors)
- **Usage**: k(t) = k₀ + s × TCO_Advantage(t)
- **Sensitivity**: **Medium** (±0.1 → ±2-3 year adoption speed)
- **Physical Meaning**: k₀ = 0.5 → ~70% adoption span = 4-5 years around t₀
- **Non-Economic Drivers (k₀)**:
  - Space/density advantages (Li-ion is 3× more compact)
  - Thermal benefits (40% less heat generation)
  - Operational simplicity (less maintenance)
  - Sustainability mandates (corporate ESG goals)
- **Calibration**: Fit to historical adoption data using least squares
- **Bounds**: [0.1, 2.0] to prevent unrealistic adoption speeds

### `s_curve_parameters.cost_sensitivity_s`
- **Type**: Float (1/USD)
- **Default**: `0.002`
- **Range**: 0.0-0.01
- **Description**: Sensitivity of adoption rate to TCO advantage
- **Usage**: Larger TCO savings → faster adoption (k increases)
- **Sensitivity**: **Low to Medium** (±0.001 → ±1 year adoption speed if large TCO gap)
- **Physical Meaning**: s = 0.002 means $100 TCO advantage increases k by 0.2
- **Economic Interpretation**:
  - s = 0: Adoption purely driven by non-economic factors (k = k₀)
  - s > 0: Economic advantage accelerates adoption
  - Higher s = more price-sensitive market
- **Calibration**: Requires paired (TCO, adoption share) time series; often fixed if data sparse
- **Bounds**: [0.0, 0.01] to prevent over-sensitivity to cost fluctuations

### `s_curve_parameters.midpoint_t0`
- **Type**: Integer or null
- **Default**: `null` (auto-detect from tipping point)
- **Range**: start_year to end_year
- **Description**: Inflection point year (50% of ceiling adoption)
- **Usage**:
  - If null: set to tipping_year (cost parity year)
  - If specified: overrides automatic detection
- **Sensitivity**: **Very High** (±2 years → entire S-curve shifts ±2 years)
- **Rationale**: Aligning t₀ with tipping year assumes adoption accelerates when economics favor Li-ion
- **Manual Override**: Use when tipping point unreliable (e.g., poor cost data)

### `s_curve_parameters.calibration_method`
- **Type**: String
- **Default**: `"least_squares"`
- **Options**: `"least_squares"`, `"manual"`, `"heuristic"`
- **Description**: Method for fitting S-curve parameters
- **Usage**:
  - "least_squares": Fit (L, t₀, k₀, s) to historical adoption data
  - "manual": Use user-specified values from config
  - "heuristic": Use defaults with t₀ = tipping_year + 7
- **Recommended**: "least_squares" if ≥5 years of adoption data; otherwise "heuristic"

### `s_curve_parameters.bounds`
- **Type**: Object with parameter ranges
- **Description**: Constraints for calibration optimization
- **Values**:
  ```json
  {
    "L": [0.90, 0.99],
    "t0": [2020, 2040],
    "k0": [0.1, 2.0],
    "s": [0.0, 0.01]
  }
  ```
- **Usage**: Prevents nonsensical fitted values (e.g., L > 1.0, negative k)

---

## Financial Parameters

### `default_parameters.discount_rate`
- **Type**: Float (decimal)
- **Default**: `0.08`
- **Range**: 0.05-0.12
- **Description**: Discount rate for NPV calculations in TCO
- **Usage**: PV = FV / (1 + r)^t
- **Sensitivity**: **High** (±2pp → ±$40-60 TCO → ±1-2 year tipping shift)
- **Interpretation**:
  - 6%: Low risk, government/utility projects
  - 8%: Corporate standard (WACC for large datacenters)
  - 10%: High risk, small operators, emerging markets
- **Regional Recommendations**:
  - USA/Europe: 6-8% (low financing costs)
  - China: 7-9% (moderate risk)
  - RoW: 9-12% (higher risk, currency volatility)
- **TCO Impact**: Higher r discounts future costs → favors lower-OpEx Li-ion
- **Best Practice**: Use 8% for baseline; sensitivity test at 6% and 10%

---

## Battery Metrics Parameters

### `battery_metrics.duration_hours`
- **Type**: Float
- **Default**: `4.0`
- **Range**: 2-8 hours
- **Description**: UPS battery discharge duration (energy/power ratio)
- **Usage**: Power_MW = Energy_GWh × 1000 / Duration_h
- **Typical Values**:
  - Critical loads: 4-6 hours (most datacenters)
  - Edge sites: 2-3 hours (generator backup priority)
  - High-reliability: 6-8 hours (remote, no grid redundancy)
- **Notes**: Does NOT affect demand forecast (only for power capacity reporting)

### `battery_metrics.cycles_per_year`
- **Type**: Integer
- **Default**: `250`
- **Range**: 50-500
- **Description**: Annual discharge cycles for UPS batteries
- **Usage**: Throughput_GWh = IB × Cycles × RTE
- **Typical Values**:
  - Standby UPS: 50-100 cycles/year (rare outages only)
  - Line-interactive: 200-300 cycles/year (grid fluctuations)
  - Online double-conversion: 300-500 cycles/year (constant cycling)
- **Notes**: UPS cycles << grid BESS cycles (365-730/year) → calendar life dominates

### `battery_metrics.round_trip_efficiency`
- **Type**: Float (decimal)
- **Default**: `0.88`
- **Range**: 0.80-0.95
- **Description**: Round-trip energy efficiency (charge/discharge)
- **Usage**: Effective throughput = Capacity × Cycles × RTE
- **Technology Comparison**:
  - Li-ion (NMC/NCA): 88-92%
  - Li-ion (LFP): 90-95%
  - VRLA: 75-80%
- **Notes**: Higher RTE → less heat, lower cooling costs (already in OpEx)

### `battery_metrics.depth_of_discharge`
- **Type**: Float (decimal)
- **Default**: `0.8`
- **Range**: 0.5-1.0
- **Description**: Fraction of capacity used per discharge
- **Usage**: Not directly used in current model; informational
- **Impact on Life**:
  - Li-ion: 80% DoD → 5,000 cycles; 50% DoD → 10,000+ cycles
  - VRLA: 80% DoD → 1,250 cycles; 50% DoD → 2,000 cycles
- **Notes**: UPS typically uses 80-100% DoD (deep discharges during outages)

---

## Validation Parameters

### `validation_rules.total_demand_tolerance`
- **Type**: Float (decimal)
- **Default**: `0.05`
- **Range**: 0.01-0.15
- **Description**: Allowable error when comparing VRLA + Li-ion vs Total Market
- **Usage**: |VRLA + Li - Total| / Total ≤ tolerance
- **Recommended**: 5% for quality control; 10% if data quality poor

### `validation_rules.mass_balance_tolerance`
- **Type**: Float (decimal)
- **Default**: `0.001`
- **Range**: 0.0001-0.01
- **Description**: Allowable error in stock-flow reconciliation
- **Usage**: |ΔIB - (Adds - Retirements)| / IB ≤ tolerance
- **Recommended**: 0.1% for strict validation; 0.5% if numerical precision issues

### `validation_rules.non_negativity`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enforce all demand/IB values ≥ 0
- **Usage**: Raises error if negative values detected
- **Notes**: Should always be true; negative demands indicate model error

### `validation_rules.monotonic_adoption`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enforce Li-ion share monotonically increases
- **Usage**: Warns if share decreases year-over-year
- **Notes**: Should be true; violations indicate S-curve instability

---

## Scenario Parameters

### Baseline Scenario

#### `scenarios.baseline.lithium_cost_decline_rate`
- **Default**: `0.08` (8% per year)
- **Range**: 0.05-0.15
- **Description**: Annual Li-ion cost reduction (CAGR)
- **Usage**: Overrides historical log-CAGR if specified
- **Rationale**: 8% aligns with recent BESS cost trends (2018-2023)

#### `scenarios.baseline.vrla_cost_change`
- **Default**: `0.0` (flat)
- **Range**: -0.05 to 0.05
- **Description**: Annual VRLA cost change (typically flat for mature tech)
- **Usage**: VRLA_Cost(t+1) = VRLA_Cost(t) × (1 + vrla_cost_change)

#### `scenarios.baseline.adoption_acceleration`
- **Default**: `1.0` (no adjustment)
- **Range**: 0.5-2.0
- **Description**: Multiplier on S-curve steepness k
- **Usage**: k_final = k × adoption_acceleration
- **Rationale**: 1.0 = use calibrated adoption rate as-is

### Accelerated Scenario

#### `scenarios.accelerated.lithium_cost_decline_rate`
- **Default**: `0.12` (12% per year)
- **Description**: Faster Li-ion cost decline (aggressive learning rate)
- **Rationale**: Assumes breakthrough in manufacturing, economies of scale

#### `scenarios.accelerated.adoption_acceleration`
- **Default**: `1.5` (50% faster)
- **Description**: Accelerated market adoption (policy incentives, sustainability push)
- **Impact**: Tipping point 2-3 years earlier; 2040 Li-ion share +8-12 pp

### Delayed Scenario

#### `scenarios.delayed.lithium_cost_decline_rate`
- **Default**: `0.05` (5% per year)
- **Description**: Slower Li-ion cost decline (supply constraints, raw material prices)
- **Rationale**: Conservative estimate; material shortages (lithium, cobalt)

#### `scenarios.delayed.vrla_cost_change`
- **Default**: `-0.02` (-2% per year)
- **Description**: Slight VRLA cost decline (competitive response)
- **Rationale**: VRLA industry responds to Li-ion threat with efficiency improvements

#### `scenarios.delayed.adoption_acceleration`
- **Default**: `0.7` (30% slower)
- **Description**: Risk aversion, supply chain concerns slow adoption
- **Impact**: Tipping point 3-5 years later; 2040 Li-ion share -10-15 pp

### High OpEx Scenario

#### `scenarios.high_opex.opex_weight_multiplier`
- **Default**: `1.5`
- **Description**: Emphasize operational cost differences (not in current model - placeholder)
- **Usage**: Could amplify OpEx impact in TCO if implemented
- **Rationale**: Scenarios where energy/labor costs surge

---

## Data Source Parameters

### `data_sources.taxonomy`
- **Default**: `"datacenter_ups_taxonomy_and_datasets.json"`
- **Description**: JSON file mapping dataset names to taxonomy entities
- **Location**: `data/` directory
- **Usage**: Defines which datasets to load for each variable

### `data_sources.vrla_demand`
- **Default**: `"datacenter_battery_demand_lab.json"`
- **Description**: Historical VRLA annual capacity demand (MWh/year)
- **Taxonomy Key**: `Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_<region>`

### `data_sources.lithium_demand`
- **Default**: `"datacenter_battery_demand_li_ion.json"`
- **Description**: Historical Li-ion annual capacity demand (MWh/year)
- **Taxonomy Key**: `Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_<region>`

### `data_sources.vrla_installed_base`
- **Default**: `"datacenter_vrla_installed_base.json"`
- **Description**: Historical VRLA installed base (MWh)
- **Taxonomy Key**: `Lead_acid_batteries_UPS_Datacenter_Installed_Base_<region>`

### `data_sources.lithium_costs`
- **Default**: `"bess_4hour_turnkey_costs.json"`
- **Description**: Grid-scale BESS 4-hour turnkey costs ($/kWh) - proxy for Li-ion UPS
- **Taxonomy Key**: `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>`

### `data_sources.vrla_costs`
- **Default**: `"vrla_battery_costs.json"`
- **Description**: VRLA battery costs ($/kWh)
- **Taxonomy Key**: `VRLA_Battery_Cost_Global`

### `data_sources.growth_rates`
- **Default**: `"datacenter_ups_growth.json"`
- **Description**: Datacenter capacity growth projections (% per year)
- **Taxonomy Key**: `Datacenter_capacity_growth_projections_<region>`

---

## Parameter Sensitivity Analysis

### High-Impact Parameters (Tipping Point ±2+ years)

| Parameter | Baseline | +10% Change | Tipping Δ | 2040 Li Share Δ |
|-----------|----------|-------------|-----------|-----------------|
| **VRLA OpEx** | $18/kWh-yr | $19.8 | -1.8 years | +6 pp |
| **Li-ion OpEx** | $6/kWh-yr | $6.6 | +1.5 years | -5 pp |
| **VRLA Lifespan** | 5 years | 5.5 years | +2.2 years | -8 pp |
| **Li-ion Lifespan** | 12 years | 13.2 years | -1.8 years | +6 pp |
| **Discount Rate** | 8% | 8.8% | -1.0 years | +4 pp |
| **VRLA CapEx** | $220/kWh | $242 | -1.2 years | +4 pp |
| **Li-ion CapEx** | $180/kWh | $198 | +1.5 years | -5 pp |

### Medium-Impact Parameters (Tipping Point ±1 year)

| Parameter | Baseline | Change | Tipping Δ | Impact |
|-----------|----------|--------|-----------|---------|
| **S-curve k₀** | 0.5 | → 0.6 | 0 | Adoption 1 year faster |
| **S-curve L** | 0.95 | → 0.90 | 0 | Final share -5 pp |
| **TCO Horizon** | 15 years | → 13 years | +1.2 years | Favor VRLA |
| **Cost Sensitivity s** | 0.002 | → 0.003 | 0 | Faster if large TCO gap |

### Low-Impact Parameters (Minimal Effect)

- UPS reliability premium (±5% → ±0.3 year)
- Smoothing window (±1 year → noise only)
- Battery metrics (duration, cycles, RTE) - no impact on demand forecast

### Interaction Effects

**OpEx × Lifespan**:
- High VRLA OpEx + Short VRLA Life = **Very strong** Li-ion advantage (tipping -3 to -4 years)
- Low Li-ion OpEx + Long Li-ion Life = **Amplified** advantage

**Discount Rate × Lifespan**:
- High r (10%) + Long Li-ion Life (15y) = **Stronger** Li-ion advantage (future savings valued less, but life gap matters more)

**Cost Decline × Adoption Acceleration**:
- Fast Li-ion decline (12%) + High acceleration (1.5×) = **Very rapid** transition (tipping -4 years, 2035 Li share 90%+)

---

## Calibration Guidance

### Step 1: Collect Historical Data
- **Required**: 5+ years of (year, cost, adoption share) for each technology
- **Sources**: BNEF, IEA, datacenter operator reports, vendor quotes

### Step 2: Fit Cost Trajectories
- VRLA: Typically flat (validate with ±2% annual change)
- Li-ion: Log-CAGR from BESS proxy (validate 6-12% decline range)

### Step 3: Calibrate S-Curve
```python
from scipy.optimize import curve_fit

def s_curve(t, L, t0, k):
    return L / (1 + np.exp(-k * (t - t0)))

# Fit to historical adoption data
params, cov = curve_fit(s_curve, years, adoption_data,
                         bounds=([0.9, 2020, 0.1], [0.99, 2040, 2.0]))
L_fit, t0_fit, k_fit = params
```

### Step 4: Validate Backtest
- Compare forecast to historical years (holdout last 2-3 years)
- Target: <10% MAPE on adoption share, <5% on total demand

### Step 5: Sensitivity Analysis
- Vary high-impact parameters ±10-20%
- Ensure tipping point within reasonable range (±3 years)

---

## Best Practices

1. **Always run sensitivity analysis** on OpEx and lifespan (highest impact)
2. **Use regional-specific discount rates** (not global 8% for all)
3. **Validate mass balance** (errors compound over time)
4. **Cross-check BESS proxy** with any available direct UPS cost data
5. **Document assumptions** (especially if overriding calibrated parameters)
6. **Test scenario extremes** (accelerated + delayed) to bound uncertainty
7. **Review adoption ceiling L** for regional appropriateness
8. **Update calibration** as new data becomes available (annual refresh)

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Maintainer**: Datacenter UPS Battery Forecasting Team
