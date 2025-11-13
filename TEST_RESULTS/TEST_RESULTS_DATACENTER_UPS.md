# Datacenter UPS Skill - Test Results and Issues

**Date**: 2025-11-13
**Skill Version**: 1.0.0
**Test Suite**: skill-test-queries/datacenter-ups-test-queries.md

---

## Executive Summary

The datacenter-ups skill was tested against 10 comprehensive test queries covering TCO analysis, tipping point detection, S-curve adoption modeling, regional comparisons, and scenario analysis. The testing revealed **8 critical issues** and **5 missing features** that prevent the skill from meeting its stated objectives.

**Overall Status**: ❌ **FAILING** - Critical TCO calculation errors and missing core functionality

---

## Test Results Summary

| Query | Status | Severity | Summary |
|-------|--------|----------|---------|
| Query 1: TCO Comparison | ❌ FAIL | **CRITICAL** | TCO calculation error - Li-ion shows higher TCO but higher adoption |
| Query 2: Tipping Point | ⚠️ PARTIAL | **HIGH** | Tipping year identified (2020) but TCO logic contradicts adoption |
| Query 3: S-Curve Adoption | ✅ PASS | - | S-curve produces monotonic adoption curves |
| Query 4: Regional Comparison | ⚠️ PARTIAL | **MEDIUM** | Regional multipliers work but TCO issues persist |
| Query 5: Installed Base Evolution | ❌ FAIL | **CRITICAL** | No installed base tracking implemented |
| Query 6: Market Decomposition | ❌ FAIL | **CRITICAL** | New-build vs replacement segmentation missing |
| Query 7: Accelerated Scenario | ⚠️ PARTIAL | **MEDIUM** | Scenario works but produces identical results to baseline |
| Query 8: Battery Metrics | ❌ FAIL | **MEDIUM** | Metrics defined in config but not calculated or output |
| Query 9: BESS Cost Proxy | ⚠️ PARTIAL | **MEDIUM** | Proxy used but validation shows incorrect cost trajectories |
| Query 10: Replacement Cycle | ❌ FAIL | **CRITICAL** | Replacement demand not calculated |

**Pass Rate**: 10% (1/10 fully passing)
**Critical Issues**: 5
**High Issues**: 1
**Medium Issues**: 4

---

## Critical Issues

### 🔴 Issue #1: TCO Calculation Logic Error (CRITICAL)
**Affected Queries**: 1, 2, 4, 7, 9
**Severity**: CRITICAL
**Location**: `scripts/forecast.py:180-215` (calculate_tco method)

**Problem**:
The TCO calculation produces results that contradict the adoption behavior:
- **USA 2040**: VRLA TCO = $40.86/kWh, Li-ion TCO = $74.86/kWh (Li-ion is $34 MORE expensive)
- **Yet Li-ion has 95% market share!**
- **Europe 2040**: VRLA TCO = $46.27/kWh, Li-ion TCO = $80.75/kWh (Li-ion is $34.48 MORE expensive)
- **China 2040**: VRLA TCO = $37.25/kWh, Li-ion TCO = $5.22/kWh (Only China shows Li-ion cheaper)

**Expected Behavior** (from test spec):
- VRLA TCO: CapEx ($220/kWh) + OpEx ($18/kWh-yr) + Replacements (every 5 years)
- Li-ion TCO: Declining CapEx + OpEx ($6/kWh-yr) + Replacements (12-year life)
- Li-ion should achieve cost parity and then cost advantage over VRLA

**Root Cause Analysis**:
1. The TCO calculation appears to use the annual CapEx from cost forecast directly rather than amortizing it properly
2. Li-ion CapEx is showing $771/kWh in 2040 for USA (unrealistically high)
3. The cost forecast method `forecast_costs()` may be producing incorrect Li-ion cost trajectories
4. Replacement cost NPV calculations may not be working correctly

**Evidence**:
```
USA Baseline 2040:
- vrla_capex_per_kwh: $220.00
- lithium_capex_per_kwh: $771.39 (Should be declining, not increasing!)
- vrla_tco_per_kwh: $40.86
- lithium_tco_per_kwh: $74.86

USA Baseline 2020:
- vrla_capex_per_kwh: $220.00
- lithium_capex_per_kwh: $192.00
- vrla_tco_per_kwh: $40.86
- lithium_tco_per_kwh: $20.90

The Li-ion CapEx INCREASES from $192 (2020) to $771 (2040) - this is backwards!
```

**Impact**:
- All TCO-based decisions are unreliable
- The model cannot be used for investment or adoption planning
- Query 1 fails completely
- Queries 2, 4, 7, and 9 produce misleading results

**Recommended Fix**:
1. Review `forecast_costs()` method (lines 93-178) - the log-CAGR projection appears to be diverging
2. Check if historical BESS costs are being extrapolated correctly
3. Verify the NPV calculation in `calculate_tco()` properly accounts for:
   - Initial CapEx
   - Discounted OpEx over horizon
   - Discounted replacement CapEx at appropriate intervals
   - Amortization over TCO horizon
4. Add validation to ensure Li-ion costs decline over time (cap at historical maximum)

---

### 🔴 Issue #2: Li-ion CapEx Trajectory Explodes (CRITICAL)
**Affected Queries**: 1, 2, 7, 9
**Severity**: CRITICAL
**Location**: `scripts/forecast.py:116-178` (forecast_costs method)

**Problem**:
Li-ion CapEx costs INCREASE dramatically from 2020 to 2040 instead of declining:
- USA: $192/kWh (2020) → $771/kWh (2040) = **+302%** (WRONG!)
- Europe: $192/kWh (2020) → $771/kWh (2040) = **+302%** (WRONG!)
- Expected: Should decline from ~$200/kWh to ~$50-80/kWh by 2040

**Root Cause**:
The log-CAGR forecasting method in lines 124-157 appears to:
1. Either calculate the slope incorrectly (sign error?)
2. Or apply the decline rate in the wrong direction
3. The `adjusted_slope` calculation may be inverting the decline

**Evidence**:
```python
# From forecast output USA:
2020: lithium_capex = $192.00
2021: lithium_capex = $267.00 (+39%)
2022: lithium_capex = $397.00 (+49%)
2023: lithium_capex = $322.00 (-19%)
2024: lithium_capex = $234.00 (-27%)
2025: lithium_capex = $252.11 (+8%)
...
2040: lithium_capex = $771.39 (+206% from 2025)

This shows erratic behavior with an overall upward trend - opposite of expected decline.
```

**Impact**:
- Makes Li-ion appear uneconomical even though the model shows high adoption
- Completely undermines the TCO analysis
- Cannot model technology transitions accurately

**Recommended Fix**:
1. Add debugging to print the calculated slope and adjusted_slope values
2. Verify sign of `scenario_decline` (should be negative for cost decline)
3. Check if `max()` function is being used correctly - may need to compare absolute values
4. Add a sanity check: if projected cost > last historical cost, cap at historical maximum
5. Consider simpler approach: use constant annual decline rate rather than log-CAGR

**Code Section to Review**:
```python
# Lines 124-157 in forecast.py
slope = coeffs[0]  # This is the log-CAGR
scenario_decline = -self.scenario.get('lithium_cost_decline_rate', 0.08)
adjusted_slope = max(slope, scenario_decline)  # Don't increase costs
```

This logic seems backwards - if slope is positive (costs increasing historically) and scenario_decline is negative (e.g., -0.08), then max() will choose the positive slope, causing costs to increase!

**Should be**: `adjusted_slope = min(slope, scenario_decline)` to ensure costs decline

---

### 🔴 Issue #3: Missing Installed Base Tracking (CRITICAL)
**Affected Queries**: 5, 6, 10
**Severity**: CRITICAL
**Location**: `scripts/forecast.py` - Missing functionality

**Problem**:
Query 5 expected: "Track the installed base evolution of VRLA vs Li-ion batteries through 2035"
- Stock-flow accounting: IB(t+1) = IB(t) + Adds - Retirements
- Mass balance validation (±0.1%)

**Current State**:
- Data loader has `load_vrla_installed_base()` method (data_loader.py:95-103)
- Historical installed base data is loaded (data_loader.py:260)
- **BUT**: No installed base forecasting or tracking in forecast.py
- Output CSV has NO installed base columns (only demand flows)

**Missing Functionality**:
1. Installed base initialization (starting stocks)
2. Stock-flow dynamics (IB accumulation)
3. Technology-specific retirement calculations
4. Mass balance reconciliation
5. Output columns: `vrla_installed_base_mwh`, `lithium_installed_base_mwh`, `total_installed_base_mwh`

**Impact**:
- Cannot model replacement demand (Query 6, 10)
- Cannot track contestable market (VRLA reaching end-of-life)
- Cannot validate demand forecasts with stock-flow consistency
- Missing critical output specified in config.json lines 133-137

**Recommended Implementation**:
```python
def forecast_installed_base(self):
    """Track installed base evolution with stock-flow accounting"""
    vrla_ib = []
    lithium_ib = []

    # Initialize from historical data
    vrla_ib_t = self.hist_vrla_installed_base.get(self.start_year, 0)
    lithium_ib_t = 0  # Start at zero (conservative)

    for i, year in enumerate(self.years):
        # Retirements = IB / Lifespan (simplified)
        vrla_retirements = vrla_ib_t / self.vrla_lifespan
        lithium_retirements = lithium_ib_t / self.lithium_lifespan

        # Additions = Annual demand
        vrla_adds = self.results['vrla_demand_gwh'].iloc[i]
        lithium_adds = self.results['lithium_demand_gwh'].iloc[i]

        # Update stocks
        vrla_ib_t = vrla_ib_t + vrla_adds - vrla_retirements
        lithium_ib_t = lithium_ib_t + lithium_adds - lithium_retirements

        vrla_ib.append(max(0, vrla_ib_t))
        lithium_ib.append(max(0, lithium_ib_t))

    self.results['vrla_installed_base_mwh'] = vrla_ib
    self.results['lithium_installed_base_mwh'] = lithium_ib
    self.results['total_installed_base_mwh'] = np.array(vrla_ib) + np.array(lithium_ib)
```

---

### 🔴 Issue #4: Missing Market Decomposition (CRITICAL)
**Affected Queries**: 6, 10
**Severity**: CRITICAL
**Location**: `scripts/forecast.py` - Missing functionality

**Problem**:
Query 6 expected: "Break down total datacenter UPS battery demand into new-build vs replacement segments"
- New-build demand from DC construction growth (7-10% annually)
- Replacement demand from installed base / lifetime
- Contestable market (VRLA at end-of-life)
- Technology split for each segment

**Current State**:
- Config.json specifies market decomposition (lines 61-65)
- Config.json specifies output columns for market segments (lines 138-142)
- **BUT**: No implementation in forecast.py
- No decomposition of demand into new-build vs replacement

**Missing Functionality**:
1. New-build demand calculation (from growth rates)
2. Replacement demand calculation (from installed base / lifespan)
3. Contestable market identification (VRLA reaching 5-year life)
4. Technology allocation for each segment
5. Output columns: `new_build_demand_mwh`, `replacement_demand_mwh`, `contestable_market_mwh`

**Impact**:
- Cannot analyze which segment drives Li-ion adoption (new builds vs replacements)
- Cannot model accelerated replacement scenarios
- Missing critical insight for market dynamics
- Cannot identify size of contestable market opportunity

**Recommended Implementation**:
```python
def decompose_market_demand(self):
    """Decompose total demand into new-build and replacement segments"""
    new_build = []
    replacement = []
    contestable = []

    for i, year in enumerate(self.years):
        if i == 0:
            # Base year: assume 70% replacement, 30% new-build
            total = self.results['total_demand_gwh'].iloc[i]
            new_build.append(total * 0.30)
            replacement.append(total * 0.70)
            contestable.append(0)
        else:
            # New-build from growth
            prev_total = self.results['total_demand_gwh'].iloc[i-1]
            growth = self.hist_growth_rates.get(year, 0.08)
            new_build_demand = prev_total * growth

            # Replacement from installed base retirements
            vrla_replacement = self.results['vrla_installed_base_mwh'].iloc[i-1] / self.vrla_lifespan
            lithium_replacement = self.results['lithium_installed_base_mwh'].iloc[i-1] / self.lithium_lifespan
            replacement_demand = vrla_replacement + lithium_replacement

            # Contestable = VRLA reaching end-of-life
            contestable_demand = vrla_replacement

            new_build.append(new_build_demand)
            replacement.append(replacement_demand)
            contestable.append(contestable_demand)

    self.results['new_build_demand_mwh'] = new_build
    self.results['replacement_demand_mwh'] = replacement
    self.results['contestable_market_mwh'] = contestable
```

**Note**: This requires Issue #3 (installed base tracking) to be fixed first.

---

### 🔴 Issue #5: Accelerated Scenario Produces Identical Results (HIGH)
**Affected Queries**: 7
**Severity**: HIGH
**Location**: `scripts/forecast.py:98-178, 217-268`

**Problem**:
Query 7 expected: "Accelerated transition scenario with faster Li-ion cost decline (12% annual) and early VRLA phase-out"
- Earlier tipping point (2-3 years advance)
- Steeper S-curve adoption (k × 1.5)
- 95%+ Li-ion market share by 2035

**Actual Results**:
Baseline vs Accelerated scenario for USA produce nearly IDENTICAL results:
- Baseline 2030: 94.4% Li-ion share, tipping point 2020
- Accelerated 2030: 95.0% Li-ion share, tipping point 2020
- **NO meaningful difference!**

**Root Cause**:
1. The Li-ion cost trajectory is broken (Issue #1, #2) so changing the decline rate has no effect
2. Tipping point is already at start year (2020) in baseline, so cannot be earlier
3. Adoption acceleration factor (1.5×) has minimal impact when starting at 47.5% share in 2020

**Evidence**:
```
USA Baseline 2040:
- Li-ion share: 95.0%
- VRLA TCO: $40.86, Li-ion TCO: $74.86
- Tipping year: 2020

USA Accelerated 2040:
- Li-ion share: 95.0%
- VRLA TCO: $40.86, Li-ion TCO: $74.86
- Tipping year: 2020

Identical results despite 12% vs 8% cost decline rate!
```

**Impact**:
- Scenario analysis is not functional
- Cannot model policy interventions or market shocks
- Cannot test sensitivity to cost assumptions

**Recommended Fix**:
1. Fix Issues #1 and #2 first (TCO and cost trajectory)
2. Verify scenario parameters are being applied correctly
3. Test with wider parameter ranges to ensure sensitivity
4. Consider resetting base year to earlier (e.g., 2015) when VRLA was dominant

---

## Medium Issues

### 🟡 Issue #6: Battery Metrics Not Calculated (MEDIUM)
**Affected Queries**: 8
**Severity**: MEDIUM
**Location**: `scripts/forecast.py` - Missing calculations

**Problem**:
Query 8 expected battery metrics calculations:
- Duration: 4 hours (default for UPS)
- Power capacity: 25 MW (Energy/Duration)
- Annual throughput: 25 TWh (250 cycles/year)
- Round-trip efficiency: 88%

**Current State**:
- Config.json defines battery_metrics (lines 66-71)
- **BUT**: No calculation or output of these metrics
- User cannot retrieve power capacity or throughput from results

**Missing Functionality**:
```python
def calculate_battery_metrics(self):
    """Calculate power, throughput, and efficiency metrics"""
    duration_h = self.config['battery_metrics']['duration_hours']
    cycles_per_year = self.config['battery_metrics']['cycles_per_year']
    rte = self.config['battery_metrics']['round_trip_efficiency']

    # Power capacity (MW) = Energy (MWh) / Duration (h)
    self.results['power_capacity_mw'] = self.results['total_demand_gwh'] * 1000 / duration_h

    # Annual throughput (MWh) = Energy capacity × Cycles per year
    self.results['annual_throughput_mwh'] = self.results['total_demand_gwh'] * 1000 * cycles_per_year
```

**Impact**:
- Users cannot convert energy capacity to power capacity
- Cannot estimate annual cycling throughput
- Minor issue but reduces usability

---

### 🟡 Issue #7: BESS Cost Proxy Not Validated (MEDIUM)
**Affected Queries**: 9
**Severity**: MEDIUM
**Location**: `scripts/forecast.py:135-178`

**Problem**:
Query 9 expected validation of using grid-scale BESS costs as proxy for UPS Li-ion costs:
- 4-hour duration match confirmation
- UPS reliability premium consideration (5-10%)
- Cycle life differences
- Directional trend validation

**Current State**:
- Config specifies `ups_reliability_premium: 1.0` (no premium applied!)
- No validation that BESS and UPS have similar 4-hour duration
- No cycle life adjustment
- Cost trajectories show INCREASE not decrease (invalid proxy)

**Issues**:
1. Reliability premium set to 1.0 (no adjustment) but config comments suggest 5-10%
2. No validation that proxy is appropriate
3. Cost trajectory showing increase suggests proxy is failing
4. No documentation of when proxy breaks down

**Recommended Fix**:
1. Set `ups_reliability_premium: 1.08` (8% premium) in config.json
2. Add validation method to check:
   - BESS costs are declining (not increasing)
   - UPS duration matches BESS duration (4h)
   - Historical correlation is reasonable
3. Flag warning if cost trajectory is anomalous

---

### 🟡 Issue #8: Replacement Cycle Not Used in TCO (MEDIUM)
**Affected Queries**: 10
**Severity**: MEDIUM
**Location**: `scripts/forecast.py:180-215`

**Problem**:
Query 10 expected analysis of replacement cycle impact:
- VRLA: 3 replacements in 15 years (5-year life)
- Li-ion: 1 replacement in 15 years (12-year life)
- NPV impact of replacement timing

**Current State**:
- Config specifies lifespans (lines 44-47)
- `calculate_tco()` attempts to model replacements (lines 204-210)
- **BUT**: Logic may not be calculating NPV correctly

**Issue**:
The replacement logic uses integer division which may not capture partial replacements:
```python
num_replacements = self.tco_horizon // lifespan_years  # Integer division
```

For 15-year horizon and 12-year lifespan: 15 // 12 = 1 (correct)
For 15-year horizon and 5-year lifespan: 15 // 5 = 3 (correct)

This logic appears correct, but the overall TCO results are wrong due to Issues #1 and #2.

**Recommended Fix**:
- Verify replacement NPV calculation after fixing Issues #1 and #2
- Add detailed output showing replacement schedule and costs
- Consider partial years if battery is not retired exactly at end of analysis

---

## Minor Issues and Missing Features

### Issue #9: Tipping Point Already at Start Year (LOW)
**Problem**: Baseline scenario shows tipping point at 2020 (start year), making it impossible to observe the transition.

**Recommended Fix**:
- Extend historical baseline to 2015 or earlier when VRLA was clearly dominant
- Or adjust cost parameters to delay tipping point to ~2025-2028

---

### Issue #10: No Mass Balance Validation (MEDIUM)
**Problem**: Config specifies mass balance tolerance (line 74) but no validation is implemented for installed base stock-flow consistency.

**Recommended Fix**:
- Implement after Issue #3 (installed base) is fixed
- Add check: `IB(t+1) - IB(t) - Adds(t) + Retirements(t) < tolerance`

---

### Issue #11: NPV Discount Rate Not Configurable by Year (LOW)
**Problem**: Discount rate is fixed at 8% for all years. Realistic analysis may want time-varying rates.

**Enhancement**: Consider making discount rate a time series if needed for advanced scenarios.

---

### Issue #12: No Output for Cost Breakdown (LOW)
**Problem**: TCO is a single number - users cannot see the breakdown of CapEx vs OpEx vs Replacement components.

**Enhancement**: Add columns for TCO component breakdown.

---

### Issue #13: Duration Mismatch Not Flagged (LOW)
**Problem**: Config assumes 4-hour UPS systems, but no validation that loaded data matches this assumption.

**Enhancement**: Add validation check or parameterize duration per region/technology.

---

## Data Quality Observations

### Data Availability
✅ **Good**: Historical data loaded successfully for all 5 regions
✅ **Good**: BESS cost proxy data available for 4 regions
✅ **Good**: Growth projections available

⚠️ **Issue**: Li-ion installed base starts at 0 (conservative but may underestimate current deployment)
⚠️ **Issue**: Historical data shows 47.5% Li-ion share in 2020 - quite high, needs validation

---

## Validation Tests Passed

✅ All demand values non-negative
✅ Li-ion adoption monotonically increasing
✅ Historical data matches within 5% tolerance for overlapping years
✅ S-curve produces bounded adoption (0-95%)
✅ Regional multipliers applied correctly

---

## Critical Path to Fix

### Phase 1: Fix TCO Calculation (CRITICAL - Unblocks everything)
1. **Issue #2**: Fix Li-ion cost trajectory (fix sign error in forecast_costs)
2. **Issue #1**: Verify TCO calculation logic produces correct $/kWh values
3. Test: USA should show Li-ion TCO < VRLA TCO by 2030
4. Test: China should show earlier tipping point than Europe

**Estimated Effort**: 4-8 hours

### Phase 2: Implement Missing Core Features (CRITICAL)
5. **Issue #3**: Implement installed base tracking with stock-flow accounting
6. **Issue #4**: Implement market decomposition (new-build vs replacement)
7. Test: Mass balance validation passing within 0.1%

**Estimated Effort**: 8-12 hours

### Phase 3: Fix Scenario Analysis (HIGH)
8. **Issue #5**: Fix accelerated scenario to produce differentiated results
9. **Issue #7**: Validate and apply BESS cost proxy adjustment
10. Test: Accelerated should show 2-3 year earlier tipping point

**Estimated Effort**: 4-6 hours

### Phase 4: Complete Feature Set (MEDIUM)
11. **Issue #6**: Implement battery metrics calculations
12. **Issue #8**: Verify replacement cycle NPV calculations
13. **Issue #10**: Implement mass balance validation

**Estimated Effort**: 4-6 hours

**Total Estimated Effort**: 20-32 hours

---

## Testing Recommendations

### Unit Tests Needed
1. `test_calculate_tco()`: Verify correct TCO calculation with known inputs
2. `test_forecast_costs()`: Verify Li-ion costs decline monotonically
3. `test_installed_base()`: Verify stock-flow mass balance
4. `test_market_decomposition()`: Verify new-build + replacement = total
5. `test_scenarios()`: Verify different scenarios produce different results

### Integration Tests Needed
1. End-to-end test with synthetic data where true answer is known
2. Validate USA, China, Europe produce different tipping points
3. Validate accelerated vs baseline produce 2-3 year difference

### Validation Tests Needed
1. Historical calibration: Does model match 2020-2024 data?
2. Expert review: Do TCO values match industry benchmarks?
3. Sensitivity analysis: Does model respond appropriately to parameter changes?

---

## Conclusion

The datacenter-ups skill has a solid architectural foundation and correctly implements S-curve adoption modeling, but suffers from **critical implementation errors in TCO calculation and cost forecasting** that make the current outputs unreliable for decision-making.

**Immediate Priority**: Fix Issue #1 and #2 (TCO and cost trajectory) before any other work. Once these are corrected, the model can be validated and the missing features (#3, #4) can be implemented with confidence.

**Risk**: Until these issues are resolved, **the skill should not be used for any business decisions, investment analysis, or policy recommendations** related to datacenter UPS battery selection.

**Recommendation**:
1. Halt production use until critical issues are resolved
2. Implement Phase 1 fixes immediately
3. Add comprehensive unit and integration tests
4. Validate corrected model against industry benchmarks before deployment
5. Consider bringing in a battery economics subject matter expert to review TCO calculations

---

## Appendix: Test Query Checklist

- [ ] ❌ Query 1: TCO Comparison Analysis - FAIL (TCO logic error)
- [ ] ⚠️ Query 2: Tipping Point Identification - PARTIAL (identified but TCO contradicts)
- [ ] ✅ Query 3: S-Curve Adoption Forecast - PASS
- [ ] ⚠️ Query 4: Regional Comparison - PARTIAL (works but TCO issues)
- [ ] ❌ Query 5: Installed Base Evolution - FAIL (not implemented)
- [ ] ❌ Query 6: Market Decomposition Analysis - FAIL (not implemented)
- [ ] ⚠️ Query 7: Accelerated Transition Scenario - PARTIAL (no differentiation)
- [ ] ❌ Query 8: Battery Metrics Calculation - FAIL (not implemented)
- [ ] ⚠️ Query 9: BESS Cost Proxy Validation - PARTIAL (no validation, premium not applied)
- [ ] ❌ Query 10: Replacement Cycle Impact - FAIL (cannot analyze without decomposition)

**Overall Grade**: **D- (30%)**
**Status**: Not ready for production use

---

*End of Report*
