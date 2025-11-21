# Parameters Reference

Complete catalog of all parameters used in cost-driven demand forecasting, including defaults, valid ranges, and when to override.

## Contents
- Required Parameters
- Optional Parameters
- Advanced Configuration
- When to Override Defaults
- Parameter Interactions

---

## Required Parameters

### region
**Description**: Geographic region to analyze

**Type**: String

**Valid values**:
- `"China"` - People's Republic of China
- `"USA"` - United States of America
- `"Europe"` - European market (aggregated)
- `"Rest_of_World"` - All regions excluding China, USA, Europe
- `"Global"` - Worldwide aggregate (runs all regions and sums)

**Usage**:
```bash
--region China
```

**Notes**:
- Each region is analyzed independently with its own cost curves and tipping point
- `"Global"` automatically processes all individual regions and aggregates results
- Regional data must exist in Passenger_Cars.json

---

## Optional Parameters

### end_year
**Description**: Final year for demand forecast horizon

**Type**: Integer

**Default**: `2040`

**Valid range**: `[2025, 2100]`

**Usage**:
```bash
--end-year 2030
```

**Notes**:
- Forecasts extend from last historical year to end_year
- Longer horizons (>2035) have higher uncertainty
- Cost curves and demand are extrapolated to this year

**When to override**:
- Short-term analysis: Use 2030 or 2035
- Extended analysis: Use 2040 (maximum recommended)
- Policy analysis: Match policy target year

---

### logistic_ceiling (L)
**Description**: Maximum BEV market share (asymptotic ceiling)

**Type**: Float

**Default**: `1.0` (100% market penetration)

**Valid range**: `[0.5, 1.0]`

**Usage**:
```bash
--ceiling 0.9
```

**Notes**:
- Represents maximum achievable BEV adoption
- L = 1.0 means BEVs can reach 100% of passenger vehicle market
- Lower values model infrastructure or policy constraints

**When to override**:
- **L = 0.9 (90%)**: Realistic scenario with good infrastructure but some market segments remain ICE (rural, niche uses)
- **L = 0.85 (85%)**: Conservative scenario with infrastructure gaps
- **L = 0.8 (80%)**: Constrained scenario with policy or physical limits
- **L = 1.0 (100%)**: Optimistic scenario with complete market transformation

**Regional considerations**:
- China: Often use L = 0.95 (strong policy support)
- USA: Consider L = 0.85 (infrastructure challenges, rural areas)
- Europe: Often use L = 0.9 (good infrastructure, policy support)
- Rest_of_World: Consider L = 0.8 (variable infrastructure)

---

### output
**Description**: Output format for forecast results

**Type**: String

**Default**: `"csv"`

**Valid values**:
- `"csv"` - Comma-separated values table
- `"json"` - JSON format with full metadata
- `"both"` - Export both CSV and JSON

**Usage**:
```bash
--output json
--output both
```

**Notes**:
- CSV is human-readable and Excel-compatible
- JSON includes metadata (tipping point, CAGRs, validation status)
- Use "both" for comprehensive analysis

---

### output_dir
**Description**: Directory path for output files

**Type**: String

**Default**: `"./output"`

**Usage**:
```bash
--output-dir ./forecasts/2024
```

**Notes**:
- Directory will be created if it doesn't exist
- Output files are named: `{region}_{end_year}.csv` or `.json`
- For Global forecasts, exports both global aggregate and individual regions

---

## Advanced Configuration

These parameters are defined in `config.json` and not exposed via command line. Modify config.json to change these values.

### smoothing_window
**Description**: Rolling median window size for cost curve smoothing

**Type**: Integer

**Default**: `3` years

**Valid range**: `[1, 7]` (odd numbers recommended)

**Purpose**: Remove noise from cost curves before tipping point detection

**When to adjust**:
- Increase (5 or 7) if cost data is very noisy
- Keep at 3 for typical analysis
- Do not use 1 (no smoothing) unless data is already clean

---

### max_market_cagr
**Description**: Maximum allowed market growth rate (compound annual growth rate)

**Type**: Float

**Default**: `0.05` (5% per year)

**Valid range**: `[0.02, 0.10]`

**Purpose**: Cap market forecast to prevent unrealistic growth or decline

**When to adjust**:
- Emerging markets with high growth: Consider 0.07 or 0.08
- Mature markets with slow growth: Keep at 0.05
- Declining markets: Lower bound is negative of this value

**Formula**:
```
-max_market_cagr ≤ actual_CAGR ≤ +max_market_cagr
```

---

### phev_peak_share
**Description**: Peak PHEV market share before decline

**Type**: Float

**Default**: `0.15` (15%)

**Valid range**: `[0.10, 0.25]`

**Purpose**: Maximum PHEV adoption in "hump" trajectory model

**When to adjust**:
- Regions with strong PHEV policy: Increase to 0.20 or 0.25
- Regions skipping PHEV phase: Decrease to 0.10
- Historical data-driven: Match observed peak

**Note**: Only used if PHEV forecast is generated (not from historical data)

---

### phev_decay_half_life
**Description**: Half-life for PHEV decline after tipping point

**Type**: Float

**Default**: `3.0` years

**Valid range**: `[2.0, 5.0]`

**Purpose**: Models how quickly PHEVs are replaced by BEVs post-tipping

**When to adjust**:
- Rapid BEV adoption: Use 2.0 years (fast PHEV decline)
- Gradual transition: Use 4.0 or 5.0 years
- Typical scenario: Keep at 3.0 years

**Formula**:
```
PHEV(t) = PHEV(tipping) × exp(-ln(2) / half_life × (t - tipping))
```

---

### logistic_k_bounds
**Description**: Bounds for logistic growth rate parameter k

**Type**: List of two floats `[k_min, k_max]`

**Default**: `[0.05, 1.5]`

**Valid range**: `[0.01, 3.0]`

**Purpose**: Constrains steepness of BEV adoption S-curve

**Parameter interpretation**:
- **k = 0.05**: Very gradual growth (50+ years from 10% to 90%)
- **k = 0.2**: Moderate growth (25 years from 10% to 90%)
- **k = 0.5**: Rapid growth (10 years from 10% to 90%)
- **k = 1.0**: Very rapid growth (5 years from 10% to 90%)
- **k = 1.5**: Explosive growth (3-4 years from 10% to 90%)

**When to adjust**:
- Allow wider range `[0.05, 2.0]` for flexible fitting
- Narrow range `[0.1, 0.8]` for conservative scenarios
- Keep default `[0.05, 1.5]` for typical analysis

---

### logistic_t0_offset
**Description**: Offset range for logistic inflection point t₀ relative to data range

**Type**: List of two integers `[offset_before, offset_after]`

**Default**: `[-5, 10]` years

**Valid range**: `[-10, 20]`

**Purpose**: Allows inflection point to occur before/after observed data range

**Parameter interpretation**:
- `t₀ ∈ [min(years) - 5, max(years) + 10]`
- Negative offset: Inflection can occur before data starts
- Positive offset: Inflection can occur after data ends

**When to adjust**:
- Early adoption: Use `[-10, 5]` if inflection likely already occurred
- Late adoption: Use `[0, 20]` if inflection far in future
- Keep default `[-5, 10]` for typical fitting

---

## Validation Parameters

Defined in `config.json` under `validation_rules`.

### non_negative_demand
**Type**: Boolean

**Default**: `true`

**Purpose**: Enforce all demand values ≥ 0

**Note**: Should always be true for physical validity

---

### sum_consistency
**Type**: Boolean

**Default**: `true`

**Purpose**: Enforce BEV + PHEV + ICE ≤ Market (with small epsilon tolerance)

**Note**: Should always be true to ensure conservation of market demand

---

### market_cagr_cap
**Type**: Float

**Default**: `0.05`

**Purpose**: Duplicate of `max_market_cagr` for validation

**Note**: Keep synchronized with `max_market_cagr`

---

### share_bounds
**Type**: List of two floats `[min, max]`

**Default**: `[0.0, 1.0]`

**Purpose**: Enforce all market shares within [0%, 100%]

**Note**: Should always be `[0.0, 1.0]` for physical validity

---

## When to Override Defaults

### Use Cases for Custom Parameters

**Short-term policy analysis (2030):**
```bash
--region USA --end-year 2030 --ceiling 0.7 --output both
```
Rationale: Near-term forecast with realistic ceiling for current infrastructure

**Optimistic long-term scenario (2040):**
```bash
--region Europe --end-year 2030 --ceiling 1.0 --output json
```
Rationale: Full market transformation over extended horizon

**Conservative infrastructure-constrained scenario:**
```bash
--region Rest_of_World --end-year 2030 --ceiling 0.75 --output csv
```
Rationale: Limited infrastructure development caps adoption

**China high-growth scenario:**
```bash
--region China --end-year 2035 --ceiling 0.95 --output both
```
Rationale: Strong policy support and rapid infrastructure buildout

---

## Parameter Interactions

### Ceiling vs End Year

**Relationship**: Longer horizons allow lower k values to still reach ceiling

- `ceiling=1.0, end_year=2035`: Requires k ≈ 0.4-0.6 to reach 100%
- `ceiling=1.0, end_year=2030`: Can use k ≈ 0.3-0.5 (more gradual)
- `ceiling=0.8, end_year=2030`: Lower ceiling reached with smaller k

### Ceiling vs PHEV Peak

**Relationship**: Higher BEV ceiling leaves less room for PHEV peak

- If `ceiling=1.0` and `phev_peak_share=0.20`: BEV + PHEV can exceed 100% temporarily (will be clamped)
- If `ceiling=0.85`: PHEV can reach 15-20% before BEV dominates
- Ensure `ceiling + phev_peak_share ≤ 1.1` for realistic trajectories

### K Bounds vs Data Quality

**Relationship**: Noisy or sparse data requires tighter k bounds

- Clean, dense data: Can use wide bounds `[0.05, 1.5]`
- Sparse data (<5 points): Narrow bounds `[0.2, 0.8]` for stability
- Very noisy data: Use tighter bounds and increase smoothing_window

### Market CAGR Cap vs Region

**Relationship**: Mature vs emerging markets have different growth potential

- Mature markets (USA, Europe): 3-5% growth is realistic
- Emerging markets (parts of Rest_of_World): 5-8% growth possible
- Declining markets: May need negative CAGR (handled by ±cap)

---

## Parameter Checklist

Before running a forecast, verify:

- [ ] Region matches available data in Passenger_Cars.json
- [ ] End year is reasonable (typically 2030-2035)
- [ ] Ceiling reflects infrastructure reality (0.85-1.0)
- [ ] Output format matches intended use (csv for Excel, json for analysis)
- [ ] Advanced parameters in config.json are appropriate for region
- [ ] Validation rules are enabled (should always be true)

---

## Default Configuration Summary

From `config.json`:

```json
{
  "end_year": 2030,
  "logistic_ceiling": 1.0,
  "smoothing_window": 3,
  "max_market_cagr": 0.05,
  "phev_peak_share": 0.15,
  "phev_decay_half_life": 3.0,
  "logistic_k_bounds": [0.05, 1.5],
  "logistic_t0_offset": [-5, 10]
}
```

These defaults work well for most analysis scenarios. Override only when specific regional or scenario characteristics warrant it.
