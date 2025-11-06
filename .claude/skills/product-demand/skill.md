---
name: product-demand
description: >
  Forecast demand for products using cost-driven disruption analysis. Handles 43 products: passenger vehicles (EV, PHEV, ICE), commercial vehicles (LCV, MDV, HDV), two/three-wheelers, energy generation (solar, wind, coal, gas, oil), energy storage (batteries). Use when user asks about product demand, market penetration, sales forecasts, adoption rates, capacity forecasts, market share, questions like "EV demand in China by 2040", "when will solar reach 50% market share", "forecast commercial vehicle adoption", "how many EVs sold", "battery storage capacity", "cost parity", "market size for solar", "product reach threshold", "product peak", "EV adoption", "solar/wind capacity", "vehicle sales", "market transformation", "technology disruption", "tipping point". Regions: China, USA, Europe, Rest_of_World, Global. Keywords: forecast, predict, demand, sales, adoption, capacity, penetration, market share, EV, solar, wind, battery, commercial vehicle, two-wheeler, cost parity, tipping point, disruption. (project)
---

# Product Demand Forecasting

Cost-driven demand forecasting for products across transportation and energy sectors using disruption theory, S-curve adoption modeling, and tipping point analysis.

## Quick Start

Forecast product demand:
```bash
cd .claude/skills/product-demand
./run_forecast.sh --product "EV_Cars" --region China --end-year 2040 --output json
```

## Available Products (43 Total)

**Transportation:** EV_Cars, PHEV_Cars, ICE_Cars, Commercial_EV, Commercial_ICE, Commercial_NGV, LCV, MDV, HDV, EV_Two_Wheeler, ICE_Two_Wheeler, EV_Three_Wheeler, ICE_Three_Wheeler

**Energy Generation:** Solar_PV, Onshore_Wind, Offshore_Wind, Coal_Power, Natural_Gas_Power, Oil_Power

**Energy Storage:** Battery_Storage, Pumped_Hydro, CAES

**Regions:** China, USA, Europe, Rest_of_World, Global

For complete list with descriptions, see: `data/products_catalog_index.json`

## Forecasting Process

1. **Load Data:** Historical cost and demand curves from entity JSON files
2. **Determine Context:** Identify disruptor/incumbent/chimera products and tipping point year
3. **Apply Model:**
   - **Disruptors** (BEV, Solar, Battery): Logistic S-curve adoption post-tipping
   - **Chimeras** (PHEV, NGV): Hump trajectory (peak at tipping, decay with 3-year half-life)
   - **Incumbents** (ICE, Coal): Residual (Market - Disruptor - Chimera)
   - **Non-disrupted**: Linear baseline with ±5% CAGR cap
4. **Validate:** Check sum constraints, non-negativity, smooth transitions
5. **Return:** Forecast with tipping point, logistic parameters, validation results

## Product Types

| Type | Model | Examples |
|------|-------|----------|
| **Disruptor** | Logistic S-curve | BEV, Solar, Wind, Battery Storage |
| **Chimera** | Hump trajectory | PHEV, NGV, Hybrids |
| **Incumbent** | Residual | ICE, Coal, Gas, Oil |
| **Market** | Linear extrapolation | Total market demand |

## Key Methodology Notes

- **Cost forecasting:** Log-CAGR method (Wright's Law) with 3-year smoothing
- **Tipping point:** First year when disruptor_cost < incumbent_cost
- **Logistic fitting:** Differential evolution with k ∈ [0.05, 1.5]
- **Chimera decay:** 3-year half-life post-tipping, peak at 15% share
- **Market CAGR:** Capped at ±5% to prevent unrealistic growth

See [reference/methodology.md](reference/methodology.md) for complete algorithms and [reference/data_schema.md](reference/data_schema.md) for data structure.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--product` | Required | Product name (e.g., EV_Cars, Solar_PV) |
| `--region` | Required | China, USA, Europe, Rest_of_World, Global |
| `--end-year` | 2040 | Forecast horizon |
| `--ceiling` | 1.0 | Max disruptor adoption (0.0-1.0) |
| `--output` | csv | csv, json, or both |

See [reference/parameters.md](reference/parameters.md) for detailed guidance.

## Examples

**EV adoption in China:**
```bash
./run_forecast.sh --product BEV_Cars --region China --end-year 2040 --output json
```

**Solar capacity in USA:**
```bash
./run_forecast.sh --product Solar_PV --region USA --end-year 2040 --output csv
```

**ICE decline globally:**
```bash
./run_forecast.sh --product ICE_Cars --region Global --end-year 2040 --output both
```

**Custom ceiling (infrastructure limited):**
```bash
./run_forecast.sh --product EV_Cars --region Europe --ceiling 0.85 --end-year 2040
```

See [reference/examples.md](reference/examples.md) for detailed examples with expected outputs.

## Output Formats

**CSV:** Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost
**JSON:** Includes product type, market context, tipping point, logistic parameters, validation

Files saved to: `output/{Product}_{Region}_{EndYear}.{format}`

## Reference Documentation

- [reference/methodology.md](reference/methodology.md) - Detailed algorithms and formulas
- [reference/data_schema.md](reference/data_schema.md) - Complete JSON structure
- [reference/parameters.md](reference/parameters.md) - Parameter tuning guidance
- [reference/examples.md](reference/examples.md) - Common usage patterns

**Note:** For terminology guidelines, see CLAUDE.md in repository root.
