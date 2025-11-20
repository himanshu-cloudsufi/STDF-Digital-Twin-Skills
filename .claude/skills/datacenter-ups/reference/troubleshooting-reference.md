# Troubleshooting Reference Guide

Comprehensive guide for diagnosing and resolving common issues in the Datacenter UPS Battery Technology Transition model.

## Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Data-Related Issues](#data-related-issues)
- [Forecasting Issues](#forecasting-issues)
- [Validation Failures](#validation-failures)
- [Performance Issues](#performance-issues)
- [Advanced Diagnostics](#advanced-diagnostics)
- [Debug Mode Operations](#debug-mode-operations)
- [Error Message Reference](#error-message-reference)

---

## Quick Diagnostics

### Diagnostic Checklist

Run this sequence to identify most common issues:

```bash
# 1. Check data availability
python3 scripts/validate_data.py --region China --check-coverage

# 2. Validate configuration
python3 scripts/validate_config.py

# 3. Test with minimal dataset
python3 scripts/forecast.py --region China --end-year 2030 --debug

# 4. Check mass balance
python3 scripts/validate_mass_balance.py --region China

# 5. Verify output consistency
python3 scripts/validate_output.py output/datacenter_ups_China_baseline.csv
```

### Health Check Script

```python
#!/usr/bin/env python3
"""Quick health check for datacenter UPS forecasting"""

def health_check():
    checks = {
        "data_files_exist": check_data_files(),
        "config_valid": validate_config(),
        "dependencies_installed": check_dependencies(),
        "output_dir_writable": check_output_directory(),
        "sample_forecast_runs": test_minimal_forecast()
    }

    print("Health Check Results:")
    for check, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check}: {status}")

    return all(checks.values())
```

---

## Common Issues and Solutions

### Issue 1: "No tipping point detected within forecast horizon"

**Symptoms:**
- Model returns no tipping year
- Li-ion adoption remains minimal (<20%) throughout forecast
- Warning message: "No tipping point found - Li-ion does not achieve cost parity"

**Causes:**
1. Li-ion costs not declining sufficiently
2. VRLA costs incorrectly low
3. OpEx parameters not set correctly
4. Forecast horizon too short

**Solutions:**

```python
# Solution 1: Verify Li-ion cost data is loaded
python3 -c "
from data_loader import DatacenterUPSDataLoader
loader = DatacenterUPSDataLoader()
data = loader.load_all_data()
print('Li-ion costs:', data['bess_costs_4h'].get('China', 'NOT FOUND'))
"

# Solution 2: Check cost trajectories
python3 scripts/analyze_costs.py --region China --plot

# Solution 3: Extend forecast horizon
python3 scripts/forecast.py --region China --end-year 2050

# Solution 4: Verify OpEx assumptions in config.json
{
  "cost_parameters": {
    "vrla": {"opex_per_kwh_year": 18.0},  # Should be higher
    "lithium": {"opex_per_kwh_year": 6.0}  # Should be lower
  }
}

# Solution 5: Use accelerated scenario
python3 scripts/forecast.py --region China --scenario accelerated
```

**Root Cause Analysis:**
```python
def diagnose_no_tipping():
    # Load costs
    vrla_tco = calculate_tco(vrla_capex=220, vrla_opex=18, lifespan=5)
    li_tco = calculate_tco(li_capex=200, li_opex=6, lifespan=12)

    print(f"VRLA TCO: ${vrla_tco:.2f}/kWh")
    print(f"Li-ion TCO: ${li_tco:.2f}/kWh")
    print(f"Gap: ${vrla_tco - li_tco:.2f}/kWh")

    if li_tco > vrla_tco:
        print("→ Li-ion still more expensive. Check:")
        print("  1. Li-ion CapEx too high")
        print("  2. VRLA lifespan too long")
        print("  3. Discount rate too low")
```

---

### Issue 2: "Installed base reconciliation failed"

**Symptoms:**
- Error: "Mass balance imbalance exceeds tolerance"
- Warning: "VRLA mass balance imbalance in 2027: 2.3456 GWh"
- Installed base becomes negative or grows unrealistically

**Causes:**
1. Missing historical installed base data
2. Incorrect retirement rates
3. Demand/IB initialization mismatch
4. Numerical precision issues

**Solutions:**

```python
# Solution 1: Check installed base initialization
python3 scripts/validate_data.py --check-installed-base --region China

# Output should show:
# VRLA IB (2020): 125.4 GWh ✓
# Li-ion IB (2020): 0.0 GWh (initialized)

# Solution 2: Verify retirement calculations
python3 -c "
vrla_ib = 125.4  # GWh
vrla_lifespan = 5  # years
retirement_rate = 1.0 / vrla_lifespan
annual_retirements = vrla_ib * retirement_rate
print(f'Annual VRLA retirements: {annual_retirements:.2f} GWh/year')
print(f'Retirement rate: {retirement_rate*100:.1f}%/year')
"

# Solution 3: Apply smoothing to installed base
python3 scripts/forecast.py --region China --allow-ib-smoothing

# Solution 4: Increase mass balance tolerance (temporary)
{
  "validation_rules": {
    "mass_balance_tolerance": 0.005  # Increase from 0.001 to 0.005
  }
}
```

**Diagnostic Function:**
```python
def diagnose_mass_balance(year_data):
    """Check mass balance for a specific year"""
    ib_start = year_data['ib_start']
    ib_end = year_data['ib_end']
    adds = year_data['demand']
    retirements = year_data['retirements']

    expected_ib_end = ib_start + adds - retirements
    actual_ib_end = ib_end

    imbalance = abs(expected_ib_end - actual_ib_end)
    imbalance_pct = imbalance / actual_ib_end * 100

    print(f"IB Start: {ib_start:.2f}")
    print(f"+ Adds: {adds:.2f}")
    print(f"- Retirements: {retirements:.2f}")
    print(f"= Expected IB End: {expected_ib_end:.2f}")
    print(f"  Actual IB End: {actual_ib_end:.2f}")
    print(f"  Imbalance: {imbalance:.4f} GWh ({imbalance_pct:.2f}%)")

    return imbalance_pct < 0.1  # Pass if < 0.1%
```

---

### Issue 3: "S-curve fitting failed - parameters unrealistic"

**Symptoms:**
- Warning: "S-curve parameters outside bounds"
- Adoption curve shows sudden jumps or drops
- Fitted L > 1.0 or k < 0

**Causes:**
1. Insufficient historical data points
2. Noisy adoption data
3. Poor initial parameter guesses
4. Cost advantage not correlated with adoption

**Solutions:**

```python
# Solution 1: Check historical data quality
python3 scripts/inspect_data.py --dataset "Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_USA"

# Solution 2: Use fallback heuristics
{
  "s_curve_parameters": {
    "calibration_method": "heuristic",  # Instead of "least_squares"
    "ceiling_L": 0.95,  # Fix ceiling
    "midpoint_t0": null,  # Auto-detect from tipping
    "base_steepness_k0": 0.4  # Conservative default
  }
}

# Solution 3: Manual parameter override
{
  "s_curve_overrides": {
    "Europe": {
      "L": 0.92,
      "t0": 2030,
      "k0": 0.38,
      "s": 0.0015
    }
  }
}

# Solution 4: Smooth historical data before fitting
python3 scripts/smooth_historical.py --window 3 --method median
```

**S-Curve Diagnostic:**
```python
def diagnose_s_curve(historical_shares):
    """Analyze S-curve fitting issues"""
    import numpy as np
    from scipy.optimize import curve_fit

    years = np.array(list(historical_shares.keys()))
    shares = np.array(list(historical_shares.values()))

    # Check data quality
    print(f"Data points: {len(shares)}")
    print(f"Share range: {shares.min():.1%} to {shares.max():.1%}")
    print(f"Monotonic: {all(shares[i] <= shares[i+1] for i in range(len(shares)-1))}")

    # Try fitting with different initial guesses
    initial_guesses = [
        [0.95, years.mean(), 0.3],  # Conservative
        [0.98, years.mean(), 0.5],  # Moderate
        [0.90, years.mean(), 0.7]   # Aggressive
    ]

    for i, p0 in enumerate(initial_guesses):
        try:
            popt, _ = curve_fit(s_curve, years, shares, p0=p0,
                               bounds=([0.8, years.min(), 0.1],
                                      [0.99, years.max(), 2.0]))
            print(f"Guess {i}: L={popt[0]:.2f}, t0={popt[1]:.0f}, k={popt[2]:.2f} ✓")
        except:
            print(f"Guess {i}: Failed to converge ✗")
```

---

## Data-Related Issues

### Missing Dataset Errors

**Error:** `KeyError: 'Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_China'`

**Solution:**
```bash
# Check if file exists
ls -la data/Energy_Storage.json

# Validate JSON structure
python3 -c "import json; json.load(open('data/Energy_Storage.json'))"

# Check dataset keys
python3 scripts/list_datasets.py --file Energy_Storage.json

# Use fallback to Global data
python3 scripts/forecast.py --region China --use-global-costs
```

### Data Quality Warnings

**Warning:** `Historical data has large gap between 2019 and 2022`

**Solution:**
```python
# Apply interpolation
python3 scripts/interpolate_data.py --dataset vrla_demand --method linear --max-gap 3

# Or use forward-fill
python3 scripts/fill_gaps.py --dataset lithium_demand --method forward
```

### Regional Data Unavailable

**Error:** `No data available for region: Rest_of_World`

**Solution:**
```bash
# Use proxy data from USA
python3 scripts/forecast.py --region Rest_of_World --proxy-region USA --proxy-multiplier 1.1

# Or create synthetic data
python3 scripts/generate_proxy_data.py --target Rest_of_World --source USA --scale 0.4
```

---

## Forecasting Issues

### Negative Demand Values

**Error:** `Negative demand values detected`

**Diagnosis:**
```python
def check_demand_calculation():
    # Common causes of negative demand:
    # 1. Market share > 100%
    # 2. Replacement demand > total demand
    # 3. Numerical instability in S-curve

    if lithium_share > 1.0:
        print("ERROR: Li-ion share exceeds 100%")
        print("Fix: Check S-curve ceiling and calibration")

    if replacement_demand > total_demand:
        print("ERROR: Replacement exceeds total market")
        print("Fix: Check retirement rate calculations")
```

### Unrealistic Growth Rates

**Warning:** `Market growth exceeds 50% year-over-year`

**Solution:**
```python
# Cap growth rates
MAX_GROWTH = 0.15  # 15% max annual growth

def apply_growth_cap(growth_rates):
    capped = growth_rates.copy()
    for year in capped.index:
        if capped[year] > MAX_GROWTH:
            print(f"Capping {year}: {capped[year]:.1%} → {MAX_GROWTH:.1%}")
            capped[year] = MAX_GROWTH
    return capped
```

### Adoption Curve Non-Monotonic

**Issue:** Li-ion share decreases in some years

**Fix:**
```python
def enforce_monotonic_adoption(shares):
    """Ensure adoption never decreases"""
    monotonic = shares.copy()
    for i in range(1, len(monotonic)):
        if monotonic[i] < monotonic[i-1]:
            print(f"Year {i}: Holding at {monotonic[i-1]:.1%}")
            monotonic[i] = monotonic[i-1]
    return monotonic
```

---

## Validation Failures

### Total Demand Validation Failure

**Error:** `Year 2023 exceeds tolerance (error: 12.3%)`

**Diagnosis Steps:**
1. Compare VRLA + Li-ion vs Total market data
2. Check for data version mismatches
3. Verify units consistency (MWh vs GWh)

```python
def diagnose_demand_validation(year):
    vrla = load_data(f"vrla_demand_{year}")
    li_ion = load_data(f"lithium_demand_{year}")
    total = load_data(f"total_demand_{year}")

    calculated = vrla + li_ion
    error = abs(calculated - total) / total

    print(f"Year {year}:")
    print(f"  VRLA: {vrla:.2f} GWh")
    print(f"  Li-ion: {li_ion:.2f} GWh")
    print(f"  Sum: {calculated:.2f} GWh")
    print(f"  Total Market: {total:.2f} GWh")
    print(f"  Error: {error:.1%}")

    if error > 0.05:
        print("Possible causes:")
        print("  1. Other battery technologies (NiMH, etc.)")
        print("  2. Data collection methodology changed")
        print("  3. Regional allocation issues")
```

### Backtest Validation Failure

**Error:** `Historical forecast error exceeds 15% MAPE`

**Solution:**
```python
# Recalibrate model with recent data
python3 scripts/recalibrate.py --holdout-years 2 --method rolling

# Adjust scenario parameters
{
  "scenarios": {
    "baseline": {
      "lithium_cost_decline_rate": 0.10,  # Increase from 0.08
      "adoption_acceleration": 1.2  # Speed up adoption
    }
  }
}
```

---

## Performance Issues

### Slow Execution

**Issue:** Forecast takes >30 seconds for single region

**Optimizations:**
```python
# 1. Use vectorized operations
import numpy as np

# Slow (loop)
for i in range(len(years)):
    tco[i] = calculate_tco(costs[i], opex, lifespan)

# Fast (vectorized)
tco = np.vectorize(calculate_tco)(costs, opex, lifespan)

# 2. Cache expensive calculations
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_tco_cached(capex, opex, lifespan, discount_rate):
    return compute_tco(capex, opex, lifespan, discount_rate)

# 3. Disable debug output
python3 scripts/forecast.py --region China --quiet

# 4. Use multiprocessing for scenarios
python3 scripts/run_scenarios.py --parallel --workers 4
```

### Memory Issues

**Error:** `MemoryError: Unable to allocate array`

**Solutions:**
```python
# 1. Process in chunks
def process_large_dataset(data, chunk_size=1000):
    results = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        results.extend(process_chunk(chunk))
    return results

# 2. Use sparse data structures
import pandas as pd
df = pd.DataFrame(data).astype(pd.SparseDtype("float", 0))

# 3. Clear intermediate results
del temporary_large_array
import gc
gc.collect()
```

---

## Advanced Diagnostics

### TCO Sensitivity Analysis

```python
def tco_sensitivity_analysis():
    """Test TCO sensitivity to key parameters"""

    base_tco_vrla = 625.82
    base_tco_li = 302.81

    parameters = {
        'vrla_opex': (18, [15, 18, 21]),
        'li_opex': (6, [4, 6, 8]),
        'vrla_life': (5, [4, 5, 6]),
        'li_life': (12, [10, 12, 15]),
        'discount_rate': (0.08, [0.06, 0.08, 0.10])
    }

    for param, (base, values) in parameters.items():
        print(f"\nSensitivity to {param}:")
        for value in values:
            # Recalculate TCO with modified parameter
            tco_vrla_new = calculate_tco_with_param(param, value, 'vrla')
            tco_li_new = calculate_tco_with_param(param, value, 'li')

            advantage = tco_vrla_new - tco_li_new
            change = advantage - (base_tco_vrla - base_tco_li)

            print(f"  {param}={value}: Advantage=${advantage:.2f} (Δ${change:+.2f})")
```

### S-Curve Stability Test

```python
def test_s_curve_stability():
    """Test S-curve behavior under different conditions"""

    test_cases = [
        {"name": "No cost advantage", "tco_diff": -100},
        {"name": "Small advantage", "tco_diff": 50},
        {"name": "Large advantage", "tco_diff": 300},
        {"name": "Extreme advantage", "tco_diff": 500}
    ]

    for case in test_cases:
        k = 0.5 + 0.002 * max(0, case['tco_diff'])

        # Calculate adoption at key points
        t_values = [-10, -5, 0, 5, 10]  # Years relative to t0
        adoptions = [0.95 / (1 + np.exp(-k * t)) for t in t_values]

        print(f"\n{case['name']} (TCO diff=${case['tco_diff']}):")
        print(f"  k={k:.3f}")
        print(f"  Adoption: {[f'{a:.1%}' for a in adoptions]}")
```

### Data Pipeline Validation

```python
def validate_data_pipeline():
    """End-to-end data pipeline check"""

    stages = [
        ("Load taxonomy", load_taxonomy),
        ("Load datacenter data", load_datacenter_data),
        ("Load cost data", load_cost_data),
        ("Parse demand series", parse_demand),
        ("Extract growth rates", extract_growth),
        ("Initialize installed base", init_installed_base)
    ]

    pipeline_state = {}

    for stage_name, stage_func in stages:
        try:
            result = stage_func(pipeline_state)
            pipeline_state.update(result)
            print(f"✓ {stage_name}: Success")
        except Exception as e:
            print(f"✗ {stage_name}: Failed - {str(e)}")
            print(f"  State at failure: {list(pipeline_state.keys())}")
            break

    return pipeline_state
```

---

## Debug Mode Operations

### Enable Debug Mode

```bash
# Via command line
python3 scripts/forecast.py --region China --debug --verbose

# Via environment variable
export DATACENTER_UPS_DEBUG=1
python3 scripts/forecast.py --region China

# In code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Debug Output Interpretation

```
[DEBUG] Loading data for China
[DEBUG] Historical years: 2018-2024 (7 points)
[DEBUG] Cost forecast: Log-CAGR = -0.0823
[DEBUG] TCO calculation: VRLA=$625.82, Li-ion=$302.81
[DEBUG] Tipping point detection: Year 2027, Advantage=$292.15
[DEBUG] S-curve fitting: L=0.95, t0=2027, k=0.52
[DEBUG] Adoption 2030: 65.2%
[DEBUG] Mass balance check: Max error 0.08%
[DEBUG] Validation: All checks passed
```

### Intermediate Data Export

```python
# Export intermediate calculations for debugging
def export_debug_data(forecast):
    debug_data = {
        'cost_forecasts': forecast.cost_trajectories,
        'tco_calculations': forecast.tco_results,
        's_curve_params': forecast.s_curve_parameters,
        'adoption_curve': forecast.adoption_shares,
        'mass_balance': forecast.mass_balance_checks
    }

    with open('debug_output.json', 'w') as f:
        json.dump(debug_data, f, indent=2)

    print("Debug data exported to debug_output.json")
```

---

## Error Message Reference

### Critical Errors

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `ValueError: Invalid region` | Region not in config | Check spelling, use supported regions |
| `FileNotFoundError: config.json` | Missing configuration | Ensure config.json exists in skill root |
| `KeyError: Dataset not found` | Missing data file | Check data/ directory, run data validation |
| `ZeroDivisionError: lifespan` | Lifespan is 0 | Check config lifespans section |
| `OverflowError: exp() too large` | S-curve calculation overflow | Check k parameter bounds |

### Warning Messages

| Warning | Meaning | Action |
|---------|---------|--------|
| `No tipping point found` | Li-ion never cheaper | Extend horizon or check costs |
| `Mass balance imbalance` | Stock-flow mismatch | Review retirement calculations |
| `Non-monotonic adoption` | Share decreases | Check S-curve stability |
| `Large YoY change detected` | >50% growth/decline | Verify data, apply smoothing |
| `Extrapolation beyond 2050` | Very long forecast | Results speculative, use caution |

### Info Messages

| Info | Meaning |
|------|---------|
| `Using proxy data for Rest_of_World` | No direct data, using estimates |
| `Li-ion IB initialized at 0` | Conservative assumption |
| `Applying 3-year smoothing` | Noise reduction applied |
| `Scenario: accelerated` | Non-baseline scenario active |

---

## Quick Fixes Reference

### Common Config Adjustments

```json
{
  "quick_fixes": {
    "no_tipping": {
      "lithium_cost_decline_rate": 0.12,
      "vrla_opex_per_kwh_year": 20,
      "lithium_opex_per_kwh_year": 5
    },
    "mass_balance_issues": {
      "mass_balance_tolerance": 0.005,
      "smoothing_window": 5
    },
    "s_curve_problems": {
      "calibration_method": "heuristic",
      "ceiling_L": 0.92,
      "base_steepness_k0": 0.4
    },
    "performance": {
      "end_year": 2035,
      "validation_rules": {
        "non_negativity": true,
        "monotonic_adoption": false
      }
    }
  }
}
```

### Emergency Overrides

```python
# Force tipping point
forecast.tipping_year = 2026

# Override S-curve
forecast.results['lithium_share_pct'] = np.linspace(10, 90, len(forecast.years))

# Skip validation
forecast.config['validation_rules'] = {
    "non_negativity": False,
    "monotonic_adoption": False,
    "total_demand_tolerance": 1.0,  # 100% tolerance = no check
    "mass_balance_tolerance": 1.0
}
```

---

## Contact and Support

For issues not covered in this guide:

1. Check log files in `logs/` directory
2. Run diagnostic suite: `python3 scripts/run_diagnostics.py --full`
3. Export debug bundle: `python3 scripts/export_debug.py --include-all`
4. Contact model maintainers with debug bundle

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Maintainer**: Datacenter UPS Battery Forecasting Team