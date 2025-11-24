---
name: demand-forecasting
description: >
  Performs cost-driven demand forecasting for passenger vehicles (EV, PHEV, ICE) across global regions. Calculates cost parity tipping points and models market adoption using logistic growth curves. Use when user asks about passenger vehicle demand, EV adoption, electric vehicle forecasts, market penetration, sales projections, or questions like "when will EVs dominate", "what is EV adoption in China", "forecast passenger vehicle demand", "when does cost parity occur", "EV market share by 2035", "predict ICE decline", "PHEV adoption trajectory". Handles regions: China, USA, Europe, Rest_of_World, Global. Trigger keywords: forecast, predict, demand, adoption, penetration, market share, EV, electric vehicle, passenger vehicle, BEV, PHEV, ICE, tipping point, cost parity, China, USA, Europe, 2030. (project)
---

# Cost-Driven Demand Forecasting

## Quick Start

**Prerequisites:**
```bash
pip install -r requirements.txt
```

```bash
# Single region
python3 scripts/forecast.py --region China --end-year 2030 --output csv

# Global (all regions + aggregation)
python3 scripts/forecast.py --region Global --end-year 2030 --output both
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | Required | China, USA, Europe, Rest_of_World, Global |
| `--end-year` | 2035 | Forecast horizon |
| `--ceiling` | 1.0 | Max EV adoption (0.0-1.0) |
| `--output` | csv | csv, json, or both |

## Forecasting Process

1. **Cost Analysis:** Detects tipping point (year EV cost < ICE cost)
2. **Market Forecast:** Linear extrapolation with ±5% CAGR cap
3. **BEV Forecast:** Logistic S-curve adoption post-tipping
4. **PHEV Forecast:** Hump trajectory (rises pre-tipping, decays after with 3-year half-life)
5. **ICE Forecast:** Residual calculation (Market - BEV - PHEV)
6. **Validation:** Ensures BEV + PHEV + ICE ≤ Market, all values ≥ 0

## Output Formats

**CSV:** Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost
**JSON:** Includes cost analysis, demand forecast, tipping point, logistic parameters, validation

Files saved to: `output/{Region}_{EndYear}.{format}`

## Examples

**Example 1: China 2030*
```bash
python3 scripts/forecast.py --region China --output csv
```

**Example 2: Europe with 90% ceiling**
```bash
python3 scripts/forecast.py --region Europe --ceiling 0.9 --end-year 2035 --output both
```

**Example 3: Global analysis**
```bash
python3 scripts/forecast.py --region Global --output json
```

## Taxonomy and Dataset Mapping

### Market Definition
- **Market:** `Passenger_Vehicles`
- **Total Market Demand:** `Passenger_Vehicle_Annual_Sales` (by region)

### Disruptor Technologies (EVs)

**EV Cars (Aggregate)**
- Entity Type: `disruptor`
- Subproducts: `BEV_Cars`, `PHEV_Cars`
- Cost Dataset: `Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost` (all regions)
- Demand Dataset: `Passenger_Vehicle_(EV)_Annual_Sales` (by region)

**BEV Cars (Battery Electric)**
- Entity Type: `disruptor`
- Demand Dataset: `Passenger_Vehicle_(BEV)_Annual_Sales` (by region)
- Installed Base: `Passenger_Vehicle_(BEV)_Total_Fleet` (by region)

**PHEV Cars (Plug-in Hybrid)**
- Entity Type: `chimera` (transitional technology)
- Demand Dataset: `Passenger_Vehicle_(PHEV)_Annual_Sales` (by region)

### Incumbent Technology

**ICE Cars (Internal Combustion Engine)**
- Entity Type: `incumbent`
- Cost Dataset: `Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)` (by region)
- Demand Dataset: `Passenger_Vehicle_(ICE)_Annual_Sales` (by region)
- Installed Base: `Passenger_Vehicle_(ICE)_Total_Fleet` (by region)
  - China also has: `Passenger_Vehicle_(ICE)_Total_Fleet_TaaSAdj` (TaaS-adjusted)

### Available Regions
All datasets support: `China`, `USA`, `Europe`, `Rest_of_World`, `Global`

### Available Dataset Files
- `Passenger_Cars.json` - Historical sales and cost data for EV, PHEV, and ICE vehicles
- `passenger_vehicles_taxonomy_and_datasets.json` - Taxonomy mapping (this section)

## Reference Documentation

- [reference/methodology-reference.md](reference/methodology-reference.md) - Complete algorithms
- [reference/parameters-reference.md](reference/parameters-reference.md) - Parameter details
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - JSON structure
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - Output specs
- [reference/troubleshooting-reference.md](reference/troubleshooting-reference.md) - Error solutions


