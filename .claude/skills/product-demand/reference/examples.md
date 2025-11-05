# Product Demand Forecasting - Usage Examples

## Overview

This document provides practical examples for using the product demand forecasting skill across different use cases and product types.

---

## Table of Contents

1. [Basic Usage](#1-basic-usage)
2. [Passenger Vehicle Forecasts](#2-passenger-vehicle-forecasts)
3. [Energy Generation Forecasts](#3-energy-generation-forecasts)
4. [Commercial Vehicle Forecasts](#4-commercial-vehicle-forecasts)
5. [Two-Wheeler and Three-Wheeler Forecasts](#5-two-wheeler-and-three-wheeler-forecasts)
6. [Programmatic Usage](#6-programmatic-usage)
7. [Advanced Scenarios](#7-advanced-scenarios)
8. [Interpreting Results](#8-interpreting-results)

---

## 1. Basic Usage

### Command Line Interface

#### Forecast EV demand in China through 2040

```bash
cd .claude/skills/product-demand
python3 scripts/product_forecast.py \
  --product EV_Cars \
  --region China \
  --end-year 2040 \
  --output both
```

**Output**:
- `output/EV_Cars_China_2040.csv`
- `output/EV_Cars_China_2040.json`

#### Using the wrapper script

```bash
cd .claude/skills/product-demand
./run_forecast.sh --product EV_Cars --region China --end-year 2040
```

---

## 2. Passenger Vehicle Forecasts

### Example 2.1: BEV Adoption in USA

**Question**: When will BEVs reach 50% market share in the USA?

```bash
python3 scripts/product_forecast.py \
  --product BEV_Cars \
  --region USA \
  --end-year 2045 \
  --output json
```

**Expected Output Structure**:
```json
{
  "product": "BEV_Cars",
  "region": "USA",
  "product_type": "disruptor",
  "market_context": {
    "disrupted": true,
    "tipping_point": 2026
  },
  "forecast": {
    "years": [2015, 2016, ..., 2045],
    "demand": [120000, 180000, ..., 8500000],
    "shares": [0.01, 0.02, ..., 0.68],
    "market": [17500000, 17600000, ..., 12500000],
    "method": "logistic",
    "logistic_params": {
      "L": 1.0,
      "k": 0.42,
      "t0": 2029
    }
  }
}
```

**Interpretation**:
- Tipping point (cost parity): 2026
- 50% share reached: ~2032 (6 years post-tipping)
- Logistic k=0.42 indicates ~11 year adoption window (10% to 90%)

---

### Example 2.2: PHEV (Chimera) Trajectory in Europe

**Question**: What is the PHEV adoption trajectory in Europe?

```bash
python3 scripts/product_forecast.py \
  --product PHEV_Cars \
  --region Europe \
  --end-year 2040 \
  --output csv
```

**Sample CSV Output**:
```csv
Year,Demand,Market
2018,45000,15000000
2020,120000,14500000
2022,250000,14800000
2025,680000,14600000  # Pre-tipping growth
2028,420000,14200000  # Post-tipping decay begins
2031,180000,13800000  # Half of peak
2034,78000,13500000   # Declining rapidly
2040,15000,13200000   # Minimal share
```

**Interpretation**:
- PHEVs peak around tipping point (~2025-2028)
- Decay half-life of 3 years
- By 2040, <1% market share (niche use cases only)

---

### Example 2.3: ICE Vehicle Decline (Incumbent as Residual)

**Question**: When does ICE passenger vehicle demand peak in China?

```bash
python3 scripts/product_forecast.py \
  --product ICE_Cars \
  --region China \
  --end-year 2040 \
  --output both
```

**Key Output Fields**:
```json
{
  "forecast": {
    "method": "residual",
    "years": [2010, 2011, ..., 2040],
    "demand": [..., 24000000, 21000000, ..., 1200000],
    "disruptor_total": [..., 2000000, 5000000, ..., 22000000],
    "chimera_total": [..., 800000, 1500000, ..., 50000]
  }
}
```

**Interpretation**:
- ICE demand peaks when EV+PHEV growth accelerates post-tipping
- Residual calculation: ICE = Market - EV - PHEV
- By 2040, ICE becomes <10% of market

---

### Example 2.4: Total Passenger Vehicle Market

**Question**: What is total passenger vehicle market demand in China?

```bash
python3 scripts/product_forecast.py \
  --product Passenger_Vehicles \
  --region China \
  --end-year 2040 \
  --output json
```

**Expected Output**:
```json
{
  "product_type": "market",
  "forecast": {
    "method": "linear_bounded",
    "max_cagr": 0.05,
    "years": [2010, ..., 2040],
    "demand": [15000000, ..., 28000000]
  }
}
```

**Interpretation**:
- Market grows at capped rate (±5% CAGR)
- No disruption logic (market is sum of all products)
- Used as denominator for share calculations

---

## 3. Energy Generation Forecasts

### Example 3.1: Solar PV Capacity Growth in USA

**Question**: When will solar PV reach 1 TW (1000 GW) in USA?

```bash
python3 scripts/product_forecast.py \
  --product Solar_PV \
  --region USA \
  --end-year 2045 \
  --output json
```

**Sample Output**:
```json
{
  "forecast": {
    "years": [2010, ..., 2045],
    "demand": [5, 10, 25, 50, 100, 200, 450, 800, 1100],
    "method": "logistic"
  }
}
```

**Interpretation**:
- Solar crosses 1 TW around 2040-2042
- Exponential growth post-tipping (cost < coal/gas)
- Units: GW of annual installed capacity

---

### Example 3.2: Coal Power Decline in China

**Question**: When does coal-fired power generation peak in China?

```bash
python3 scripts/product_forecast.py \
  --product Coal_Power \
  --region China \
  --end-year 2045 \
  --output csv
```

**Sample CSV Output**:
```csv
Year,Demand,Market
2015,3900,5200  # TWh
2020,4200,6100
2025,4500,6800  # Peak around here
2030,3800,7200  # Decline begins
2035,2400,7600
2040,1200,8000
2045,400,8400   # Residual baseload only
```

**Interpretation**:
- Coal peaks mid-2020s as solar+wind+battery scales
- Rapid decline post-peak (halves every ~5 years)
- By 2045, <5% of generation (residual inflexible plants)

---

## 4. Commercial Vehicle Forecasts

### Example 4.1: Commercial EV Adoption in Europe

**Question**: What is the commercial EV adoption rate in Europe?

```bash
python3 scripts/product_forecast.py \
  --product Commercial_EV \
  --region Europe \
  --end-year 2040 \
  --output both
```

**Expected Behavior**:
- Slower adoption than passenger EVs (k ≈ 0.2-0.3)
- Longer logistic window (15-20 years from 10% to 90%)
- Fleet turnover cycles matter

---

## 5. Two-Wheeler and Three-Wheeler Forecasts

### Example 5.1: EV Two-Wheeler in India

**Question**: When will EV two-wheelers dominate the Indian market?

```bash
python3 scripts/product_forecast.py \
  --product EV_Two_Wheeler \
  --region India \
  --end-year 2040 \
  --output json
```

**Notes**:
- India-specific region code used
- Two-wheelers have very fast adoption (k > 0.5) due to lower cost barriers
- Potential for L < 1.0 due to rural infrastructure limits

---

## 6. Programmatic Usage

### Example 6.1: Batch Forecasting Multiple Products

```python
import sys
import os
sys.path.insert(0, '.claude/skills/product-demand/scripts')

from product_forecast import ProductForecaster

products = ['EV_Cars', 'PHEV_Cars', 'ICE_Cars']
region = 'China'
end_year = 2040

results = {}
for product in products:
    forecaster = ProductForecaster(product, region, end_year)
    results[product] = forecaster.forecast()

# Analyze results
ev_peak_year = results['EV_Cars']['market_context']['tipping_point']
ice_peak_demand = max(results['ICE_Cars']['forecast']['demand'])

print(f"EV tipping point: {ev_peak_year}")
print(f"ICE peak demand: {ice_peak_demand:,.0f} vehicles")
```

---

### Example 6.2: Custom Configuration

```python
import json
from product_forecast import ProductForecaster

# Load config
with open('config.json') as f:
    config = json.load(f)

# Modify parameters for scenario analysis
config['default_parameters']['logistic_ceiling'] = 0.85  # 85% max EV share
config['default_parameters']['market_cagr_cap'] = 0.03   # Conservative market

# Save modified config
with open('config_scenario.json', 'w') as f:
    json.dump(config, f, indent=2)

# Run forecast with custom config
forecaster = ProductForecaster(
    'EV_Cars', 'USA', 2040,
    config_path='config_scenario.json'
)
result = forecaster.forecast()
```

---

## 7. Advanced Scenarios

### Example 7.1: Sensitivity Analysis on Logistic Ceiling

**Question**: How sensitive is the forecast to the maximum EV adoption share?

```bash
# Scenario 1: 100% EV adoption possible
python3 scripts/product_forecast.py \
  --product EV_Cars --region USA --end-year 2040 --output json

# Scenario 2: Edit config.json to set logistic_ceiling = 0.90
# Then rerun
```

**Analysis**:
Compare final year (2040) demand:
- L=1.0: 14M EVs (93% share)
- L=0.9: 13.5M EVs (90% share, capped)

---

### Example 7.2: Regional Comparison

**Question**: Compare EV adoption speeds across regions

```bash
for region in China USA Europe Rest_of_World; do
  python3 scripts/product_forecast.py \
    --product EV_Cars \
    --region $region \
    --end-year 2040 \
    --output csv
done

# Analyze tipping points and k values from JSON outputs
```

**Expected Findings**:
- **China**: Earliest tipping point (2023-2025), fastest adoption (k ≈ 0.5)
- **Europe**: Mid tipping point (2025-2027), moderate adoption (k ≈ 0.4)
- **USA**: Later tipping point (2026-2028), moderate adoption (k ≈ 0.35)
- **Rest_of_World**: Latest tipping point (2028-2030), slower adoption (k ≈ 0.25)

---

## 8. Interpreting Results

### Understanding JSON Output

#### Key Field: `market_context`

```json
"market_context": {
  "disrupted": true,
  "tipping_point": 2026,
  "disruptor_products": ["EV_Cars", "BEV_Cars"],
  "incumbent_products": ["ICE_Cars"],
  "chimera_products": ["PHEV_Cars"],
  "market_product": "Passenger_Vehicles"
}
```

**Interpretation**:
- **disrupted=true**: Market has active disruption dynamics
- **tipping_point=2026**: Cost parity year (EV cost < ICE cost)
- Product classification determines forecasting method

---

#### Key Field: `forecast`

```json
"forecast": {
  "years": [2015, ..., 2040],
  "demand": [120000, ..., 15000000],
  "shares": [0.01, ..., 0.85],
  "market": [17500000, ..., 14500000],
  "method": "logistic",
  "tipping_point": 2026,
  "logistic_params": {"L": 1.0, "k": 0.42, "t0": 2029}
}
```

**Field Descriptions**:
- **years**: Time axis (annual)
- **demand**: Product-specific demand (units/year)
- **shares**: Product share of market (0.0-1.0)
- **market**: Total market size (all products)
- **method**: Algorithm used (logistic, chimera_hump, residual, etc.)
- **logistic_params**: S-curve parameters (if applicable)

---

#### Key Field: `validation`

```json
"validation": {
  "is_valid": true,
  "warnings": [
    "Large year-over-year changes detected in 2027-2028"
  ],
  "errors": []
}
```

**Interpretation**:
- **is_valid=true**: Forecast passed all checks
- **warnings**: Non-critical issues (review recommended)
- **errors**: Critical failures (forecast may be unreliable)

---

### Calculating Key Metrics from Output

#### When does product reach X% market share?

```python
import json

with open('output/EV_Cars_China_2040.json') as f:
    result = json.load(f)

years = result['forecast']['years']
shares = result['forecast']['shares']

# Find year when share crosses 50%
for year, share in zip(years, shares):
    if share >= 0.50:
        print(f"50% share reached in {year}")
        break
```

#### What is the CAGR between two years?

```python
import numpy as np

demand = np.array(result['forecast']['demand'])
years = np.array(result['forecast']['years'])

idx_2025 = list(years).index(2025)
idx_2035 = list(years).index(2035)

cagr = (demand[idx_2035] / demand[idx_2025]) ** (1/10) - 1
print(f"CAGR (2025-2035): {cagr:.2%}")
```

#### When does demand peak?

```python
demand = result['forecast']['demand']
years = result['forecast']['years']

peak_idx = demand.index(max(demand))
peak_year = years[peak_idx]
peak_demand = demand[peak_idx]

print(f"Demand peaks in {peak_year} at {peak_demand:,.0f} units")
```

---

### Visualizing Results

#### Using pandas and matplotlib

```python
import pandas as pd
import matplotlib.pyplot as plt
import json

# Load forecast
with open('output/EV_Cars_China_2040.json') as f:
    result = json.load(f)

# Create DataFrame
df = pd.DataFrame({
    'Year': result['forecast']['years'],
    'EV_Demand': result['forecast']['demand'],
    'Market': result['forecast']['market'],
    'EV_Share': result['forecast']['shares']
})

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Demand plot
ax1.plot(df['Year'], df['EV_Demand'], label='EV Demand', linewidth=2)
ax1.plot(df['Year'], df['Market'], label='Total Market', linewidth=2, linestyle='--')
ax1.set_xlabel('Year')
ax1.set_ylabel('Annual Sales (vehicles)')
ax1.set_title('EV Demand vs Total Market - China')
ax1.legend()
ax1.grid(alpha=0.3)

# Share plot
ax2.plot(df['Year'], df['EV_Share'] * 100, color='green', linewidth=2)
ax2.axhline(50, color='red', linestyle='--', label='50% Share')
ax2.set_xlabel('Year')
ax2.set_ylabel('EV Market Share (%)')
ax2.set_title('EV Market Penetration - China')
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('output/ev_forecast_china.png', dpi=150)
plt.show()
```

---

## Common Questions

### Q1: Why is my forecast showing zero demand after a certain year?

**Answer**: This typically happens for incumbent products when disruptors fully capture the market. Check:
1. Logistic ceiling parameter (is L = 1.0?)
2. Market context (is product classified as "incumbent"?)
3. Residual calculation (is Market - Disruptor - Chimera < 0?)

**Solution**: If unrealistic, adjust logistic_ceiling to <1.0 to preserve niche market.

---

### Q2: My logistic fitting failed. What should I do?

**Answer**: Logistic fitting requires ≥3 historical data points with clear S-curve pattern. If failing:
1. Check data quality in entity JSON file
2. Verify tipping point exists (cost parity detected)
3. Review historical shares (are they monotonically increasing?)

**Fallback**: System automatically uses linear extrapolation if fitting fails.

---

### Q3: How do I forecast for "Global" region?

**Answer**: Global forecasts are computed by summing regional forecasts:

```bash
# Forecast each region
for region in China USA Europe Rest_of_World; do
  python3 scripts/product_forecast.py \
    --product EV_Cars --region $region --end-year 2040
done

# Then sum the outputs programmatically
```

---

### Q4: Can I override the tipping point year?

**Answer**: Tipping point is automatically detected from cost curves. To override, you would need to:
1. Modify cost curves in entity JSON file
2. Or manually specify in Python by modifying the `_get_market_context()` method

Not recommended unless you have strong justification.

---

## Next Steps

- Review [methodology.md](methodology.md) for algorithm details
- Check [parameters.md](parameters.md) for parameter tuning guidance
- Explore [data_schema.md](data_schema.md) for data format specifications

---

For more examples and updated use cases, see the skill's GitHub repository or documentation site.
