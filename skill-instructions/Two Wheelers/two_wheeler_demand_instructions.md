# Two-Wheeler Demand Analysis & Forecasting Instructions

## Scope

- **Market**: Two_Wheelers (all powertrains)
- **Powertrains**:
  - Disruptor: EV two-wheelers (battery electric)
  - Incumbent: ICE two-wheelers (internal combustion)
- **Regions**: China, Europe, USA, Rest_of_World
- Treat each region separately; compute regional forecasts first.
- Global = sum of regional results (no double counting).
- Tipping point = cost parity year where EV 2W becomes cheaper than ICE 2W on a comparable basis.

---

## 1. Determine Tipping Point (EV vs ICE Two-Wheelers)

### 1.1 Select Cost Series

For each region:

- **EV disruptor cost (primary for parity)**  
  - `EV_2_Wheeler_(Range-100_KM)_Lowest_Cost_<Region>`  
  - Lowest available cost for a ~100 km range EV 2W that is a viable substitute for mainstream ICE 2W.

- **EV disruptor cost (support / sensitivity)**  
  - `Two_Wheeler_(EV)_Median_Cost_<Region>`  
  - Use for sensitivity analysis and cross-checking lowest-cost series.

- **ICE incumbent cost**  
  - `Two_Wheeler_(ICE)_Median_Cost_<Region>`  
  - Median transaction cost for ICE two-wheelers.

**Preconditions**

- Convert all cost series to a common **real currency** (e.g., 2023 USD).
- Ensure comparable segment / product definition across EV and ICE series.

### 1.2 Smooth Cost Curves

For each cost series:

1. Apply a **3-year rolling median** (or mean) on the historical series.
2. Use the smoothed series for tipping-point detection.

### 1.3 Forecast Cost Curves

For each of the three cost series (EV-lowest, EV-median, ICE-median):

1. Transform to log-scale: `log(cost_t)`.
2. Compute long-term **CAGR** on the log series over a stable historical window.
3. Extrapolate `log(cost)` forward to the forecast horizon (default 2040).
4. Exponentiate to get the forecast cost in normal units.
5. Merge historical + forecast into a full cost curve per series.

### 1.4 Tipping Point Logic

Primary comparison:

- EV disruptor: `EV_2_Wheeler_(Range-100_KM)_Lowest_Cost_<Region>`
- Incumbent: `Two_Wheeler_(ICE)_Median_Cost_<Region>`

Rules:

1. For each year, compare smoothed + forecasted EV and ICE cost.
2. If EV cost crosses below ICE cost:
   - Tipping year = first year where `Cost_EV <= Cost_ICE`.
3. If EV cost has always been cheaper in your window:
   - Tipping year = first historical year.
4. If EV never becomes cheaper (even by 2040):
   - Tipping year = None → use slower, non-logistic EV adoption.

Optionally also compute a **second tipping** using EV-median vs ICE-median for sensitivity.

---

## 2. Forecast Total Two-Wheeler Market Demand

### 2.1 Base Market Dataset

For each region:

- `Two_Wheeler_Annual_Sales_<Region>`

Use regional series (China, Europe, USA, Rest_of_World) as primary.  
Compute Global by summing regional sales.

### 2.2 Fit Market Trend

For each region:

1. Use historical `Two_Wheeler_Annual_Sales_<Region>`.
2. Fit a robust long-term trend (e.g., Theil–Sen regression) of annual sales vs year.
3. Extrapolate to the forecast horizon (default 2040).

Constraints:

- Enforce non-negative demand: `market_fore(y) ≥ 0`.
- Clamp long-run average **CAGR** to a sensible range, e.g. `-5% ≤ CAGR ≤ +5%`.
- For highly volatile data, smooth sales with a rolling median before fitting.

Output:

- `Two_Wheeler_Annual_Sales_<Region>_Forecast(y)` for all forecast years.

---

## 3. Forecast EV Two-Wheeler Demand (Disruptor)

### 3.1 Historical EV Share

EV demand datasets:

- `Two_Wheeler_(EV)_Annual_Sales_<Region>`

For each region:

1. Align EV sales and total 2W sales by year.
2. Compute EV share:
   - `share_EV(y) = Two_Wheeler_(EV)_Annual_Sales_<Region>(y) / Two_Wheeler_Annual_Sales_<Region>(y)`
3. Skip years where total sales are zero or missing.
4. Clip `share_EV(y)` into `[0, 1]`.

### 3.2 Pre-Tipping Extrapolation

If tipping year is **after** the last historical year:

1. Take the last few years of historical EV share.
2. Fit a simple linear / low-order polynomial trend on share vs year.
3. Extrapolate that **pre-tipping** trend to the tipping year.
4. Clip extrapolated share into `[0, 1]`.

### 3.3 Logistic Adoption Post-Tipping

Use a logistic curve for EV share evolution:

`s(t) = L / (1 + exp(-k * (t - t0)))`

- `L`: long-run ceiling (default 1.0 or 0.9).
- `k`: slope (speed of transition).
- `t0`: mid-point year where share ~ L/2.

Fitting:

- Use observed shares + pre-tipping extension + early post-tipping data (if available).
- Constrain parameters:
  - `k` in `[0.05, 1.5]`
  - `t0` in `[min_year - 5, max_year + 10]`
- Anchor `t0` loosely around the tipping year.

Fallback if fitting fails (sparse/noisy data):

- Use a heuristic S-curve:
  - Slow growth until a few years before tipping.
  - Rapid growth around tipping ±5–10 years.
  - Saturation near `L` by ~2035–2040.

### 3.4 Convert EV Share to EV Demand

For each forecast year and region:

1. Compute forecast share: `share_EV_fore(y)`.
2. Multiply by total market forecast:
   - `Two_Wheeler_(EV)_Annual_Sales_<Region>_Forecast(y) = share_EV_fore(y) * Two_Wheeler_Annual_Sales_<Region>_Forecast(y)`
3. Enforce:
   - `0 ≤ EV_sales_fore ≤ Total_2W_sales_fore`.

### 3.5 Installed Base Consistency (EV Fleet)

EV fleet datasets:

- `Two_Wheeler_(EV)_Total_Fleet_<Region>` (where available)

Steps:

1. From historical EV sales and an assumed lifetime / scrappage curve, reconstruct implied EV fleet.
2. Compare with `Two_Wheeler_(EV)_Total_Fleet_<Region>` and adjust lifetime assumptions if needed.
3. In forecasts, enforce:

   - `EV_Fleet(y) = EV_Fleet(y-1) + EV_Sales(y) - EV_Scrappage(y)`

Use fleet mainly for **sanity checks**; primary forecast is on sales.

---

## 4. Forecast ICE Two-Wheeler Demand (Incumbent)

### 4.1 Residual Demand Logic

For each region and year:

`Two_Wheeler_(ICE)_Annual_Sales_<Region>_Forecast(y) = max(Two_Wheeler_Annual_Sales_<Region>_Forecast(y) - Two_Wheeler_(EV)_Annual_Sales_<Region>_Forecast(y), 0)`

- ICE sales = remaining market after EV demand.
- Clamp to zero if EV sales exceed total market due to numeric issues.

### 4.2 Installed Base Consistency (ICE Fleet)

ICE fleet datasets:

- `Two_Wheeler_(ICE)_Total_Fleet_<Region>`

Procedure:

1. Using historical ICE sales and a lifetime curve, reconstruct implied ICE fleet.
2. Compare against `Two_Wheeler_(ICE)_Total_Fleet_<Region>` to calibrate scrappage assumptions.
3. In forecasts, ensure:

   - `ICE_Fleet(y) = ICE_Fleet(y-1) + ICE_Sales(y) - ICE_Scrappage(y)`

Again, use fleet as consistency check for displacement of ICE.

---

## 5. Link to Lead Demand (for Lead Module)

Lead datasets:

- `Lead_Annual_Implied_Demand-Sales_2_wheelers_Global`
- `Lead_Annual_Implied_Demand-Vehicle_replacement_2_wheelers_Global`

High-level usage:

1. Interpret EV and ICE fleet evolution as drivers of batteries that use lead (mainly ICE 2W and some EV depending on chemistry).
2. In the lead module:
   - Estimate lead per vehicle and battery chemistry mix.
   - Use EV/ICE sales and fleet to allocate lead implied demand between:
     - Original equipment batteries (sales)
     - Replacement batteries (fleet and replacement rate)

This is optional for 2W demand forecasting but required to connect disruption to **lead implied demand**.

---

## 6. Checks, Defaults, and Good Practices

- Always align series on:
  - Same calendar year
  - Same region definitions
- Run the full pipeline **per region**, then sum to Global.
- Clip shares to `[0, 1]`.
- Ensure `EV_sales + ICE_sales ≤ Total_2W_sales` (within numerical tolerance).
- No negative values for sales or fleets.
- Avoid sharp discontinuities around the tipping year; transitions should be smooth.

**Default knobs:**

- Forecast horizon: 2040
- Logistic ceiling `L`: 1.0 (or 0.9)
- Market CAGR cap: ±5% per year
- Cost smoothing: 3-year rolling median

---

## 7. Final Outputs Per Region

1. Cost curves (EV lowest, EV median, ICE median) with tipping year(s).
2. Total 2W demand: historical + forecasted.
3. EV demand: historical + forecasted.
4. ICE demand: historical + forecasted.
5. EV and ICE fleets (consistency checked).
6. Global aggregates built as the sum of regional outputs.
