---
name: disruption-analysis
description: Analyze cross-market disruption impacts and displacement timelines. Synthesizes product and commodity forecasts to answer questions about disruption, displacement, and peak demand years. Use when user asks "when will [disruptor] displace [incumbent]", "based on [X] disruption when will [Y] peak", "when will [market] be disrupted", or requests disruption analysis, displacement timelines, or threshold crossings (e.g., "when 95% displaced"). Handles EV disrupting oil demand, SWB disrupting coal/gas, autonomous vehicles disrupting transportation, etc.
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
