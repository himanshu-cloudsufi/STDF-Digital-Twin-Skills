---
name: commercial-vehicle-demand
description: >
  Performs segment-level demand forecasting for commercial vehicles (LCV, MCV, HCV) with EV disruption analysis, tipping point detection, and NGV chimera modeling across global regions. Calculates cost parity per segment and models differentiated EV adoption with segment-specific ceilings. Use when user asks about commercial vehicle demand, truck forecasts, CV electrification, LCV/MCV/HCV adoption, fleet tracking, or questions like "forecast commercial vehicle demand", "when will trucks electrify", "LCV vs HCV adoption rates", "NGV decline trajectory", "commercial vehicle fleet evolution", "segment-level tipping points". Handles segments: LCV (light duty), MCV (medium duty), HCV (heavy duty). Regions: China, USA, Europe, Rest_of_World, Global. Trigger keywords: forecast, commercial vehicle, CV, truck, LCV, MCV, HCV, light duty, medium duty, heavy duty, NGV, natural gas, segment, tipping point, fleet tracking, electrification, China, USA, Europe. (project)
---

> ⚠️ **MANDATORY SCRIPT EXECUTION REQUIREMENT**
>
> This skill REQUIRES executing `scripts/forecast.py` using Bash tool.
>
> **REQUIRED:** `cd .claude/skills/commercial-vehicle-demand && python3 scripts/forecast.py --region X --end-year Y`
>
> **PROHIBITED:** Mental calculation, self-generated forecasts, methodology replication
>
> The methodology below describes what THE SCRIPT does. Your job: RUN THE SCRIPT, not replicate its logic.
> Understanding the methodology ≠ Running the code. Reading this file ≠ Executing the analysis.
>
> **🔴 HISTORICAL DATA:** Do NOT generate historical values (LCV/MCV/HCV sales, costs, fleet) from memory. The script loads actual data from `Commercial_Vehicles.json`. Only script output contains verified historical data.

# Commercial Vehicle Demand Forecasting

**Status:** Active skill for segment-level commercial vehicle (CV) demand forecasting with EV disruption and NGV modeling.

## Table of Contents
- [Available Datasets](#available-datasets)
- [When to Use This Skill](#when-to-use-this-skill)
- [Quick Start](#quick-start)
- [Parameters](#parameters)
- [Forecasting Process](#forecasting-process)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Taxonomy and Dataset Mapping](#taxonomy-and-dataset-mapping)
- [Reference Documentation](#reference-documentation)

## Available Datasets

**CRITICAL FOR PLANNING:** The following datasets are available for all three segments (LCV, MCV, HCV):

### LCV (Light Duty Commercial Vehicles)
- **Market:** `Light_Duty_Commercial_Vehicle_Annual_Sales_{Region}`
- **EV Cost:** `LCV_commercial_vehicle_(Range-100_KM)_Lowest_Cost_{Region}` (key for tipping point)
- **ICE Cost:** `Light_Duty_Commercial_Vehicle_(ICE)_Price_{Region}` (key for tipping point)
- **EV Demand:** `Light_Duty_Commercial_Vehicle_(EV)_Annual_Sales_{Region}`
- **ICE Demand:** `Light_Duty_Commercial_Vehicle_(ICE)_Annual_Sales_{Region}`
- **NGV Demand:** `Light-duty_commercial_vehicles_(NGV)_Annual_Sales_{Region}`
- **EV Fleet:** `Light_Duty_Commercial_Vehicle_(EV)_Total_Fleet_{Region}`
- **ICE Fleet:** `Light_Duty_Commercial_Vehicle_(ICE)_Total_Fleet_{Region}`
- **NGV Fleet:** `Light_Duty_Commercial_Vehicle_(NGV)_Total_Fleet_{Region}`

### MCV (Medium Duty Commercial Vehicles)
- **Market:** `Medium_Duty_Commercial_Vehicle_Annual_Sales_{Region}`
- **EV Cost:** `MCV_commercial_vehicle_(Range-200_KM)_Lowest_Cost_{Region}` (key for tipping point)
- **ICE Cost:** `Medium_Duty_Commercial_Vehicle_(ICE)_Price_{Region}` (key for tipping point)
- **EV Demand:** `Medium_Duty_Commercial_Vehicle_(EV)_Annual_Sales_{Region}`
- **ICE Demand:** `Medium_Duty_Commercial_Vehicle_(ICE)_Annual_Sales_{Region}`
- **NGV Demand:** `Medium-duty_commercial_vehicles_(NGV)_Annual_Sales_{Region}`
- **EV Fleet:** `Medium_Duty_Commercial_Vehicle_(EV)_Total_Fleet_{Region}`
- **ICE Fleet:** `Medium_Duty_Commercial_Vehicle_(ICE)_Total_Fleet_{Region}`
- **NGV Fleet:** `Medium_Duty_Commercial_Vehicle_(NGV)_Total_Fleet_{Region}`

### HCV (Heavy Duty Commercial Vehicles)
- **Market:** `Heavy_Duty_Commercial_Vehicle_Annual_Sales_{Region}`
- **EV Cost:** `HCV_commercial_vehicle_(Range-400_KM)_Lowest_Cost_{Region}` (key for tipping point)
- **ICE Cost:** `Heavy_Duty_Commercial_Vehicle_(ICE)_Price_{Region}` (key for tipping point)
- **EV Demand:** `Heavy_Duty_Commercial_Vehicle_(EV)_Annual_Sales_{Region}`
- **ICE Demand:** `Heavy_Duty_Commercial_Vehicle_(ICE)_Annual_Sales_{Region}`
- **NGV Demand:** `Heavy-duty_commercial_vehicles_(NGV)_Annual_Sales_{Region}`
- **EV Fleet:** `Heavy_Duty_Commercial_Vehicle_(EV)_Total_Fleet_{Region}`
- **ICE Fleet:** `Heavy_Duty_Commercial_Vehicle_(ICE)_Total_Fleet_{Region}`
- **NGV Fleet:** `Heavy_Duty_Commercial_Vehicle_(NGV)_Total_Fleet_{Region}`

### Dataset Files Location
- `Commercial_Vehicle.json` - All segment data (LCV, MCV, HCV) for all powertrains
- `commercial_vehicle_taxonomy_and_datasets.json` - Complete taxonomy mapping

### Regional Coverage
All datasets available for: **China, USA, Europe, Rest_of_World, Global**

### Adoption Ceilings by Segment
- **LCV:** 95% EV adoption ceiling (high suitability for urban delivery)
- **MCV:** 85% EV adoption ceiling (moderate range requirements)
- **HCV:** 75% EV adoption ceiling (long-haul constraints)

## When to Use This Skill

Use for commercial vehicle demand forecasting when:
- Analyzing segment-specific electrification (LCV, MCV, HCV)
- Detecting tipping points for different vehicle classes
- Modeling NGV (Natural Gas Vehicle) decline as transitional technology
- Tracking fleet evolution with segment-specific lifetimes
- Comparing adoption rates across light, medium, and heavy duty vehicles

**Key Differentiators:**
- Segment-level granularity (LCV/MCV/HCV)
- Differentiated EV adoption ceilings per segment
- NGV chimera modeling with exponential decline
- Multi-level aggregation (segment → product → region → global)

## Quick Start

```bash
# Single segment forecast
python3 scripts/forecast.py --region China --segment LCV --end-year 2030 --output csv

# All segments with aggregation
python3 scripts/forecast.py --region USA --all-segments --end-year 2030 --output both

# With fleet tracking
python3 scripts/forecast.py --region Europe --segment MCV --track-fleet --output json

# Using shell script
./run_forecast.sh China all 2030 csv         # All segments
./run_forecast.sh USA LCV 2035 json          # Single segment
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | Required | China, USA, Europe, Rest_of_World |
| `--segment` | all | LCV, MCV, or HCV (omit for all segments) |
| `--all-segments` | false | Flag to forecast all segments |
| `--end-year` | 2035 | Forecast horizon |
| `--output` | csv | csv, json, or both |
| `--output-dir` | ./output | Output directory path |
| `--track-fleet` | false | Enable fleet evolution tracking |
| `--ngv-half-life` | 6.0 | NGV decline half-life in years |

## Forecasting Process

1. **Segment-Level Cost Analysis:** Detects tipping point per segment (LCV, MCV, HCV) using 3-year rolling median smoothing and log-CAGR extrapolation
2. **Market Growth Forecast:** Theil-Sen regression with ±5% CAGR cap per segment
3. **EV Adoption Modeling:** Logistic S-curve post-tipping with segment-specific ceilings (LCV: 95%, MCV: 85%, HCV: 75%)
4. **NGV Chimera Modeling:** Detects historical peak, applies exponential decline with configurable half-life (default 6 years)
5. **ICE Residual Calculation:** ICE = Market - EV - NGV per segment
6. **Multi-Level Aggregation:** Segments → Total CV → Regional → Global
7. **Fleet Tracking (Optional):** Stock-flow accounting with segment lifetimes (LCV: 12yr, MCV: 15yr, HCV: 18yr)
8. **Validation:** Non-negativity checks, sum consistency (±2% tolerance), share bounds

## Output Formats

**CSV:** Region, Segment, Year, Market, EV, ICE, NGV, EV_Share, ICE_Share, NGV_Share, EV_Fleet, ICE_Fleet, NGV_Fleet, Total_Fleet

**JSON:** Includes segment_results (cost_analysis, demand_forecast, ngv_metadata), total_cv aggregation, tipping_points, logistic parameters, validation

Files saved to: `output/{Region}_{Segment}_{EndYear}.{format}`

## Examples

**Example 1: China LCV forecast**
```bash
python3 scripts/forecast.py --region China --segment LCV --output csv
```
Result: LCV-specific tipping point (~2027), 95% EV adoption ceiling by 2035

**Example 2: USA all segments with fleet tracking**
```bash
python3 scripts/forecast.py --region USA --all-segments --track-fleet --output both
```
Result: Differentiated adoption across LCV/MCV/HCV + aggregated Total CV + fleet evolution

**Example 3: Europe MCV with custom NGV decline**
```bash
python3 scripts/forecast.py --region Europe --segment MCV --ngv-half-life 5.0 --output json
```
Result: Faster NGV decline (5-year half-life) for medium duty trucks

## Taxonomy and Dataset Mapping

### Market Definition
- **Market:** `Commercial_Vehicles`
- **Total Market Demand:** `Annual_Sales` (by region)
- **Segments:** `LCV` (Light Duty), `MCV` (Medium Duty), `HCV` (Heavy Duty)

### Technology Types

**EV Commercial Vehicles**
- Entity Type: `disruptor`
- Demand Dataset: `(EV)_Annual_Sales` (by region)
- Installed Base: `(EV)_Total_Fleet` (by region)

**ICE Commercial Vehicles**
- Entity Type: `incumbent`
- Demand Dataset: `(ICE)_Annual_Sales` (by region)
- Installed Base: `(ICE)_Total_Fleet` (by region)

**NGV Commercial Vehicles (Natural Gas)**
- Entity Type: `chimera` (transitional technology)
- Demand Dataset: `(NGV)_Annual_Sales` (by region)
- Installed Base: `(NGV)_Total_Fleet` (by region)

### Segment-Specific Datasets

**LCV (Light Duty Commercial Vehicles)**
- Full Name: `Light_Duty_Commercial_Vehicles`
- EV Cost: `LCV_commercial_vehicle_(Range-100_KM)_Lowest_Cost` (by region)
- ICE Cost: `Light_Duty_Commercial_Vehicle_(ICE)_Price` (by region)
- Total Market: `Light_Duty_Commercial_Vehicle_Annual_Sales` (by region)
- EV Demand: `Light_Duty_Commercial_Vehicle_(EV)_Annual_Sales` (by region)
- ICE Demand: `Light_Duty_Commercial_Vehicle_(ICE)_Annual_Sales` (by region)
- NGV Demand: `Light-duty_commercial_vehicles_(NGV)_Annual_Sales` (by region)
- EV Fleet: `Light_Duty_Commercial_Vehicle_(EV)_Total_Fleet` (by region)
- ICE Fleet: `Light_Duty_Commercial_Vehicle_(ICE)_Total_Fleet` (by region)
- NGV Fleet: `Light_Duty_Commercial_Vehicle_(NGV)_Total_Fleet` (by region)

**MCV (Medium Duty Commercial Vehicles)**
- Full Name: `Medium_Duty_Commercial_Vehicles`
- EV Cost: `MCV_commercial_vehicle_(Range-200_KM)_Lowest_Cost` (by region)
- ICE Cost: `Medium_Duty_Commercial_Vehicle_(ICE)_Price` (by region)
- Total Market: `Medium_Duty_Commercial_Vehicle_Annual_Sales` (by region)
- EV Demand: `Medium_Duty_Commercial_Vehicle_(EV)_Annual_Sales` (by region)
- ICE Demand: `Medium_Duty_Commercial_Vehicle_(ICE)_Annual_Sales` (by region)
- NGV Demand: `Medium-duty_commercial_vehicles_(NGV)_Annual_Sales` (by region)
- EV Fleet: `Medium_Duty_Commercial_Vehicle_(EV)_Total_Fleet` (by region)
- ICE Fleet: `Medium_Duty_Commercial_Vehicle_(ICE)_Total_Fleet` (by region)
- NGV Fleet: `Medium_Duty_Commercial_Vehicle_(NGV)_Total_Fleet` (by region)

**HCV (Heavy Duty Commercial Vehicles)**
- Full Name: `Heavy_Duty_Commercial_Vehicles`
- EV Cost: `HCV_commercial_vehicle_(Range-400_KM)_Lowest_Cost` (by region)
- ICE Cost: `Heavy_Duty_Commercial_Vehicle_(ICE)_Price` (by region)
- Total Market: `Heavy_Duty_Commercial_Vehicle_Annual_Sales` (by region)
- EV Demand: `Heavy_Duty_Commercial_Vehicle_(EV)_Annual_Sales` (by region)
- ICE Demand: `Heavy_Duty_Commercial_Vehicle_(ICE)_Annual_Sales` (by region)
- NGV Demand: `Heavy-duty_commercial_vehicles_(NGV)_Annual_Sales` (by region)
- EV Fleet: `Heavy_Duty_Commercial_Vehicle_(EV)_Total_Fleet` (by region)
- ICE Fleet: `Heavy_Duty_Commercial_Vehicle_(ICE)_Total_Fleet` (by region)
- NGV Fleet: `Heavy_Duty_Commercial_Vehicle_(NGV)_Total_Fleet` (by region)

### Available Regions
All datasets support: `China`, `USA`, `Europe`, `Rest_of_World`, `Global`

### Available Dataset Files
- `Commercial_Vehicle.json` - Historical sales, costs, and fleet data for all segments and technologies
- `commercial_vehicle_taxonomy_and_datasets.json` - Taxonomy mapping (this section)

### Adoption Ceilings by Segment
- **LCV:** 95% EV adoption ceiling (high suitability for urban delivery)
- **MCV:** 85% EV adoption ceiling (moderate range requirements)
- **HCV:** 75% EV adoption ceiling (long-haul constraints)

## Reference Documentation

- [reference/methodology-reference.md](reference/methodology-reference.md) - Detailed algorithms, cost curve smoothing, logistic fitting
- [reference/parameters-reference.md](reference/parameters-reference.md) - Parameter catalog with segment-specific settings
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - Schema specifications for CSV/JSON
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - Input data requirements (Commercial_Vehicle.json)

