# Data Gaps Report - Energy Forecasting Skill
**Date**: 2025-11-07
**For**: Data Gathering Team
**Status**: CRITICAL GAPS IDENTIFIED

---

## Executive Summary

The energy-forecasting skill is **80% non-functional** due to missing critical datasets. **3 high-priority datasets** are blocking accurate cost parity analysis and forecasting.

---

## Critical Missing Data (HIGH PRIORITY)

### 1. **Coal Power LCOE** ❌ MISSING
**Impact**: Cannot calculate accurate SWB vs Coal tipping points
**Current Workaround**: Using industry estimates ($55-85/MWh)
**Accuracy**: ±20-30% margin of error

**Required Data**:
```
Dataset Name: Coal_Power_LCOE
Regions: China, USA, Europe, Rest_of_World, Global
Time Range: 2010-2024 (minimum)
Units: $/MWh
Format: Annual values
```

**Why Critical**: Coal is the primary incumbent being displaced by SWB. Without real LCOE data, tipping point detection is unreliable.

---

### 2. **Natural Gas Power LCOE** ❌ MISSING
**Impact**: Cannot calculate SWB vs Gas tipping points
**Current Workaround**: Using industry estimates ($50-95/MWh)
**Accuracy**: ±20-30% margin of error (higher in Europe post-2022)

**Required Data**:
```
Dataset Name: Natural_Gas_Power_LCOE
Regions: China, USA, Europe, Rest_of_World, Global
Time Range: 2010-2024 (minimum)
Units: $/MWh
Format: Annual values
```

**Why Critical**: In USA, gas (not coal) is the primary competitor to SWB. Gas-first displacement requires accurate LCOE.

---

### 3. **Coal Capacity Factor** ❌ MISSING (DERIVED)
**Impact**: Moderate - currently calculated from generation/capacity
**Current Workaround**: Derived via `CF = Generation / (Capacity × 8760)`
**Accuracy**: Good (±5%)

**Status**: **ACCEPTABLE** - derived data is accurate, but real data would be better

**Optional Real Data**:
```
Dataset Name: Coal_Capacity_Factor
Regions: China, USA, Europe, Rest_of_World, Global
Time Range: 2010-2024
Units: Ratio (0-1) or Percentage
Format: Annual values
```

---

## Moderate Missing Data (MEDIUM PRIORITY)

### 4. **CSP Capacity Factor** ❌ MISSING
**Impact**: Low - CSP is <1% of solar capacity in most regions
**Current Workaround**: Using industry standard (30-35%)
**Accuracy**: ±10%

**Required Data**:
```
Dataset Name: CSP_Capacity_Factor
Regions: Global (minimum), regional if available
Time Range: 2015-2024
Units: Ratio (0-1)
Format: Annual values
```

---

## Regional Data Gaps (LOW PRIORITY)

These gaps are handled via Global fallback but regional data would improve accuracy:

| Technology | Missing Regions | Fallback |
|------------|----------------|----------|
| **Solar PV LCOE** | Europe, Rest_of_World | Using Global |
| **Solar PV Capacity Factor** | All regions except Global | Using Global |
| **Onshore Wind LCOE** | Europe, Rest_of_World | Using Global |
| **Onshore Wind CF** | Europe, Rest_of_World | Using Global |
| **Offshore Wind LCOE** | All regions except Global | Using Global |
| **Offshore Wind CF** | All regions except Global | Using Global |
| **Battery Storage Cost** | Rest_of_World | Using Global |

**Impact**: Low - Global data is acceptable for initial forecasts

---

## Data Quality Issues

### Inconsistent Time Ranges
Different technologies have different historical coverage:

| Technology | Start Year | End Year | Years of Data |
|------------|-----------|----------|---------------|
| Solar PV | 2000 | 2040 | 41 years |
| Onshore Wind | 2000 | 2040 | 41 years |
| Offshore Wind | 2006 | 2040 | 35 years |
| CSP | 2006 | 2040 | 35 years |
| Battery Storage | 2019 | 2024 | 6 years |
| Coal Generation | 2006 | 2024 | 19 years |

**Recommendation**: Align all datasets to start from **2010** (or earlier if available) for consistent analysis.

---

## Priority Actions

### Immediate (Week 1)
1. ✅ **Obtain Coal Power LCOE** - historical data for all regions (2010-2024)
2. ✅ **Obtain Natural Gas Power LCOE** - historical data for all regions (2010-2024)

### Short-term (Month 1)
3. **Backfill Battery Storage Cost** - extend historical data to 2010 (currently only 2019-2024)
4. **Add CSP Capacity Factor** - real data to replace industry standards

### Long-term (Quarter 1)
5. Add regional LCOE data for Solar/Wind (currently using Global fallback)
6. Extend all time series to common baseline (2000 or 2010)

---

## Data Format Requirements

All datasets should follow this structure:

```json
{
  "Energy Generation": {
    "Dataset_Name": {
      "metadata": {
        "type": "cost",
        "units": "$/MWh",
        "source": "Your Source",
        "category": "cost",
        "entity_type": "incumbent",
        "description": "Dataset description"
      },
      "regions": {
        "China": {
          "X": [2010, 2011, 2012, ...],
          "Y": [55.0, 54.5, 53.2, ...]
        },
        "USA": {
          "X": [2010, 2011, 2012, ...],
          "Y": [65.0, 64.2, 63.5, ...]
        }
      }
    }
  }
}
```

**Units**:
- LCOE: `$/MWh` or `$/kWh`
- Capacity Factor: `ratio (0-1)` or `percentage`
- Generation: `GWh` or `TWh`
- Capacity: `MW` or `GW`

---

## Impact Assessment

### Without Coal/Gas LCOE Data:
- ❌ Tipping point analysis is **unreliable** (±3-5 years error)
- ❌ Cost parity projections are **inaccurate**
- ❌ Cannot validate SWB disruption narrative
- ❌ Stakeholder reports lack credibility

### With Coal/Gas LCOE Data:
- ✅ Accurate tipping point detection (±1 year)
- ✅ Reliable cost forecasts
- ✅ Defensible analysis for policy/investment decisions
- ✅ Regional displacement sequencing (coal-first vs gas-first)

---

## Data Sources (Suggested)

### For Coal/Gas LCOE:
- **IEA World Energy Outlook** - Annual LCOE by technology and region
- **IRENA Renewable Power Generation Costs** - Comparative LCOE data
- **Lazard LCOE Reports** - Annual unsubsidized LCOE
- **EIA (US Energy Information Administration)** - US-specific data
- **BNEF (Bloomberg NEF)** - Global energy economics data

### For Capacity Factors:
- **IEA Electricity Information** - Historical CF by technology
- **EIA Form EIA-860/923** - US plant-level data
- **EMBER Climate** - Global electricity data
- **National statistics agencies** - Country-specific data (China NEA, Eurostat)

---

## Contact

For questions about data requirements or format specifications:
- Review: `ENERGY_SKILL_VALIDATION_REPORT.md` (detailed technical report)
- Check: `.claude/skills/energy-forecasting/data/Energy_Generation.json` (current data structure)
- Reference: `.claude/skills/energy-forecasting/data/swb_taxonomy_and_datasets.json` (dataset mappings)

---

**Bottom Line**: We need **real Coal and Gas LCOE data** to make the energy-forecasting skill credible. Everything else is secondary.
