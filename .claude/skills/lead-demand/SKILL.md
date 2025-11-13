---
name: lead-demand
description: >
  Forecasts refined lead demand (tonnes/year) using bottom-up installed-base accounting for battery applications.
  Use when analyzing lead demand, SLI batteries (automotive), industrial batteries (motive/stationary), or lead consumption trends.
  Handles regions: China, USA, Europe, Rest_of_World, Global.
  Models vehicle electrification impact on lead demand (EVs use smaller 12V batteries vs ICE).
  Tracks OEM demand (new sales) and replacement demand (battery lifecycle) separately.
  Accounts for all vehicle types (cars, 2W, 3W, CVs) and powertrains (ICE, BEV, PHEV, EV, NGV).
  Trigger keywords: lead demand, lead forecast, SLI batteries, battery lead, automotive batteries, industrial batteries. (project)
---

# Lead Demand Forecasting Skill

This skill implements bottom-up installed-base accounting for lead demand forecasting, focusing on battery applications (85% of total demand) across automotive and industrial segments.

## Overview

The skill forecasts lead demand across major segments:
- **SLI Batteries (Starting-Lighting-Ignition)**:
  - Passenger Cars (ICE, BEV, PHEV)
  - Two-Wheelers (ICE, EV)
  - Three-Wheelers (ICE, EV)
  - Commercial Vehicles (ICE, EV, NGV)
- **Industrial Batteries**:
  - Motive Power (forklifts, material handling)
  - Stationary Power (UPS, backup systems)
- **Other Uses** (15%): Non-battery applications

## Key Features

### Vehicle Electrification Impact
- **ICE vehicles**: Larger SLI batteries (15-25 kg for cars)
- **BEV/EV vehicles**: Smaller 12V auxiliary batteries (8-10 kg for cars)
- **PHEV vehicles**: Also carry 12V lead-acid batteries
- **NGV vehicles**: Similar to ICE for lead content
- Powertrain-specific coefficients for accurate modeling

### Installed-Base Accounting
- Track vehicle fleets by type and powertrain
- Separate OEM (new sales) and Replacement (battery lifecycle) demand
- Technology-specific battery lifetimes:
  - SLI: 3-5 years (typically 4.5 years)
  - Motive: 5-8 years (typically 7 years)
  - Stationary: 5-7 years (typically 6 years)

### Dual Calculation Approach
- **Primary**: Bottom-up from vehicle sales/fleet data
- **Validation**: Against aggregate demand datasets
- Reconciliation when bottom-up vs direct demand differ

## Usage

```bash
# Run the lead demand forecast
skill lead-demand

# With custom parameters
skill lead-demand --end-year 2040 --scenario baseline

# Generate validation report
skill lead-demand --validate --output-format csv
```

## Parameters

Key parameters configured in `config.json`:

### Lead Content Coefficients (kg/unit)
- **Passenger Cars**: ICE: 11.5, BEV: 9.0, PHEV: dataset-specific
- **Two-Wheelers**: ICE: 2.5, EV: 1.8
- **Three-Wheelers**: ICE: 7.0, EV: 5.0
- **Commercial Vehicles**: ICE: 22.0, EV: 18.0, NGV: 22.0

### Battery Lifetimes
- **SLI batteries**: 4.5 years
- **Motive batteries**: 7.0 years
- **Stationary batteries**: 6.0 years

### Asset Lifetimes (vehicles)
- **Passenger cars**: 15-20 years
- **Two-wheelers**: 10-12 years
- **Three-wheelers**: 8-10 years
- **Commercial vehicles**: 18-22 years

## Outputs

The skill generates:
1. Annual lead demand by segment (tonnes)
2. OEM vs Replacement breakdown
3. Vehicle fleet evolution by powertrain
4. Battery demand by vehicle type
5. Industrial battery demand (motive + stationary)
6. Other uses demand
7. Validation metrics

## Data Requirements

### Available Datasets
- **Vehicle Sales**: Annual sales by type and powertrain
  - `Passenger_Vehicle_(ICE/BEV/PHEV)_Annual_Sales_Global`
  - `Two_Wheeler_(ICE/EV)_Annual_Sales_Global`
  - `Three_Wheeler_(ICE/EV)_Annual_Sales_Global`
  - `Commercial_Vehicle_(ICE/EV/NGV)_Annual_Sales_Global`

- **Vehicle Fleet**: Total fleet/installed base
  - `Passenger_Vehicle_(ICE/BEV/PHEV)_Total_Fleet_Global`
  - `Two_Wheeler_(ICE/EV)_Total_Fleet_Global`
  - `Three_Wheeler_(ICE/EV)_Total_Fleet_Global`
  - `Commercial_Vehicle_(ICE/EV/NGV)_Total_Fleet_Global`

- **Lead Content**: PHEV-specific coefficient
  - `Passenger_Vehicle_(PHEV)_Average_lead_content_Global`

- **Industrial Demand** (aggregate fallback):
  - `Lead_Annual_Implied_Demand-Industrial_batteries_motive_power_Global`
  - `Lead_Annual_Implied_Demand-Industrial_batteries_stationary_Global`

## Validation

The skill validates:
- Bottom-up calculations against direct demand datasets
- Fleet mass balance (Sales - Scrappage = ΔFleet)
- Non-negativity constraints
- Lead content consistency across powertrains

## Scenarios

Pre-configured scenarios:
- **Baseline**: Moderate EV adoption, standard replacement cycles
- **Accelerated EV**: Faster electrification, reduced lead demand
- **Extended Lifecycles**: Longer battery life, reduced replacement
- **High Growth**: Increased vehicle sales, higher total demand

## Technical Details

- **Horizon**: 10-15 years (2024-2040), annual granularity
- **Primary Unit**: Tonnes of refined lead per year
- **Stock Unit**: Vehicle units, battery MWh
- **Methodology**: Bottom-up installed-base accounting
- **Confidence**: HIGH for SLI (data complete), MEDIUM for industrial

## Electrification Impact

The transition to EVs reduces lead demand per vehicle:
- BEV cars use ~22% less lead than ICE cars
- EV two-wheelers use ~28% less lead than ICE
- Overall impact depends on adoption rate and total fleet growth

## References

Based on:
- International Lead Association (ILA) methodologies
- Battery Council International (BCI) data
- Automotive industry fleet statistics
- Industrial battery market analysis