---
name: commodity-demand
description: >
  Forecast commodity demand driven by product sales and component replacement cycles. Handles copper, lithium, lead, cobalt, aluminum, nickel (batteries/motors), oil, coal, natural gas (energy). Use when user asks about commodity demand, material requirements, supply needs, peak demand years, questions like "when will lithium demand peak", "copper demand for EVs in 2035", "forecast copper demand driven by vehicles", "oil demand for transportation", "coal demand peak", "lithium supply for batteries", "material needs for EV production", "copper per EV", "replacement demand". Calculates demand from BOTH new sales AND installed base replacements. Regions: China, USA, Europe, Rest_of_World, Global. Keywords: commodity, material, metal, resource, supply, demand, peak, copper, lithium, lead, cobalt, aluminum, nickel, oil, coal, gas, battery materials, mining, intensity, replacement, installed base. (project)
---

# Commodity Demand Forecasting

## Quick Start

Forecast commodity demand:
```bash
./run_forecast.sh --commodity "lead" --region Global --end-year 2040 --output json
```

## Available Commodities

**Metals:**
- Copper (EVs, motors, infrastructure)
- Lithium (batteries)
- Lead (ICE batteries, UPS, datacenters)
- Cobalt (batteries)
- Aluminum (vehicle bodies, conductors)
- Nickel (batteries)

**Energy:**
- Oil (transportation fuel)
- Coal (power generation)
- Natural Gas (power generation, heating)

For complete list and applications, see [reference/commodities_catalog.md](reference/commodities_catalog.md)

## Forecasting Process

1. **Identify contributing products**
   - Load commodity→products mapping
   - Get top 80% contributors by volume

2. **For each product, calculate:**
   - **New sales demand:** `product_units × intensity_factor`
   - **Replacement demand:** `installed_base × replacement_rate × intensity_factor`

3. **Aggregate across all products**
   - Sum new sales demand
   - Sum replacement demand
   - Total = new + replacement

4. **Validate and return forecast**

## Product Demand Estimation

**If product forecast files provided:**
```bash
./run_forecast.sh --commodity lead --region China --product-forecasts-dir ./product_outputs/
```
Uses pre-computed product forecasts (more accurate).

**Otherwise:**
Uses built-in lightweight product trend analysis:
- Linear extrapolation of historical product demand
- No disruption/tipping point analysis (faster, less accurate)

## Intensity Factors

Intensity = quantity of commodity per product unit

**Examples:**
- Copper in EV: 80 kg/vehicle
- Copper in ICE: 20 kg/vehicle
- Lithium in EV battery: 8 kg/kWh × 60 kWh = 480 kg/vehicle
- Lead in ICE battery: 12 kg/vehicle

See [reference/intensity_factors.md](reference/intensity_factors.md) for complete table.

## Replacement Cycles

**Examples:**
- Lead battery in ICE car: 3-4 year replacement cycle
- EV battery pack: 10-15 year replacement cycle
- Industrial motors: 15-20 year replacement cycle

See [reference/replacement_cycles.md](reference/replacement_cycles.md) for complete table.

## Installed Base Calculation

```
Installed_base(year) = Cumulative_sales - Cumulative_retirements
```

Retirement rate based on product lifetime (e.g., 15 years for vehicles).

## Methodology

See [reference/methodology.md](reference/methodology.md) for:
- Product demand estimation methods
- Intensity factor derivation
- Replacement cycle modeling
- Installed base calculation

## Examples

See [reference/examples.md](reference/examples.md) for:
- Lead demand from ICE battery replacements
- Copper demand from EV sales
- Lithium demand forecast

## Terminology Guardrails

When presenting results, use:
- "transformation" or "disruption" (NOT "transition")
- "market-driven" (NOT "policy-driven")
- "exponential" (NOT "linear growth")
- "superabundance" and "zero marginal cost" (NOT "sustainability" or "efficiency")

Avoid: "renewable energy", "sustainable", "green", "hydrogen economy", "grid parity"
