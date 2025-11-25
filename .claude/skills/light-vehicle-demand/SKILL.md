---
name: light-vehicle-demand
description: >
  Unified forecasting for two-wheeler and three-wheeler demand (units/year) with EV disruption analysis.
  Uses tipping point detection and logistic adoption curves. Supports both vehicle types with vehicle-specific
  parameters (fleet lifetime, regional coverage, cost trajectories). Use when analyzing light vehicle markets,
  EV adoption, ICE displacement, or questions like "when will EVs dominate", "forecast demand",
  "EV adoption trends". Handles regions based on vehicle type. (project)
---

> ⚠️ **MANDATORY SCRIPT EXECUTION REQUIREMENT**
>
> This skill REQUIRES executing `scripts/forecast.py` using Bash tool.
>
> **REQUIRED:** `cd .claude/skills/light-vehicle-demand && python3 scripts/forecast.py --vehicle-type X --region Y --end-year Z`
>
> **PROHIBITED:** Mental calculation, self-generated forecasts, methodology replication
>
> The methodology below describes what THE SCRIPT does. Your job: RUN THE SCRIPT, not replicate its logic.
> Understanding the methodology ≠ Running the code. Reading this file ≠ Executing the analysis.
>
> **🔴 HISTORICAL DATA:** Do NOT generate historical values (2W/3W sales, costs, fleet) from memory. The script loads actual data from `Two_Wheeler.json` / `Three_Wheeler.json`. Only script output contains verified historical data.

# Light Vehicle Demand Forecasting Skill

Unified skill for forecasting two-wheeler and three-wheeler demand with cost-driven EV disruption analysis.

## Table of Contents
- [Available Datasets](#available-datasets)
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Command-Line Parameters](#command-line-parameters)
- [Architecture](#architecture)
- [Methodology](#methodology)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Common Use Cases](#common-use-cases)
- [Taxonomy and Dataset Mapping](#taxonomy-and-dataset-mapping)
- [Related Skills](#related-skills)

## Available Datasets

**CRITICAL FOR PLANNING:** Datasets vary by vehicle type. Always check vehicle-specific availability:

### Two-Wheeler Datasets (includes USA)
- **Market:** `Two_Wheeler_Annual_Sales_{Region}`
- **EV Cost:** `EV_2_Wheeler_(Range-100_KM)_Lowest_Cost_{Region}` (key for tipping point)
- **ICE Cost:** `Two_Wheeler_(ICE)_Median_Cost_{Region}` (key for tipping point)
- **EV Demand:** `Two_Wheeler_(EV)_Annual_Sales_{Region}`
- **ICE Demand:** `Two_Wheeler_(ICE)_Annual_Sales_{Region}`
- **EV Fleet:** `Two_Wheeler_(EV)_Total_Fleet_{Region}` (NOT available for China)
- **ICE Fleet:** `Two_Wheeler_(ICE)_Total_Fleet_{Region}`
- **Fleet Lifetime:** 11 years
- **Regions:** China, USA, Europe, Rest_of_World, Global

### Three-Wheeler Datasets (NO USA)
- **Market:** `Annual_Sales_{Region}`
- **EV Cost:** `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_{Region}` (key for tipping point)
- **ICE Cost:** `(ICE)_Median_Cost_{Region}` (key for tipping point)
- **EV Demand:** `(EV)_Annual_Sales_{Region}`
- **ICE Demand:** `(ICE)_Annual_Sales_{Region}`
- **EV Fleet:** `(EV)_Total_Fleet_{Region}`
- **ICE Fleet:** `(ICE)_Total_Fleet_{Region}`
- **Lead Impact:** `Lead_Annual_Implied_Demand-Sales_3_wheelers`, `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers` (Global)
- **Fleet Lifetime:** 10 years (commercial use)
- **Regions:** China, Europe, Rest_of_World, Global (NO USA)

### Dataset Files Location
- `data/two_wheeler/Two_Wheeler.json` - Two-wheeler sales, cost, fleet data
- `data/three_wheeler/Three_Wheeler.json` - Three-wheeler sales, cost, fleet data
- `data/two_wheeler/two_wheeler_taxonomy_and_datasets.json` - Two-wheeler taxonomy
- `data/three_wheeler/three_wheeler_taxonomy_and_datasets.json` - Three-wheeler taxonomy

### Configuration Files
- `configs/two_wheeler_config.json` - Two-wheeler specific parameters
- `configs/three_wheeler_config.json` - Three-wheeler specific parameters

### Critical Notes for Planning
1. **USA region:** Only available for two-wheelers
2. **EV fleet (China):** NOT available for two-wheelers, available for three-wheelers
3. **Fleet lifetimes:** Different by vehicle type (11y vs 10y)
4. **Use Case:** Two-wheelers = personal/commuter, Three-wheelers = commercial/delivery

## Overview

This skill provides a single, unified framework for forecasting light vehicle markets:

### Supported Vehicle Types
- **Two-Wheelers**: 11-year fleet lifetime, includes USA region
- **Three-Wheelers**: 10-year fleet lifetime, excludes USA region (minimal market)

### Key Features
- **Cost-driven tipping point detection** (EV vs ICE cost parity)
- **Logistic S-curve adoption modeling** with configurable ceiling
- **Robust market forecasting** with CAGR constraints
- **Optional fleet tracking** with vehicle-specific lifetimes
- **Regional and global aggregation**

## Quick Start

### Basic Usage

```bash
cd .claude/skills/light-vehicle-demand

# Two-wheeler forecast for China
python3 scripts/forecast.py --vehicle-type two_wheeler --region China --end-year 2030

# Three-wheeler forecast for Rest_of_World
python3 scripts/forecast.py --vehicle-type three_wheeler --region Rest_of_World --end-year 2030

# Global forecast (all regions)
python3 scripts/forecast.py --vehicle-type two_wheeler --region Global --end-year 2030
```

### Using Shell Wrapper

```bash
# Format: ./run_forecast.sh <vehicle_type> <region> <end_year> [output_format]
./run_forecast.sh two_wheeler China 2030 csv
./run_forecast.sh three_wheeler Europe 2035 both
```

## Command-Line Parameters

| Parameter | Required | Options | Description |
|-----------|----------|---------|-------------|
| `--vehicle-type` | Yes | two_wheeler, three_wheeler | Vehicle type to forecast |
| `--region` | Yes | See below | Region name or "Global" |
| `--end-year` | No (default: 2030) | Year | Forecast horizon |
| `--ceiling` | No (default: 0.9) | 0.0-1.0 | Max EV adoption share |
| `--output` | No (default: csv) | csv, json, both | Output format |
| `--output-dir` | No (auto) | Path | Output directory |
| `--track-fleet` | No (flag) | - | Enable fleet tracking |

### Supported Regions by Vehicle Type

**Two-Wheeler:**
- China, USA, Europe, Rest_of_World, Global

**Three-Wheeler:**
- China, Europe, Rest_of_World, Global (NO USA)

## Architecture

### Directory Structure

```
light-vehicle-demand/
├── scripts/
│   ├── forecast.py              # Main entry point
│   ├── vehicle_config.py        # Vehicle-specific configuration
│   └── common/                  # Shared modules
│       ├── utils.py             # Utility functions
│       ├── cost_analysis.py     # Cost forecasting & tipping points
│       ├── data_loader.py       # Data loading
│       └── demand_forecast.py   # Demand forecasting
├── configs/
│   ├── two_wheeler_config.json
│   └── three_wheeler_config.json
├── data/
│   ├── two_wheeler/
│   └── three_wheeler/
└── output/
    ├── two_wheeler/
    └── three_wheeler/
```

### Key Differences Between Vehicle Types

| Feature | Two-Wheeler | Three-Wheeler |
|---------|-------------|---------------|
| Fleet Lifetime | 11 years | 10 years (commercial use) |
| USA Region | Included | Excluded |
| Market Product | Two_Wheelers | Three_Wheelers |
| EV Product | EV_2_Wheelers | EV_3_Wheelers |
| ICE Product | ICE_2_Wheelers | ICE_3_Wheelers |

## Methodology

### 1. Cost Analysis
- Load historical EV and ICE cost curves
- Apply 3-year rolling median smoothing
- Forecast costs using log-CAGR method
- Detect cost parity year (tipping point)

### 2. Demand Forecasting

**Market Forecast:**
- Theil-Sen regression (outlier-resistant)
- ±5% CAGR constraint
- Non-negativity enforcement

**EV Forecast:**
- Pre-tipping: Linear share extrapolation
- Post-tipping: Logistic S-curve `s(t) = L / (1 + exp(-k*(t-t0)))`
  - L: ceiling parameter
  - k: growth rate (fitted)
  - t0: inflection point

**ICE Forecast:**
- Residual calculation: `ICE = Market - EV`

### 3. Fleet Tracking (Optional)
- Stock-flow accounting: `Fleet(t+1) = Fleet(t) + Sales(t) - Scrappage(t)`
- Vehicle-specific lifetimes (11 years for two-wheelers, 10 for three-wheelers)

## Output Formats

### CSV Output

Columns:
- Year, Market, EV, ICE
- EV_Share, ICE_Share (%)
- EV_Cost, ICE_Cost (USD)
- EV_Fleet, ICE_Fleet, Total_Fleet (if `--track-fleet`)

**Example:**
```
Year,Market,EV,ICE,EV_Share,ICE_Share,EV_Cost,ICE_Cost
2025,25000000,10000000,15000000,40.0,60.0,1100,1450
2040,30000000,27000000,3000000,90.0,10.0,800,1800
```

### JSON Output

Includes:
- Cost analysis (tipping point, CAGRs, trajectories)
- Demand forecasts (market, EV, ICE)
- Historical data references
- Validation status
- Parameters used

## Examples

### Example 1: Two-Wheeler Forecast with Fleet Tracking

```bash
python3 scripts/forecast.py \
  --vehicle-type two_wheeler \
  --region China \
  --end-year 2030 \
  --track-fleet \
  --output both
```

**Output:**
- `output/two_wheeler/two_wheeler_China_2030.csv`
- `output/two_wheeler/two_wheeler_China_2030.json`

### Example 2: Three-Wheeler Global Forecast

```bash
python3 scripts/forecast.py \
  --vehicle-type three_wheeler \
  --region Global \
  --end-year 2035 \
  --ceiling 0.85 \
  --output csv
```

**Output:**
- `output/three_wheeler/three_wheeler_China_2035.csv`
- `output/three_wheeler/three_wheeler_Europe_2035.csv`
- `output/three_wheeler/three_wheeler_Rest_of_World_2035.csv`
- `output/three_wheeler/three_wheeler_Global_2035_global.csv`

### Example 3: Conservative EV Adoption Scenario

```bash
python3 scripts/forecast.py \
  --vehicle-type two_wheeler \
  --region USA \
  --end-year 2030 \
  --ceiling 0.75 \
  --output csv
```

## Common Use Cases

### Use Case 1: Regional Comparison

```bash
# Compare two-wheeler adoption across key markets
for region in China USA Europe Rest_of_World; do
  python3 scripts/forecast.py --vehicle-type two_wheeler --region $region --end-year 2035 --output csv
done

# Compare outputs manually or using data analysis tools
```

### Use Case 2: Sensitivity Analysis

```bash
# Test different EV adoption ceilings
python3 scripts/forecast.py --vehicle-type two_wheeler --region China --ceiling 0.75 --output csv
python3 scripts/forecast.py --vehicle-type two_wheeler --region China --ceiling 0.90 --output csv
python3 scripts/forecast.py --vehicle-type two_wheeler --region China --ceiling 0.95 --output csv
```

### Use Case 3: Vehicle Type Comparison

```bash
# Compare two-wheeler vs three-wheeler adoption in China
python3 scripts/forecast.py --vehicle-type two_wheeler --region China --output csv
python3 scripts/forecast.py --vehicle-type three_wheeler --region China --output csv
```

## Troubleshooting

### Issue: "Region not supported for vehicle type"
**Cause:** USA is not supported for three-wheelers
**Solution:** Use China, Europe, Rest_of_World, or Global for three-wheelers

### Issue: "No tipping point found"
**Cause:** ICE remains cheaper throughout forecast horizon
**Solution:** Extend forecast horizon (`--end-year 2050`) or check cost data

### Issue: "Validation failed: Sum consistency violated"
**Cause:** Numerical precision or extreme parameters
**Solution:** Check input data quality, adjust ceiling parameter

### Issue: Import errors when running scripts
**Cause:** Missing dependencies or incorrect Python path
**Solution:**
```bash
cd .claude/skills/light-vehicle-demand
pip3 install -r requirements.txt
python3 scripts/forecast.py --help
```

## Technical Details

- **Historical Data**: 2010-2024 (varies by metric and region)
- **Forecast Horizon**: Configurable (typically 2020-2030 (extended: 2035))
- **Temporal Granularity**: Annual
- **Primary Unit**: Units per year (vehicles)
- **Methodology**: Cost-driven disruption with logistic adoption
- **Runtime**: <30 seconds per region
- **Memory**: Requires ~100MB RAM


## Taxonomy and Dataset Mapping

### Overview
This skill supports two distinct light vehicle markets, each with its own taxonomy and dataset structure.

---

### Two-Wheeler Market

**Market Definition**
- **Market:** `Two_Wheelers`
- **Total Market Demand:** `Two_Wheeler_Annual_Sales` (by region)

**Disruptor Technology**
- **EV Two-Wheelers**
  - Entity Type: `disruptor`
  - Primary Cost: `EV_2_Wheeler_(Range-100_KM)_Lowest_Cost` (by region)
  - Median Cost: `Two_Wheeler_(EV)_Median_Cost` (by region)
  - Demand Dataset: `Two_Wheeler_(EV)_Annual_Sales` (by region)
  - Installed Base: `Two_Wheeler_(EV)_Total_Fleet` (by region, except China)

**Incumbent Technology**
- **ICE Two-Wheelers**
  - Entity Type: `incumbent`
  - Cost: `Two_Wheeler_(ICE)_Median_Cost` (by region)
  - Demand Dataset: `Two_Wheeler_(ICE)_Annual_Sales` (by region)
  - Installed Base: `Two_Wheeler_(ICE)_Total_Fleet` (by region)

**Available Regions:** China, USA, Europe, Rest_of_World, Global

**Fleet Lifetime:** 11 years

**Dataset Files:**
- `data/two_wheeler/Two_Wheeler.json` - Sales, cost, and fleet data
- `data/two_wheeler/two_wheeler_taxonomy_and_datasets.json` - Taxonomy mapping

---

### Three-Wheeler Market

**Market Definition**
- **Market:** `Three_Wheelers`
- **Total Market Demand:** `Annual_Sales` (by region)

**Disruptor Technology**
- **EV Three-Wheelers**
  - Entity Type: `disruptor`
  - Primary Cost: `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost` (by region)
  - Secondary Cost: `(EV)_Median_Cost` (by region)
  - Demand Dataset: `(EV)_Annual_Sales` (by region)
  - Installed Base: `(EV)_Total_Fleet` (by region)

**Incumbent Technology**
- **ICE Three-Wheelers**
  - Entity Type: `incumbent`
  - Cost: `(ICE)_Median_Cost` (by region)
  - Demand Dataset: `(ICE)_Annual_Sales` (by region)
  - Installed Base: `(ICE)_Total_Fleet` (by region)

**Commodity Impact Tracking**
- **Lead (Battery Material)**
  - Entity Type: `commodity`
  - Implied Demand (Global):
    - Sales: `Lead_Annual_Implied_Demand-Sales_3_wheelers`
    - Replacement: `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers`

**Available Regions:** China, Europe, Rest_of_World, Global

**Note:** USA is excluded as the three-wheeler market is minimal in North America.

**Fleet Lifetime:** 10 years (shorter due to commercial use intensity)

**Dataset Files:**
- `data/three_wheeler/Three_Wheeler.json` - Sales, cost, and fleet data
- `data/three_wheeler/three_wheeler_taxonomy_and_datasets.json` - Taxonomy mapping

---

### Key Differences Summary

| Feature | Two-Wheeler | Three-Wheeler |
|---------|-------------|---------------|
| **Market Dataset** | `Two_Wheeler_Annual_Sales` | `Annual_Sales` |
| **EV Cost (Primary)** | `EV_2_Wheeler_(Range-100_KM)_Lowest_Cost` | `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost` |
| **Fleet Lifetime** | 11 years | 10 years |
| **USA Region** | ✓ Supported | ✗ Not supported |
| **EV Fleet Data (China)** | ✗ Not available | ✓ Available |
| **Lead Tracking** | ✗ Not included | ✓ Included |
| **Use Case** | Personal/commuter | Commercial/delivery |

### Configuration Files

Each vehicle type has its own configuration:
- `configs/two_wheeler_config.json` - Two-wheeler specific parameters
- `configs/three_wheeler_config.json` - Three-wheeler specific parameters

These configs include:
- Default adoption ceilings
- Fleet lifetime settings
- Regional availability
- Cost smoothing parameters
- Logistic curve fitting parameters

## Related Skills

- **demand-forecasting**: General demand forecasting framework
- **energy-forecasting**: Energy demand forecasting
- **commercial-vehicle-demand**: Commercial vehicle forecasting

