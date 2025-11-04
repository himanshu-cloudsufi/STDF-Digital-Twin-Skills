# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **cost-driven demand forecasting system** for analyzing technology transitions in passenger vehicles (EV, PHEV, ICE) across global regions. The system predicts when disruptor technologies (EVs) will achieve cost parity with incumbents (ICE vehicles) and models subsequent market adoption using logistic growth curves.

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
- **Disruptor**: Electric Vehicles (BEV)
- **Chimera**: Plug-in Hybrid Vehicles (PHEV)
- **Incumbent**: Internal Combustion Engine vehicles (ICE)
- **Regions**: China, USA, Europe, Rest_of_World, Global (aggregated)

## Data Architecture

### Curves Catalog Structure
- **Location**: `curves_catalog_files/`
- **Format**: Split by entity (20 entities, 235 metrics, 825 datasets)
- **Key Entity**: `Passenger_Cars.json` contains all cost and demand curves for vehicle forecasting
- **Index**: `_index.json` provides metadata about available entities

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
- **File**: `passenger_vehicles_taxonomy_and_datasets.json`
- **Purpose**: Maps product types (EV_Cars, BEV_Cars, PHEV_Cars, ICE_Cars) to dataset names
- **Entity Types**: Defines whether each product is disruptor, incumbent, chimera, or market

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
- [ ] Required data files exist (Passenger_Cars.json, taxonomy)

**After forecast completes:**
- [ ] No negative demand values in any year
- [ ] BEV + PHEV + ICE ≤ Market (tolerance: 0.1%)
- [ ] Smooth year-over-year transitions (no sudden jumps >50%)
- [ ] Tipping point detected or explicitly noted as "none found"

**Before presenting results:**
- [ ] Output format matches user request (csv/json/both)
- [ ] Logistic parameters are physically reasonable (k ∈ [0.05, 1.5])
- [ ] Terminology follows guardrails (no "transition", use "transformation")

## Demand Forecasting Skill

### Location
`.claude/skills/demand-forecasting/`

### Module Structure
- `scripts/forecast.py` - Main orchestration (ForecastOrchestrator class)
- `scripts/data_loader.py` - Data loading utilities
- `scripts/cost_analysis.py` - Cost curve analysis and tipping point detection
- `scripts/demand_forecast.py` - Demand forecasting logic (logistic curves)
- `scripts/utils.py` - Helper functions
- `data/` - Self-contained datasets (Passenger_Cars.json, taxonomy, etc.)

### Running Forecasts

**Command Line (using wrapper script - recommended):**
```bash
# Single region forecast
.claude/skills/demand-forecasting/run_forecast.sh --region China --end-year 2040 --ceiling 1.0 --output csv

# Global forecast (all regions + aggregation)
.claude/skills/demand-forecasting/run_forecast.sh --region Global --end-year 2040 --output both

# Custom EV ceiling (90% max adoption)
.claude/skills/demand-forecasting/run_forecast.sh --region Europe --ceiling 0.9 --output json
```

**Direct Python (alternative method):**
```bash
cd .claude/skills/demand-forecasting && python3.12 scripts/forecast.py --region Europe --end-year 2050 --output json
```

**Programmatic:**
```python
import sys
import os
sys.path.insert(0, '.claude/skills/demand-forecasting/scripts')
from forecast import ForecastOrchestrator

forecaster = ForecastOrchestrator(end_year=2040, logistic_ceiling=1.0)
result = forecaster.forecast_region("China")
global_result = forecaster.forecast_global()
forecaster.export_to_csv(result, "output.csv", "China")
```

### Parameters
- **region** (required): China, USA, Europe, Rest_of_World, or Global
- **end_year** (optional, default: 2040): Forecast horizon
- **logistic_ceiling** (optional, default: 1.0): Maximum EV adoption share (0.0-1.0)
- **output** (optional, default: csv): csv, json, or both

### Output Structure
**CSV format**: Year, Market, BEV, PHEV, ICE, EV, EV_Cost, ICE_Cost

**JSON format**: Contains region, cost_analysis (tipping_point, CAGRs), demand_forecast (years, arrays)

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r .claude/skills/demand-forecasting/requirements.txt
```

### Testing
No formal test suite exists. Validate forecasts manually by:
1. Checking BEV + PHEV + ICE ≤ Market (with small epsilon)
2. Verifying smooth transitions near tipping year
3. Ensuring no negative values
4. Confirming physically realistic growth rates

## Critical Implementation Notes

1. **Regional Independence**: Each region is analyzed separately; Global is aggregated afterward (avoid double counting)

2. **Cost Curve Smoothing**: Always apply 3-year rolling median before tipping point detection to remove noise

3. **Logistic Fitting**: Uses scipy.optimize.differential_evolution with bounds:
   - k (slope): [0.05, 1.5]
   - t₀ (inflection): [min_year-5, max_year+10]

4. **Fallback Strategy**: If logistic convergence fails (<3 data points), seed with k=0.4, t₀=tipping_year or fall back to linear trend

   **Edge cases handled:**
   - **No tipping point found**: Use conservative baseline (k < 0.1, slow adoption) or report "no cost parity by [end_year]"
   - **Logistic fitting fails to converge**: Try seeded parameters (k=0.4, t₀=tipping_year) → Linear trend with market bounds → Use recent historical trend
   - **Sparse data (<3 points)**: Skip logistic fitting, use linear extrapolation with CAGR bounds
   - **Data gaps in time series**: Linear interpolation between available points, flag gaps in validation report
   - **Unrealistic CAGR (>±20%)**: Cap at ±5% for market, flag anomaly in output metadata

5. **Numerical Stability**:
   - Clamp all shares to [0, 1]
   - Clamp all demands to [0, market]
   - Ensure no negative forecasts

6. **Data Consistency**: All costs must be in real USD, normalized basis (e.g., cost per mile or per vehicle at same trim level)

## Important Constraints

- Market CAGR capped at ±5% per year to prevent unrealistic growth/decline
- PHEV decay half-life: 3 years after tipping point
- Default logistic ceiling L = 1.0 (100%); use L = 0.9 if infrastructure/policy limits exist
- Tipping point determines transition dynamics for both disruptor and chimera

## Data Loading Pattern

```python
import json
import os

# Load taxonomy
with open('passenger_vehicles_taxonomy_and_datasets.json') as f:
    taxonomy = json.load(f)

# Load curves from catalog
with open('curves_catalog_files/Passenger_Cars.json') as f:
    curves = json.load(f)['Passenger Cars']

# Access specific metric
ev_cost_china = curves['EV_Cars_Cost']['regions']['China']
years = ev_cost_china['X']
costs = ev_cost_china['Y']
```

## Dependencies

- Python 3.7+
- numpy >= 1.20.0
- scipy >= 1.7.0 (for differential_evolution, Theil-Sen)
- pandas >= 1.3.0
- matplotlib >= 3.4.0 (for visualization)
