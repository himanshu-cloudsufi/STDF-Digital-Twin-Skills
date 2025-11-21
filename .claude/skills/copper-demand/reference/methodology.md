# Copper Demand Forecasting Methodology

## Overview

The copper demand forecast uses a hybrid two-tier approach:
- **TIER 1**: Bottom-up calculations from driver data (high confidence)
- **TIER 2**: Top-down allocation from segment shares (lower confidence)

## TIER 1: Bottom-Up Segments

### Automotive Segment (HIGH Confidence)

**Data Required:**
- Vehicle sales by powertrain type (ICE, BEV, PHEV, HEV)
- Fleet data for replacement demand calculation

**Calculation:**
```
Automotive Copper = Σ (Vehicle Sales × Copper Intensity)

Where copper intensity varies by type:
- ICE passenger car: 23 kg
- BEV passenger car: 83 kg (3.6× ICE)
- PHEV passenger car: 60 kg
- HEV passenger car: 35 kg
```

**EV Transition Modeling:**
- Use scenario-specific EV adoption targets (baseline: 75%, accelerated: 92%, delayed: 55%)
- Apply logistic curve interpolation between historical data and 2040 target
- Account for 3-4× copper intensity increase for BEVs vs ICE

### Grid Generation Segment (MEDIUM Confidence)

**Data Required:**
- Installed capacity by technology (wind, solar, coal, gas)
- Annual capacity additions

**Calculation:**
```
Grid Generation Copper = Σ (New Capacity MW × Copper Intensity t/MW)

Copper intensity by technology:
- Onshore wind: 6.0 t/MW
- Offshore wind: 10.0 t/MW
- Solar PV: 5.0 t/MW
- Gas CCGT: 1.0 t/MW
- Coal: 1.0 t/MW
```

**Renewable Buildout Modeling:**
- Use scenario-specific renewable capacity targets (baseline: 15 TW, accelerated: 20 TW)
- Apply growth factors to capacity addition rates
- Renewables are 5-10× more copper-intensive than fossil fuels

## TIER 2: Top-Down Segments

### Electrical Segment Allocation

Total Electrical Demand = Total Consumption × Electrical Share (typically 68%)

**Allocation within Electrical:**
- Construction: 48% of electrical
- Grid T&D: 35% of electrical
- Industrial: 17% of electrical

### Construction Segment (LOW Confidence - Allocated)

**Why Top-Down:**
- No comprehensive floorspace construction data by region
- Building codes and copper intensity vary significantly

**Calculation:**
```
Construction = Electrical Total × 0.48

OEM/Replacement Split:
- OEM (new construction): 65%
- Replacement (retrofit): 35%
```

### Grid T&D Segment (LOW Confidence - Residual)

**Why Residual:**
- Calculated as remainder after grid generation
- No detailed transmission/distribution expansion data

**Calculation:**
```
Grid T&D = (Electrical Total × 0.35) - Grid Generation OEM
```

### Industrial Segment (LOW Confidence - Allocated)

**Why Top-Down:**
- No motor sales or industrial equipment data
- Varies significantly by region and industrial composition

**Calculation:**
```
Industrial = Electrical Total × 0.17

OEM/Replacement Split:
- OEM: 60%
- Replacement: 40%
```

### Electronics Segment (LOW Confidence - Fixed Share)

**Calculation:**
```
Electronics = Total Consumption × 0.11

Assumed all OEM (consumer devices)
```

### Other Uses Segment (LOW Confidence - Bounded Residual)

**Includes:**
- Alloys (brass, bronze)
- Chemicals and compounds
- Miscellaneous applications

**Calculation:**
```
Other Uses = Total Consumption - Σ(All Other Segments)

Bounded between 8% and 18% of total
```

## Reconciliation Framework

**Purpose:** Ensure segment sum equals total consumption

**Process:**
1. Calculate TIER 1 segments (automotive, grid generation)
2. Allocate TIER 2 segments based on shares
3. Calculate total from all segments
4. If |calculated - target| > 0.1%:
   - Adjust TIER 2 segments proportionally
   - Never adjust TIER 1 (high confidence from real data)
5. Recalculate until reconciled

## Scenario Application

### Baseline Scenario
- EV adoption: 75% by 2035
- Renewable capacity: 15 TW by 2035
- Demand multiplier: 1.0×

### Accelerated Scenario
- EV adoption: 92% by 2035
- Renewable capacity: 20 TW by 2035
- Demand multiplier: 1.25×
- **Effect:** +25% higher total demand

### Delayed Scenario
- EV adoption: 55% by 2035
- Renewable capacity: 11 TW by 2035
- Demand multiplier: 0.85×
- **Effect:** -15% lower total demand

### Substitution Scenario
- EV adoption: 75% by 2035 (baseline)
- Renewable capacity: 15 TW by 2035 (baseline)
- Coefficient reduction: 15% for construction and grid T&D
- **Effect:** -7% total demand, vulnerable segments reduced

## Validation Rules

### Share Tolerances
- Transportation: ±2%
- Electrical: ±5%
- EV: ±3%
- Renewables: ±4%

### Growth Guards
- Maximum YoY growth: +50%
- Maximum YoY decline: -30%

### Smoothing
- Bottom-up segments: 3-year rolling window
- Allocated segments: 5-year rolling window

## Confidence Tagging

Each segment receives a confidence tag:

- **HIGH_BOTTOM_UP**: Automotive (full vehicle data)
- **MEDIUM_BOTTOM_UP**: Grid generation (capacity data available but incomplete)
- **LOW_ALLOCATED**: Construction, Industrial, Electronics (no driver data)
- **LOW_RESIDUAL**: Grid T&D, Other Uses (calculated as remainder)

## Data Sources

**Required for TIER 1:**
- Vehicle sales and fleet (OICA, IEA EV Outlook)
- Generation capacity (IEA, IRENA, BP Statistical Review)

**Required for Baseline:**
- Historical copper consumption (ICA, ICSG, USGS)
- Segment share percentages (industry benchmarks)

**For Validation:**
- Transportation demand percentage
- Electrical demand percentage
- EV demand percentage
- Solar/Wind demand percentages
