# Component Replacement Cycles

## Overview

This document describes replacement cycles for components containing commodities. Replacement cycles determine how often components need to be replaced over a product's lifetime, driving ongoing commodity demand from the installed base.

---

## Batteries

### Automotive Batteries

| Product | Commodity | Replacement Cycle | Units | Notes |
|---------|-----------|-------------------|-------|-------|
| **ICE Cars** | Lead | 3.5 years | per battery | Standard 12V SLI battery |
| **PHEV Cars** | Lead | 3.5 years | per 12V auxiliary | Same as ICE |
| **ICE Cars** | Lead (alt) | 3-4 years | regional variation | Warmer climates: 3 years, Colder: 4 years |
| **EV Cars** | Lithium | 12 years | per battery pack | Or 150,000-200,000 miles |
| **Commercial ICE** | Lead | 3.0 years | per battery | Heavier duty cycle |
| **Commercial EV** | Lithium | 10 years | per battery pack | Commercial use degrades faster |

**Key Factors Affecting Battery Life:**
1. **Climate**: Heat accelerates degradation (30°C avg vs 20°C = 1 year shorter life)
2. **Charging patterns**: Fast charging reduces cycle life by 10-20%
3. **Depth of discharge**: Shallow cycles extend battery life
4. **Quality**: Premium batteries last 20-30% longer than budget options

**Replacement Triggers:**
- **Lead-acid**: Capacity < 50% of original (cranking amperage insufficient)
- **EV lithium**: Capacity < 70-80% of original (range degradation)
- **Warranty**: Many EV batteries have 8-10 year warranties encouraging replacement

**Source:** Battery manufacturers, warranty data, AAA battery failure statistics

---

### Industrial & Stationary Batteries

| Application | Commodity | Replacement Cycle | Units | Notes |
|-------------|-----------|-------------------|-------|-------|
| **Datacenter UPS** | Lead | 5 years | per system | VRLA batteries |
| **Telecom Backup** | Lead | 5-7 years | per system | Constant float charging |
| **Grid Storage** | Lithium | 15 years | per system | Lower cycle depth |
| **Residential Solar** | Lithium | 10-12 years | per system | Daily cycling |

**Note:** Stationary batteries typically last longer than automotive because:
- Climate controlled environments
- Gentler duty cycles
- Better battery management systems
- Regular maintenance

**Source:** Energy storage industry reports, manufacturer specifications

---

## Motors & Power Electronics

### Electric Motors

| Product | Commodity | Replacement Cycle | Units | Notes |
|---------|-----------|-------------------|-------|-------|
| **EV Traction Motor** | Copper | 20+ years | vehicle lifetime | Rarely replaced |
| **Industrial Motors** | Copper | 15-20 years | per motor | Depends on duty cycle |
| **Wind Turbine Generator** | Copper | 20-25 years | turbine lifetime | Rarely replaced |

**Why Motors Last:**
- Few moving parts (especially direct-drive)
- No chemical degradation like batteries
- Regular maintenance extends life
- Failure modes are gradual (bearings, insulation)

**Replacement Drivers:**
- Mechanical failure (bearings, shaft)
- Insulation breakdown
- Winding short circuits
- Typically replaced only on catastrophic failure

**Source:** Motor manufacturer data, industrial maintenance standards

---

### Power Electronics

| Component | Product | Replacement Cycle | Units | Notes |
|-----------|---------|-------------------|-------|-------|
| **Inverters** | Solar PV | 10-15 years | per system | Earlier than panels |
| **Converters** | EV | 15+ years | vehicle lifetime | Rarely replaced |
| **Chargers** | Various | 10 years | per unit | Electronics wear out |

**Why Inverters Fail Earlier:**
- Heat stress on components
- Capacitor degradation
- Semiconductor aging
- More complex than motors

**Source:** Solar industry reports, EV powertrain reliability data

---

## Wiring & Conductors

| Component | Commodity | Replacement Cycle | Units | Notes |
|-----------|-----------|----------|-------|-------|
| **Vehicle Wiring** | Copper | Never | lifetime | Built into structure |
| **Building Wiring** | Copper | 50+ years | building lifetime | Very durable |
| **Solar Cables** | Copper | 25+ years | system lifetime | UV-rated insulation |

**Note:** Wiring is typically not replaced unless:
- Physical damage
- Insulation failure
- Corrosion in harsh environments
- Building renovation/demolition

---

## Replacement Cycle Trends

### Historical Trends

**Lead-Acid Batteries (ICE vehicles):**
- 1990s: 5-6 years average
- 2000s: 4-5 years average
- 2010s: 3-4 years average
- 2020s: 3-3.5 years average

**Why Shorter?**
- More electrical systems draining battery
- Stop-start technology stress
- Smaller batteries for weight savings
- Higher operating temperatures

**EV Batteries:**
- Early EVs (2010-2015): 8-10 years observed
- Modern EVs (2015-2020): 10-15 years projected
- Future EVs (2025+): 15-20 years projected

**Why Longer?**
- Better battery chemistry (less degradation)
- Improved thermal management
- Smarter battery management systems
- Lower depth of discharge usage

---

## Regional Variations

### Lead-Acid Battery Life by Region

| Region | Average Life | Primary Factor |
|--------|--------------|----------------|
| **Middle East** | 2-2.5 years | Extreme heat |
| **Northern Europe** | 4-5 years | Moderate climate |
| **USA (South)** | 3 years | Hot climate |
| **USA (North)** | 4 years | Cold starts stress battery |
| **China** | 3-3.5 years | Mixed climate |

**Source:** Battery manufacturers regional data, warranty claims

---

## Modeling Replacement Demand

### Basic Formula

```
Replacement_Rate = 1 / Replacement_Cycle_Years

Annual_Replacements = Installed_Base × Replacement_Rate
```

**Example: Lead batteries in ICE fleet**
```
Installed Base: 1 billion ICE vehicles
Replacement Cycle: 3.5 years
Replacement Rate: 1 / 3.5 = 0.286 per year

Annual Replacements = 1,000,000,000 × 0.286 = 286 million batteries per year
```

### Advanced Modeling

For more accuracy, use **Weibull distribution** to model failure rates:

```python
from scipy.stats import weibull_min

# Battery failures follow Weibull with shape k=2.5, scale=3.5 years
k = 2.5  # shape (increasing failure rate)
lambda_param = 3.5  # scale (characteristic life)

failure_rate(age) = weibull_min.pdf(age, k, scale=lambda_param)
```

This captures:
- Early failures (manufacturing defects)
- Wear-out failures (majority)
- Long tail of survivors

**Most common approach:** Use average replacement cycle (simpler, adequate for aggregate forecasts)

---

## Data Sources

### Primary Sources
1. **Warranty Claims Data**: Automotive manufacturers, battery companies
2. **Fleet Maintenance Records**: Commercial fleet operators
3. **Consumer Surveys**: AAA, Consumer Reports battery life surveys
4. **Academic Studies**: Battery degradation research
5. **Industry Reports**: Energy storage industry analyses

### Data Quality
- **Lead-acid batteries**: High confidence (decades of data)
- **EV lithium batteries**: Medium confidence (limited long-term data)
- **Industrial systems**: Medium confidence (varies by application)
- **Motors/wiring**: High confidence (mature technology)

---

## Future Projections

### Expected Replacement Cycle Changes by 2030

| Component | Current | 2030 Est. | Change | Driver |
|-----------|---------|-----------|--------|--------|
| EV Batteries | 12 years | 15 years | +25% | Better chemistry, BMS |
| Lead-Acid | 3.5 years | 3.0 years | -14% | More electrical loads |
| Inverters | 12 years | 15 years | +25% | Better electronics |
| Motors | 20 years | 25 years | +25% | Improved materials |

**Note:** These are projections based on current technology trends.

---

## Replacement vs. Recycling

### End-of-Life Disposition

Not all replacements result in commodity demand from primary sources:

| Commodity | Current Recycling Rate | 2030 Target |
|-----------|----------------------|-------------|
| **Lead** | 99% | 99% |
| **Copper** | 30% | 50% |
| **Aluminum** | 75% | 85% |
| **Lithium** | 5% | 50% |
| **Cobalt** | 30% | 70% |

**Lead Battery Recycling:**
- Mature closed-loop system
- >99% of lead batteries recycled
- Recycled lead meets >50% of annual demand

**EV Battery Recycling:**
- Still developing infrastructure
- Second-life applications (grid storage) delay recycling
- By 2030, recycling could meet 20-30% of new lithium demand

**Implication:** As recycling matures, replacement demand increasingly met by secondary supply, reducing primary commodity demand.

---

## Limitations of Replacement Cycle Models

1. **Averages hide variation**: Individual products fail early or last much longer
2. **Technology change**: New chemistries/designs alter replacement patterns
3. **Economic factors**: Price changes affect replacement timing decisions
4. **Repair vs. replace**: Some components repairable rather than replaced
5. **Premature retirement**: Vehicles scrapped before component failure

**Best Practice:** Use replacement cycles for aggregate forecasts, acknowledge uncertainty for individual predictions.
