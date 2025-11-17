---
name: energy-forecasting
description: >
  Performs cost-driven capacity and generation forecasting for Solar-Wind-Battery (SWB) energy systems and their displacement of fossil fuels (coal, gas). Calculates SWB stack cost parity, models capacity growth using YoY averaging, and sequences coal/gas displacement. Use when user asks about renewable energy capacity, solar/wind forecasts, battery storage, SWB adoption, electricity generation, fossil fuel displacement, or questions like "when will solar reach cost parity", "forecast wind capacity", "when will coal be displaced", "SWB generation by 2040", "battery storage growth", "renewable energy disruption". Handles regions: China, USA, Europe, Rest_of_World, Global. Trigger keywords: solar, wind, battery, SWB, renewable, clean energy, electricity, generation, capacity, coal, gas, displacement, LCOE, cost parity, energy transformation, disruption. (project)
---

# Energy Forecasting (Solar-Wind-Battery)

Cost-driven forecasting for SWB (Solar-Wind-Battery) energy systems and fossil fuel displacement.

## When to Use This Skill

Use for energy generation and capacity forecasting when:
- Analyzing solar, wind, or battery storage adoption
- Forecasting electricity generation by technology
- Calculating SWB stack cost vs coal/gas LCOE
- Modeling coal or gas displacement timelines
- Questions about renewable energy capacity, generation, or market share
- Cross-technology questions (e.g., "when will SWB displace coal?")

## Quick Start

```bash
# Single region forecast
./run_forecast.sh --region China --end-year 2040 --output csv

# Global (all regions + aggregation)
./run_forecast.sh --region Global --end-year 2040 --output both

# Custom battery parameters
./run_forecast.sh --region USA --battery-duration 4 --output json
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | Required | China, USA, Europe, Rest_of_World, Global |
| `--end-year` | 2040 | Forecast horizon |
| `--battery-duration` | 4 | Battery duration in hours (2, 4, or 8) |
| `--output` | csv | csv, json, or both |

## Forecasting Process

1. **Cost Analysis:** Calculate SWB stack cost (MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE) vs Coal/Gas LCOE
2. **Tipping Point Detection:** Identify year when SWB cost < min(Coal_LCOE, Gas_LCOE)
3. **Capacity Forecasting:** YoY growth averaging for Solar, Onshore Wind, Offshore Wind, Battery Storage
4. **CSP Handling:** Include CSP conditionally if capacity > 1% of Solar PV
5. **Generation Derivation:** Convert capacity to generation using capacity factors
6. **Displacement Sequencing:** Model coal-first or gas-first displacement by region
7. **Residual Allocation:** Calculate nuclear, hydro, and remaining fossil generation
8. **Validation:** Energy balance, capacity factor bounds, reserve floors, non-negativity

## Key Methodology Differences

**vs Passenger Vehicle Forecasting:**
- Uses **YoY growth averaging** (not logistic S-curve)
- Multi-component disruptor: SWB stack (Solar + Wind + Battery)
- Sequenced displacement: Coal-first vs gas-first by region
- Capacity-generation conversion via capacity factors
- LCOE + SCOE cost calculations (not $/mile)
- Reserve floors: 10% coal, 15% gas until full displacement

## Output Formats

**CSV:** Year, Solar_Capacity, Wind_Capacity, Battery_Capacity, SWB_Generation, Coal_Generation, Gas_Generation, Total_Generation

**JSON:** Includes cost analysis (tipping point, LCOE, SCOE), capacity forecasts, generation forecasts, displacement timeline, validation results

Files saved to: `output/{Region}_{EndYear}.{format}`

## Examples

**Example 1: China 2040 (coal-first displacement)**
```bash
./run_forecast.sh --region China --output csv
```

**Example 2: USA 2040 (gas-first displacement)**
```bash
./run_forecast.sh --region USA --end-year 2040 --output both
```

**Example 3: Global aggregation with 8-hour battery**
```bash
./run_forecast.sh --region Global --battery-duration 8 --output json
```

## Displacement Sequences by Region

| Region | Sequence | Rationale |
|--------|----------|-----------|
| China | Coal-first | High coal dependency, government policy |
| USA | Gas-first | Gas-heavy grid, coal already declining |
| Europe | Coal-first | Coal phase-out commitments |
| Rest_of_World | Coal-first | Default assumption |

## Reference Documentation

- [reference/methodology-reference.md](reference/methodology-reference.md) - YoY averaging, SCOE, displacement logic
- [reference/parameters-reference.md](reference/parameters-reference.md) - Battery parameters, CFs, reserve floors
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - SWB data structures
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - CSV/JSON specifications
- [reference/troubleshooting-reference.md](reference/troubleshooting-reference.md) - Common errors and solutions

## Key Concepts

- **SWB Stack**: Solar PV + Wind (Onshore + Offshore) + Battery Storage
- **LCOE**: Levelized Cost of Energy ($/MWh) for generation technologies
- **SCOE**: Storage Cost of Energy ($/MWh) for battery storage
- **Capacity Factor (CF)**: Ratio of actual generation to theoretical maximum (e.g., Solar ~0.15, Wind ~0.30)
- **Displacement**: Gradual replacement of coal/gas generation by SWB
- **Reserve Floor**: Minimum coal (10%) or gas (15%) capacity retained for grid stability

