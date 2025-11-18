# Commercial Vehicle Demand Analysis & Forecasting – Instructions

Market: **Commercial Vehicles** (LCV, MCV, HCV)  
Powertrains: **EV (disruptor), ICE (incumbent), NGV (chimera)**  
Regions: **China, Europe, USA, Rest_of_World** (Global = sum of regions)  
Horizon: typically to **2040**.

---

## Step‑by‑step methodology

### 1. Select Region, Segments & Load Data
- Work one region at a time (China, Europe, USA, Rest_of_World).
- Load total CV sales, segment‑level sales (LCV/MCV/HCV × EV/ICE/NGV), fleets where available, and all EV/ICE cost series for that region.
- Align all series to a common year axis and document data gaps.

### 2. Build Segment Totals & Check vs Total CV
- For each segment `s` compute:  
  `Sales_Total_s(y) = Sales_EV_s(y) + Sales_ICE_s(y) + Sales_NGV_s(y)`.
- Sum segments to get reconstructed total CV sales and compare with `Commercial_Vehicle_Annual_Sales_<Region>`.
- Use segment totals as primary; treat large gaps as data‑quality flags.

### 3. Prepare & Forecast Cost Curves (by Segment)
- For each segment (LCV, MCV, HCV), convert EV lowest cost and ICE price series to a common real currency.
- Smooth with a 3‑year rolling median.
- Work in log(cost), fit a long‑term trend, and forecast to 2040; exponentiate back to level space.
- Keep aggregate EV median cost as a cross‑check only.

### 4. Determine Segment Tipping Points
- For each segment, find the first year where forecast EV cost ≤ ICE cost.
- If EV is always cheaper, tipping = first historical year; if never cheaper by 2040, tipping = `None`.
- Store `Tipping_Year_LCV`, `Tipping_Year_MCV`, `Tipping_Year_HCV` per region.

### 5. Forecast Segment‑Level Total Demand
- Using historical `Sales_Total_s(y)`, smooth if needed and fit a robust trend (e.g. Theil–Sen).
- Extrapolate to 2040 with constraints: no negative sales, long‑run CAGR roughly in [−5%, +5%].
- Sum segment forecasts to obtain total CV forecast per region and reconcile against a direct forecast on `Commercial_Vehicle_Annual_Sales_<Region>`.

### 6. Estimate Historical EV Shares & Pre‑Tipping Evolution
- For each segment: `share_EV_s(y) = Sales_EV_s(y) / Sales_Total_s(y)`, clipped to [0,1].
- Ignore years with missing or zero totals; optionally smooth noisy series.
- If tipping is in the future, extend EV share smoothly from last historical year to tipping (simple linear / low‑order polynomial trend).

### 7. Forecast EV Adoption (Post‑Tipping, per Segment)
- Fit a logistic curve for EV share: `s(t) = L / (1 + exp(−k(t − t0)))` using historical + pre‑tipping points.
- Constrain `L` (0.7–1.0), `k` (0.05–1.5), `t0` around the tipping year.
- If fitting is unstable, use a rule‑based S‑curve: slow pre‑tipping growth, fast post‑tipping rise, near‑saturation by 2035–2040.
- Multiply EV share by segment total demand to get EV sales forecasts.

### 8. Model NGV as Chimera & Convert to Sales
- Compute NGV share per segment: `share_NGV_s(y) = Sales_NGV_s(y) / Sales_Total_s(y)`.
- Identify the historical peak; allow growth up to peak, then impose a declining profile (e.g. 5–7 year half‑life after peak or after tipping).
- Ensure NGV share tends to near‑zero by 2040.
- Multiply NGV share by total demand to get NGV sales.

### 9. Compute ICE Residual & Calibrate Fleets
- For each segment and year:  
  `Sales_ICE_s_fore(y) = max(Sales_Total_s_fore(y) − Sales_EV_s_fore(y) − Sales_NGV_s_fore(y), 0)`.
- Check that EV + NGV + ICE never exceeds total segment demand.
- Using assumed lifetimes, reconstruct EV and ICE fleets from sales and compare with fleet datasets; adjust scrappage assumptions to keep fleets consistent.

### 10. Aggregate, Validate & Link to Lead Demand
- Aggregate segment‑level EV/ICE/NGV forecasts to total CV per region and then to Global.
- Run final validation: shares in [0,1]; no negative values; segment sums ≈ total; smooth behaviour around tipping years.
- Use the resulting sales/fleet forecasts as inputs to lead‑demand modules based on:
  - `Lead_Annual_Implied_Demand-Sales_Commercial_vehicles_Global`
  - `Lead_Annual_Implied_Demand-Sales_Buses_Global`
  - `Lead_Annual_Implied_Demand-Vehicle_replacement_Commercial_Global`.