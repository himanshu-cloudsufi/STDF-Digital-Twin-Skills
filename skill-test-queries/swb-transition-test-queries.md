# SWB Transition Skill - Test Queries

## Overview
Test queries to validate the Solar-Wind-Battery energy transition skill for modeling fossil fuel displacement by renewables.

---

## Query 1: LCOE Tipping Point Analysis
**Query**: "When will the SWB stack (Solar+Wind+Battery) become cheaper than coal and gas generation?"
**Expected**:
- Solar LCOE trajectory (declining ~8% annually)
- Wind LCOE trajectory (declining ~6% annually)
- Battery SCOE calculation (CapEx/cycles/duration/RTE)
- Separate tipping points for vs-coal and vs-gas
- Regional variations in tipping years

---

## Query 2: Displacement Sequencing - China
**Query**: "Model China's energy transition using coal-first displacement sequencing through 2040"
**Expected**:
- Coal reduced first (environmental priority)
- Gas maintained for flexibility
- Coal floor at 10% of peak load
- Gas floor at 15% of peak load
- Annual displacement amounts in TWh

---

## Query 3: Battery Storage Requirements
**Query**: "Calculate battery storage capacity needed to support 50% renewable penetration"
**Expected**:
- Peak load calculation from annual demand
- Storage sizing: k_days × Peak_Load × 24h
- Default 4-hour duration systems
- Power (GW) and Energy (GWh) requirements
- Annual throughput at 250 cycles/year

---

## Query 4: Capacity Factor Evolution
**Query**: "Show how capacity factors for renewable technologies improve over time"
**Expected**:
- Solar: 15-25% with 0.2-0.3 pp/year improvement
- Onshore wind: 25-35% with 0.2-0.3 pp/year improvement
- Offshore wind: 35-50% with 0.3-0.5 pp/year improvement
- Impact on generation from same capacity

---

## Query 5: Generation vs Capacity Forecast
**Query**: "Forecast both installed capacity (GW) and generation (TWh) for all technologies through 2045"
**Expected**:
- Capacity growth rates by technology
- Generation = Capacity × CF × 8760
- Renewable capacity vs generation share divergence
- Fossil capacity retirement schedule

---

## Query 6: Regional Comparison - USA vs Europe
**Query**: "Compare energy transition pathways between USA (gas-first) and Europe (coal-first) displacement"
**Expected**:
- USA: Cheap gas leads to gas-bridge strategy
- Europe: Carbon pricing drives coal phase-out
- Different renewable adoption rates
- Regional cost differences
- Policy impact on transition speed

---

## Query 7: CO₂ Emissions Reduction
**Query**: "Calculate CO₂ emissions reduction from displacing coal (0.9-1.0 tCO₂/MWh) and gas (0.4-0.5 tCO₂/MWh)"
**Expected**:
- Annual emissions by technology
- Cumulative emissions avoided
- Pathway to net-zero grid
- Regional emission factors
- Percentage reduction vs baseline

---

## Query 8: High Renewable Scenario
**Query**: "Model an 80% renewable electricity system by 2040 with adequate battery storage"
**Expected**:
- Solar + Wind capacity requirements
- Battery storage for grid stability (2-4 days)
- Residual fossil for reliability
- Total system costs
- Land use implications

---

## Query 9: Cost Stack Analysis
**Query**: "Compare the full cost stack of SWB vs traditional generation including integration costs"
**Expected**:
- SWB Stack: MAX(Solar, Wind) + SCOE
- Coal: LCOE + carbon costs
- Gas: LCOE + fuel price volatility
- Grid integration costs for renewables
- System-level cost comparison

---

## Query 10: Non-SWB Baseline Evolution
**Query**: "Track nuclear, hydro, and other renewable generation as baseline through the transition"
**Expected**:
- Nuclear: Flat or slight decline (0-2% annually)
- Hydro: Weather-dependent, stable capacity
- Geothermal, biomass: Small but growing
- Baseline share of total generation
- Regional differences in baseline resources

---

## Additional Test Cases

### Extreme Scenarios
- 100% renewable grid feasibility
- No battery storage available
- Carbon price at $100/tCO₂
- Natural gas price spike (3x)

### Technology Variations
- Offshore wind dominance
- Solar+storage 24/7 contracts
- Long-duration storage (8-100 hours)
- Green hydrogen integration

### Validation Tests
- Energy balance (Generation = Demand ±2%)
- Reserve requirements maintained
- Capacity factor bounds checking
- Smooth transition paths

### Policy Scenarios
- Renewable energy mandates
- Coal plant retirement schedules
- Carbon tax implementation
- Grid reliability standards

### Edge Cases
- Extreme weather impact on renewables
- Negative electricity prices
- Curtailment management
- Transmission constraints