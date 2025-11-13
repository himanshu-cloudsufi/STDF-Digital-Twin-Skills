# Workflow Reference Guide

## Overview

This guide provides step-by-step workflows for common copper demand forecasting analyses. Each workflow includes a checklist to ensure comprehensive analysis.

---

## Workflow 1: Green Transition Scenario Analysis

**Goal:** Assess copper demand implications of different green energy transition pathways

**Use Cases:**
- Policy impact assessment
- Supply adequacy planning
- Investment timing decisions

### Checklist

- [ ] **Define Scenarios**
  - [ ] Select scenarios to compare (baseline, accelerated, delayed)
  - [ ] Validate scenario parameters using `validate_scenario.py`
  - [ ] Document assumptions and parameter choices

- [ ] **Run Forecasts**
  - [ ] Run baseline scenario: `python3 scripts/forecast.py --scenario baseline --region Global --end-year 2045`
  - [ ] Run accelerated scenario: `python3 scripts/forecast.py --scenario accelerated --region Global --end-year 2045`
  - [ ] Run delayed scenario: `python3 scripts/forecast.py --scenario delayed --region Global --end-year 2045`
  - [ ] Verify all outputs generated successfully

- [ ] **Validate Outputs**
  - [ ] Run validation on each output: `python3 scripts/validate_output.py output/[filename]`
  - [ ] Check for reconciliation errors
  - [ ] Review warnings for unrealistic values
  - [ ] Verify growth rates within expected bounds

- [ ] **Compare Results**
  - [ ] Run comparison script: `python3 scripts/compare_scenarios.py output/copper_demand_Global_baseline_2045.csv output/copper_demand_Global_accelerated_2045.csv output/copper_demand_Global_delayed_2045.csv`
  - [ ] Analyze total demand differences (target: accelerated +25%, delayed -15% vs baseline)
  - [ ] Review automotive share evolution
  - [ ] Assess green copper (EV+Solar+Wind) share trends

- [ ] **Identify Key Drivers**
  - [ ] Calculate EV contribution to demand growth
  - [ ] Quantify renewable generation impact
  - [ ] Determine electrification multiplier effects
  - [ ] Identify inflection points and peak demand years

- [ ] **Document Insights**
  - [ ] Summarize demand range across scenarios (e.g., 25.5-37.5 Mt by 2045)
  - [ ] Highlight key sensitivities (EV adoption, renewable capacity)
  - [ ] Note supply implications and potential gaps
  - [ ] Document assumptions and caveats

### Expected Results

- **Baseline 2045:** ~30 Mt total, 27% green copper share
- **Accelerated 2045:** ~37.5 Mt total (+25%), 24% green copper share
- **Delayed 2045:** ~25.5 Mt total (-15%), 30% green copper share

### Common Issues

- If scenarios show identical results, check scenario application in `forecast.py`
- If reconciliation errors > 0.1%, review segment calculations
- If growth rates seem unrealistic, validate input data and coefficients

---

## Workflow 2: Regional Demand Analysis

**Goal:** Compare copper demand patterns across major regions

**Use Cases:**
- Regional supply planning
- Trade flow analysis
- Market entry decisions

### Checklist

- [ ] **Select Regions**
  - [ ] Choose regions to analyze (China, USA, Europe, Rest_of_World, Global)
  - [ ] Verify regional data availability in input files
  - [ ] Note any regional data gaps or limitations

- [ ] **Run Regional Forecasts**
  - [ ] Run China: `python3 scripts/forecast.py --region China --scenario baseline --end-year 2045`
  - [ ] Run USA: `python3 scripts/forecast.py --region USA --scenario baseline --end-year 2045`
  - [ ] Run Europe: `python3 scripts/forecast.py --region Europe --scenario baseline --end-year 2045`
  - [ ] Run Rest_of_World: `python3 scripts/forecast.py --region Rest_of_World --scenario baseline --end-year 2045`
  - [ ] Run Global for comparison: `python3 scripts/forecast.py --region Global --scenario baseline --end-year 2045`

- [ ] **Validate Regional Outputs**
  - [ ] Run validation on each regional output
  - [ ] Check if regional totals reconcile to global
  - [ ] Review confidence tags by segment and region
  - [ ] Note high/low confidence areas

- [ ] **Analyze Regional Patterns**
  - [ ] Compare total demand by region
  - [ ] Identify regional growth rates (CAGR)
  - [ ] Compare automotive share across regions
  - [ ] Assess regional EV adoption trajectories
  - [ ] Evaluate construction/industrial patterns

- [ ] **Identify Regional Drivers**
  - [ ] China: Construction and industrial demand drivers
  - [ ] USA/Europe: Automotive and grid electrification drivers
  - [ ] Rest_of_World: Infrastructure development drivers
  - [ ] Note regional policy and technology differences

- [ ] **Document Regional Insights**
  - [ ] Rank regions by 2045 demand
  - [ ] Calculate regional shares of global demand
  - [ ] Highlight fastest-growing regions
  - [ ] Note supply-demand balance implications by region

### Expected Patterns

- **China:** Largest absolute demand, construction-heavy, slowing growth
- **USA/Europe:** Higher automotive share, faster EV adoption, grid modernization
- **Rest_of_World:** Infrastructure-driven growth, lower EV share

### Common Issues

- Regional data may be incomplete for some segments (use LOW_ALLOCATED confidence tags)
- Sum of regions may not exactly equal Global due to independent calculation methods
- EV adoption rates vary significantly by region

---

## Workflow 3: Substitution Risk Assessment

**Goal:** Evaluate copper demand risks from aluminum substitution

**Use Cases:**
- Price impact analysis
- Material competition assessment
- Demand sensitivity testing

### Checklist

- [ ] **Define Substitution Scenario**
  - [ ] Validate substitution scenario parameters: `python3 scripts/validate_scenario.py config.json substitution`
  - [ ] Review coefficient reduction assumptions (default: 15%)
  - [ ] Verify annual thrifting rate (default: 0.7% per year)
  - [ ] Document trigger conditions (e.g., Cu/Al price ratio > 3.5)

- [ ] **Run Baseline and Substitution Scenarios**
  - [ ] Run baseline: `python3 scripts/forecast.py --scenario baseline --region Global --end-year 2045`
  - [ ] Run substitution: `python3 scripts/forecast.py --scenario substitution --region Global --end-year 2045`
  - [ ] Verify both outputs generated

- [ ] **Validate Outputs**
  - [ ] Run validation on both scenarios
  - [ ] Check that substitution affects only vulnerable segments
  - [ ] Verify BEV and renewable segments unchanged
  - [ ] Confirm progressive thrifting over time

- [ ] **Compare Scenarios**
  - [ ] Run comparison: `python3 scripts/compare_scenarios.py output/copper_demand_Global_baseline_2045.csv output/copper_demand_Global_substitution_2045.csv`
  - [ ] Calculate total demand difference (target: ~-7%)
  - [ ] Identify affected segments (construction, grid T&D)
  - [ ] Confirm protected segments (automotive BEV, wind, solar)

- [ ] **Quantify Substitution Impact**
  - [ ] Calculate tonnes of copper displaced
  - [ ] Determine timeline of substitution (start year, ramp-up, plateau)
  - [ ] Assess impact on supply-demand balance
  - [ ] Evaluate by segment vulnerability

- [ ] **Assess Segment Vulnerability**
  - [ ] **High Vulnerability:** Construction wiring (-15%), Grid T&D cables (-15%)
  - [ ] **Low Vulnerability:** Industrial motors (minimal), Electronics (minimal)
  - [ ] **No Substitution:** BEV (conductivity requirements), Wind/Solar (efficiency requirements)

- [ ] **Document Substitution Risks**
  - [ ] Summarize total demand at risk (~2 Mt by 2045)
  - [ ] Note price thresholds for substitution
  - [ ] Highlight protected high-growth segments
  - [ ] Assess net impact on demand growth trajectory

### Expected Results

- **Substitution 2045:** ~28 Mt total (-7% vs baseline)
- **Demand at Risk:** ~2 Mt displaced by aluminum
- **Protected Demand:** BEV, wind, solar unchanged (~8 Mt green copper)
- **Vulnerable Segments:** Construction, grid T&D see 15% intensity reduction

### Common Issues

- Substitution should NOT affect automotive BEV or renewable generation
- Thrifting should be progressive (small initially, larger over time)
- If substitution impact > 10%, review coefficient reduction parameter

---

## Workflow 4: Multi-Scenario Comparison

**Goal:** Comprehensive comparison of all scenarios for strategic planning

**Use Cases:**
- Strategic planning under uncertainty
- Risk-adjusted supply planning
- Portfolio analysis

### Checklist

- [ ] **Run All Scenarios**
  - [ ] Baseline: `python3 scripts/forecast.py --scenario baseline --region Global --end-year 2045`
  - [ ] Accelerated: `python3 scripts/forecast.py --scenario accelerated --region Global --end-year 2045`
  - [ ] Delayed: `python3 scripts/forecast.py --scenario delayed --region Global --end-year 2045`
  - [ ] Substitution: `python3 scripts/forecast.py --scenario substitution --region Global --end-year 2045`

- [ ] **Validate All Outputs**
  - [ ] Run validation on all four scenarios
  - [ ] Verify no reconciliation errors
  - [ ] Check growth rates within bounds
  - [ ] Review confidence tags consistency

- [ ] **Generate Comparison Report**
  - [ ] Run full comparison: `python3 scripts/compare_scenarios.py output/copper_demand_Global_baseline_2045.csv output/copper_demand_Global_accelerated_2045.csv output/copper_demand_Global_delayed_2045.csv output/copper_demand_Global_substitution_2045.csv`
  - [ ] Export to JSON if needed: `--format json`

- [ ] **Analyze Demand Range**
  - [ ] Identify minimum scenario (delayed: 25.5 Mt)
  - [ ] Identify maximum scenario (accelerated: 37.5 Mt)
  - [ ] Calculate demand uncertainty range (12 Mt or +/-20%)
  - [ ] Note central tendency (baseline/substitution: 28-30 Mt)

- [ ] **Compare Key Metrics**
  - [ ] Total demand by scenario (2025, 2030, 2035, 2040, 2045)
  - [ ] Automotive share evolution
  - [ ] Green copper (EV+Solar+Wind) share trends
  - [ ] CAGR across scenarios (0.3%-1.2%)

- [ ] **Identify Critical Uncertainties**
  - [ ] EV adoption trajectory (55%-92% by 2045)
  - [ ] Renewable capacity buildout (11-20 TW by 2045)
  - [ ] Electrification intensity (0.85x-1.25x multiplier)
  - [ ] Substitution risk (0%-7% demand loss)

- [ ] **Assess Supply Implications**
  - [ ] Map demand scenarios to supply capacity needs
  - [ ] Identify potential surplus scenarios (delayed)
  - [ ] Highlight potential shortage scenarios (accelerated)
  - [ ] Note timing of supply-demand inflection points

- [ ] **Prepare Strategic Recommendations**
  - [ ] Define base case scenario (typically baseline)
  - [ ] Identify upside and downside scenarios
  - [ ] Recommend supply strategy for each scenario
  - [ ] Suggest signposts to monitor scenario evolution

### Expected Comparison Matrix

| Scenario | 2045 Demand | vs Baseline | CAGR | EV Adoption | Renewables | Green Cu % |
|----------|-------------|-------------|------|-------------|------------|------------|
| Baseline | 30 Mt | - | 0.7% | 75% | 15 TW | 27% |
| Accelerated | 37.5 Mt | +25% | 1.2% | 92% | 20 TW | 24% |
| Delayed | 25.5 Mt | -15% | 0.3% | 55% | 11 TW | 30% |
| Substitution | 28 Mt | -7% | 0.5% | 75% | 15 TW | 29% |

### Common Issues

- Large demand ranges indicate high scenario uncertainty
- If all scenarios cluster tightly, review scenario differentiation
- Peak demand year varies by scenario (watch for demand plateaus)

---

## Workflow 5: Sensitivity Analysis

**Goal:** Test forecast sensitivity to key parameter changes

**Use Cases:**
- Uncertainty quantification
- Parameter importance ranking
- Robustness testing

### Checklist

- [ ] **Identify Parameters to Test**
  - [ ] EV adoption 2045 (vary ±10% from baseline)
  - [ ] Renewable capacity 2045 (vary ±5 TW from baseline)
  - [ ] Demand multiplier (test 0.9x, 1.0x, 1.1x)
  - [ ] Copper intensity coefficients (test ±10%)

- [ ] **Create Custom Scenarios**
  - [ ] Edit `config.json` to add custom scenarios
  - [ ] Example: `ev_adoption_high` (85%), `ev_adoption_low` (65%)
  - [ ] Validate each custom scenario: `python3 scripts/validate_scenario.py config.json custom_scenario`

- [ ] **Run Sensitivity Tests**
  - [ ] Run each parameter variation
  - [ ] Keep all other parameters constant (ceteris paribus)
  - [ ] Document parameter values for each run

- [ ] **Measure Impact**
  - [ ] Calculate demand change per parameter change
  - [ ] Example: 10% EV adoption change → X% demand change
  - [ ] Rank parameters by impact magnitude

- [ ] **Document Sensitivity Results**
  - [ ] Create sensitivity table (parameter vs demand impact)
  - [ ] Identify most sensitive parameters
  - [ ] Note non-linear relationships
  - [ ] Highlight threshold effects

### Expected Sensitivities (Global 2045)

- **EV Adoption:** 10% change → ~2-3% demand change (moderate sensitivity)
- **Renewable Capacity:** 5 TW change → ~5-7% demand change (high sensitivity)
- **Demand Multiplier:** 10% change → ~10% demand change (linear, high impact)
- **BEV Intensity:** 10% change → ~2% demand change (moderate, growing over time)

---

## Best Practices

### General Guidelines

1. **Always validate** scenarios before running forecasts
2. **Always validate** outputs after generating forecasts
3. **Document assumptions** explicitly for each analysis
4. **Use version control** for custom scenarios and config changes
5. **Archive outputs** with clear naming: `{metric}_{region}_{scenario}_{date}`

### Troubleshooting

| Issue | Check | Solution |
|-------|-------|----------|
| Scenarios identical | Scenario application in forecast.py | Verify demand multiplier applied |
| Reconciliation errors | Segment calculations | Check coefficient values and data |
| Unrealistic growth | Input data quality | Validate source data, apply smoothing |
| Missing regional data | Data loader fallback | Review confidence tags, use Global |
| Substitution too high | Coefficient reduction | Cap at 15% for vulnerable segments |

### Quality Checks

Before finalizing analysis:
- [ ] All validation scripts pass
- [ ] Reconciliation errors < 0.1%
- [ ] Growth rates within bounds (max 50% YoY growth, min -30% decline)
- [ ] Confidence tags documented
- [ ] Assumptions clearly stated
- [ ] Results peer-reviewed

---

## Quick Reference Commands

```bash
# Validate scenario
python3 scripts/validate_scenario.py config.json [scenario_name]

# Run forecast
python3 scripts/forecast.py --scenario [scenario] --region [region] --end-year 2045 --output-format [csv|json]

# Validate output
python3 scripts/validate_output.py output/[filename]

# Compare scenarios
python3 scripts/compare_scenarios.py output/[file1] output/[file2] [file3...] [--format table|json]
```

## Further Reading

- `reference/methodology.md` - Detailed two-tier methodology
- `reference/scenarios.md` - Scenario parameters and assumptions
- `reference/data-schema.md` - Output formats and data structures
