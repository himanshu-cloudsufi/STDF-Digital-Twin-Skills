---
name: disruption-analysis
description: Analyze cross-market disruption impacts and displacement timelines by synthesizing product and commodity forecasts. Use when user asks about disruption, displacement, impact, peak years, threshold crossings, or questions like "when will EVs disrupt oil demand", "based on EV adoption when will oil peak", "when will solar+wind displace coal", "when 95% of coal displaced", "how will EVs affect oil", "impact of solar on coal", "when will ICE vehicles peak", "displacement timeline for gas power", "EV disruption of oil", "SWB displacing coal/gas", "when will [disruptor] displace [incumbent]", "based on [X] disruption when will [Y] peak", "when will [market] be disrupted", "compare disruption speed", "which peaks first", "timeline for displacement", "how fast will market be disrupted", "cascading effects", "secondary impacts", "cross-market influence". Handles known disruption mappings: EV→oil demand, Solar+Wind+Battery (SWB)→coal/gas power, EV→lead demand, ICE decline→oil decline, EV→ICE displacement, autonomous vehicles→transportation. Covers regions: China, USA, Europe, Rest_of_World, Global. Trigger keywords: disrupt, displace, impact, affect, influence, peak, threshold, decline, displacement timeline, cross-market, cascading, secondary effects, transformation, EV, solar, wind, battery, SWB, oil, coal, gas, ICE, 50% displaced, 95% displaced, 100% displaced, peak year, tipping point, 2040, 2050.
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

See [data/disruption_mappings.json](data/disruption_mappings.json) for:
- Known disruptor→incumbent relationships
- Conversion factors (e.g., 1 EV displaces X barrels oil/year)
- Regional variations

**Examples:**
```json
{
  "EV_disrupts_oil": {
    "disruptor": "EV_Cars",
    "impacted": "Oil_Demand_Transportation",
    "conversion_factor": 2.5,
    "units": "barrels_per_day per vehicle"
  },
  "SWB_displaces_coal": {
    "disruptor": ["Solar_PV", "Onshore_Wind", "Battery_Storage"],
    "impacted": "Coal_Power_Generation",
    "conversion_factor": 1.0,
    "units": "MWh_displaced per MWh_generated"
  }
}
```

## Input Formats

**Option 1: Pre-computed forecasts directory**
```bash
./run_analysis.sh --event "EV disruption" --impact "oil" --forecasts-dir ./forecasts/
```
Expects:
- `forecasts/EV_Cars_Global.json`
- `forecasts/oil_Global.json`

**Option 2: Inline forecast data**
```bash
./run_analysis.sh --event "EV disruption" --impact "oil" --ev-forecast ev_data.json --oil-forecast oil_data.json
```

**Option 3: No input (internal estimation)**
```bash
./run_analysis.sh --event "EV disruption" --impact "oil" --region Global
```
Uses built-in simple trend estimation (least accurate).

## Methodology

See [reference/methodology.md](reference/methodology.md) for:
- Displacement calculation algorithms
- Peak detection methods
- Threshold crossing analysis
- Confidence intervals (if data available)

## Examples

See [reference/examples.md](reference/examples.md)

## Terminology Guardrails

When presenting results, follow these guidelines:

**Use:**
- "transformation" or "disruption" (NOT "transition")
- "market-driven" (NOT "policy-driven")
- "exponential" (NOT "linear growth")
- "superabundance" and "zero marginal cost"
- "distributed" or "decentralized" systems

**Avoid:**
- "renewable energy", "sustainable", "green"
- "hydrogen economy", "grid parity", "energy transition"
- "intermittency", "net zero"
- "baseload power", "peak oil"

**Rationale:**
These terms reflect the speed, scale, and systemic nature of technological disruption driven by exponential cost curves and zero marginal cost economics.

**Communication Style:**
- Think exponentially, not linearly
- Focus on speed and scale (10-15 years to 80%+ adoption post-tipping)
- Be quantitative and bold (provide specific years, show the math)
- Avoid technical jargon in user-facing output
