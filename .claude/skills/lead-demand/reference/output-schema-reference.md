# Output Schema Reference

## Contents
- Output Formats
- Core Demand Columns
- SLI Breakdown by Vehicle Type
- Detailed Powertrain Breakdown
- Installed Base Tracking
- Sales/Adds Data
- Parameter Columns
- Validation Columns
- Metadata Columns

---

## Output Formats

The forecast generates outputs in two formats:

- **CSV**: Standard tabular format (default) - Best for Excel and data analysis
- **JSON**: Structured data with indentation - Best for programmatic access

---

## Core Demand Columns (9 columns)

Primary demand metrics in kilotonnes (kt) per year:

- `total_lead_demand_kt`: Total refined lead demand (all applications)
- `battery_demand_kt`: All battery applications combined
- `sli_demand_kt`: Total SLI (Starting-Lighting-Ignition) battery demand
- `sli_oem_kt`: SLI OEM demand (batteries for new vehicles)
- `sli_replacement_kt`: SLI replacement demand (contestable market)
- `industrial_demand_kt`: Industrial batteries total (motive + stationary)
- `industrial_motive_kt`: Motive power batteries (forklifts, material handling)
- `industrial_stationary_kt`: Stationary batteries (UPS, backup power)
- `other_uses_kt`: Non-battery lead uses (15% of total)

---

## SLI Breakdown by Vehicle Type (8 columns)

OEM and replacement demand split by vehicle type (kt):

### Passenger Cars
- `sli_oem_passenger_cars_kt`: New car battery demand
- `sli_replacement_passenger_cars_kt`: Replacement battery demand

### Two-Wheelers
- `sli_oem_two_wheelers_kt`: New 2W battery demand
- `sli_replacement_two_wheelers_kt`: Replacement battery demand

### Three-Wheelers
- `sli_oem_three_wheelers_kt`: New 3W battery demand
- `sli_replacement_three_wheelers_kt`: Replacement battery demand

### Commercial Vehicles
- `sli_oem_commercial_vehicles_kt`: New CV battery demand
- `sli_replacement_commercial_vehicles_kt`: Replacement battery demand

---

## Detailed Powertrain Breakdown (24+ columns)

Granular demand breakdown by vehicle type and powertrain (kt):

### Passenger Cars
**OEM Demand:**
- `cars_ICE_oem_kt`: ICE cars OEM demand
- `cars_BEV_oem_kt`: BEV cars OEM demand
- `cars_PHEV_oem_kt`: PHEV cars OEM demand
- `cars_HEV_oem_kt`: HEV cars OEM demand (if applicable)

**Replacement Demand:**
- `cars_ICE_replacement_kt`: ICE cars replacement demand
- `cars_BEV_replacement_kt`: BEV cars replacement demand
- `cars_PHEV_replacement_kt`: PHEV cars replacement demand
- `cars_HEV_replacement_kt`: HEV cars replacement demand (if applicable)

### Two-Wheelers
**OEM & Replacement:**
- `2w_ICE_oem_kt`, `2w_ICE_replacement_kt`
- `2w_EV_oem_kt`, `2w_EV_replacement_kt`

### Three-Wheelers
**OEM & Replacement:**
- `3w_ICE_oem_kt`, `3w_ICE_replacement_kt`
- `3w_EV_oem_kt`, `3w_EV_replacement_kt`

### Commercial Vehicles
**OEM & Replacement:**
- `cv_ICE_oem_kt`, `cv_ICE_replacement_kt`
- `cv_EV_oem_kt`, `cv_EV_replacement_kt`
- `cv_NGV_oem_kt`, `cv_NGV_replacement_kt`

---

## Installed Base Tracking (millions of units)

Tracks the total number of vehicles in operation:

### Passenger Cars
- `ib_cars_ICE_million_units`: ICE cars in operation
- `ib_cars_BEV_million_units`: BEV cars in operation
- `ib_cars_PHEV_million_units`: PHEV cars in operation

### Two-Wheelers
- `ib_2w_ICE_million_units`: ICE 2W in operation
- `ib_2w_EV_million_units`: EV 2W in operation

### Three-Wheelers
- `ib_3w_ICE_million_units`: ICE 3W in operation
- `ib_3w_EV_million_units`: EV 3W in operation

### Commercial Vehicles
- `ib_cv_ICE_million_units`: ICE CV in operation
- `ib_cv_EV_million_units`: EV CV in operation
- `ib_cv_NGV_million_units`: NGV CV in operation

---

## Sales/Adds Data (millions of units)

Annual vehicle sales by type and powertrain:

- `sales_cars_ice_million_units`, `sales_cars_bev_million_units`, `sales_cars_phev_million_units`
- `sales_2w_ice_million_units`, `sales_2w_ev_million_units`
- `sales_3w_ice_million_units`, `sales_3w_ev_million_units`
- `sales_cv_ice_million_units`, `sales_cv_ev_million_units`, `sales_cv_ngv_million_units`

---

## Parameter Columns

Records the parameters used in the forecast:

### Lead Coefficients (kg/unit)
- `coeff_cars_ice_kg`, `coeff_cars_bev_kg`, `coeff_cars_phev_kg`
- `coeff_2w_ice_kg`, `coeff_2w_ev_kg`
- `coeff_3w_ice_kg`, `coeff_3w_ev_kg`
- `coeff_cv_ice_kg`, `coeff_cv_ev_kg`, `coeff_cv_ngv_kg`

### Battery Lifetimes
- `life_battery_sli_years`: SLI battery replacement cycle
- `life_battery_motive_years`: Motive power battery cycle
- `life_battery_stationary_years`: Stationary battery cycle

### Asset Lifetimes
- `life_asset_car_years`: Passenger car scrappage
- `life_asset_2w_years`: Two-wheeler scrappage
- `life_asset_3w_years`: Three-wheeler scrappage
- `life_asset_cv_years`: Commercial vehicle scrappage

---

## Validation Columns

Tracks variance between bottom-up calculations and validation datasets:

### OEM Variance
- `cars_oem_variance_pct`: Passenger car OEM variance vs direct demand
- `2w_oem_variance_pct`: Two-wheeler OEM variance
- `3w_oem_variance_pct`: Three-wheeler OEM variance

### Replacement Variance
- `cars_replacement_variance_pct`: Passenger car replacement variance
- `2w_replacement_variance_pct`: Two-wheeler replacement variance
- `3w_replacement_variance_pct`: Three-wheeler replacement variance

**Note**: Commercial vehicles typically lack validation datasets, so no CV variance columns.

**Interpretation**:
- Variance <10%: Excellent alignment
- Variance 10-30%: Acceptable range
- Variance >50%: Investigate methodology or data quality

---

## Metadata Columns

Contextual information about each forecast row:

- `year`: Forecast year (integer)
- `region`: Geographic region (China, USA, Europe, Rest_of_World, Global)
- `scenario`: Scenario name (baseline, accelerated_ev, extended_lifecycles, high_growth)
- `battery_share_pct`: Battery uses as % of total lead demand
- `sli_share_pct`: SLI demand as % of total lead demand

---

## Example Output Row

```csv
year,region,scenario,total_lead_demand_kt,battery_demand_kt,sli_demand_kt,...
2025,China,baseline,2450.5,2082.9,1850.2,...
```

---

## Understanding the Data Flow

1. **Vehicle Sales** → **OEM Demand** (`sli_oem_*`)
2. **Installed Base** → **Replacement Demand** (`sli_replacement_*`)
3. **OEM + Replacement** → **Total SLI** (`sli_demand_kt`)
4. **SLI + Industrial** → **Battery Demand** (`battery_demand_kt`)
5. **Battery + Other Uses** → **Total Demand** (`total_lead_demand_kt`)
