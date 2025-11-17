# Validation Framework

## Contents
- Validation Approach
- Direct Demand Comparison
- Stock-Flow Consistency
- Quality Checks
- Validation Datasets
- Interpreting Variance Results

---

## Validation Approach

The skill implements a comprehensive validation framework to ensure forecast accuracy and reliability. Validation occurs at multiple levels:

1. **Direct Demand Comparison**: Compare bottom-up calculations against validation datasets
2. **Stock-Flow Consistency**: Verify installed base evolution follows accounting identity
3. **Quality Checks**: Flag anomalies and apply smoothing
4. **Parameter Bounds**: Ensure coefficients remain realistic

---

## Direct Demand Comparison

Bottom-up demand calculations are compared against independent validation datasets.

**Target Variance**: <10% (excellent alignment)

**Formula**:
```
Variance (%) = 100 × (Bottom_Up_Demand - Validation_Demand) / Validation_Demand
```

**Vehicle Types Validated**:
- **Passenger Cars**: OEM and Replacement demand
- **Two-Wheelers**: OEM and Replacement demand
- **Three-Wheelers**: OEM and Replacement demand

**Note**: Commercial vehicles typically lack validation datasets due to data limitations.

**Variance Interpretation**:
- **<10%**: Excellent - methodology is well-calibrated
- **10-30%**: Acceptable - minor coefficient adjustments may help
- **30-50%**: Moderate concern - review data quality and parameters
- **>50%**: High concern - investigate methodology, trigger calibration

---

## Stock-Flow Consistency

The installed base evolution must satisfy the accounting identity:

```
IB(t+1) = IB(t) + Adds(t) - Scrappage(t)
```

Where:
- **IB(t)**: Installed base at time t
- **Adds(t)**: New vehicle sales in year t
- **Scrappage(t)**: Vehicles removed from fleet = IB(t) / Life_Asset

**Validation Steps**:
1. Initialize IB using historical fleet data (warm-up period)
2. For each year, calculate expected IB based on adds and scrappage
3. Verify calculated IB matches input fleet data (when available)
4. Flag discrepancies >5%

---

## Quality Checks

### Non-Negativity Constraints
All demand values must be ≥ 0. Negative values indicate:
- Data errors (negative sales)
- Parameter mismatches (wrong coefficients)
- Logic errors (incorrect formulas)

### Growth Rate Checks
Year-over-year growth >20% triggers diagnostic reporting:
```
Growth Rate (%) = 100 × (Demand(t) - Demand(t-1)) / Demand(t-1)
```

**Causes of High Growth**:
- Sudden market expansion (legitimate)
- Data discontinuities (check source data)
- Parameter changes (review config.json)

### Smoothing Application
3-year rolling median applied to final outputs to reduce volatility:
```
Smoothed_Demand(t) = median(Demand(t-1), Demand(t), Demand(t+1))
```

**Benefits**:
- Reduces impact of single-year anomalies
- Produces smoother trend lines
- More realistic for long-term planning

---

## Validation Datasets

### Passenger Cars
- **OEM Validation**: `Lead_Annual_Implied_Demand-Sales_Cars`
  - Direct measurement of lead in new car batteries
  - Compares against bottom-up OEM calculation

- **Replacement Validation**: `Lead_Annual_Implied_Demand-Vehicle_replacement_Cars`
  - Contestable replacement market data
  - Compares against IB-based replacement calculation

### Two-Wheelers
- **OEM Validation**: `Lead_Annual_Implied_Demand-Sales_2W`
- **Replacement Validation**: `Lead_Annual_Implied_Demand-Vehicle_replacement_2W`

### Three-Wheelers
- **OEM Validation**: `Lead_Annual_Implied_Demand-Sales_3W`
- **Replacement Validation**: `Lead_Annual_Implied_Demand-Vehicle_replacement_3W`

### Industrial Batteries
- **Aggregate Fallback**: When detailed IB modeling unavailable
  - `Lead_Annual_Implied_Demand-Industrial_batteries_motive_power_Global`
  - `Lead_Annual_Implied_Demand-Industrial_batteries_stationary_Global`

---

## Interpreting Variance Results

### High Positive Variance (+)
**Bottom-up > Validation**

Possible causes:
- Lead coefficients too high (overestimating kg/unit)
- Double-counting in bottom-up calculation
- Validation dataset underestimates market

**Actions**:
1. Review lead coefficient sources (see `evidence_register.py`)
2. Run `calibrate_coefficients.py` to auto-adjust
3. Check for data quality issues in validation dataset

### High Negative Variance (-)
**Bottom-up < Validation**

Possible causes:
- Lead coefficients too low
- Missing vehicle segments in bottom-up calculation
- Battery lifetime too long (underestimating replacement frequency)

**Actions**:
1. Verify all vehicle types included (ICE, BEV, PHEV, etc.)
2. Review battery lifetime assumptions (default: 4.5 years for SLI)
3. Run calibration to increase coefficients

### Regional Differences
Variance may vary by region due to:
- Market structure differences (OEM vs aftermarket dominance)
- Battery technology variations (tropical vs temperate climates)
- Data availability and quality

**Best Practice**: Accept variance <30% for developing markets where data is limited.

---

## Using Validation Outputs

### Generate QA Report
```bash
python3 scripts/qa_report.py --results output/lead_demand_forecast_Global_baseline.csv \
                              --output output/qa_report.txt
```

The QA report includes:
- Variance summary table (by vehicle type and demand type)
- Parameter table with sources
- Forecast summary statistics

### Run Calibration Loop
When variance >threshold:
```bash
# Step 1: Generate forecast
python3 scripts/forecast.py --region Global --scenario baseline

# Step 2: Review variance in output CSV (check *_variance_pct columns)

# Step 3: Auto-calibrate if variance >10%
python3 scripts/calibrate_coefficients.py --results output/lead_demand_forecast_Global_baseline.csv \
                                           --threshold 10.0 \
                                           --adjustment-factor 0.5

# Step 4: Re-run forecast with calibrated parameters
python3 scripts/forecast.py --region Global --scenario baseline

# Step 5: Verify improved variance
```

### Historical Back-Testing
Test forecast accuracy on past data:
```bash
python3 scripts/backcast.py --region Global --scenario baseline \
                             --output-report output/backcast_report.txt
```

Metrics calculated:
- **MAPE**: Mean Absolute Percentage Error
- **MAE**: Mean Absolute Error
- **RMSE**: Root Mean Square Error
- **R²**: Coefficient of determination
- **Bias**: Systematic over/under-estimation

---

## Lead Content Consistency

Coefficients should align with industry literature:

**Passenger Cars**:
- ICE: 10-13 kg (skill uses 11.5)
- BEV: 8-10 kg (skill uses 9.0)
- PHEV: 9-12 kg (skill uses 10.5 fallback)

**Two-Wheelers**:
- ICE: 2-3 kg (skill uses 2.5)
- EV: 1.5-2 kg (skill uses 1.8)

**Commercial Vehicles**:
- ICE: 20-25 kg (skill uses 22.0)

If calibration pushes coefficients outside these ranges, investigate root causes rather than accepting unrealistic values.
