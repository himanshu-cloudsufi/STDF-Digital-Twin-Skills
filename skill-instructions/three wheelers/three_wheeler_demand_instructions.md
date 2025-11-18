# Three-Wheeler Demand Analysis & Forecasting Instructions

## Scope

- **Market**: Three_Wheelers (all powertrains)
- **Powertrains**:
  - Disruptor: EV three-wheelers (battery electric)
  - Incumbent: ICE three-wheelers (internal combustion)
- **Regions (core)**: China, Europe, Rest_of_World
- **Global**: Derived as sum of regional results (China + Europe + Rest_of_World). Use global series mainly as a sanity check.
- **Forecast horizon**: Typically to 2040.
- **Tipping point**: Year when EV 3W cost falls below ICE 3W cost on a comparable basis.

---

## 1. Cost-Based Tipping Point (EV vs ICE Three-Wheelers)

### 1.1 Select Cost Series

For each region (China, Europe, Rest_of_World) load:

- **EV disruptor cost (primary parity series)**  
  - `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_<Region>`  
  - Lowest available cost for a ~100 km range EV 3W that is a viable substitute for typical ICE 3W usage.

- **EV disruptor cost (support / sensitivity)**  
  - `Three_Wheeler_(EV)_Median_Cost_<Region>`  
  - Use for cross-checking and sensitivity around typical buyer costs.

- **ICE incumbent cost**  
  - `Three_Wheeler_(ICE)_Median_Cost_<Region>`  
  - Median transaction cost for ICE three-wheelers in that region.

**Preconditions**

- Convert all cost series to a common real currency (e.g., 2023 USD).
- Ensure EV and ICE costs refer to comparable segments / use cases.
- Handle obvious outliers before modelling.

### 1.2 Smooth Cost Curves

For each cost series:

1. Apply a 3-year rolling median (or mean) on historical data.
2. Use the smoothed curves for tipping and forecasting; keep original as reference.

### 1.3 Forecast Cost Curves

For each of the three series (EV-lowest, EV-median, ICE-median) and for each region:

1. Transform to log scale: `y_t = log(cost_t)`.
2. Compute a long-term CAGR from a stable historical window (e.g., last 5–10 years).
3. Extrapolate `y_t` forward to 2040 using that trend (optionally damped if extreme).
4. Exponentiate back to get forecasted cost in real currency.
5. Optionally re-apply a light 3-year rolling median on the full (historical + forecast) series.

### 1.4 Tipping Point Logic

Primary comparison (per region):

- EV: `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_<Region>` (smoothed, forecasted)  
- ICE: `Three_Wheeler_(ICE)_Median_Cost_<Region>` (smoothed, forecasted)

Rules:

1. For each year, find the first year where  
   `Cost_EV_lowest(y) <= Cost_ICE_median(y)`.
2. If EV has been cheaper for the full window, set tipping year to first historical year.
3. If EV never becomes cheaper by 2040, set tipping year = `None`.
4. Optionally compute a second tipping using EV-median vs ICE-median.

Outputs:

- `Tipping_Year_Primary_<Region>`
- `Tipping_Year_Secondary_<Region>` (optional)

---

## 2. Forecast Total Three-Wheeler Market Demand

### 2.1 Base Market Datasets

For each region:

- `Three_Wheeler_Annual_Sales_China`
- `Three_Wheeler_Annual_Sales_Europe`
- `Three_Wheeler_Annual_Sales_Rest_of_World`

Global (sanity check):

- `Three_Wheeler_Annual_Sales_Global`

### 2.2 Fit Market Trend Per Region

For each `Three_Wheeler_Annual_Sales_<Region>`:

1. If noisy, smooth sales with a 3-year rolling median.
2. Fit a robust long-term trend (Theil–Sen / robust linear regression) of sales vs year.
3. Extrapolate to 2040.

Constraints:

- Enforce `Three_Wheeler_Annual_Sales_<Region>_Forecast(y) ≥ 0`.
- Keep long-run CAGR within a reasonable band (e.g., −5% to +5% per year).
- Allow flat or gently declining forecasts if history clearly shows maturity/decline.

Outputs:

- `Three_Wheeler_Annual_Sales_<Region>_Forecast(y)` to 2040.
- `Three_Wheeler_Annual_Sales_Global_Forecast(y)` = sum of regional forecasts.

---

## 3. Forecast EV Three-Wheeler Demand (Disruptor)

### 3.1 Historical EV Share

EV sales datasets:

- `Three_Wheeler_(EV)_Annual_Sales_China`
- `Three_Wheeler_(EV)_Annual_Sales_Europe`
- `Three_Wheeler_(EV)_Annual_Sales_Rest_of_World`  
- `Three_Wheeler_(EV)_Annual_Sales_Global` (reference)

For each region:

1. Align EV and total 3W sales by year.
2. Compute EV share:  
   `share_EV(y) = Three_Wheeler_(EV)_Annual_Sales_<Region>(y) / Three_Wheeler_Annual_Sales_<Region>(y)`.
3. Skip years where total sales are missing or zero.
4. Clip `share_EV(y)` into [0, 1].
5. Optionally smooth share with a short rolling window if extremely noisy.

### 3.2 Extend EV Share Pre-Tipping (If Needed)

If `Tipping_Year_Primary_<Region>` > last historical year:

1. Take the last few (3–7) years of historical EV share.
2. Fit a simple linear or low-order polynomial trend of `share_EV(y)` vs `y`.
3. Extrapolate EV share from last historical year to tipping year.
4. Clip extrapolated share into [0, 1].

Output:

- `share_EV_pre_tipping(y)` to tipping year.

### 3.3 Logistic EV Adoption Post-Tipping

Use a logistic curve:

`s(t) = L / (1 + exp(-k * (t - t0)))`

- `L`: long-run EV share ceiling (default 1.0 or 0.9).
- `k`: slope (speed of transition).
- `t0`: mid-point year when share ~ L/2 (anchor near tipping year).

Per region:

1. Combine historical EV share, pre-tipping extension, and any early post-tipping data.
2. Fit `L`, `k`, `t0` with bounds, e.g.:
   - `L ∈ [0.7, 1.0]`
   - `k ∈ [0.05, 1.5]`
   - `t0` in `[min_year - 5, max_year + 10]`, loosely anchored near tipping year.

Fallback (if fit fails):

- Use a rule-based S-curve:
  - Slow increase until ~5 years before tipping.
  - Rapid increase from ~5 years before to ~10 years after tipping.
  - Saturation near `L` by 2035–2040.

### 3.4 Convert EV Share to EV Sales

For each forecast year and region:

1. Get `share_EV_fore(y)` from logistic or fallback S-curve.
2. Compute EV sales:

   `Three_Wheeler_(EV)_Annual_Sales_<Region>_Forecast(y) = share_EV_fore(y) * Three_Wheeler_Annual_Sales_<Region>_Forecast(y)`

3. Enforce:

   - `0 ≤ Three_Wheeler_(EV)_Annual_Sales_<Region>_Forecast(y) ≤ Three_Wheeler_Annual_Sales_<Region>_Forecast(y)`.

---

## 4. Forecast ICE Three-Wheeler Demand (Incumbent)

### 4.1 Residual Demand Logic

For each region and year:

`Three_Wheeler_(ICE)_Annual_Sales_<Region>_Forecast(y) = max(Three_Wheeler_Annual_Sales_<Region>_Forecast(y) - Three_Wheeler_(EV)_Annual_Sales_<Region>_Forecast(y), 0)`

- ICE demand is the residual once EV demand is accounted for.
- Clamp at zero to avoid negative ICE sales.

### 4.2 Installed Base Consistency (ICE Fleet)

ICE fleet datasets:

- `Three_Wheeler_(ICE)_Total_Fleet_China`
- `Three_Wheeler_(ICE)_Total_Fleet_Europe`
- `Three_Wheeler_(ICE)_Total_Fleet_Rest_of_World`
- `Three_Wheeler_(ICE)_Total_Fleet_Global`

Procedure:

1. Define an ICE lifetime / scrappage curve (e.g., 8–12 years average, tail to 15 years).
2. Using historical ICE sales, reconstruct an implied ICE fleet.
3. Compare reconstructed fleet with `Three_Wheeler_(ICE)_Total_Fleet_<Region>` and adjust lifetime assumptions if needed.
4. In forecasts, enforce:

   `ICE_Fleet(y) = ICE_Fleet(y-1) + ICE_Sales_Forecast(y) - ICE_Scrappage(y)`

---

## 5. EV Fleet Consistency

EV fleet datasets:

- `Three_Wheeler_(EV)_Total_Fleet_China`
- `Three_Wheeler_(EV)_Total_Fleet_Europe`
- `Three_Wheeler_(EV)_Total_Fleet_Rest_of_World`
- `Three_Wheeler_(EV)_Total_Fleet_Global`

Procedure:

1. Define an EV lifetime / scrappage curve (possibly different from ICE).
2. Reconstruct historical EV fleet from EV sales and compare to `Three_Wheeler_(EV)_Total_Fleet_<Region>`.
3. Adjust EV lifetime / scrappage parameters if systematic mismatches appear.
4. In forecasts, enforce:

   `EV_Fleet(y) = EV_Fleet(y-1) + EV_Sales_Forecast(y) - EV_Scrappage(y)`

Fleet consistency ensures that rapid EV adoption in sales is reflected in fleet, not just a one-off spike.

---

## 6. Link to Lead Demand (Three-Wheeler Component)

Lead datasets:

- `Lead_Annual_Implied_Demand-Sales_3_wheelers_Global`
- `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers_Global`

Usage (in the lead module):

1. Use EV/ICE fleet trajectories and battery chemistries to estimate:
   - Lead demand from batteries in new 3W sales.
   - Lead demand from replacement batteries in the existing 3W fleet.
2. Map these to the global implied demand series:
   - Sales-driven lead demand → `Lead_Annual_Implied_Demand-Sales_3_wheelers_Global`
   - Replacement-driven lead demand → `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers_Global`

This is not required to forecast 3W units, but critical for commodity impact analysis.

---

## 7. Checks, Defaults & Best Practices

- Align all series on:
  - Same calendar years
  - Same region definitions
- Run full pipeline per region, then sum to Global.
- Clamp shares to [0, 1].
- Ensure `EV_sales + ICE_sales ≤ Total_3W_sales` within numerical tolerance.
- Avoid sharp discontinuities around tipping year; use smoothing or parameter adjustments.
- Defaults:
  - Forecast horizon: 2040
  - Logistic ceiling L: 1.0 (or 0.9)
  - Market CAGR limits: −5% to +5% per year
  - Cost smoothing: 3-year rolling median

---

## 8. Tabular Step-by-Step Instructions (for Implementation Sheet)

| Step # | Step Title                                   | Step Description                                                                                                                                                                                                                                                                                                                                                                         | Key Outputs |
|--------|----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| 1      | Select Region & Load Data                    | Work on each region (China, Europe, Rest_of_World) independently. For the chosen region, load: `Three_Wheeler_Annual_Sales_<Region>`, `Three_Wheeler_(EV)_Annual_Sales_<Region>`, `Three_Wheeler_(ICE)_Annual_Sales_<Region>` (if available), EV and ICE fleet datasets, and all cost series (`EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_<Region>`, `Three_Wheeler_(EV)_Median_Cost_<Region>`, `Three_Wheeler_(ICE)_Median_Cost_<Region>`). Align years across all series. | Region name, aligned datasets and common year range |
| 2      | Prepare & Harmonize Cost Series              | Convert EV and ICE cost series to a common real currency (e.g., 2023 USD). Check comparability of vehicle segment/use-case. Handle missing values via interpolation or by marking gaps. Decide which EV cost series is primary (lowest cost) and which is supporting (median cost) for sensitivity analysis.                                                                                                            | Clean, harmonized EV-lowest, EV-median, and ICE-median cost series per region |
| 3      | Forecast Cost Curves (EV vs ICE)             | For each cost series: transform to `log(cost)`, compute long-term CAGR over a stable historical window, and extrapolate to 2040 in log-space. Exponentiate back to get forecast cost. Apply a 3-year rolling median to the combined historical+forecast series to reduce noise.                                                                                                                                                  | Smoothed, forecasted EV and ICE cost curves to 2040 |
| 4      | Determine Tipping Point                      | Using forecasted, smoothed cost curves, identify the first year where `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_<Region> <= Three_Wheeler_(ICE)_Median_Cost_<Region>`. If EV is always cheaper, set tipping = first historical year. If EV never becomes cheaper by 2040, set tipping = `None`. Optionally compute a secondary tipping using EV-median vs ICE-median.                                                                 | Primary tipping year (and optional secondary tipping year) per region |
| 5      | Forecast Market Demand                       | Start from `Three_Wheeler_Annual_Sales_<Region>`. Smooth if very noisy. Fit a robust long-term trend (Theil–Sen / robust linear regression) of sales vs year. Extrapolate to 2040, enforcing non-negative values and keeping long-run CAGR between roughly −5% and +5% per year. Sum regional forecasts to build a Global forecast and compare with `Three_Wheeler_Annual_Sales_Global` as a sanity check.                         | `Three_Wheeler_Annual_Sales_<Region>_Forecast` and derived Global forecast |
| 6      | Estimate Historical EV Share & Pre-Tipping Share | Use `Three_Wheeler_(EV)_Annual_Sales_<Region>` and total sales to compute `EV_share(y) = EV_sales / total_sales`. Skip years with zero/undefined total sales and clip shares to [0,1]. If the tipping year is after the last historical year, extend EV share to the tipping year using a simple linear (or low-order polynomial) trend, again clipped to [0,1].                                                                      | Historical EV share series and pre-tipping EV share extension (if required) |
| 7      | Forecast EV Adoption (Post-Tipping)          | Fit a logistic curve for EV share: `s(t) = L / (1 + exp(-k · (t − t0)))` using historical EV share + pre-tipping extension (+ early post-tipping points if any). Constrain `L`, `k`, and `t0` to sensible ranges and loosely anchor `t0` near the tipping year. If fitting fails, use a rule-based S-curve (slow growth pre-tipping, rapid growth around tipping, saturation near `L` by 2035–2040).                             | EV share curve `share_EV_fore(y)` for each region to 2040 |
| 8      | Convert EV Share to EV Sales                 | For each forecast year, compute EV sales as `Three_Wheeler_(EV)_Annual_Sales_<Region>_Forecast(y) = share_EV_fore(y) * Three_Wheeler_Annual_Sales_<Region>_Forecast(y)`. Clamp EV sales to be between 0 and total market sales for that year.                                                                                                                                                                                    | `Three_Wheeler_(EV)_Annual_Sales_<Region>_Forecast` |
| 9      | Compute ICE Sales (Residual) & Fleet Checks  | Compute ICE sales as residual: `Three_Wheeler_(ICE)_Annual_Sales_<Region>_Forecast = max(Total_3W_sales_fore − EV_sales_fore, 0)`. Use historical and forecast ICE sales with a lifetime/scrappage curve to reconstruct ICE fleet and compare with `Three_Wheeler_(ICE)_Total_Fleet_<Region>`. Adjust lifetime assumptions if fleets deviate systematically.                                                                       | `Three_Wheeler_(ICE)_Annual_Sales_<Region>_Forecast` and consistent ICE fleet paths |
| 10     | EV Fleet Consistency, Validation & Lead Linkage | Similarly, reconstruct EV fleet using EV sales and a lifetime curve, and compare with `Three_Wheeler_(EV)_Total_Fleet_<Region>`. Adjust assumptions if needed. Run final sanity checks: clamp all shares to [0,1]; ensure `EV_sales + ICE_sales ≤ Total_3W_sales`; ensure no negative values; transitions around tipping should be smooth. Aggregate regional EV/ICE/total sales and fleets to Global, and (optionally) prepare linkages to `Lead_Annual_Implied_Demand-Sales_3_wheelers_Global` and `Lead_Annual_Implied_Demand-Vehicle_replacement_3_wheelers_Global` for the lead module. | Clean, internally consistent EV/ICE/total 3W sales and fleets per region and Global, ready for commodity impact (Lead) |
