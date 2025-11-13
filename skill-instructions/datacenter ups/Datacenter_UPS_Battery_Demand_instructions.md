# Cost‑Driven Datacenter UPS Battery Analysis — VRLA → Li‑ion (v1)

## Scope
- Treat each **region** (≠ Global) independently; compute regional results first.
- If you need **Global**, aggregate (China + USA + Europe + Rest_of_World) carefully (avoid double counting).
- Define **Tipping Point = Economic Cost Parity Year** where Li‑ion **TCO** ≤ VRLA **TCO** in real terms.
- Time step = **annual**; horizon = **10–15y** (extendable to 2040/2050).
- Primary unit = **MWh installed per year** (flows). Stock = **MWh installed base**. $ basis = **real USD (base‑year indexed)**.

---

## 0️⃣.1️⃣ Dataset Interpretation & Constraints

**Understanding available data**
- **"Annual capacity demand"** datasets = annual NEW installations (flows, MWh/year), not cumulative stock.
- **Total market demand** (Datacenter_UPS level) = VRLA demand + Li-ion demand (use as validation target).
- **Growth projections** = fractional annual rates (e.g., 0.077 = 7.7%) applied to total market size.
- **Installed base** datasets = cumulative stock (MWh) at year-end.

**Key workflow constraint**
- Total_Demand(t) datasets are **validation targets** only; reconcile sum of VRLA + Li-ion forecasts against these.
- Do NOT use total demand as an input constraint that forces adjustments.

---

## 1️⃣ Determine Cost Parity (Tipping Point)
**Compare cost stacks in real terms**

**✅ COST DATA AVAILABLE**
- **Li-ion CapEx proxy**: Use `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>` datasets.
  - These are turnkey costs ($/kWh) including battery + PCS + installation.
  - Treat as **CapEx_Li(t)** in TCO calculations.
  - Note: Grid-scale BESS costs used as proxy for UPS battery costs (directionally consistent; see Section 1.1).

- **VRLA CapEx**: Use `VRLA_Battery_Cost_Global` dataset (flat trajectory ~$220/kWh).
  - Apply regional multipliers if needed: China 0.9×, Europe 1.15×, USA/RoW 1.0×.
  - Alternative: Source from VRLA battery vendor quotes or industry reports if available.

- **OpEx separation**: Turnkey costs do NOT include ongoing OpEx.
  - Use defaults from Section 9: VRLA $18/kWh-yr; Li-ion $6/kWh-yr.
  - These cover maintenance, monitoring, cooling, footprint costs.

- Technology cost stacks:
  - **VRLA TCO**(t) = CapEx_VRLA(t) + PV[OpEx_VRLA(t..t+15)] + Replacement_Costs_VRLA(yrs ~5,10)
  - **Li‑ion TCO**(t) = CapEx_Li(t)   + PV[OpEx_Li(t..t+15)]   + Replacement_Costs_Li (≈ 0 within 15y)
- **CapEx pathing** (per kWh installed):
  - VRLA: flat / slight decline.
  - Li‑ion: declining (use **log‑CAGR** or **learning rate**; see Defaults).
- **OpEx components** (annual, per kWh installed):
  - Maintenance/monitoring/testing; cooling; space/footprint.
- **Discount rate r**: default 8% (configurable 6–10%).

**Economic driver**
- Cost_Advantage(t) = TCO_VRLA(t) − TCO_Li(t)  (positive ⇒ Li‑ion wins)
- **Tipping (economic)** = first year where Cost_Advantage(t) ≥ 0 **and** remains ≥ 0 for ≥ 3 consecutive years (guard against one‑off noise).

**Cost curve forecasting protocol**
- Transform **cost series** with log(cost);
- Compute long‑run CAGR on log series;
- Forecast log forward (to end_year);
- Exponentiate back; stitch (hist + forecast);
- Apply **3‑yr rolling median** smoothing before use.

### 1.1 Cost Data Adaptation for UPS Application

**Using BESS cost curves for UPS batteries**
- Available: Grid-scale Battery Energy Storage System (BESS) turnkey costs
- Application: Datacenter UPS batteries (similar Li-ion chemistry, different use case)

**Adjustments to consider**:
1. **Duration**: BESS costs are for 4-hour systems; UPS default = 4h → direct mapping valid
2. **Cycle life**: UPS batteries cycle less frequently (backup only) vs grid BESS (daily cycling)
   - Effect: UPS batteries may last longer (favorable for Li-ion)
   - Cost impact: Minimal on CapEx, affects replacement frequency (already in model via Life_Li)
3. **Reliability premium**: UPS requires higher reliability → may add 5-10% to costs
   - Optional adjustment: multiply BESS costs by 1.05-1.10 for UPS premium
4. **Regional alignment**: Use region-specific BESS costs for regional UPS analysis

**Default approach** (conservative):
- Use BESS 4-hour turnkey costs **as-is** for Li-ion CapEx
- Accept that directional trends (declining Li-ion, flat VRLA) matter more than absolute levels for tipping point identification
- Sensitivity test: vary costs ±10% to assess tipping year range

---

## 2️⃣ Market Decomposition (Identity)
**Total_Demand(t) = New_Build_Demand(t) + Replacement_Demand(t)**
- **New builds**: batteries required by newly constructed DCs in year t.
- **Replacements**: batteries required to replace end‑of‑life systems in installed base.

**Validation**: Total market demand datasets (Datacenter_UPS level) serve as validation targets. After forecasting, verify: VRLA_Demand(t) + Li_Demand(t) ≈ Total_Market_Demand(t) within ±5%.

---

## 3️⃣ Installed‑Base Accounting & Lifetimes
Maintain technology stocks and retirements (per region):
- IB_VRLA(t+1) = IB_VRLA(t) + Adds_VRLA(t) − Retire_VRLA(t)
- IB_Li(t+1)   = IB_Li(t)   + Adds_Li(t)   − Retire_Li(t)
- Retire_VRLA(t) ≈ IB_VRLA(t) / Life_VRLA (default 5y)
- Retire_Li(t)   ≈ IB_Li(t)   / Life_Li   (default 12y)
- **Contestable market** (VRLA at EoL): Contestable(t) ≈ IB_VRLA(t) / Life_VRLA

**Regional parameter inheritance**
- Use **Global-level parameters** (replacement cycles, lithium content) for all regions unless regional-specific values exist in datasets.
- Dataset `Li_ion_UPS_Replacement_cycle_Global` provides Life_Li = 12y (use for all regions).
- Dataset `Lead_acid_batteries_UPS_Datacenter_Replacement_cycle_Battery_Replacement_cycle_Global` provides Life_VRLA (use for all regions).
- If Li-ion installed base missing for t=start_year, initialize **IB_Li(start_year) = 0** (conservative assumption).

Guardrails
- Keep stocks, flows ≥ 0; reconcile mass balance to ±0.1%.

---

## 4️⃣ Adoption Split (S‑Curve linked to Economics)
**Logistic share of Li‑ion**
- M(t) = L / (1 + exp(−k * (t − t0)))
  - L ∈ [0.90, 0.99] (ceiling; residual VRLA niche)
  - t0 = midpoint (M = L/2)
  - k  = steepness

**Link steepness to economics**
- k(t) = k0 + s * Cost_Advantage(t)
  - k0: base adoption (non‑price advantages: density, thermal tolerance, reliability)
  - s : sensitivity to $ advantage (units: 1 / USD)

**Split logic each year**
- New‑build Li‑ion fraction = M(t); VRLA = 1 − M(t)
- Replacement (contestable VRLA) Li‑ion retrofits = M(t) * Contestable(t)
- VRLA‑for‑VRLA = (1 − M(t)) * Contestable(t)
- Update IB via Section 3.

**Data requirements for calibration**
- Historical shares can be **derived** from demand data: Li_share(t) = Li_demand(t) / (VRLA_demand(t) + Li_demand(t))
- Use datasets: `Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_<region>` and `Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_<region>`
- **If historical span < 5 years**: Fix L and t0 from expert priors; calibrate only k0 using least squares.
- **Parameter s** (cost sensitivity) requires Cost_Advantage(t) series; if cost data unavailable, set s = 0 (adoption driven by non-price factors only).

**Calibration**
- Fit (L, t0, k0, s) to observed VRLA vs Li shares (least squares + bounds).
- Prior constraints: L < 1; smoothness on k(t); monotone response to Cost_Advantage.

---

## 5️⃣ Battery Metrics & Duration Assumptions
- **Duration (h)** for power→energy conversion (default 4h; range 2–8h).
- **Energy capacity (GWh)** vs **Power capacity (GW)**: Power = Energy / Duration.
- **Throughput (TWh/yr)** = Energy_Capacity_GWh × cycles_per_year / 1000.
  - Defaults: cycles_per_year = 250; round‑trip efficiency (RTE) = 0.88.

**Note**: These metrics (duration, cycles, RTE) are **optional** in v1 core demand workflow. Use them for:
- Auxiliary throughput analysis (TWh/yr)
- Material intensity calculations (using `Data_Center_UPS_Battery_(Li-Ion)_Average_Lithium_content_Global` dataset)
- If not computing these outputs, this section can be omitted.

---

## 6️⃣ New‑Build Modeling
**Inputs**
- Growth projection series per region (fractional rates: e.g., 0.077 = 7.7%)
- Dataset: `Datacenter_capacity_growth_projections_<region>`
- OR direct new-build trajectory (if available)

**Derivation from growth projections**
If only growth rates provided:
1. Compute total market size: Total_Market(t) = Total_Market(t−1) × (1 + growth(t))
2. Compute total retirements: Replacement(t) = IB_VRLA(t)/Life_VRLA + IB_Li(t)/Life_Li
3. Derive new-build residually: New_Build(t) = Total_Market(t) − Replacement(t)
4. Floor at zero: New_Build(t) = max(0, New_Build(t))

**Alternative: Direct CAGR on new-build**
- If new-build trajectory given: New_Build(t) = New_Build(t−1) × (1 + g_t)
- Optionally cap YoY growth with **g_max** to avoid blow‑ups; carry unmet growth forward as backlog.

**Initialization**
- If Total_Market(start_year) unknown: sum available VRLA_demand + Li_demand for that year.
- Use datasets: `Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_<region>` + `Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_<region>`

---

## 7️⃣ Replacement Modeling
- Li‑ion retrofits = M(t) × Contestable(t).
- VRLA‑for‑VRLA  = (1 − M(t)) × Contestable(t).
- Li‑for‑Li replacements begin materializing near year ≈ Life_Li (around year start_year + 12).
- Note: Contestable(t) defined in Section 3.

---

## 8️⃣ Price & $ Outputs
- Revenue_Li(t)  = Li_MWh_Adds(t)  × Price_Li_per_kWh(t)
- Revenue_VRLA(t)= VRLA_MWh_Adds(t)× Price_VRLA_per_kWh(t)
- Price series derived from CapEx per kWh if ASPs absent (apply margin uplift if needed).

---

## 9️⃣ Recommended Defaults (edit in config)
- Lifespans: VRLA **5y**; Li‑ion **12y**.
- Ceiling L: **0.95–0.98**; t0 prior: **2028–2030** if unknown; k0 prior: **0.2–0.3**.
- Sensitivity s: **2e−5 per USD** of TCO advantage (calibrate to history).
- Discount rate r: **0.08** (range 0.06–0.10).
- Duration: **4h**; cycles/yr: **250**; RTE: **0.88**.
- Li‑ion CapEx: **learning rate 15–20%** per doubling or **log‑CAGR** 6–12%/yr.
- VRLA OpEx proxy (per kWh‑yr): **$18** (≈ $12 O&M + $6 cooling/space).
- Li‑ion OpEx proxy (per kWh‑yr): **$6** (≈ $4 O&M + $2 cooling/space).
- Regional price multipliers (if regional series missing): China 0.9×; USA 1.0×; Europe 1.15×; RoW 1.0×.

---

## 🔟 Data Mapping & Fallback Summary

**✅ AVAILABLE in Taxonomy (datacenter_ups_taxonomy_and_datasets_v2)**

*Demand datasets:*
- Historical demand by technology & region:
  - `Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_<region>` (VRLA)
  - `Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_<region>` (Li-ion)
  - `Data_Center_Battery_Demand_Annual_Capacity_Demand_<region>` (Total market - use for validation)
  - Regions: China, Europe, Global, Rest_of_World, USA

*Installed base:*
- `Lead_acid_batteries_UPS_Datacenter_Installed_Base_<region>` (VRLA only; Li-ion missing)

*Cost data:*
- Li-ion: `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>` (China, Europe, USA, Global)
- Li-ion: `Battery_Energy_Storage_System_(2-hour_Turnkey)_Cost_<region>` (alternative duration)
- VRLA: `VRLA_Battery_Cost_Global` (flat trajectory assumption)
- Power-basis: `Battery_Energy_Storage_System_Installed_Cost_Global` ($/kW; convert using duration)

*Growth drivers:*
- `Datacenter_capacity_growth_projections_<region>` (fractional annual rates)

*Lifetimes:*
- `Lead_acid_batteries_UPS_Datacenter_Replacement_cycle_Battery_Replacement_cycle_Global` (VRLA)
- `Li_ion_UPS_Replacement_cycle_Global` (Li-ion; default 12y)

*Material intensity (auxiliary):*
- `Data_Center_UPS_Battery_(Li-Ion)_Average_Lithium_content_Global`

**⚠️ PARTIAL - Use Defaults for Missing Data**

*OpEx data:*
- Turnkey costs do NOT include ongoing operational expenses
- Use Section 9 defaults:
  - VRLA: $18/kWh-yr (maintenance + cooling/space)
  - Li-ion: $6/kWh-yr
- Optionally: collect regional OpEx multipliers if available

**🔧 INITIALIZATION RULES (for missing data)**
- **Li-ion installed base**: If missing for start_year, initialize `IB_Li(start) = 0` OR derive from derived shares × total IB
- **Historical shares**: Derive from demand data: `Li_share(t) = Li_demand(t) / (VRLA_demand(t) + Li_demand(t))`
- **Regional parameters**: Inherit from Global (e.g., replacement cycles, lithium content) if regional values unavailable
- **New-build absolute values**: If missing, derive using Section 6 logic from growth projections
- **VRLA regional costs**: Apply regional multipliers (China 0.9×, Europe 1.15×, USA/RoW 1.0×) to Global cost

**📋 FALLBACK RULES**
- Missing shares (pre-history) → initialize M(t0) from expert point + adopt k0 prior; cap annual share delta ≤ 15 pp
- Cost shocks → allow scenario overrides on CapEx/OpEx for specific years
- Missing Li-ion installed base warm-up → back-cast only if >12 years of demand history available

---

## 1️⃣1️⃣ Example Flow Summary
1. Select region (e.g., **USA**).
2. Load inputs: new_build, capex/opex by tech, shares_hist; warm‑up installed bases if missing.
3. Build CapEx paths using **log‑CAGR/learning rate**; assemble OpEx; compute **TCO** per tech.
4. Compute **Cost_Advantage**(t); find **tipping (economic)**.
5. Calibrate (L, t0, k0, s) to observed shares (bounds + priors).
6. Annual loop: new_build + contestable → split with M(t) → update installed bases → record flows/stocks.
7. Price to $ using per‑kWh series; export tables & charts.

---

## 1️⃣2️⃣ Output Schema (per region, annual)
- `year`
- `li_share`, `vrla_share`, `tipping_flag` (0/1)
- `new_build_mwh`, `replacement_mwh`, `contestable_mwh`
- `adds_li_mwh`, `adds_vrla_mwh`, `reti_li_mwh`, `reti_vrla_mwh`
- `ib_li_mwh`, `ib_vrla_mwh`, `total_mwh`
- `$li`, `$vrla`, `price_li_per_kwh`, `price_vrla_per_kwh`
- `cost_advantage_per_kwh`

---

## 1️⃣3️⃣ Config Keys (YAML)
```
horizon: {start_year: 2024, end_year: 2035}
units: {demand: MWh, currency: USD_2024}
finance: {discount_rate: 0.08}
lifespans: {vrla: 5, li: 12}
market: {mode: cagr, start_value_mwh: 100000, cagr: 0.077}
adoption: {L_max: 0.98, k0_prior: 0.25, t0_prior: 2029, sensitivity_prior: 0.00002}
capex_per_kwh: 
  vrla: {mode: flat, value: 220, regional_multiplier: {china: 0.9, usa: 1.0, europe: 1.15, row: 1.0}}
  li: {mode: historical_series, dataset: "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost", forecast_method: log_cagr}
opex: {vrla_per_kwh_year: 18, li_per_kwh_year: 6}
cooling_space_uplift_note: "OpEx values above include maintenance + cooling/space costs"
regional_price_multiplier: {china: 0.9, usa: 1.0, europe: 1.15, row: 1.0}
duration_hours: 4
cycles_per_year: 250
rte: 0.88
share_delta_cap_pp: 15
```

---

## 1️⃣4️⃣ Validation & QA
- **Mass balance** holds (adds − retirements) vs installed‑base delta: |error| ≤ 0.1%.
- **Unit checks**: MW↔MWh conversion via duration; $ in real terms.
- **Backtest** on holdout years: shares MAPE ≤ 15%.
- **Sensitivity**: adoption increases monotonically with Cost_Advantage.
- **Scenario sanity**: tipping year moves earlier if Li‑ion CapEx falls faster or OpEx gap widens.

---

## 1️⃣5️⃣ Edge Cases & Overrides
- New‑build slump (negative g): floor new_build at ≥ 0; allow carry‑forward backlog.
- Share saturation: clamp M(t) ∈ [0, L]; enforce L ≤ 0.99.
- Data gaps: linear‑interpolate ≤ 2y gaps; >2y → use proxy region multiplier.
- Sudden ASP shocks: explicit override list `{year: delta_$}` applied post‑forecast.

