---
name: product-demand
description: Forecast demand for products using cost-driven disruption analysis across transportation and energy sectors. Handles 43 products including passenger vehicles (EV, PHEV, ICE), commercial vehicles (LCV, MDV, HDV), two-wheelers, three-wheelers, energy generation (solar, wind, coal, gas, oil), energy storage (batteries). Use when user asks about product demand, market penetration, sales forecasts, adoption rates, capacity forecasts, market share, market size, or questions like "what is EV demand in China by 2040", "when will solar reach 50% market share", "forecast commercial vehicle adoption", "how many EVs will be sold", "project battery storage capacity", "when does cost parity occur", "what is the market size for solar", "when will product reach threshold", "when will product peak", "EV adoption", "solar capacity", "wind capacity", "vehicle sales", "market transformation", "technology disruption", "tipping point detection". Covers regions: China, USA, Europe, Rest_of_World, Global. Trigger keywords: forecast, predict, project, demand, sales, adoption, capacity, penetration, market share, market size, EV, solar, wind, battery, commercial vehicle, two-wheeler, three-wheeler, cost parity, tipping point, disruption, 2040, 2050.
---

# Product Demand Forecasting

Cost-driven demand forecasting for products across transportation and energy sectors using disruption theory, S-curve adoption modeling, and tipping point analysis.

## Quick Start

Forecast product demand:
```bash
cd .claude/skills/product-demand
./run_forecast.sh --product "EV_Cars" --region China --end-year 2040 --output json
```

## Available Products

### Passenger Vehicles
- **EV_Cars** / **BEV_Cars** - Battery Electric Vehicles (disruptor)
- **PHEV_Cars** - Plug-in Hybrid Electric Vehicles (chimera/bridge)
- **ICE_Cars** - Internal Combustion Engine vehicles (incumbent)
- **Passenger_Vehicles** - Total passenger vehicle market

### Commercial Vehicles
- **Commercial_EV** - Commercial electric vehicles (disruptor)
- **Commercial_ICE** - Commercial ICE vehicles (incumbent)
- **Commercial_NGV** - Natural gas vehicles (chimera)
- **LCV** - Light commercial vehicles
- **MDV** - Medium-duty vehicles
- **HDV** - Heavy-duty vehicles

### Two-Wheelers
- **EV_Two_Wheeler** - Electric two-wheelers (disruptor)
- **ICE_Two_Wheeler** - ICE two-wheelers (incumbent)
- **Two_Wheeler_Market** - Total two-wheeler market

### Three-Wheelers
- **EV_Three_Wheeler** - Electric three-wheelers (disruptor)
- **ICE_Three_Wheeler** - ICE three-wheelers (incumbent)
- **Three_Wheeler_Market** - Total three-wheeler market

### Energy Generation
- **Solar_PV** - Solar photovoltaic (disruptor)
- **Onshore_Wind** - Onshore wind power (disruptor)
- **Offshore_Wind** - Offshore wind power (disruptor)
- **Coal_Power** - Coal power generation (incumbent)
- **Natural_Gas_Power** - Natural gas power (incumbent)
- **Oil_Power** - Oil power generation (incumbent)

### Energy Storage
- **Battery_Storage** - Battery energy storage (disruptor)
- **Pumped_Hydro** - Pumped hydro storage (incumbent)
- **CAES** - Compressed air energy storage

### Regions
- **China**, **USA**, **Europe**, **Rest_of_World**, **Global** (aggregated)

For complete list, see: `data/products_catalog_index.json`

## Forecasting Process

The skill uses a **cost-driven disruption framework** to forecast product demand:

### 1. Load Product Data
Load historical cost and demand curves from entity JSON files.

### 2. Determine Market Context
- Is this market disrupted? (disruptor technology exists with declining costs)
- What are the disruptor/incumbent/chimera products?
- What's the tipping point year? (cost parity between disruptor and incumbent)

### 3. Route to Appropriate Model

**For Disruptor Products** (e.g., BEV, Solar, Battery Storage):
- Use **logistic S-curve adoption model**
- Pre-tipping: Linear or accelerating growth
- Post-tipping: Exponential acceleration to ceiling (typically 90-100%)
- Formula: `s(t) = L / (1 + exp(-k * (t - t₀)))`
  - L = ceiling (max adoption share)
  - k = growth rate (steepness)
  - t₀ = inflection point year

**For Chimera Products** (e.g., PHEV, NGV):
- Use **hump trajectory** model
- Rise to peak at tipping point (typically 10-15% market share)
- Exponential decay post-tipping with 3-year half-life
- Bridge technologies that facilitate transition but don't dominate

**For Incumbent Products** (e.g., ICE, Coal):
- Use **residual calculation**: `Incumbent = Market - Disruptor - Chimera`
- Ensures sum constraint always met
- Captures displacement by disruptors

**For Non-Disrupted Markets**:
- Use **linear baseline** with Theil-Sen robust regression
- CAGR capped at ±5% to prevent unrealistic growth

### 4. Validate
- Check: BEV + PHEV + ICE ≤ Market (with 0.1% tolerance)
- Check: All values ≥ 0
- Check: Smooth year-over-year transitions (no >50% jumps)
- Check: Physically realistic CAGRs (<20%)

### 5. Return Forecast
Output includes:
- Historical + forecasted demand/capacity
- Cost curves (if applicable)
- Tipping point year
- Logistic parameters (L, k, t₀)
- Validation results

## Product Classification

Products are classified by their role in market disruption:

| Type | Description | Examples | Model |
|------|-------------|----------|-------|
| **Disruptor** | New technology with exponentially declining costs that achieves cost parity with incumbent | BEV, Solar PV, Wind, Battery Storage | Logistic S-curve |
| **Chimera** | Bridge technology that rises pre-tipping, decays post-tipping | PHEV, NGV, Hybrid systems | Hump trajectory |
| **Incumbent** | Established technology displaced by disruptor | ICE, Coal, Gas, Oil | Residual |
| **Market** | Total market demand (sum of all competing technologies) | Passenger_Vehicles, Energy_Generation | Linear extrapolation |

Classification is defined in taxonomy files and product catalog index.

## Methodology

### Cost Curve Forecasting
1. Apply 3-year rolling median smoothing to remove noise
2. Forecast using **log-CAGR method** (Wright's Law):
   - Transform to log scale: `log(cost)`
   - Fit linear trend: `log(cost) = a + b*year`
   - Forecast in log scale, convert back to normal scale
3. Result: Exponentially declining cost curves

### Tipping Point Detection
1. Align disruptor and incumbent cost curves to common years
2. Find first year where: `disruptor_cost < incumbent_cost`
3. This is the **tipping point** (cost parity year)
4. If already past parity, use earliest available year
5. If never reach parity by end_year, return None

### Market Demand Forecast
1. Use **Theil-Sen robust regression** on historical market data
2. Extrapolate linearly to end_year
3. Apply **CAGR cap** (default: ±5%) to prevent unrealistic growth/decline
4. Ensures smooth, bounded market trajectory

### Logistic Adoption (Disruptors)
1. Calculate historical market share: `share = disruptor_demand / market_demand`
2. If tipping point > last historical year:
   - Extend share linearly to tipping point
3. Fit logistic curve using **differential evolution**:
   - Bounds: k ∈ [0.05, 1.5], t₀ ∈ [min_year - 5, max_year + 10]
   - Seed: k=0.4, t₀=tipping_year (if available)
4. Generate forecast shares: `s(t) = L / (1 + exp(-k*(t - t₀)))`
5. Convert to absolute demand: `demand = share × market`
6. Clamp to [0, market]

### Chimera Hump (Bridge Technologies)
1. Pre-tipping: Linear rise to peak_share (default: 15%)
2. At tipping: Reach maximum
3. Post-tipping: Exponential decay with half-life (default: 3 years)
   - `share(t) = peak_share × exp(-ln(2) × (t - tipping) / half_life)`
4. Convert to absolute demand
5. Clamp to [0, market]

### Incumbent Residual
1. Forecast market, disruptor, and chimera first
2. Calculate: `incumbent = max(0, market - disruptor - chimera)`
3. Ensures sum constraint always satisfied
4. Captures displacement effect

## Data Schema

Entity JSON files follow this structure:

```json
{
  "Entity Name": {
    "Product_Cost": {
      "metadata": {
        "type": "cost",
        "units": "USD per mile / USD per kWh / etc.",
        "entity_type": "disruptor"
      },
      "regions": {
        "China": {"X": [2015, 2016, ...], "Y": [0.50, 0.45, ...]},
        "USA": {"X": [...], "Y": [...]}
      }
    },
    "Product_Demand": {
      "metadata": {
        "type": "demand",
        "units": "vehicles / MW / GWh",
        "entity_type": "disruptor"
      },
      "regions": {
        "China": {"X": [...], "Y": [...]},
        "USA": {"X": [...], "Y": [...]}
      }
    }
  }
}
```

See `reference/data_schema.md` for complete specification.

## Parameters

Default parameters in `config.json`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `end_year` | 2040 | Forecast horizon |
| `logistic_ceiling` | 1.0 | Maximum disruptor adoption share (100%) |
| `market_cagr_cap` | 0.05 | Maximum market CAGR (±5%) |
| `smoothing_window` | 3 | Rolling median window for cost curves |
| `chimera_decay_half_life` | 3.0 | PHEV decay half-life (years) |
| `phev_peak_share` | 0.15 | Peak chimera share (15%) |

Adjust via command line:
```bash
./run_forecast.sh --product EV_Cars --region Europe --end-year 2050 --ceiling 0.9
```

See `reference/parameters.md` for detailed guidance.

## Examples

### Example 1: EV Adoption in China
```bash
./run_forecast.sh --product BEV_Cars --region China --end-year 2040 --output json
```

**Output:**
- Tipping point: 2022
- BEV share in 2040: 87%
- Logistic parameters: L=1.0, k=0.42, t₀=2025

### Example 2: Solar Capacity in USA
```bash
./run_forecast.sh --product Solar_PV --region USA --end-year 2040 --output csv
```

**Output:**
- Tipping point: 2020
- Solar capacity in 2040: 1,200 GW
- Displaces coal and gas

### Example 3: ICE Decline Globally
```bash
./run_forecast.sh --product ICE_Cars --region Global --end-year 2040 --output both
```

**Output:**
- Peak ICE demand: 2025 (72M vehicles)
- 2040 demand: 8M vehicles (90% decline)
- Residual calculation based on EV disruption

### Example 4: Custom Ceiling (Infrastructure Limited)
```bash
./run_forecast.sh --product EV_Cars --region Europe --ceiling 0.85 --end-year 2040
```

**Output:**
- Assumes EV adoption capped at 85% due to infrastructure/policy constraints
- Adjusts logistic ceiling parameter

## Terminology Guardrails

When presenting forecast results, this skill follows these guidelines:

### Use These Terms:
- **"transformation"** or **"disruption"** (NOT "transition")
- **"market-driven"** (NOT "policy-driven")
- **"exponential"** trends (NOT "linear growth")
- **"superabundance"** and **"zero marginal cost"**
- **"distributed"** or **"decentralized"** systems

### Avoid These Terms:
- "renewable energy", "sustainable", "green"
- "hydrogen economy", "grid parity", "energy transition"
- "intermittency", "net zero"
- "baseload power", "peak oil"

### Rationale:
These terms reflect the **speed, scale, and systemic nature** of technological disruption driven by:
- Exponential cost curves (Wright's Law)
- Zero marginal cost economics
- Market forces (not policy)
- 10-15 year transformation timelines post-tipping (not multi-generational)

### Communication Style:
- **Think exponentially, not linearly**: Disruptions accelerate after tipping points
- **Focus on speed and scale**: 80%+ adoption in 10-15 years post-tipping
- **Be quantitative**: Provide specific years for milestones
- **Show the math**: Display calculations, parameters, and derivations
- **Avoid technical jargon in user-facing output**: Explain methods in plain language

## Error Handling

### Edge Cases:
- **No tipping point found**: Report "Cost parity not achieved by {end_year}" and use conservative baseline
- **Sparse data (<3 points)**: Fall back to linear extrapolation with CAGR bounds
- **Logistic fitting fails**: Use seeded parameters (k=0.4, t₀=tipping_year) or linear trend
- **Data gaps**: Linear interpolation between available points, flag in validation report
- **Unrealistic CAGR (>±20%)**: Cap at ±5% for market, flag anomaly in metadata

## Output Formats

### CSV Format
```
Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost
2020, 75000000, 2000000, 500000, 72500000, 2500000, 0.30, 0.35
2025, 85000000, 15000000, 10000000, 60000000, 25000000, 0.22, 0.36
...
```

### JSON Format
```json
{
  "product": "EV_Cars",
  "region": "China",
  "product_type": "disruptor",
  "market_context": {
    "disrupted": true,
    "tipping_point": 2022,
    "disruptor": "EV_Cars",
    "incumbent": "ICE_Cars",
    "chimera": "PHEV_Cars"
  },
  "forecast": {
    "years": [2000, 2001, ..., 2040],
    "demand": [...]
  },
  "logistic_parameters": {
    "L": 1.0,
    "k": 0.42,
    "t0": 2025
  },
  "validation": {
    "is_valid": true,
    "message": "All checks passed"
  }
}
```

## Reference Documentation

- **methodology.md**: Detailed algorithms and formulas
- **data_schema.md**: Complete JSON structure specification
- **parameters.md**: Parameter ranges, meanings, and tuning guidance
- **examples.md**: Common usage patterns and use cases

## Implementation Notes

- **Shared library**: Imports from `.claude/skills/_forecasting_core` for math utilities
- **Taxonomy-driven**: Product names mapped to datasets via taxonomy files
- **Self-contained**: All data in `data/` directory (no external dependencies)
- **Validated**: Every forecast runs comprehensive validation suite
- **Stateless**: Each forecast is independent (no persistent state)
