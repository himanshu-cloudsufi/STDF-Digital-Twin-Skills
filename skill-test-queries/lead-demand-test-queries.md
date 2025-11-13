# Lead Demand Skill - Test Queries

## Overview
Test queries to validate the lead-demand forecasting skill with focus on battery applications and vehicle electrification impact.

---

## Query 1: Total Lead Demand Forecast
**Query**: "Forecast global lead demand from 2024 to 2040, showing battery vs non-battery breakdown"
**Expected**:
- Total lead demand in tonnes/year
- Battery demand (~85% of total)
- Other uses demand (~15% of total)
- Annual growth rates

---

## Query 2: Vehicle Electrification Impact
**Query**: "Analyze how the transition from ICE to EV vehicles affects lead demand in SLI batteries"
**Expected**:
- ICE passenger cars: 11.5 kg lead per vehicle
- BEV passenger cars: 9.0 kg lead per vehicle (22% reduction)
- Fleet mix evolution over time
- Net impact on automotive lead demand

---

## Query 3: SLI Battery Demand by Vehicle Type
**Query**: "Break down SLI battery lead demand by vehicle category (cars, 2W, 3W, commercial vehicles)"
**Expected**:
- Passenger cars SLI demand (largest segment)
- Two-wheelers: ICE (2.5 kg) vs EV (1.8 kg)
- Three-wheelers: ICE (7 kg) vs EV (5 kg)
- Commercial vehicles: ICE (22 kg) vs EV (18 kg) vs NGV (22 kg)

---

## Query 4: Installed Base and Replacement Cycles
**Query**: "Calculate replacement battery demand based on vehicle fleet and battery lifespans"
**Expected**:
- SLI battery life: 4.5 years
- Replacement demand = Fleet / Battery_Life × Lead_Content
- OEM (new vehicle) vs Replacement split
- Fleet growth impact on replacement demand

---

## Query 5: Industrial Battery Segments
**Query**: "Analyze industrial battery lead demand for motive power (forklifts) and stationary power (UPS)"
**Expected**:
- Motive power: 60% of industrial (~250 kg/unit)
- Stationary power: 40% of industrial (~120,000 kg/MWh)
- Battery lifespans: Motive 7 years, Stationary 6 years
- Growth trajectories for each segment

---

## Query 6: PHEV Lead Content Analysis
**Query**: "What is the lead content for PHEV vehicles and how does it compare to other powertrains?"
**Expected**:
- PHEV-specific coefficient from dataset
- Comparison with ICE, BEV, HEV
- PHEV market share projections
- Impact on total automotive lead demand

---

## Query 7: Regional Fleet Analysis - China
**Query**: "Analyze China's vehicle fleet composition and its impact on regional lead demand"
**Expected**:
- Fleet breakdown by vehicle type and powertrain
- Regional EV adoption rates
- China's share of global lead demand
- Growth rate vs global average

---

## Query 8: Extended Battery Life Scenario
**Query**: "Model the impact of 25% longer battery lifespans on replacement demand"
**Expected**:
- SLI: 4.5 → 5.6 years
- Motive: 7 → 8.75 years
- Stationary: 6 → 7.5 years
- Reduction in replacement demand (~20%)
- Total demand impact

---

## Query 9: Bottom-up vs Aggregate Validation
**Query**: "Compare bottom-up calculations from vehicle data with aggregate industrial battery demand datasets"
**Expected**:
- Bottom-up SLI from sales × coefficients
- Aggregate industrial demand from direct datasets
- Variance analysis (tolerance ±10%)
- Reconciliation methodology

---

## Query 10: NGV Commercial Vehicle Analysis
**Query**: "Analyze lead demand from Natural Gas commercial vehicles and their SLI battery requirements"
**Expected**:
- NGV lead content: 22 kg (same as ICE CV)
- NGV fleet size and growth
- Regional distribution of NGV adoption
- Contribution to total CV lead demand

---

## Additional Test Cases

### Powertrain Scenarios
- 75% EV adoption by 2040
- Delayed electrification (50% by 2040)
- PHEV as bridge technology scenario
- Hydrogen fuel cell impact

### Market Dynamics
- Other uses elasticity with GDP
- Price sensitivity analysis
- Recycling rate impact
- Supply chain constraints

### Validation Tests
- Fleet mass balance (Sales - Scrappage = ΔFleet)
- Non-negativity constraints
- Lead content consistency
- Historical back-testing

### Special Cases
- Zero EV growth scenario
- Battery technology breakthrough (50% less lead)
- Regulatory phase-out of lead batteries
- Alternative chemistry adoption (Li-ion for SLI)