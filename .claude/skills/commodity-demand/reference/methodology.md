# Commodity Demand Forecasting Methodology

## Overview

This document describes the algorithms and methods used to forecast commodity demand driven by product sales and component replacement cycles.

## Core Calculation Framework

Commodity demand comes from two sources:

```
Total_Demand(year) = New_Sales_Demand(year) + Replacement_Demand(year)
```

### 1. New Sales Demand

New sales demand represents commodity requirements for newly manufactured products.

**Formula:**
```
New_Sales_Demand(year) = Product_Units_Sold(year) × Intensity_Factor
```

**Where:**
- `Product_Units_Sold(year)` = Number of product units sold in that year
- `Intensity_Factor` = Quantity of commodity per product unit (e.g., kg copper per EV)

**Example: Copper demand from new EV sales**
```
Year: 2030
EV Sales: 20 million vehicles
Copper Intensity: 80 kg/vehicle

Copper Demand = 20,000,000 × 80 = 1,600,000,000 kg = 1.6 million tonnes
```

### 2. Replacement Demand

Replacement demand represents commodity requirements for replacing components in the existing installed base.

**Formula:**
```
Replacement_Demand(year) = Installed_Base(year) × Replacement_Rate × Intensity_Factor
```

**Where:**
- `Installed_Base(year)` = Number of product units in operation
- `Replacement_Rate` = 1 / Component_Lifetime (e.g., 1/3.5 = 0.286 for 3.5-year battery life)
- `Intensity_Factor` = Quantity of commodity per component

**Example: Lead demand from ICE battery replacements**
```
Year: 2030
ICE Fleet: 1 billion vehicles
Battery Lifetime: 3.5 years
Replacement Rate: 1/3.5 = 0.286 per year
Lead per Battery: 12 kg

Replacement Demand = 1,000,000,000 × 0.286 × 12 = 3,432,000,000 kg = 3.4 million tonnes
```

## Installed Base Calculation

The installed base represents the active fleet of products currently in use.

**Formula:**
```
Installed_Base(year) = Cumulative_Sales(year) - Cumulative_Retirements(year)
```

**Where:**
```
Cumulative_Sales(year) = Sum of all sales from start through current year
Cumulative_Retirements(year) = Sum of all retirements through current year
```

**Retirement Logic:**
Products retire after their useful lifetime. For a product sold in year Y with lifetime L:
```
Retirement_Year = Y + L
```

**Example:**
```
Vehicle sold in 2015
Vehicle lifetime: 15 years
Retirement year: 2015 + 15 = 2030
```

**Algorithm:**
```python
installed_base = []
for year in years:
    cumulative_sales = sum(sales up to this year)
    retirement_year = year - lifetime

    if retirement_year >= start_year:
        cumulative_retirements = sum(sales up to retirement_year)
    else:
        cumulative_retirements = 0

    installed_base.append(cumulative_sales - cumulative_retirements)
```

## Product Demand Estimation

### Option A: Use Pre-Computed Product Forecasts

If product forecast files are provided (from the `product-demand` skill), load them directly:

```python
forecast_path = f"{forecasts_dir}/{product}_{region}.json"
with open(forecast_path) as f:
    product_demand = json.load(f)['forecast']['demand']
```

This provides the most accurate estimates because they incorporate:
- Cost-driven tipping point analysis
- Logistic S-curve adoption modeling
- Market disruption dynamics

### Option B: Simplified Internal Estimation

If no pre-computed forecasts are available, use lightweight linear extrapolation:

1. Load historical product demand data
2. Calculate trend using Theil-Sen robust regression
3. Extrapolate linearly to end year
4. Apply CAGR bounds (±5%) to prevent unrealistic growth

**Note:** This method is faster but less accurate for markets undergoing disruption.

## Aggregation Across Products

For each commodity, aggregate demand from all contributing products:

```
Total_Demand(year) = Σ (New_Sales_Demand_i(year) + Replacement_Demand_i(year))
                     for all products i
```

**Example: Total copper demand**
```
Sources:
- EV_Cars: 800,000 tonnes
- Commercial_EV: 150,000 tonnes
- Solar_PV: 300,000 tonnes
- Wind: 200,000 tonnes

Total Copper Demand = 1,450,000 tonnes
```

## Peak Detection

Peak demand year is identified as:
```
Peak_Year = year with max(Total_Demand)
```

**Algorithm:**
```python
peak_year = years[np.argmax(demand_values)]
```

## Validation Checks

### 1. Non-Negativity
All demand values must be ≥ 0.

```python
assert all(d >= 0 for d in demand), "Negative demand detected"
```

### 2. Smooth Transitions
Year-over-year changes should not exceed 100% (doubling).

```python
for i in range(1, len(demand)):
    if demand[i-1] > 0:
        change_rate = abs((demand[i] - demand[i-1]) / demand[i-1])
        if change_rate > 1.0:
            warnings.append(f"Large jump at year {years[i]}: {change_rate*100:.1f}%")
```

### 3. Physical Plausibility
- Intensity factors should match engineering specifications
- Replacement cycles should align with typical product lifetimes
- Total demand should not exceed global production capacity (when known)

## Intensity Factor Derivation

Intensity factors are derived from:

1. **Engineering specifications**: Bill of materials for products
2. **Industry reports**: Average material content per unit
3. **Academic studies**: Life cycle assessments
4. **Manufacturer data**: Component specifications

**Example: Copper in EVs**
- Electric motor: 20-25 kg
- Battery wiring: 15-20 kg
- Power electronics: 10-15 kg
- Charging system: 5-10 kg
- Other wiring: 20-30 kg
**Total: 70-100 kg, average 80 kg**

## Replacement Cycle Modeling

Replacement cycles vary by component and application:

### Battery Systems
- **EV batteries**: 10-15 years (or 150,000-200,000 miles)
- **ICE starter batteries**: 3-4 years
- **UPS batteries**: 5-8 years

### Other Components
- **Motors**: 15-20 years
- **Inverters**: 10-15 years
- **Wiring harnesses**: Vehicle lifetime (no replacement)

**Note:** Early retirements due to failure are averaged into the replacement cycle duration.

## Limitations

1. **No feedback loops**: Commodity price changes from demand shifts are not modeled
2. **Fixed intensity factors**: Assumes constant material content over time (ignores lightweighting trends)
3. **Simplified product forecasts**: Internal estimation doesn't capture disruption dynamics
4. **No recycling**: Secondary supply from recycled materials is not included
5. **Regional aggregation**: Global totals aggregate regions independently

## Future Enhancements

Potential improvements to the methodology:

1. **Recycling integration**: Model secondary supply from end-of-life products
2. **Dynamic intensity factors**: Trend intensity over time (e.g., reducing cobalt in batteries)
3. **Price elasticity**: Incorporate demand response to commodity price changes
4. **Technology substitution**: Model switching to alternative materials (e.g., aluminum for copper)
5. **Regional supply constraints**: Cap demand at regional production capacity
