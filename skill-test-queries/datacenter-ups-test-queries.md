# Datacenter UPS Skill - Test Queries

## Overview
Test queries to validate the datacenter-ups battery transition forecasting skill and demonstrate TCO-driven adoption modeling.

---

## Query 1: TCO Comparison Analysis
**Query**: "Compare the Total Cost of Ownership between VRLA and Lithium-ion batteries for datacenter UPS systems over a 15-year horizon"
**Expected**:
- VRLA TCO: CapEx ($220/kWh) + OpEx ($18/kWh-yr) + Replacements (every 5 years)
- Li-ion TCO: Declining CapEx + OpEx ($6/kWh-yr) + Replacements (12-year life)
- Cost advantage curve over time
- NPV calculations with 8% discount rate

---

## Query 2: Tipping Point Identification
**Query**: "When will Li-ion batteries reach cost parity with VRLA for datacenter UPS applications in the USA?"
**Expected**:
- Tipping year when Li-ion TCO ≤ VRLA TCO
- Persistence check (≥3 consecutive years)
- Cost trajectories leading to tipping point
- Early warning indicators

---

## Query 3: S-Curve Adoption Forecast
**Query**: "Model the S-curve adoption of Li-ion batteries in datacenters with economic sensitivity parameters"
**Expected**:
- Logistic function: M(t) = L / (1 + exp(-k × (t - t0)))
- Technology ceiling L = 90-95%
- Adoption rate linked to cost advantage
- Market share evolution 2024-2040

---

## Query 4: Regional Comparison - China vs Europe
**Query**: "Compare datacenter UPS battery transition dynamics between China and Europe regions"
**Expected**:
- China: Lower costs (0.9× multiplier), faster adoption
- Europe: Higher costs (1.15× multiplier), sustainability drivers
- Different tipping point years
- Regional market size differences

---

## Query 5: Installed Base Evolution
**Query**: "Track the installed base evolution of VRLA vs Li-ion batteries through 2035"
**Expected**:
- VRLA IB declining after peak
- Li-ion IB growing exponentially
- Stock-flow accounting: IB(t+1) = IB(t) + Adds - Retirements
- Mass balance validation (±0.1%)

---

## Query 6: Market Decomposition Analysis
**Query**: "Break down total datacenter UPS battery demand into new-build vs replacement segments"
**Expected**:
- New-build demand from DC construction growth (7-10% annually)
- Replacement demand from installed base / lifetime
- Contestable market (VRLA at end-of-life)
- Technology split for each segment

---

## Query 7: Accelerated Transition Scenario
**Query**: "Model an accelerated transition scenario with faster Li-ion cost decline (12% annual) and early VRLA phase-out"
**Expected**:
- Earlier tipping point (2-3 years advance)
- Steeper S-curve adoption (k × 1.5)
- 95%+ Li-ion market share by 2035
- Impact on total market size

---

## Query 8: Battery Metrics Calculation
**Query**: "Calculate battery storage metrics including duration, power capacity, and annual throughput for a 100 MWh datacenter UPS system"
**Expected**:
- Duration: 4 hours (default for UPS)
- Power capacity: 25 MW (Energy/Duration)
- Annual throughput: 25 TWh (250 cycles/year)
- Round-trip efficiency: 88%

---

## Query 9: BESS Cost Proxy Validation
**Query**: "Validate using grid-scale BESS costs as proxy for datacenter UPS Li-ion costs with appropriate adjustments"
**Expected**:
- 4-hour duration match confirmation
- UPS reliability premium consideration (5-10%)
- Cycle life differences (backup vs daily cycling)
- Directional trend validation

---

## Query 10: Replacement Cycle Impact
**Query**: "Analyze how different battery lifespans (VRLA 5y vs Li-ion 12y) affect replacement demand and TCO"
**Expected**:
- VRLA: 3 replacements in 15 years
- Li-ion: 1 replacement in 15 years
- Contestable market size each year
- NPV impact of replacement timing

---

## Additional Test Cases

### Sensitivity Analysis
- Vary discount rate (6-10%)
- Adjust OpEx assumptions (±20%)
- Change battery lifespans (±1 year)
- Test different S-curve parameters

### Validation Checks
- VRLA + Li-ion demand = Total market (±5%)
- Non-negative constraints on all flows
- Monotonic adoption curve
- Historical calibration accuracy

### Edge Cases
- 100% Li-ion adoption ceiling
- Delayed transition (slow cost decline)
- Supply chain disruption scenarios
- Regional policy interventions