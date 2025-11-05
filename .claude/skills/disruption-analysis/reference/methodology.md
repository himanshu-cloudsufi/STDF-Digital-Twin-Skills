# Disruption Analysis Methodology

## Overview

The disruption analysis skill synthesizes product and commodity forecasts to analyze cross-market impacts, displacement timelines, and peak demand detection. The methodology follows these core principles:

1. **Market-driven transformation** - Focus on economics and cost curves, not policy
2. **Exponential adoption** - Post-tipping, disruptions follow S-curves (not linear)
3. **Systemic impacts** - Disruptions cascade across multiple markets
4. **Quantitative precision** - Provide specific years and magnitudes

## Core Algorithms

### 1. Disruption Pattern Matching

**Input:** Natural language query (e.g., "When will EVs disrupt oil demand?")

**Process:**
1. Extract keywords from query (lowercase, tokenize)
2. Match against known disruption patterns in `disruption_mappings.json`
3. Score each pattern by number of keyword matches
4. Select pattern with highest score (minimum 1 match required)

**Output:** Disruption metadata (disruptor, impacted, conversion_factor)

### 2. Displacement Calculation

**Input:**
- Disruptor forecast: `{years: [2020, 2021, ...], demand: [d1, d2, ...]}`
- Impacted forecast: `{years: [2020, 2021, ...], demand: [i1, i2, ...]}`
- Conversion factor: `c` (units: disruptor per impacted)

**Algorithm:**
```
For each year t in common_years:
    disruptor_level[t] = forecast_disruptor[t]
    baseline_demand[t] = forecast_impacted[t]

    displaced[t] = disruptor_level[t] × conversion_factor
    remaining[t] = max(0, baseline_demand[t] - displaced[t])
    displacement_rate[t] = displaced[t] / baseline_demand[t]

    # Clamp displacement_rate to [0, 1]
    displacement_rate[t] = min(1.0, max(0, displacement_rate[t]))
```

**Notes:**
- Negative conversion factors indicate inverse relationships (e.g., EVs reduce lead demand)
- Remaining demand is clamped to non-negative values
- Displacement rate represents fraction of incumbent displaced (0 = none, 1 = complete)

### 3. Peak Detection

**Input:** Time series of baseline demand `{year: demand}`

**Algorithm:**
```python
peak_year = argmax(baseline_demand)
peak_value = baseline_demand[peak_year]
```

**Notes:**
- Peak detection uses baseline demand, not remaining demand
- If demand is monotonically increasing, peak is at end of forecast horizon
- If demand is monotonically decreasing, peak is at start (historical)

### 4. Threshold Crossing Detection

**Input:**
- Displacement timeline
- Thresholds: [0.50, 0.95, 1.00] (50%, 95%, 100% displacement)

**Algorithm:**
```python
for threshold in [0.50, 0.95, 1.00]:
    for year, data in timeline:
        if data['displacement_rate'] >= threshold:
            milestones[f'{threshold*100}_percent'] = year
            break
```

**Notes:**
- First year crossing threshold is recorded
- If threshold never crossed, milestone is omitted
- Near-complete displacement: <1% remaining demand

## Forecast Data Sources

The skill supports three modes for obtaining forecast data:

### Mode A: Pre-computed Forecasts (Recommended)

**Usage:**
```bash
./run_analysis.sh --event "EV disruption" --forecasts-dir ./forecasts/
```

**Expected files:**
- `forecasts/{product}_{region}.json` for each product

**Advantages:**
- Most accurate (uses full disruption analysis from product-demand skill)
- Includes tipping point analysis, S-curve fitting
- Supports complex multi-product aggregation (e.g., SWB = Solar + Wind + Battery)

### Mode B: Inline Forecast Files

**Usage:**
```bash
./run_analysis.sh --event "EV disruption" --ev-forecast ev.json --oil-forecast oil.json
```

**Advantages:**
- Flexible for custom forecast scenarios
- Good for sensitivity analysis

### Mode C: Internal Estimation (Fallback)

**Usage:**
```bash
./run_analysis.sh --event "EV disruption" --region Global
```

**Behavior:**
- Uses simple linear extrapolation of historical trends
- No disruption/tipping point analysis
- Least accurate, but always available

**When to use:**
- Quick exploratory analysis
- No pre-computed forecasts available
- Current state queries (historical data only)

## Multi-Product Aggregation

For disruptions involving multiple products (e.g., SWB = Solar + Wind + Battery):

**Algorithm:**
```python
def aggregate_forecasts(forecasts):
    years = forecasts[0]['years']
    aggregated_demand = zeros(len(years))

    for forecast in forecasts:
        aggregated_demand += forecast['demand']

    return {
        'years': years,
        'demand': aggregated_demand,
        'aggregated_from': [f['product'] for f in forecasts]
    }
```

**Notes:**
- All forecasts must share the same year range
- Demand is summed (assumes independent contributions)
- Metadata tracks which products were aggregated

## Validation and Quality Checks

### Input Validation
- [ ] Region is valid (China, USA, Europe, Rest_of_World, Global)
- [ ] Event description matches at least one disruption pattern
- [ ] Forecast data available for both disruptor and impacted
- [ ] Years overlap between disruptor and impacted forecasts

### Output Validation
- [ ] All displacement rates in [0, 1]
- [ ] Remaining demand ≥ 0
- [ ] Peak year within forecast range
- [ ] Milestones in chronological order

### Edge Cases
- **No pattern match:** Return error with available patterns
- **No overlapping years:** Return error specifying year ranges
- **Missing forecast data:** Fall back to internal estimation with warning
- **Conversion factor = 0:** Return error (invalid mapping)

## Assumptions and Limitations

### Assumptions
1. **Linear displacement:** 1 unit of disruptor displaces `c` units of incumbent
2. **No feedback loops:** Displacement doesn't affect disruptor adoption rate
3. **Static conversion factors:** Conversion factors don't change over time
4. **Regional independence:** No cross-region spillover effects

### Limitations
1. **No uncertainty quantification:** Results are deterministic, no confidence intervals
2. **No policy scenarios:** Assumes market-driven forces only
3. **Simplified aggregation:** Multi-product disruptions use simple summation
4. **No second-order effects:** E.g., cheaper oil from reduced demand doesn't slow EV adoption

## Output Schema

### JSON Output Structure
```json
{
  "event": "EV disruption",
  "region": "Global",
  "disruptor": "EV_Cars",
  "impacted": "Oil_Demand_Transportation",
  "conversion_factor": 2.5,
  "units": "barrels_per_day per 1000 vehicles",
  "displacement_timeline": [
    {
      "year": 2020,
      "disruptor_level": 1000000,
      "baseline_demand": 5000000,
      "displaced_demand": 2500,
      "remaining_demand": 4997500,
      "displacement_rate": 0.0005
    },
    ...
  ],
  "milestones": {
    "peak_year": 2025,
    "peak_demand": 5200000,
    "50_percent_displacement": 2035,
    "95_percent_displacement": 2042,
    "near_complete_displacement": 2045
  },
  "summary": "EVs displace oil demand in transportation sector; Peak demand occurs in 2025; 50% displaced by 2035; 95% displaced by 2042"
}
```

## Performance Characteristics

- **Time complexity:** O(n) where n = number of forecast years
- **Space complexity:** O(n) for timeline storage
- **Typical runtime:** <1 second for single disruption analysis
- **Scalability:** Can analyze 100+ years of data efficiently

## References

- Disruption mappings: `../data/disruption_mappings.json`
- Configuration: `../config.json`
- Self-contained utilities: `../scripts/lib/` (utils.py, validators.py)
