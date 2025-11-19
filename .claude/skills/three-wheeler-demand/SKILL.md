---
name: three-wheeler-demand
description: >
  Forecasts three-wheeler demand (units/year) with EV disruption analysis using tipping point detection and logistic adoption curves.
  Use when analyzing three-wheeler markets, EV three-wheeler adoption, ICE displacement, cost parity dynamics, market penetration,
  or questions like "when will EV three-wheelers dominate", "three-wheeler demand forecast", "EV adoption in China/India",
  "tipping point for three-wheelers". Handles regions: China, Europe, Rest_of_World, Global.
  Models EV-ICE competition, calculates cost parity year, fits S-curve adoption, tracks fleet evolution. (project)
---

# Three-Wheeler Demand Forecasting Skill

This skill implements cost-driven demand forecasting for three-wheeler markets, focusing on EV disruption dynamics and tipping point analysis.

## Overview

The skill forecasts three-wheeler demand across:
- **Market Segments**: Total three-wheeler market, EV three-wheelers, ICE three-wheelers
- **Regions**: China, Europe, Rest_of_World, Global (aggregated)
- **Time Horizon**: Configurable (typically 2020-2040)

**Note**: USA is excluded as the three-wheeler market is minimal in North America.

## Key Features

### Tipping Point Detection
- **Cost Comparison**: EV (Range-100km lowest cost) vs ICE (median cost)
- **3-year rolling median smoothing** on historical cost curves
- **Log-CAGR forecasting** for future cost trajectories
- **Automatic crossover detection** to identify cost parity year

### Logistic Adoption Modeling
- **Pre-tipping phase**: Linear extrapolation of historical EV share
- **Post-tipping phase**: Logistic S-curve with configurable ceiling (default: 90%)
- **Automatic parameter fitting** using differential evolution
- **Fallback heuristics** for sparse data scenarios

### Market Forecasting
- **Robust trend fitting**: Theil-Sen regression (outlier-resistant)
- **±5% CAGR constraint** on market growth
- **Non-negativity enforcement**
- **Regional then global aggregation**

### Fleet Tracking (Optional)
- **Stock-flow accounting**: Fleet(t+1) = Fleet(t) + Sales(t) - Scrappage(t)
- **10-year vehicle lifetime** for three-wheelers (commercial use)
- **Consistency validation** against historical fleet data

## Usage

### Basic Forecasting

```bash
# Single region forecast
cd .claude/skills/three-wheeler-demand
python3 scripts/forecast.py --region China --end-year 2040 --output csv

# Global forecast (all regions + aggregation)
python3 scripts/forecast.py --region Global --end-year 2040 --output both

# With fleet tracking
python3 scripts/forecast.py --region China --end-year 2040 --track-fleet --output csv
```

### Using the Shell Wrapper

```bash
# Quick run (region, end year, output format)
./run_forecast.sh China 2040 csv
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | Required | China, Europe, Rest_of_World, Global |
| `--end-year` | 2040 | Forecast horizon year |
| `--ceiling` | 0.9 | Max EV adoption share (0.0-1.0) |
| `--output` | csv | csv, json, or both |
| `--output-dir` | ./output | Output directory path |
| `--track-fleet` | False | Enable fleet evolution tracking |

## Methodology

### 1. Cost Analysis Phase

**Steps:**
1. Load historical cost data:
   - EV: `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_{Region}`
   - ICE: `Three_Wheeler_(ICE)_Median_Cost_{Region}`
2. Apply 3-year rolling median smoothing
3. Forecast costs using log-CAGR method
4. Detect tipping point (cost parity year)

**Output:** Tipping year, cost trajectories, CAGRs

### 2. Demand Forecast Phase

**Market Forecast:**
- Input: Historical total three-wheeler sales
- Method: Theil-Sen regression with ±5% CAGR cap
- Output: Total market demand projection

**EV Forecast:**
- Calculate historical EV share
- Pre-tipping: Linear share extrapolation
- Post-tipping: Fit logistic S-curve `s(t) = L / (1 + exp(-k*(t-t0)))`
  - L: ceiling (0.9 default)
  - k: growth rate (fitted)
  - t0: inflection point (anchored near tipping)
- Convert share to absolute demand: `EV_demand = share × market_demand`

**ICE Forecast:**
- Residual calculation: `ICE_demand = market_demand - EV_demand`
- Non-negativity enforcement

### 3. Validation

- **Sum consistency**: EV + ICE ≤ Market (within 1% tolerance)
- **Non-negativity**: All values ≥ 0
- **Share bounds**: EV share ∈ [0, 1]
- **Fleet consistency** (if tracking enabled)

## Output Formats

### CSV Output

Columns:
- `Year`: Forecast year
- `Market`: Total three-wheeler demand (units)
- `EV`: EV three-wheeler demand (units)
- `ICE`: ICE three-wheeler demand (units)
- `EV_Share`: EV market share (%)
- `ICE_Share`: ICE market share (%)
- `EV_Cost`: EV cost (USD per vehicle)
- `ICE_Cost`: ICE cost (USD per vehicle)
- `EV_Fleet`: EV fleet size (if `--track-fleet`)
- `ICE_Fleet`: ICE fleet size (if `--track-fleet`)
- `Total_Fleet`: Total fleet size (if `--track-fleet`)

**Example:**
```
Year,Market,EV,ICE,EV_Share,ICE_Share,EV_Cost,ICE_Cost
2020,5000000,1000000,4000000,20.0,80.0,3500,4000
...
2040,6000000,5400000,600000,90.0,10.0,2000,5000
```

### JSON Output

Includes:
- Cost analysis results (tipping point, CAGRs, cost trajectories)
- Demand forecast results (market, EV, ICE projections)
- Historical data references
- Validation status
- Parameters used

Files saved to: `output/three_wheeler_{Region}_{EndYear}.{format}`

## Scenarios

Pre-configured scenarios in `config.json`:

### Baseline (default)
- Logistic ceiling: 90%
- Market growth: 1.0x
- Description: Moderate EV adoption following cost parity dynamics

### Accelerated EV
- Logistic ceiling: 95%
- Market growth: 1.1x
- Tipping acceleration: -2 years
- Description: Rapid EV adoption with policy support

### Conservative
- Logistic ceiling: 75%
- Market growth: 0.95x
- Tipping delay: +3 years
- Description: Slower EV adoption due to infrastructure constraints

## Examples

### Example 1: China Forecast

**Command:**
```bash
python3 scripts/forecast.py --region China --end-year 2040 --output csv
```

**Process:**
1. Load China cost data → Detect tipping point (e.g., 2025)
2. Forecast market growth → 4M (2020) to 5M (2040)
3. Fit EV S-curve → 20% (2020) to 90% (2040)
4. Calculate ICE residual → 3.2M (2020) to 0.5M (2040)

**Output:** `output/three_wheeler_China_2040.csv`

### Example 2: Global Comparison

**Command:**
```bash
python3 scripts/forecast.py --region Global --end-year 2040 --output both
```

**Process:**
1. Forecast China, Europe, Rest_of_World individually
2. Aggregate sales to global totals
3. Export global CSV + regional CSVs + full JSON

**Output:**
- `output/three_wheeler_Global_2040_global.csv`
- `output/three_wheeler_China_2040.csv`
- `output/three_wheeler_Europe_2040.csv`
- `output/three_wheeler_Rest_of_World_2040.csv`
- `output/three_wheeler_Global_2040.json`

### Example 3: Fleet Evolution Analysis

**Command:**
```bash
python3 scripts/forecast.py --region China --end-year 2040 --track-fleet --output csv
```

**Additional Output:**
- EV_Fleet, ICE_Fleet, Total_Fleet columns
- Stock-flow validation with 10-year commercial vehicle lifetime

## Performance Notes

- **Code execution environment**: 5GiB RAM, 5GiB storage
- **Typical runtime**: <30 seconds per region
- **Data requirements**: Historical cost and sales data (minimum 5 years recommended)

## Common Analysis Patterns

**Pattern 1: Regional Comparison**

Input: "Compare three-wheeler EV adoption across China, India, and Europe"

Approach:
```bash
for region in China Europe Rest_of_World; do
  python3 scripts/forecast.py --region $region --end-year 2035 --output csv
done
# Then compare CSV outputs
```

**Pattern 2: Tipping Point Sensitivity**

Input: "What if China's tipping point is 3 years earlier?"

Approach:
1. Modify scenario in `config.json` with `tipping_acceleration: -3`
2. Run forecast
3. Compare against baseline

**Pattern 3: Ceiling Sensitivity**

Input: "What if EV adoption peaks at 75% instead of 90%?"

Approach:
```bash
python3 scripts/forecast.py --region China --ceiling 0.75 --output csv
python3 scripts/forecast.py --region China --ceiling 0.90 --output csv
# Compare outputs
```

**Pattern 4: Rest_of_World (India-Dominated) Analysis**

Input: "Forecast India's three-wheeler market through 2040"

Note: Rest_of_World is heavily weighted by India's large three-wheeler market
```bash
python3 scripts/forecast.py --region Rest_of_World --end-year 2040 --output csv
```

## Technical Details

- **Historical Data**: 2010-2024 (varies by metric and region)
- **Forecast Horizon**: Configurable (typically through 2040)
- **Temporal Granularity**: Annual
- **Primary Unit**: Units per year (vehicles)
- **Methodology**: Cost-driven disruption with logistic adoption
- **Confidence**: HIGH for China and Rest_of_World (India), LOW for Europe (emerging market)

## Market Context

### Three-Wheeler Characteristics
- **Primary use**: Commercial (delivery, taxi, last-mile transport)
- **Key markets**: India (Rest_of_World), China, emerging markets
- **Fleet lifetime**: 10 years (shorter due to commercial intensity)
- **TCO sensitivity**: High (commercial operators optimize for total cost)
- **EV adoption drivers**: Lower operating costs, reduced maintenance, policy incentives

### Regional Notes
- **China**: Established market, rapid EV adoption for urban delivery
- **Rest_of_World (India)**: Dominant global market, cost-sensitive, strong EV policy support
- **Europe**: Small emerging market, primarily urban delivery use cases
- **USA**: Not included (negligible three-wheeler market)

## Reference Documentation

- [reference/methodology-reference.md](reference/methodology-reference.md) - Detailed algorithms and equations
- [reference/parameters-reference.md](reference/parameters-reference.md) - Complete parameter catalog
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - Output schema specifications
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - Input data requirements

## Data Sources

Based on:
- Three-wheeler industry sales statistics (by region)
- EV three-wheeler pricing data (range-normalized)
- ICE three-wheeler pricing data (median transaction)
- Fleet registration databases (for validation)
- Commercial vehicle utilization studies

## Troubleshooting

**Issue:** "No tipping point found"
- **Cause:** ICE remains cheaper throughout forecast horizon
- **Solution:** Extend forecast horizon or check cost data

**Issue:** "Validation failed: Sum consistency violated"
- **Cause:** Numerical precision or extreme parameter values
- **Solution:** Check input data quality, adjust CAGR caps

**Issue:** "Dataset not found in taxonomy"
- **Cause:** Missing historical data for region
- **Solution:** Verify data files in `data/` directory, check taxonomy mappings

**Issue:** "USA region not available"
- **Cause:** USA market is excluded for three-wheelers
- **Solution:** Use China, Europe, Rest_of_World, or Global regions only

## Version History

- **v1.0.0** (2025-11): Initial release with tipping point detection, logistic adoption, fleet tracking
