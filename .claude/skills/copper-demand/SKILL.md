---
name: copper-demand
description: >
  Forecasts refined copper demand (tonnes/year) using a hybrid bottom-up + top-down methodology.
  Use when analyzing copper consumption, green transition impacts, EV copper demand, or renewable energy copper requirements.
  Handles regions: China, USA, Europe, Rest_of_World, Global.
  Features two-tier approach: TIER 1 (Automotive, Grid Generation) with bottom-up calculations from driver data,
  TIER 2 (Construction, Industrial, Electronics) with top-down allocation from segment shares.
  Accounts for EV transition (3-4× copper intensity vs ICE) and renewable energy buildout (wind/solar 5-10× vs fossil).
  Trigger keywords: copper demand, copper forecast, copper consumption, green transition copper, EV copper, renewable copper, copper modeling. (project)
---

# Copper Demand Forecasting Skill

Forecasts refined copper consumption using a two-tier hybrid methodology that combines bottom-up driver calculations with top-down segment allocation.

## Quick Start

**Basic forecast:**
```bash
python3 scripts/forecast.py --scenario baseline --region Global --end-year 2030
```

**Compare scenarios:**
```bash
python3 scripts/compare_scenarios.py output/copper_demand_Global_baseline_2040.csv \
                                      output/copper_demand_Global_accelerated_2040.csv
```

**Validate output:**
```bash
python3 scripts/validate_output.py output/copper_demand_Global_baseline_2040.csv
```

## Key Capabilities

- **Scenario Analysis**: Model green transition pathways (baseline, accelerated, delayed, substitution)
- **Regional Forecasts**: China, USA, Europe, Rest_of_World, Global
- **EV Transition Modeling**: 3-4× copper intensity multiplier (BEV vs ICE)
- **Renewable Energy Impact**: Wind and solar copper intensity tracking
- **Substitution Risk**: Aluminum substitution in vulnerable segments

## Two-Tier Methodology

**TIER 1 (High Confidence - Bottom-up):**
- Automotive: Vehicle sales × copper intensity by powertrain
- Grid Generation: Capacity additions × technology-specific copper content

**TIER 2 (Lower Confidence - Top-down):**
- Construction, Industrial, Electronics: Allocated from total using segment shares
- Grid T&D: Residual-based calculation

See `reference/methodology.md` for detailed methodology.

## Available Scenarios

| Scenario | EV Adoption 2040 | Renewables 2040 | 2040 Demand | vs Baseline |
|----------|------------------|-----------------|-------------|-------------|
| **Baseline** | 75% | 15 TW | ~30 Mt | - |
| **Accelerated** | 92% | 20 TW | ~37.5 Mt | +25% |
| **Delayed** | 55% | 11 TW | ~25.5 Mt | -15% |
| **Substitution** | 75% | 15 TW | ~28 Mt | -7% |

See `reference/scenarios.md` for scenario details and assumptions.

## Output Format

CSV/JSON files with columns:
- Annual demand by segment (automotive, grid generation, construction, grid T&D, industrial, electronics, other)
- OEM vs replacement breakdown
- Confidence tags per segment
- Share calculations (transport %, EV %, green copper %)

See `reference/data-schema.md` for complete output specification.

## Validation Tools

**Pre-run validation:**
```bash
python3 scripts/validate_scenario.py config.json baseline
```

**Post-run validation:**
```bash
python3 scripts/validate_output.py output/copper_demand_Global_baseline_2040.csv
```

Checks reconciliation, segment shares, growth rates, and data completeness.

## Workflows

Common analysis workflows with step-by-step checklists:
1. Green transition scenario analysis
2. Regional demand comparison
3. Substitution risk assessment
4. Multi-scenario strategic planning
5. Sensitivity analysis

See `reference/workflows.md` for detailed workflow guides.

## Evaluations

Test the skill with evaluation scenarios:
- `eval-1-basic-forecast.json` - Basic forecast generation
- `eval-2-scenario-comparison.json` - Scenario differentiation
- `eval-3-regional-analysis.json` - Regional support
- `eval-4-ev-impact.json` - EV impact calculations
- `eval-5-substitution-risk.json` - Substitution scenario

See `evaluations/README.md` for evaluation suite details.

## Key Parameters

Configured in `config.json`:
- **Copper Coefficients**: BEV (83 kg), ICE (23 kg), Wind (6-10 t/MW), Solar (5 t/MW)
- **Segment Shares**: Construction (48% electrical), Industrial (17% electrical), Electronics (11% total)
- **Scenario Drivers**: EV adoption targets, renewable capacity, demand multipliers

## Regional Coverage

- **China**: Largest consumer, construction-heavy, infrastructure focus
- **USA/Europe**: Higher automotive share, faster EV adoption, grid modernization
- **Rest_of_World**: Infrastructure development, lower EV penetration
- **Global**: Aggregated total or independent calculation

## Confidence Levels

- **HIGH_BOTTOM_UP**: Automotive (full driver data)
- **MEDIUM_BOTTOM_UP**: Grid generation (capacity data available)
- **LOW_ALLOCATED**: Construction, industrial, electronics (top-down shares)
- **LOW_RESIDUAL**: Grid T&D, other uses (residual calculation)

## Data Sources

Historical data from:
- Vehicle sales by powertrain (Passenger Cars, Commercial Vehicles, Two/Three Wheelers)
- Generation capacity by technology (Wind, Solar, Fossil)
- Copper consumption and segment shares

## Technical Notes

- **Forecast Horizon**: 2020-2040 (21 years), annual granularity
- **Reconciliation**: Forces segments to sum exactly to total consumption
- **Smoothing**: 3-year rolling window for noise reduction
- **Guards**: Growth rate limits (max +50% YoY, min -30% YoY), non-negativity

## References

Methodology based on:
- International Copper Association (ICA) studies
- International Copper Study Group (ICSG) data
- IEA Energy Transition scenarios
- BloombergNEF EV Outlook
- IRENA Renewable Capacity Statistics

---

**Need more detail?** Reference documents provide comprehensive information:
- `reference/methodology.md` - Full two-tier methodology explanation
- `reference/scenarios.md` - Scenario parameters and sensitivities
- `reference/data-schema.md` - Output formats and configuration
- `reference/workflows.md` - Step-by-step analysis workflows