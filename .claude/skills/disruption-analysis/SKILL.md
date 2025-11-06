---
name: disruption-analysis
description: >
  Analyze cross-market disruption impacts and displacement timelines. Use when user asks about disruption, displacement, impact, peak years, threshold crossings, questions like "when will EVs disrupt oil demand", "based on EV adoption when will oil peak", "when will solar+wind displace coal", "when 95% displaced", "how EVs affect oil", "ICE vehicles peak", "displacement timeline", "EV disruption of oil", "SWB displacing coal/gas", "when will [disruptor] displace [incumbent]", "based on [X] when will [Y] peak", "compare disruption speed", "which peaks first", "cascading effects", "cross-market influence". Handles: EV→oil, SWB→coal/gas, EV→lead, ICE→oil decline, EV→ICE, autonomous vehicles→transport. Regions: China, USA, Europe, Rest_of_World, Global. Keywords: disrupt, displace, impact, peak, threshold, decline, displacement timeline, cross-market, cascading, EV, solar, wind, battery, SWB, oil, coal, gas, ICE, 50% displaced, 95% displaced, peak year, tipping point. (project)
---

# Disruption Impact Analysis

## Quick Start

Analyze disruption impact:
```bash
./run_analysis.sh --event "EV disruption" --impact "oil demand" --region Global
```

## Use Cases

**Cross-market impacts:**
- EV adoption → oil demand peak
- Solar+Wind+Battery (SWB) → coal demand decline
- SWB → natural gas displacement
- Autonomous vehicles → parking demand collapse
- EVs → lead demand (ICE batteries)

**Threshold analysis:**
- "When will SWB displace 100% of coal?"
- "When will EV reach 95% market share?"
- "When will oil demand decline 50%?"

**Peak detection:**
- "Has coal demand already peaked in Europe?"
- "When will natural gas demand peak in China?"
- "When will ICE car demand peak globally?"

## Analysis Process

1. **Parse disruption event:**
   - Identify disruptor product(s)
   - Identify impacted market(s)
   - Load disruption relationship mapping

2. **Gather forecast data:**
   - Option A: Load pre-computed forecasts from input directory
   - Option B: Request Claude Code to provide forecast data
   - Option C: Run simplified internal estimates

3. **Calculate impact:**
   - Displacement rate = disruptor_adoption × conversion_factor
   - Impacted_demand = baseline - displacement
   - Detect peak year, threshold crossings

4. **Generate timeline:**
   - Current state (year N)
   - Tipping point year
   - 50% displacement year
   - 95% displacement year
   - 100% displacement year (if applicable)

5. **Return analysis report**

## Disruption Mappings

Known relationships include:
- **EV → Oil:** 2.5 barrels/day per 1000 vehicles
- **Solar+Wind+Battery → Coal/Gas:** 1:1 MWh displacement
- **EV → Lead:** -12 kg/vehicle (eliminates ICE batteries)
- **EV → ICE:** 1:1 vehicle displacement

See [data/disruption_mappings.json](data/disruption_mappings.json) for complete mappings and [reference/relationships.md](reference/relationships.md) for methodology.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--event` | Yes | Disruption event (e.g., "EV disruption") |
| `--impact` | Yes | Impacted market (e.g., "oil demand", "coal") |
| `--region` | Yes | China, USA, Europe, Rest_of_World, Global |
| `--output` | No | json, text (default: json) |

The skill uses internal trend estimation by default. For higher accuracy, first generate forecasts with product-demand or commodity-demand skills.

## Examples

**EV disruption of oil demand:**
```bash
./run_analysis.sh --event "EV disruption" --impact "oil demand" --region Global
```

**Solar+Wind+Battery displacing coal:**
```bash
./run_analysis.sh --event "SWB displacement" --impact "coal" --region China --output json
```

See [reference/examples.md](reference/examples.md) for detailed analysis examples.

## Reference Documentation

- [reference/methodology.md](reference/methodology.md) - Displacement algorithms and peak detection
- [reference/relationships.md](reference/relationships.md) - Known disruption relationships
- [reference/examples.md](reference/examples.md) - Detailed analysis examples
- [data/disruption_mappings.json](data/disruption_mappings.json) - Complete mappings data

**Note:** For terminology guidelines, see CLAUDE.md in repository root.
