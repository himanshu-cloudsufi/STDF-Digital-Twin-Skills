# Methodology Reference - Energy Forecasting (SWB)

## Overview

The energy forecasting methodology models Solar-Wind-Battery (SWB) capacity growth and the displacement of fossil fuels (coal, gas) using cost-driven disruption analysis.

## Key Methodology Differences from Vehicle Forecasting

| Aspect | SWB Energy | Passenger Vehicles |
|--------|-----------|-------------------|
| Forecasting Method | YoY growth averaging | Logistic S-curve |
| Disruptor | Multi-component stack (S+W+B) | Single product (BEV) |
| Cost Metric | LCOE + SCOE ($/MWh) | $/mile TCO |
| Capacity-Generation | Requires CF conversion | N/A (direct sales) |
| Displacement | Sequenced (coal-first or gas-first) | Residual calculation |
| Reserve Floors | 10% coal, 15% gas | None |

## Forecasting Pipeline

```
1. Cost Analysis
   └─> LCOE forecasting (log-CAGR + 3-year smoothing)
   └─> SCOE calculation for battery storage
   └─> SWB stack cost = MAX(Solar_LCOE, Wind_LCOE) + SCOE
   └─> Tipping point detection (SWB < min(Coal, Gas))

2. Capacity Forecasting
   └─> YoY growth averaging for each SWB component
   └─> Conditional CSP inclusion (if capacity > 1% solar)
   └─> Capacity factor assignment (historical or default)

3. Generation Derivation
   └─> Generation = Capacity × CF × 8760 hours

4. Displacement Sequencing
   └─> Calculate non-SWB baseline (nuclear, hydro)
   └─> Allocate residual to coal/gas by sequence
   └─> Enforce reserve floors (10% coal, 15% gas)

5. Validation
   └─> Energy balance: SWB + Coal + Gas + Non-SWB = Total
   └─> Non-negativity checks
   └─> Capacity factor bounds (5%-70%)
```

## 1. Cost Analysis

### SCOE (Storage Cost of Energy) Calculation

Formula for battery storage cost:

```
SCOE = (Capex × 1000) / (Cycles × Duration × RTE) + Fixed_OM

Where:
- Capex: Battery capital cost ($/kWh)
- Cycles: Battery lifetime cycles (default: 5000)
- Duration: Battery duration (2, 4, or 8 hours)
- RTE: Round-trip efficiency (default: 0.88 or 88%)
- Fixed_OM: Fixed O&M cost (default: $5/MWh)
```

### SWB Stack Cost

```
SWB_Stack_Cost = MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE
```

Rationale: The stack cost is the higher of solar or wind LCOE (since they're substitutes) plus battery storage.

### Tipping Point Detection

Tipping occurs when:
```
SWB_Stack_Cost < min(Coal_LCOE, Gas_LCOE)
```

Two tipping points tracked:
- **Tipping vs Coal**: SWB_Stack_Cost < Coal_LCOE
- **Tipping vs Gas**: SWB_Stack_Cost < Gas_LCOE

## 2. Capacity Forecasting (YoY Growth Averaging)

### Method

For each SWB component (Solar PV, Onshore Wind, Offshore Wind, Battery Storage):

1. Calculate year-over-year growth rates from historical data
2. Compute median growth rate (robust to outliers)
3. Apply median growth rate to forecast future years
4. Cap growth rate at ±50% per year

### Formula

```python
yoy_growth_rates = [(value[i] - value[i-1]) / value[i-1] for i in range(1, n)]
median_growth = median(yoy_growth_rates)

for year in forecast_years:
    capacity[year] = capacity[year-1] * (1 + median_growth)
```

### CSP Inclusion (Conditional)

CSP (Concentrated Solar Power) is included only if:
```
CSP_Capacity / Solar_PV_Capacity > 1% (in any forecast year)
```

## 3. Generation Derivation

### Capacity to Generation Conversion

```
Generation (GWh) = Capacity (GW) × Capacity_Factor × 8760 hours
```

### Capacity Factor Assignment

Hierarchy:
1. **Historical CF data**: If available in datasets, interpolate to forecast years
2. **Default CF with improvement**: Use default CF with 0.3% annual improvement
3. **Fallback defaults**:
   - Solar PV: 0.15 (15%)
   - CSP: 0.25 (25%)
   - Onshore Wind: 0.30 (30%)
   - Offshore Wind: 0.40 (40%)
   - Coal: 0.55 (55%)
   - Gas: 0.50 (50%)

### CF Improvement Over Time

```
CF(year) = CF(base_year) × (1 + 0.003)^(year - base_year)
```

Clamped to range: [0.05, 0.70]

## 4. Displacement Sequencing

### Displacement Sequences by Region

| Region | Sequence | Rationale |
|--------|----------|-----------|
| China | Coal-first | High coal dependency, policy push |
| USA | Gas-first | Gas-heavy grid, coal declining |
| Europe | Coal-first | Coal phase-out commitments |
| Rest_of_World | Coal-first | Default assumption |

### Coal-First Displacement

```python
residual = Total_Demand - SWB_Generation - Non_SWB_Generation

# Allocate to gas first (up to reserve floor)
gas_generation = min(residual, Total_Demand * 0.15)  # 15% reserve
residual -= gas_generation

# Rest to coal
coal_generation = residual
```

### Gas-First Displacement

```python
residual = Total_Demand - SWB_Generation - Non_SWB_Generation

# Allocate to coal first (up to reserve floor)
coal_generation = min(residual, Total_Demand * 0.10)  # 10% reserve
residual -= coal_generation

# Rest to gas
gas_generation = residual
```

### Reserve Floors

- **Coal Reserve Floor**: 10% of total demand
- **Gas Reserve Floor**: 15% of total demand

These represent minimum generation retained for grid stability/peaker plants.

## 5. Validation

### Energy Balance Check

```
abs(SWB + Coal + Gas + Non_SWB - Total_Demand) / Total_Demand < 2%
```

### Non-Negativity

All generation values must be ≥ 0.

### Capacity Factor Bounds

```
0.05 ≤ CF ≤ 0.70 (for renewable technologies)
```

Coal/gas/nuclear can exceed 0.70 (baseload).

## Key Formulas Summary

| Metric | Formula |
|--------|---------|
| SCOE | `(Capex × 1000) / (Cycles × Duration × RTE) + Fixed_OM` |
| SWB Stack Cost | `MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE` |
| Generation | `Capacity × CF × 8760` |
| YoY Growth | `median([(v[i]-v[i-1])/v[i-1] for i])` |
| Energy Balance | `SWB + Coal + Gas + Non_SWB = Total` |

## References

- **SWB Instructions**: `swb/swb_instructions_v4_updated.md`
- **Taxonomy**: `data/swb_taxonomy_and_datasets.json`
- **Configuration**: `config.json`
