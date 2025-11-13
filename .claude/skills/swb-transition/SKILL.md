---
name: swb-transition
description: >
  Models electricity system transition from coal/gas to Solar-Wind-Battery (SWB) stack based on LCOE/SCOE cost parity.
  Use when analyzing energy transition, renewable vs fossil displacement, grid decarbonization, or SWB economics.
  Handles regions: China, USA, Europe, Rest_of_World, Global.
  Tracks tipping points when SWB becomes cheaper than coal and gas separately.
  Models capacity expansion, generation displacement, and battery storage requirements.
  Features configurable displacement sequencing (coal-first vs gas-first) by region.
  Trigger keywords: energy transition, swb stack, solar wind battery, coal gas displacement, renewable vs fossil, grid transition, LCOE analysis. (project)
---

# Solar-Wind-Battery Energy Transition Skill

This skill models the economic-driven transition from fossil fuels (coal/gas) to renewable energy (Solar+Wind+Battery stack) in the electricity system, using LCOE/SCOE cost parity analysis and displacement sequencing.

## Overview

The skill forecasts the energy transition across:
- **Disruptors (SWB Stack)**:
  - Solar PV (utility-scale)
  - Wind (onshore and offshore)
  - Battery Energy Storage (4-hour default)
- **Incumbents**:
  - Coal power plants
  - Natural gas power plants
- **Supporting**:
  - Nuclear, hydro, other renewables (maintained baseline)

## Key Features

### Cost-Driven Tipping Points
- **LCOE Comparison**: Solar, Wind vs Coal, Gas ($/MWh)
- **SCOE Addition**: Storage Cost of Energy for batteries
- **Stack Cost**: MAX(Solar, Wind) + SCOE (conservative approach)
- **Dual Tipping Points**: Separate for vs-coal and vs-gas

### Generation & Capacity Modeling
- **Capacity-Generation Linkage**: Gen = Capacity × CF × 8760
- **Capacity Factors**: Regional trajectories with improvement
- **Approach**: Forecast capacity, derive generation

### Displacement Sequencing
- **Coal-First**: Default for China, Europe (environmental priority)
- **Gas-First**: Default for USA (economics + flexibility)
- **Reserve Floors**: Minimum coal (10%) and gas (15%) of peak load

### Battery Storage Sizing
- **Resilience Heuristic**: k_days × Peak_Load × 24 hours
- **Duration**: 4-hour default, configurable
- **Throughput**: 250 cycles/year typical

## Usage

```bash
# Run the SWB transition forecast
skill swb-transition

# With custom parameters
skill swb-transition --end-year 2045 --region China --sequence coal-first

# Generate cost comparison
skill swb-transition --analyze-lcoe --output-format csv
```

## Parameters

Key parameters configured in `config.json`:

### Cost Parameters
- **Solar LCOE**: Declining trajectory (learning rate ~20%)
- **Wind LCOE**: Declining trajectory (learning rate ~15%)
- **Battery SCOE**: Based on CapEx, cycles, duration, RTE
- **Coal LCOE**: Flat/rising with carbon pricing
- **Gas LCOE**: Variable with fuel prices

### Capacity Factors (Regional)
- **Solar**: 15-25% typical, improving 0.2-0.3 pp/year
- **Onshore Wind**: 25-35% typical, improving 0.2-0.3 pp/year
- **Offshore Wind**: 35-50% typical, improving 0.3-0.5 pp/year
- **Coal**: 50-70% (dispatchable)
- **Gas**: 30-50% (peaking/intermediate)

### Displacement Parameters
- **Sequence**: Coal-first or gas-first by region
- **Reserve Floors**: Coal 10%, Gas 15% of peak
- **Non-SWB Baseline**: Nuclear + hydro (0-2% annual decline)

## Outputs

The skill generates:
1. Annual generation by technology (TWh)
2. Installed capacity evolution (GW)
3. LCOE/SCOE cost curves ($/MWh)
4. Tipping point years (vs coal, vs gas)
5. Displacement amounts (TWh displaced)
6. Battery storage requirements (GWh)
7. CO₂ emissions reduction (Mt)
8. Regional and global aggregates

## Data Requirements

### Available Datasets
- **Generation**: `X_Annual_Power_Generation_<region>` by technology
- **Capacity**: `X_Installed_Capacity_<region>` by technology
- **Costs**: `X_LCOE_<region>`, `Battery_Energy_Storage_System_Cost_<region>`
- **Capacity Factors**: `X_Capacity_Factor_<region>`
- **Electricity Demand**: `Electricity_Annual_Production_<region>`

### Derived Metrics
- New capacity: Difference in consecutive year installed capacity
- Peak load: Annual_TWh × 1000 / 8760 × Load_Factor
- Residual demand: Total - SWB - Non-SWB_Fixed

## Validation

The skill validates:
- Energy balance: Generation ≈ Demand (±2%)
- Capacity factors within reasonable bounds
- Non-negativity on all generation/capacity
- Reserve requirements maintained
- Smooth transitions (no sudden jumps)

## Scenarios

Pre-configured scenarios:
- **Baseline**: Current policy trajectories
- **Accelerated**: Faster cost declines, early coal phase-out
- **Delayed**: Slower transition, gas bridge extended
- **High Renewable**: 80%+ renewable by 2040
- **Carbon Pricing**: Explicit carbon cost on fossils

## Regional Considerations

### Displacement Sequencing
- **China**: Coal-first (air quality, climate commitments)
- **Europe**: Coal-first (carbon pricing, green policies)
- **USA**: Gas-first (cheap gas, flexible generation)
- **Rest_of_World**: Mixed, country-specific

### Cost Adjustments
- Regional cost multipliers for technologies
- Local content requirements impact
- Grid integration costs vary by region

## Technical Details

- **Horizon**: 15-25 years (2024-2045/2050)
- **Time Step**: Annual
- **Primary Units**: TWh (generation), GW (capacity), $/MWh (costs)
- **Emissions Factors**: Coal 0.9-1.0 tCO₂/MWh, Gas 0.4-0.5 tCO₂/MWh

## Cost Forecasting Method

1. Transform costs to log scale
2. Calculate long-run CAGR
3. Project forward with learning rates
4. Apply 3-year rolling median smoothing
5. Check for floor costs (technology limits)

## Battery Integration

Battery storage requirements based on:
- Renewable penetration level
- Grid stability requirements
- Peak load coverage (1-4 days typical)
- Economic optimization vs reliability

## References

Based on:
- IEA World Energy Outlook scenarios
- IRENA renewable cost databases
- Regional grid operator studies
- Energy transition literature