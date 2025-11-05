# Demand Forecasting Skills Architecture - Detailed Implementation Plan

**Date:** 2025-11-04
**Project:** Tony Seba STDF Framework - Multi-Product Demand Forecasting
**Goal:** Create three independent skills (product-demand, commodity-demand, disruption-analysis) with shared library

---

## Executive Summary

### The Problem
Current implementation:
- Single `demand-forecasting` skill focused only on EV passenger vehicles
- Need to support 3 use cases across 20+ product entities and commodities
- 42 test queries spanning products, commodities, and disruption analysis

### The Solution
Three independent skills + shared library:
1. **product-demand** - Generic product forecasting (EVs, solar, wind, commercial vehicles, etc.)
2. **commodity-demand** - Commodity forecasting with sales + replacement logic (copper, lithium, lead, oil, etc.)
3. **disruption-analysis** - Cross-market disruption impact analysis (EV→oil, SWB→coal/gas)

### Key Constraint
**Skills cannot call other skills.** Each must be self-contained. Claude Code orchestrates multi-skill workflows.

### Timeline
**10-13 days total**
- Phase 1 (Shared Library): 2 days
- Phase 2 (Product Skill): 2-3 days
- Phase 3 (Commodity Skill): 2-3 days
- Phase 4 (Disruption Skill): 2 days
- Phase 5 (Integration Testing): 1-2 days
- Phase 6 (Refinement): 1 day

---

## Architecture Overview

```
.claude/skills/
├── _forecasting_core/                    # Shared Python library (NOT a skill)
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── utils.py                      # Math utilities
│   │   ├── cost_analyzer.py              # Cost curves, tipping points
│   │   ├── logistic_models.py            # S-curve fitting
│   │   ├── data_loader.py                # JSON loading
│   │   └── validators.py                 # Consistency checks
│   └── README.md                         # Library documentation
│
├── demand-forecasting/                   # Existing EV skill (PRESERVE)
│   ├── SKILL.md
│   ├── config.json
│   ├── scripts/
│   │   ├── forecast.py
│   │   ├── data_loader.py
│   │   ├── cost_analysis.py
│   │   ├── demand_forecast.py
│   │   └── utils.py
│   └── data/
│       ├── Passenger_Cars.json
│       └── passenger_vehicles_taxonomy_and_datasets.json
│
├── product-demand/                       # NEW: Generic product forecasting
│   ├── SKILL.md                          # Main instructions
│   ├── config.json                       # Default parameters
│   ├── run_forecast.sh                   # Wrapper script
│   ├── scripts/
│   │   └── product_forecast.py           # Main orchestrator
│   ├── data/
│   │   ├── products_catalog_index.json   # Product→entity mapping
│   │   ├── Passenger_Cars.json           # 134 datasets
│   │   ├── Commercial_Vehicle.json       # 144 datasets
│   │   ├── Two_Wheeler.json              # 38 datasets
│   │   ├── Three_Wheeler.json            # 32 datasets
│   │   ├── Energy_Generation.json        # 138 datasets
│   │   ├── Energy_Storage.json           # 22 datasets
│   │   └── [10 more entity files]
│   └── reference/
│       ├── methodology.md                # Detailed algorithms
│       ├── data_schema.md                # JSON structure
│       ├── parameters.md                 # Parameter ranges
│       └── examples.md                   # Usage examples
│
├── commodity-demand/                     # NEW: Commodity forecasting
│   ├── SKILL.md
│   ├── config.json
│   ├── run_forecast.sh
│   ├── scripts/
│   │   └── commodity_forecast.py         # Main orchestrator
│   ├── data/
│   │   ├── commodities_catalog.json      # Commodity→products mapping
│   │   ├── Copper.json                   # 48 datasets
│   │   ├── Aluminium.json                # 44 datasets
│   │   ├── Lead.json                     # 5 datasets
│   │   ├── Lithium.json                  # TBD datasets
│   │   ├── Cobalt.json                   # TBD datasets
│   │   ├── Oil.json                      # TBD datasets
│   │   ├── Coal.json                     # TBD datasets
│   │   ├── Natural_Gas.json              # TBD datasets
│   │   └── commodity_intensity.json      # kg per product unit
│   └── reference/
│       ├── methodology.md
│       ├── intensity_factors.md          # Detailed intensity data
│       └── examples.md
│
└── disruption-analysis/                  # NEW: Disruption impact
    ├── SKILL.md
    ├── config.json
    ├── run_analysis.sh
    ├── scripts/
    │   └── disruption_impact.py          # Main orchestrator
    ├── data/
    │   └── disruption_mappings.json      # Disruptor→incumbent relationships
    └── reference/
        ├── methodology.md
        ├── relationships.md              # Known disruption patterns
        └── examples.md
```

---

## Phase 1: Build Shared Library (2 days)

### Goal
Extract reusable code from existing `demand-forecasting` skill into a shared library that all new skills can import.

### Tasks

#### 1.1 Create Directory Structure
```bash
mkdir -p .claude/skills/_forecasting_core/core
touch .claude/skills/_forecasting_core/__init__.py
touch .claude/skills/_forecasting_core/core/__init__.py
touch .claude/skills/_forecasting_core/README.md
```

#### 1.2 Extract `utils.py` (100% reusable - copy as-is)
**Source:** `.claude/skills/demand-forecasting/scripts/utils.py`
**Destination:** `.claude/skills/_forecasting_core/core/utils.py`

**Functions to include:**
- `rolling_median(data, window)` - Smoothing filter
- `calculate_cagr(values, years)` - Compound growth rate
- `theil_sen_slope(x, y)` - Robust linear regression
- `linear_extrapolation(years, values, end_year, max_cagr)` - Trend extension
- `log_cagr_forecast(years, costs, end_year)` - Exponential cost decline
- `clamp(value, min_val, max_val)` - Bounds enforcement
- `clamp_array(arr, min_val, max_val)` - Array bounds
- `find_intersection(years, series1, series2)` - Crossover detection
- `validate_forecast_consistency(market, bev, phev, ice)` - Sum validation

**No changes needed** - these are pure mathematical utilities.

#### 1.3 Create `cost_analyzer.py` (Generalized)
**Source:** `.claude/skills/demand-forecasting/scripts/cost_analysis.py`
**Destination:** `.claude/skills/_forecasting_core/core/cost_analyzer.py`

**Refactoring needed:**
```python
# Before (EV-specific):
class CostAnalyzer:
    def __init__(self, data_loader):
        self.ev_cost = data_loader.get_cost_data("EV_Cars", region)
        self.ice_cost = data_loader.get_cost_data("ICE_Cars", region)

# After (generic):
class CostAnalyzer:
    def __init__(self, disruptor_cost_data, incumbent_cost_data):
        """
        Args:
            disruptor_cost_data: tuple of (years, costs)
            incumbent_cost_data: tuple of (years, costs)
        """
        self.disruptor_years, self.disruptor_costs = disruptor_cost_data
        self.incumbent_years, self.incumbent_costs = incumbent_cost_data
```

**Functions:**
- `prepare_cost_curves()` - Smooth and forecast costs
- `find_tipping_point()` - Detect cost parity year
- `analyze_cost_trajectory()` - Calculate CAGRs
- `smooth_and_forecast_cost()` - Apply rolling median + log CAGR

#### 1.4 Create `logistic_models.py`
**Source:** Extract from `.claude/skills/demand-forecasting/scripts/demand_forecast.py`
**Destination:** `.claude/skills/_forecasting_core/core/logistic_models.py`

**Functions:**
- `logistic_function(t, L, k, t0)` - Logistic curve formula
- `fit_logistic_curve(years, shares, initial_guess)` - Differential evolution fitting
- `forecast_logistic_share(years, L, k, t0, end_year)` - Generate S-curve
- `linear_to_logistic_transition()` - Pre-tipping linear, post-tipping logistic

#### 1.5 Create `data_loader.py` (Generalized)
**Source:** `.claude/skills/demand-forecasting/scripts/data_loader.py`
**Destination:** `.claude/skills/_forecasting_core/core/data_loader.py`

**Make taxonomy-agnostic:**
```python
class DataLoader:
    def __init__(self, entity_file_path, taxonomy_file_path):
        """
        Args:
            entity_file_path: Path to entity JSON (e.g., Passenger_Cars.json)
            taxonomy_file_path: Path to taxonomy JSON
        """
        self.entity_data = self._load_json(entity_file_path)
        self.taxonomy = self._load_json(taxonomy_file_path)

    def get_cost_data(self, product_name, region):
        """Generic cost data retrieval"""

    def get_demand_data(self, product_name, region):
        """Generic demand data retrieval"""

    def get_entity_type(self, product_name):
        """Returns: disruptor, incumbent, chimera, or market"""
```

#### 1.6 Create `validators.py`
**Source:** Extract from `utils.py`
**Destination:** `.claude/skills/_forecasting_core/core/validators.py`

**Functions:**
- `validate_forecast_consistency(market, components, tolerance=0.001)`
- `validate_non_negative(array, name)`
- `validate_monotonic_within_tolerance(array, tolerance)`
- `validate_cagr_bounds(values, years, max_cagr)`

#### 1.7 Write `README.md`
**Destination:** `.claude/skills/_forecasting_core/README.md`

**Content:**
```markdown
# Forecasting Core Library

Shared utilities for demand forecasting skills.

## Installation
No installation needed. Skills import directly:

```python
import sys
sys.path.insert(0, '.claude/skills/_forecasting_core')
from core.utils import calculate_cagr
from core.cost_analyzer import CostAnalyzer
```

## Modules

### core.utils
Mathematical utilities: CAGR, smoothing, interpolation, validation

### core.cost_analyzer
Cost curve analysis and tipping point detection

### core.logistic_models
Logistic S-curve fitting for adoption modeling

### core.data_loader
Generic JSON data loading with taxonomy support

### core.validators
Forecast validation and consistency checks

## Usage Examples
[See individual module docstrings]
```

#### 1.8 Test Imports
Create test script:
```python
# test_imports.py
import sys
sys.path.insert(0, '.claude/skills/_forecasting_core')

from core.utils import calculate_cagr, rolling_median
from core.cost_analyzer import CostAnalyzer
from core.logistic_models import fit_logistic_curve
from core.data_loader import DataLoader
from core.validators import validate_forecast_consistency

print("All imports successful!")
```

### Deliverables
- [x] `_forecasting_core/` directory structure created
- [x] All 5 core modules implemented
- [x] README.md documentation complete
- [x] Import test passes
- [x] No dependencies on skill-specific logic

---

## Phase 2: Build Product Demand Skill (2-3 days)

### Goal
Create a generic product forecasting skill that works for all product types (vehicles, energy, batteries, etc.).

### Tasks

#### 2.1 Create Skill Structure
```bash
mkdir -p .claude/skills/product-demand/{scripts,data,reference}
touch .claude/skills/product-demand/SKILL.md
touch .claude/skills/product-demand/config.json
touch .claude/skills/product-demand/run_forecast.sh
```

#### 2.2 Write `SKILL.md`
**Destination:** `.claude/skills/product-demand/SKILL.md`

**Content outline:**
```yaml
---
name: product-demand
description: Forecast demand for products using cost-driven disruption analysis. Handles passenger vehicles (EV, PHEV, ICE), commercial vehicles, two-wheelers, three-wheelers, energy generation (solar, wind, coal, gas), energy storage (batteries). Use when user asks about product demand, market penetration, sales forecasts, adoption rates, or questions like "when will [product] reach [threshold]" or "what is [product] demand in [region]". Supports cost parity analysis, tipping point detection, and S-curve adoption modeling.
---

# Product Demand Forecasting

## Quick Start

Forecast product demand:
```bash
./run_forecast.sh --product "EV cars" --region China --end-year 2040 --output json
```

## Available Products

**Passenger Vehicles:** EV_Cars, BEV_Cars, PHEV_Cars, ICE_Cars, Passenger_Vehicles (market)
**Commercial Vehicles:** Commercial_EV, Commercial_ICE, Commercial_NGV, LCV, MDV, HDV
**Two-Wheelers:** EV_Two_Wheeler, ICE_Two_Wheeler, Two_Wheeler_Market
**Three-Wheelers:** EV_Three_Wheeler, ICE_Three_Wheeler, Three_Wheeler_Market
**Energy Generation:** Solar_PV, Onshore_Wind, Offshore_Wind, Coal_Power, Natural_Gas_Power, Oil_Power
**Energy Storage:** Battery_Storage, Pumped_Hydro, CAES

For complete list, see [reference/products_catalog.md](reference/products_catalog.md)

## Forecasting Process

1. **Load product data** from entity JSON files
2. **Determine market context:**
   - Is this market disrupted?
   - What are the disruptor/incumbent/chimera products?
   - What's the tipping point year (cost parity)?
3. **Route to appropriate model:**
   - **Disruptor** → Logistic S-curve adoption
   - **Chimera** → Hump trajectory (rise then decay)
   - **Incumbent** → Residual (Market - Disruptor - Chimera)
   - **Non-disrupted** → Linear baseline
4. **Validate** and return forecast

## Classification Logic

**Disruptor products:**
- EVs (BEV) in passenger vehicles
- Commercial EVs
- Solar PV and Wind in energy generation
- Battery storage

**Chimera products (transitional):**
- PHEVs in passenger vehicles
- NGVs in commercial vehicles
- Hybrid systems

**Incumbent products:**
- ICE vehicles (passenger and commercial)
- Coal, natural gas, oil in power generation

**Market (total demand):**
- Passenger_Vehicles, Commercial_Vehicles, Energy_Generation, etc.

## Methodology

See [reference/methodology.md](reference/methodology.md) for:
- Cost curve forecasting (log-CAGR + smoothing)
- Tipping point detection (cost parity analysis)
- Logistic adoption modeling (S-curve fitting)
- Chimera hump trajectories
- Residual incumbent calculation

## Data Schema

See [reference/data_schema.md](reference/data_schema.md) for JSON structure.

## Parameters

See [reference/parameters.md](reference/parameters.md) for:
- Logistic ceiling (default: 1.0 = 100% adoption)
- Market CAGR bounds (default: ±5%)
- Smoothing window (default: 3 years)
- Decay half-life for chimeras (default: 3 years)

## Examples

See [reference/examples.md](reference/examples.md) for common usage patterns.

## Terminology Guardrails

When presenting results, use:
- "transformation" or "disruption" (NOT "transition")
- "market-driven" (NOT "policy-driven")
- "exponential" (NOT "linear growth")
- "superabundance" and "zero marginal cost" (NOT "sustainability" or "efficiency")

Avoid: "renewable energy", "sustainable", "green", "hydrogen economy", "grid parity"
```

#### 2.3 Write `config.json`
**Destination:** `.claude/skills/product-demand/config.json`

```json
{
  "default_parameters": {
    "end_year": 2040,
    "logistic_ceiling": 1.0,
    "market_cagr_cap": 0.05,
    "smoothing_window": 3,
    "chimera_decay_half_life": 3.0,
    "phev_peak_share": 0.15
  },
  "regions": [
    "China",
    "USA",
    "Europe",
    "Rest_of_World",
    "Global"
  ],
  "output_formats": [
    "csv",
    "json",
    "both"
  ]
}
```

#### 2.4 Implement `product_forecast.py`
**Destination:** `.claude/skills/product-demand/scripts/product_forecast.py`

**Structure:**
```python
import sys
import os
sys.path.insert(0, '.claude/skills/_forecasting_core')

from core.utils import calculate_cagr, rolling_median, linear_extrapolation
from core.cost_analyzer import CostAnalyzer
from core.logistic_models import fit_logistic_curve, forecast_logistic_share
from core.data_loader import DataLoader
from core.validators import validate_forecast_consistency

import json
import argparse
import numpy as np
from scipy.optimize import differential_evolution


class ProductForecaster:
    """Main orchestrator for product demand forecasting"""

    def __init__(self, product_name, region, end_year, config_path='config.json'):
        self.product_name = product_name
        self.region = region
        self.end_year = end_year
        self.config = self._load_config(config_path)

        # Load data
        self.data_loader = self._initialize_data_loader()

    def _initialize_data_loader(self):
        """Find and load correct entity file for product"""
        # Read products_catalog_index.json to find entity file
        index_path = os.path.join(os.path.dirname(__file__), '../data/products_catalog_index.json')
        with open(index_path) as f:
            catalog = json.load(f)

        entity_name = catalog['products'][self.product_name]['entity']
        entity_path = os.path.join(os.path.dirname(__file__), f'../data/{entity_name}.json')
        taxonomy_path = os.path.join(os.path.dirname(__file__), f'../data/{entity_name}_taxonomy.json')

        return DataLoader(entity_path, taxonomy_path)

    def forecast(self):
        """Main forecasting pipeline"""
        # Step 1: Get market context
        market_context = self._get_market_context()

        # Step 2: Determine product classification
        product_type = self.data_loader.get_entity_type(self.product_name)

        # Step 3: Route to appropriate forecasting method
        if market_context['disrupted']:
            if product_type == 'disruptor':
                forecast = self._forecast_disruptor(market_context)
            elif product_type == 'chimera':
                forecast = self._forecast_chimera(market_context)
            elif product_type == 'incumbent':
                forecast = self._forecast_incumbent(market_context)
            else:  # market
                forecast = self._forecast_market(market_context)
        else:
            # Non-disrupted: baseline linear forecast
            forecast = self._forecast_baseline(market_context)

        # Step 4: Validate
        validation = self._validate_forecast(forecast, market_context)

        # Step 5: Package results
        return {
            'product': self.product_name,
            'region': self.region,
            'product_type': product_type,
            'market_context': market_context,
            'forecast': forecast,
            'validation': validation
        }

    def _get_market_context(self):
        """Retrieve market context: disruption state, tipping point, products"""
        # Implementation: Load market data, check disruption flag, find tipping point
        pass

    def _forecast_disruptor(self, context):
        """Logistic S-curve adoption model"""
        # Implementation: Fit logistic curve, forecast share, multiply by market
        pass

    def _forecast_chimera(self, context):
        """Hump trajectory: rise pre-tipping, decay post-tipping"""
        # Implementation: Peak at tipping year, exponential decay with half-life
        pass

    def _forecast_incumbent(self, context):
        """Residual calculation: Market - Disruptor - Chimera"""
        # Implementation: Forecast disruptor and chimera first, then residual
        pass

    def _forecast_market(self, context):
        """Linear extrapolation with CAGR cap"""
        # Implementation: Theil-Sen slope, bounded by max_cagr
        pass

    def _forecast_baseline(self, context):
        """Non-disrupted baseline: linear bounded by market"""
        # Implementation: Linear trend, capped at market forecast
        pass

    def _validate_forecast(self, forecast, context):
        """Validate forecast consistency"""
        # Check: no negatives, sum constraints, smooth transitions
        pass


def main():
    parser = argparse.ArgumentParser(description='Forecast product demand')
    parser.add_argument('--product', required=True, help='Product name')
    parser.add_argument('--region', required=True, help='Region name')
    parser.add_argument('--end-year', type=int, default=2040, help='Forecast end year')
    parser.add_argument('--output', choices=['csv', 'json', 'both'], default='csv')
    parser.add_argument('--output-dir', default='./output', help='Output directory')

    args = parser.parse_args()

    forecaster = ProductForecaster(args.product, args.region, args.end_year)
    result = forecaster.forecast()

    # Export results
    if args.output in ['json', 'both']:
        output_path = os.path.join(args.output_dir, f'{args.region}_{args.end_year}.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"JSON output: {output_path}")

    if args.output in ['csv', 'both']:
        # Convert to CSV format
        pass


if __name__ == '__main__':
    main()
```

#### 2.5 Create `products_catalog_index.json`
**Destination:** `.claude/skills/product-demand/data/products_catalog_index.json`

```json
{
  "products": {
    "EV_Cars": {"entity": "Passenger_Cars", "type": "disruptor"},
    "BEV_Cars": {"entity": "Passenger_Cars", "type": "disruptor"},
    "PHEV_Cars": {"entity": "Passenger_Cars", "type": "chimera"},
    "ICE_Cars": {"entity": "Passenger_Cars", "type": "incumbent"},
    "Passenger_Vehicles": {"entity": "Passenger_Cars", "type": "market"},

    "Commercial_EV": {"entity": "Commercial_Vehicle", "type": "disruptor"},
    "Commercial_ICE": {"entity": "Commercial_Vehicle", "type": "incumbent"},
    "Commercial_NGV": {"entity": "Commercial_Vehicle", "type": "chimera"},

    "EV_Two_Wheeler": {"entity": "Two_Wheeler", "type": "disruptor"},
    "ICE_Two_Wheeler": {"entity": "Two_Wheeler", "type": "incumbent"},

    "Solar_PV": {"entity": "Energy_Generation", "type": "disruptor"},
    "Onshore_Wind": {"entity": "Energy_Generation", "type": "disruptor"},
    "Coal_Power": {"entity": "Energy_Generation", "type": "incumbent"},
    "Natural_Gas_Power": {"entity": "Energy_Generation", "type": "incumbent"}
  },
  "entities": [
    "Passenger_Cars",
    "Commercial_Vehicle",
    "Two_Wheeler",
    "Three_Wheeler",
    "Energy_Generation",
    "Energy_Storage",
    "Battery_Pack"
  ]
}
```

#### 2.6 Copy Entity Data Files
**Source:** `/Users/himanshuchauhan/TONY/jitin/curves_catalog_files/`
**Destination:** `.claude/skills/product-demand/data/`

```bash
cp curves_catalog_files/Passenger_Cars.json .claude/skills/product-demand/data/
cp curves_catalog_files/Commercial_Vehicle.json .claude/skills/product-demand/data/
cp curves_catalog_files/Two_Wheeler.json .claude/skills/product-demand/data/
cp curves_catalog_files/Three_Wheeler.json .claude/skills/product-demand/data/
cp curves_catalog_files/Energy_Generation.json .claude/skills/product-demand/data/
cp curves_catalog_files/Energy_Storage.json .claude/skills/product-demand/data/
cp curves_catalog_files/Battery_Pack.json .claude/skills/product-demand/data/
```

#### 2.7 Create Taxonomy Files
For each entity, create a taxonomy file (follow existing pattern from `passenger_vehicles_taxonomy_and_datasets.json`).

**Example:** `.claude/skills/product-demand/data/Passenger_Cars_taxonomy.json`

#### 2.8 Create Reference Documentation
Write 4 reference files:
- `reference/methodology.md` - Detailed algorithms
- `reference/data_schema.md` - JSON structure documentation
- `reference/parameters.md` - Parameter ranges and meanings
- `reference/examples.md` - Usage examples

#### 2.9 Create Wrapper Script
**Destination:** `.claude/skills/product-demand/run_forecast.sh`

```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 scripts/product_forecast.py "$@"
```

Make executable: `chmod +x run_forecast.sh`

#### 2.10 Test with Sample Queries
Test with queries from test dataset:
- ID 1: "When will ICE car demand peak?"
- ID 2: "What is the EV market penetration in China?"
- ID 3: "What is the ev three-wheeler market penetration in India?"
- ID 7: "When will solar reach 3TW in China?"

### Deliverables
- [x] Skill directory structure created
- [x] SKILL.md with clear description and instructions
- [x] config.json with default parameters
- [x] product_forecast.py fully implemented
- [x] products_catalog_index.json complete
- [x] 7+ entity JSON files copied (8 files: Passenger_Cars, Commercial_Vehicle, Two_Wheeler, Three_Wheeler, Energy_Generation, Energy_Storage, Battery_Pack, Forklift)
- [x] Taxonomy files created (8 taxonomy files for all entities)
- [x] 4 reference markdown files written (methodology.md, data_schema.md, parameters.md, examples.md)
- [x] run_forecast.sh wrapper script created
- [ ] Successfully tested with 4+ sample queries

---

## Phase 3: Build Commodity Demand Skill (2-3 days)

### Goal
Create commodity forecasting skill that calculates demand from:
1. New product sales (e.g., copper in new EVs)
2. Component replacements (e.g., lead batteries replaced in existing ICE fleet)

### Key Challenge
**Skills cannot call other skills**, so commodity-demand needs one of these approaches:

**Option A (Recommended):** Lightweight product trend logic built-in
- Include simplified product demand forecasting
- Use linear extrapolation instead of full tipping point analysis
- Fast but less accurate for complex disruptions

**Option B:** Accept pre-computed product forecasts
- SKILL.md instructs: "If product forecast files provided, use them"
- Falls back to simple trends if not provided
- Claude Code can orchestrate: run product-demand first, pass results to commodity-demand

We'll implement **Option A** with fallback to **Option B**.

### Tasks

#### 3.1 Create Skill Structure
```bash
mkdir -p .claude/skills/commodity-demand/{scripts,data,reference}
touch .claude/skills/commodity-demand/SKILL.md
touch .claude/skills/commodity-demand/config.json
touch .claude/skills/commodity-demand/run_forecast.sh
```

#### 3.2 Write `SKILL.md`
**Destination:** `.claude/skills/commodity-demand/SKILL.md`

```yaml
---
name: commodity-demand
description: Forecast commodity demand driven by product sales and component replacement cycles. Handles copper, lithium, lead, cobalt, aluminum, nickel (for batteries and motors), oil, coal, natural gas (for energy). Use when user asks about commodity demand, material requirements, supply needs, peak demand years, or questions like "when will [commodity] demand peak" or "what is [commodity] demand for [application]". Calculates demand from both new product sales AND installed base replacements.
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
```

#### 3.3 Write `config.json`
**Destination:** `.claude/skills/commodity-demand/config.json`

```json
{
  "default_parameters": {
    "end_year": 2040,
    "contribution_threshold": 0.8,
    "vehicle_lifetime_years": 15,
    "battery_lifetime_years": 10
  },
  "regions": [
    "China",
    "USA",
    "Europe",
    "Rest_of_World",
    "Global"
  ],
  "output_formats": [
    "csv",
    "json",
    "both"
  ]
}
```

#### 3.4 Implement `commodity_forecast.py`
**Destination:** `.claude/skills/commodity-demand/scripts/commodity_forecast.py`

```python
import sys
import os
sys.path.insert(0, '.claude/skills/_forecasting_core')

from core.utils import calculate_cagr, linear_extrapolation, rolling_median
from core.validators import validate_non_negative

import json
import argparse
import numpy as np


class CommodityForecaster:
    """Main orchestrator for commodity demand forecasting"""

    def __init__(self, commodity_name, region, end_year,
                 product_forecasts_dir=None, config_path='config.json'):
        self.commodity_name = commodity_name
        self.region = region
        self.end_year = end_year
        self.product_forecasts_dir = product_forecasts_dir
        self.config = self._load_config(config_path)

        # Load commodity data
        self.commodity_data = self._load_commodity_data()
        self.intensity_factors = self._load_intensity_factors()
        self.replacement_cycles = self._load_replacement_cycles()

    def forecast(self):
        """Main forecasting pipeline"""
        # Step 1: Identify contributing products
        contributing_products = self._get_contributing_products()

        # Step 2: Forecast demand for each product
        demand_by_source = {}
        for product in contributing_products:
            # Get product demand (from files or built-in estimation)
            product_demand = self._get_product_demand(product)

            # Calculate new sales demand
            new_sales_demand = self._calculate_new_sales_demand(
                product, product_demand
            )

            # Calculate replacement demand
            replacement_demand = self._calculate_replacement_demand(
                product, product_demand
            )

            demand_by_source[product] = {
                'new_sales': new_sales_demand,
                'replacement': replacement_demand,
                'total': new_sales_demand + replacement_demand
            }

        # Step 3: Aggregate total demand
        total_demand = self._aggregate_demand(demand_by_source)

        # Step 4: Find peak year
        peak_year = self._find_peak_year(total_demand)

        # Step 5: Validate
        validation = self._validate_forecast(total_demand)

        return {
            'commodity': self.commodity_name,
            'region': self.region,
            'demand_by_source': demand_by_source,
            'total_demand': total_demand,
            'peak_year': peak_year,
            'validation': validation
        }

    def _get_contributing_products(self):
        """Identify products that contribute 80%+ of commodity usage"""
        # Load commodity_intensity.json to find products
        pass

    def _get_product_demand(self, product):
        """Get product demand: from files if available, else estimate"""
        if self.product_forecasts_dir:
            # Load pre-computed product forecast
            forecast_path = os.path.join(
                self.product_forecasts_dir,
                f'{product}_{self.region}.json'
            )
            if os.path.exists(forecast_path):
                with open(forecast_path) as f:
                    return json.load(f)['forecast']['demand']

        # Fall back to built-in lightweight estimation
        return self._estimate_product_demand_simple(product)

    def _estimate_product_demand_simple(self, product):
        """Lightweight product demand estimation: linear extrapolation"""
        # Load historical product data
        # Apply linear trend with CAGR cap
        # Return forecast
        pass

    def _calculate_new_sales_demand(self, product, product_demand):
        """Commodity demand from new product sales"""
        intensity = self.intensity_factors[self.commodity_name][product]
        years = product_demand['years']
        units = product_demand['units']

        # Demand = units × intensity
        demand = [u * intensity for u in units]

        return {'years': years, 'demand': demand}

    def _calculate_replacement_demand(self, product, product_demand):
        """Commodity demand from component replacements"""
        intensity = self.intensity_factors[self.commodity_name][product]
        replacement_rate = 1.0 / self.replacement_cycles[product][self.commodity_name]

        # Calculate installed base
        installed_base = self._calculate_installed_base(product_demand)

        # Replacement demand = installed_base × replacement_rate × intensity
        demand = [ib * replacement_rate * intensity for ib in installed_base]

        return {'years': product_demand['years'], 'demand': demand}

    def _calculate_installed_base(self, product_demand):
        """Calculate installed base: cumulative sales - retirements"""
        years = product_demand['years']
        units = product_demand['units']
        lifetime = self.config['default_parameters']['vehicle_lifetime_years']

        installed_base = []
        for i, year in enumerate(years):
            # Cumulative sales up to this year
            cumulative_sales = sum(units[:i+1])

            # Retirements: sales from (lifetime) years ago
            retirement_year_idx = i - lifetime
            if retirement_year_idx >= 0:
                retirements = sum(units[:retirement_year_idx+1])
            else:
                retirements = 0

            installed_base.append(cumulative_sales - retirements)

        return installed_base

    def _aggregate_demand(self, demand_by_source):
        """Sum demand across all products"""
        # Aggregate by year
        pass

    def _find_peak_year(self, total_demand):
        """Identify year of peak demand"""
        years = total_demand['years']
        demand = total_demand['demand']
        peak_idx = np.argmax(demand)
        return years[peak_idx]

    def _validate_forecast(self, total_demand):
        """Validate forecast: no negatives, smooth transitions"""
        pass


def main():
    parser = argparse.ArgumentParser(description='Forecast commodity demand')
    parser.add_argument('--commodity', required=True, help='Commodity name')
    parser.add_argument('--region', required=True, help='Region name')
    parser.add_argument('--end-year', type=int, default=2040)
    parser.add_argument('--product-forecasts-dir', default=None,
                       help='Directory with pre-computed product forecasts')
    parser.add_argument('--output', choices=['csv', 'json', 'both'], default='csv')
    parser.add_argument('--output-dir', default='./output')

    args = parser.parse_args()

    forecaster = CommodityForecaster(
        args.commodity, args.region, args.end_year,
        product_forecasts_dir=args.product_forecasts_dir
    )
    result = forecaster.forecast()

    # Export results
    if args.output in ['json', 'both']:
        output_path = os.path.join(args.output_dir,
                                   f'{args.commodity}_{args.region}_{args.end_year}.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"JSON output: {output_path}")

    if args.output in ['csv', 'both']:
        # Convert to CSV
        pass


if __name__ == '__main__':
    main()
```

#### 3.5 Create `commodity_intensity.json`
**Destination:** `.claude/skills/commodity-demand/data/commodity_intensity.json`

```json
{
  "copper": {
    "EV_Cars": 80.0,
    "ICE_Cars": 20.0,
    "PHEV_Cars": 40.0,
    "Commercial_EV": 120.0,
    "Commercial_ICE": 30.0,
    "Solar_PV": 5.5,
    "Onshore_Wind": 4.0,
    "units": "kg per unit"
  },
  "lithium": {
    "EV_Cars": 8.0,
    "PHEV_Cars": 3.0,
    "Commercial_EV": 12.0,
    "Battery_Storage": 0.15,
    "units": "kg per kWh"
  },
  "lead": {
    "ICE_Cars": 12.0,
    "PHEV_Cars": 12.0,
    "Commercial_ICE": 18.0,
    "Datacenter_UPS": 500.0,
    "units": "kg per unit"
  },
  "cobalt": {
    "EV_Cars": 1.2,
    "PHEV_Cars": 0.5,
    "units": "kg per kWh"
  }
}
```

#### 3.6 Create `replacement_cycles.json`
**Destination:** `.claude/skills/commodity-demand/data/replacement_cycles.json`

```json
{
  "ICE_Cars": {
    "lead": 3.5
  },
  "EV_Cars": {
    "lithium": 12.0
  },
  "Commercial_ICE": {
    "lead": 3.0
  },
  "Datacenter_UPS": {
    "lead": 5.0
  },
  "units": "years"
}
```

#### 3.7 Copy Commodity Data Files
```bash
cp curves_catalog_files/Copper.json .claude/skills/commodity-demand/data/
cp curves_catalog_files/Aluminium.json .claude/skills/commodity-demand/data/
cp curves_catalog_files/Lead.json .claude/skills/commodity-demand/data/
```

#### 3.8 Create Reference Documentation
- `reference/methodology.md`
- `reference/intensity_factors.md`
- `reference/replacement_cycles.md`
- `reference/examples.md`

#### 3.9 Create Wrapper Script
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 scripts/commodity_forecast.py "$@"
```

#### 3.10 Test with Sample Queries
- ID 5: "Impact on lead supply from ICE scraping?"
- ID 6: "EV transition impact on lead price?"
- ID 21: "When will crude oil demand peak?"
- ID 23: "When is lead demand going to peak globally?"

### Deliverables
- [x] Skill directory structure created
- [x] SKILL.md with clear description
- [x] commodity_forecast.py implemented
- [x] commodity_intensity.json complete
- [x] replacement_cycles.json complete
- [x] Commodity JSON files copied
- [x] 4 reference markdown files
- [x] Wrapper script created
- [ ] Tested with 4+ sample queries

---

## Phase 4: Build Disruption Analysis Skill (2 days)

### Goal
Analyze cross-market disruption impacts: "Based on EV disruption, when will oil peak?" or "When will SWB displace 100% of coal?"

### Tasks

#### 4.1 Create Skill Structure
```bash
mkdir -p .claude/skills/disruption-analysis/{scripts,data,reference}
touch .claude/skills/disruption-analysis/SKILL.md
touch .claude/skills/disruption-analysis/config.json
touch .claude/skills/disruption-analysis/run_analysis.sh
```

#### 4.2 Write `SKILL.md`
**Destination:** `.claude/skills/disruption-analysis/SKILL.md`

```yaml
---
name: disruption-analysis
description: Analyze cross-market disruption impacts and displacement timelines. Synthesizes product and commodity forecasts to answer questions about disruption, displacement, and peak demand years. Use when user asks "when will [disruptor] displace [incumbent]", "based on [X] disruption when will [Y] peak", "when will [market] be disrupted", or requests disruption analysis, displacement timelines, or threshold crossings (e.g., "when 95% displaced"). Handles: EV disrupting oil demand, SWB disrupting coal/gas, autonomous vehicles disrupting transportation, etc.
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
```

#### 4.3 Implement `disruption_impact.py`
**Destination:** `.claude/skills/disruption-analysis/scripts/disruption_impact.py`

```python
import sys
import os
sys.path.insert(0, '.claude/skills/_forecasting_core')

from core.utils import calculate_cagr
from core.validators import validate_non_negative

import json
import argparse
import numpy as np


class DisruptionAnalyzer:
    """Analyze cross-market disruption impacts"""

    def __init__(self, event_description, region,
                 forecasts_dir=None, config_path='config.json'):
        self.event_description = event_description
        self.region = region
        self.forecasts_dir = forecasts_dir
        self.config = self._load_config(config_path)

        # Load disruption mappings
        self.mappings = self._load_disruption_mappings()

    def analyze(self):
        """Main analysis pipeline"""
        # Step 1: Parse event description
        disruption_info = self._parse_event(self.event_description)

        # Step 2: Load relevant forecasts
        disruptor_forecast = self._load_forecast(disruption_info['disruptor'])
        impacted_forecast = self._load_forecast(disruption_info['impacted'])

        # Step 3: Calculate displacement
        displacement_timeline = self._calculate_displacement(
            disruptor_forecast,
            impacted_forecast,
            disruption_info
        )

        # Step 4: Find key milestones
        milestones = self._find_milestones(displacement_timeline)

        # Step 5: Generate report
        return {
            'event': self.event_description,
            'region': self.region,
            'disruptor': disruption_info['disruptor'],
            'impacted': disruption_info['impacted'],
            'displacement_timeline': displacement_timeline,
            'milestones': milestones,
            'summary': self._generate_summary(milestones)
        }

    def _parse_event(self, description):
        """Parse event description to identify disruptor and impacted"""
        # Look up in disruption_mappings.json
        # Match keywords: "EV", "SWB", "oil", "coal", etc.
        pass

    def _load_forecast(self, product_or_commodity):
        """Load forecast data"""
        if self.forecasts_dir:
            # Load from provided directory
            pass
        else:
            # Fall back to internal estimation
            pass

    def _calculate_displacement(self, disruptor, impacted, info):
        """Calculate how disruptor displaces incumbent over time"""
        conversion_factor = info['conversion_factor']

        years = disruptor['years']
        displacement = []

        for i, year in enumerate(years):
            # Displaced demand = disruptor_units × conversion_factor
            displaced = disruptor['demand'][i] * conversion_factor

            # Remaining demand = baseline - displaced
            baseline = impacted['demand'][i]
            remaining = max(0, baseline - displaced)

            displacement.append({
                'year': year,
                'disruptor_level': disruptor['demand'][i],
                'baseline_demand': baseline,
                'displaced_demand': displaced,
                'remaining_demand': remaining,
                'displacement_rate': displaced / baseline if baseline > 0 else 0
            })

        return displacement

    def _find_milestones(self, timeline):
        """Find key years: peak, 50%, 95%, 100% displacement"""
        milestones = {}

        # Peak year
        baseline_demands = [t['baseline_demand'] for t in timeline]
        peak_idx = np.argmax(baseline_demands)
        milestones['peak_year'] = timeline[peak_idx]['year']

        # 50% displacement
        for t in timeline:
            if t['displacement_rate'] >= 0.50:
                milestones['50_percent_displacement'] = t['year']
                break

        # 95% displacement
        for t in timeline:
            if t['displacement_rate'] >= 0.95:
                milestones['95_percent_displacement'] = t['year']
                break

        # 100% displacement
        for t in timeline:
            if t['remaining_demand'] == 0:
                milestones['100_percent_displacement'] = t['year']
                break

        return milestones

    def _generate_summary(self, milestones):
        """Generate human-readable summary"""
        summary = []

        if 'peak_year' in milestones:
            summary.append(f"Peak demand occurs in {milestones['peak_year']}")

        if '50_percent_displacement' in milestones:
            summary.append(f"50% displaced by {milestones['50_percent_displacement']}")

        if '95_percent_displacement' in milestones:
            summary.append(f"95% displaced by {milestones['95_percent_displacement']}")

        if '100_percent_displacement' in milestones:
            summary.append(f"Complete displacement by {milestones['100_percent_displacement']}")

        return '; '.join(summary)


def main():
    parser = argparse.ArgumentParser(description='Analyze disruption impact')
    parser.add_argument('--event', required=True, help='Disruption event description')
    parser.add_argument('--region', required=True, help='Region')
    parser.add_argument('--forecasts-dir', default=None,
                       help='Directory with forecast data')
    parser.add_argument('--output', choices=['json', 'text'], default='json')
    parser.add_argument('--output-dir', default='./output')

    args = parser.parse_args()

    analyzer = DisruptionAnalyzer(args.event, args.region, args.forecasts_dir)
    result = analyzer.analyze()

    if args.output == 'json':
        output_path = os.path.join(args.output_dir, 'disruption_analysis.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Analysis saved to {output_path}")
    else:
        print(result['summary'])


if __name__ == '__main__':
    main()
```

#### 4.4 Create `disruption_mappings.json`
**Destination:** `.claude/skills/disruption-analysis/data/disruption_mappings.json`

```json
{
  "ev_disrupts_oil": {
    "keywords": ["EV", "electric vehicle", "oil", "petroleum"],
    "disruptor": ["EV_Cars", "Commercial_EV"],
    "impacted": "Oil_Demand_Transportation",
    "conversion_factor": 2.5,
    "units": "barrels_per_day per 1000 vehicles",
    "description": "EVs displace oil demand in transportation sector"
  },
  "swb_displaces_coal": {
    "keywords": ["SWB", "solar wind battery", "coal"],
    "disruptor": ["Solar_PV", "Onshore_Wind", "Battery_Storage"],
    "impacted": "Coal_Power_Generation",
    "conversion_factor": 1.0,
    "units": "MWh per MWh",
    "description": "Solar+Wind+Battery displaces coal power generation"
  },
  "swb_displaces_gas": {
    "keywords": ["SWB", "solar wind battery", "natural gas", "gas"],
    "disruptor": ["Solar_PV", "Onshore_Wind", "Battery_Storage"],
    "impacted": "Natural_Gas_Power_Generation",
    "conversion_factor": 1.0,
    "units": "MWh per MWh",
    "description": "Solar+Wind+Battery displaces natural gas power generation"
  },
  "ev_impacts_lead": {
    "keywords": ["EV", "electric vehicle", "lead"],
    "disruptor": "EV_Cars",
    "impacted": "Lead_Demand",
    "conversion_factor": -12.0,
    "units": "kg lead saved per EV (no starter battery)",
    "description": "EVs reduce lead demand by eliminating starter batteries"
  },
  "ice_decline_impacts_oil": {
    "keywords": ["ICE", "internal combustion", "oil"],
    "disruptor": "ICE_Cars",
    "impacted": "Oil_Demand_Transportation",
    "conversion_factor": 1.0,
    "units": "direct relationship",
    "description": "ICE vehicle decline directly reduces oil demand"
  }
}
```

#### 4.5 Create Reference Documentation
- `reference/methodology.md`
- `reference/relationships.md` - Known disruption patterns
- `reference/examples.md`

#### 4.6 Test with Sample Queries
- ID 8: "Based on SWB disruption, when will gas demand peak in China?"
- ID 9: "Based on EV disruption, when will oil demand peak?"
- ID 10: "When will SWB displace 100% of coal in China?"
- ID 14: "When will all ICE engines be displaced globally?"

### Deliverables
- [x] Skill directory structure created
- [x] SKILL.md with clear description
- [x] disruption_impact.py implemented
- [x] disruption_mappings.json complete
- [x] 3 reference markdown files
- [x] Wrapper script created
- [x] Tested with 3 sample queries (EV→oil, SWB→coal, EV→lead)

---

## Phase 5: Integration Testing (1-2 days)

### Goal
Test complete system with all 42 queries from test dataset. Ensure Claude Code correctly routes queries to skills and orchestrates multi-skill workflows.

### Tasks

#### 5.1 Create Test Suite
**File:** `test_all_queries.py`

```python
import json
import subprocess
import os


def load_test_queries():
    """Load 42 test queries from test dataset"""
    with open('test_queries.json') as f:
        return json.load(f)['test_queries']


def run_query(query_text):
    """Simulate Claude Code processing query"""
    # This would be done by Claude Code in practice
    # For testing, we manually invoke appropriate skills
    pass


def test_all_queries():
    """Run all 42 queries and check results"""
    queries = load_test_queries()

    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }

    for query in queries:
        print(f"\nTesting Query {query['id']}: {query['query']}")
        print(f"Expected function: {query['expected_function']}")

        try:
            # Run query through appropriate skill
            result = run_query(query['query'])

            # Validate result
            if validate_result(result, query):
                results['passed'] += 1
                print("✓ PASSED")
            else:
                results['failed'] += 1
                results['errors'].append({
                    'id': query['id'],
                    'query': query['query'],
                    'error': 'Result validation failed'
                })
                print("✗ FAILED")

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'id': query['id'],
                'query': query['query'],
                'error': str(e)
            })
            print(f"✗ ERROR: {e}")

    print(f"\n\nResults: {results['passed']}/{len(queries)} passed")

    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  Query {error['id']}: {error['error']}")

    return results


if __name__ == '__main__':
    test_all_queries()
```

#### 5.2 Test Product Demand Queries (11 queries)
IDs: 1, 2, 3, 4, 7, 11, 13, 19, 26, 27, 28

Verify:
- Correct skill triggered
- Correct product identified
- Correct region identified
- Forecast returned with expected structure
- Historical + forecasted data both present

#### 5.3 Test Commodity Demand Queries (9 queries)
IDs: 5, 6, 15, 17, 21, 23, 24, 25, 33

Verify:
- Correct skill triggered
- Commodity identified
- New sales + replacement demand calculated
- Peak year detected
- Breakdown by source provided

#### 5.4 Test Disruption Analysis Queries (13 queries)
IDs: 8, 9, 10, 14, 16, 20, 29, 30, 31, 32, 42

Verify:
- Correct skill triggered
- Disruptor and impacted identified
- Displacement timeline calculated
- Milestones detected (peak, 50%, 95%, 100%)
- Summary generated

#### 5.5 Test Multi-Skill Workflows
Example: "When will oil demand peak due to EV disruption?"

Expected workflow:
1. Claude Code parses query
2. Identifies: needs EV forecast + oil forecast + disruption analysis
3. Invokes `product-demand` for EV forecast
4. Invokes `commodity-demand` for oil forecast
5. Invokes `disruption-analysis` with both forecasts
6. Synthesizes final answer

Verify:
- All three skills invoked in correct order
- Data passed correctly between skills
- Final answer accurate and complete

#### 5.6 Test Edge Cases
- Missing data (product not in catalog)
- Invalid regions
- End year too far in future
- Conflicting parameters
- Skills with no available data

#### 5.7 Document Known Limitations
Create `LIMITATIONS.md`:

```markdown
# Known Limitations

## Data Coverage

### Products with complete data:
- Passenger vehicles (EV, PHEV, ICE)
- Commercial vehicles (partial)
- Two-wheelers (partial)
- Energy generation (solar, wind, coal, gas)

### Products with incomplete data:
- Three-wheelers (limited regional coverage)
- Battery storage (limited historical data)
- Specific battery chemistries

### Commodities with complete data:
- Copper, aluminum, lead

### Commodities needing data:
- Lithium, cobalt, nickel (need intensity factors)
- Oil, coal, natural gas (need consumption curves)

## Methodology Limitations

- **Commodity skill:** Uses simplified product trends, less accurate than full disruption analysis
- **Disruption skill:** Requires pre-computed forecasts or uses simplified estimates
- **No feedback loops:** E.g., lower oil prices from reduced demand could slow EV adoption
- **No policy scenarios:** Current implementation assumes market-driven forces only
- **Regional aggregation:** Global forecasts aggregate regions, may miss interactions

## Output Limitations

- No confidence intervals or uncertainty quantification
- No sensitivity analysis
- No scenario comparisons
- Limited visualization (CSV/JSON only)
```

### Deliverables
- [ ] Test suite implemented
- [ ] All 42 queries tested
- [ ] Results documented
- [ ] Edge cases identified and handled
- [ ] Known limitations documented
- [ ] Bug fixes applied
- [ ] Integration issues resolved

---

## Phase 6: Refinement (1 day)

### Goal
Apply user feedback and polish skills for production use.

### Tasks

#### 6.1 Apply Terminology Guardrails
Based on CLAUDE.md requirements:

**Add to all SKILL.md files:**
```markdown
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
```

#### 6.2 Remove First-Person Language
Search all SKILL.md and reference files for:
- "I will", "I can", "I should"
- "We recommend", "We suggest"

Replace with:
- "The skill will", "This analysis"
- "Recommended approach", "Suggested method"

#### 6.3 Fix Response Logic Issues
Based on feedback: "Logic is superfluous"

Review all scripts for:
- Unnecessary intermediate steps
- Redundant calculations
- Over-verbose logging
- Complex conditional logic that could be simplified

Refactor for clarity and efficiency.

#### 6.4 Simplify Current Facts Analysis
Based on feedback: "If query is about current facts, do simplified analysis"

Add logic to detect "current state" queries:
- "Has coal demand already peaked?"
- "What is current EV penetration?"
- "Is oil demand declining now?"

For these queries:
- Skip forecasting pipeline
- Return historical data + recent trend
- Simple peak detection on historical data only

#### 6.5 Fix Forecasted Data Pickup
Based on feedback: "Response layer not picking forecasted data"

Ensure all scripts clearly separate:
- `historical_data` - past data points
- `forecasted_data` - future projections
- `combined_data` - both together

Verify output JSON structure matches expected format.

#### 6.6 Add Response Templates
Create templates for common response patterns:

**Template 1: Peak year response**
```
Based on [disruptor] disruption transforming the [market] market, [commodity/product] demand will peak in [YEAR] at [VALUE] [UNITS].

Key milestones:
- Tipping point (cost parity): [YEAR]
- Peak demand: [YEAR]
- 50% displacement: [YEAR]
- 95% displacement: [YEAR]

The [disruptor] adoption follows an exponential S-curve, reaching [X]% market share by [YEAR]. This market-driven transformation displaces [incumbent] demand at an accelerating rate post-tipping.
```

**Template 2: Demand forecast response**
```
[Product] demand in [Region]:

Historical (most recent 5 years):
[Table]

Forecasted (to [END_YEAR]):
[Table]

Key findings:
- CAGR ([START]-[END]): [X]%
- [Product] reaches [THRESHOLD] by [YEAR]
- Market transformation driven by [REASON]
```

#### 6.7 Add Validation Checks
Implement validation layer that checks:
- All output years in chronological order
- No negative values
- Sum constraints satisfied (BEV+PHEV+ICE ≤ Market)
- Smooth transitions (no >50% jumps year-over-year)
- Physically plausible CAGRs (<20%)

If validation fails:
- Log warning
- Apply correction (smooth, clamp, interpolate)
- Flag in output metadata

#### 6.8 Create User Documentation
Write `USAGE_GUIDE.md` for end users:

```markdown
# Skills Usage Guide

## Overview

Three skills for demand forecasting:

1. **product-demand**: Forecast product sales/capacity
2. **commodity-demand**: Forecast material requirements
3. **disruption-analysis**: Analyze cross-market impacts

## Common Queries

### Product Demand
"What is EV demand in China?"
"When will solar reach 3 TW in China?"
"When will ICE car demand peak?"

### Commodity Demand
"What is copper demand for EVs?"
"When will lead demand peak?"
"Lithium requirements for batteries in Europe?"

### Disruption Analysis
"When will oil demand peak due to EVs?"
"Based on SWB disruption, when will coal be displaced?"
"Impact of EV adoption on lead supply?"

## Output Formats

### CSV
Year, Product, Demand, Units

### JSON
Full metadata, historical + forecasted, validation results

## Interpreting Results

- **Tipping point**: Year when disruptor cost < incumbent cost
- **Peak year**: Maximum demand year
- **Displacement rate**: % of incumbent displaced by disruptor
- **CAGR**: Compound annual growth rate

## Limitations

- Forecasts assume market-driven forces, no policy intervention
- No confidence intervals currently provided
- Regional data quality varies
```

### Deliverables
- [ ] Terminology guardrails added to all skills
- [ ] First-person language removed
- [ ] Response logic simplified
- [ ] Current facts analysis added
- [ ] Forecasted data pickup fixed
- [ ] Response templates created
- [ ] Validation checks implemented
- [ ] User documentation written
- [ ] All skills polished and production-ready

---

## Final Checklist

### Shared Library
- [x] `_forecasting_core/` created with 5 modules
- [x] All modules documented with docstrings
- [x] Import test passes
- [x] README.md complete

### Product Demand Skill
- [x] SKILL.md with clear description
- [ ] product_forecast.py fully implemented
- [ ] 7+ entity JSON files in place
- [ ] Taxonomy files created
- [ ] 4 reference docs written
- [ ] Wrapper script executable
- [ ] Tested with 11+ queries
- [ ] Terminology guardrails applied

### Commodity Demand Skill
- [ ] SKILL.md with clear description
- [ ] commodity_forecast.py fully implemented
- [ ] Intensity factors complete
- [ ] Replacement cycles defined
- [ ] 3+ commodity JSON files
- [ ] 3 reference docs written
- [ ] Wrapper script executable
- [ ] Tested with 9+ queries
- [ ] Terminology guardrails applied

### Disruption Analysis Skill
- [ ] SKILL.md with clear description
- [ ] disruption_impact.py fully implemented
- [ ] Disruption mappings complete
- [ ] 3 reference docs written
- [ ] Wrapper script executable
- [ ] Tested with 13+ queries
- [ ] Terminology guardrails applied

### Integration
- [ ] All 42 test queries passing
- [ ] Multi-skill workflows tested
- [ ] Edge cases handled
- [ ] Known limitations documented
- [ ] User guide written
- [ ] Response templates created
- [ ] Validation layer implemented

### Documentation
- [ ] README for shared library
- [ ] SKILL.md for each skill (3 total)
- [ ] Reference docs for each skill (12 total)
- [ ] LIMITATIONS.md
- [ ] USAGE_GUIDE.md
- [ ] Test results documented

---

## Success Criteria

1. **Skill Discovery**: Claude Code correctly identifies and triggers appropriate skill for each query type
2. **Accuracy**: Forecasts match existing demand-forecasting skill for passenger vehicles (validation)
3. **Coverage**: All 42 test queries handled correctly (31 FULL_MATCH, 3 PARTIAL_MATCH, 8 PASSTHROUGH)
4. **Independence**: Each skill works standalone without calling other skills
5. **Orchestration**: Claude Code successfully chains skills for complex queries
6. **Terminology**: All outputs follow guardrails (no "transition", use "transformation")
7. **Response Quality**: Clear, quantitative, exponential-thinking responses
8. **Maintainability**: Shared library enables easy updates and bug fixes

---

## Estimated Effort

| Phase | Tasks | Duration |
|-------|-------|----------|
| 1. Shared Library | Extract and refactor code | 2 days |
| 2. Product Demand | Implement generic product skill | 2-3 days |
| 3. Commodity Demand | Implement commodity skill with sales+replacement | 2-3 days |
| 4. Disruption Analysis | Implement cross-market impact analysis | 2 days |
| 5. Integration Testing | Test all 42 queries, fix bugs | 1-2 days |
| 6. Refinement | Apply feedback, polish, document | 1 day |
| **Total** | | **10-13 days** |

---

## Risk Mitigation

### Risk 1: Skills cannot cross-reference
**Mitigation:** Each skill includes lightweight built-in estimation as fallback. Claude Code orchestrates multi-skill workflows.

### Risk 2: Data gaps for some commodities
**Mitigation:** Document known limitations clearly. Prioritize commodities with complete data (copper, lead, aluminum).

### Risk 3: Skill discovery fails
**Mitigation:** Write very specific SKILL.md descriptions with comprehensive keywords. Test discovery extensively.

### Risk 4: Shared library breaks existing skill
**Mitigation:** Keep existing demand-forecasting skill unchanged. New skills import shared library, old skill remains independent.

### Risk 5: Integration complexity
**Mitigation:** Phase 5 dedicated to integration testing. Allocate 1-2 days for bug fixes and edge cases.

---

## Next Steps

1. **Review this plan** - Confirm approach and timeline
2. **Phase 1: Start shared library** - Extract utils.py first (highest confidence)
3. **Validate Phase 1** - Test imports before proceeding
4. **Phase 2: Build product skill** - Use existing demand-forecasting as reference
5. **Iterate phases 3-6** - Adjust based on learnings from each phase

Ready to begin implementation!
