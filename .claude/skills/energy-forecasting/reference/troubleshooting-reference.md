# Troubleshooting Reference - Energy Forecasting (SWB)

## Common Errors and Solutions

### 1. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'numpy'
```

**Solution:**
Install dependencies:
```bash
cd .claude/skills/energy-forecasting
pip install -r requirements.txt
```

Or use python3 explicitly:
```bash
python3 -m pip install -r requirements.txt
```

### 2. Data Loading Errors

**Error:**
```
ValueError: Dataset Solar_LCOE_Utility not found in curves data
```

**Solution:**
- Check that data files exist in `data/` directory
- Verify dataset name in taxonomy file matches entity file
- Check regional data availability (some regions may lack data)

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/swb_taxonomy_and_datasets.json'
```

**Solution:**
```bash
# Verify data files are copied
ls .claude/skills/energy-forecasting/data/

# Should show:
# Energy_Generation.json
# Energy_Storage.json
# Electricity.json
# swb_taxonomy_and_datasets.json
```

### 3. Tipping Point Not Found

**Warning:**
```
Tipping vs Coal: Not found
Tipping vs Gas: Not found
```

**Meaning:**
- SWB stack cost does not cross below coal/gas LCOE by end_year
- Increase `--end-year` to extend forecast horizon
- Check if cost data is available for region

**Note:** This is not an error - it indicates disruption has not occurred yet.

### 4. Energy Balance Validation Fails

**Error:**
```
Energy balance violated by up to 5.2%
```

**Causes:**
- Missing non-SWB baseline data (nuclear, hydro)
- Inaccurate electricity demand data
- Data inconsistencies across entity files

**Solutions:**
- Increase tolerance in config.json: `"energy_balance_tolerance": 0.10` (10%)
- Check data quality for the region
- Verify total electricity demand aligns with sum of generation sources

### 5. Negative Generation Values

**Error:**
```
Coal generation has negative values
```

**Cause:**
- SWB generation exceeds total demand (data inconsistency)
- Reserve floors too aggressive

**Solution:**
- Check electricity demand data is reasonable
- Reduce reserve floors in config.json
- Verify SWB capacity forecasts aren't over-extrapolating

### 6. Missing Capacity Factor Data

**Warning:**
```
Warning: Could not load Solar CF for Rest_of_World
```

**Meaning:**
- CF data not available in datasets for this region
- Fallback to default CF will be used (0.15 for solar)

**Action:** No action needed - this is expected behavior. Default CFs are reasonable.

### 7. CSP Not Included

**Observation:**
CSP not appearing in capacity forecasts despite having data.

**Reason:**
CSP capacity < 1% of Solar PV capacity (below threshold).

**To include CSP:**
- Lower threshold in config.json: `"csp_threshold": 0.001` (0.1%)
- Or manually add CSP to forecasts

### 8. Global Aggregation Issues

**Error:**
```
KeyError: 'generation_forecasts'
```

**Cause:**
- Regional forecast failed, so Global aggregation incomplete
- Check individual regional forecasts first

**Solution:**
```bash
# Test each region individually first
./run_forecast.sh --region China --output csv
./run_forecast.sh --region USA --output csv
./run_forecast.sh --region Europe --output csv
./run_forecast.sh --region Rest_of_World --output csv

# Then try Global
./run_forecast.sh --region Global --output csv
```

### 9. Unrealistic Growth Rates

**Warning:**
```
YoY growth rate capped at 50%
```

**Meaning:**
- Historical growth > 50% per year detected
- Growth rate capped to prevent exponential explosion

**Action:**
- This is expected behavior (cap prevents unrealistic forecasts)
- If needed, increase cap in config.json: `"max_yoy_growth": 1.0` (100%)

### 10. Battery SCOE Calculation Errors

**Error:**
```
SCOE = nan (not a number)
```

**Cause:**
- Battery cost data missing or zero
- Invalid battery parameters (cycles = 0, RTE = 0, etc.)

**Solution:**
- Check battery cost data exists in Energy_Storage.json
- Verify battery parameters in config.json are non-zero
- Use fallback SCOE estimate if data unavailable

## Debugging Tips

### 1. Run with Verbose Output

Add print statements to see intermediate values:
```python
# In forecast.py
print(f"DEBUG: SWB generation = {total_swb_generation}")
print(f"DEBUG: Coal generation = {coal_generation}")
```

### 2. Test Individual Modules

Test data loader:
```bash
cd .claude/skills/energy-forecasting/scripts
python3 data_loader.py
```

Test utilities:
```bash
python3 utils.py
```

### 3. Check Data Files

Verify JSON structure:
```bash
python3 -m json.tool data/Energy_Generation.json | head -50
```

### 4. Validate Config

Check config.json is valid JSON:
```bash
python3 -m json.tool config.json
```

### 5. Inspect Outputs

Check output files:
```bash
cat output/China_2040.csv | head -20
python3 -m json.tool output/China_2040.json | head -50
```

## Data Quality Checks

Before running forecasts:

**✓ Verify data files exist:**
```bash
ls -lh data/*.json
```

**✓ Check taxonomy structure:**
```bash
python3 -c "import json; print(json.load(open('data/swb_taxonomy_and_datasets.json'))['products'].keys())"
```

**✓ Test data loading:**
```bash
python3 scripts/data_loader.py
```

## Performance Issues

### Slow Forecasts

**Cause:** Large forecast horizons (e.g., 2100) with many technologies.

**Solutions:**
- Reduce `--end-year` to 2030  or 2035
- Remove CSP if not needed (set threshold to 1.0)
- Run regional forecasts in parallel instead of Global

### Memory Issues

**Error:**
```
MemoryError: Unable to allocate array
```

**Solution:**
- Reduce forecast horizon
- Process regions one at a time instead of Global aggregation
- Use smaller smoothing window (reduce to 2)

## Getting Help

If issues persist:

1. **Check data schema**: Verify taxonomy and entity files match expected structure
2. **Validate inputs**: Ensure region names and parameters are valid
3. **Review methodology**: See reference/methodology-reference.md for logic
4. **Inspect outputs**: Check intermediate results in JSON output
5. **Simplify**: Test with single technology first (e.g., just Solar)

## Known Limitations

- **No offshore wind data** for some regions → Uses onshore only
- **No CSP data** for most regions → Excluded unless threshold met
- **Limited historical CF data** → Relies on defaults
- **Non-SWB baseline rough estimate** → Assumes 15% of total
- **Reserve floors simplified** → Does not model peaker plants explicitly
