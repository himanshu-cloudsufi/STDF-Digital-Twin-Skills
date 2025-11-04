# Troubleshooting Reference

Common errors, validation failures, debugging strategies, and solutions for demand forecasting issues.

## Contents
- Common Error Messages
- Data Issues
- Validation Failures
- Convergence Problems
- Output Issues
- Debug Checklist
- Getting Help

---

## Common Error Messages

### KeyError: Region not found

**Error:**
```
KeyError: 'Rest_of_World'
```

**Cause**: Dataset doesn't have data for requested region

**Solutions**:
1. Check available regions in data:
   ```python
   import json
   with open('data/Passenger_Cars.json') as f:
       curves = json.load(f)['Passenger Cars']
       dataset = curves['Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost']
       print("Available regions:", list(dataset['regions'].keys()))
   ```

2. Use alternate region or skip this region

3. Verify taxonomy mapping for this region:
   ```python
   with open('data/passenger_vehicles_taxonomy_and_datasets.json') as f:
       taxonomy = json.load(f)
       print(taxonomy['data']['EV_Cars']['cost'])
   ```

**Prevention**: Always check region availability before forecasting

---

### KeyError: Dataset not found

**Error:**
```
KeyError: 'Passenger_Vehicle_Annual_Sales'
```

**Cause**: Dataset name misspelled or doesn't exist in Passenger_Cars.json

**Solutions**:
1. List all available datasets:
   ```bash
   python3 -c "import json; f=open('data/Passenger_Cars.json'); print('\\n'.join(json.load(f)['Passenger Cars'].keys()))" | grep -i "sales"
   ```

2. Check exact spelling (case-sensitive, underscores, parentheses)

3. Verify taxonomy file has correct mapping:
   ```python
   with open('data/passenger_vehicles_taxonomy_and_datasets.json') as f:
       taxonomy = json.load(f)
       print(taxonomy['data']['Passenger_Vehicles'])
   ```

**Prevention**: Use DataLoader class which handles taxonomy lookups automatically

---

### ImportError: No module named 'scripts'

**Error:**
```
ImportError: No module named 'scripts.data_loader'
```

**Cause**: Running script from wrong directory or import paths incorrect

**Solutions**:
1. Run from skill root directory:
   ```bash
   cd .claude/skills/demand-forecasting
   python3 scripts/forecast.py --region China
   ```

2. If imports still fail, check `__init__.py` exists in scripts directory:
   ```bash
   touch scripts/__init__.py
   ```

3. Alternative: Use absolute imports by adding parent directory to path:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(__file__))
   from scripts.data_loader import DataLoader
   ```

**Prevention**: Always run scripts from skill root directory

---

### ValueError: Arrays have different lengths

**Error:**
```
ValueError: X and Y arrays must have same length
```

**Cause**: Data corruption or malformed dataset in JSON

**Solutions**:
1. Check data integrity:
   ```python
   import json
   with open('data/Passenger_Cars.json') as f:
       curves = json.load(f)['Passenger Cars']
       dataset = curves['<dataset_name>']['regions']['China']
       print(f"X length: {len(dataset['X'])}")
       print(f"Y length: {len(dataset['Y'])}")
   ```

2. If lengths mismatch, fix the data file manually

3. Check for null values or missing data:
   ```python
   print("X:", dataset['X'])
   print("Y:", dataset['Y'])
   ```

**Prevention**: Validate data files after manual edits

---

## Data Issues

### Insufficient Historical Data

**Symptom**: Warning message: "Insufficient data points for logistic fitting"

**Cause**: Less than 3 historical data points for BEV demand

**Solutions**:
1. **Automatic fallback**: System will use seeded logistic parameters:
   - k = 0.4
   - t₀ = tipping_year

2. **Manual intervention**: Provide more historical data or use linear extrapolation

3. **Adjust parameters**: Widen logistic bounds to allow more flexible fitting

**When this occurs**:
- New regions with sparse EV data
- Recent BEV adoption (only 1-2 years of sales)
- Historical data missing due to collection gaps

**Impact**: Forecast may be less accurate but still usable

---

### Noisy Cost Data

**Symptom**: Tipping point detection is erratic or unstable

**Cause**: Cost curves have high year-to-year volatility

**Solutions**:
1. **Increase smoothing window** in config.json:
   ```json
   "smoothing_window": 5
   ```
   (default is 3)

2. **Check raw data** for outliers:
   ```python
   import matplotlib.pyplot as plt
   plt.plot(years, costs)
   plt.title('Check for outliers')
   plt.show()
   ```

3. **Manual outlier removal**: Edit data file to remove anomalous points

**Prevention**: Always apply 3-year rolling median (default behavior)

---

### Missing Regional Data

**Symptom**: "Region X not found in dataset Y"

**Cause**: Data file incomplete for some regions

**Solutions**:
1. **Skip region**: Don't forecast unavailable regions

2. **Use proxy data**: Copy data from similar region as approximation

3. **Aggregate approach**: Use Global data divided by region weights

**Common missing combinations**:
- Rest_of_World cost data (often needs to be derived)
- Some autonomous vehicle metrics don't have all regions

**Workaround**: Focus analysis on China, USA, Europe where data is complete

---

## Validation Failures

### Sum Consistency Violation

**Symptom**: "Validation warning: BEV + PHEV + ICE > Market"

**Cause**: Numerical rounding or aggressive logistic fitting causes overshoot

**Impact**: Usually minor (< 0.1% error)

**Solutions**:
1. **Accept minor violations**: If max_sum_error < 0.01 (1%), ignore

2. **Proportional adjustment**: Scale BEV, PHEV, ICE down to match market:
   ```python
   total = bev + phev + ice
   if total > market:
       scale = market / total
       bev *= scale
       phev *= scale
       ice *= scale
   ```

3. **Lower logistic ceiling**: Reduce L from 1.0 to 0.95 to prevent overshoot

**When this matters**:
- Large errors (> 5%): Indicates serious fitting problem
- Presenting to stakeholders: Fix for credibility
- Further modeling: Ensure conservation of demand

---

### Negative ICE Demand

**Symptom**: ICE forecast goes negative after tipping point

**Cause**: BEV + PHEV exceed market due to aggressive growth

**Solutions**:
1. **Automatic clamping**: ICE = max(Market − BEV − PHEV, 0)
   (already implemented in code)

2. **Lower ceiling**: Reduce logistic_ceiling to leave room for ICE:
   ```bash
   --ceiling 0.9
   ```

3. **Adjust PHEV peak**: Lower phev_peak_share in config.json

**Root cause**: Usually indicates market forecast is too conservative or EV growth too aggressive

**Validation**: Check that this only occurs late in forecast (near end_year)

---

### Unrealistic Growth Rates

**Symptom**: BEV goes from 5% to 95% in 2 years

**Cause**: Logistic k parameter too high (explosive growth)

**Solutions**:
1. **Tighten k bounds** in config.json:
   ```json
   "logistic_k_bounds": [0.1, 0.8]
   ```
   (default is [0.05, 1.5])

2. **Check data quality**: Ensure historical shares are correct

3. **Extend forecast horizon**: Longer horizons allow more gradual growth

**Realistic k values**:
- k = 0.2-0.4: Normal technology adoption (10-20 years from 10% to 90%)
- k = 0.5-0.8: Rapid adoption (5-10 years)
- k > 1.0: Explosive adoption (< 5 years) - usually unrealistic

**When explosive growth is valid**:
- Strong policy mandates (e.g., ICE ban)
- Major cost breakthrough
- Infrastructure suddenly available

---

## Convergence Problems

### Logistic Fitting Fails to Converge

**Symptom**: "Warning: Logistic optimization did not converge"

**Cause**: Data doesn't follow logistic pattern or optimizer stuck

**Solutions**:
1. **Automatic fallback**: System uses seeded parameters or linear trend

2. **Check data pattern**: Plot historical shares to see if logistic makes sense:
   ```python
   shares = bev_demand / market_demand
   plt.plot(years, shares, 'o-')
   plt.title('Does this look S-shaped?')
   plt.show()
   ```

3. **Seed optimizer**: Provide initial guess based on data inspection

4. **Use different method**: Switch to linear extrapolation if logistic doesn't fit

**When logistic is inappropriate**:
- Linear growth pattern (not S-curve)
- Multiple inflection points (non-monotonic)
- Very sparse or noisy data

**Impact**: Fallback methods usually provide reasonable forecast

---

### Differential Evolution Timeout

**Symptom**: Optimization takes > 30 seconds

**Cause**: Large parameter space, many data points, or difficult optimization landscape

**Solutions**:
1. **Reduce max iterations**: Modify differential_evolution call:
   ```python
   differential_evolution(func, bounds, maxiter=500)  # default 1000
   ```

2. **Simplify problem**: Reduce data points used for fitting

3. **Better initial guess**: Seed with approximate parameters

**Prevention**: Use default parameters; this rarely occurs

---

## Output Issues

### Empty Output Files

**Symptom**: CSV or JSON file is created but has no data

**Cause**: Forecast failed silently or export function crashed

**Solutions**:
1. **Check console output**: Look for error messages during forecast

2. **Run with verbose logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Test export manually**:
   ```python
   from scripts.forecast import ForecastOrchestrator
   orchestrator = ForecastOrchestrator()
   result = orchestrator.forecast_region("China")
   print(result)  # Check if result has data
   ```

**Prevention**: Always check console for "✓ Exported to:" confirmation

---

### JSON Serialization Error

**Symptom**: "Object of type ndarray is not JSON serializable"

**Cause**: Numpy arrays not converted to lists before JSON export

**Solutions**:
1. **Should not occur**: Export function has convert_numpy helper

2. **If it does occur**, manually convert:
   ```python
   import json
   import numpy as np

   result_converted = {
       k: v.tolist() if isinstance(v, np.ndarray) else v
       for k, v in result.items()
   }
   with open('output.json', 'w') as f:
       json.dump(result_converted, f)
   ```

**Prevention**: Use provided export functions (export_to_json)

---

### CSV Encoding Issues

**Symptom**: Special characters garbled in CSV

**Cause**: Encoding mismatch (UTF-8 vs ASCII)

**Solutions**:
1. **Specify encoding** when reading:
   ```python
   df = pd.read_csv('output.csv', encoding='utf-8')
   ```

2. **Export with encoding**:
   ```python
   df.to_csv('output.csv', encoding='utf-8', index=False)
   ```

**Prevention**: Use UTF-8 encoding consistently

---

## Debug Checklist

When forecast fails or produces unexpected results, work through this checklist:

### Step 1: Verify Inputs
- [ ] Region name is correct and available in data
- [ ] End year is reasonable (2025-2100)
- [ ] Ceiling parameter is valid (0.5-1.0)
- [ ] Output directory is writable

### Step 2: Check Data Loading
- [ ] Data files exist in data/ directory
- [ ] Passenger_Cars.json is valid JSON (not corrupted)
- [ ] Taxonomy file is valid JSON
- [ ] Required datasets exist for this region

### Step 3: Validate Data Quality
- [ ] Cost curves have > 3 data points
- [ ] Demand curves have > 3 data points
- [ ] No null values in X or Y arrays
- [ ] X and Y arrays have same length
- [ ] Years are sorted chronologically

### Step 4: Review Cost Analysis
- [ ] EV and ICE costs loaded successfully
- [ ] Smoothing applied correctly (3-year window)
- [ ] Tipping point detected (or None if ICE always cheaper)
- [ ] CAGRs are reasonable (not extreme)

### Step 5: Review Demand Forecast
- [ ] Market forecast is positive and reasonable
- [ ] BEV shares are in [0, 1]
- [ ] Logistic fitting converged (or fallback used)
- [ ] PHEV trajectory is smooth
- [ ] ICE residual is non-negative

### Step 6: Validate Outputs
- [ ] BEV + PHEV + ICE ≈ Market (within tolerance)
- [ ] All values are non-negative
- [ ] No unrealistic jumps in forecast
- [ ] Transitions near tipping point are smooth

### Step 7: Check Exports
- [ ] Output files created successfully
- [ ] CSV columns are correct (8 for regional, 6 for global)
- [ ] JSON structure is valid
- [ ] File sizes are reasonable (not empty or corrupt)

---

## Quick Diagnostics

### Test Data Loading

```bash
cd .claude/skills/demand-forecasting
python3 -c "
from scripts.data_loader import DataLoader
loader = DataLoader()
try:
    data = loader.load_cost_data('EV_Cars', 'China')
    print(f'✓ Data loaded: {len(data[\"X\"])} points')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

### Test Cost Analysis

```bash
python3 -c "
from scripts.data_loader import DataLoader
from scripts.cost_analysis import run_cost_analysis
loader = DataLoader()
result = run_cost_analysis(loader, 'China', end_year=2040)
print(f'Tipping point: {result[\"tipping_point\"]}')
print(f'EV CAGR: {result[\"ev_cagr\"]:.2%}')
print(f'ICE CAGR: {result[\"ice_cagr\"]:.2%}')
"
```

### Test Demand Forecast

```bash
python3 -c "
from scripts.data_loader import DataLoader
from scripts.cost_analysis import run_cost_analysis
from scripts.demand_forecast import run_demand_forecast
loader = DataLoader()
cost_result = run_cost_analysis(loader, 'China', end_year=2040)
demand_result = run_demand_forecast(loader, 'China', cost_result['tipping_point'], end_year=2040)
print(f'Validation: {demand_result[\"validation\"][\"is_valid\"]}')
print(f'Message: {demand_result[\"validation\"][\"message\"]}')
"
```

---

## Getting Help

### Information to Gather

When seeking help, provide:

1. **Command used**:
   ```bash
   python3 scripts/forecast.py --region China --end-year 2040 --ceiling 0.9
   ```

2. **Full error message**:
   ```
   Copy complete traceback from terminal
   ```

3. **Python version**:
   ```bash
   python3 --version
   ```

4. **Package versions**:
   ```bash
   pip list | grep -E "numpy|scipy|pandas"
   ```

5. **Data file status**:
   ```bash
   ls -lh data/
   md5sum data/Passenger_Cars.json
   ```

6. **Recent changes**: What was modified before error occurred?

### Common Solutions Summary

| Problem | Quick Fix |
|---------|-----------|
| Module not found | Run from skill root directory |
| Region not found | Check data file has this region |
| Convergence failure | Use fallback (automatic) or adjust k bounds |
| Validation error | Check if error < 1%, adjust ceiling if needed |
| Negative ICE | Reduce ceiling or PHEV peak share |
| Unrealistic growth | Tighten logistic k bounds |
| Empty output | Check console for errors, verify result object |

---

## Summary

**Key troubleshooting steps**:
1. Verify inputs and data availability
2. Check data quality (lengths, ranges, no nulls)
3. Review cost analysis results (tipping point, CAGRs)
4. Validate demand forecasts (sum consistency, non-negative)
5. Inspect outputs for expected structure and values

**Most common issues**:
- Running from wrong directory (ImportError)
- Missing regional data (KeyError)
- Validation warnings (usually ignorable if < 1%)
- Logistic convergence (automatic fallback handles this)

**When in doubt**:
- Use debug checklist systematically
- Run quick diagnostics to isolate problem
- Check that fallback mechanisms activated correctly
