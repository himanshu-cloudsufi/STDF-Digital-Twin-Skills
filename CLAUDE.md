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

The forecasting system uses a **fully independent multi-skill architecture** with two specialized, self-contained skills.

### Architecture Diagram

```
    ├── energy-forecasting   (Solar-Wind-Battery systems, fossil displacement)
    │   └── scripts/lib/     (self-contained utilities)
    │
    └── demand-forecasting   (EV/Passenger vehicle demand forecasting)
        └── scripts/         (self-contained, no lib/)
```

### Skill Independence

Each skill is completely self-contained:

- **No cross-skill dependencies**: Each skill operates independently without requiring outputs from other skills
- **Self-contained utilities**: Each skill has its own `scripts/lib/` directory with necessary utility functions
- **Independent data access**: Each skill only accesses data within its own directory structure
- **Standalone execution**: Skills can be run in isolation without any coordination

### Shared Utility Code

The energy-forecasting skill contains core utilities in `scripts/lib/`:

- `utils.py` - CAGR calculation, smoothing, interpolation, linear extrapolation
- `cost_analyzer.py` - LCOE/SCOE calculation, tipping point detection
- `capacity_forecast.py` - YoY growth averaging for capacity forecasting
- `generation_derivation.py` - Capacity-to-generation conversion via capacity factors
- `displacement_logic.py` - Coal/gas displacement sequencing
- `data_loader.py` - Taxonomy-driven data loading
- `validators.py` - Forecast validation, energy balance checks

**Note**: Each skill is fully self-contained to ensure complete independence.

## Core Forecasting Methodologies

### Vehicle Demand Forecasting (demand-forecasting skill)

Located in `instructions_editable.md`, the methodology follows this pipeline:

1. **Cost Curve Forecasting**: Log-CAGR extrapolation with 3-year rolling median smoothing
2. **Tipping Point Detection**: First year when EV cost < ICE cost (cost per mile)
3. **Market Demand Forecast**: Linear extrapolation using Theil-Sen robust regression, capped at ±5% CAGR
4. **BEV Forecast**: Logistic curve fitting post-tipping: `s(t) = L / (1 + exp(-k * (t - t₀)))`
5. **PHEV Forecast**: "Hump" trajectory rising before tipping, decaying with 3-year half-life after
6. **ICE Forecast**: Residual calculation: `ICE = max(Market - BEV - PHEV, 0)`
7. **Validation**: Ensure BEV + PHEV + ICE ≤ Market, all values ≥ 0, smooth transitions

### Energy Forecasting (energy-forecasting skill)

Methodology documented in `.claude/skills/energy-forecasting/reference/`:

1. **Cost Analysis**: Calculate SWB stack cost (MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE) vs Coal/Gas LCOE
2. **Tipping Point Detection**: Year when SWB cost < min(Coal_LCOE, Gas_LCOE)
3. **Capacity Forecasting**: YoY growth averaging (not logistic S-curve) for Solar, Wind, Battery
4. **Generation Derivation**: Convert capacity to generation using capacity factors (Capacity × CF × 8760)
5. **Displacement Sequencing**: Coal-first (China, Europe, RoW) or Gas-first (USA)
6. **Residual Allocation**: Nuclear, hydro, and remaining fossil generation
7. **Validation**: Energy balance (±2%), capacity factor bounds, reserve floors, non-negativity

### Validation Checkpoints

Use these quick checks before/after major operations:

**Before running forecast:**
- [ ] Region parameter is valid (China, USA, Europe, Rest_of_World, Global)
- [ ] End year is reasonable (2025-2100)
- [ ] Skill selection matches user query intent (energy vs vehicles)
- [ ] Required data files exist in skill's data directory

**After forecast completes:**
- [ ] No negative values in any year (demand/capacity/generation)
- [ ] Balance constraints satisfied (see skill-specific testing sections)
- [ ] Smooth year-over-year transitions (no sudden jumps >50%)
- [ ] Tipping point detected or explicitly noted as "none found"

**Before presenting results:**
- [ ] Output format matches user request (csv/json/both)
- [ ] Parameters are physically reasonable (see skill-specific constraints)
- [ ] Terminology follows guardrails (no "transition", use "transformation")

## Skill Selection Guide

### Decision Tree: Which Skill to Use?

```
User Query → Analyze Keywords → Select Skill

Is it about ENERGY (solar, wind, battery, SWB, electricity, coal/gas displacement)?
    → Use energy-forecasting

Is it about PASSENGER VEHICLES / EVs (BEV, PHEV, ICE demand/adoption)?
    → Use demand-forecasting
```

### Trigger Keywords by Skill

| Skill | Use When Query Contains | Example Questions |
|-------|------------------------|-------------------|
| **energy-forecasting** | solar, wind, battery, SWB, renewable, clean energy, electricity, generation, capacity, coal, gas, displacement, LCOE, cost parity, energy transformation, disruption, fossil fuel, stellar energy | "What is solar capacity in China by 2040?"<br>"When will SWB reach cost parity?"<br>"Forecast wind generation in Europe"<br>"When will coal be displaced?"<br>"SWB vs fossil fuel generation"<br>"Battery storage growth" |
| **demand-forecasting** | EV, BEV, PHEV, ICE, passenger vehicles, passenger cars, electric vehicle adoption, vehicle demand, EV sales, car market, automotive, tipping point (vehicles), cost per mile | "What is EV demand in China by 2040?"<br>"When will EVs reach cost parity?"<br>"Forecast BEV adoption in Europe"<br>"When will ICE vehicles decline?"<br>"Passenger car market transformation"<br>"EV vs ICE market share" |

### Quick Reference: Skill Capabilities

#### energy-forecasting
- **Scope**: Solar-Wind-Battery (SWB) systems and fossil fuel displacement
- **Technologies**: Solar PV, CSP, Onshore Wind, Offshore Wind, Battery Storage, Coal Power, Natural Gas Power
- **Methodology**: Cost-driven (LCOE+SCOE), YoY growth averaging, sequenced coal/gas displacement
- **Output**: Capacity forecasts, generation forecasts, displacement timelines, tipping point analysis
- **When**: User asks about renewable/clean energy capacity, solar/wind/battery forecasts, electricity generation, fossil fuel displacement, SWB adoption, cost parity, energy transformation

#### demand-forecasting
- **Scope**: Passenger vehicles (EV, BEV, PHEV, ICE)
- **Methodology**: Cost-driven ($/mile), logistic S-curve adoption modeling, chimera decay, residual calculation
- **Output**: Vehicle demand forecasts (BEV, PHEV, ICE), market projections, tipping point analysis
- **When**: User asks about passenger vehicle demand, EV adoption, BEV/PHEV/ICE sales forecasts, automotive market transformation, vehicle cost parity

### Independent Execution

Each skill operates completely independently:

```bash
# Energy forecasting - standalone
.claude/skills/energy-forecasting/run_forecast.sh --region China --end-year 2040 --output json

# Legacy demand forecasting - standalone
.claude/skills/demand-forecasting/run_forecast.sh --region China --end-year 2040 --output csv
```

**Note**: Each skill is fully self-contained with no cross-skill dependencies.

## Skills Reference

This section documents all forecasting skills in detail.

### 1. energy-forecasting

**Location**: `.claude/skills/energy-forecasting/`

**Purpose**: Cost-driven forecasting for Solar-Wind-Battery (SWB) energy systems and fossil fuel displacement

**Scope**:
- **SWB Components**: Solar PV, CSP, Onshore Wind, Offshore Wind, Battery Storage (2/4/8-hour)
- **Fossil Incumbents**: Coal Power, Natural Gas Power
- **Non-SWB Technologies**: Nuclear, Hydro, Other Renewables

**When to Use**:
- User asks about **renewable/clean energy capacity**, solar/wind/battery forecasts, electricity generation, fossil fuel displacement
- Questions like: "when will solar reach cost parity", "forecast wind capacity", "when will coal be displaced", "SWB generation by 2040", "battery storage growth", "renewable energy disruption"
- Examples: SWB adoption, LCOE analysis, electricity generation mix, coal/gas displacement timelines, energy transformation

**Parameters**:
- `--region` (required): China, USA, Europe, Rest_of_World, Global
- `--end-year` (optional, default: 2040): Forecast horizon
- `--battery-duration` (optional, default: 4): Battery duration in hours (2, 4, or 8)
- `--output` (optional, default: csv): csv, json, or both

**Execution**:
```bash
# Single region forecast
.claude/skills/energy-forecasting/run_forecast.sh --region China --end-year 2040 --output csv

# Global aggregation
.claude/skills/energy-forecasting/run_forecast.sh --region Global --end-year 2050 --output both

# Custom battery duration (8-hour)
.claude/skills/energy-forecasting/run_forecast.sh --region USA --battery-duration 8 --output json
```

**Forecasting Process**:
1. **Cost Analysis**: Calculate SWB stack cost (MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE) vs Coal/Gas LCOE
2. **Tipping Point Detection**: Identify year when SWB cost < min(Coal_LCOE, Gas_LCOE)
3. **Capacity Forecasting**: YoY growth averaging for Solar, Onshore Wind, Offshore Wind, Battery Storage
4. **CSP Handling**: Include CSP conditionally if capacity > 1% of Solar PV
5. **Generation Derivation**: Convert capacity to generation using capacity factors
6. **Displacement Sequencing**: Model coal-first (China, Europe, RoW) or gas-first (USA) displacement
7. **Residual Allocation**: Calculate nuclear, hydro, and remaining fossil generation
8. **Validation**: Energy balance, capacity factor bounds, reserve floors (10% coal, 15% gas), non-negativity

**Key Methodology Differences** (vs Passenger Vehicle Forecasting):
- Uses **YoY growth averaging** (not logistic S-curve)
- Multi-component disruptor: SWB stack (Solar + Wind + Battery)
- Sequenced displacement: Coal-first vs gas-first by region
- Capacity-generation conversion via capacity factors
- LCOE + SCOE cost calculations (not $/mile)
- Reserve floors: 10% coal, 15% gas until full displacement

**Output Format**:
- **CSV**: Year, Solar_Capacity, Wind_Capacity, Battery_Capacity, SWB_Generation, Coal_Generation, Gas_Generation, Total_Generation
- **JSON**: Full forecast with cost analysis (tipping point, LCOE, SCOE), capacity forecasts, generation forecasts, displacement timeline, validation results

**Data**: Self-contained in `.claude/skills/energy-forecasting/data/` with Energy_Generation.json, Energy_Storage.json, Electricity.json, swb_taxonomy_and_datasets.json

**Dependencies**: Self-contained with `scripts/lib/` utilities (utils.py, cost_analyzer.py, capacity_forecast.py, generation_derivation.py, displacement_logic.py, data_loader.py, validators.py)

---

### 2. demand-forecasting

**Location**: `.claude/skills/demand-forecasting/`

**Purpose**: Cost-driven demand forecasting for passenger vehicles and electric vehicle adoption

**Scope**: Passenger vehicles (EV_Cars, BEV_Cars, PHEV_Cars, ICE_Cars, Passenger_Vehicles)

**When to Use**:
- User asks about **passenger vehicle demand**, EV adoption, BEV/PHEV/ICE sales forecasts
- Questions like: "when will EVs reach [threshold]", "what is BEV demand in [region]", "when will ICE vehicles decline"
- Examples: EV adoption, passenger car market transformation, vehicle cost parity, automotive disruption, BEV vs ICE market share

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

**Forecasting Models**:
- **BEV (Disruptor)**: Logistic S-curve adoption post-tipping point
- **PHEV (Chimera)**: Hump trajectory - rises before tipping, decays with 3-year half-life after
- **ICE (Incumbent)**: Residual calculation (Market - BEV - PHEV)
- **Market**: Linear extrapolation with CAGR cap (±5%)

**Output Structure**:
- **CSV**: Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost
- **JSON**: Contains region, cost_analysis (tipping_point, CAGRs), demand_forecast (years, arrays), logistic parameters, validation results

**Dependencies**: Self-contained utilities in `scripts/` (cost_analysis.py, data_loader.py, demand_forecast.py, utils.py)

## Development Commands

### Setup

**Install dependencies for specific skill**:
```bash
# Energy forecasting (Solar-Wind-Battery systems)
pip install -r .claude/skills/energy-forecasting/requirements.txt

# Demand forecasting (EV/Passenger vehicles)
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

**For energy forecasts**:
1. **Energy Balance**: Total generation = SWB + Coal + Gas + Nuclear + Hydro (within ±2% tolerance)
2. **Non-negativity**: All capacity and generation values ≥ 0
3. **Smooth Transitions**: No sudden jumps >50% YoY
4. **Capacity Factor Bounds**: All CFs within [0.05, 0.70] range
5. **Reserve Floors**: Coal ≥ 10% and Gas ≥ 15% until full displacement
6. **Displacement Sequence**: Coal-first (China, Europe, RoW) or Gas-first (USA)
7. **Tipping Point**: SWB cost < min(Coal, Gas) LCOE identified (or noted as "not found")
8. **CSP Inclusion**: Only included if capacity > 1% of Solar PV

**For vehicle demand forecasts**:
1. Check BEV + PHEV + ICE ≤ Market (tolerance: 0.1%)
2. Verify smooth transitions near tipping year (no sudden jumps >50%)
3. Ensure no negative values
4. Confirm physically realistic growth rates (CAGR ≤ ±5% for market)
5. Validate tipping point detection (or note "no cost parity found")
6. Verify logistic parameters are physically reasonable (k ∈ [0.05, 1.5])
7. Check PHEV chimera decay follows 3-year half-life post-tipping

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

**energy-forecasting**:
- Uses YoY growth averaging (not logistic S-curve) for capacity forecasting
- SWB stack cost = MAX(Solar_LCOE, Wind_LCOE) + Battery_SCOE
- Displacement sequence varies by region: coal-first (China, Europe, RoW), gas-first (USA)
- Reserve floors enforced: 10% coal, 15% gas until full displacement
- Capacity factors improve linearly by 0.3% per year (configurable)
- CSP included conditionally if capacity > 1% of Solar PV
- Battery duration options: 2, 4, or 8 hours (default: 4)
- Energy balance tolerance: ±2% (configurable)
- Data consistency: LCOE in $/MWh, capacity in GW, generation in TWh

**demand-forecasting**:
- Uses logistic S-curve for BEV adoption post-tipping point
- Market CAGR capped at ±5% per year to prevent unrealistic growth/decline
- Chimera (PHEV) decay half-life: 3 years after tipping point
- Default logistic ceiling L = 1.0 (100%); use L = 0.9 if infrastructure/policy limits exist
- Tipping point year: First year when EV cost < ICE cost (cost per mile)
- ICE demand calculated as residual: max(Market - BEV - PHEV, 0)
- Data consistency: All costs must be in real USD, normalized basis ($/mile)

## Important Constraints

### Universal Constraints
- **Regions**: China, USA, Europe, Rest_of_World, Global ONLY (no other regions supported)
- **Forecast horizon**: 2025-2100 (default: 2040)
- **Validation tolerance**: ±2% for energy balance checks
- **Smoothing window**: 3-year rolling median for cost curves

### Energy-Specific Constraints
- **Battery duration**: 2, 4, or 8 hours only (default: 4)
- **Reserve floors**: 10% coal, 15% gas minimum until full displacement
- **Capacity factors**: Must be within [0.05, 0.70] range
- **YoY growth cap**: ±50% maximum year-over-year capacity growth
- **CSP threshold**: Only included if capacity > 1% of Solar PV
- **Displacement sequence**: Coal-first (China, Europe, RoW), Gas-first (USA)

### Vehicle Demand Constraints
- **Logistic ceiling**: Default L = 1.0 (100%); use L = 0.9 if infrastructure/policy limits exist
- **Chimera decay**: Half-life = 3 years after tipping point
- **Market CAGR cap**: ±5% per year to prevent unrealistic growth/decline
- **Validation tolerance**: ±0.1% for sum consistency checks
- **Logistic parameters**: k (slope) ∈ [0.05, 1.5], t₀ (inflection) ∈ [min_year-5, max_year+10]

### Data Format Constraints
- **Energy**: LCOE in $/MWh, capacity in GW, generation in TWh
- **Vehicles**: Costs in $/mile (real USD), demand in million vehicles
- Time series: Annual data, no gaps or missing years in historical data

## Data Loading Patterns

### Direct JSON Loading (for Energy Data)

```python
import json
import os

# Load from skill's data directory
skill_data_dir = '.claude/skills/energy-forecasting/data/'

# Load taxonomy
taxonomy_path = os.path.join(skill_data_dir, 'swb_taxonomy_and_datasets.json')
with open(taxonomy_path) as f:
    taxonomy = json.load(f)

# Load energy generation curves
generation_path = os.path.join(skill_data_dir, 'Energy_Generation.json')
with open(generation_path) as f:
    generation_curves = json.load(f)

# Load energy storage curves
storage_path = os.path.join(skill_data_dir, 'Energy_Storage.json')
with open(storage_path) as f:
    storage_curves = json.load(f)

# Access specific metric (e.g., Solar LCOE)
solar_lcoe_china = generation_curves['Energy Generation']['Solar_PV_LCOE']['regions']['China']
years = solar_lcoe_china['X']
lcoe_values = solar_lcoe_china['Y']
```

### Using Skill Directly (Programmatic)

```python
import sys
sys.path.insert(0, '.claude/skills/energy-forecasting/scripts')

from energy_forecast import EnergyForecastOrchestrator

# Initialize forecaster
forecaster = EnergyForecastOrchestrator(
    region="China",
    end_year=2040,
    battery_duration=4
)

# Run forecast
result = forecaster.run_forecast()

# Export results
forecaster.export_to_csv(result, "output/China_2040.csv")
forecaster.export_to_json(result, "output/China_2040.json")
```

## Quick Start Examples

### Example 1: Energy Capacity & Generation Forecast

```bash
# Forecast SWB adoption and fossil displacement in China through 2040
.claude/skills/energy-forecasting/run_forecast.sh \
  --region China \
  --end-year 2040 \
  --output json
```

### Example 2: Global Energy Transformation

```bash
# Analyze global energy transformation (all regions + aggregation)
.claude/skills/energy-forecasting/run_forecast.sh \
  --region Global \
  --end-year 2050 \
  --output both
```

### Example 3: Custom Battery Duration

```bash
# Forecast USA with 8-hour battery storage
.claude/skills/energy-forecasting/run_forecast.sh \
  --region USA \
  --battery-duration 8 \
  --end-year 2040 \
  --output csv
```

### Example 4: Regional Comparison

```bash
# Run forecasts for all regions independently

# China (coal-first displacement)
.claude/skills/energy-forecasting/run_forecast.sh --region China --output json

# USA (gas-first displacement)
.claude/skills/energy-forecasting/run_forecast.sh --region USA --output json

# Europe (coal-first displacement)
.claude/skills/energy-forecasting/run_forecast.sh --region Europe --output json

# Rest of World
.claude/skills/energy-forecasting/run_forecast.sh --region Rest_of_World --output json
```
