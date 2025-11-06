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

**Metals:** Copper, Lithium, Lead, Cobalt, Aluminum, Nickel
**Energy:** Oil, Coal, Natural Gas

See [reference/intensity_factors.md](reference/intensity_factors.md) for applications and intensity factors.

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

The skill uses built-in lightweight product trend analysis (linear extrapolation of historical demand). For higher accuracy, use the product-demand skill first, then reference those forecasts.

## Key Concepts

**Intensity Factor:** Quantity of commodity per product unit (e.g., 80 kg copper/EV, 12 kg lead/ICE battery)

**Replacement Cycle:** Component lifetime before replacement (e.g., 3-4 years for lead batteries, 10-15 years for EV batteries)

**Installed Base:** `Cumulative_sales - Cumulative_retirements` based on product lifetime

See reference documentation for complete tables.

## Examples

**Copper demand from EV adoption:**
```bash
./run_forecast.sh --commodity copper --region China --end-year 2040
```

**Lead demand (ICE battery replacements):**
```bash
./run_forecast.sh --commodity lead --region Global --output json
```

See [reference/examples.md](reference/examples.md) for detailed examples.

## Reference Documentation

- [reference/methodology.md](reference/methodology.md) - Demand calculation algorithms
- [reference/intensity_factors.md](reference/intensity_factors.md) - Complete intensity factor table
- [reference/replacement_cycles.md](reference/replacement_cycles.md) - Component lifetime data
- [reference/examples.md](reference/examples.md) - Detailed usage examples

**Note:** For terminology guidelines, see CLAUDE.md in repository root.
