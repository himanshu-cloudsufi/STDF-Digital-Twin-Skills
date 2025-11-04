# Cost-Driven Demand Forecasting Logic (Editable Version)

## Scope
- Treat each region (≠ Global) independently.  
- Compute regional demand forecasts first.  
- If you need a Global demand forecast, sum regions carefully (avoid double counting).  
- Define **Tipping Point = Cost Parity Year**.

---

## 1️⃣ Determine Tipping Point

**Compare Cost Curves**
- Disruptor cost can be taken from EV cost data and Incumbent cost can be taken from ICE car cost data for a particular region
- Compare disruptor vs incumbent cost curves in real terms (same currency, same trim level or normalized basis).
- Apply a 3-year rolling median to smooth noisy cost curves before comparison.

**Forecasting Cost Curves**
- Cost curves must be forecasted before intersection analysis.  
- Steps to forecast each cost series:
  1. Convert the cost time series into logarithmic form: `log(cost)`.
  2. Compute the long-term CAGR (compound annual growth rate) on the log-transformed series.
  3. Forecast the log series forward using the computed CAGR until `end_year` or 2040.
  4. Convert the forecasted log series back to normal values using exponentiation.
  5. Combine historical and forecasted series for both disruptor and incumbent.

**Intersection Logic**
- If disruptor cost crosses below incumbent cost → tipping = first intersection year.  
- If disruptor is always cheaper → tipping = first year in historical series.  
- If incumbent is always cheaper → tipping = None (fall back to baseline or slow adoption).

---

## 2️⃣ Forecast Market Demand

- Start from historical dataset: `Passenger_Vehicle_Annual_Sales_<Region>`.
- Default forecast method: linear extrapolation to `end_year` (default 2040).
- Use a robust long-term slope (e.g., Theil–Sen or median regression).
- Enforce `market_fore(y) ≥ 0` for all years.
- Optionally, cap the annual CAGR between –5% and +5% to prevent unrealistic growth or decline.

---

## 3️⃣ Forecast Disruptor Sales (EV / BEV)

**Historical Share**
- Compute share = EV_sales / Market_sales (skip zero-market years).  
- If tipping is in the future, extend recent share trend linearly to tipping (clamped between 0 and 1).

**Post-Tipping Forecast**
- Fit a logistic curve on share trajectory:  
  `s(t) = L / (1 + exp(-k * (t - t₀)))`
- Default values:
  - L = 1.0 (100%) ceiling.  
  - k ∈ [0.05, 1.5].  
  - t₀ ∈ [min(years) - 5, max(years) + 10].  
- Use `scipy.optimize.differential_evolution` to fit k and t₀.  
- Convert share to absolute demand: `EV_fore(y) = share_fore(y) × market_fore(y)`.  
- Clamp to `[0, market_fore(y)]`.

---

## 4️⃣ Forecast Chimera Sales (PHEV)

- If a historical or external forecast exists → use it directly.  
- Otherwise, generate a “hump” trajectory:
  - Rising phase before tipping (up to tipping year).  
  - Decaying phase after tipping with half-life ≈ 3 years.  
  - Keep it continuous and smooth (avoid sharp drops or jumps).

---

## 5️⃣ Forecast Incumbent Sales (ICE)

- Compute as the residual:
  `ICE(y) = max(market_fore(y) - EV(y) - PHEV(y), 0)`

## 5️⃣ Forecast EV Car Sales (EV)

- Compute as the aggregated sales of BEV and PHEV:
  `EV(y) = BEV(y)+ PHEV(y)`
- Clamp to `[0, market_fore(y)]`

---

## 🚧 Watch Outs and Best Practices

**Data Consistency**
- Ensure all cost curves use the same basis: real USD, normalized for product configuration or cost per mile/km.  
- Use 3-year rolling medians to remove noise before intersection detection.

**Regional Logic**
- Treat each region separately.  
- Define “Rest of World (RoW)” as:  
  RoW = World − (China + USA + Europe).

**Numerical and Logical Stability**
- Clamp all shares to [0, 1] and all forecasts to ≥ 0.  
- Ensure EV + PHEV + ICE ≤ Market (+ small epsilon).  
- If history is too sparse (<3 points), seed logistic parameters with:
  - k = 0.4  
  - t₀ = tipping_year  
- If convergence fails, fall back to a linear trend (bounded by market forecast).

**Adoption Ceilings**
- Use L < 1.0 (e.g., 0.9) if physical, infrastructure, or policy limits exist by 2040.

---

## 🧩 Recommended Defaults

- Forecast horizon: 2040 (if unspecified).  
- Logistic ceiling L: 1.0 (100%) or 0.9 if constrained.  
- Logistic slope bounds: 0.05–1.5.  
- Chimera decay half-life: 3 years after tipping.  
- Market CAGR cap: ±5% per year.  
- Cost curve smoothing window: 3 years (rolling median).

---

## 6️⃣ Expected Outputs

Each run should generate the following outputs for the specified region:

1. **Cost Data (historical + forecasted)**  
   - Disruptor and Incumbent cost series in real USD.  
   - Forecasts generated via log-CAGR extrapolation method.  
   - Includes tipping point detection logic based on intersection.

2. **Demand Data (historical + forecasted)**  
   - Market demand (total passenger vehicle sales).  
   - Disruptor demand (BEV).  
   - Incumbent demand (ICE).  
   - Chimera demand (PHEV, if applicable).
   - EV demand (BEV+PHEV)

3. **Tipping Point (year)**  
   - Year where disruptor cost < incumbent cost for the first time.  
   - Used to anchor logistic growth transition for disruptor and chimera demand.

4. **If Region == Global**  
   - Perform analysis for all individual regions
   - Individual regions level cost and demand datasets and tipping points
   - Aggregated demand level datasets for global region

---

## Example Flow Summary

1. Select region (e.g., China).  
2. Forecast cost curves for EV and ICE using log-CAGR method.  
3. Compute tipping = first intersection year of EV vs ICE cost curves.  
4. Forecast market demand using linear extrapolation.  
5. Compute EV historical share and fit logistic curve to project future EV sales.  
6. Use PHEV forecast (from data or hump model).  
7. Derive ICE = Market − EV − PHEV.  
8. Validate:
   - EV + PHEV + ICE ≤ Market  
   - No negative values  
   - Smooth transitions near tipping year.
