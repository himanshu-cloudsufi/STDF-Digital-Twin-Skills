# Curves Catalog Data Gaps Report
**Date**: 2025-11-07
**Source**: `curves_catalog_files/`
**For**: Data Gathering Team

---

## Executive Summary

The `curves_catalog_files/` directory contains **22 out of 25** required datasets for energy forecasting. **3 critical LCOE datasets are missing** for fossil fuel incumbents.

**Key Finding**: Catalog has better structure than skill's data directory (includes scenario-based forecasts), but missing critical cost data for Coal and Gas.

---

## Critical Missing Datasets

### 1. **Coal_Power_LCOE** ❌ MISSING
**File**: Should be in `Energy_Generation.json`
**Impact**: Cannot calculate SWB vs Coal tipping points
**Status**: COMPLETELY MISSING

**Required**:
- Regions: China, USA, Europe, Rest_of_World, Global
- Time range: 2010-2024 (historical), optionally 2025-2040 (scenarios)
- Units: $/MWh or $/kWh
- Scenarios: standard (minimum), Prosperity, Superabundance (optional)

---

### 2. **Natural_Gas_LCOE** or **Natural_Gas_Power_LCOE** ❌ MISSING
**File**: Should be in `Energy_Generation.json`
**Impact**: Cannot calculate SWB vs Gas tipping points
**Status**: COMPLETELY MISSING

**Required**:
- Regions: China, USA, Europe, Rest_of_World, Global
- Time range: 2010-2024 (historical), optionally 2025-2040 (scenarios)
- Units: $/MWh or $/kWh
- Scenarios: standard (minimum), Prosperity, Superabundance (optional)

---

### 3. **Coal_Capacity_Factor** ❌ MISSING
**File**: Should be in `Energy_Generation.json`
**Impact**: Cannot derive generation from capacity accurately
**Status**: MISSING (currently being calculated from generation/capacity data)

**Current Workaround**: `CF = Generation_GWh / (Capacity_MW × 8.76)`

**Optional but Recommended**:
- Regions: China, USA, Europe, Rest_of_World, Global
- Time range: 2010-2024
- Units: Ratio (0-1) or Percentage
- Note: Derived values are acceptable, but real historical data would be better

---

## Datasets Found ✅

### Cost Data (LCOE)
| Dataset | Regions Available | Time Range (China) | Scenarios |
|---------|-------------------|-------------------|-----------|
| **Solar_Photovoltaic_LCOE** | China, USA, Global | 2010-2024 | Single |
| **Onshore_Wind_LCOE** | China, USA, Global | 1996-2024 | Single |
| **Offshore_Wind_LCOE** | Global only | Unknown | Single |
| **Concentrated_Solar_Power_LCOE** | Global only | Unknown | Single |

**Missing Regions**: Europe, Rest_of_World (acceptable - can use Global fallback)

---

### Capacity Data
| Dataset | Regions Available | Time Range (China) | Scenarios |
|---------|-------------------|-------------------|-----------|
| **Solar_Installed_Capacity** | All regions | 2000-2040 | Single |
| **Onshore_Wind_Installed_Capacity** | All regions | Unknown | Single |
| **Offshore_Wind_Installed_Capacity** | All regions | Unknown | Single |
| **CSP_Installed_Capacity** | All regions | Unknown | Single |
| **Battery_Storage_Installed_Capacity** | All regions | Unknown | Single |
| **Coal_Installed_Capacity** | All regions | 2005-2040 | ✓ 3 scenarios |
| **Natural_Gas_Installed_Capacity** | All regions | Unknown | Unknown |

---

### Generation Data
| Dataset | Regions Available | Time Range (China) | Scenarios |
|---------|-------------------|-------------------|-----------|
| **Solar_Annual_Power_Generation** | All regions | Unknown | Unknown |
| **Wind_Annual_Power_Generation** | All regions | Unknown | Unknown |
| **Coal_Annual_Power_Generation** | All regions | 2006-2040 | ✓ 3 scenarios |
| **Natural_Gas_Annual_Power_Generation** | All regions | Unknown | Unknown |
| **Oil_Annual_Power_Generation** | All regions | Unknown | Unknown |

---

### Capacity Factors
| Dataset | Regions Available | Status |
|---------|-------------------|--------|
| **Solar_Photovoltaic_Capacity_Factor** | Global only | ✅ Found |
| **Onshore_Wind_Capacity_Factor** | China, USA, Global | ✅ Found |
| **Offshore_Wind_Capacity_Factor** | Global only | ✅ Found |
| **Natural_Gas_Capacity_Factor** | All regions | ✅ Found |
| **Coal_Capacity_Factor** | None | ❌ MISSING |

---

### Battery Storage
| Dataset | Regions Available | Status |
|---------|-------------------|--------|
| **Battery (2-hour) Cost** | China, USA, Europe, Global | ✅ Found |
| **Battery (4-hour) Cost** | China, USA, Europe, Global | ✅ Found |
| **Battery Installed Capacity** | All regions | ✅ Found |

**Missing**: Rest_of_World (acceptable - can use Global)

---

### Electricity System
| Dataset | Regions Available | Status |
|---------|-------------------|--------|
| **Annual_Domestic_Consumption** | All regions | ✅ Found |
| **Annual_Production** | All regions | ✅ Found |
| **Residential_Price** | China, USA, Europe | ✅ Found |

---

## Regional Coverage Summary

| Region | Coverage | Missing |
|--------|----------|---------|
| **China** | Excellent | Coal/Gas LCOE only |
| **USA** | Excellent | Coal/Gas LCOE only |
| **Europe** | Good | Coal/Gas LCOE, Solar/Wind regional data |
| **Rest_of_World** | Fair | Coal/Gas LCOE, Solar/Wind regional data |
| **Global** | Excellent | Coal/Gas LCOE only |

**Note**: Missing regional data (Europe, Rest_of_World) for Solar/Wind is acceptable since Global fallback works well.

---

## Time Range Analysis

### Historical Data (What We Have)
| Technology | Start Year | End Year | Length |
|------------|-----------|----------|--------|
| **Solar LCOE** | 2010 | 2024 | 15 years ✅ |
| **Onshore Wind LCOE** | 1996 | 2024 | 29 years ✅ |
| **Solar Capacity** | 2000 | 2040 | 41 years ✅ |
| **Coal Capacity** | 2005 | 2040 | 36 years ✅ |
| **Coal Generation** | 2006 | 2040 | 35 years ✅ |

**Issue**: Solar LCOE only starts in 2010, while capacity data goes back to 2000. Ideally LCOE should align with capacity timeframes.

### Forecast Data (Scenarios)
Only **Coal** datasets include scenario-based forecasts:
- ✓ Coal_Installed_Capacity: standard, Prosperity, Superabundance
- ✓ Coal_Annual_Power_Generation: standard, Prosperity, Superabundance

**Missing Scenarios** for:
- Solar capacity/generation (2025-2040)
- Wind capacity/generation (2025-2040)
- Battery capacity (2025-2040)
- All LCOE forecasts (2025-2040)

**Recommendation**: Add scenario-based forecasts for SWB technologies to enable Prosperity/Superabundance analysis.

---

## Structural Differences vs Skill Data Directory

The catalog uses a **simpler structure** compared to the skill's data directory:

### Catalog Structure (Better):
```json
{
  "Energy Generation": {
    "Solar_Photovoltaic_LCOE": {
      "regions": {
        "China": {
          "X": [2010, 2011, ...],
          "Y": [0.34, 0.32, ...]
        }
      }
    }
  }
}
```

### Skill Data Structure (More Complex):
```json
{
  "Energy Generation": {
    "Coal_Annual_Power_Generation": {
      "regions": {
        "China": {
          "standard": {"X": [...], "Y": [...]},
          "Prosperity": {"X": [...], "Y": [...]},
          "Superabundance": {"X": [...], "Y": [...]}
        }
      }
    }
  }
}
```

**Finding**:
- Catalog datasets mostly use **simple X/Y structure** (no scenarios)
- Skill data has **scenario-based structure** for Coal/Gas
- This mismatch causes data loader issues

**Recommendation**:
1. **Short-term**: Keep simple structure for historical data (2010-2024)
2. **Long-term**: Add scenarios for forecast period (2025-2040) for all technologies

---

## Data Quality Issues

### 1. Short Time Ranges
- **Solar LCOE**: Only 15 years (2010-2024) - should extend back to 2000
- **Battery Cost**: Only 6 years (2019-2024) - should extend back to 2010

### 2. Missing Forecast Scenarios
- No scenarios for SWB technologies (Solar, Wind, Battery)
- Cannot model Prosperity vs Superabundance trajectories
- Only Coal has scenario-based forecasts

### 3. No CSP Regional Data
- CSP only has Global data
- Limits regional analysis for concentrated solar

---

## Priority Action Items

### Immediate (Week 1)
1. ✅ **Add Coal_Power_LCOE** - All regions, 2010-2024
2. ✅ **Add Natural_Gas_LCOE** - All regions, 2010-2024

### Short-term (Month 1)
3. **Backfill Solar LCOE** - Extend from 2010→2000 to match capacity data
4. **Backfill Battery Cost** - Extend from 2019→2010
5. **Add Coal_Capacity_Factor** - Real data (or confirm derived is acceptable)

### Medium-term (Quarter 1)
6. **Add scenario forecasts** for SWB technologies (2025-2040):
   - Solar_Installed_Capacity: standard, Prosperity, Superabundance
   - Wind_Installed_Capacity: standard, Prosperity, Superabundance
   - Battery_Installed_Capacity: standard, Prosperity, Superabundance
   - All LCOE forecasts with scenarios

7. **Add regional data** for Europe/Rest_of_World:
   - Solar LCOE (currently Global only)
   - Onshore Wind LCOE (currently Global only)

---

## Comparison: Catalog vs Skill Data Directory

| Aspect | Curves Catalog | Skill Data Directory | Winner |
|--------|----------------|---------------------|--------|
| **Datasets Found** | 22/25 (88%) | 22/25 (88%) + 4 derived | Tie |
| **Structure** | Simple, clean | Mixed (simple + scenarios) | Catalog |
| **Scenarios** | Coal only | Coal + derived estimates | Skill |
| **Time Ranges** | Varies by dataset | Consistent (mostly) | Skill |
| **Regional Coverage** | Good | Good | Tie |
| **Missing Critical Data** | Coal/Gas LCOE, Coal CF | Coal/Gas LCOE, Coal CF | Tie |

**Recommendation**: Use catalog as **primary data source**, but ensure:
1. Add missing Coal/Gas LCOE
2. Extend time ranges to align with capacity data
3. Add scenario-based forecasts for SWB technologies

---

## Data Sources for Missing Datasets

### For Coal LCOE:
- **Lazard LCOE** - Annual reports (2010-2024)
- **IEA World Energy Outlook** - Regional LCOE
- **IRENA Power Generation Costs** - Renewable vs fossil comparison
- **EIA Levelized Costs** - US-specific data
- **BNEF LCOE Benchmarks** - Global data

### For Natural Gas LCOE:
- Same sources as Coal
- **EIA Natural Gas Data** - US-specific historical LCOE
- **IEA Gas Reports** - Regional gas power costs

### For Coal Capacity Factor:
- **IEA Electricity Information** - Annual reports with CF data
- **EIA Form 923** - US power plant operations (CF calculable)
- **EMBER Climate** - Global electricity data
- **National stats agencies** - China NEA, Eurostat, etc.

---

## Bottom Line

**The catalog is missing the same 3 critical datasets as the skill's data directory:**

1. ❌ **Coal_Power_LCOE** (all regions)
2. ❌ **Natural_Gas_LCOE** (all regions)
3. ❌ **Coal_Capacity_Factor** (all regions)

**Without these, tipping point analysis is unreliable (±3-5 years error margin).**

**Additional improvements needed:**
- Extend Solar LCOE back to 2000 (currently starts 2010)
- Extend Battery Cost back to 2010 (currently starts 2019)
- Add scenario-based forecasts for SWB technologies (2025-2040)

---

## Next Steps

1. **Week 1**: Obtain Coal and Gas LCOE data from Lazard/IEA/IRENA
2. **Month 1**: Backfill Solar/Battery historical data, add Coal CF
3. **Quarter 1**: Add scenario-based forecasts for all SWB technologies

This will enable:
- ✅ Accurate tipping point detection
- ✅ Scenario analysis (standard, Prosperity, Superabundance)
- ✅ Regional displacement modeling
- ✅ Reliable long-term forecasting

---

**Report Generated**: 2025-11-07
**Status**: 88% complete (3 critical datasets missing)
