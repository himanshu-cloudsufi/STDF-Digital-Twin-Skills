# Cost-Driven SWB (Solar–Wind–Battery) Analysis — Updated Version v4

## Scope
- Treat each **region** (≠ Global) independently; compute regional results first.
- If you need **Global**, aggregate (China + USA + Europe + Rest_of_World) carefully (avoid double counting).
  - Note: "RoW" and "Rest_of_World" are equivalent terms used interchangeably in this document.
- Define **Tipping Point = Cost Parity Year** for **electricity**: LCOE/SCOE of SWB stack ≤ LCOE of incumbent (coal or gas) in real terms.

---

## 1️⃣ Determine Cost Parity (Tipping Point)
**Compare Cost Curves (real terms)**
- Disruptor costs:
  - **Solar PV LCOE** (utility-scale)
  - **Onshore Wind LCOE**
  - **Offshore Wind LCOE** (optional / region-specific)
  - **Battery Storage System Cost** ($/kWh installed) + **levelized storage cost** (SCOE)
- Incumbent costs:
  - **Coal LCOE** (include fuel, variable O&M, fixed O&M, carbon costs if applicable)
  - **Gas CCGT LCOE** (or regional marginal cost where used)

**Battery SCOE Calculation**
- If not provided directly, calculate SCOE (Storage Cost of Energy) as:
  ```
  SCOE ($/MWh) = [Battery_Capex ($/kWh) × 1000] / [Total_Cycles × Duration (h) × RTE] + Fixed_OM_Annual
  ```
  Where:
  - **Battery_Capex**: Use regional `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<Region>` (default)
  - **Total_Cycles**: Battery cycle life (default: 5000 cycles)
  - **Duration**: Storage discharge duration in hours (default: 4 hours)
  - **RTE**: Round-trip efficiency (default: 0.88 or 88%)
  - **Fixed_OM_Annual**: Annual fixed O&M cost ($/kWh-year, default: $5/kWh-year, amortize over annual throughput)

**SWB Stack Cost Calculation**
- For tipping point comparison, define SWB stack cost as:
  - **Option A (Conservative):** `SWB_stack_cost = MAX(Solar_LCOE, Onshore_Wind_LCOE) + SCOE`
    - Represents worst-case intermittent generation plus storage cost
  - **Option B (Weighted Average):** `SWB_stack_cost = (Solar_LCOE × w_s + Wind_LCOE × w_w + SCOE × w_b)`
    - Where weights (w_s, w_w, w_b) sum to 1.0 and reflect regional capacity mix
    - Typical weights: Solar=0.4, Wind=0.4, Battery=0.2
  - **Recommended:** Use Option A for conservative tipping point estimates

**Deriving Incumbent LCOE (if not available in datasets)**
- If Coal_LCOE or Gas_LCOE datasets are missing, use fallback approach:
  - **Coal LCOE baseline**: $60-80/MWh (2020 real USD)
  - **Gas LCOE baseline**: $50-70/MWh (2020 real USD)
  - Apply **regional multipliers**: China (0.8×), USA (1.0×), Europe (1.2×), Rest_of_World (0.9×)
  - Assume **flat or slowly declining** costs over time (0-1% decline per year)
  - Adjust for carbon pricing if applicable: add $20-50/MWh for coal, $10-25/MWh for gas

**Forecasting Cost Curves**
1. Transform each historical cost series with `log(cost)`.
2. Compute long-run CAGR on the log series.
3. Forecast forward (to end_year, default 2040) using the log-CAGR.
4. Exponentiate back to level terms and stitch (historical + forecast).
5. Smooth with a **3-year rolling median** before intersection checks.

**Intersection / Tipping Logic**
- If `SWB_stack_cost(t) ≤ incumbent_cost(t)` → **tipping = first such year**.
- If SWB is always cheaper across history → **tipping = first historical year**.
- If never cheaper by end_year → **tipping = None** (fallback to slow adoption).

---

## 2️⃣ Forecast Electricity Demand & Residual Load
**Dataset Selection**
- Start from regional electricity demand using available datasets:
  - **Primary (recommended)**: `Electricity_Annual_Production_<Region>` (generation-based, supply-side view)
  - **Alternative**: `Electricity_Annual_Domestic_Consumption_<Region>` (consumption-based, demand-side view)
  - Use **Production** for supply-side displacement analysis (aligns with generation data)
  - Note: Production typically includes exports; Consumption includes imports

**Default Forecasting Logic**
- a. Calculate year-on-year rate of change for each year
- b. Take average of historical rates to calculate long-term growth rate
- c. Use the calculated long-term growth rate to forecast forward (to end_year, default 2040)

**Peak Load Proxy**
- Produce **peak load** proxy if hourly data is missing:
  - `Peak Load (GW) = Annual Demand (TWh) × 1000 / 8760 × Load Factor`
  - Use regional Load Factor defaults: **1.3–1.5** (higher for regions with greater demand variability)
  - Units check: TWh × 1000 = GWh; GWh / 8760 hours = average GW; × Load Factor = peak GW

---

## 3️⃣ Capacity and Generation Relationship
**Capacity Factors Linkage**
- Generation and capacity are linked via regional capacity factors:
  - `Solar_Generation (GWh) = Solar_Capacity (GW) × CF_solar × 8760`
  - `Wind_Generation (GWh) = Wind_Capacity (GW) × CF_wind × 8760`
- Use **regional CF trajectories** (historical + modest improvement, ≤0.3 percentage points/yr).

**Regional Capacity Factor Fallback Strategy**
- When regional CF data unavailable, use the following fallback order:
  1. **First**: Use regional-specific CF from dataset (if available)
  2. **Second**: Use Global CF from dataset (if regional missing)
  3. **Third**: Use default values from table below (if no dataset available)

**Default Capacity Factors (when data unavailable)**

| Technology      | China | USA  | Europe | Rest_of_World | Global |
|-----------------|-------|------|--------|---------------|--------|
| Solar PV        | 0.17  | 0.18 | 0.12   | 0.16          | 0.15   |
| Onshore Wind    | 0.24  | 0.35 | 0.22   | 0.28          | 0.27   |
| Offshore Wind   | 0.42  | 0.40 | 0.45   | 0.42          | 0.43   |
| Coal (base)     | 0.55  | 0.50 | 0.45   | 0.50          | 0.50   |
| Gas (peaking)   | 0.40  | 0.45 | 0.35   | 0.40          | 0.40   |

**Forecasting Approach**
- Forecast **either** capacity OR generation using YoY growth averaging (Section 4).
- Derive the other using the capacity factor relationship above.
- **Recommendation**: Forecast **capacity** (as it's more commonly reported), then derive generation.

---

## 4️⃣ SWB Capacity & Generation Forecasting
**Forecasting Method**
- Calculate year-on-year growth rate for each historical year.
- Take average of historical growth rates to calculate long-term growth rate.
- Use the calculated long-term growth rate to forecast forward (to end_year, default 2040).
- Apply to each SWB component:
  - **Solar PV**: Forecast capacity (GW), derive generation using CF
  - **Onshore Wind**: Forecast capacity (GW), derive generation using CF  
  - **Offshore Wind**: Forecast capacity (GW) if applicable, derive generation using CF
  - **Battery**: Forecast energy capacity (GWh) directly from historical trends

**Handling Wind Generation Data**
- **If separate Onshore/Offshore generation unavailable**, derive from capacity:
  - `Onshore_Generation (GWh) = Onshore_Capacity (GW) × CF_onshore × 8760`
  - `Offshore_Generation (GWh) = Offshore_Capacity (GW) × CF_offshore × 8760`
  - Use capacity datasets: `Onshore_Wind_Installed_Capacity_<Region>` and `Offshore_Wind_Installed_Capacity_<Region>`
- **Wind_Mix datasets** (entity: Wind_Mix):
  - `Wind_Annual_Power_Generation_<Region>` represents **combined** onshore + offshore wind
  - Use for validation: verify that `Onshore_Gen + Offshore_Gen ≈ Wind_Mix_Gen`
  - If Wind_Mix is primary source and breakdown unavailable, allocate by capacity share

**CSP (Concentrated Solar Power) Treatment**
- **Optional / region-specific component**
- Include CSP in SWB stack only if:
  - Significant capacity exists (>1% of total solar capacity in region), OR
  - Region-specific analysis requires it (e.g., Spain, Morocco, southwestern USA)
- **Otherwise**: Treat CSP as negligible and exclude from main SWB stack
- **Note**: CSP has built-in thermal storage capability, treat differently from Solar PV + Battery combination

---

## 5️⃣ Battery Storage Sizing
**Battery Cost Dataset Selection**
- **Default**: Use `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<Region>`
- **Rationale**: 4-hour duration aligns with grid-scale typical range (2-8 hours)
- **Fallback**: If 4-hour data unavailable, use 2-hour cost as proxy (adjust for duration difference if needed)

**Simple Storage Sizing Approach**
- **Energy Capacity (GWh)**: 
  - **Option A**: `Energy_Capacity = k_days × Peak_Load (GW) × 24` (resilience-days heuristic, k_days = 1-4)
  - **Option B**: Use forecasted battery capacity from historical trends (Section 4)
  - **Recommended**: Use Option B where historical data available; Option A for new regions
- **Power Capacity (GW)**:
  - `Power_Capacity = Energy_Capacity (GWh) / Duration (hours)`
  - Typical duration: **2–8 hours** for grid-scale batteries
  - Default: **4 hours** (aligns with cost datasets)
- **Battery Throughput (annual)**:
  - `Throughput (TWh) = Energy_Capacity (GWh) × cycles_per_year / 1000`
  - Default cycles: **200-300/year** for daily cycling
  - Validate: `cycles_per_year = Throughput (TWh) × 1000 / Energy_Capacity (GWh)`

---

## 6️⃣ Incumbent Displacement & Sequencing
**Calculate Residual Generation**
- **Total Non-SWB Supply** = Nuclear + Hydro + Other legacy renewables
- **Handling missing Nuclear/Hydro data**:
  - If datasets unavailable, derive indirectly:
    ```
    Non_SWB_Supply = Total_Production − Coal_Gen − Gas_Gen − Solar_Gen − Wind_Gen − Battery_Discharge
    ```
  - Use **earliest available year** to establish Non-SWB baseline
  - **Assumption**: Hold Non-SWB supply constant or apply slow decline (0-2% per year for nuclear retirements)
  - Document baseline year and assumptions clearly in outputs

- **Residual for Coal/Gas** = `max(Total_Demand − SWB_Generation − Non_SWB_Fixed, 0)`

**Displacement Sequencing**
- **Sequence A (Coal-first)**: Reduce coal generation until floor (e.g., minimum reserve), then reduce gas
  - Use for regions with high coal emissions targets (e.g., China, Europe)
- **Sequence B (Gas-first)**: Reduce gas generation first (if marginal cost high), then coal
  - Use for regions with abundant gas or coal baseload commitments (e.g., USA in some states)
- Provide a **switch** and **regional defaults**:
  - **Default**: China, Europe → Coal-first; USA → Gas-first; Rest_of_World → Coal-first
  - Document assumptions clearly in outputs

**Allocation Logic**
- If `Residual > Coal_Floor + Gas_Floor`: Allocate based on sequence priority
- If `Residual < Coal_Floor + Gas_Floor`: Both incumbents hit minimum reserves
- Ensure `Coal_Gen ≥ 0` and `Gas_Gen ≥ 0` (no negative generation)
- **Minimum reserve floors**: Coal = 10% of peak historical capacity; Gas = 15% of peak historical capacity (flexible peaking reserve)

---

## 7️⃣ Numerical Stability & Guards
- Clamp shares ∈ [0, 1], capacities ≥ 0, generation ≥ 0.
- Ensure energy balance: `SWB_Gen + Incumbents_Gen + Other_Gen ≈ Total_Demand` (within ±2% tolerance)
- Smooth year-to-year capacity additions using 3-yr rolling average if spikes occur.
- Validate battery consistency: `Battery_Energy (GWh) ≥ Battery_Throughput (TWh) × 1000 / cycles_per_year`
- Check capacity factors stay within reasonable bounds: CF ∈ [0.05, 0.70] for renewables

---

## 8️⃣ Expected Outputs (per Region)
1. **Cost Data (historical + forecast)**
   - Solar PV LCOE, Onshore Wind LCOE, Offshore Wind LCOE (if applicable), CSP LCOE (if applicable)
   - Battery system $/kWh (capital cost) and **SCOE** (levelized cost)
   - Coal & Gas LCOE (or marginal cost), in **real USD/MWh**
   - **Tipping Point year(s)**: vs coal, vs gas (report separately)
   - Document data sources and any fallback methods used

2. **Demand & Generation (historical + forecast)**
   - Electricity demand/production (TWh), peak load proxy (GW)
   - SWB generation by source: Solar PV, Onshore Wind, Offshore Wind, CSP (if applicable)
   - SWB total share of generation (%)
   - Incumbent generation: Coal (TWh), Gas (TWh) after displacement sequence
   - Non-SWB fixed supply: Nuclear, Hydro, Other (TWh)

3. **Installed Capacity (historical + forecast)**
   - Solar PV, Onshore Wind, Offshore Wind, CSP (if applicable) — all in **GW**
   - Battery storage: **energy capacity (GWh)** and **power capacity (GW)**
   - Optional: Non-SWB legacy capacities (nuclear, hydro) — in **GW**

4. **Battery Storage Metrics**
   - Battery throughput (TWh/year)
   - Battery utilization (cycles/year)
   - Storage duration (hours)
   - Round-trip efficiency used (%)

5. **Emissions (optional but recommended)**
   - CO₂ emissions from coal generation (Mt CO₂/year)
   - CO₂ emissions from gas generation (Mt CO₂/year)
   - Total fossil emissions trajectory
   - If emission factors provided: Coal ≈ 0.9-1.0 t CO₂/MWh; Gas ≈ 0.4-0.5 t CO₂/MWh

6. **Global Aggregates**
   - Regional tables + aggregated global generation, capacities, and emissions
   - Verify: Global = China + USA + Europe + Rest_of_World (no double counting)

---

## 9️⃣ Recommended Defaults

**General Parameters**
- Forecast horizon: **2040** (adjustable to 2050 if long-term scenarios required)
- Rolling-median smoothing window: **3 years** (for cost curves)
- Energy balance tolerance: **±2%** (for generation vs demand)

**Peak Load & Demand**
- Peak Load Factor: **1.3–1.5** (region-specific, higher for greater demand variability)
  - China: 1.4, USA: 1.5, Europe: 1.3, Rest_of_World: 1.4

**Capacity Factors** (see table in Section 3 for defaults)
- Apply **modest improvement** over forecast period: ≤0.3 percentage points per year
- Solar PV: technology improvements in tracking, bifacial modules
- Wind: larger turbines, taller towers, better siting

**Battery Storage**
- Storage duration: **2–8 hours** (grid-scale typical), default **4 hours**
- Battery cycle life: **5000 cycles** (typical for Li-ion grid storage)
- Battery cycles per year: **250** (daily cycling assumption, ~0.7 cycles/day average)
- Storage round-trip efficiency: **0.88** (88%, configurable: 0.85–0.92 range)
- Storage resilience days (k_days): **2 days** (if using heuristic sizing, Option A)
- Fixed O&M: **$5/kWh-year** (for SCOE calculation)

**Incumbent Displacement**
- Coal minimum reserve floor: **10%** of peak historical capacity
- Gas minimum reserve floor: **15%** of peak historical capacity
- Nuclear/Hydro decline rate: **0-2%** per year (if data unavailable, assume 0%)
- Default displacement sequence:
  - China: Coal-first
  - USA: Gas-first
  - Europe: Coal-first
  - Rest_of_World: Coal-first

**Fallback LCOE Values** (real 2020 USD, if datasets unavailable)
- Coal LCOE: $70/MWh × regional multiplier
- Gas LCOE: $60/MWh × regional multiplier
- Regional multipliers: China (0.8), USA (1.0), Europe (1.2), Rest_of_World (0.9)

---

## 🔟 Data Mapping & Fallback Summary

**Critical Datasets Required**
1. **Generation/Demand**: `Electricity_Annual_Production_<Region>` (primary)
2. **SWB Capacity**: Solar, Onshore Wind, Offshore Wind installed capacity by region
3. **SWB Costs**: Solar LCOE, Wind LCOE, Battery $/kWh by region (or Global as fallback)
4. **Incumbent Generation**: Coal and Gas generation by region (for displacement)

**Datasets with Fallbacks Available**
- **Capacity Factors**: Use Global if regional missing; use defaults (Section 3 table) if neither available
- **Incumbent LCOE**: Use fallback values (Section 9) if datasets missing
- **Nuclear/Hydro**: Derive from residual generation if datasets missing

**Optional Datasets**
- CSP capacity and LCOE (include only if significant)
- Offshore wind (include only if applicable to region)
- Capacity factors for coal/gas (use defaults if missing)
- Emission factors (use literature values if missing)

---

## Example Flow Summary
1. Select region (e.g., **China**).
2. Load datasets: Production, SWB capacities, costs; apply fallbacks where needed.
3. Forecast Solar/Wind LCOE and battery costs via **log-CAGR** (Section 1).
4. Calculate **SCOE** using formula; derive **SWB stack cost** (Section 1).
5. Compute tipping points vs coal & gas; identify cost parity year(s).
6. Forecast electricity demand/production and peak load proxy via **YoY growth averaging** (Section 2).
7. Forecast SWB capacity and generation via **YoY growth averaging** (Section 4).
8. Derive generation from capacity (or vice versa) using regional **capacity factors** (Section 3).
9. Establish Non-SWB baseline (nuclear, hydro) from residual if needed (Section 6).
10. Calculate incumbent displacement via sequencing (Section 6); size **battery storage** (Section 5).
11. Validate energy balance and numerical stability (Section 7).
12. Export outputs (Section 8): costs, generation, capacities, tipping points, emissions.


