# Commodity Demand Forecasting Examples

## Overview

This document provides practical examples of using the commodity demand forecasting skill for various use cases.

---

## Example 1: Lead Demand from ICE Battery Replacements

### Scenario
Analyze lead demand driven by the installed base of ICE vehicles requiring battery replacements.

### Command
```bash
./run_forecast.sh --commodity lead --region Global --end-year 2040 --output both
```

### Key Insights

**Contributing Products:**
- ICE passenger cars (12 kg lead per battery)
- PHEV cars (12 kg lead for 12V auxiliary)
- Commercial ICE vehicles (18 kg lead per battery)

**Demand Components:**

1. **New Sales Demand:**
   - Declining as ICE sales drop post-EV tipping point
   - PHEV sales provide temporary demand bridge

2. **Replacement Demand:**
   - Dominant component (installed base of 1+ billion vehicles)
   - 3.5-year replacement cycle = ~286 million batteries/year
   - Peaks before declining installed base overwhelms replacement rate

**Expected Peak:** 2025-2028
- ICE fleet peaks
- Replacement cycles maintain high demand
- After peak: Declining fleet → declining replacement demand

**Result Interpretation:**
```
Lead Demand Forecast (Global)

Peak Year: 2027
Peak Demand: 12.5 million tonnes

Breakdown at Peak:
- New Sales: 2.8 million tonnes (22%)
- Replacement: 9.7 million tonnes (78%)

Post-Peak Decline:
- 2027-2035: -4% per year (ICE fleet shrinking)
- 2035-2040: -6% per year (accelerating decline)
```

---

## Example 2: Copper Demand from EV Sales

### Scenario
Forecast copper demand from electric vehicle production and installed base.

### Command
```bash
./run_forecast.sh --commodity copper --region China --end-year 2040 --output json
```

### Key Insights

**Contributing Products:**
- EV passenger cars (80 kg copper per vehicle)
- Commercial EVs (120 kg per vehicle)
- ICE cars still contribute (20 kg per vehicle, declining)
- PHEVs bridge product (40 kg per vehicle)

**Demand Components:**

1. **New Sales Demand:**
   - Dominant component (EVs don't have copper component replacements)
   - Grows exponentially post-tipping point (~2023 in China)
   - S-curve adoption drives rapid increase 2023-2035

2. **Replacement Demand:**
   - Minimal (electric motors last vehicle lifetime)
   - Wiring never replaced

**Expected Pattern:** Continuous Growth
- No peak through 2040
- EV sales continue growing
- Offset by declining ICE copper content

**Result Interpretation:**
```
Copper Demand Forecast (China, EV sector)

2023: 1.2 million tonnes
2030: 3.5 million tonnes
2040: 6.2 million tonnes

CAGR 2023-2040: 9.8%

Breakdown (2030):
- EV New Sales: 3.0 million tonnes (86%)
- PHEV New Sales: 0.3 million tonnes (9%)
- ICE New Sales: 0.2 million tonnes (5%)
- Replacement: 0 tonnes (0%)
```

---

## Example 3: Lithium Demand Forecast

### Scenario
Forecast lithium demand for EV batteries, including both new sales and battery pack replacements.

### Command
```bash
./run_forecast.sh --commodity lithium --region Global --end-year 2050 --output both
```

### Key Insights

**Contributing Products:**
- EV passenger cars (8 kg/kWh × 60 kWh = 480 kg per vehicle)
- PHEVs (3 kg/kWh × 15 kWh = 45 kg per vehicle)
- Commercial EVs (12 kg/kWh × 200 kWh = 2,400 kg per vehicle)
- Battery storage systems (0.15 kg/kWh)

**Demand Components:**

1. **New Sales Demand:**
   - Dominant through 2040
   - Exponential growth phase

2. **Replacement Demand:**
   - Begins ramping up 2030-2035 (12-year battery life)
   - Early EV batteries (2018-2023) start retiring
   - Becomes significant component by 2035

**Expected Pattern:** Growth with Slowdown
- Rapid growth 2023-2035 (S-curve steep phase)
- Slower growth 2035-2050 (market saturation)
- Replacement demand increases as installed base ages

**Result Interpretation:**
```
Lithium Demand Forecast (Global)

2023: 450,000 tonnes
2030: 1.2 million tonnes
2035: 2.1 million tonnes
2040: 2.8 million tonnes (peak growth rate)
2050: 3.5 million tonnes

Breakdown (2035):
- EV New Sales: 1.8 million tonnes (86%)
- EV Replacements: 0.2 million tonnes (9%)
- PHEV New Sales: 0.08 million tonnes (4%)
- Storage New Sales: 0.02 million tonnes (1%)

Replacement Demand Trajectory:
2030: 50,000 tonnes (4% of total)
2035: 200,000 tonnes (9% of total)
2040: 600,000 tonnes (21% of total)
2050: 1.2 million tonnes (34% of total)
```

**Key Finding:** Replacement demand becomes increasingly important after 2035.

---

## Example 4: Multi-Product Commodity Analysis (Copper)

### Scenario
Comprehensive copper demand across all contributing products: EVs, solar, wind, grid infrastructure.

### Command
```bash
./run_forecast.sh --commodity copper --region Global --end-year 2040 --output both
```

### Contributing Products Breakdown

**Transportation (60% of total):**
- EV Cars: 80 kg/vehicle
- Commercial EV: 120 kg/vehicle
- ICE Cars: 20 kg/vehicle (declining)

**Energy Generation (25% of total):**
- Solar PV: 5.5 kg/kW
- Onshore Wind: 4.0 kg/kW
- Offshore Wind: 6.0 kg/kW

**Grid Infrastructure (15% of total):**
- Transmission lines
- Distribution systems
- Charging infrastructure

**Result Interpretation:**
```
Copper Demand Forecast (Global, All Sectors)

2023: 12 million tonnes
2030: 18 million tonnes
2040: 28 million tonnes

CAGR 2023-2040: 5.2%

Breakdown by Sector (2030):
Transportation:
  - EV New Sales: 6.5 million tonnes (36%)
  - ICE New Sales: 2.0 million tonnes (11%)

Energy Generation:
  - Solar PV: 2.8 million tonnes (16%)
  - Wind: 1.5 million tonnes (8%)

Grid & Other: 5.2 million tonnes (29%)

Peak Forecast: No peak expected through 2040
  - EV growth continues
  - Solar/wind deployment accelerating
  - Grid expansion ongoing
```

---

## Example 5: Oil Demand Impact from EV Disruption

### Scenario
Calculate reduced oil demand as EVs displace ICE vehicles.

### Notes
This example requires integration with the `disruption-analysis` skill for full analysis. Here we show the commodity perspective.

### Command
```bash
# First, run EV forecast
cd .claude/skills/product-demand
./run_forecast.sh --product "EV_Cars" --region Global --end-year 2040 --output json

# Then, analyze oil impact
cd ../commodity-demand
./run_forecast.sh --commodity oil --region Global --end-year 2040 --product-forecasts-dir ../product-demand/output
```

### Key Insights

**ICE Vehicle Oil Consumption:**
- Average ICE car: 2.5 barrels/day per 1,000 vehicles
- Annual: 2.5 × 365 = 912 barrels/year per 1,000 vehicles
- Per vehicle: 0.912 barrels/day = ~380 gallons/year

**Displacement Calculation:**
```
Oil_Displaced = ICE_Vehicles_Replaced × Oil_Per_Vehicle

Example (2030):
- EVs on road: 200 million globally
- Oil displaced: 200M × 0.912 barrels/day = 182 million barrels/day
- Percentage of global demand: 182 / 100 = 182% of daily production

NOTE: Numbers illustrative, actual calculation more nuanced
```

**Expected Pattern:** Peak then Decline
- Oil demand for transportation peaks 2025-2028
- Post-peak decline: -3% to -5% per year
- By 2040: Oil demand 40-50% below peak

---

## Example 6: Comparing New Sales vs. Replacement Demand

### Scenario
Analyze the crossover point when replacement demand exceeds new sales demand.

### Example: Lead in ICE Batteries

**2023 Breakdown:**
```
ICE Fleet: 1.2 billion vehicles
ICE Sales: 60 million vehicles/year
Replacement Cycle: 3.5 years

New Sales Demand:
60M vehicles × 12 kg = 720,000 tonnes

Replacement Demand:
1,200M vehicles × (1/3.5) × 12 kg = 4,114,000 tonnes

Replacement / New Sales Ratio: 5.7x
```

**Observation:** For mature markets with large installed base, replacement demand dominates.

### Example: Lithium in EV Batteries

**2023 Breakdown:**
```
EV Fleet: 25 million vehicles
EV Sales: 10 million vehicles/year
Replacement Cycle: 12 years

New Sales Demand:
10M vehicles × 480 kg = 4,800,000 tonnes

Replacement Demand:
25M vehicles × (1/12) × 480 kg = 1,000,000 tonnes

Replacement / New Sales Ratio: 0.21x
```

**Observation:** For rapidly growing markets, new sales demand dominates initially.

**Crossover Point:**
When does EV replacement demand exceed new sales demand?

```
Crossover occurs when:
Fleet_Size / Replacement_Cycle > Annual_Sales

For EVs:
If sales stabilize at 100M/year
Fleet saturates at ~1.5 billion vehicles
Replacement demand = 1,500M / 12 = 125M vehicles/year
Crossover year: ~2045-2050
```

---

## Example 7: Regional Comparison

### Scenario
Compare copper demand from EVs across different regions.

### Commands
```bash
./run_forecast.sh --commodity copper --region China --end-year 2040 --output csv
./run_forecast.sh --commodity copper --region USA --end-year 2040 --output csv
./run_forecast.sh --commodity copper --region Europe --end-year 2040 --output csv
```

### Expected Results

**China:**
- Largest absolute demand
- Earliest tipping point (2023)
- Fastest growth rate (12% CAGR 2023-2030)
- Peaks later (~2040+)

**USA:**
- Slower adoption
- Later tipping point (2025-2026)
- Moderate growth (8% CAGR 2023-2030)
- Larger vehicles = more copper per EV

**Europe:**
- Medium adoption speed
- Tipping point (2024)
- Moderate growth (9% CAGR 2023-2030)
- Smaller vehicles = less copper per EV

**Regional Intensity Variations:**
```
Average EV Copper Content:
- China: 75 kg (smaller vehicles, LFP batteries)
- USA: 90 kg (larger vehicles, NMC batteries)
- Europe: 80 kg (medium vehicles, mixed batteries)
```

---

## Example 8: Sensitivity Analysis (Manual)

### Scenario
Understand how different parameters affect commodity demand forecasts.

### Parameter: Battery Replacement Cycle

**Base Case: 12-year replacement**
```
2040 Lithium Replacement Demand: 600,000 tonnes
```

**Scenario A: 10-year replacement (faster degradation)**
```
2040 Lithium Replacement Demand: 720,000 tonnes (+20%)
```

**Scenario B: 15-year replacement (better batteries)**
```
2040 Lithium Replacement Demand: 480,000 tonnes (-20%)
```

**Impact:** ±20% variation in replacement demand from ±2 year cycle change.

### Parameter: Intensity Factor

**Base Case: 8 kg Li/kWh**
```
2040 Lithium New Sales Demand: 1,800,000 tonnes
```

**Scenario A: 6 kg Li/kWh (higher energy density)**
```
2040 Lithium New Sales Demand: 1,350,000 tonnes (-25%)
```

**Scenario B: 10 kg Li/kWh (lower energy density)**
```
2040 Lithium New Sales Demand: 2,250,000 tonnes (+25%)
```

**Impact:** Linear relationship between intensity and demand.

---

## Best Practices

### 1. Use Pre-Computed Product Forecasts
For highest accuracy, run `product-demand` skill first, then pass results:

```bash
# Step 1: Product forecast
cd .claude/skills/product-demand
./run_forecast.sh --product "EV_Cars" --region China --end-year 2040 --output json --output-dir ./output

# Step 2: Commodity forecast with product data
cd ../commodity-demand
./run_forecast.sh --commodity copper --region China --end-year 2040 --product-forecasts-dir ../product-demand/output
```

### 2. Validate Against Known Data
Check 2023 estimates against actual reported consumption:
- Lithium: ~450,000 tonnes (actual) vs forecast
- Copper: ~12 million tonnes (actual) vs forecast
- Lead: ~12 million tonnes (actual) vs forecast

### 3. Consider Recycling
Remember that forecasts show primary demand. Actual supply needs are lower due to recycling:
- Lead: ~99% recycling rate
- Copper: ~30% recycling rate
- Aluminum: ~75% recycling rate
- Lithium: ~5% recycling rate (growing rapidly)

### 4. Watch for Peak Demand
- **Lead**: Peaked ~2025-2028, declining thereafter
- **Oil (transport)**: Peaking 2025-2030
- **Copper**: No peak expected through 2040
- **Lithium**: Growth slows 2035-2040 but no peak

### 5. Understand Limitations
- Fixed intensity factors (no lightweighting trends)
- Simplified product forecasts without full disruption analysis
- No feedback loops (price impacts)
- No recycling integration

---

## Troubleshooting Common Issues

### Issue: "Commodity not found"
**Cause:** Commodity name not in intensity_factors.json
**Solution:** Check available commodities in SKILL.md, use exact name (case-insensitive)

### Issue: "No data available for product"
**Cause:** Product forecast not found and no historical data to estimate
**Solution:** Provide pre-computed product forecast or add historical data files

### Issue: Unrealistic demand growth
**Cause:** Likely missing CAGR cap in product estimation
**Solution:** Use pre-computed product forecasts from `product-demand` skill

### Issue: Peak year seems wrong
**Cause:** Insufficient data or incorrect replacement cycles
**Solution:** Verify replacement cycle values, check installed base calculation

---

## Next Steps

After running commodity forecasts:

1. **Cross-validate** with `disruption-analysis` skill
2. **Compare** across regions for consistency
3. **Analyze** implications for supply chains
4. **Identify** potential bottlenecks or oversupply
5. **Communicate** results using terminology guardrails (transformation, not transition)
