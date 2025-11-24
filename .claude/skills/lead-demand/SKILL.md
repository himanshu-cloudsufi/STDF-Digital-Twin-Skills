---
name: lead-demand
description: >
  Forecasts refined lead demand (tonnes/year) using bottom-up installed-base accounting for battery applications.
  Use when analyzing lead demand, SLI batteries (automotive), industrial batteries (motive/stationary), battery recycling,
  lead consumption trends, stock-flow accounting, installed base modeling, end-of-life vehicles, or scrappage analysis.
  Handles regions: China, USA, Europe, Rest_of_World, Global.
  Models vehicle electrification impact on lead demand (EVs use smaller 12V batteries vs ICE).
  Tracks OEM demand (new sales) and replacement demand (battery lifecycle) separately.
  Accounts for all vehicle types (cars, 2W, 3W, CVs) and powertrains (ICE, BEV, PHEV, EV, NGV). (project)
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

### Full Installed-Base Evolution
- **IB Tracking**: `IB(t+1) = IB(t) + Adds(t) - Scrappage(t)`
- **Scrappage Calculation**: `Scrappage(t) = IB(t) / Life_Asset`
- Separate tracking of asset lifetime vs battery lifetime
- Warm-up period using historical fleet data
- Stock-flow consistency validation

### OEM vs Replacement Demand Split
- **OEM Demand**: `SLI_OEM(t) = Σ Sales(t) × k_v,p (kg)`
  - Batteries for new vehicle sales
- **Replacement Demand**: `SLI_Repl(t) = Σ (IB(t) / Life_Battery) × k_v,p`
  - Contestable batteries from installed base
  - Accounts for 70-80% of SLI demand

### Advanced Analysis Features
- **Coefficient Calibration**: Auto-adjust lead coefficients based on validation variance
- **Back-casting Validation**: Historical forecast accuracy testing (MAPE, MAE, RMSE, R²)
- **Multi-Scenario Comparison**: Side-by-side scenario analysis with differential reporting
- **Sensitivity Analysis**: Parameter robustness testing with tornado diagrams

## Usage

### Basic Forecasting Workflow

```bash
# Run the lead demand forecast
cd .claude/skills/lead-demand
python3 scripts/forecast.py --region Global --scenario baseline

# With custom output path
python3 scripts/forecast.py --region China --scenario accelerated_ev --output output/china_forecast.csv
```

### Complete Analysis Workflow

Copy this checklist and track progress:

```
Analysis Progress:
- [ ] Step 1: Run baseline forecast
- [ ] Step 2: Generate QA report
- [ ] Step 3: Check validation variance (<50% acceptable)
- [ ] Step 4: Create visualizations
- [ ] Step 5: Generate evidence register (if needed)
```

**Step 1: Run baseline forecast**
```bash
python3 scripts/forecast.py --region Global --scenario baseline
```

**Step 2: Generate QA report**
```bash
python3 scripts/qa_report.py --results output/lead_demand_forecast_Global_baseline.csv \
                              --output output/qa_report.txt
```

**Step 3: Check validation variance**
Open the output CSV and review `*_variance_pct` columns. Target: <10% excellent, <30% acceptable, >50% needs calibration.

**Step 4: Create visualizations**
```bash
python3 scripts/visualization.py --results output/lead_demand_forecast_Global_baseline.csv \
                                  --output-dir output/plots
```

**Step 5: Generate evidence register** (optional)
```bash
python3 scripts/evidence_register.py --config config.json \
                                       --output output/evidence_register.csv
```

### Calibration Workflow (When Variance >50%)

Copy this checklist and track progress:

```
Calibration Progress:
- [ ] Step 1: Run baseline forecast
- [ ] Step 2: Check QA report (identify high variance segments)
- [ ] Step 3: Run coefficient calibration
- [ ] Step 4: Review config.json changes
- [ ] Step 5: Re-run forecast with calibrated parameters
- [ ] Step 6: Verify improved variance (<20%)
```

**Step 1: Run baseline forecast**
```bash
python3 scripts/forecast.py --region Global --scenario baseline
```

**Step 2: Check validation variance**
```bash
python3 scripts/qa_report.py --results output/lead_demand_forecast_Global_baseline.csv
```
If variance >50%, proceed to calibration.

**Step 3: Run coefficient calibration**
```bash
python3 scripts/calibrate_coefficients.py --results output/lead_demand_forecast_Global_baseline.csv \
                                           --threshold 10.0 \
                                           --adjustment-factor 0.5 \
                                           --report output/calibration_report.txt
```

**Step 4: Review config.json changes**
Check the backup file and review adjusted coefficients. Ensure values remain realistic.

**Step 5: Re-run forecast**
```bash
python3 scripts/forecast.py --region Global --scenario baseline
```

**Step 6: Verify improved variance**
Check QA report again. If variance still high, repeat calibration with adjusted threshold.

### Back-Testing Validation Workflow

```bash
# Run back-cast to validate against historical data
python3 scripts/backcast.py --region Global \
                             --scenario baseline \
                             --output-report output/backcast_report.txt \
                             --output-plot output/plots

# Review MAPE, MAE, RMSE, R² metrics in report
# Target: MAPE <15% indicates good forecast accuracy
```

### Scenario Comparison

```bash
# Compare multiple scenarios
python3 scripts/compare_scenarios.py --region Global \
                                      --scenarios baseline accelerated_ev extended_lifecycles \
                                      --output-report output/scenario_comparison.txt \
                                      --output-plots output/plots
```

### Sensitivity Analysis

```bash
# Test parameter robustness
python3 scripts/sensitivity_analysis.py --region Global \
                                        --scenario baseline \
                                        --output-report output/sensitivity_report.txt \
                                        --output-plots output/plots
```

## Parameters

Key parameters configured in `config.json`:

**Lead content coefficients**: ICE cars: 11.5 kg, BEV cars: 9.0 kg, 2W ICE: 2.5 kg, etc.
**Battery lifetimes**: SLI: 4.5 years, Motive: 7.0 years, Stationary: 6.0 years
**Asset lifetimes**: Cars: 18 years, 2W: 11 years, 3W: 9 years, CV: 20 years

**Complete reference**: See [reference/parameters-reference.md](reference/parameters-reference.md) for all parameters and modification guide.

## Outputs

The forecast generates CSV and JSON files with 60+ columns covering:
- Core demand metrics (total, battery, SLI, industrial, other uses)
- Vehicle type breakdowns (cars, 2W, 3W, CV)
- Powertrain-specific demand (ICE, BEV, PHEV, EV, NGV)
- Installed base tracking (millions of units)
- Validation variance columns

**Complete schema**: See [reference/output-schema-reference.md](reference/output-schema-reference.md) for full column descriptions.

## Validation

The skill validates:
1. **Direct Demand Comparison**: Bottom-up vs validation datasets (target variance <10%)
2. **Stock-Flow Consistency**: `IB(t+1) = IB(t) + Sales - Scrappage`
3. **Non-negativity**: All demand values ≥ 0
4. **Growth Rate Checks**: Flag YoY growth >20%
5. **Smoothing**: 3-year rolling median reduces volatility

**Complete validation guide**: See [reference/validation-reference.md](reference/validation-reference.md) for detailed framework and interpretation.

## Scenarios

Pre-configured scenarios:
- **Baseline**: Moderate EV adoption, standard replacement cycles
- **Accelerated EV**: Faster electrification, reduced lead demand
- **Extended Lifecycles**: Longer battery life, reduced replacement
- **High Growth**: Increased vehicle sales, higher total demand

**Scenario guide**: See [reference/scenarios-reference.md](reference/scenarios-reference.md) for detailed descriptions and custom scenario creation.

## Multi-Step Analysis Workflow

For complex analyses, reuse the container across multiple steps:

```bash
# Step 1: Run forecast
python3 scripts/forecast.py --region China --scenario baseline

# Step 2: In same container, generate QA report
python3 scripts/qa_report.py --results output/lead_demand_forecast_China_baseline.csv

# Step 3: In same container, create visualizations
python3 scripts/visualization.py --results output/lead_demand_forecast_China_baseline.csv \
                                  --output-dir output/plots

# Step 4: In same container, run sensitivity analysis
python3 scripts/sensitivity_analysis.py --region China --scenario baseline
```

This maintains all intermediate files and improves performance.

## Performance Notes

**Code execution environment**: 5GiB RAM, 5GiB storage

For large datasets (multi-region analyses):
- Process regions individually, then aggregate
- Use CSV format (more efficient than JSON for large tables)
- Filter output columns if only subset needed

## Common Analysis Patterns

**Example 1: Regional comparison**

Input: "Compare lead demand across China, India, and Europe for 2025-2035"

Approach:
1. Run forecast.py three times with different --region flags
2. Use compare_scenarios.py to generate comparative analysis
3. Highlight regional differences in growth rates and electrification impact

```bash
python3 scripts/forecast.py --region China --scenario baseline
python3 scripts/forecast.py --region India --scenario baseline
python3 scripts/forecast.py --region Europe --scenario baseline
# Then manually compare outputs or use compare_scenarios.py
```

**Example 2: EV impact assessment**

Input: "What's the impact of 50% EV adoption on lead demand in China?"

Approach:
1. Run baseline scenario (current EV adoption trajectory)
2. Create custom scenario with 50% EV share by 2035 in config.json
3. Run both scenarios
4. Use compare_scenarios.py to show differential impact

```bash
# Baseline
python3 scripts/forecast.py --region China --scenario baseline

# Custom high EV scenario (after editing config.json)
python3 scripts/forecast.py --region China --scenario high_ev_50pct

# Compare
python3 scripts/compare_scenarios.py --region China --scenarios baseline high_ev_50pct
```

**Example 3: Parameter sensitivity ranking**

Input: "Which parameters have the biggest impact on the China forecast?"

Approach:
1. Run sensitivity analysis (tests ±20% on all key parameters)
2. Review tornado diagram showing ranked impact
3. Focus calibration efforts on high-impact parameters

```bash
python3 scripts/sensitivity_analysis.py --region China --scenario baseline \
                                        --output-report output/sensitivity_report.txt \
                                        --output-plots output/plots
# Review tornado diagram in output/plots/sensitivity_tornado.png
```

## Technical Details

- **Historical Data**: 1998-2024 (varies by metric)
- **Forecast Horizon**: Configurable (typically through 2030 (extended: 2035))
- **Temporal Granularity**: Annual
- **Primary Unit**: Tonnes of refined lead per year (kt)
- **Stock Unit**: Vehicle units (millions), battery MWh
- **Methodology**: Bottom-up installed-base accounting with trend projections
- **Confidence**: HIGH for SLI (data complete), MEDIUM for industrial

## Taxonomy and Dataset Mapping

### Commodity Definition
- **Commodity:** `Lead` (refined lead metal)
- **Primary Unit:** Tonnes (kt) per year

### Lead Demand Categories

**Total Lead Demand**
- Total Demand: `Annual_Implied_Demand` (Global)
- Industrial Motive: `Annual_Implied_Demand-Industrial_batteries_motive_power` (Global)
- Industrial Stationary: `Annual_Implied_Demand-Industrial_batteries_stationary` (Global)
- Non-Battery Uses: `Annual_Implied_Demand-Non-battery_uses` (Global)
- Cost: `Cost` (Global)

### Vehicle Markets and Lead Demand

**Passenger Cars**
- Entity Type: `market`
- Vehicle Types: ICE, BEV, PHEV
- ICE Sales: `Passenger_Vehicle_(ICE)_Annual_Sales` (by region)
- BEV Sales: `Passenger_Vehicle_(BEV)_Annual_Sales` (Global)
- PHEV Sales: `Passenger_Vehicle_(PHEV)_Annual_Sales` (Global)
- ICE Fleet: `Passenger_Vehicle_(ICE)_Total_Fleet` (Global)
- BEV Fleet: `Passenger_Vehicle_(BEV)_Total_Fleet` (Global)
- Lead Demand: `Lead_Annual_Implied_Demand-Sales_Cars` (Global)

**Two-Wheelers**
- Entity Type: `market`
- Vehicle Types: ICE, EV
- Total Sales: `Annual_Sales` (by region)
- ICE Sales: `(ICE)_Annual_Sales` (by region)
- EV Sales: `(EV)_Annual_Sales` (by region)
- ICE Fleet: `(ICE)_Total_Fleet` (by region)
- EV Fleet: `(EV)_Total_Fleet` (by region, except China)
- ICE Cost: `(ICE)_Median_Cost` (by region)
- EV Cost: `(EV)_Median_Cost` (by region)
- Lead Demand (Sales): `Lead_Annual_Implied_Demand-Sales_2_wheelers` (Global)
- Lead Demand (Replacement): `Lead_Annual_Implied_Demand-Vehicle_replacement_2_wheelers` (Global)

**Three-Wheelers**
- Entity Type: `market`
- Vehicle Types: ICE, EV
- Total Sales: `Annual_Sales` (by region, no USA)
- ICE Sales: `(ICE)_Annual_Sales` (by region)
- EV Sales: `(EV)_Annual_Sales` (by region)
- ICE Fleet: `(ICE)_Total_Fleet` (by region)
- EV Fleet: `(EV)_Total_Fleet` (by region)
- ICE Cost: `(ICE)_Median_Cost` (by region)
- EV Cost: `(EV)_Median_Cost` (by region)
- Lead Demand (Sales): `Lead_Annual_Implied_Demand-Sales_3_wheelers` (Global)
- Lead Demand (Replacement): `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers` (Global)

**Commercial Vehicles**
- Entity Type: `market`
- Vehicle Types: ICE, EV, NGV
- Sub-Categories: Light_Duty, Medium_Duty, Heavy_Duty
- Total Sales: `Annual_Sales` (by region)
- ICE Sales: `(ICE)_Annual_Sales` (by region)
- EV Sales: `(EV)_Annual_Sales` (by region)
- NGV Sales: `(NGV)_Annual_Sales` (by region)
- ICE Fleet: `(ICE)_Total_Fleet` (by region)
- EV Fleet: `(EV)_Total_Fleet` (by region)
- NGV Fleet: `(NGV)_Total_Fleet` (by region)
- ICE Cost: `(ICE)_Median_Cost` (Global)
- EV Cost: `(EV)_Median_Cost` (Global)
- Lead Demand (Sales): `Lead_Annual_Implied_Demand-Sales_Commercial_vehicles` (Global)
- Lead Demand (Buses): `Lead_Annual_Implied_Demand-Sales_Buses` (Global)
- Lead Demand (Replacement): `Lead_Annual_Implied_Demand-Vehicle_replacement_Commercial` (Global)

### Available Regions
- **Passenger Cars:** China, USA, Europe, Rest_of_World, Global
- **Two-Wheelers:** China, USA, Europe, Rest_of_World, Global
- **Three-Wheelers:** China, Europe, Rest_of_World, Global (no USA)
- **Commercial Vehicles:** China, USA, Europe, Rest_of_World, Global
- **Lead Demand:** Global only

### Available Dataset Files
- `Lead.json` - Lead cost and demand by category
- `Passenger_Cars.json` - Passenger vehicle sales and fleet data
- `Two_Wheeler.json` - Two-wheeler sales, fleet, and cost data
- `Three_Wheeler.json` - Three-wheeler sales, fleet, and cost data
- `Commercial_Vehicle.json` - Commercial vehicle sales, fleet, and cost data
- `lead_taxonomy_and_datasets.json` - Taxonomy mapping (this section)

### Lead Demand Sources
- **SLI Batteries:** Starting, Lighting, Ignition for ICE vehicles
- **Industrial Motive:** Forklift, material handling (being displaced by Li-ion)
- **Industrial Stationary:** Backup power, UPS (being displaced by Li-ion)
- **Non-Battery Uses:** Construction, ammunition, etc.

## Reference Documentation

- [reference/parameters-reference.md](reference/parameters-reference.md) - Complete parameter catalog
- [reference/output-schema-reference.md](reference/output-schema-reference.md) - 60+ column schema
- [reference/validation-reference.md](reference/validation-reference.md) - Validation framework
- [reference/scenarios-reference.md](reference/scenarios-reference.md) - Scenario guide

## Data Sources

Based on:
- International Lead Association (ILA) methodologies
- Battery Council International (BCI) data
- Automotive industry fleet statistics
- Industrial battery market analysis
