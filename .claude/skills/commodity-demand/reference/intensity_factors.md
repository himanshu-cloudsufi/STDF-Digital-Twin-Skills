# Commodity Intensity Factors

## Overview

This document provides detailed intensity factors for commodities in various products. Intensity factors represent the quantity of a commodity required per product unit.

## Format

All intensity factors are specified as:
```
Intensity = Quantity per Unit (e.g., kg per vehicle, kg per kWh, kg per MW)
```

---

## Copper (Cu)

### Vehicles

| Product | Intensity | Units | Breakdown |
|---------|-----------|-------|-----------|
| **EV Cars** | 80 kg | per vehicle | Motor: 25 kg, Battery wiring: 18 kg, Power electronics: 12 kg, Charging: 8 kg, Other: 17 kg |
| **ICE Cars** | 20 kg | per vehicle | Alternator: 5 kg, Radiator: 4 kg, Wiring: 11 kg |
| **PHEV Cars** | 40 kg | per vehicle | Hybrid motor: 12 kg, Smaller battery wiring: 8 kg, ICE components: 12 kg, Other: 8 kg |
| **Commercial EV** | 120 kg | per vehicle | Larger motor: 40 kg, Battery wiring: 30 kg, Power electronics: 20 kg, Other: 30 kg |
| **Commercial ICE** | 30 kg | per vehicle | Larger alternator: 8 kg, Radiator: 6 kg, Wiring: 16 kg |

### Energy Generation

| Product | Intensity | Units | Breakdown |
|---------|-----------|-------|-----------|
| **Solar PV** | 5.5 kg | per kW | Inverter: 2.5 kg, Wiring: 2.0 kg, Junction boxes: 1.0 kg |
| **Onshore Wind** | 4.0 kg | per kW | Generator: 2.5 kg, Transformer: 1.0 kg, Cabling: 0.5 kg |
| **Offshore Wind** | 6.0 kg | per kW | Generator: 3.0 kg, Transformer: 1.5 kg, Subsea cabling: 1.5 kg |

**Source:** Industry averages from equipment manufacturers and academic studies

---

## Lithium (Li)

### Batteries

| Product | Intensity | Units | Chemistry | Notes |
|---------|-----------|-------|-----------|-------|
| **EV Cars** | 8.0 kg | per kWh | LFP/NMC average | Assumes 60 kWh pack = 480 kg total lithium |
| **PHEV Cars** | 3.0 kg | per kWh | NMC | Smaller pack (15 kWh avg) = 45 kg lithium |
| **Commercial EV** | 12.0 kg | per kWh | LFP | Larger commercial packs (200 kWh avg) |
| **Battery Storage** | 0.15 kg | per kWh | LFP dominant | Utility-scale systems |

**Chemistry Notes:**
- **LFP (Lithium Iron Phosphate)**: ~4% Li content by weight
- **NMC (Nickel Manganese Cobalt)**: ~7% Li content by weight
- **NCA (Nickel Cobalt Aluminum)**: ~6% Li content by weight

**Source:** Battery cell manufacturers, teardown analyses

---

## Lead (Pb)

### Batteries

| Product | Intensity | Units | Application | Notes |
|---------|-----------|-------|-------------|-------|
| **ICE Cars** | 12 kg | per vehicle | Starter battery | Standard 12V SLI battery |
| **PHEV Cars** | 12 kg | per vehicle | Starter battery | Still requires 12V auxiliary |
| **Commercial ICE** | 18 kg | per vehicle | Larger battery | 24V system for trucks |
| **Datacenter UPS** | 500 kg | per unit | Backup power | VRLA batteries |

**Note:** EVs typically use small 12V Li-ion auxiliary batteries (~2 kg lithium), not lead-acid.

**Source:** Battery manufacturers, vehicle specifications

---

## Cobalt (Co)

### Batteries

| Product | Intensity | Units | Chemistry | Notes |
|---------|-----------|-------|-----------|-------|
| **EV Cars** | 1.2 kg | per kWh | NMC 622/811 | Declining with newer chemistries |
| **PHEV Cars** | 0.5 kg | per kWh | NMC | Lower cobalt NMC variants |

**Trend:** Cobalt intensity is declining over time:
- 2015: ~3 kg/kWh (NMC 111)
- 2020: ~1.5 kg/kWh (NMC 622)
- 2025: ~0.5 kg/kWh (NMC 811, LFP shift)

**Source:** Battery manufacturers, BNEF

---

## Aluminum (Al)

### Vehicles

| Product | Intensity | Units | Application | Notes |
|---------|-----------|-------|-------------|-------|
| **EV Cars** | 150 kg | per vehicle | Body panels: 80 kg, Castings: 40 kg, Battery tray: 20 kg, Other: 10 kg | Higher use in EVs |
| **ICE Cars** | 100 kg | per vehicle | Engine block: 40 kg, Body panels: 40 kg, Other: 20 kg | Traditional ICE |
| **PHEV Cars** | 125 kg | per vehicle | Hybrid components | Between EV and ICE |
| **Commercial EV** | 200 kg | per vehicle | Larger body structure | Commercial vehicles |
| **Commercial ICE** | 150 kg | per vehicle | Engine, body | Traditional commercial |

**Trend:** Aluminum intensity increasing due to lightweighting efforts.

**Source:** Ducker Automotive Studies, manufacturer data

---

## Nickel (Ni)

### Batteries

| Product | Intensity | Units | Chemistry | Notes |
|---------|-----------|-------|-----------|-------|
| **EV Cars** | 2.5 kg | per kWh | NMC 622/811 | High-nickel chemistries |
| **PHEV Cars** | 1.0 kg | per kWh | NMC | Lower nickel variants |
| **Commercial EV** | 3.5 kg | per kWh | High-nickel NCA | Tesla Model S/X type |

**Trend:** Nickel intensity increasing with shift to high-nickel chemistries for longer range.

**Source:** Battery manufacturers, BNEF

---

## Oil (Crude Oil)

### Transportation

| Product | Intensity | Units | Application | Notes |
|---------|-----------|-------|-------------|-------|
| **ICE Cars** | 2.5 | barrels/day per 1000 vehicles | Gasoline consumption | Avg 12,000 miles/year, 25 MPG |
| **Commercial ICE** | 8.0 | barrels/day per 1000 vehicles | Diesel consumption | Higher mileage, lower efficiency |

**Conversion:**
- 1 barrel = 42 gallons
- Annual consumption per ICE car = 480 gallons = 11.4 barrels/year

**Note:** EV cars have zero direct oil consumption for fuel.

**Source:** EIA, transportation statistics

---

## Intensity Factor Sources

### Primary Sources
1. **Vehicle teardowns**: A2Mac1, Munro & Associates
2. **Battery cell analyses**: BNEF, Avicenne Energy
3. **LCA studies**: Argonne National Laboratory GREET model
4. **Industry reports**: USGS Mineral Commodity Summaries
5. **Manufacturer specifications**: Tesla, BYD, CATL

### Data Quality Ratings
- **High confidence**: Copper, Aluminum, Lead (well-documented)
- **Medium confidence**: Lithium, Nickel, Cobalt (chemistry variations)
- **Lower confidence**: Rare earths (proprietary formulations)

### Update Frequency
Intensity factors should be reviewed annually to account for:
- Technology improvements (e.g., reduced cobalt content)
- Manufacturing process changes
- Material substitution trends
- Regional variations in specifications

---

## Regional Variations

Some intensity factors vary by region due to:
- **Regulatory standards**: Emission requirements affecting engine design
- **Consumer preferences**: Vehicle size differences (US vs Europe)
- **Climate factors**: Battery sizing for range in cold climates
- **Infrastructure**: Charging availability affecting battery capacity needs

**Example: EV battery capacity**
- China: 50-60 kWh average (shorter daily distances)
- USA: 70-80 kWh average (longer range preference)
- Europe: 60-70 kWh average (middle ground)

---

## Future Trends

### Expected Intensity Changes by 2030

| Commodity | Current | 2030 Est. | Change | Driver |
|-----------|---------|-----------|--------|--------|
| Cobalt | 1.2 kg/kWh | 0.3 kg/kWh | -75% | LFP adoption, cobalt-free NMC |
| Lithium | 8.0 kg/kWh | 6.0 kg/kWh | -25% | Higher energy density |
| Copper (EV) | 80 kg | 90 kg | +12% | More powerful motors, 800V systems |
| Aluminum (EV) | 150 kg | 180 kg | +20% | Lightweighting push |

**Note:** These are projections and subject to change based on technology development.
