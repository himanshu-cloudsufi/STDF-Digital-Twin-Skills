# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **cost-driven demand forecasting system** for analyzing technology disruption across transportation, energy generation, and commodities. The system predicts when disruptor technologies achieve cost parity with incumbents and models subsequent market adoption using logistic growth curves.

### Scope
- **Transportation**: Passenger vehicles (EV, PHEV, ICE), commercial vehicles, two-wheelers, three-wheelers
- **Energy Generation**: Solar, wind, batteries, coal, natural gas, oil power
- **Commodities**: Copper, lithium, lead, cobalt, aluminum, nickel, oil, coal, natural gas
- **Analysis**: Cross-market disruption impacts and displacement timelines

## Interaction Protocol

When working with this repository, Claude Code should follow these guidelines:

1. **Ask Clarifying Questions**: If a user request is ambiguous, incomplete, or could be interpreted multiple ways, ask clarifying questions before proceeding. Examples:
   - Missing information needed to complete the task
   - Unclear scope or intent
   - Multiple valid approaches are available
   - Assumptions that should be confirmed

2. **Present Plan for Approval**: Before executing any task that modifies files, runs computations, or generates outputs, present a brief summary of what you'll do and wait for user confirmation. Include:
   - What you'll do
   - Key assumptions or parameters
   - Expected outputs or changes

3. **Skip for Read-Only Tasks**: These steps are not needed for exploratory work such as reading files, answering questions, or explaining concepts.

## Terminology Guardrails

When generating outputs, reports, documentation, or communicating about this forecasting system, adhere to the following terminology guidelines to accurately reflect the speed, scale, and systemic nature of technological disruption:

### Terms to Avoid

**Primary terms to avoid:**
- "renewable energy," "sustainable," "green," "hydrogen economy," "grid parity," "energy transition," "intermittency," "net zero"
  - These terms frame the energy shift in ways that underestimate the speed, scale, and systemic nature of technological disruption

**Additional terms to avoid:**
- "alternative energy," "baseload power," "peak oil," "energy efficiency," "carbon neutral," "smart grid," "fossil fuel transition"
  - These terms reinforce outdated assumptions about scarcity, gradual change, or the viability of legacy systems

**Avoid overemphasis on:** "energy storage" as a limiting factor

### Preferred Terminology

**Instead, use:**
- **"Stellar Energy"** or **"clean disruption"** - Language that reflects abundance, exponential change, and new system architectures
- **"transformation"** or **"disruption"** - Instead of "transition," "evolution," or "incremental" to emphasize rapid, systemic change
- **"superabundance"** and **"zero marginal cost"** - Instead of "sustainability," "efficiency," or "scarcity" to focus on abundance and exponential potential
- **"exponential"** trends - Not "linear growth" or "steady improvement" to reflect technology cost curves and adoption surges
- **"market-driven"** forces - Not "policy-driven transitions" to attribute shifts to economics, not regulations (unless modeling specific policy risks)
- **"distributed"** or **"decentralized"** systems - Avoid legacy terms like "smart grid," "centralized energy," or "baseload"

### Rationale

This terminology aligns with the vision of a world powered by near-zero-cost, superabundant clean energy by 2030, driven by market forces and exponential technology improvements rather than incremental policy changes or efficiency gains.

### Communication Style

When analyzing queries and presenting results:

**Think exponentially, not linearly:**
- Disruptions accelerate after tipping points (S-curve adoption), they don't proceed at steady rates
- Cost improvements follow exponential trajectories (Wright's Law), not linear decline
- Market transformations happen in years/decades, not generations

**Focus on speed and scale:**
- Emphasize how quickly disruption occurs post-tipping (typically 10-15 years to 80%+ adoption)
- Highlight the magnitude of change (incumbent markets can lose 50%+ share within a decade)
- Use concrete numbers and timeframes, not vague predictions

**Avoid technical jargon in user-facing output:**
- Don't say "Wright's Law analysis" → say "cost curve decline analysis"
- Don't say "logistic regression" → say "S-curve adoption modeling"
- Don't say "Theil-Sen estimator" → say "robust trend analysis"
- Explain methods in plain language, cite specific data points

**Be quantitative and bold:**
- Provide specific years for milestones (e.g., "China reaches 80% EV adoption by 2035")
- Show the math: display calculations, intermediate values, and derivations
- Don't hedge with "might" or "could" when data supports a clear projection

## Key Concepts

- **Tipping Point**: The cost parity year when disruptor cost < incumbent cost
- **Disruptor**: New technology with exponentially declining costs (e.g., BEV, Solar, Battery Storage) - modeled with logistic S-curve
- **Chimera**: Bridge technology that rises temporarily then decays (e.g., PHEV, NGV) - modeled with hump trajectory
- **Incumbent**: Legacy technology displaced by disruptor (e.g., ICE, Coal, Natural Gas) - calculated as residual
- **Regions**: China, USA, Europe, Rest_of_World, Global (aggregated across all regions)

## Data Architecture

### Centralized Catalog Structure
- **Location**: `curves_catalog_files/`
- **Format**: Split by entity (20 entities, 235 metrics, 825 datasets)
- **Key Entities**:
  - `Passenger_Cars.json` - EV, PHEV, ICE passenger vehicles
  - `Commercial_Vehicles.json` - LCV, MDV, HDV, buses
  - `Two_Wheeler.json`, `Three_Wheeler.json` - Light EVs
  - `Solar.json`, `Wind.json` - Energy generation
  - `Copper.json`, `Lithium.json`, `Lead.json` - Commodities
  - `Coal.json`, `Crude_Oil.json` - Fossil fuels
- **Index**: `_index.json` provides metadata about available entities

### Skill-Specific Data
Each skill has a self-contained `data/` directory with:
- **Entity JSON files** - Cost and demand curves for products/commodities in that skill's scope
- **Taxonomy files** - Map product names to datasets and define entity types (disruptor/incumbent/chimera)
- **Intensity/mapping files** - Commodity intensity factors, disruption mappings, replacement cycles

### Data Format
Each entity file contains:
```json
{
  "Entity Name": {
    "Metric_Name": {
      "metadata": {
        "type": "...",
        "units": "...",
        "entity_type": "disruptor|incumbent|chimera|market"
      },
      "regions": {
        "China": {"X": [years], "Y": [values]},
        "Europe": {"X": [years], "Y": [values]},
        ...
      }
    }
  }
}
```

### Taxonomy Mapping
Taxonomy files map product types to datasets and define entity classifications:
```json
{
  "products": {
    "EV_Cars": {
      "entity_type": "disruptor",
      "datasets": ["EV_Cars_Cost", "EV_Cars_Demand"],
      "description": "Battery electric passenger vehicles"
    }
  }
}
```

## Skills Architecture Overview

The forecasting system uses a **fully independent multi-skill architecture** with four specialized, self-contained skills.

### Architecture Diagram

```
    ├── product-demand       (PRIMARY - all products, all sectors)
    │   └── scripts/lib/     (self-contained utilities)
    │
    ├── commodity-demand     (metals, energy commodities)
    │   └── scripts/lib/     (self-contained utilities)
    │
    ├── disruption-analysis  (cross-market impacts)
    │   └── scripts/lib/     (self-contained utilities)
    │
    └── demand-forecasting   (LEGACY - passenger vehicles only)
        └── scripts/         (self-contained, no lib/)
```

### Skill Independence

Each skill is completely self-contained:

- **No cross-skill dependencies**: Each skill operates independently without requiring outputs from other skills
- **Self-contained utilities**: Each skill has its own `scripts/lib/` directory with necessary utility functions
- **Independent data access**: Each skill only accesses data within its own directory structure
- **Standalone execution**: Skills can be run in isolation without any coordination

### Shared Utility Code

Each skill (except legacy demand-forecasting) contains identical copies of core utilities in `scripts/lib/`:

- `utils.py` - CAGR calculation, smoothing, interpolation, linear extrapolation
- `cost_analyzer.py` - Cost curve forecasting, tipping point detection (product-demand only)
- `logistic_models.py` - S-curve fitting, logistic adoption modeling (product-demand only)
- `data_loader.py` - Taxonomy-driven data loading (product-demand only)
- `validators.py` - Forecast validation, consistency checks

**Note**: Code duplication is intentional to ensure complete skill independence.

## Core Forecasting Methodology

Located in `instructions_editable.md`, the methodology follows this pipeline:

1. **Cost Curve Forecasting**: Log-CAGR extrapolation with 3-year rolling median smoothing
2. **Tipping Point Detection**: First year when EV cost < ICE cost
3. **Market Demand Forecast**: Linear extrapolation using Theil-Sen robust regression, capped at ±5% CAGR
4. **BEV Forecast**: Logistic curve fitting post-tipping: `s(t) = L / (1 + exp(-k * (t - t₀)))`
5. **PHEV Forecast**: "Hump" trajectory rising before tipping, decaying with 3-year half-life after
6. **ICE Forecast**: Residual calculation: `ICE = max(Market - BEV - PHEV, 0)`
7. **Validation**: Ensure BEV + PHEV + ICE ≤ Market, all values ≥ 0, smooth transitions

### Validation Checkpoints

Use these quick checks before/after major operations:

**Before running forecast:**
- [ ] Region parameter is valid (China, USA, Europe, Rest_of_World, Global)
- [ ] End year is reasonable (2025-2100)
- [ ] Product/commodity name matches taxonomy definitions
- [ ] Required data files exist in skill's data directory

**After forecast completes:**
- [ ] No negative demand values in any year
- [ ] For products with market: Disruptor + Chimera + Incumbent ≤ Market (tolerance: 0.1%)
- [ ] Smooth year-over-year transitions (no sudden jumps >50%)
- [ ] Tipping point detected or explicitly noted as "none found"

**Before presenting results:**
- [ ] Output format matches user request (csv/json/both)
- [ ] Logistic parameters are physically reasonable (k ∈ [0.05, 1.5])
- [ ] Terminology follows guardrails (no "transition", use "transformation")

## Skill Selection Guide

### Decision Tree: Which Skill to Use?

```
User Query → Analyze Keywords → Select Skill

Is it about PRODUCTS (vehicles, solar, wind, batteries)?
    → Use product-demand

Is it about COMMODITIES (copper, lithium, oil, coal)?
    → Use commodity-demand

Is it about DISRUPTION/DISPLACEMENT/IMPACTS?
    → Use disruption-analysis

Is it ONLY about passenger vehicles AND requires legacy output format?
    → Use demand-forecasting (legacy)
```

### Trigger Keywords by Skill

| Skill | Use When Query Contains | Example Questions |
|-------|------------------------|-------------------|
| **product-demand** | product demand, market penetration, sales forecasts, adoption rates, capacity forecasts, market share, tipping point, cost parity, EV adoption, solar capacity, wind capacity, vehicle sales, market transformation | "What is EV demand in China by 2040?"<br>"When will solar reach 50% market share?"<br>"Forecast commercial vehicle adoption in Europe"<br>"When does cost parity occur for batteries?" |
| **commodity-demand** | commodity demand, material requirements, supply needs, copper demand, lithium demand, lead demand, oil demand, coal demand, metal requirements, peak demand | "When will lithium demand peak?"<br>"What is copper demand for EVs in 2035?"<br>"Forecast lead demand driven by vehicles"<br>"Oil demand for transportation sector" |
| **disruption-analysis** | disrupt, displace, impact, peak, threshold, decline, when will X displace Y, cross-market, displacement timeline, 95% displaced, market disruption | "When will EVs disrupt oil demand?"<br>"Based on EV adoption when will oil peak?"<br>"When 95% of coal displaced by solar+wind?"<br>"Disruption timeline for ICE vehicles" |
| **demand-forecasting** | (legacy) passenger vehicles ONLY, backward compatibility required | "Run legacy passenger vehicle forecast"<br>(Use product-demand instead for new work) |

### Quick Reference: Skill Capabilities

#### product-demand (PRIMARY SKILL)
- **Scope**: 43 products across 8 entities
- **Sectors**: Transportation (passenger, commercial, two/three-wheelers), Energy (solar, wind, batteries, coal, gas, oil), Storage (batteries, pumped hydro)
- **Output**: Forecasts for disruptor, chimera, incumbent, market demand
- **When**: User asks about ANY product demand, adoption, market share, sales, capacity

#### commodity-demand
- **Scope**: Copper, Lithium, Lead, Cobalt, Aluminum, Nickel, Oil, Coal, Natural Gas
- **Methodology**: Intensity-based calculation (new sales + replacement cycles)
- **Output**: Total commodity demand aggregated across contributing products
- **When**: User asks about material/commodity requirements, supply needs, peak demand years

#### disruption-analysis
- **Scope**: Known disruption mappings (EV→oil, SWB→coal/gas, EV→ICE, etc.)
- **Analysis Types**: Cross-market impact, threshold crossing, peak detection, displacement timeline
- **Output**: Tipping point year, 50% displacement year, 95% displacement year, peak year
- **When**: User asks about disruption impacts, displacement timelines, when one technology displaces another

#### demand-forecasting (LEGACY)
- **Scope**: Passenger vehicles ONLY (EV, PHEV, ICE)
- **Status**: Superseded by product-demand for most use cases
- **When**: Backward compatibility required, or user explicitly requests legacy skill

### Independent Execution

Each skill operates completely independently with no cross-dependencies:

```bash
# Product demand - standalone
.claude/skills/product-demand/run_forecast.sh --product "EV_Cars" --region China --output json

# Commodity demand - standalone (uses internal estimation)
.claude/skills/commodity-demand/run_forecast.sh --commodity "lead" --region China

# Disruption analysis - standalone (uses internal estimation)
.claude/skills/disruption-analysis/run_analysis.sh --event "EV disruption" --region Global
```

**Note**: Cross-skill data loading has been removed. Each skill uses its own internal estimation methods.

## Skills Reference

This section documents all four forecasting skills in detail.

### 1. product-demand (PRIMARY SKILL)

**Location**: `.claude/skills/product-demand/`

**Purpose**: Generic product demand forecasting using cost-driven disruption analysis across ALL sectors

**Scope**: 43 products across 8 entities
- **Transportation**: EV_Cars, BEV_Cars, PHEV_Cars, ICE_Cars, Passenger_Vehicles, Commercial_EV, Commercial_ICE, Commercial_NGV, LCV, MDV, HDV, EV_Two_Wheeler, ICE_Two_Wheeler, EV_Three_Wheeler, ICE_Three_Wheeler, EV_Forklift, ICE_Forklift
- **Energy Generation**: Solar_PV, Onshore_Wind, Offshore_Wind, Coal_Power, Natural_Gas_Power, Oil_Power
- **Energy Storage**: Battery_Storage, Pumped_Hydro, CAES
- **Batteries**: Battery_Pack, Lithium_Ion_Battery

**When to Use**:
- User asks about **product demand**, market penetration, sales forecasts, adoption rates, capacity forecasts, market share
- Questions like: "when will [product] reach [threshold]", "what is [product] demand in [region]", "when will [product] peak"
- Examples: EV adoption, solar capacity, wind capacity, vehicle sales, market transformation, technology disruption, cost parity, tipping point detection

**Parameters**:
- `--product` (required): Product name (e.g., "EV_Cars", "Solar_PV", "Commercial_EV")
- `--region` (required): China, USA, Europe, Rest_of_World, Global
- `--end-year` (optional, default: 2040): Forecast horizon
- `--logistic-ceiling` (optional, default: 1.0): Maximum adoption share (0.0-1.0)
- `--output` (optional, default: csv): csv, json, or both

**Execution**:
```bash
# Single product forecast
.claude/skills/product-demand/run_forecast.sh --product "EV_Cars" --region China --end-year 2040 --output json

# Global aggregation
.claude/skills/product-demand/run_forecast.sh --product "Solar_PV" --region Global --output both

# Custom ceiling (90% max adoption)
.claude/skills/product-demand/run_forecast.sh --product "Battery_Storage" --region Europe --ceiling 0.9
```

**Forecasting Models**:
- **Disruptor products** (BEV, Solar, Battery Storage): Logistic S-curve adoption post-tipping
- **Chimera products** (PHEV, NGV, Hybrid): Hump trajectory (rise before tipping, decay with 3-year half-life after)
- **Incumbent products** (ICE, Coal, Gas, Oil): Residual calculation (Market - Disruptor - Chimera)
- **Non-disrupted markets**: Linear baseline with CAGR cap (±5%)

**Output Format**:
- **CSV**: Year, Product_Demand, Market_Demand, Cost, [related products]
- **JSON**: Full forecast with product type, market context, tipping point, logistic parameters, validation results

**Data**: Self-contained in `.claude/skills/product-demand/data/` with 8 entity JSON files + taxonomies

**Dependencies**: Self-contained with `scripts/lib/` utilities (utils.py, cost_analyzer.py, logistic_models.py, data_loader.py, validators.py)

---

### 2. commodity-demand

**Location**: `.claude/skills/commodity-demand/`

**Purpose**: Forecast commodity demand driven by product sales AND component replacement cycles

**Scope**: Copper, Lithium, Lead, Cobalt, Aluminum, Nickel (for batteries/motors), Oil, Coal, Natural Gas (for energy)

**When to Use**:
- User asks about **commodity demand**, material requirements, supply needs, peak demand years
- Questions like: "when will [commodity] demand peak", "what is [commodity] demand for [application]"
- Calculates demand from BOTH new product sales AND installed base replacements

**Parameters**:
- `--commodity` (required): Commodity name (e.g., "lead", "copper", "lithium")
- `--region` (required): China, USA, Europe, Rest_of_World, Global
- `--end-year` (optional, default: 2040): Forecast horizon
- `--output` (optional, default: csv): csv, json, or both

**Execution**:
```bash
# Standalone commodity forecast
.claude/skills/commodity-demand/run_forecast.sh --commodity "lead" --region Global --end-year 2040 --output json
```

**Methodology**:
1. **Identify contributing products**: Find products that use this commodity (top 80% by volume)
2. **Calculate new sales demand**: `product_units × intensity_factor` (e.g., 80 kg copper per EV)
3. **Calculate replacement demand**: `installed_base × replacement_rate × intensity_factor`
4. **Aggregate**: Total = new sales + replacement across all products
5. **Validate**: Check non-negativity, smooth transitions, reasonable growth rates

**Key Data Files**:
- `commodity_intensity.json` - Intensity factors (e.g., 80 kg copper/EV, 12 kg lead/ICE starter battery)
- `replacement_cycles.json` - Replacement cycles (e.g., 3-4 years for lead batteries, 8-10 years for EV batteries)
- Entity files: `Copper.json`, `Lithium.json`, `Lead.json`, `Coal.json`, `Crude_Oil.json`, `Aluminium.json`

**Output Format**:
- **CSV**: Year, Total_Demand, New_Sales_Demand, Replacement_Demand, [by product]
- **JSON**: Full breakdown by product, intensity factors, replacement cycles, validation

**Dependencies**: Self-contained with `scripts/lib/` utilities (utils.py, validators.py)

---

### 3. disruption-analysis

**Location**: `.claude/skills/disruption-analysis/`

**Purpose**: Analyze cross-market disruption impacts and displacement timelines by synthesizing product/commodity forecasts

**Scope**: Disruption relationships across markets (EV→oil, SWB→coal/gas, EV→ICE, Solar/Wind→Fossil, etc.)

**When to Use**:
- User asks: "when will [disruptor] displace [incumbent]"
- "Based on [X] disruption when will [Y] peak"
- "When will [market] be disrupted"
- Requests for disruption analysis, displacement timelines, threshold crossings (e.g., "when 95% displaced")

**Parameters**:
- `--event` (required): Disruption event description (e.g., "EV disruption", "SWB displacement")
- `--impact` (required): Impacted market (e.g., "oil demand", "coal power", "ICE vehicles")
- `--region` (required): China, USA, Europe, Rest_of_World, Global
- `--output` (optional, default: json): json, text

**Execution**:
```bash
# Analyze EV disruption of oil demand (standalone)
.claude/skills/disruption-analysis/run_analysis.sh --event "EV disruption" --impact "oil" --region Global
```

**Known Disruption Mappings** (from `disruption_mappings.json`):
1. **EV disrupts oil**: EVs → Oil_Demand_Transportation (2.5 barrels/day per 1000 vehicles)
2. **SWB displaces coal**: Solar+Wind+Battery → Coal_Power_Generation (1:1 MWh)
3. **SWB displaces gas**: Solar+Wind+Battery → Natural_Gas_Power_Generation (1:1 MWh)
4. **EV impacts lead**: EVs reduce lead demand by eliminating starter batteries (-12 kg/vehicle)
5. **ICE decline impacts oil**: ICE vehicle decline → Oil demand decline (direct relationship)
6. **EV disrupts ICE**: EVs → ICE_Cars displacement (1:1 vehicles)
7. **Solar/Wind displaces fossil**: Solar+Wind → Coal+Gas power generation (1:1 MWh)

**Analysis Types**:
- `cross_market_impact` - Calculate impact of one market on another
- `threshold_crossing` - Detect when displacement reaches thresholds (50%, 95%, 100%)
- `peak_detection` - Identify peak demand years for incumbent
- `displacement_timeline` - Generate full displacement timeline

**Output Format**:
- **JSON**: Timeline with tipping point year, 50% displacement year, 95% displacement year, peak year, displacement rate
- **Text**: Human-readable summary with key milestones

**Dependencies**: Self-contained with `scripts/lib/` utilities (utils.py, validators.py)

---

### 4. demand-forecasting (LEGACY)

**Location**: `.claude/skills/demand-forecasting/`

**Status**: LEGACY - Superseded by `product-demand` for most use cases. Retained for backward compatibility.

**Purpose**: Cost-driven demand forecasting specifically for passenger vehicles (EV, PHEV, ICE) only

**Scope**: Passenger vehicles ONLY (EV_Cars, BEV_Cars, PHEV_Cars, ICE_Cars, Passenger_Vehicles)

**When to Use**:
- Backward compatibility with existing workflows required
- User explicitly requests legacy demand-forecasting skill
- **Recommendation**: Use `product-demand` instead for new work (same vehicles, broader capabilities)

**Parameters**:
- `--region` (required): China, USA, Europe, Rest_of_World, or Global
- `--end-year` (optional, default: 2040): Forecast horizon
- `--logistic-ceiling` (optional, default: 1.0): Maximum EV adoption share (0.0-1.0)
- `--output` (optional, default: csv): csv, json, or both

**Execution**:
```bash
# Single region forecast
.claude/skills/demand-forecasting/run_forecast.sh --region China --end-year 2040 --ceiling 1.0 --output csv

# Global forecast (all regions + aggregation)
.claude/skills/demand-forecasting/run_forecast.sh --region Global --end-year 2040 --output both
```

**Output Structure**:
- **CSV**: Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost
- **JSON**: Contains region, cost_analysis (tipping_point, CAGRs), demand_forecast (years, arrays)

**Dependencies**: Self-contained (does not import from `_forecasting_core`)

## Development Commands

### Setup

**Install dependencies for specific skill**:
```bash
# Product demand
pip install -r .claude/skills/product-demand/requirements.txt

# Commodity demand
pip install -r .claude/skills/commodity-demand/requirements.txt

# Disruption analysis
pip install -r .claude/skills/disruption-analysis/requirements.txt

# Legacy demand forecasting
pip install -r .claude/skills/demand-forecasting/requirements.txt
```

**Common dependencies** (all skills):
- Python 3.7+
- numpy >= 1.20.0
- scipy >= 1.7.0 (for differential_evolution, Theil-Sen)
- pandas >= 1.3.0

**Additional dependencies**:
- matplotlib >= 3.4.0 (for visualization, optional)

### Testing

No formal test suite exists. Validate forecasts manually using the validation checkpoints above:

**For product forecasts**:
1. Check Disruptor + Chimera + Incumbent ≤ Market (tolerance: 0.1%)
2. Verify smooth transitions near tipping year (no sudden jumps >50%)
3. Ensure no negative values
4. Confirm physically realistic growth rates (CAGR ≤ ±5% for market)
5. Validate tipping point detection (or note "no cost parity found")

**For commodity forecasts**:
1. Verify non-negative demand values
2. Check new sales + replacement = total (accounting consistency)
3. Ensure reasonable intensity factors (e.g., 80 kg copper per EV)
4. Validate replacement cycles (e.g., 3-4 years for lead batteries)

**For disruption analysis**:
1. Confirm known disruption mappings are correctly applied
2. Verify threshold crossings are monotonic (50% before 95% before 100%)
3. Check peak detection aligns with displacement timeline
4. Ensure displacement rates are physically plausible

## Critical Implementation Notes

### Universal Principles (All Skills)

1. **Regional Independence**: Each region is analyzed separately; Global is aggregated afterward (avoid double counting)

2. **Cost Curve Smoothing**: Always apply 3-year rolling median before tipping point detection to remove noise

3. **Logistic Fitting**: Uses scipy.optimize.differential_evolution with bounds:
   - k (slope): [0.05, 1.5] - Controls steepness of S-curve
   - t₀ (inflection): [min_year-5, max_year+10] - Midpoint of adoption curve

4. **Fallback Strategy**: If logistic convergence fails (<3 data points), seed with k=0.4, t₀=tipping_year or fall back to linear trend

5. **Numerical Stability**:
   - Clamp all shares to [0, 1]
   - Clamp all demands to [0, market]
   - Ensure no negative forecasts

### Edge Cases Handled

- **No tipping point found**: Use conservative baseline (k < 0.1, slow adoption) or report "no cost parity by [end_year]"
- **Logistic fitting fails to converge**: Try seeded parameters (k=0.4, t₀=tipping_year) → Linear trend with market bounds → Use recent historical trend
- **Sparse data (<3 points)**: Skip logistic fitting, use linear extrapolation with CAGR bounds
- **Data gaps in time series**: Linear interpolation between available points, flag gaps in validation report
- **Unrealistic CAGR (>±20%)**: Cap at ±5% for market, flag anomaly in output metadata

### Skill-Specific Notes

**product-demand**:
- Market CAGR capped at ±5% per year to prevent unrealistic growth/decline
- Chimera (PHEV, NGV) decay half-life: 3 years after tipping point
- Default logistic ceiling L = 1.0 (100%); use L = 0.9 if infrastructure/policy limits exist
- Tipping point determines transition dynamics for both disruptor and chimera
- Data consistency: All costs must be in real USD, normalized basis (e.g., cost per mile, cost per kWh)

**commodity-demand**:
- Intensity factors must be empirically grounded (e.g., 80 kg copper/EV, 12 kg lead/ICE starter)
- Replacement cycles vary by product (3-4 years for lead batteries, 8-10 years for EV batteries, 10-15 years for motors)
- Installed base calculated as cumulative sales minus retirements
- Top 80% contributing products by volume are included; long-tail products excluded

**disruption-analysis**:
- Disruption mappings must be physically accurate (e.g., 2.5 barrels oil/day per 1000 EVs)
- Threshold crossings must be monotonic (50% < 95% < 100%)
- Peak detection looks backward from end_year to find maximum incumbent demand
- Cross-market impacts can be positive (new demand) or negative (displacement)

## Important Constraints

### Universal Constraints
- **Regions**: China, USA, Europe, Rest_of_World, Global ONLY (no other regions supported)
- **Forecast horizon**: 2025-2100 (default: 2040)
- **Market CAGR cap**: ±5% per year to prevent unrealistic growth/decline
- **Validation tolerance**: ±0.1% for sum consistency checks
- **Smoothing window**: 3-year rolling median for cost curves

### Product-Specific Constraints
- **Logistic ceiling**: Default L = 1.0 (100%); use L = 0.9 if infrastructure/policy limits exist
- **Chimera decay**: Half-life = 3 years after tipping point
- **Tipping point**: Determines transition dynamics for disruptor, chimera, incumbent

### Commodity-Specific Constraints
- **Intensity factors**: Must be realistic and empirically validated
- **Replacement cycles**: Must reflect actual product lifetimes
- **Contributing products**: Top 80% by volume (long tail excluded)

### Data Format Constraints
- All costs: Real USD (not nominal), normalized basis
- All demands: Units must be consistent within entity (e.g., million vehicles, TWh, million tonnes)
- Time series: Annual data, no gaps or missing years in historical data

## Data Loading Patterns

### Using Core Library (Recommended)

```python
import sys
sys.path.insert(0, '.claude/skills/_forecasting_core')

from core.data_loader import load_curves, load_taxonomy

# Load taxonomy
taxonomy = load_taxonomy('passenger_vehicles_taxonomy_and_datasets.json')

# Load curves for entity
curves = load_curves('Passenger_Cars.json')

# Access specific metric
ev_cost_china = curves['Passenger Cars']['EV_Cars_Cost']['regions']['China']
years = ev_cost_china['X']
costs = ev_cost_china['Y']
```

### Direct JSON Loading (Alternative)

```python
import json
import os

# Load from skill's data directory
skill_data_dir = '.claude/skills/product-demand/data/'

# Load taxonomy
taxonomy_path = os.path.join(skill_data_dir, 'passenger_vehicles_taxonomy_and_datasets.json')
with open(taxonomy_path) as f:
    taxonomy = json.load(f)

# Load entity curves
entity_path = os.path.join(skill_data_dir, 'Passenger_Cars.json')
with open(entity_path) as f:
    curves = json.load(f)['Passenger Cars']

# Access specific metric
ev_cost_china = curves['EV_Cars_Cost']['regions']['China']
years = ev_cost_china['X']
costs = ev_cost_china['Y']
```

### Using Skill Directly (Programmatic)

```python
import sys
sys.path.insert(0, '.claude/skills/product-demand/scripts')

from forecast import ForecastOrchestrator

# Initialize forecaster
forecaster = ForecastOrchestrator(
    product="EV_Cars",
    end_year=2040,
    logistic_ceiling=1.0
)

# Run forecast
result = forecaster.forecast_region("China")

# Export results
forecaster.export_to_csv(result, "output.csv", "China")
forecaster.export_to_json(result, "output.json")
```

## Quick Start Examples

### Example 1: Product Demand Forecast

```bash
# Forecast EV adoption in China through 2040
.claude/skills/product-demand/run_forecast.sh \
  --product "EV_Cars" \
  --region China \
  --end-year 2040 \
  --output json
```

### Example 2: Commodity Demand Forecast

```bash
# Forecast lithium demand driven by EV adoption
.claude/skills/commodity-demand/run_forecast.sh \
  --commodity "lithium" \
  --region Global \
  --end-year 2040 \
  --output csv
```

### Example 3: Disruption Analysis

```bash
# Analyze when EVs will disrupt oil demand
.claude/skills/disruption-analysis/run_analysis.sh \
  --event "EV disruption" \
  --impact "oil" \
  --region Global \
  --output json
```

### Example 4: Multiple Independent Forecasts

```bash
# Run multiple independent forecasts (no chaining required)

# 1. Generate EV forecast
.claude/skills/product-demand/run_forecast.sh \
  --product "EV_Cars" \
  --region China \
  --output json

# 2. Calculate copper demand (standalone, uses internal estimation)
.claude/skills/commodity-demand/run_forecast.sh \
  --commodity "copper" \
  --region China \
  --output json

# 3. Analyze disruption impact (standalone, uses internal estimation)
.claude/skills/disruption-analysis/run_analysis.sh \
  --event "EV disruption" \
  --impact "oil" \
  --region China \
  --output json
```
