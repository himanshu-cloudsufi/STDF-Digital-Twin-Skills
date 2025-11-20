# Datacenter UPS Skill Evaluations

This directory contains evaluation scenarios for testing the datacenter-ups skill functionality.

## Evaluation Files

### 1. `eval_basic_forecast.json`
Tests basic forecasting capability for a single region (China) showing VRLA to Li-ion transition.

**Key Tests:**
- Data loading and processing
- TCO calculation and tipping point detection
- S-curve adoption modeling
- Installed base tracking
- Mass balance validation
- Output generation (CSV/JSON)

**Expected Outcomes:**
- Tipping point around 2027
- 75-85% Li-ion share by 2035
- Non-negative demand values
- Mass balance consistency

### 2. `eval_tco_analysis.json`
Tests detailed Total Cost of Ownership analysis for USA.

**Key Tests:**
- VRLA TCO calculation (CapEx + OpEx + replacements)
- Li-ion TCO calculation with declining costs
- NPV calculations with 8% discount rate
- Tipping point identification (3+ year persistence)
- Cost component breakdown

**Expected Outcomes:**
- Tipping point around 2028 for USA
- TCO crossover before price parity (OpEx advantage)
- Realistic cost values
- 15-year horizon analysis

### 3. `eval_scenario_comparison.json`
Tests scenario analysis comparing baseline, accelerated, and delayed adoption paths for Europe.

**Key Tests:**
- Multiple scenario execution
- Scenario comparison analysis
- Parameter sensitivity (CAGR variations)
- Adoption timing differences
- Market share variance

**Expected Outcomes:**
- Baseline: tipping ~2029, 75-80% Li-ion by 2035
- Accelerated: tipping ~2026, 88-92% Li-ion by 2035
- Delayed: tipping ~2032, 60-70% Li-ion by 2035
- ±3 year tipping point range across scenarios

### 4. `eval_global_aggregation.json`
Tests regional aggregation and global forecasting capabilities.

**Key Tests:**
- Multi-region forecast execution
- Regional result aggregation
- Mass balance at global level
- Regional heterogeneity analysis
- Data consistency validation

**Expected Outcomes:**
- Global totals = sum of regional demands (±1% tolerance)
- Regional tipping points: China ~2027, USA ~2028, Europe ~2029, RoW ~2030
- 80-85% global Li-ion share by 2035
- ~40-50 GWh/year total demand by 2035

### 5. `eval_adoption_sensitivity.json`
Tests sensitivity analysis for key model parameters.

**Key Tests:**
- Discount rate sensitivity (6%, 8%, 10%)
- Lifespan sensitivity (10yr, 12yr, 15yr)
- S-curve ceiling sensitivity (90%, 95%, 99%)
- Parameter impact on tipping point
- Adoption rate variations

**Expected Outcomes:**
- Discount rate: ±2% → ±1-2 year tipping shift
- Lifespan: +3 years → -2 year tipping, +6 pp adoption
- Ceiling: affects final market penetration (90-99%)
- ±3 year tipping point uncertainty range

### 6. `eval_replacement_dynamics.json`
Tests market decomposition and replacement demand analysis.

**Key Tests:**
- New-build vs replacement breakdown
- Contestable market identification
- Technology-specific retirement rates
- Installed base evolution
- Demand composition over time

**Expected Outcomes:**
- 2025-2028: ~70% new-build, ~30% replacement
- By 2035: ~70-75% replacement demand
- VRLA peaks around 2027-2028, then declines
- 5-7 year transition lag from tipping to high adoption

### 7. `eval_mass_balance_validation.json`
Tests comprehensive validation and mass balance reconciliation.

**Key Tests:**
- Stock-flow consistency (IB(t) = IB(t-1) + Adds - Retirements)
- Technology-specific retirement rates
- Demand sum consistency (VRLA + Li-ion = Total)
- Non-negativity constraints
- Share bounds (0-100%)
- S-curve monotonicity

**Expected Outcomes:**
- Mass balance error < 0.1%
- All validation checks pass
- No negative values
- Shares sum to 100%
- Monotonic Li-ion adoption post-tipping

## Running Evaluations

### Manual Testing

Run individual forecasts:
```bash
cd .claude/skills/datacenter-ups

# Basic forecast
python3 scripts/forecast.py --region China --scenario baseline --output output/china_baseline.csv

# Scenario comparison
python3 scripts/forecast.py --region Europe --scenario baseline --output output/europe_baseline.csv
python3 scripts/forecast.py --region Europe --scenario accelerated --output output/europe_accelerated.csv
python3 scripts/compare_scenarios.py output/europe_baseline.csv output/europe_accelerated.csv
```

### Validation Scripts

Validate outputs:
```bash
# Mass balance validation
python3 scripts/validate_mass_balance.py --input output/china_baseline.csv

# Output validation
python3 scripts/validate_output.py output/china_baseline.csv

# Extract key metrics
python3 scripts/extract_metrics.py output/china_baseline.csv
```

### Global Forecast

Run global aggregation:
```bash
python3 scripts/forecast.py --region Global --scenario baseline --output output/global_baseline.csv
```

## Expected Behavior Summary

All evaluations should demonstrate:
1. **Data Loading**: Successful loading of taxonomy-mapped datasets
2. **TCO Analysis**: Realistic cost calculations with proper discounting
3. **Tipping Point**: Identification of economic crossover year (2025-2030 range)
4. **S-Curve Adoption**: Smooth logistic adoption curve (not step function)
5. **Mass Balance**: Stock-flow consistency within 0.1% tolerance
6. **Regional Variance**: Heterogeneous adoption timing across regions
7. **Validation**: All output constraints satisfied
8. **Reproducibility**: Consistent results for same parameters

## Known Issues

- **Market Decomposition**: Early years (2021-2027) may show decomposition warnings due to installed base initialization. This is expected and doesn't affect forecast validity.
- **TCO Validation**: Some regions may fail strict TCO validation if market decomposition exceeds 15% tolerance in early years.

## Success Criteria

An evaluation passes if:
- ✓ Forecast completes without errors
- ✓ Mass balance validation passes (< 0.1% error)
- ✓ Output files generated with expected columns
- ✓ Tipping point detected within reasonable range (2020-2035)
- ✓ Final Li-ion adoption reaches 75-95% range
- ✓ All demand values non-negative
- ✓ Regional aggregation sums correctly (±1%)
