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

## Table of Contents
- [Available Datasets](#available-datasets)
- [Overview](#overview)
- [Key Features](#key-features)
- [Usage](#usage)
- [Parameters](#parameters)
- [Outputs](#outputs)
- [Data Requirements](#data-requirements)
- [Validation](#validation)
- [Scenarios](#scenarios)
- [Regional Considerations](#regional-considerations)
- [Technical Details](#technical-details)

## Available Datasets

**CRITICAL FOR PLANNING:** The following datasets drive the SWB transition model:

### ✅ Disruptor Technologies (SWB Stack)
- **Solar LCOE:** `Solar_Photovoltaic_LCOE_{Region}` (China, USA, Global)
- **Onshore Wind LCOE:** `Onshore_Wind_LCOE_{Region}` (China, USA, Global)
- **Offshore Wind LCOE:** `Offshore_Wind_LCOE_{Region}` (China, USA, Global)
- **Battery Cost:** `Battery_Energy_Storage_System_Cost_{Region}` (various durations)
- **Solar Capacity:** `Solar_Installed_Capacity_{Region}` (Global, cumulative)
- **Onshore Wind Capacity:** `Onshore_Wind_Installed_Capacity_{Region}` (Global, cumulative)
- **Offshore Wind Capacity:** `Offshore_Wind_Installed_Capacity_{Region}` (Global, cumulative)
- **Battery Capacity:** `Battery_Energy_Storage_System_Installed_Capacity_{Region}` (Global)
- **Solar Generation:** `Solar_Annual_Power_Generation_{Region}` (Global)
- **Wind Generation:** `Wind_Annual_Power_Generation_{Region}` (Global)
- **Solar CF:** `Solar_Photovoltaic_Capacity_Factor_{Region}` (15-25%, improving)
- **Onshore Wind CF:** `Onshore_Wind_Capacity_Factor_{Region}` (25-35%, improving)
- **Offshore Wind CF:** `Offshore_Wind_Capacity_Factor_{Region}` (35-50%, improving)

### ❌ Incumbent Technologies (Fossil Fuels) - **PARTIAL DATA**
- **Coal LCOE:** NO DATASET - uses fallback (~$65/MWh China, rising 1.5%/yr)
- **Gas LCOE:** NO DATASET - uses fallback (~$60/MWh USA, rising 1.2%/yr)
- **Coal Capacity:** `Coal_Installed_Capacity` (Global, cumulative) ✅
- **Gas Capacity:** `Natural_Gas_Installed_Capacity` (Global, cumulative) ✅
- **Coal Generation:** `Coal_Annual_Power_Generation` (Global) ✅
- **Gas Generation:** `Natural_Gas_Annual_Power_Generation` (Global) ✅
- **Coal CF:** Derived from capacity/generation ✅
- **Gas CF:** `Natural_Gas_Capacity_Factor` (Global) ✅

### System Metrics
- **Electricity Demand:** `Electricity_Annual_Production_{Region}`
- **Total Demand:** `Electricity_Annual_Domestic_Consumption_{Region}`

### Dataset Files Location
- `Coal.json` - Coal generation, capacity, CO2 (1975-2024)
- `Electricity.json` - Total production and consumption by region
- `Energy_Generation.json` - Capacity and generation by technology
- `Energy_Storage.json` - Battery storage costs and capacity
- `swb_taxonomy_and_datasets.json` - Complete taxonomy mapping

### Regional Coverage
All datasets available for: **China, USA, Europe, Rest_of_World, Global**

### Displacement Sequencing by Region
- **China:** Coal-first (air quality, climate commitments)
- **Europe:** Coal-first (carbon pricing, green policies)
- **USA:** Gas-first (cheap gas, flexible generation)
- **Rest_of_World:** Mixed, country-specific

### Critical Notes for Planning
1. **SWB Stack Cost = MAX(Solar_LCOE, Wind_LCOE) + SCOE** (conservative approach)
2. **Tipping Points:** Separate vs-coal and vs-gas detection
3. **Reserve Floors:** Min 10% coal, 15% gas of peak load retained
4. **New Capacity = Difference in cumulative capacity** for all generation types
5. **Capacity Factors improve annually:** Solar +0.2-0.3pp/yr, Wind +0.2-0.5pp/yr
6. **Fallback LCOE values are conservative** - tipping points remain valid

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
skill swb-transition --end-year 2030 --region China --sequence coal-first

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
- **High Renewable**: 80%+ renewable by 2035
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

- **Horizon**: 15-20 years (2024-2040)
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