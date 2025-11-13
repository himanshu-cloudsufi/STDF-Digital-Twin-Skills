# instructions.md — Copper Demand Forecasting (Hybrid Bottom-Up + Top-Down Framework)

> This guide standardizes how to forecast refined **copper demand (tonnes/year)** using a **hybrid methodology** that combines bottom-up installed-base accounting (where driver data exists) with top-down allocation from segment shares (where drivers are missing). The approach is adapted for available data constraints while maintaining transparency about confidence levels and assumptions.

---

## 1) Scope & Objectives

- **Horizon:** 10–20 years (e.g., 2024–2045), **annual** step  
- **Granularity:** Global aggregate built from independently modeled end-use segments  
- **Primary flow unit:** tonnes of **refined copper** consumed per year  
- **Primary stock unit:** Installed Base (**IB**) tracked where data permits (vehicle parc in **units**; generation capacity in **GW**)  
- **Core principle:** For each segment, demand = **OEM (new-build)** + **Replacement** (from IB refurbishment cycles)  
- **Methodology:** **Hybrid approach** combining:
  - **TIER 1 (Bottom-Up):** Where sales/fleet/capacity drivers exist → installed-base accounting
  - **TIER 2 (Top-Down):** Where drivers missing → allocation from segment shares
  - **Anchor:** Total consumption (`Copper_Annual_Consumption_Global`) reconciles all segments

---

## 2) Forecast Identity (Top Level)

**Total_Copper_Demand(t) = Demand_Grid(t) + Demand_Construction(t) + Demand_Automotive(t) + Demand_Industrial(t) + Demand_Electronics(t) + Demand_Other_Uses(t)**

### 2.1 Segment Decomposition (each = OEM + Replacement)

- **Grid:** Transmission lines, Distribution lines, Transformers, Generation-linked wiring
- **Construction:** Residential, Non-residential (commercial/institutional)
- **Automotive:** Passenger cars, Commercial vehicles, 2-wheelers, 3-wheelers (by powertrain: ICE/HEV/PHEV/BEV where applicable)
- **Industrial:** Motors, HVAC, machinery
- **Electronics:** Phones, PCs, appliances ("white goods")
- **Other Uses:** Alloys (brass/bronze), ammunition, pigments, miscellaneous

**Segment identity:** `Demand_Segment(t) = Segment_OEM(t) + Segment_Replacement(t)`

---

## 2.5) Hybrid Calculation Strategy (Data-Constrained Implementation)

### 2.5.1 Two-Tier Approach

Given available datasets, the model employs a **two-tier methodology**:

**TIER 1 — Bottom-Up (High Confidence):**
- ✅ **Automotive:** Complete sales & fleet data for all vehicle types/powertrains → full installed-base accounting
- ✅ **Grid Generation-Linked:** Installed capacity for Wind/Solar/Gas/Coal → derive new capacity via differencing

**TIER 2 — Top-Down Allocation (Lower Confidence):**
- ⚠️ **Construction:** Missing floorspace data → allocate from Electrical segment share
- ⚠️ **Grid T&D:** Missing km/transformer data → residual after generation-linked component
- ⚠️ **Industrial:** Missing motor sales → allocate from Electrical segment share
- ⚠️ **Electronics:** Missing device sales → fixed share or residual allocation
- ⚠️ **Other Uses:** Residual with bounds and smoothing

### 2.5.2 Reconciliation Framework

1. **Anchor to known total:** `Copper_Annual_Consumption_Global(t)` is the reference truth
2. **Calculate bottom-up first:** Automotive, Grid generation-linked (where drivers exist)
3. **Allocate remainder:** Use segment share datasets to distribute remaining demand
4. **Validate consistency:** Cross-check calculated shares against `Copper_Demand_X_Percentage_Global` datasets
5. **Force reconciliation:** Apply proportional adjustments to ensure sum equals total (within 0.1%)

### 2.5.3 Confidence Levels & Transparency

All outputs must be tagged with confidence levels:
- **HIGH:** Bottom-up from driver data (Automotive, Grid gen)
- **MEDIUM:** Top-down validated against segment shares (Construction, Industrial)
- **LOW:** Residual or assumption-based (Other Uses, OEM/Replacement splits)

Document all assumptions, coefficients, and allocation factors in the **Evidence Register**.

---

## 3) Installed-Base (IB) Accounting & Lifetimes

For each asset class A ∈ {Cars, CVs, 2W, 3W, Wind_GW, Solar_GW, Buildings_sqm (implied), Motors_MW (implied), …}:

**IB_A(t+1) = IB_A(t) + Adds_A(t) − Scrappage_A(t)**

- **Adds_A(t):** new sales/installs in year *t* (units/GW/sqm/MW) → drives **OEM**  
- **Scrappage_A(t):** end-of-life of the asset itself; baseline: `IB_A(t) / Life_Asset_A` (or a lifetime distribution)  
- **Replacement demand** occurs when **sub-components** within the IB reach end-of-life or planned refurbishment cycles:  
  `Contestable_for_Replacement_A(t) ≈ IB_A(t) / Life_Component_A`

**IB Tracking Status:**
- ✅ **Vehicles:** Direct tracking from fleet datasets
- ✅ **Generation capacity:** Direct tracking from installed capacity datasets
- ⚠️ **Construction, Grid T&D, Industrial:** **Implied** via back-calculation from demand (not direct tracking)

**Typical lifetimes** (tune per literature/region):  
- **Refurb cycles (components):** Grid lines **25–40y**, Building retrofit **20–30y**, Industrial motor/HVAC **15–20y**  
- **Assets (scrappage):** Passenger car **15–20y**, Transformer **40–50y**, Building shell **50–100y**

---

## 4) New-Build (OEM) Modules

### 4.1 Automotive OEM ✅ BOTTOM-UP (High Confidence)

**Data Status:** ✅ Complete — All vehicle sales & fleet datasets available

**Inputs (annual):** New vehicle sales by type & powertrain (ICE/HEV/PHEV/BEV/NGV).  

**Available Datasets:**
- `Passenger_Vehicle_(ICE/BEV/PHEV)_Annual_Sales_Global`
- `Commercial_Vehicle_(ICE/EV/NGV)_Annual_Sales_Global`
- `Two_Wheeler_(ICE/EV)_Annual_Sales_Global`
- `Three_Wheeler_(ICE/EV)_Annual_Sales_Global`

**Coefficients (kg/unit):**  
- Passenger cars: `k_car_ICE: 23`, `k_car_BEV: 83`, `k_car_PHEV: 60`, `k_car_HEV: 35`
- Commercial vehicles: `k_cv_ICE: 35`, `k_cv_EV: 120`, `k_cv_NGV: 38`
- Two-wheelers: `k_2w_ICE: 3`, `k_2w_EV: 4`
- Three-wheelers: `k_3w_ICE: 4`, `k_3w_EV: 5`

> **Note:** BEV copper per vehicle (≈80–85 kg) is typically **3–4×** ICE (≈20–25 kg); this drives demand growth as EV adoption accelerates.

**Identity:**  
```
Auto_OEM(t) = Σ_vehicle_type Σ_powertrain [Sales_v,p(t) × k_v,p(kg)] / 1000  → tonnes
```

**Implementation:**
1. Load sales datasets for all vehicle types/powertrains
2. Apply copper coefficients per kg/vehicle
3. Sum across all segments and convert kg → tonnes
4. Update installed base: `IB_vehicle(t) = IB(t-1) + Sales(t) - Scrappage(t)`
   - Scrappage: `IB(t-1) / Life_vehicle` (use 18y for cars, 20y for CVs)

**Validation:**
- `Auto_OEM(t) / Total_Consumption(t)` should match `Copper_Demand_Transportation_Percentage_Global(t)` (±2%)
- `Auto_BEV_Demand(t) / Total_Consumption(t)` should match `Copper_EV_Demand_Percentage_Global(t)` (±3%)

---

### 4.2 Construction OEM ⚠️ TOP-DOWN (Lower Confidence)

**Data Status:** ❌ Missing floorspace data — Use top-down allocation

**FALLBACK METHOD (when floorspace data unavailable):**

**Step 1 — Derive total Construction demand from shares:**

```
Electrical_Total(t) = Copper_Annual_Consumption_Global(t) 
                      × Copper_Electrical_Demand_Percentage_Global(t)

Construction_Total(t) = Electrical_Total(t) × construction_split_factor
```

Where `construction_split_factor = 0.48` (Construction ≈ 48% of Electrical segment)
- Empirical range: 45–52% based on ICA, ICSG literature
- Tune via calibration if historical segment-level data available

**Step 2 — Split OEM vs Replacement:**

**Option A (Growth-proxy method):**
```
Electricity_Growth(t) = [Electricity_Annual_Production_Global(t) 
                         / Electricity_Annual_Production_Global(t-1)] - 1

Construction_OEM(t) = Construction_Total(t) × OEM_factor(t)
Construction_Replacement(t) = Construction_Total(t) - Construction_OEM(t)
```

Where:
```
OEM_factor(t) = 0.65 + 0.15 × tanh(Electricity_Growth(t) / 0.03)
```
- Default: 65% OEM / 35% Replacement
- Adjust upward when electricity growth high (urbanization, construction boom)
- Adjust downward when growth slow (mature markets)

**Option B (Fixed split):**
```
Construction_OEM(t) = Construction_Total(t) × 0.65
Construction_Replacement(t) = Construction_Total(t) × 0.35
```

**Assumptions to document:**
- Global construction copper intensity (blended): ~4.5 kg/sqm new-build, ~2.5 kg/sqm retrofit
- Retrofit cycle: 25 years → ~4% annual replacement rate
- Construction share of Electrical: 48% (range: 45–52%)
- OEM/Replacement split: 65/35 (range: 60–70% OEM)

**Implied Back-Calculation (for reference):**
```
Implied_New_Floorspace(t) = Construction_OEM(t) / (k_sqm_blended / 1000)  → million sqm
Implied_Retrofit_Floorspace(t) = Construction_Replacement(t) / (k_sqm_retrofit / 1000)
```
Tag these as **"IMPLIED FROM ALLOCATION"** in outputs.

**Alternative (if GDP data available):**
```
Construction_Total(t) = Construction_Total(t-1) × [1 + 0.7 × GDP_growth_rate(t)]
```
Use GDP elasticity of 0.7 for construction copper intensity.

---

### 4.3 Power Grid (Hybrid: Generation Bottom-Up + T&D Top-Down)

#### 4.3.1 Generation-Linked Copper ✅ BOTTOM-UP (Medium Confidence)

**Data Status:** ✅ Partial — Have installed capacity, derive new capacity

**Available Datasets:**
- `Onshore_Wind_Installed_Capacity_Global`
- `Offshore_Wind_Installed_Capacity_Global`
- `Solar_Installed_Capacity_Global`
- `Coal_Installed_Capacity_Global`
- `Natural_Gas_Installed_Capacity_Global`

**Calculate annual NEW capacity (GW):**
```
New_Capacity_gen(t) = max(0, Installed_Capacity_gen(t) - Installed_Capacity_gen(t-1))
```

**Coefficients (tonnes/MW):**
- Wind onshore: 6.0 (range: 4–10)
- Wind offshore: 10.0 (range: 8–12)
- Solar PV: 5.0 (range: 4–6)
- Gas CCGT: 1.0 (range: 0.8–1.2)
- Coal: 1.0 (range: 0.8–1.2)

**Identity:**
```
Grid_Generation_OEM(t) = Σ_gen [New_Capacity_gen(t) × 1000 MW/GW × k_tonnes_per_MW_gen]
```

**Example:**
```
Grid_Generation_OEM(2025) = (New_Wind_Onshore × 1000 × 6.0) 
                             + (New_Wind_Offshore × 1000 × 10.0)
                             + (New_Solar × 1000 × 5.0)
                             + (New_Gas × 1000 × 1.0)
                             + (New_Coal × 1000 × 1.0)  → tonnes
```

**Validation:**
```
Grid_Gen_Renewables_Demand(t) / Total_Consumption(t) 
  should match [Copper_Solar_Demand_Percentage_Global(t) 
                + Copper_Wind_Turbines_Percentage_Global(t)] (±4%)
```

---

#### 4.3.2 T&D Lines & Transformers ⚠️ TOP-DOWN (Lower Confidence)

**Data Status:** ❌ Missing km/GW data — Use residual allocation

**FALLBACK METHOD:**

**Step 1 — Estimate total Grid demand from Electrical share:**
```
Electrical_Total(t) = Copper_Annual_Consumption_Global(t) 
                      × Copper_Electrical_Demand_Percentage_Global(t)

Grid_Total_from_Share(t) = Electrical_Total(t) × grid_split_factor
```
Where `grid_split_factor = 0.35` (Grid ≈ 35% of Electrical segment)
- Range: 32–38% based on literature

**Step 2 — Subtract generation-linked to get T&D residual:**
```
Grid_TD_and_Transformers_Total(t) = Grid_Total_from_Share(t) - Grid_Generation_OEM(t)
```

**Step 3 — Split OEM vs Replacement:**

**Method A (Electricity growth proxy):**
```
Electricity_Growth(t) = [Electricity_Annual_Production_Global(t) 
                         / Electricity_Annual_Production_Global(t-1)] - 1

Grid_TD_OEM(t) = Grid_TD_Total(t) × [Electricity_Growth(t) / (Electricity_Growth(t) + 1/40)]
Grid_TD_Replacement(t) = Grid_TD_Total(t) - Grid_TD_OEM(t)
```
Logic: When electricity growing fast → more OEM; when stable → more replacement

**Method B (Fixed split):**
```
Grid_TD_OEM(t) = Grid_TD_Total(t) × 0.70  (70% OEM assumption)
Grid_TD_Replacement(t) = Grid_TD_Total(t) × 0.30  (30% Replacement, ~40y refurb cycle)
```

**Combine Grid components:**
```
Grid_OEM(t) = Grid_Generation_OEM(t) + Grid_TD_OEM(t)
Grid_Replacement(t) = Grid_TD_Replacement(t)
Grid_Total(t) = Grid_OEM(t) + Grid_Replacement(t)
```

**Implied Back-Calculation (for reference):**
```
# Assume 60% of T&D is transmission, 40% distribution
Implied_Transmission_km(t) = Grid_TD_Total(t) × 0.60 / k_per_km_transmission  → km
Implied_Distribution_km(t) = Grid_TD_Total(t) × 0.40 / k_per_km_distribution  → km

# Assume transformers are ~20% of Grid T&D demand
Implied_Transformer_GW(t) = Grid_TD_Total(t) × 0.20 / k_per_GW_transformer  → GW
```

**Assumptions:**
- T&D refurb cycle: 40 years → ~2.5% annual replacement
- Grid share of Electrical: 35% (range: 32–38%)
- OEM/Replacement default: 70/30 (adjust based on electrification rate)
- Coefficients (for reference only): 7 t/km transmission, 3.5 t/km distribution, 800 t/GW transformer

---

### 4.4 Industrial OEM ⚠️ TOP-DOWN (Lower Confidence)

**Data Status:** ❌ Missing motor sales data — Use top-down allocation

**FALLBACK METHOD:**

**Step 1 — Derive from Electrical share:**
```
Electrical_Total(t) = Copper_Annual_Consumption_Global(t) 
                      × Copper_Electrical_Demand_Percentage_Global(t)

Industrial_Total(t) = Electrical_Total(t) × industrial_split_factor
```
Where `industrial_split_factor = 0.17` (Industrial ≈ 17% of Electrical segment)
- Range: 15–20% based on literature

**Step 2 — Split OEM vs Replacement:**

**Method A (Electricity-linked):**
```
Electricity_Growth(t) = [Electricity_Annual_Production_Global(t) 
                         / Electricity_Annual_Production_Global(t-1)] - 1

Industrial_OEM(t) = Industrial_Total(t) × [0.60 + 0.20 × tanh(Electricity_Growth(t) / 0.03)]
Industrial_Replacement(t) = Industrial_Total(t) - Industrial_OEM(t)
```
- Default: 60% OEM / 40% Replacement
- Higher OEM when industrial growth strong

**Method B (Fixed split):**
```
Industrial_OEM(t) = Industrial_Total(t) × 0.60
Industrial_Replacement(t) = Industrial_Total(t) × 0.40
```

**Assumptions:**
- Industrial motor life: 18 years → ~5.5% annual replacement rate
- Industrial share of Electrical: 17% (range: 15–20%)
- OEM/Replacement split: 60/40 (range: 55–65% OEM)
- Copper per MW motor: ~5 tonnes/MW (for reference)

**Implied Back-Calculation (for reference):**
```
Implied_Motor_Sales_MW(t) = Industrial_OEM(t) / k_per_MW_motor  → MW
Implied_Motor_IB_MW(t) = Industrial_Replacement(t) × Life_motor / k_per_MW_motor  → MW
```

---

### 4.5 Electronics OEM ⚠️ TOP-DOWN (Lower Confidence)

**Data Status:** ❌ Missing device sales data — Use fixed share or residual

**FALLBACK METHOD:**

**Option A — Fixed share (preferred for stability):**
```
Electronics_Total(t) = Copper_Annual_Consumption_Global(t) × electronics_share
```
Where `electronics_share = 0.11` (Electronics ≈ 11% of total demand)
- Range: 10–12% based on historical data
- Relatively stable over time (mature market)

**Option B — Residual allocation:**
```
Electronics_Total(t) = Copper_Annual_Consumption_Global(t) 
                       - [Auto_Total + Construction_Total + Grid_Total 
                          + Industrial_Total + Other_Uses_Total]
```
Use when sum of other segments is well-constrained.

**OEM vs Replacement:**
```
Electronics_OEM(t) = Electronics_Total(t)  (100% OEM)
Electronics_Replacement(t) = 0.0  (replacement captured via new sales)
```

**Forward Forecast (when extrapolating):**
```
Electronics_Total(t+1) = Electronics_Total(t) × (1 + electronics_growth_rate)
```
Where `electronics_growth_rate = 0.025` (2.5% annual, stable growth)

**Assumptions:**
- Electronics share: 11% (range: 10–12%)
- Growth: 2.5% annually (mature market, stable demand)
- Copper content declining per device (miniaturization) offset by volume growth

**Implied Back-Calculation (for reference):**
```
# Assume device mix: 40% phones, 30% PCs, 30% appliances
Implied_Phones_millions(t) = Electronics_Total(t) × 0.40 / k_phone  → million units
Implied_PCs_millions(t) = Electronics_Total(t) × 0.30 / k_pc  → million units
Implied_Appliances_millions(t) = Electronics_Total(t) × 0.30 / k_appliance  → million units
```
Where: `k_phone = 0.015 kg`, `k_pc = 0.8 kg`, `k_appliance = 1.5 kg` (blended average)

---

## 5) Replacement Modules

### 5.1 Automotive Replacement ✅ BOTTOM-UP

- Bulk copper in a vehicle (wiring, motors) is seldom replaced mid-life; replacement occurs when **vehicles are replaced**, which is captured in **OEM** via sales to offset scrappage.  

**Identity:**  
```
Auto_Replacement(t) = 0  (fully captured in OEM)
```

---

### 5.2 Construction Replacement ⚠️ TOP-DOWN

**Captured in §4.2 Construction OEM fallback method.**

```
Construction_Replacement(t) = Construction_Total(t) × (1 - OEM_factor)
```
Where OEM_factor typically 0.65, so Replacement = 35% of total.

**Logic:**
- Represents renovation, retrofit, and component replacement in existing buildings
- 25-year retrofit cycle implies ~4% of stock renovated annually
- Lower copper intensity than new-build (partial rewiring vs. full installation)

---

### 5.3 Power Grid Replacement ⚠️ TOP-DOWN

**Captured in §4.3.2 Grid T&D fallback method.**

```
Grid_Replacement(t) = Grid_TD_Replacement(t)
```
Where Grid_TD_Replacement typically 30% of Grid T&D total.

**Logic:**
- Generation equipment replacement captured in new capacity (decommissioning offset by new builds)
- T&D refurbishment: 40-year cycle → ~2.5% of network annually
- Transformers: 45-year life → ~2.2% annual replacement

---

### 5.4 Industrial Replacement ⚠️ TOP-DOWN

**Captured in §4.4 Industrial OEM fallback method.**

```
Industrial_Replacement(t) = Industrial_Total(t) × 0.40
```

**Logic:**
- Motor/equipment life: 18 years → ~5.5% annual replacement
- HVAC, machinery refurbishment cycles: 15–20 years
- Lower confidence due to lack of installed base tracking

---

### 5.5 Electronics Replacement ✅ CONCEPTUAL

**Identity:**  
```
Electronics_Replacement(t) = 0  (fully captured in OEM)
```

Like automotive, device replacement drives new sales (no mid-life copper component replacement).

---

## 6) "Other Uses" (~10–15%) — Residual Method

**Data Status:** ❌ No direct dataset — Use residual with bounds

**METHOD:**

**Step 1 — Calculate as residual:**
```
Other_Uses_Raw(t) = Copper_Annual_Consumption_Global(t) 
                    - [Auto_Total(t) + Construction_Total(t) + Grid_Total(t) 
                       + Industrial_Total(t) + Electronics_Total(t)]
```

**Step 2 — Apply bounds:**
```
Other_Uses_Bounded(t) = clip(Other_Uses_Raw(t), 
                              Total_Consumption(t) × 0.08,  # Min 8%
                              Total_Consumption(t) × 0.18)  # Max 18%
```
Historical range: 10–15%, allow 8–18% for robustness.

**Step 3 — Apply smoothing:**
```
Other_Uses(t) = rolling_median(Other_Uses_Bounded, window=5)  # 5-year median
```
Reduces noise from allocation errors in other segments.

**Forward Forecast:**
```
Other_Uses(t+1) = Other_Uses(t) × (1 + other_uses_growth_rate)
```
Where `other_uses_growth_rate = 0.015` (1.5% annual, slower than main sectors)

**Price Elasticity (optional, if Copper_Price_Global available):**
```
Price_Ratio(t) = Copper_Price_Global(t) / Copper_Price_Global(t-5_yr_avg)
Other_Uses(t+1) = Other_Uses(t) × (1 + 0.018 - 0.15 × ln(Price_Ratio(t)))
```
Logic: Other Uses includes discretionary/substitutable applications (alloys, pigments) → price-sensitive.

**Assumptions:**
- Other Uses: 10–15% of total (non-electrical applications)
- Includes: Brass/bronze alloys, ammunition, architectural uses, pigments, chemicals
- Relatively price-sensitive compared to structural/electrical uses
- Mature market, slow growth (1.5% annually)

---

## 7) Data Mapping, Parameters & Fallbacks

### 7.1 Input Families (AVAILABLE DATASETS)

**✅ TIER 1 — Direct Bottom-Up (High Confidence):**

**Vehicles (Complete):**
- Sales: `Passenger_Vehicle_(BEV/ICE/PHEV)_Annual_Sales_Global`
- Sales: `Commercial_Vehicle_(EV/ICE/NGV)_Annual_Sales_Global`
- Sales: `Two_Wheeler_(EV/ICE)_Annual_Sales_Global`
- Sales: `Three_Wheeler_(EV/ICE)_Annual_Sales_Global`
- Fleet: `Passenger_Vehicle_(BEV/ICE/PHEV)_Total_Fleet_Global`
- Fleet: `Commercial_Vehicle_(EV/ICE/NGV)_Total_Fleet_Global`
- Fleet: `Two_Wheeler_(EV/ICE)_Total_Fleet_Global`
- Fleet: `Three_Wheeler_(EV/ICE)_Total_Fleet_Global`

**Energy Generation (Partial — derive new capacity):**
- `Onshore_Wind_Installed_Capacity_Global`
- `Offshore_Wind_Installed_Capacity_Global`
- `Solar_Installed_Capacity_Global`
- `Coal_Installed_Capacity_Global`
- `Natural_Gas_Installed_Capacity_Global`
- `Oil_Installed_Capacity_Global`
- `Battery_Energy_Storage_System_Installed_Capacity_Global`
- Supporting: `X_Annual_Power_Generation_Global`, `X_Capacity_Factor_Global`, `X_LCOE_Global`

**⚠️ TIER 2 — Top-Down from Shares (Lower Confidence):**

**Market Totals (Primary Anchor):**
- `Copper_Annual_Consumption_Global` ← **PRIMARY REFERENCE**
- Regional: `Copper_Annual_Consumption_China/Europe/USA/Rest_of_World` (validation)

**Segment Shares (Allocation & Validation):**
- `Copper_Demand_Transportation_Percentage_Global` → validates Automotive
- `Copper_Electrical_Demand_Percentage_Global` → allocates Construction+Grid+Industrial
- `Copper_EV_Demand_Percentage_Global` → validates BEV/ICE split
- `Copper_Solar_Demand_Percentage_Global` → validates Solar generation-linked
- `Copper_Wind_Turbines_Percentage_Global` → validates Wind generation-linked

**Context Datasets (Proxies & Validation):**
- `Electricity_Annual_Production_Global` → growth proxy for Construction, Industrial, Grid T&D
- `Electricity_Annual_Domestic_Consumption_Global` → alternative growth proxy
- `Copper_Price_Global` → elasticity for Other Uses (optional)
- `Copper_Annual_Production_Global`, `Copper_Annual_Recycling_Rate_Global` → context
- Cost/LCOE datasets → context for generation analysis

**❌ MISSING (Use Fallbacks):**
- Construction: NO floorspace data → Top-down from Electrical share × 0.48
- Grid T&D: NO km/GW data → Residual after generation-linked
- Industrial: NO motor data → Top-down from Electrical share × 0.17
- Electronics: NO device sales → Fixed share (11%) or residual
- Macro: NO GDP/IPI → Use Electricity_Annual_Production_Global growth as proxy

---

### 7.2 Parameters & Coefficients (Assumptions)

**Automotive (kg/vehicle) — TIER 1 (High Confidence):**
- `car_ice: 23.0`
- `car_bev: 83.0`
- `car_phev: 60.0`
- `car_hev: 35.0`
- `cv_ice: 35.0`
- `cv_ev: 120.0`
- `cv_ngv: 38.0`
- `two_wheeler_ice: 3.0`
- `two_wheeler_ev: 4.0`
- `three_wheeler_ice: 4.0`
- `three_wheeler_ev: 5.0`

**Grid Generation (tonnes/MW) — TIER 1 (Medium Confidence):**
- `per_mw_wind_onshore: 6.0` (range: 4–10)
- `per_mw_wind_offshore: 10.0` (range: 8–12)
- `per_mw_solar_pv: 5.0` (range: 4–6)
- `per_mw_gas_ccgt: 1.0` (range: 0.8–1.2)
- `per_mw_coal: 1.0` (range: 0.8–1.2)

**Construction (kg/sqm) — TIER 2 (For Reference Only):**
- `sqm_resi_new: 4.0` (range: 3–5)
- `sqm_nonresi_new: 6.5` (range: 5–8)
- `sqm_resi_reno: 2.0` (range: 1–3)
- `sqm_nonresi_reno: 3.0` (range: 2–4)
- Blended average: ~4.5 kg/sqm new-build, ~2.5 kg/sqm retrofit

**Grid T&D (tonnes per unit) — TIER 2 (For Reference Only):**
- `per_km_transmission: 7.0` (range: 7–12)
- `per_km_distribution: 3.5` (range: 3–5)
- `per_gw_transformer: 800.0` (range: 600–1000)

**Industrial (tonnes/MW) — TIER 2 (For Reference Only):**
- `per_mw_motor: 5.0` (range: 4–6)

**Electronics (kg/unit) — TIER 2 (For Reference Only):**
- `per_phone: 0.015` (15g, declining)
- `per_pc: 0.8` (800g)
- `per_appliance: 1.5` (1.5kg blended: refrigerators, washers, etc.)

**Segment Allocation Factors — TIER 2 (Core Assumptions):**

**Within Electrical segment splits:**
- `construction_pct: 0.48` (Construction = 48% of Electrical; range: 45–52%)
- `grid_pct: 0.35` (Grid = 35% of Electrical; range: 32–38%)
- `industrial_pct: 0.17` (Industrial = 17% of Electrical; range: 15–20%)

**Direct shares (% of total demand):**
- `electronics_pct: 0.11` (Electronics = 11% of total; range: 10–12%)
- `other_uses_pct: 0.12` (Other Uses target = 12%; historical range: 10–15%)

**OEM/Replacement Default Splits (when cannot calculate):**
- `construction_oem_pct: 0.65` (65% OEM, 35% Replacement; range: 60–70%)
- `grid_td_oem_pct: 0.70` (70% OEM, 30% Replacement; range: 65–75%)
- `industrial_oem_pct: 0.60` (60% OEM, 40% Replacement; range: 55–65%)

**Lifespans — Component Refurbishment Cycles (years):**
- `grid_refurb_cycle: 40.0`
- `construction_retrofit_cycle: 25.0`
- `industrial_motor: 18.0`
- `transformer: 45.0`

**Lifespans — Asset Scrappage (years):**
- `passenger_car: 18.0`
- `commercial_vehicle: 20.0`
- `two_wheeler: 12.0`
- `three_wheeler: 10.0`
- `building_shell: 70.0`

**Growth Proxies (for forward forecasting without drivers):**
- `construction_electricity_elasticity: 0.7` (Construction grows at 70% of electricity growth)
- `industrial_electricity_elasticity: 0.8` (Industrial grows at 80% of electricity growth)
- `electronics_annual_growth: 0.025` (2.5% per year, stable)
- `other_uses_annual_growth: 0.015` (1.5% per year, slow)
- `other_uses_price_elasticity: -0.15` (Price sensitivity for Other Uses)

---

### 7.3 Fallback Rules & Decision Tree

**PRIORITY ORDER:**
1. ✅ **Use total consumption as anchor** → `Copper_Annual_Consumption_Global(t)` is the reference truth
2. ✅ **Calculate bottom-up where possible** → Automotive (full), Grid generation-linked (partial)
3. ⚠️ **Allocate remainder using shares** → Construction, Industrial, Electronics, Other Uses
4. ✅ **Validate with segment percentages** → Transportation, Electrical, EV, Solar, Wind shares
5. ✅ **Force reconciliation** → Ensure sum of all segments = total (±0.1%)

**SPECIFIC FALLBACKS:**

| Missing Data | Fallback Method | Confidence | Notes |
|--------------|-----------------|------------|-------|
| **Vehicle IB (t=0)** | Warm up using ≥18 years historical sales | HIGH | `IB(0) = Σ_{i=1}^{18} Sales(0-i)` |
| **New capacity (energy)** | Difference consecutive installed capacity | MEDIUM | `New(t) = max(0, Installed(t) - Installed(t-1))` |
| **Floorspace data** | Construction = Electrical_share × 0.48 × Total | LOW | Top-down allocation |
| **T&D km, Transformer GW** | Grid_TD = Electrical_share × 0.35 × Total - Gen_linked | LOW | Residual method |
| **Motor sales** | Industrial = Electrical_share × 0.17 × Total | LOW | Top-down allocation |
| **Device sales** | Electronics = 0.11 × Total or residual | LOW | Fixed share or residual |
| **Other Uses direct** | Residual, bounded 8–18%, 5-yr smoothing | LOW | Residual with guards |
| **GDP/IPI** | Use Electricity_Annual_Production_Global growth | MEDIUM | Proxy for economic activity |
| **Coefficients** | Use literature mid-points from §7.2 | MEDIUM | Document as assumptions |
| **OEM/Replacement split** | Use defaults from §7.2 (65/35, 70/30, 60/40) | LOW | Adjust by growth proxy |

**DATA QUALITY GUARDS:**
- ✅ **3-year rolling median:** Apply to all derived flows (Construction, Industrial, Grid T&D, Other Uses)
- ✅ **Non-negativity clamps:** All outputs ≥ 0
- ✅ **Growth-rate guards:** If any segment YoY > +50% or < -30% → flag, investigate, smooth
- ✅ **Share validation:** If calculated segment share deviates >5% from percentage datasets → apply proportional adjustment and flag in QA report
- ✅ **Bounds on residuals:** Other Uses must be 8–18% of total; if outside, flag data issue

---

## 8) Aggregation, Reconciliation & Validation

### 8.1 Aggregation Identity (tonnes)

```
Total_Copper_Demand(t) = 
  // OEM components
  Auto_OEM(t) 
  + Construction_OEM(t) 
  + Grid_OEM(t)               // = Grid_Generation_OEM + Grid_TD_OEM
  + Industrial_OEM(t) 
  + Electronics_OEM(t)
  
  // Replacement components
  + Auto_Replacement(t)        // = 0
  + Construction_Replacement(t) 
  + Grid_Replacement(t)        // = Grid_TD_Replacement
  + Industrial_Replacement(t) 
  + Electronics_Replacement(t) // = 0
  
  // Other
  + Other_Uses(t)
```

**Simplified:**
```
Total_Copper_Demand(t) = Auto_Total(t) 
                         + Construction_Total(t) 
                         + Grid_Total(t) 
                         + Industrial_Total(t) 
                         + Electronics_Total(t) 
                         + Other_Uses(t)
```

---

### 8.2 Top-Down Reconciliation Loop

**STEP-BY-STEP RECONCILIATION:**

**1. Load anchor:**
```
Total_Consumption(t) = Copper_Annual_Consumption_Global(t)  # Known truth
```

**2. Calculate TIER 1 (bottom-up) segments:**
```
Auto_Total(t) = Auto_OEM(t)  # From vehicle sales × coefficients
Grid_Generation_OEM(t) = Σ[New_Gen_Capacity × k_per_MW]  # From energy capacity differencing
```

**3. Load segment shares:**
```
Share_Transport(t) = Copper_Demand_Transportation_Percentage_Global(t)
Share_Electrical(t) = Copper_Electrical_Demand_Percentage_Global(t)
Share_EV(t) = Copper_EV_Demand_Percentage_Global(t)
Share_Solar(t) = Copper_Solar_Demand_Percentage_Global(t)
Share_Wind(t) = Copper_Wind_Turbines_Percentage_Global(t)
```

**4. Validate TIER 1 against shares:**
```
# Check Automotive
Auto_Implied_Share(t) = Auto_Total(t) / Total_Consumption(t)
Variance_Auto = abs(Auto_Implied_Share - Share_Transport)

if Variance_Auto > 0.02:  # >2% deviation
    flag_for_review(t, "Automotive", Auto_Implied_Share, Share_Transport)
    # Options: 
    # A) Adjust Auto_Total proportionally to match share (if share data more trusted)
    # B) Keep bottom-up value, document variance (if vehicle data more trusted)

# Check Grid Renewables
Grid_Renewables_Implied(t) = Grid_Gen_from_Solar_Wind(t) / Total_Consumption(t)
Grid_Renewables_Share(t) = Share_Solar(t) + Share_Wind(t)
Variance_Renewables = abs(Grid_Renewables_Implied - Grid_Renewables_Share)

if Variance_Renewables > 0.04:  # >4% deviation
    flag_for_review(t, "Grid_Renewables", Grid_Renewables_Implied, Grid_Renewables_Share)
```

**5. Allocate TIER 2 (top-down) segments:**
```
Electrical_Total(t) = Total_Consumption(t) × Share_Electrical(t)

Construction_Total(t) = Electrical_Total(t) × construction_split_factor  # 0.48
Grid_TD_Total(t) = Electrical_Total(t) × grid_split_factor - Grid_Generation_OEM(t)  # 0.35
Industrial_Total(t) = Electrical_Total(t) × industrial_split_factor  # 0.17

Electronics_Total(t) = Total_Consumption(t) × electronics_share  # 0.11
```

**6. Calculate Other Uses as residual:**
```
Other_Uses_Raw(t) = Total_Consumption(t) 
                    - [Auto_Total(t) + Construction_Total(t) + Grid_Total(t) 
                       + Industrial_Total(t) + Electronics_Total(t)]

Other_Uses(t) = clip(Other_Uses_Raw(t), 
                     Total_Consumption(t) × 0.08, 
                     Total_Consumption(t) × 0.18)
Other_Uses(t) = rolling_median(Other_Uses, window=5)
```

**7. Force perfect reconciliation:**
```
Total_Calculated(t) = Auto_Total(t) + Construction_Total(t) + Grid_Total(t) 
                      + Industrial_Total(t) + Electronics_Total(t) + Other_Uses(t)

if abs(Total_Calculated(t) - Total_Consumption(t)) > 0.01:  # >0.01% error
    # Proportionally adjust TIER 2 segments only (preserve bottom-up)
    adjustment_factor = (Total_Consumption(t) - Auto_Total(t) - Grid_Generation_OEM(t)) 
                        / (Construction_Total(t) + Grid_TD_Total(t) + Industrial_Total(t) 
                           + Electronics_Total(t) + Other_Uses(t))
    
    Construction_Total(t) *= adjustment_factor
    Grid_TD_Total(t) *= adjustment_factor
    Industrial_Total(t) *= adjustment_factor
    Electronics_Total(t) *= adjustment_factor
    Other_Uses(t) *= adjustment_factor
```

---

### 8.3 Validation Checklist

**✅ Historical Fit:**
- Total matches `Copper_Annual_Consumption_Global(t)` by construction (forced reconciliation)
- **Action:** Document reconciliation adjustments in QA report

**✅ Shares Consistency (Primary Validation):**

| Segment | Calculated Share | Reference Dataset | Tolerance | Priority |
|---------|-----------------|-------------------|-----------|----------|
| **Transportation** | `Auto_Total / Total` | `Copper_Demand_Transportation_Percentage_Global` | ±2% | HIGH |
| **Electrical** | `(Construction+Grid+Industrial) / Total` | `Copper_Electrical_Demand_Percentage_Global` | ±5% | HIGH |
| **EV** | `Auto_BEV_Demand / Total` | `Copper_EV_Demand_Percentage_Global` | ±3% | MEDIUM |
| **Solar** | `Grid_Solar_Demand / Total` | `Copper_Solar_Demand_Percentage_Global` | ±4% | MEDIUM |
| **Wind** | `Grid_Wind_Demand / Total` | `Copper_Wind_Turbines_Percentage_Global` | ±4% | MEDIUM |

**Action:** If any variance exceeds tolerance → flag in QA report, investigate data quality, document as assumption if no resolution.

**✅ Segment Evolution Sanity:**
- **Automotive:** Should rise from ~10-12% → 15-18% of total (driven by EV growth, copper intensity 3-4× ICE)
- **Grid Renewables:** Should rise (energy transition, wind/solar copper-intensive)
- **Construction + Grid:** Stable or rising (electrification, urbanization)
- **Electronics:** Stable ~10-12% (mature market, miniaturization offset by volume)
- **Other Uses:** Declining as % (10-15% → 8-12%, mature/discretionary applications)

**Action:** Plot segment shares over time, flag anomalies (sudden jumps/drops >5 percentage points YoY).

**✅ Internal Consistency:**
- `OEM(t) + Replacement(t) = Segment_Total(t)` for each segment
- `Σ Segment_Total(t) = Total_Consumption(t)` (within 0.1% after reconciliation)
- Non-negativity: All components ≥ 0

**✅ Green Transition Dynamics:**
- EV copper demand growth > overall auto growth (verify: BEV sales growth × 83kg > ICE sales decline × 23kg)
- Wind/Solar copper demand growth > grid average (verify: renewables capacity additions dominate)
- **Action:** Plot "Green Copper Demand" (EV + Solar + Wind) as % of total → should be rising trajectory

**⚠️ Acknowledge Limitations (Transparency Requirements):**
- **Construction, Industrial, Electronics:** Allocated from shares, NOT bottom-up calculations → **MODEL ASSUMPTIONS**
- **Grid T&D:** Residual after generation-linked, NOT directly measured → **DERIVED**
- **Other Uses:** Residual with bounds, NOT directly calculated → **RESIDUAL**
- **Coefficients:** From literature, NOT calibrated to your specific data → **ASSUMPTIONS**
- **OEM/Replacement splits (TIER 2):** Default percentages, NOT from lifecycle tracking → **ASSUMPTIONS**

**Action:** In all outputs, tag each segment with confidence level (HIGH/MEDIUM/LOW) and method (BOTTOM-UP/ALLOCATED/RESIDUAL).

---

## 9) Output Schema (Wide Format, Per Year)

### 9.1 Summary Columns
- `year` (int)
- `total_demand_tonnes` (float)
- `total_oem_demand_tonnes` (float)
- `total_replacement_demand_tonnes` (float)
- `total_other_uses_tonnes` (float)

### 9.2 Segment Columns (OEM, Replacement, Total)
- `auto_oem`, `auto_repl`, `auto_total`
- `construction_oem`, `construction_repl`, `construction_total`
- `grid_oem`, `grid_repl`, `grid_total`
  - `grid_generation_oem` (sub-component, for transparency)
  - `grid_td_oem`, `grid_td_repl` (sub-components)
- `industrial_oem`, `industrial_repl`, `industrial_total`
- `electronics_oem`, `electronics_repl`, `electronics_total`

### 9.3 Reference Columns (Auditability)

**Installed Base (where tracked):**
- `ib_cars_ice_units`, `ib_cars_bev_units`, `ib_cars_phev_units`
- `ib_cvs_ice_units`, `ib_cvs_ev_units`, `ib_cvs_ngv_units`
- `ib_2w_ice_units`, `ib_2w_ev_units`
- `ib_3w_ice_units`, `ib_3w_ev_units`
- `ib_wind_onshore_gw`, `ib_wind_offshore_gw`, `ib_solar_gw`, `ib_gas_gw`, `ib_coal_gw`

**Adds/Sales (direct from datasets):**
- `sales_cars_ice_units`, `sales_cars_bev_units`, `sales_cars_phev_units`
- `sales_cvs_ice_units`, `sales_cvs_ev_units`, `sales_cvs_ngv_units`
- `sales_2w_ice_units`, `sales_2w_ev_units`
- `sales_3w_ice_units`, `sales_3w_ev_units`
- `new_wind_onshore_gw`, `new_wind_offshore_gw`, `new_solar_gw`, `new_gas_gw`, `new_coal_gw`

**Implied Quantities (derived for reference):**
- `implied_new_floorspace_million_sqm` (from Construction_OEM / coefficient)
- `implied_retrofit_floorspace_million_sqm` (from Construction_Replacement / coefficient)
- `implied_new_transmission_km` (from Grid_TD_Total × allocation / coefficient)
- `implied_new_distribution_km` (from Grid_TD_Total × allocation / coefficient)
- `implied_transformer_additions_gw` (from Grid_TD_Total × allocation / coefficient)
- `implied_motor_sales_mw` (from Industrial_OEM / coefficient)

**Parameters Used (for transparency):**
- `coeff_car_bev_kg`, `coeff_car_ice_kg`, `coeff_cv_bev_kg`, etc.
- `coeff_wind_onshore_tonnes_per_mw`, `coeff_wind_offshore_tonnes_per_mw`, `coeff_solar_tonnes_per_mw`
- `split_construction_oem_pct`, `split_grid_td_oem_pct`, `split_industrial_oem_pct`

**Validation Metrics:**
- `share_transport_calculated`, `share_transport_reference`, `share_transport_variance`
- `share_electrical_calculated`, `share_electrical_reference`, `share_electrical_variance`
- `share_ev_calculated`, `share_ev_reference`, `share_ev_variance`
- `share_solar_calculated`, `share_solar_reference`, `share_solar_variance`
- `share_wind_calculated`, `share_wind_reference`, `share_wind_variance`

**Confidence Tags (text):**
- `auto_confidence: "HIGH_BOTTOM_UP"`
- `construction_confidence: "LOW_ALLOCATED"`
- `grid_confidence: "MEDIUM_HYBRID"`
- `industrial_confidence: "LOW_ALLOCATED"`
- `electronics_confidence: "LOW_ALLOCATED"`
- `other_uses_confidence: "LOW_RESIDUAL"`

---

## 10) Configuration File (YAML)

```yaml
horizon:
  start_year: 2020
  end_year: 2045

units:
  demand: tonnes
  stock_vehicles: units
  stock_generation: GW
  # Note: Construction, Industrial stocks are implied, not directly tracked

# ========== TIER 1 COEFFICIENTS (Bottom-Up) ==========
copper_coefficients:
  # Automotive (kg/vehicle) — HIGH CONFIDENCE
  car_ice: 23.0
  car_bev: 83.0
  car_phev: 60.0
  car_hev: 35.0
  cv_ice: 35.0
  cv_ev: 120.0
  cv_ngv: 38.0
  two_wheeler_ice: 3.0
  two_wheeler_ev: 4.0
  three_wheeler_ice: 4.0
  three_wheeler_ev: 5.0

  # Grid Generation (tonnes/MW) — MEDIUM CONFIDENCE
  per_mw_wind_onshore: 6.0      # Range: 4-10
  per_mw_wind_offshore: 10.0    # Range: 8-12
  per_mw_solar_pv: 5.0          # Range: 4-6
  per_mw_gas_ccgt: 1.0          # Range: 0.8-1.2
  per_mw_coal: 1.0              # Range: 0.8-1.2

  # ========== TIER 2 COEFFICIENTS (Reference Only) ==========
  # Construction (kg/sqm) — For implied back-calculation
  sqm_resi_new: 4.0             # Range: 3-5
  sqm_nonresi_new: 6.5          # Range: 5-8
  sqm_resi_reno: 2.0            # Range: 1-3
  sqm_nonresi_reno: 3.0         # Range: 2-4
  sqm_blended_new: 4.5          # Weighted average
  sqm_blended_retrofit: 2.5     # Weighted average

  # Grid T&D (tonnes per unit) — For implied back-calculation
  per_km_transmission: 7.0      # Range: 7-12
  per_km_distribution: 3.5      # Range: 3-5
  per_gw_transformer: 800.0     # Range: 600-1000

  # Industrial (tonnes/MW) — For implied back-calculation
  per_mw_motor: 5.0             # Range: 4-6

  # Electronics (kg/unit) — For implied back-calculation
  per_phone: 0.015              # 15g
  per_pc: 0.8                   # 800g
  per_appliance: 1.5            # 1.5kg blended

# ========== ALLOCATION PARAMETERS (TIER 2) ==========
segment_allocation:
  # Within Electrical segment (shares sum to 100%)
  construction_pct: 0.48        # Construction = 48% of Electrical (range: 45-52%)
  grid_pct: 0.35                # Grid = 35% of Electrical (range: 32-38%)
  industrial_pct: 0.17          # Industrial = 17% of Electrical (range: 15-20%)
  
  # Direct shares of total demand
  electronics_pct: 0.11         # Electronics = 11% of total (range: 10-12%)
  other_uses_target_pct: 0.12   # Other Uses target = 12% (historical 10-15%)

# OEM/Replacement default splits (when cannot calculate from drivers)
oem_replacement_defaults:
  construction_oem_pct: 0.65    # 65% OEM, 35% Replacement (range: 60-70%)
  grid_td_oem_pct: 0.70         # 70% OEM, 30% Replacement (range: 65-75%)
  industrial_oem_pct: 0.60      # 60% OEM, 40% Replacement (range: 55-65%)

# ========== LIFESPANS ==========
lifespans_component_repl_years:
  grid_refurb_cycle: 40.0
  construction_retrofit_cycle: 25.0
  industrial_motor: 18.0
  transformer: 45.0

lifespans_asset_scrappage_years:
  passenger_car: 18.0
  commercial_vehicle: 20.0
  two_wheeler: 12.0
  three_wheeler: 10.0
  building_shell: 70.0

# ========== GROWTH PROXIES (Forward Forecasting) ==========
growth_proxies:
  construction_electricity_elasticity: 0.7   # Construction grows at 70% of elec growth
  industrial_electricity_elasticity: 0.8     # Industrial grows at 80% of elec growth
  electronics_annual_growth: 0.025           # 2.5% per year (stable)
  other_uses_annual_growth: 0.015            # 1.5% per year (slow)
  other_uses_price_elasticity: -0.15         # Price sensitivity for Other Uses

# ========== VALIDATION & RECONCILIATION ==========
validation:
  use_segment_shares: true                   # Primary validation method
  force_reconciliation: true                 # Always match total consumption exactly
  
  # Tolerance thresholds (% deviation allowed)
  share_tolerance_transportation: 0.02       # ±2%
  share_tolerance_electrical: 0.05           # ±5%
  share_tolerance_ev: 0.03                   # ±3%
  share_tolerance_renewables: 0.04           # ±4%
  
  # Other Uses bounds
  other_uses_min_pct: 0.08                   # Min 8% of total
  other_uses_max_pct: 0.18                   # Max 18% of total

# ========== DATA QUALITY CONTROLS ==========
smoothing:
  rolling_median_years: 3                    # Apply to bottom-up flows
  rolling_median_years_allocated: 5          # Apply to allocated/residual segments

guards:
  non_negative: true                         # Clamp all outputs ≥ 0
  max_yoy_growth_pct: 50.0                   # Flag if any segment grows >50% YoY
  max_yoy_decline_pct: -30.0                 # Flag if any segment declines >30% YoY

# ========== GRID T&D SUB-ALLOCATION (For Implied Calculation) ==========
grid_td_suballocation:
  transmission_pct: 0.60                     # Transmission = 60% of Grid T&D
  distribution_pct: 0.40                     # Distribution = 40% of Grid T&D
  transformer_pct: 0.20                      # Transformers = 20% of Grid T&D total

# ========== ELECTRONICS SUB-ALLOCATION (For Implied Calculation) ==========
electronics_suballocation:
  phones_pct: 0.40                           # Phones = 40% of Electronics demand
  pcs_pct: 0.30                              # PCs = 30% of Electronics demand
  appliances_pct: 0.30                       # Appliances = 30% of Electronics demand

# ========== CALCULATION STRATEGY FLAGS ==========
calculation_strategy:
  automotive_method: "bottom_up_full"        # Full IB accounting
  grid_generation_method: "bottom_up_partial" # Derive new from installed capacity
  grid_td_method: "residual_allocation"      # Top-down residual
  construction_method: "share_allocation"    # Top-down from Electrical share
  industrial_method: "share_allocation"      # Top-down from Electrical share
  electronics_method: "fixed_share"          # Fixed % of total
  other_uses_method: "residual_bounded"      # Residual with bounds & smoothing
  
  automotive_repl_method: "zero_captured_in_oem"
  electronics_repl_method: "zero_captured_in_oem"
```

---

## 11) Implementation Blueprint (Pseudocode)

See full pseudocode in original document section 11. Key steps:

1. **Initialize:** Load config, datasets, set up IB tracking structures
2. **Main loop (each year):**
   - Calculate TIER 1 bottom-up: Automotive (sales × coefficients), Grid Generation (new capacity × coefficients)
   - Load segment shares and validate TIER 1 results
   - Allocate TIER 2 top-down: Construction, Industrial, Electronics from Electrical share
   - Calculate Other Uses as bounded residual
   - Force reconciliation to match total consumption
3. **Post-processing:** Apply smoothing, growth guards, calculate aggregates
4. **Export:** CSV/Parquet with all output schema columns

---

## 12) Calibration, QA & Transparency

### 12.1 Back-Cast Validation

1. **Historical Fit:** Total matches consumption data by construction
2. **Segment Share Alignment:** Compare calculated vs. reference shares (Transportation, Electrical, EV, Renewables)
3. **Coefficient Implied Validation:** Back-calculate implied coefficients from bottom-up segments, compare to literature
4. **Trend Consistency:** Check segment growth aligns with driver growth

### 12.2 Segment Share Validation (Primary QA Method)

| Segment | Test | Tolerance | Action if Fail |
|---------|------|-----------|----------------|
| Transportation | Auto/Total vs. Share_Transport | ±2% | Investigate vehicle data or coefficients |
| Electrical | (Const+Grid+Ind)/Total vs. Share_Electrical | ±5% | Rebalance split factors |
| EV | Auto_BEV/Total vs. Share_EV | ±3% | Check BEV sales or coefficient |
| Renewables | (Solar+Wind)/Total vs. (Share_Solar+Share_Wind) | ±4% | Check capacity data |

### 12.3 Segment Evolution Sanity Checks

- **Auto:** Rising share (EV effect), ~11% → 15-18%
- **Grid:** Rising (renewables, electrification), ~12-15% → 18-22%
- **Construction:** Stable, ~20-25%
- **Industrial:** Stable, ~8-10%
- **Electronics:** Stable/slight decline, ~11-12% → 10-11%
- **Other Uses:** Declining, ~12-14% → 8-10%

### 12.4 Stress Testing & Sensitivity Analysis

- **Allocation splits:** ±10% on construction/grid/industrial percentages
- **Coefficients:** ±20% on automotive and grid generation
- **OEM/Replacement splits:** ±10 pp on construction/grid/industrial
- **EV adoption scenarios:** ±20% BEV sales
- **Renewables buildout:** ±25% wind/solar capacity

### 12.5 Transparency Documentation Requirements

**All outputs MUST include:**
1. Confidence level tags (HIGH/MEDIUM/LOW) for every segment
2. Assumption register with all parameters, sources, ranges
3. Data provenance for every input dataset
4. Validation results summary (share alignments, pass/fail)
5. Known limitations section (what's allocated vs. bottom-up)
6. Reconciliation audit trail (adjustments applied)

### 12.6 Evidence Register

Structured log of:
- Coefficient sources (ICA, NREL, IRENA, etc.)
- Allocation parameter justifications
- Data gaps and workarounds
- All assumptions flagged

---

## 13) Special Considerations (Copper-Specific)

### 13.1 Green Transition Dominance

- **EVs:** 3-4× copper intensity vs. ICE → major demand driver
- **Renewables:** Wind/Solar 5-10× copper intensity vs. fossil fuels
- **Grid upgrades:** Electrification requires reinforcement
- **Implication:** Prioritize fidelity in EV and renewables modeling

### 13.2 Substitution Risk

- **Aluminum:** Competes in cables, transformers, automotive wiring
- **Economic threshold:** Viable when Price_Cu/Price_Al > ~3.5
- **Model approach:** Time-varying coefficients `k(t)` or scenario with -10 to -20% reduction

### 13.3 Thrifting (Design Optimization)

- **Trend:** ~0.5-1.0% annual decline in copper per unit function
- **Drivers:** Miniaturization, higher voltages, efficiency improvements
- **Model approach:** Apply -0.7% annual drift to coefficients (scenario)

### 13.4 Regionalization

- Copper intensity varies by region (China higher for construction/grid, Europe higher for vehicles)
- For regional forecasts, adjust coefficients ±10-20% per region

### 13.5 Circularity & Recycling

- Recycling rate ~30-35% currently, rising to ~35-38% by 2045
- Model forecasts CONSUMPTION (refined); use recycling rate to estimate PRIMARY demand

---

## 14) Forward Forecasting Beyond Historical Data

### 14.1 Automotive
- Continue IB accounting if sales forecasts available
- Otherwise use S-curve for EV adoption

### 14.2 Grid Generation
- Use capacity forecasts from IEA/BNEF if available
- Otherwise extrapolate growth rates (+8-12% wind, +10-15% solar)

### 14.3 Construction, Industrial, Electronics
- Continue share allocation or link to economic growth (electricity production as proxy)

### 14.4 Other Uses
- Residual with declining share assumption (-0.5% annually)

### 14.5 Scenario Development
- **Baseline:** 70-80% EV, 15 TW renewables by 2045
- **Accelerated:** 90%+ EV, 20+ TW renewables (+20-30% demand)
- **Delayed:** 50-60% EV, 10-12 TW renewables (-15-20% demand)
- **Substitution/Thrifting:** Base transition but -15% grid/construction coefficients, -0.7% annual drift

---

## 15) Deliverables Checklist

### 15.1 Core Outputs
- [ ] CSV/Parquet file with all output schema columns
- [ ] Config YAML with all parameters
- [ ] QA Report with validation results, sensitivities, limitations
- [ ] Evidence Register with sources, assumptions, data gaps

### 15.2 Visualizations
- [ ] Total demand stacked area (by segment, color-coded by confidence)
- [ ] Segment shares evolution (stacked %)
- [ ] OEM vs. Replacement breakdown
- [ ] Validation: Calculated vs. Reference shares
- [ ] Green Copper Demand (EV+Solar+Wind) trajectory
- [ ] Scenario comparison fan chart

### 15.3 Documentation
- [ ] README with overview, data requirements, how to run
- [ ] Methodology Appendix with formulas, fallback logic
- [ ] Scenario Pack with Baseline + alternatives

---

## 16) Review Checklist (Pre-Delivery)

**Verify:**
- [ ] No negative values
- [ ] No missing values
- [ ] Growth rate guards applied
- [ ] Smoothing applied to allocated segments
- [ ] Other Uses bounded 8-18%
- [ ] Reconciliation perfect (±0.1%)
- [ ] All validation tests run
- [ ] Confidence tags on all segments
- [ ] All coefficients documented
- [ ] Known limitations stated
- [ ] Reproducible (config + code provided)

---

## 17) Maintenance & Updates

### 17.1 Quarterly (Data Refresh)
- Update latest actuals, re-run validation

### 17.2 Annually (Coefficient Review)
- Review literature, check for BEV/wind/solar coefficient updates

### 17.3 Bi-Annually (Methodology Review)
- Re-assess allocation factors, check if new data sources available

### 17.4 Ad-Hoc (Scenario Updates)
- When new transition scenarios published, policy changes, price thresholds reached

### 17.5 Model Evolution Path
1. **Priority 1:** Add construction floorspace data (transition to bottom-up)
2. **Priority 2:** Add grid T&D infrastructure data
3. **Priority 3:** Add industrial motor sales
4. **Priority 4:** Add electronics device sales

---

## Appendix A: Quick Start Guide

1. Load data (consumption, vehicle sales/fleet, generation capacity, segment shares)
2. Set parameters (copy config YAML, adjust if needed)
3. Run model (loop through years per pseudocode)
4. Validate (check share alignment, plot trends)
5. Document (tag confidence, record assumptions, list gaps)
6. Deliver (export CSV, provide config + QA report)

---

## Appendix B: Glossary

- **Bottom-Up:** Demand from drivers × coefficients
- **Top-Down:** Demand allocated from shares
- **OEM:** Copper for NEW assets
- **Replacement:** Copper for refurbishment of EXISTING assets
- **Installed Base (IB):** Stock of assets in operation
- **Coefficient:** Copper intensity per unit
- **Segment Share:** % of total demand from end-use
- **Allocation Factor:** % to split parent into sub-segments
- **Residual:** Demand as remainder after other segments
- **Reconciliation:** Adjust to match known total
- **Validation:** Compare calculated vs. reference shares
- **Confidence Level:** HIGH (bottom-up), MEDIUM (partial), LOW (allocated)
- **Thrifting:** Copper reduction via design optimization
- **Substitution:** Replacement with aluminum
- **Green Copper:** EV + Solar + Wind + Grid upgrades

---

## Appendix C: Contact & Support

- Document version: 1.0 (Hybrid Bottom-Up + Top-Down Framework)
- Last updated: 2024-Q4
- For questions/issues, reference section numbers
- Report data quality problems in Evidence Register
- Report validation failures in QA Report

---

**END OF DOCUMENT**

