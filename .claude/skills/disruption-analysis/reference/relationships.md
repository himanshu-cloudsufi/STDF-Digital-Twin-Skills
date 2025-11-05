# Known Disruption Relationships

This document catalogs known disruption patterns and cross-market impacts that the skill can analyze.

## Primary Disruptions

### 1. EV → Oil Demand (Transportation)

**Pattern ID:** `ev_disrupts_oil`

**Disruptor:** Electric Vehicles (EV_Cars, Commercial_EV)

**Impacted:** Oil demand for transportation

**Conversion Factor:** 2.5 barrels/day per 1000 vehicles

**Mechanism:**
- Each EV displaces gasoline/diesel consumption from ICE vehicle
- Average ICE vehicle consumes ~2.5 barrels/day per 1000 vehicles
- Commercial EVs have higher displacement (trucks, buses)

**Timeline:**
- Cost parity (tipping point): ~2023-2025 in most regions
- 50% displacement: ~2030-2035
- 95% displacement: ~2040-2045

**Regional Variations:**
- **China:** Fastest displacement (tipping ~2023, 95% by 2040)
- **Europe:** Moderate pace (tipping ~2024, 95% by 2042)
- **USA:** Slower initially, accelerates post-2025
- **Rest_of_World:** Delayed by 5-7 years relative to leading regions

### 2. Solar+Wind+Battery (SWB) → Coal Power

**Pattern ID:** `swb_displaces_coal`

**Disruptor:** Solar PV, Onshore Wind, Battery Storage (aggregated)

**Impacted:** Coal power generation

**Conversion Factor:** 1.0 MWh per MWh (direct substitution)

**Mechanism:**
- SWB provides cheaper electricity than coal
- Battery storage solves intermittency, enabling 24/7 clean power
- Coal plants retired as uneconomical

**Timeline:**
- Cost parity: Already achieved in most regions (2020-2023)
- 50% displacement: ~2028-2032
- 95% displacement: ~2035-2040

**Regional Variations:**
- **China:** Massive SWB buildout, coal peaks ~2025
- **Europe:** Coal already in decline, complete exit by 2035
- **USA:** Regional variation (Texas fast, Midwest slower)
- **Rest_of_World:** Depends on coal infrastructure age

### 3. Solar+Wind+Battery (SWB) → Natural Gas Power

**Pattern ID:** `swb_displaces_gas`

**Disruptor:** Solar PV, Onshore Wind, Battery Storage

**Impacted:** Natural gas power generation

**Conversion Factor:** 1.0 MWh per MWh

**Mechanism:**
- SWB undercuts natural gas on cost
- Gas retains peaker plant role temporarily (2025-2035)
- Eventually displaced entirely by SWB + long-duration storage

**Timeline:**
- Cost parity: ~2025-2030 (later than coal)
- 50% displacement: ~2035-2040
- 95% displacement: ~2045-2050

**Notes:**
- Natural gas declines slower than coal (lower baseline cost)
- May retain niche role for industrial heat
- Peaker plants replaced by 4-8 hour batteries first

### 4. EV → Lead Demand (Batteries)

**Pattern ID:** `ev_impacts_lead`

**Disruptor:** Electric Vehicles

**Impacted:** Lead demand (automotive batteries)

**Conversion Factor:** -12.0 kg per vehicle (negative = reduction)

**Mechanism:**
- ICE vehicles use lead-acid starter batteries (~12 kg lead each)
- EVs don't need starter batteries (lithium-ion only)
- Each EV eliminates 12 kg lead demand
- Partially offset by replacement demand from existing ICE fleet

**Timeline:**
- Lead demand peaks: ~2025-2028 (earlier than oil)
- 50% reduction: ~2035-2040
- 95% reduction: ~2050+ (long tail from legacy ICE fleet)

**Notes:**
- Lead has other uses (UPS, datacenters, industrial)
- Automotive sector is ~60-70% of total lead demand
- Replacement cycle: ICE batteries replaced every 3-4 years

## Secondary Disruptions

### 5. ICE Decline → Oil Demand

**Pattern ID:** `ice_decline_impacts_oil`

**Disruptor:** ICE vehicle demand (declining)

**Impacted:** Oil demand

**Conversion Factor:** 1.0 (direct relationship)

**Mechanism:**
- As ICE sales decline, oil demand for new vehicle fleet declines
- Existing ICE fleet continues consuming oil (replacement demand)
- Net effect: oil demand lags ICE sales decline by ~10-15 years (vehicle lifetime)

**Notes:**
- This is the inverse of EV disruption
- Used for queries about ICE peak vs. oil peak
- Demonstrates lag between product sales and commodity demand

### 6. EV → ICE Direct Displacement

**Pattern ID:** `ev_disrupts_ice`

**Disruptor:** Electric Vehicles

**Impacted:** ICE vehicle sales

**Conversion Factor:** 1.0 vehicles per vehicle

**Mechanism:**
- Direct competition in passenger vehicle market
- EV reaches cost parity, then undercuts ICE
- S-curve adoption post-tipping (logistic growth)

**Timeline:**
- Cost parity: ~2023-2025
- 50% market share: ~2028-2032
- 95% market share: ~2035-2040

**Regional Variations:**
- **China:** Leading (95% by 2040)
- **Europe:** Close second (95% by 2042)
- **USA:** Slower (95% by 2045)
- **Rest_of_World:** Delayed (95% by 2050)

### 7. Solar+Wind → Fossil Fuels (Combined)

**Pattern ID:** `solar_wind_displaces_fossil`

**Disruptor:** Solar PV, Onshore Wind

**Impacted:** Coal + Natural Gas (aggregated)

**Conversion Factor:** 1.0 MWh per MWh

**Mechanism:**
- Solar and wind directly displace fossil fuel generation
- Battery storage enables firm capacity
- Combined SWB system displaces all fossil generation

**Notes:**
- This is aggregated version of patterns 2 and 3
- Used for "when will clean energy dominate?" queries
- Fossil fuels displaced in order: coal → gas → oil (by economics)

## Conversion Factor Derivations

### Oil Displacement (EV → Oil)

**Calculation:**
- Average ICE vehicle: 12,000 miles/year
- Average fuel economy: 25 miles/gallon
- Annual gasoline consumption: 480 gallons/year
- Conversion to barrels: 480 gal ÷ 42 gal/barrel = 11.4 barrels/year
- Per 1000 vehicles: 11,400 barrels/year
- Daily rate: 11,400 ÷ 365 = 31.2 barrels/day per 1000 vehicles

**Simplified factor:** 2.5 barrels/day per 1000 vehicles (conservative)

### Lead Displacement (EV → Lead)

**Calculation:**
- ICE vehicle lead-acid battery: 12-15 kg lead
- EV: 0 kg lead (uses lithium-ion)
- Net displacement: -12 kg per EV

**Replacement cycle:**
- ICE battery lifetime: 3-4 years
- Replacement demand: 12 kg ÷ 3.5 years = 3.4 kg/year per ICE vehicle
- EVs eliminate both initial and replacement demand

## Multi-Product Disruptions

### SWB = Solar + Wind + Battery

**Components:**
- Solar PV (utility-scale)
- Onshore Wind
- Battery Storage (4-8 hour duration)

**Why aggregated:**
- These technologies work together as a system
- Individually, solar/wind face intermittency criticism
- Combined with batteries, they provide firm capacity 24/7
- Market adopts SWB as integrated solution

**Aggregation method:**
- Sum capacity (GW) or generation (MWh) across all three
- Use combined output to displace fossil fuels

### Commercial EV = Light + Medium + Heavy Duty

**Components:**
- Light Commercial Vehicles (LCV)
- Medium Duty Vehicles (MDV)
- Heavy Duty Vehicles (HDV)

**Why aggregated:**
- All displace diesel/gasoline in commercial sector
- Different conversion factors (HDV displaces more oil per vehicle)
- Often analyzed together for fleet transformation

## Disruption Archetypes

### Type 1: Direct Substitution (1:1)
- EV displaces ICE
- SWB displaces coal/gas
- Conversion factor ≈ 1.0

### Type 2: Derived Demand (lagged)
- ICE decline reduces oil demand
- Oil demand lags ICE sales by vehicle lifetime
- Includes both new sales and replacement cycles

### Type 3: Inverse Impact (negative conversion)
- EV reduces lead demand
- Disruptor eliminates need for commodity
- Conversion factor < 0

### Type 4: Systemic Cascade
- EV → oil → petrochemical → plastics
- Multiple downstream impacts
- Not yet modeled in current implementation

## Adding New Disruption Patterns

To add a new pattern to the skill:

1. **Identify relationship:**
   - What product/technology is the disruptor?
   - What incumbent is being displaced?
   - Is this direct substitution or derived demand?

2. **Calculate conversion factor:**
   - Units must be compatible (e.g., barrels per vehicle)
   - Use industry averages, not theoretical maxima
   - Document calculation method

3. **Add to `disruption_mappings.json`:**
```json
{
  "new_pattern_id": {
    "keywords": ["keyword1", "keyword2"],
    "disruptor": "Product_Name",
    "impacted": "Incumbent_Name",
    "conversion_factor": X.X,
    "units": "units description",
    "description": "Brief explanation"
  }
}
```

4. **Validate:**
   - Test with natural language queries
   - Verify conversion factor units
   - Check for reasonable timelines

## References

- IEA World Energy Outlook (oil consumption data)
- BloombergNEF (EV adoption forecasts)
- NREL (solar/wind cost data)
- Tony Seba, "Rethinking Transportation 2020-2030"
- RethinkX sector disruption reports
