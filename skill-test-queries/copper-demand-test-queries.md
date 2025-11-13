# Copper Demand Skill - Test Queries

## Overview
Test queries to validate the copper-demand forecasting skill functionality and demonstrate various use cases.

---

## Query 1: Basic Global Forecast
**Query**: "Forecast global copper demand through 2045 using the baseline scenario"
**Expected**:
- Total copper demand projection from 2024-2045
- Breakdown by major segments (Automotive, Grid, Construction, Industrial, Electronics, Other)
- Confidence levels for each segment

---

## Query 2: EV Impact Analysis
**Query**: "What is the impact of electric vehicle adoption on copper demand? Show me how BEV penetration affects automotive copper consumption"
**Expected**:
- Comparison of copper intensity: BEV (83 kg) vs ICE (23 kg) vehicles
- Automotive copper demand growth trajectory
- EV demand as percentage of total copper consumption

---

## Query 3: Renewable Energy Copper Requirements
**Query**: "Calculate copper demand from wind and solar capacity additions for 2025-2030"
**Expected**:
- Wind (onshore/offshore) copper demand in tonnes
- Solar PV copper demand in tonnes
- Grid generation-linked copper as % of total
- Validation against renewable percentage datasets

---

## Query 4: Regional Analysis - China
**Query**: "Analyze copper demand for China region specifically, focusing on construction and industrial segments"
**Expected**:
- China-specific copper consumption forecast
- Construction segment demand (top-down allocation)
- Industrial segment demand
- Regional share of global demand

---

## Query 5: Green Transition Scenario
**Query**: "Run an accelerated green transition scenario with 90% EV adoption and 20 TW renewables by 2045"
**Expected**:
- Elevated copper demand (+20-30% vs baseline)
- Dominant share from automotive and grid segments
- "Green copper" (EV+Solar+Wind) trajectory
- Peak demand year identification

---

## Query 6: Segment Reconciliation Validation
**Query**: "Validate that all segment demands sum to total consumption with proper reconciliation"
**Expected**:
- Sum of all segments = Total consumption (±0.1%)
- Transportation share validation (±2%)
- Electrical share validation (±5%)
- Reconciliation adjustments applied to TIER 2 segments only

---

## Query 7: Two-Tier Methodology Comparison
**Query**: "Compare TIER 1 bottom-up calculations (automotive, grid generation) with TIER 2 top-down allocations (construction, industrial)"
**Expected**:
- HIGH confidence tags for bottom-up segments
- LOW/MEDIUM confidence for allocated segments
- Data availability status for each tier
- Methodological differences explained

---

## Query 8: Copper Intensity Coefficients
**Query**: "Show me the copper intensity coefficients for all vehicle types and powertrains"
**Expected**:
- Passenger cars: ICE (23 kg), BEV (83 kg), PHEV (60 kg), HEV (35 kg)
- Commercial vehicles: ICE (35 kg), EV (120 kg), NGV (38 kg)
- Two-wheelers: ICE (3 kg), EV (4 kg)
- Three-wheelers: ICE (4 kg), EV (5 kg)

---

## Query 9: Substitution Risk Analysis
**Query**: "Model aluminum substitution risk with 15% reduction in grid/construction copper intensity"
**Expected**:
- Baseline vs substitution scenario comparison
- Impact on total demand (-10 to -15%)
- Price ratio threshold (Cu/Al > 3.5)
- Segments most vulnerable to substitution

---

## Query 10: Historical Validation Back-test
**Query**: "Validate the model against historical copper consumption data from 2020-2023"
**Expected**:
- Calculated vs actual consumption comparison
- Segment share alignment with reference percentages
- Growth rate consistency check
- Model calibration recommendations

---

## Additional Test Cases

### Error Handling
- Test with missing vehicle sales data
- Test with invalid year ranges
- Test with conflicting parameters

### Performance
- Large date range (25+ years)
- Multiple regions simultaneously
- High-frequency scenario comparisons

### Edge Cases
- Zero EV adoption scenario
- 100% renewable grid scenario
- Extreme price volatility impacts