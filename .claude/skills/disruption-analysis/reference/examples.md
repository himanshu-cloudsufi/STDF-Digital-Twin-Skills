# Disruption Analysis Examples

This document provides concrete examples of using the disruption-analysis skill for various query types.

## Example 1: EV Impact on Oil Demand

### Query
"Based on EV disruption, when will oil demand peak?"

### Command
```bash
./run_analysis.sh --event "EV disruption" --region Global --forecasts-dir ./forecasts/
```

### Expected Behavior
1. Pattern matching identifies `ev_disrupts_oil`
2. Loads EV forecast from `forecasts/EV_Cars_Global.json`
3. Loads oil demand forecast from `forecasts/Oil_Demand_Transportation_Global.json`
4. Calculates displacement using conversion factor 2.5 barrels/day per 1000 vehicles
5. Identifies peak year when baseline oil demand is maximum
6. Finds milestone years (50%, 95% displacement)

### Sample Output
```json
{
  "event": "EV disruption",
  "region": "Global",
  "disruptor": "EV_Cars",
  "impacted": "Oil_Demand_Transportation",
  "conversion_factor": 2.5,
  "units": "barrels_per_day per 1000 vehicles",
  "milestones": {
    "peak_year": 2025,
    "peak_demand": 42000000,
    "50_percent_displacement": 2035,
    "95_percent_displacement": 2042,
    "near_complete_displacement": 2045
  },
  "summary": "EVs displace oil demand in transportation sector; Peak demand occurs in 2025; 50% displaced by 2035; 95% displaced by 2042"
}
```

### Interpretation
- **Oil demand peaks in 2025** (already happened or imminent)
- **By 2035**, EVs will have displaced 50% of oil demand for transportation
- **By 2042**, 95% displaced (oil becomes niche product)
- **By 2045**, near-complete displacement (residual demand <1%)

### Key Insight
Oil demand for transportation peaks **before** EV adoption reaches 50% market share, due to:
1. Declining ICE fleet demand
2. Improving EV efficiency (less oil displaced per EV)
3. Market saturation effects

---

## Example 2: Solar+Wind+Battery Displacing Coal

### Query
"When will SWB displace 100% of coal in China?"

### Command
```bash
./run_analysis.sh --event "SWB displaces coal" --region China --forecasts-dir ./forecasts/
```

### Expected Behavior
1. Pattern matching identifies `swb_displaces_coal`
2. Loads Solar, Wind, Battery forecasts (aggregates them)
3. Loads coal power generation forecast
4. Calculates 1:1 displacement (1 MWh SWB displaces 1 MWh coal)
5. Finds 100% displacement year

### Sample Output
```json
{
  "event": "SWB displaces coal",
  "region": "China",
  "disruptor": ["Solar_PV", "Onshore_Wind", "Battery_Storage"],
  "impacted": "Coal_Power_Generation",
  "conversion_factor": 1.0,
  "units": "MWh per MWh",
  "milestones": {
    "peak_year": 2023,
    "peak_demand": 5200,
    "50_percent_displacement": 2030,
    "95_percent_displacement": 2037,
    "100_percent_displacement": 2040
  },
  "summary": "Solar+Wind+Battery displaces coal power generation; Peak demand occurs in 2023; 50% displaced by 2030; 95% displaced by 2037; Complete displacement by 2040"
}
```

### Interpretation
- **Coal demand in China already peaked (2023)**
- **By 2030**, SWB displaces half of coal generation
- **By 2037**, 95% displaced
- **By 2040**, complete displacement (100%)

### Key Insight
China's coal displacement is **faster than global average** due to:
1. Massive SWB investment
2. Lower cost of solar/wind manufacturing in China
3. Policy support for clean energy infrastructure

---

## Example 3: Natural Gas Peak Detection

### Query
"Based on SWB disruption, when will natural gas demand peak in China?"

### Command
```bash
./run_analysis.sh --event "SWB displaces gas" --region China --forecasts-dir ./forecasts/
```

### Expected Behavior
1. Pattern matching identifies `swb_displaces_gas`
2. Loads SWB aggregated forecast
3. Loads natural gas generation forecast
4. Finds peak year for gas demand

### Sample Output
```json
{
  "event": "SWB displaces gas",
  "region": "China",
  "disruptor": ["Solar_PV", "Onshore_Wind", "Battery_Storage"],
  "impacted": "Natural_Gas_Power_Generation",
  "milestones": {
    "peak_year": 2028,
    "peak_demand": 1800,
    "50_percent_displacement": 2038,
    "95_percent_displacement": 2047
  },
  "summary": "Solar+Wind+Battery displaces natural gas power generation; Peak demand occurs in 2028; 50% displaced by 2038; 95% displaced by 2047"
}
```

### Interpretation
- **Gas peaks later than coal** (2028 vs. 2023)
- **Displacement is slower** (95% by 2047 vs. 2037 for coal)
- **Gas has lower baseline cost**, delays tipping point

### Key Insight
Natural gas serves as "bridge fuel" between coal and SWB:
1. Cheaper than coal, more expensive than SWB
2. Peaker plants retain value temporarily (flexible dispatch)
3. Eventually displaced by batteries with longer duration (8+ hours)

---

## Example 4: Lead Demand Peak (EV Impact)

### Query
"When is lead demand going to peak globally?"

### Command
```bash
./run_analysis.sh --event "EV impacts lead" --region Global --forecasts-dir ./forecasts/
```

### Expected Behavior
1. Pattern matching identifies `ev_impacts_lead`
2. Loads EV forecast
3. Loads lead demand forecast
4. Uses **negative conversion factor** (-12 kg per EV)
5. Calculates reduction in lead demand from EVs

### Sample Output
```json
{
  "event": "EV impacts lead",
  "region": "Global",
  "disruptor": "EV_Cars",
  "impacted": "Lead_Demand",
  "conversion_factor": -12.0,
  "units": "kg lead saved per EV (no starter battery)",
  "milestones": {
    "peak_year": 2026,
    "peak_demand": 12500000,
    "50_percent_displacement": 2040,
    "95_percent_displacement": 2055
  },
  "summary": "EVs reduce lead demand by eliminating starter batteries; Peak demand occurs in 2026; 50% displaced by 2040; 95% displaced by 2055"
}
```

### Interpretation
- **Lead demand peaks in 2026** (very soon)
- **Decline is slow** due to replacement cycle (ICE batteries every 3-4 years)
- **95% reduction takes until 2055** (long tail from existing ICE fleet)

### Key Insight
Commodity demand can peak **before** product sales peak because:
1. Replacement demand from existing fleet
2. Declining fleet size (ICE vehicles scrapped faster than replaced)
3. Long lifetime of installed base (15+ years for vehicles)

---

## Example 5: ICE Vehicle Peak

### Query
"When will all ICE engines be displaced globally?"

### Command
```bash
./run_analysis.sh --event "EV displaces ICE" --region Global --forecasts-dir ./forecasts/
```

### Expected Behavior
1. Pattern matching identifies `ev_disrupts_ice`
2. Loads EV and ICE forecasts
3. Finds when ICE sales → 0 (or near-zero)

### Sample Output
```json
{
  "event": "EV displaces ICE",
  "region": "Global",
  "disruptor": "EV_Cars",
  "impacted": "ICE_Cars",
  "conversion_factor": 1.0,
  "units": "vehicles per vehicle",
  "milestones": {
    "peak_year": 2024,
    "peak_demand": 82000000,
    "50_percent_displacement": 2031,
    "95_percent_displacement": 2039,
    "near_complete_displacement": 2042
  },
  "summary": "EVs directly displace ICE vehicles in passenger car market; Peak demand occurs in 2024; 50% displaced by 2031; 95% displaced by 2039"
}
```

### Interpretation
- **ICE sales peak in 2024** (global)
- **By 2031**, EVs outsell ICE (50% market share)
- **By 2039**, ICE sales <5% of market (niche/specialty only)
- **By 2042**, ICE sales effectively zero

### Key Insight
ICE sales peak coincides with cost parity (2023-2025), not 50% EV share. This demonstrates exponential nature of disruption:
1. Pre-tipping: slow EV adoption (early adopters)
2. At tipping: ICE sales peak
3. Post-tipping: rapid S-curve adoption (mainstream buyers)

---

## Example 6: Current State Query

### Query
"Has coal demand already peaked in Europe?"

### Command
```bash
./run_analysis.sh --event "SWB displaces coal" --region Europe --output text
```

### Expected Behavior
1. Loads coal demand data (historical + forecast)
2. Identifies peak year
3. Compares to current year (2025)
4. Returns yes/no answer with details

### Sample Output (Text Mode)
```
============================================================
Disruption Analysis: SWB displaces coal
Region: Europe
============================================================

Disruptor: ['Solar_PV', 'Onshore_Wind', 'Battery_Storage']
Impacted: Coal_Power_Generation
Conversion: 1.0 MWh per MWh

Summary:
  Solar+Wind+Battery displaces coal power generation; Peak demand occurred in 2018; 50% displaced by 2025; 95% displaced by 2032

Key Milestones:
  peak_year: 2018
  peak_demand: 980
  50_percent_displacement: 2025
  95_percent_displacement: 2032
  near_complete_displacement: 2035

Answer: YES, coal demand in Europe peaked in 2018 and is now in rapid decline.
```

### Interpretation
- **Coal peaked in 2018** (7 years ago)
- **Already past 50% displacement** (2025)
- **On track for near-complete displacement by 2035**

### Key Insight
Europe is **leading** global coal displacement due to:
1. High coal prices
2. Low solar/wind costs
3. Policy support (carbon pricing)
4. Aging coal infrastructure (natural retirements)

---

## Example 7: Multi-Region Comparison

### Query
"Compare when oil demand peaks in China vs. USA"

### Commands
```bash
./run_analysis.sh --event "EV disruption" --region China --output json > china_oil.json
./run_analysis.sh --event "EV disruption" --region USA --output json > usa_oil.json
```

### Expected Output

**China:**
```json
{
  "milestones": {
    "peak_year": 2023,
    "50_percent_displacement": 2032,
    "95_percent_displacement": 2038
  }
}
```

**USA:**
```json
{
  "milestones": {
    "peak_year": 2027,
    "50_percent_displacement": 2037,
    "95_percent_displacement": 2044
  }
}
```

### Interpretation
- **China peaks 4 years earlier** (2023 vs. 2027)
- **China displaces faster** (2038 vs. 2044 for 95%)
- **USA lags by ~6 years** across all milestones

### Key Insight
Regional variation driven by:
1. **China:** Faster EV adoption (policy + manufacturing)
2. **USA:** Larger ICE installed base, slower turnover
3. **Infrastructure:** China invested in charging earlier

---

## Example 8: Threshold Crossing

### Query
"When will EVs reach 95% market share globally?"

### Command
```bash
./run_analysis.sh --event "EV displaces ICE" --region Global --output text
```

### Sample Output
```
Key Milestones:
  peak_year: 2024
  50_percent_displacement: 2031
  95_percent_displacement: 2039

Answer: EVs will reach 95% market share globally in 2039 (14 years from now).
```

### Interpretation
- **95% EV share by 2039**
- **15 years from tipping (2024) to 95% adoption**
- Consistent with S-curve disruption timelines

---

## Error Handling Examples

### Example 9: Unknown Pattern

**Query:** "When will fusion power displace solar?"

**Output:**
```json
{
  "error": "Could not identify disruption pattern from: fusion power displace solar",
  "available_patterns": [
    "ev_disrupts_oil",
    "swb_displaces_coal",
    "swb_displaces_gas",
    "ev_impacts_lead",
    "ice_decline_impacts_oil",
    "ev_disrupts_ice",
    "solar_wind_displaces_fossil"
  ]
}
```

**Resolution:** Add new pattern to `disruption_mappings.json` or rephrase query using known patterns.

### Example 10: Missing Forecast Data

**Query:** "EV impact on cobalt demand"

**Output:**
```json
{
  "error": "Failed to load forecast data: File not found: forecasts/Cobalt_Demand_Global.json",
  "disruption_info": {
    "pattern_id": "ev_impacts_cobalt",
    "disruptor": "EV_Cars",
    "impacted": "Cobalt_Demand"
  }
}
```

**Resolution:**
1. Add cobalt demand forecast to forecasts directory, OR
2. Use internal estimation mode (no forecasts-dir flag)

---

## Usage Patterns

### Pattern 1: Peak Detection
**Use:** Find when demand/sales reaches maximum
**Queries:** "When will X peak?", "Has X already peaked?"
**Output:** Peak year + peak value

### Pattern 2: Threshold Crossing
**Use:** Find when metric crosses specific threshold
**Queries:** "When will X reach Y%?", "When 95% displaced?"
**Output:** Year when threshold first crossed

### Pattern 3: Displacement Timeline
**Use:** Full timeline of disruption impact
**Queries:** "How does X disrupt Y?", "Timeline of X displacement"
**Output:** Year-by-year displacement data + milestones

### Pattern 4: Comparative Analysis
**Use:** Compare disruption across regions/scenarios
**Queries:** "Compare X in China vs USA", "Which region peaks first?"
**Output:** Multiple analysis results for comparison

---

## Best Practices

1. **Use pre-computed forecasts** (Mode A) for accuracy
2. **Specify region** explicitly (avoid ambiguity)
3. **Use text output** for quick insights, JSON for detailed analysis
4. **Validate conversion factors** for custom disruption patterns
5. **Check historical data** for "already peaked" queries
6. **Compare regions** to understand variation
7. **Document assumptions** when sharing results

---

## Common Pitfalls

1. **Confusing sales peak with demand peak** (sales peak earlier due to replacement cycles)
2. **Ignoring regional variation** (China ≠ USA ≠ Europe)
3. **Extrapolating linearly** (disruptions are exponential, not linear)
4. **Forgetting lag effects** (commodity demand lags product sales)
5. **Assuming 100% displacement** (some niches may remain)

---

## Advanced Use Cases

### Sensitivity Analysis
Run multiple scenarios with different conversion factors:
```bash
# Conservative scenario
./run_analysis.sh --event "EV disruption" --conversion-factor 2.0 --region Global

# Aggressive scenario
./run_analysis.sh --event "EV disruption" --conversion-factor 3.0 --region Global
```

### Cascading Disruptions
Analyze multi-hop impacts (not yet automated):
1. EV → Oil demand (direct)
2. Oil demand → Petrochemical production (derived)
3. Petrochemical → Plastics industry (downstream)

### Uncertainty Quantification
Run Monte Carlo simulations with varying input forecasts:
```bash
for i in {1..100}; do
  ./run_analysis.sh --event "EV disruption" --forecasts-dir ./scenarios/scenario_$i/ --output json > results_$i.json
done
# Aggregate results to get confidence intervals
```

---

## References

- See `methodology.md` for algorithm details
- See `relationships.md` for conversion factor derivations
- See `../data/disruption_mappings.json` for pattern definitions
