---
name: demand-forecasting
description: Performs cost-driven demand forecasting for passenger vehicles (EV, PHEV, ICE) across global regions. Calculates cost parity tipping points and models market adoption using logistic growth curves. Use when user asks about passenger vehicle demand, EV adoption, electric vehicle forecasts, market penetration, sales projections, or questions like "when will EVs dominate", "what is EV adoption in China", "forecast passenger vehicle demand", "when does cost parity occur", "EV market share by 2040", "predict ICE decline", "PHEV adoption trajectory". Handles regions: China, USA, Europe, Rest_of_World, Global. Use when forecasting vehicle demand by region through 2040, analyzing technology transformation, or evaluating EV adoption scenarios. Trigger keywords: forecast, predict, demand, adoption, penetration, market share, EV, electric vehicle, passenger vehicle, BEV, PHEV, ICE, tipping point, cost parity, China, USA, Europe, 2040.
---

# Cost-Driven Demand Forecasting

## When to Use This Skill

Use this skill to forecast passenger vehicle demand (EV, PHEV, ICE) when:
- Analyzing regional or global EV adoption scenarios
- Calculating when EVs achieve cost parity with ICE vehicles
- Generating demand forecasts through 2040 (or custom horizon)
- Evaluating technology transition dynamics
- Supporting policy or investment decisions

## Workflow

Follow this workflow systematically for each forecast request.

### Prerequisites Checklist

Before starting, verify:
- [ ] User has specified region or needs help selecting one
- [ ] Forecast horizon is clear (default: 2040)
- [ ] Any custom parameters are understood (ceiling, output format)

### Step 1: Parameter Collection

Ask the user for these parameters:

**Required:**
- **Region**: China, USA, Europe, Rest_of_World, or Global

**Optional (use defaults if not specified):**
- **End Year**: Forecast horizon (default: 2040)
- **Logistic Ceiling**: Maximum EV adoption share 0.0-1.0 (default: 1.0)
- **Output Format**: csv, json, or both (default: csv)

See [reference/parameters-reference.md](reference/parameters-reference.md) for detailed parameter descriptions.

### Step 2: Load and Validate Data

Load datasets from skill's data directory:

```bash
python3 scripts/forecast.py --region {REGION} --end-year {END_YEAR} --ceiling {CEILING} --output {FORMAT}
```

**Data sources** (automatically loaded by script):
- `data/Passenger_Cars.json` - Cost and demand curves
- `data/passenger_vehicles_taxonomy_and_datasets.json` - Dataset mappings

**Validation checkpoint:**
- [ ] Data loaded successfully for specified region
- [ ] Cost curves have sufficient historical points (>3)
- [ ] Demand curves have sufficient historical points (>3)

If data issues occur, see [reference/troubleshooting-reference.md](reference/troubleshooting-reference.md).

### Step 3: Run Cost Analysis

The script performs cost curve forecasting and tipping point detection:

**What happens:**
1. Loads EV and ICE cost curves for region
2. Applies 3-year rolling median smoothing
3. Forecasts costs to end_year using log-CAGR method
4. Detects tipping point (first year EV cost < ICE cost)

**Validation checkpoint:**
- [ ] Cost curves loaded and smoothed
- [ ] Tipping point identified (or None if ICE always cheaper)
- [ ] CAGRs are reasonable (EV declining faster than ICE)

**Expected console output:**
```
[1/2] Running cost analysis...
  ✓ Tipping point: 2024
  ✓ EV CAGR: -8.50%
  ✓ ICE CAGR: -1.20%
```

See [reference/methodology-reference.md#step-1-tipping-point-detection](reference/methodology-reference.md) for algorithm details.

### Step 4: Run Demand Forecast

The script generates market, BEV, PHEV, and ICE forecasts:

**What happens:**
1. Forecasts total market demand using linear extrapolation
2. Fits logistic curve to BEV adoption post-tipping
3. Models PHEV "hump" trajectory (rise then decay)
4. Calculates ICE as residual (Market − BEV − PHEV)
5. Validates consistency (BEV + PHEV + ICE ≤ Market)

**Validation checkpoint:**
- [ ] Market forecast is positive and reasonable
- [ ] BEV forecast follows logistic S-curve
- [ ] PHEV trajectory is smooth
- [ ] ICE residual is non-negative
- [ ] Sum consistency validated (within tolerance)

**Expected console output:**
```
[2/2] Running demand forecast...
  ✓ Validation passed

  Forecast for 2040:
    Market:  28,000,000
    BEV:     24,500,000 (87.5%)
    PHEV:       500,000 (1.8%)
    ICE:      3,000,000 (10.7%)
    EV:      25,000,000 (89.3%)
```

See [reference/methodology-reference.md#step-3-bev-demand-forecasting](reference/methodology-reference.md) for algorithm details.

### Step 5: Export Results

The script exports forecast in requested format:

**CSV output** (regional):
- Columns: Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost
- Saved to: `output/{Region}_{EndYear}.csv`

**JSON output** (regional):
- Includes: Cost analysis, demand forecast, tipping point, CAGRs, validation status
- Saved to: `output/{Region}_{EndYear}.json`

**Global output**:
- Runs all 4 regions automatically
- Aggregates to global totals
- Exports 5 CSVs (if csv) or 1 JSON (if json)

**Validation checkpoint:**
- [ ] Output files created successfully
- [ ] File paths displayed in console
- [ ] No error messages during export

See [reference/output-formats-reference.md](reference/output-formats-reference.md) for complete format specifications.

### Step 6: Interpret and Report Results

Present key findings to the user:

**For single region:**
- Tipping point year (when EVs achieve cost parity)
- Final year forecast breakdown (Market, BEV, PHEV, ICE percentages)
- Growth dynamics (CAGRs, logistic parameters)
- Validation status
- Output file paths

**For Global:**
- Individual regional tipping points
- Regional final year breakdowns
- Global aggregated totals
- Comparison across regions
- Output file paths

**Example summary:**
```
Forecast Complete: China 2040

Tipping Point: 2024 (EV cost parity achieved)
Cost Dynamics:
  - EV costs declining at 8.5% per year
  - ICE costs declining at 1.2% per year

2040 Forecast:
  - Total Market: 28.0M vehicles
  - BEV: 24.5M (87.5%)
  - PHEV: 0.5M (1.8%)
  - ICE: 3.0M (10.7%)

Validation: ✓ Passed (all checks)

Outputs:
  - CSV: output/China_2040.csv
  - JSON: output/China_2040.json
```

## Error Handling

If issues occur at any step:

1. **Check error message** in console output
2. **Consult troubleshooting guide**: [reference/troubleshooting-reference.md](reference/troubleshooting-reference.md)
3. **Common issues**:
   - Missing regional data → Check data availability
   - Convergence failure → Automatic fallback to seeded parameters
   - Validation warnings → Usually acceptable if error < 1%
   - Import errors → Ensure running from skill root directory

## Special Case: Global Forecast

When region = "Global", the workflow automatically:
1. Runs forecast for China, USA, Europe, Rest_of_World sequentially
2. Reports individual regional results
3. Aggregates demand to global totals
4. Exports both regional and global files

**Note**: Global forecasts take ~4x longer than single region.

## Notes and Best Practices

**Regional independence:**
- Each region is analyzed separately with its own cost curves and tipping point
- Global is aggregated afterward (not forecasted independently)

**Data consistency:**
- All costs are in real USD (inflation-adjusted)
- Demand is annual sales (not cumulative)
- Years are calendar years (not model years)

**Parameter guidance:**
- Use default ceiling (1.0) unless infrastructure constraints exist
- Use ceiling 0.85-0.9 for regions with known adoption limits
- Default end_year (2040) is standard policy horizon
- Extend to 2050+ for longer-term scenarios

**Validation:**
- Minor sum errors (< 1%) are acceptable due to rounding
- Negative ICE late in forecast is expected (clamped to zero)
- Logistic convergence failures trigger automatic fallbacks

## Reference Files

**Detailed algorithm documentation:**
- [reference/methodology-reference.md](reference/methodology-reference.md) - Complete forecasting methodology

**Parameter descriptions:**
- [reference/parameters-reference.md](reference/parameters-reference.md) - All parameters with ranges and guidance

**Data documentation:**
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - JSON structure and dataset naming

**Output specifications:**
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - CSV and JSON format details

**Problem solving:**
- [reference/troubleshooting-reference.md](reference/troubleshooting-reference.md) - Common errors and solutions

## Quick Start Examples

**Example 1: Simple regional forecast**
```bash
python3 scripts/forecast.py --region China --output csv
```

**Example 2: Custom ceiling scenario**
```bash
python3 scripts/forecast.py --region Europe --end-year 2050 --ceiling 0.9 --output both
```

**Example 3: Global analysis**
```bash
python3 scripts/forecast.py --region Global --output json
```

## Implementation Details

**Script location**: `scripts/forecast.py`

**Data location**: `data/` directory (relative to skill root)

**Output location**: `./output` (default) or custom via `--output-dir`

**Python modules** (in `scripts/`):
- `forecast.py` - Main orchestration (use this)
- `data_loader.py` - Data loading utilities
- `cost_analysis.py` - Cost curve analysis and tipping point detection
- `demand_forecast.py` - Demand forecasting logic
- `utils.py` - Helper functions

**Configuration**: `config.json` contains default parameters (advanced users only)

## Dependencies

Required Python packages (in `requirements.txt`):
- numpy >= 1.20.0
- scipy >= 1.7.0
- pandas >= 1.3.0
- matplotlib >= 3.4.0 (for visualization)

Install via:
```bash
pip install -r requirements.txt
```
