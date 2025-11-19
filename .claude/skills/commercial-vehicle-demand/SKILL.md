---
name: commercial-vehicle-demand
description: >
  Performs segment-level demand forecasting for commercial vehicles (LCV, MCV, HCV) with EV disruption analysis, tipping point detection, and NGV chimera modeling across global regions. Calculates cost parity per segment and models differentiated EV adoption with segment-specific ceilings. Use when user asks about commercial vehicle demand, truck forecasts, CV electrification, LCV/MCV/HCV adoption, fleet tracking, or questions like "forecast commercial vehicle demand", "when will trucks electrify", "LCV vs HCV adoption rates", "NGV decline trajectory", "commercial vehicle fleet evolution", "segment-level tipping points". Handles segments: LCV (light duty), MCV (medium duty), HCV (heavy duty). Regions: China, USA, Europe, Rest_of_World, Global. Trigger keywords: forecast, commercial vehicle, CV, truck, LCV, MCV, HCV, light duty, medium duty, heavy duty, NGV, natural gas, segment, tipping point, fleet tracking, electrification, China, USA, Europe, 2040. (project)
---

# Commercial Vehicle Demand Forecasting

**Status:** Active skill for segment-level commercial vehicle (CV) demand forecasting with EV disruption and NGV modeling.

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
python3 scripts/forecast.py --region China --segment LCV --end-year 2040 --output csv

# All segments with aggregation
python3 scripts/forecast.py --region USA --all-segments --end-year 2040 --output both

# With fleet tracking
python3 scripts/forecast.py --region Europe --segment MCV --track-fleet --output json

# Using shell script
./run_forecast.sh China all 2040 csv         # All segments
./run_forecast.sh USA LCV 2035 json          # Single segment
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | Required | China, USA, Europe, Rest_of_World |
| `--segment` | all | LCV, MCV, or HCV (omit for all segments) |
| `--all-segments` | false | Flag to forecast all segments |
| `--end-year` | 2040 | Forecast horizon |
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
Result: LCV-specific tipping point (~2027), 95% EV adoption ceiling by 2040

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

## Reference Documentation

- [reference/methodology-reference.md](reference/methodology-reference.md) - Detailed algorithms, cost curve smoothing, logistic fitting
- [reference/parameters-reference.md](reference/parameters-reference.md) - Parameter catalog with segment-specific settings
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - Schema specifications for CSV/JSON
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - Input data requirements (Commercial_Vehicle.json)

