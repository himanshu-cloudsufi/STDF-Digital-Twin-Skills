---
name: datacenter-ups
description: >
  Forecasts datacenter UPS battery technology transition from VRLA (lead-acid) to Lithium-ion based on TCO economics.
  Use when analyzing datacenter battery demand, UPS technology transition, VRLA vs Li-ion adoption, or backup power systems.
  Handles regions: China, USA, Europe, Rest_of_World, Global.
  Models S-curve adoption driven by Total Cost of Ownership (TCO) parity, with VRLA 5-year vs Li-ion 12-year lifespans.
  Tracks installed base, new-build demand, and replacement demand for both technologies.
  Trigger keywords: datacenter ups, ups batteries, VRLA lithium, datacenter battery transition, backup power, TCO analysis. (project)
---

# Datacenter UPS Battery Technology Transition Skill

This skill models the economic-driven transition from VRLA (Valve-Regulated Lead-Acid) to Lithium-ion batteries in datacenter UPS (Uninterruptible Power Supply) systems, using TCO-based tipping point analysis and S-curve adoption modeling.

## Overview

The skill forecasts battery demand for datacenter backup power systems across two competing technologies:
- **VRLA (Incumbent)**: Lower CapEx (~$220/kWh), higher OpEx ($18/kWh-yr), 5-year lifespan
- **Lithium-ion (Disruptor)**: Declining CapEx, lower OpEx ($6/kWh-yr), 12-year lifespan

## Key Features

### TCO-Driven Analysis
- **Total Cost of Ownership**: CapEx + PV(OpEx) + Replacement Costs over 15-year horizon
- **Tipping Point Detection**: Year when Li-ion TCO ≤ VRLA TCO (sustained for 3+ years)
- **Cost Forecasting**: Log-CAGR for Li-ion decline, flat trajectory for VRLA

### Market Decomposition
- **New-Build Demand**: Batteries for newly constructed datacenters
- **Replacement Demand**: End-of-life replacements from installed base
- **Contestable Market**: VRLA reaching 5-year life can switch to Li-ion

### S-Curve Adoption Model
- **Logistic Function**: M(t) = L / (1 + exp(-k × (t - t0)))
- **Economic Sensitivity**: Steepness k linked to cost advantage
- **Technology Ceiling**: L = 90-99% (residual VRLA niche)

### Installed Base Accounting
- Separate tracking for VRLA and Li-ion stocks
- Technology-specific retirement rates (VRLA: 5y, Li-ion: 12y)
- Mass balance reconciliation

## Usage

```bash
# Run the datacenter UPS forecast
skill datacenter-ups

# With custom parameters
skill datacenter-ups --end-year 2040 --region China

# Generate TCO comparison
skill datacenter-ups --analyze-tco --output-format csv
```

## Parameters

Key parameters configured in `config.json`:
- **Cost Parameters**:
  - VRLA CapEx: ~$220/kWh (flat)
  - Li-ion CapEx: Uses BESS 4-hour turnkey costs as proxy
  - OpEx: VRLA $18/kWh-yr, Li-ion $6/kWh-yr
- **Lifespans**:
  - VRLA: 5 years
  - Li-ion: 12 years
- **S-Curve Parameters**:
  - L: Technology ceiling (0.90-0.99)
  - t0: Midpoint year
  - k0: Base adoption rate
  - s: Cost sensitivity factor
- **Financial**:
  - Discount rate: 8% (6-10% range)
  - TCO horizon: 15 years

## Outputs

The skill generates:
1. Annual battery demand by technology (MWh)
2. TCO comparison ($/kWh) over time
3. Tipping point year identification
4. Installed base evolution (VRLA vs Li-ion)
5. New-build vs replacement breakdown
6. Adoption curve (Li-ion market share)
7. Regional analysis and aggregation

## Data Requirements

### Available Datasets
- **Demand**: `Data_Center_Battery_Demand_(Li-Ion/LAB)_Annual_Capacity_Demand_<region>`
- **Costs**: `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>` (Li-ion proxy)
- **Costs**: `VRLA_Battery_Cost_Global` (flat ~$220/kWh)
- **Growth**: `Datacenter_UPS_annual_growth_<region>` (7-10% typical)
- **Installed Base**: `Data_Center_Battery_Demand_(LAB)_Installed_base_<region>`

### Missing/Initialized
- Li-ion installed base often starts at 0 (conservative)
- Regional cost adjustments applied where needed

## Validation

The skill validates:
- VRLA_Demand + Li_Demand ≈ Total_Market_Demand (±5%)
- Mass balance: Adds - Retirements = ΔIB (±0.1%)
- Non-negativity constraints on all stocks and flows
- S-curve monotonicity and bounds

## Scenarios

Pre-configured scenarios:
- **Baseline**: Current cost trajectories, moderate adoption
- **Accelerated**: Faster Li-ion cost decline, early tipping
- **Delayed**: Slower cost parity, extended VRLA dominance
- **High OpEx**: Emphasize operational cost advantages

## Regional Considerations

- **China**: Lower costs, faster adoption typical
- **USA**: Moderate costs, reliability focus
- **Europe**: Higher costs, sustainability drivers
- **Rest_of_World**: Varied, often follows USA trends
- **Global**: Aggregate of regional results (avoid double-counting)

## Technical Details

- **Horizon**: 10-15 years typical, extendable to 2040/2050
- **Time Step**: Annual
- **Primary Unit**: MWh/year (flows), MWh (stocks)
- **Duration**: 4-hour default for UPS systems
- **Cycles**: ~250/year for backup use
- **Round-trip Efficiency**: 88% for Li-ion

## Cost Data Adaptation

Using grid-scale BESS costs as UPS proxy:
- Duration match: Both 4-hour systems
- Cycle life: UPS cycles less (backup only)
- Reliability premium: Optional 5-10% adjustment
- Directional trends matter most for tipping point

## References

Based on:
- Datacenter UPS market analysis
- Battery technology cost curves
- TCO methodology for technology transitions
- S-curve adoption modeling literature