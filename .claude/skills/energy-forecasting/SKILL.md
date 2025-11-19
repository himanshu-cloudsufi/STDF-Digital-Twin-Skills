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
# Single region forecast (baseline scenario)
./run_forecast.sh --region China --end-year 2040 --scenario baseline --output csv

# Accelerated transition scenario
./run_forecast.sh --region USA --end-year 2040 --scenario accelerated --output both

# Global (all regions + aggregation)
./run_forecast.sh --region Global --end-year 2040 --scenario baseline --output both

# Custom battery parameters with delayed scenario
./run_forecast.sh --region Europe --battery-duration 8 --scenario delayed --output json
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--region` | Required | China, USA, Europe, Rest_of_World, Global |
| `--end-year` | 2040 | Forecast horizon |
| `--battery-duration` | 4 | Battery duration in hours (2, 4, or 8) |
| `--scenario` | baseline | Scenario: baseline, accelerated, delayed |
| `--output` | csv | csv, json, or both |

## Scenarios

| Scenario | Description | Cost Declines | Displacement Speed |
|----------|-------------|---------------|-------------------|
| **baseline** | Current policy trajectories | Solar: 8%/yr, Wind: 5%/yr, Battery: 10%/yr | 1.0× |
| **accelerated** | Faster transition with strong policy support | Solar: 12%/yr, Wind: 8%/yr, Battery: 15%/yr | 1.5× |
| **delayed** | Slower transition with incumbent advantages | Solar: 5%/yr, Wind: 3%/yr, Battery: 7%/yr | 0.7× |

Scenarios also affect:
- Carbon pricing (accelerated: 1.8×, delayed: 0.5×)
- Displacement speed multiplier
- Cost decline trajectories

## Forecasting Process

1. **Cost Analysis:** Calculate SWB stack cost (MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE) vs Coal/Gas LCOE with carbon pricing
2. **Tipping Point Detection:** Identify year when SWB cost < min(Coal_LCOE, Gas_LCOE) using 3-year rolling median smoothing
3. **Capacity Forecasting:** YoY growth averaging for Solar, Onshore Wind, Offshore Wind, Battery Storage
4. **Battery Sizing:** Option B (historical trends) or Option A (resilience days heuristic) if no historical data
5. **CSP Handling:** Include CSP conditionally if capacity > 1% of Solar PV
6. **Generation Derivation:** Convert capacity to generation using regional capacity factors with additive improvement
7. **Peak Load Calculation:** Calculate peak load proxy from annual demand and regional load factors
8. **Displacement Sequencing:** Model coal-first or gas-first displacement by region with scenario speed multiplier
9. **Residual Allocation:** Calculate nuclear, hydro, and remaining fossil generation
10. **Emissions Tracking:** Calculate annual and cumulative CO2 emissions with avoided emissions vs baseline
11. **Validation:** Energy balance, capacity factor bounds, reserve floors, non-negativity

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

**JSON:** Includes cost analysis (tipping point, LCOE, SCOE), capacity forecasts, battery metrics (power, energy, throughput), generation forecasts (including peak load proxy), displacement timeline, emissions trajectory (annual, cumulative, avoided), carbon pricing, validation results

Files saved to: `output/{Region}_{EndYear}_{Scenario}.{format}`

## Examples

**Example 1: China baseline scenario (coal-first displacement)**
```bash
./run_forecast.sh --region China --scenario baseline --output csv
```

**Example 2: USA accelerated transition (gas-first displacement)**
```bash
./run_forecast.sh --region USA --end-year 2040 --scenario accelerated --output both
```

**Example 3: Europe delayed scenario with 8-hour battery**
```bash
./run_forecast.sh --region Europe --battery-duration 8 --scenario delayed --output json
```

**Example 4: Global aggregation across all scenarios**
```bash
./run_forecast.sh --region Global --scenario baseline --output json
./run_forecast.sh --region Global --scenario accelerated --output json
./run_forecast.sh --region Global --scenario delayed --output json
```

## Displacement Sequences by Region

| Region | Sequence | Rationale |
|--------|----------|-----------|
| China | Coal-first | High coal dependency, government policy |
| USA | Gas-first | Gas-heavy grid, coal already declining |
| Europe | Coal-first | Coal phase-out commitments |
| Rest_of_World | Coal-first | Default assumption |

## Dataset Limitations & Fallback Strategies

### Available Historical Data
✅ Solar PV LCOE (China, USA, Global)
✅ Onshore/Offshore Wind LCOE (China, USA, Global)
✅ Battery Storage costs and capacity
✅ Coal/Gas generation and capacity
✅ Wind/Solar capacity factors
✅ Electricity production/consumption
✅ Coal CO2 emissions (validation data)

### Missing Data with Fallbacks

❌ **Coal & Gas LCOE** - NO datasets available
- **Fallback:** Regional baseline values (2020) with annual cost escalation
- China Coal: $65/MWh growing at 1.5%/year
- USA Gas: $60/MWh growing at 1.2%/year
- See `config.json` → `fallback_lcoe_values` for complete regional values

❌ **Nuclear & Hydro Generation** - Limited or unavailable
- **Fallback Hierarchy:**
  1. Try loading actual generation data (if available)
  2. Derive from residual (Total - Fossil - SWB)
  3. Use regional percentage estimates (China: 20%, USA: 22%, Europe: 28%)
- See `config.json` → `non_swb_baseline_percentages`

❌ **Regional Capacity Factors** - Partial coverage
- **Fallback Hierarchy:**
  1. Historical CF data (if available)
  2. Regional defaults from config
  3. Global average
  4. Technology default (Solar: 0.15, Wind: 0.27)
- See `config.json` → `capacity_factors` → `fallback_hierarchy`

### Implications

- **Coal/Gas LCOE fallbacks** are reasonable industry estimates but less accurate than historical data
- **Tipping points** remain valid due to conservative assumptions (rising incumbent costs)
- **Non-SWB baseline** uses multiple fallback methods to minimize error
- **Validation** uses actual Coal emissions data (1975-2024) from Coal.json to verify calculations

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

