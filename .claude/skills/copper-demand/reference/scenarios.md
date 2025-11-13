# Scenario Reference Guide

## Overview

Scenarios model different pathways for the green energy transition and their impact on copper demand.

## Available Scenarios

### Baseline Scenario

**Description:** Moderate green transition aligned with current policy commitments

**Parameters:**
- EV Adoption 2045: 75%
- Renewable Capacity 2045: 15 TW
- Demand Multiplier: 1.0× (no adjustment)

**Characteristics:**
- Steady EV adoption following S-curve trajectory
- Renewable buildout matches stated policy scenarios (IEA STEPS)
- Balanced transition across all regions
- Total demand grows ~0.7% annually

**Use When:**
- Need reference/comparison baseline
- Want conservative estimates
- Modeling most likely scenario

**Expected 2045 Results:**
- Total Demand: ~30 Mt
- Automotive Share: ~19%
- EV Share: ~18%
- Green Copper (EV+Solar+Wind): ~27%

---

### Accelerated Scenario

**Description:** Aggressive green transition exceeding policy targets

**Parameters:**
- EV Adoption 2045: 92%
- Renewable Capacity 2045: 20 TW
- Demand Multiplier: 1.25× (25% increase)

**Characteristics:**
- Rapid EV adoption driven by technology breakthroughs or policy
- Accelerated renewable deployment (net-zero aligned)
- Higher electrification across all sectors
- Total demand grows ~1.2% annually

**Use When:**
- Modeling net-zero scenarios
- Planning for high-demand futures
- Stress-testing supply adequacy

**Expected 2045 Results:**
- Total Demand: ~37.5 Mt (+25% vs baseline)
- Automotive Share: ~15%
- EV Share: ~14%
- Green Copper (EV+Solar+Wind): ~24%

**Growth Drivers:**
- Higher EV adoption → +17% automotive demand
- More renewables → +33% grid generation demand
- Overall electrification → +25% across all segments

---

### Delayed Scenario

**Description:** Slower green transition due to economic or policy constraints

**Parameters:**
- EV Adoption 2045: 55%
- Renewable Capacity 2045: 11 TW
- Demand Multiplier: 0.85× (15% decrease)

**Characteristics:**
- Slower EV adoption (ICE vehicles persist longer)
- Reduced renewable deployment
- Lower overall electrification
- Total demand grows ~0.3% annually

**Use When:**
- Modeling downside risks
- Planning for low-demand scenarios
- Assessing supply surplus risks

**Expected 2045 Results:**
- Total Demand: ~25.5 Mt (-15% vs baseline)
- Automotive Share: ~22%
- EV Share: ~12%
- Green Copper (EV+Solar+Wind): ~30%

**Reduction Drivers:**
- Lower EV adoption → -8% automotive demand
- Fewer renewables → -27% grid generation demand
- Reduced electrification → -15% across all segments

---

### Substitution Scenario

**Description:** Baseline transition with aluminum substitution in vulnerable segments

**Parameters:**
- EV Adoption 2045: 75% (baseline)
- Renewable Capacity 2045: 15 TW (baseline)
- Coefficient Reduction: 15%
- Annual Thrifting: 0.7% per year

**Characteristics:**
- Copper-aluminum price ratio exceeds 3.5
- Substitution occurs in construction (wiring) and grid T&D (cables)
- No substitution in automotive BEVs or renewables (technical requirements)
- Progressive substitution over time (thrifting)

**Use When:**
- Modeling price-driven substitution
- Assessing demand risks from high copper prices
- Planning for competition from alternative materials

**Expected 2045 Results:**
- Total Demand: ~28 Mt (-7% vs baseline)
- Automotive Share: ~20% (unchanged)
- EV Share: ~19% (unchanged)
- Green Copper (EV+Solar+Wind): ~29%

**Vulnerable Segments:**
- Construction: -15% copper intensity
- Grid T&D: -15% copper intensity

**Protected Segments:**
- Automotive BEV: No substitution (conductivity requirements)
- Wind/Solar: No substitution (efficiency requirements)
- Industrial motors: Minimal substitution (performance requirements)

---

## Scenario Comparison Matrix

| Aspect | Baseline | Accelerated | Delayed | Substitution |
|--------|----------|-------------|---------|--------------|
| **2045 Total Demand** | 30 Mt | 37.5 Mt | 25.5 Mt | 28 Mt |
| **vs Baseline** | - | +25% | -15% | -7% |
| **EV Adoption** | 75% | 92% | 55% | 75% |
| **Renewable Capacity** | 15 TW | 20 TW | 11 TW | 15 TW |
| **CAGR** | 0.7% | 1.2% | 0.3% | 0.5% |
| **Automotive Share** | 19% | 15% | 22% | 20% |
| **Green Copper %** | 27% | 24% | 30% | 29% |
| **Peak Demand Year** | 2045 | 2045 | 2040 | 2043 |

## Using Scenarios

### Running a Scenario

```bash
# Baseline (default)
python3 scripts/forecast.py --scenario baseline --region Global --end-year 2045

# Accelerated
python3 scripts/forecast.py --scenario accelerated --region Global --end-year 2045

# Delayed
python3 scripts/forecast.py --scenario delayed --region Global --end-year 2045

# Substitution
python3 scripts/forecast.py --scenario substitution --region Global --end-year 2045
```

### Comparing Scenarios

To compare multiple scenarios:

1. Run each scenario with same region and end year
2. Outputs saved with scenario name in filename
3. Use comparison script or analyze JSON outputs

```bash
python3 scripts/forecast.py --scenario baseline --output-format json
python3 scripts/forecast.py --scenario accelerated --output-format json

# Compare outputs
python3 -c "
import json
with open('output/copper_demand_Global_baseline_2045.json') as f:
    baseline = json.load(f)
with open('output/copper_demand_Global_accelerated_2045.json') as f:
    accel = json.load(f)
# Analysis code...
"
```

## Scenario Sensitivity

### Key Sensitivities

**EV Adoption Impact:**
- 10% change in EV adoption → ~2-3% change in total demand
- Most sensitive: automotive and overall transport share
- Less sensitive: grid, construction, industrial

**Renewable Capacity Impact:**
- 5 TW change in renewables → ~5-7% change in grid generation demand
- Most sensitive: grid generation segment
- Moderate impact: grid T&D (reinforcement needs)
- Less sensitive: other segments

**Demand Multiplier Impact:**
- Direct linear relationship to total demand
- Applied after segment calculations
- Represents broader electrification trends

**Coefficient Reduction Impact:**
- 15% reduction in construction/grid T&D → ~7% total demand reduction
- Only affects vulnerable segments
- No impact on BEV or renewable segments

## Custom Scenarios

To create custom scenarios, modify `config.json`:

```json
{
  "scenarios": {
    "custom_scenario": {
      "description": "Your scenario description",
      "ev_adoption_2045": 0.80,
      "renewable_capacity_2045_tw": 18,
      "demand_multiplier": 1.15,
      "coefficient_reduction": 0.10  // optional
    }
  }
}
```

Then run:
```bash
python3 scripts/forecast.py --scenario custom_scenario
```

## Scenario Assumptions

### Common Assumptions Across All Scenarios

1. **Copper Intensity Coefficients:**
   - BEV: 83 kg, ICE: 23 kg (constant across scenarios)
   - Wind: 6-10 t/MW, Solar: 5 t/MW (constant)

2. **Segment Allocation:**
   - Construction: 48% of electrical
   - Industrial: 17% of electrical
   - Electronics: 11% of total

3. **Regional Patterns:**
   - China dominates construction/industrial
   - USA/Europe lead in automotive transition
   - Global aggregation follows weighted average

4. **Timeline:**
   - All scenarios run 2020-2045 (26 years)
   - EV adoption follows logistic curve to 2045 target
   - Renewable buildout linear with acceleration

### Scenario-Specific Assumptions

**Accelerated:**
- Faster battery cost decline
- Stronger policy support for EVs and renewables
- Grid reinforcement keeps pace with generation

**Delayed:**
- Slower battery adoption
- Weaker policy environment
- Grid expansion lags behind demand

**Substitution:**
- Cu/Al price ratio > 3.5 sustained
- Substitution begins 2025, reaches 15% by 2035
- Technical limitations prevent substitution in EVs/renewables

## References

Scenarios based on:
- IEA World Energy Outlook (STEPS, APS, NZE)
- BloombergNEF EV Outlook
- IRENA Renewable Capacity Statistics
- International Copper Association studies
