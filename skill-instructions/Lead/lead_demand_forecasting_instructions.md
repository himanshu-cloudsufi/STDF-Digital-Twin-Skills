# instructions.md — Lead Demand Forecasting (Bottom-Up, Installed-Base Framework)

> This guide standardizes how to forecast refined **lead demand (tonnes/year)** from battery and non-battery uses using **installed-base accounting** + **new-build vs replacement** flows for every relevant asset class (SLI, industrial motive, industrial stationary), and an econometric module for "other uses." It mirrors the Datacenter UPS approach and borrows guardrails (e.g., smoothing, numerical checks) from the SWB instructions.

---

## 1) Scope & Objectives

- **Horizon:** 10–15 years (e.g., 2024–2040), **annual** step  
- **Granularity:** Global aggregate built from independently-modeled sub-segments  
- **Primary flow unit:** tonnes of refined lead consumed per year  
- **Primary stock unit:** Installed Base (**IB**) of lead-using equipment (e.g., vehicle parc in **units**; UPS in **MWh**)  
- **Core principle:** Every battery segment = **New-Build demand** + **Replacement demand** (via IB & battery lifetimes)

---

## 2) Forecast Identity (Top Level)

**Total_Lead_Demand(t) = Demand_Battery(t) + Demand_Other_Uses(t)**

- Battery typically ≈ 85% of total; Other Uses ≈ 15% (calibrate to history)

### 2.1 Battery Decomposition

**Demand_Battery(t) = Demand_SLI(t) + Demand_Industrial(t)**

- **SLI**(t) = **SLI_OEM**(t) + **SLI_Replacement**(t)  
- **Industrial**(t) = **Motive**(t) + **Stationary**(t) (each = new-build + replacement)

### 2.2 SLI Segment Decomposition

**SLI_OEM(t) = SLI_OEM_Cars(t) + SLI_OEM_2W(t) + SLI_OEM_3W(t) + SLI_OEM_CV(t)**

**SLI_Replacement(t) = SLI_Repl_Cars(t) + SLI_Repl_2W(t) + SLI_Repl_3W(t) + SLI_Repl_CV(t)**

Each vehicle segment includes multiple powertrain types:
- **Cars**: ICE, BEV, PHEV
- **Two-Wheelers (2W)**: ICE, EV
- **Three-Wheelers (3W)**: ICE, EV
- **Commercial Vehicles (CV)**: ICE, EV, **NGV** (Natural Gas Vehicles)

**Note on EVs and Lead Content:**
- BEV/EV vehicles use smaller 12V auxiliary lead-acid batteries compared to ICE (typically 8-10 kg vs 15-25 kg for ICE passenger cars)
- PHEV vehicles also carry 12V lead-acid batteries
- NGV (Natural Gas) commercial vehicles use lead-acid SLI batteries similar to ICE CVs
- Use powertrain-specific coefficients (k_v_ICE, k_v_EV, k_v_NGV) or apply scaling factors

### 2.3 Segment-Level Identity

**Demand_Segment(t) = New_Build_Demand(t) + Replacement_Demand(t)**

---

## 3) Installed-Base (IB) Accounting & Lifetimes

For each asset class A ∈ {Passenger Cars, 2W, 3W, CVs, Forklifts, UPS, …}:

**IB_A(t+1) = IB_A(t) + Adds_A(t) − Scrappage_A(t)**

- **Adds** = new sales/installs in year t (units or MWh)  
- **Scrappage** ≈ IB_A(t) / Life_Asset_A (or use a lifetime distribution if available)

**Contestable batteries** (needing replacement):

**Contestable_A(t) ≈ IB_A(t) / Life_Battery_A**

Then convert contestable counts/energy to **tonnes** via coefficients (kg/unit or kg/MWh).

**Typical lifetimes** (tune per source):  
- SLI battery: **3–5** yrs; Motive: **5–8** yrs; Stationary (VRLA): **5–7** yrs  
- Assets: Car **15–20** yrs; 2W **10–12** yrs; CV **18–22** yrs; Forklift **12–16** yrs; UPS rack lifespan **8–12** yrs

---

## 4) New-Build Modules

### 4.1 SLI OEM (vehicles)

Inputs (per year):  
- **New vehicle sales** by type and powertrain:
  - **Passenger Cars**: ICE, BEV, PHEV
  - **Two-Wheelers**: ICE, EV
  - **Three-Wheelers**: ICE, EV
  - **Commercial Vehicles**: ICE, EV, **NGV**
  
- **Lead coefficients** (kg/unit): k_car_ICE, k_car_BEV, k_car_PHEV, k_2W_ICE, k_2W_EV, k_3W_ICE, k_3W_EV, k_CV_ICE, k_CV_EV, k_CV_NGV

**Available Data Sources:**
- Vehicle sales datasets: `Passenger_Vehicle_(ICE)_Annual_Sales_Global`, `Two_Wheeler_(EV)_Annual_Sales_Global`, etc.
- PHEV lead coefficient: `Passenger_Vehicle_(PHEV)_Average_lead_content_Global`

**SLI_OEM(t) = Σ_v Σ_p Sales_v,p(t) × k_v,p (kg) → tonnes**

Where:
- v = vehicle type (Car, 2W, 3W, CV)
- p = powertrain type (ICE, EV, BEV, PHEV, NGV)

**Example for Passenger Cars:**
```
SLI_OEM_Cars(t) = Sales_Car_ICE(t) × k_car_ICE 
                + Sales_Car_BEV(t) × k_car_BEV
                + Sales_Car_PHEV(t) × k_car_PHEV
```

**NGV Handling:**
NGV commercial vehicles use lead-acid SLI batteries; apply the same coefficient as ICE CVs (k_CV_NGV = k_CV_ICE) unless specific data indicates otherwise.

### 4.2 Industrial New-Build

**IF DATA AVAILABLE:**
- **Motive (forklifts):** Motive_New(t) = Sales_ElectricForklift(t) × k_forklift  
- **Stationary (UPS):** Stationary_New(t) = New_UPS_Installed_MWh(t) × k_UPS(kg/MWh)

**FALLBACK (if detailed data unavailable):**
Use aggregate demand datasets directly:
- `Lead_Annual_Implied_Demand-Industrial_batteries_motive_power_Global`
- `Lead_Annual_Implied_Demand-Industrial_batteries_stationary_Global`

---

## 5) Replacement Modules

### 5.1 SLI Replacement

From IB (vehicle parc) & SLI life:

**SLI_Repl(t) = Σ_v Σ_p (IB_v,p(t) / Life_Battery_SLI) × k_v,p → tonnes**

Where:
- v = vehicle type (Car, 2W, 3W, CV)
- p = powertrain type (ICE, EV, BEV, PHEV, NGV)

**Available Data Sources:**
- Fleet datasets: `Passenger_Vehicle_(ICE)_Total_Fleet_Global`, `Two_Wheeler_(EV)_Total_Fleet_Global`, `Commercial_Vehicle_(NGV)_Total_Fleet_Global`, etc.

**Example for Commercial Vehicles:**
```
SLI_Repl_CV(t) = (IB_CV_ICE(t) / Life_Battery_SLI) × k_CV_ICE
               + (IB_CV_EV(t) / Life_Battery_SLI) × k_CV_EV
               + (IB_CV_NGV(t) / Life_Battery_SLI) × k_CV_NGV
```

### 5.2 Industrial Replacement

**IF DATA AVAILABLE:**
- **Motive:** Motive_Repl(t) = (IB_forklift(t) / Life_Battery_Motive) × k_forklift  
- **Stationary:** Stationary_Repl(t) = (IB_UPS(t) / Life_Battery_Stationary) × k_UPS(kg/MWh)

**FALLBACK:**
Use aggregate industrial demand datasets (which include both new-build and replacement).

---

## 6) "Other Uses" (≈15%) — Multiple Approaches by Data Availability

Model this as industrial consumables (pigments, alloys, shielding, ammunition).

### Option A: Direct Dataset (RECOMMENDED)
**IF AVAILABLE:** Use `Lead_Annual_Implied_Demand-Non-battery_uses_Global` directly

### Option B: Econometric Model (if macro drivers available)
**Drivers:** Global IPI, Global GDP, LME Lead price (for substitution/thrifting)  
**Spec (elasticities to calibrate):**  
```
ln(OtherUses_t) = β0 + β1 ln(IPI_t) + β2 ln(GDP_t) + β3 ln(Price_t) + ε_t
```

### Option C: Simplified Price-Trend Model (fallback)
**IF only price data available:**
```
OtherUses_t = OtherUses_base × (1 + trend_rate)^(t - t_base) × (Price_t / Price_base)^β_price
```

**Recommendation:**
1. Try **Option A** first (direct dataset)
2. Use **Option B** for sensitivity scenarios (if macro data becomes available)
3. Fall back to **Option C** if only `Lead_Cost_Global` is available

---

## 7) Data Mapping & Fallbacks

### 7.1 Inputs to supply or connect

**Vehicle Sales (by type and powertrain):**
- Cars: `Passenger_Vehicle_(ICE)_Annual_Sales_Global`, `Passenger_Vehicle_(BEV)_Annual_Sales_Global`, `Passenger_Vehicle_(PHEV)_Annual_Sales_Global`
- 2W: `Two_Wheeler_(ICE)_Annual_Sales_Global`, `Two_Wheeler_(EV)_Annual_Sales_Global`
- 3W: `Three_Wheeler_(ICE)_Annual_Sales_Global`, `Three_Wheeler_(EV)_Annual_Sales_Global`
- CV: `Commercial_Vehicle_(ICE)_Annual_Sales_Global`, `Commercial_Vehicle_(EV)_Annual_Sales_Global`, `Commercial_Vehicle_(NGV)_Annual_Sales_Global`

**Fleet/Installed Base (by type and powertrain):**
- Cars: `Passenger_Vehicle_(ICE)_Total_Fleet_Global`, `Passenger_Vehicle_(BEV)_Total_Fleet_Global`, `Passenger_Vehicle_(PHEV)_Total_Fleet_Global`
- 2W: `Two_Wheeler_(ICE)_Total_Fleet_Global`, `Two_Wheeler_(EV)_Total_Fleet_Global`
- 3W: `Three_Wheeler_(ICE)_Total_Fleet_Global`, `Three_Wheeler_(EV)_Total_Fleet_Global`
- CV: `Commercial_Vehicle_(ICE)_Total_Fleet_Global`, `Commercial_Vehicle_(EV)_Total_Fleet_Global`, `Commercial_Vehicle_(NGV)_Total_Fleet_Global`

**Direct Lead Demand (for validation):**
- `Lead_Annual_Implied_Demand-Sales_Cars_Global`
- `Lead_Annual_Implied_Demand-Vehicle_replacement_Cars_Global`
- `Lead_Annual_Implied_Demand-Sales_2_wheelers_Global`
- `Lead_Annual_Implied_Demand-Vehicle_replacement_2_wheelers_Global`
- `Lead_Annual_Implied_Demand-Sales_3_wheelers_Global`
- `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers_Global`

**Industrial & Other:**
- `Lead_Annual_Implied_Demand-Industrial_batteries_motive_power_Global`
- `Lead_Annual_Implied_Demand-Industrial_batteries_stationary_Global`
- `Lead_Annual_Implied_Demand-Non-battery_uses_Global`
- `Lead_Cost_Global`

**Macro drivers (if available):** IPI, GDP time series

### 7.2 Parameters to source (with ranges/defaults)

**Lead coefficients (kg/unit):**
- **Passenger Cars:**
  - ICE: 11.5–15 kg (use 11.5 as default)
  - BEV: 8–10 kg (or 0.6 × ICE)
  - PHEV: Use `Passenger_Vehicle_(PHEV)_Average_lead_content_Global` dataset

- **Two-Wheelers:**
  - ICE: 2.5–4 kg (use 2.5 as default)
  - EV: 1.5–2.5 kg (or 0.7 × ICE)

- **Three-Wheelers:**
  - ICE: 7–10 kg (use 7.0 as default)
  - EV: 4–6 kg (or 0.7 × ICE)

- **Commercial Vehicles:**
  - ICE: 22–35 kg (use 22.0 as default)
  - EV: 15–20 kg (for 12V auxiliary)
  - NGV: Same as ICE (22.0 kg)

- **Industrial (if bottom-up):**
  - Forklift: 750–1000 kg (placeholder)
  - UPS: 300 kg/kWh or 300,000 kg/MWh (placeholder)

**Lifespans (years):**
- Battery lifetimes: SLI (4.5), Motive (7.0), Stationary VRLA (6.0)
- Asset lifetimes: Car (18), 2W (12), 3W (12), CV (20), Forklift (15), UPS rack (10)

**Initial IB values:**
- Use fleet datasets (Total_Fleet_Global) for starting stocks

### 7.3 Calculation Strategy: Bottom-Up vs Direct Demand

**Primary Method (Bottom-Up):**
- Calculate SLI demand from vehicle sales/fleet + lead coefficients
- Formula: `Demand = Sales × k_v (OEM) + (IB / Life) × k_v (Replacement)`
- Use for: All vehicle segments (Cars, 2W, 3W, CV)
- **Advantages:** Transparent, allows scenario testing, coefficient calibration

**Validation (Direct Demand):**
- Compare with pre-calculated demand datasets:
  - `Lead_Annual_Implied_Demand-Sales_Cars_Global`
  - `Lead_Annual_Implied_Demand-Vehicle_replacement_Cars_Global`
  - (same pattern for 2W, 3W)
- Use for: QA checks, coefficient calibration (§12.2), back-casting validation
- **Note:** No direct demand datasets available for CVs; must use bottom-up

**Fallback Priority:**
1. **Bottom-up** from sales/fleet (if coefficients available or can be calibrated)
2. **Direct demand** datasets (if sales/fleet data missing or unreliable)
3. **Aggregate** industrial datasets (if segment-level data unavailable)

**Implementation Note:**
For segments with both bottom-up inputs AND direct demand datasets (Cars, 2W, 3W):
- Use bottom-up as primary calculation
- Compare with direct demand datasets
- If difference > 10%, investigate and recalibrate coefficients
- Document assumptions in evidence register

### 7.4 Fallback Rules

- **Missing initial IB:** Warm up IB using historical sales for ≥ one asset lifetime.  
- **Missing coefficients:** Use ILZSG/BCI global averages; mark as **assumption** and add to evidence register.  
- **Missing sales data:** Use direct demand datasets if available; otherwise interpolate or use growth rates from similar regions.
- **Missing industrial detail:** Accept aggregate industrial demand datasets rather than attempting bottom-up without data.
- Apply **rolling-median smoothing / guards** for numerical stability and non-negativity.

---

## 8) Aggregation & Validation

**Aggregate (tonnes):**

```
Total_Lead_Demand(t) = 
    // SLI OEM by vehicle type
    SLI_OEM_Cars(t) + SLI_OEM_2W(t) + SLI_OEM_3W(t) + SLI_OEM_CV(t) +
    
    // SLI Replacement by vehicle type  
    SLI_Repl_Cars(t) + SLI_Repl_2W(t) + SLI_Repl_3W(t) + SLI_Repl_CV(t) +
    
    // Industrial
    Motive_New(t) + Motive_Repl(t) +
    Stationary_New(t) + Stationary_Repl(t) +
    
    // Other Uses
    OtherUses(t)
```

**Validation checklist:**
- **Historical fit:** Sum should closely track ILZSG Total Refined Lead Consumption (level & structure).  
- **Cross-check:** A simple top-down model f(GDP, IPI) should be directionally consistent.  
- **Shares sanity:** 
  - Battery share ~ 85% (historical baseline)
  - SLI replacement should dominate battery demand in steady state
  - SLI OEM + Replacement should be 60-70% of total demand
  - Industrial (Motive + Stationary) should be 15-25%
  - Other Uses should be 10-20%
- **Vehicle segment shares:** Cars > CVs > 2W > 3W (in tonnes, not units)
- **Numerical guards:** Clamp non-negatives; smooth spikes with **3-yr rolling median**; ensure flow/stock consistency.
- **Coefficient validation:** Back-calculate implied coefficients from direct demand datasets where available; compare with literature ranges.
- **EV impact:** Verify that increasing EV adoption appropriately reduces total lead demand over time.

---

## 9) Output Schema (wide table, per year)

### 9.1 Summary Columns
- `year`  
- `total_demand_tonnes`  
- `total_battery_demand_tonnes`
- `total_other_uses_tonnes`

### 9.2 SLI Demand Breakdown

**By vehicle type:**
- `sli_oem_demand_total`
  - `sli_oem_cars`
  - `sli_oem_2w`
  - `sli_oem_3w`
  - `sli_oem_cv`

- `sli_replacement_demand_total`
  - `sli_repl_cars`
  - `sli_repl_2w`
  - `sli_repl_3w`
  - `sli_repl_cv`

**By powertrain (optional granular breakdown):**
- `sli_oem_cars_ice`, `sli_oem_cars_bev`, `sli_oem_cars_phev`
- `sli_oem_2w_ice`, `sli_oem_2w_ev`
- `sli_oem_3w_ice`, `sli_oem_3w_ev`
- `sli_oem_cv_ice`, `sli_oem_cv_ev`, `sli_oem_cv_ngv`
- (Same pattern for replacement)

### 9.3 Industrial Demand
- `industrial_motive_new_demand`, `industrial_motive_repl_demand`, `industrial_motive_total_demand`
- `industrial_stationary_new_demand`, `industrial_stationary_repl_demand`, `industrial_stationary_total_demand`

### 9.4 Reference Columns (for auditability)

**Installed Base:**
- `ib_cars_ice_units`, `ib_cars_bev_units`, `ib_cars_phev_units`
- `ib_2w_ice_units`, `ib_2w_ev_units`
- `ib_3w_ice_units`, `ib_3w_ev_units`
- `ib_cv_ice_units`, `ib_cv_ev_units`, `ib_cv_ngv_units`
- `ib_forklifts_units` (if available)
- `ib_ups_mwh` (if available)

**Sales/Adds:**
- `sales_cars_ice`, `sales_cars_bev`, `sales_cars_phev`
- `sales_2w_ice`, `sales_2w_ev`
- `sales_3w_ice`, `sales_3w_ev`
- `sales_cv_ice`, `sales_cv_ev`, `sales_cv_ngv`
- `new_ups_installed_mwh` (if available)

**Parameters Used:**
- `coeff_car_ice_kg`, `coeff_car_bev_kg`, `coeff_car_phev_kg`
- `coeff_2w_ice_kg`, `coeff_2w_ev_kg`
- `coeff_3w_ice_kg`, `coeff_3w_ev_kg`
- `coeff_cv_ice_kg`, `coeff_cv_ev_kg`, `coeff_cv_ngv_kg`
- `life_batt_sli_years`, `life_batt_motive_years`, `life_batt_stationary_years`
- `life_asset_car_years`, `life_asset_2w_years`, `life_asset_3w_years`, `life_asset_cv_years`

**Validation Columns:**
- `validation_cars_oem_direct_demand` (from `Lead_Annual_Implied_Demand-Sales_Cars_Global`)
- `validation_cars_repl_direct_demand` (from `Lead_Annual_Implied_Demand-Vehicle_replacement_Cars_Global`)
- (Same for 2W, 3W)
- `variance_pct_cars_oem` (calculated vs validation)
- `variance_pct_cars_repl`

---

## 10) Config (example YAML)

```yaml
horizon: 
  start_year: 2020
  end_year: 2040

units:
  demand: tonnes
  stock_vehicles: units
  stock_ups: MWh

lifespans_battery_years:
  sli: 4.5
  motive: 7.0
  stationary_vrla: 6.0

lifespans_asset_scrappage_years:
  passenger_car: 18.0
  two_wheeler: 12.0
  three_wheeler: 12.0
  commercial_vehicle: 20.0
  forklift: 15.0
  ups_rack: 10.0

lead_coefficients_kg_per_unit:
  # Passenger Cars
  car_ice: 11.5
  car_bev: 9.0        # or use scaling: 0.6 × car_ice
  car_phev: null      # use dataset: Passenger_Vehicle_(PHEV)_Average_lead_content_Global
  
  # Two-Wheelers
  two_wheeler_ice: 2.5
  two_wheeler_ev: 1.8  # or use scaling: 0.7 × two_wheeler_ice
  
  # Three-Wheelers
  three_wheeler_ice: 7.0
  three_wheeler_ev: 5.0  # or use scaling: 0.7 × three_wheeler_ice
  
  # Commercial Vehicles
  commercial_vehicle_ice: 22.0
  commercial_vehicle_ev: 18.0   # 12V auxiliary battery
  commercial_vehicle_ngv: 22.0  # same as ICE
  
  # Industrial (if bottom-up)
  forklift_motive: 750.0        # placeholder - requires validation
  ups_stationary_mwh: 300000.0  # 300 kg/kWh placeholder

calculation_strategy:
  sli_method: bottom_up  # options: bottom_up, direct, hybrid
  industrial_method: aggregate  # options: bottom_up, aggregate
  other_uses_method: direct  # options: direct, econometric, price_trend

validation:
  use_direct_demand_comparison: true
  max_variance_pct_threshold: 10.0
  
econometric_drivers:
  # Only used if other_uses_method: econometric
  other_uses_ipi_elasticity: 0.8
  other_uses_gdp_elasticity: 0.5
  other_uses_price_elasticity: -0.1

smoothing:
  rolling_median_years: 3
  
guards:
  min_value: 0.0
  max_growth_rate_pct: 20.0  # flag if YoY growth exceeds this
```

---

## 11) Implementation Blueprint (pseudocode)

```python
# Initialize
config = load_yaml("config.yaml")
datasets = load_datasets()

# Prepare coefficient lookup
def get_coefficient(vehicle_type, powertrain):
    if vehicle_type == "car" and powertrain == "phev":
        return datasets["Passenger_Vehicle_(PHEV)_Average_lead_content_Global"][year]
    else:
        return config["lead_coefficients_kg_per_unit"][f"{vehicle_type}_{powertrain}"]

# Main loop
for t in years:
    # ========== IB UPDATES (per asset & powertrain) ==========
    for vehicle_type in ["car", "2w", "3w", "cv"]:
        for powertrain in get_powertrains(vehicle_type):
            key = f"{vehicle_type}_{powertrain}"
            
            # Get sales from datasets
            sales[key, t] = datasets[f"{vehicle_type}_{powertrain}_sales"][t]
            
            # Update IB
            scrappage[key, t] = IB[key, t-1] / life_asset[vehicle_type]
            IB[key, t] = IB[key, t-1] + sales[key, t] - scrappage[key, t]
            
            # Get coefficient
            kg_per_unit = get_coefficient(vehicle_type, powertrain)
            
            # Calculate OEM demand
            sli_oem[key, t] = sales[key, t] * kg_per_unit / 1000.0  # to tonnes
            
            # Calculate Replacement demand
            contestable[key, t] = IB[key, t] / life_batt['sli']
            sli_repl[key, t] = contestable[key, t] * kg_per_unit / 1000.0  # to tonnes
    
    # Aggregate SLI by vehicle type
    for vehicle_type in ["car", "2w", "3w", "cv"]:
        sli_oem_by_type[vehicle_type, t] = sum(sli_oem[f"{vehicle_type}_{p}", t] 
                                                 for p in get_powertrains(vehicle_type))
        sli_repl_by_type[vehicle_type, t] = sum(sli_repl[f"{vehicle_type}_{p}", t] 
                                                  for p in get_powertrains(vehicle_type))
    
    # Total SLI
    sli_oem_total[t] = sum(sli_oem_by_type[v, t] for v in ["car", "2w", "3w", "cv"])
    sli_repl_total[t] = sum(sli_repl_by_type[v, t] for v in ["car", "2w", "3w", "cv"])
    
    # ========== INDUSTRIAL ==========
    if config["industrial_method"] == "bottom_up":
        # Forklift motive (if data available)
        if "forklift_sales" in datasets:
            motive_new[t] = datasets["forklift_sales"][t] * config["forklift_motive"] / 1000.0
            IB["forklift", t] = IB["forklift", t-1] + datasets["forklift_sales"][t] - ...
            motive_repl[t] = (IB["forklift", t] / life_batt["motive"]) * config["forklift_motive"] / 1000.0
        
        # UPS stationary (if data available)
        if "ups_new_mwh" in datasets:
            stat_new[t] = datasets["ups_new_mwh"][t] * config["ups_stationary_mwh"] / 1000.0
            # ... similar IB logic
    else:  # aggregate method
        # Use direct datasets
        motive_total[t] = datasets["Lead_Annual_Implied_Demand-Industrial_batteries_motive_power_Global"][t]
        stat_total[t] = datasets["Lead_Annual_Implied_Demand-Industrial_batteries_stationary_Global"][t]
    
    # ========== OTHER USES ==========
    if config["other_uses_method"] == "direct":
        other_uses[t] = datasets["Lead_Annual_Implied_Demand-Non-battery_uses_Global"][t]
    elif config["other_uses_method"] == "econometric":
        other_uses[t] = exp(beta0 + beta1*ln(IPI[t]) + beta2*ln(GDP[t]) + beta3*ln(Price[t]))
    else:  # price_trend
        other_uses[t] = other_uses_base * (1 + trend)**t * (Price[t]/Price_base)**beta_price
    
    # ========== TOTAL ==========
    total_demand[t] = (sli_oem_total[t] + sli_repl_total[t] + 
                       motive_total[t] + stat_total[t] + other_uses[t])
    
    # ========== VALIDATION ==========
    if config["validation"]["use_direct_demand_comparison"]:
        for vehicle_type in ["car", "2w", "3w"]:
            if f"Lead_Annual_Implied_Demand-Sales_{vehicle_type}s_Global" in datasets:
                validation_oem = datasets[f"Lead_Annual_Implied_Demand-Sales_{vehicle_type}s_Global"][t]
                variance_pct = abs(sli_oem_by_type[vehicle_type, t] - validation_oem) / validation_oem * 100
                
                if variance_pct > config["validation"]["max_variance_pct_threshold"]:
                    log_warning(f"Year {t}, {vehicle_type} OEM: {variance_pct:.1f}% variance")
    
    # Store outputs...
```

**Apply numerical guards:**
- **Rolling-median smoothing** (3-year window) on demand curves to remove spikes
- **Non-negative clamps** on all demand values
- **Growth rate checks** to flag unrealistic YoY changes
- **Stock-flow consistency** checks (IB changes should match sales - scrappage)

---

## 12) Calibration & QA Steps

1. **Back-cast** 10–15 years and check fit vs ILZSG total.  
   - Target: < 5% MAPE on total demand
   - Check both level and trend alignment

2. **Decompose error** by segment; tune lifetimes & coefficients within documented literature ranges.  
   - Start with SLI segments (largest contributor)
   - Adjust EV coefficients if needed (0.5-0.7 × ICE range)
   - Use direct demand datasets to back-calculate implied coefficients

3. **Validate against direct demand datasets:**
   - Compare bottom-up calculations for Cars, 2W, 3W with direct demand datasets
   - If variance > 10%, investigate:
     - Are coefficients reasonable?
     - Is vehicle fleet data accurate?
     - Are battery lifetimes correct?

4. **Stress tests:** 
   - ±1 year shifts in battery life
   - ±10% in coefficients
   - ±20% in EV adoption rates
   - Faster NGV penetration scenarios
   - Assess impact on total demand volatility

5. **Scenario toggles:** 
   - **EV adoption scenarios:** 
     - Baseline, Accelerated (+20% EV share), Delayed (-20% EV share)
     - Impact: Accelerated EV reduces total lead demand by 5-15% by 2040
   - **Battery lifetime extension:** 
     - Technology improvements extend SLI life to 6 years (vs 4.5 baseline)
     - Impact: Reduces replacement demand by ~25%
   - **Industrial electrification:** 
     - Forklift electrification pace
     - UPS tech mix (VRLA vs Li-ion share)
     - Impact on stationary segment

6. **Evidence register:** Record each parameter source; flag placeholders for client validation.
   - Document all coefficient sources with citations
   - Flag assumptions (e.g., NGV = ICE coefficient, EV scaling factors)
   - List datasets used vs available but unused
   - Note data quality issues or gaps

---

## 13) Notes on Consistency with SWB/Datacenter Methods

- Uses the **same accounting mechanics** as Datacenter UPS (Installed-Base → Contestable → Replacement).  
- Reuses **stability guards** (rolling-median smoothing, clamps) and documentation rigor from SWB instructions; keep these identical across modules for auditability.
- **Bottom-up philosophy:** Build from granular segments (vehicle types, powertrains) with validation against aggregates
- **Transparency:** Every tonne of demand should be traceable to specific asset counts/sales and coefficients

---

## 14) Special Considerations

### 14.1 NGV (Natural Gas Vehicles)
- NGVs are a significant and growing segment in commercial vehicles (especially in regions with CNG/LNG infrastructure)
- Use lead-acid SLI batteries similar to diesel/petrol CVs
- Apply same coefficient as ICE CVs unless specific data indicates different battery sizes
- Dataset: `Commercial_Vehicle_(NGV)_Annual_Sales_Global`, `Commercial_Vehicle_(NGV)_Total_Fleet_Global`

### 14.2 PHEV Special Handling
- Dedicated coefficient dataset available: `Passenger_Vehicle_(PHEV)_Average_lead_content_Global`
- Pre-calculated demand also available: `Passenger_Vehicle_(PHEV)_Annual_Lead_Implied_Demand_Global`
- Approach: Use coefficient dataset in bottom-up; validate against pre-calculated demand
- PHEV batteries may differ from pure ICE or BEV due to hybrid system requirements

### 14.3 EV Fleet Growth Impact
- As EV share increases, average lead content per vehicle declines
- Monitor "blended coefficient" trends: `Total_SLI_Demand / Total_Vehicle_Sales`
- Expected trajectory: ~12-15 kg/car (2020) → 8-10 kg/car (2040) as EV share rises
- Replacement demand lags OEM demand by battery lifetime (~4-5 years)

### 14.4 Data Quality Notes
- **Passenger_Vehicle_(EV)_Annual_Sales_Global** may overlap with BEV; verify and avoid double-counting
- Some datasets may include projections beyond historical data; validate consistency of historical vs projected values
- Fleet data should be consistent with sales data after accounting for scrappage

---

### Deliverables

- **CSV/Parquet** in "Output Schema" format (§9)
- **Config YAML** used for the run (§10)
- **QA report** (fit vs ILZSG, parameter table, sensitivity outcomes) (§12)
- **Evidence register** (sources for lifetimes, coefficients, IB warm-ups) (§12.6)
- **Validation summary** comparing bottom-up vs direct demand datasets
- **Scenario analysis** (at minimum: baseline, accelerated EV, extended battery life)
