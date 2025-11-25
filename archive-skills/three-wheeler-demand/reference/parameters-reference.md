# Parameters Reference - Three-Wheeler Demand Forecasting

## Configuration File: config.json

### Core Parameters

#### `end_year`
- **Type**: Integer
- **Default**: 2040
- **Range**: 2025-2035
- **Description**: Final year of forecast horizon
- **Usage**: `--end-year 2030`

#### `logistic_ceiling`
- **Type**: Float
- **Default**: 0.9 (90%)
- **Range**: 0.5-1.0
- **Description**: Maximum EV adoption share in logistic S-curve
- **Usage**: `--ceiling 0.9`
- **Notes**:
  - 1.0 = 100% EV adoption
  - 0.9 = 90% EV adoption (10% ICE remains)
  - Lower values model infrastructure/preference constraints

#### `smoothing_window`
- **Type**: Integer
- **Default**: 3
- **Range**: 1-7 (odd numbers preferred)
- **Description**: Window size for rolling median smoothing of cost curves
- **Impact**: Larger values = smoother curves, less responsive to recent changes

#### `max_market_cagr`
- **Type**: Float
- **Default**: 0.05 (5%)
- **Range**: 0.01-0.10
- **Description**: Maximum allowed CAGR for market growth (positive or negative)
- **Purpose**: Prevents unrealistic exponential growth/decline in extrapolation

#### `logistic_k_bounds`
- **Type**: Array [min, max]
- **Default**: [0.05, 1.5]
- **Description**: Bounds for logistic growth rate parameter
- **Interpretation**:
  - 0.05 = very slow adoption
  - 0.4 = moderate adoption
  - 1.5 = rapid adoption

#### `logistic_t0_offset`
- **Type**: Array [min_offset, max_offset]
- **Default**: [-5, 10]
- **Description**: Allowed offset of inflection point from tipping year
- **Interpretation**: t0 ∈ [tipping - 5, tipping + 10]

### Regional Parameters

#### `regions`
- **Type**: Array of strings
- **Values**: ["China", "Europe", "Rest_of_World", "Global"]
- **Description**: Supported regions for forecasting
- **Notes**:
  - Global = sum of all regional forecasts
  - Process regions individually first
  - USA excluded (minimal three-wheeler market)

### Product Parameters

#### `products`
- **market**: "Three_Wheelers" (total market)
- **disruptor**: "EV_3_Wheelers"
- **incumbent**: "ICE_3_Wheelers"

### Cost Series Configuration

#### `cost_series`
- **ev_primary**: "EV_3_Wheeler_(Range-100_KM)_Lowest_Cost"
  - Used for primary tipping point detection
  - Represents affordable EV option
- **ev_secondary**: "Three_Wheeler_(EV)_Median_Cost"
  - Used for sensitivity analysis
  - Represents typical EV pricing
- **ice**: "Three_Wheeler_(ICE)_Median_Cost"
  - Baseline incumbent cost

### Fleet Tracking Parameters

#### `fleet_tracking.three_wheeler_lifetime_years`
- **Type**: Float
- **Default**: 10.0
- **Range**: 8-12
- **Description**: Average vehicle lifetime for fleet calculations
- **Source**: Commercial vehicle utilization studies
- **Notes**: Shorter than two-wheelers due to intensive commercial use

#### `fleet_tracking.track_consistency`
- **Type**: Boolean
- **Default**: true
- **Description**: Validate fleet stock-flow accounting

### Validation Rules

#### `validation_rules.non_negative_demand`
- **Type**: Boolean
- **Default**: true
- **Description**: Enforce all demand values ≥ 0

#### `validation_rules.sum_consistency`
- **Type**: Boolean
- **Default**: true
- **Description**: Enforce EV + ICE ≤ Market (within tolerance)

#### `validation_rules.market_cagr_cap`
- **Type**: Float
- **Default**: 0.05
- **Description**: Maximum market CAGR (same as max_market_cagr)

#### `validation_rules.share_bounds`
- **Type**: Array [min, max]
- **Default**: [0.0, 1.0]
- **Description**: Valid range for EV share

## Scenario Parameters

### Baseline Scenario
```json
{
  "logistic_ceiling": 0.9,
  "market_growth_factor": 1.0
}
```
- Moderate EV adoption
- No market acceleration
- Tipping point as detected

### Accelerated EV Scenario
```json
{
  "logistic_ceiling": 0.95,
  "market_growth_factor": 1.1,
  "tipping_acceleration": -2
}
```
- Higher EV ceiling (95%)
- 10% market growth boost
- Tipping point 2 years earlier

### Conservative Scenario
```json
{
  "logistic_ceiling": 0.75,
  "market_growth_factor": 0.95,
  "tipping_delay": 3
}
```
- Lower EV ceiling (75%)
- 5% market growth reduction
- Tipping point 3 years later

## Command Line Parameters

### Required

#### `--region`
- **Choices**: China, Europe, Rest_of_World, Global
- **Example**: `--region China`
- **Note**: USA not available for three-wheelers

### Optional

#### `--end-year`
- **Default**: 2040
- **Example**: `--end-year 2035`

#### `--ceiling`
- **Default**: 0.9
- **Example**: `--ceiling 0.85`

#### `--output`
- **Choices**: csv, json, both
- **Default**: csv
- **Example**: `--output both`

#### `--output-dir`
- **Default**: ./output
- **Example**: `--output-dir /path/to/results`

#### `--track-fleet`
- **Type**: Flag (boolean)
- **Default**: False
- **Example**: `--track-fleet`

## Modifying Parameters

### Via Command Line (Recommended)
```bash
python3 scripts/forecast.py \
  --region China \
  --end-year 2035 \
  --ceiling 0.85 \
  --track-fleet \
  --output both
```

### Via config.json (Advanced)
1. Open `.claude/skills/three-wheeler-demand/config.json`
2. Modify desired parameters
3. Save file
4. Run forecast (parameters will be inherited)

### Via Python API (Expert)
```python
from scripts.forecast import ForecastOrchestrator

orchestrator = ForecastOrchestrator(
    end_year=2035,
    logistic_ceiling=0.85,
    track_fleet=True
)
result = orchestrator.forecast_region("China")
```

## Parameter Sensitivity

### High Sensitivity Parameters
- `logistic_ceiling`: ±10% → ±8% final EV share
- `tipping_point`: ±2 years → ±5% share in 2030
- `max_market_cagr`: ±2% → ±15% market size by 2035

### Medium Sensitivity Parameters
- `logistic_k_bounds`: Affects adoption speed (±10% mid-period share)
- `smoothing_window`: Affects tipping year (±1 year)

### Low Sensitivity Parameters
- `fleet_tracking.lifetime_years`: Fleet size only (no demand impact)
- `validation tolerances`: Binary pass/fail only

## Recommendations

### For Conservative Analysis
- Set `ceiling` = 0.75-0.80
- Use `tipping_delay` = +2 to +5 years
- Reduce `market_growth_factor` = 0.95

### For Aggressive Analysis
- Set `ceiling` = 0.95-1.0
- Use `tipping_acceleration` = -2 to -3 years
- Increase `market_growth_factor` = 1.1-1.15

### For Robust Analysis
- Run multiple scenarios (baseline, conservative, aggressive)
- Use default parameters as central case
- Report uncertainty ranges

## Three-Wheeler Specific Considerations

### Commercial Use Impact
- Three-wheelers are primarily commercial vehicles
- TCO (Total Cost of Ownership) is critical
- May justify higher EV ceilings (0.95-1.0) due to cost sensitivity

### Regional Focus
- **China**: Urban delivery, rapid electrification
- **Rest_of_World (India)**: Large market, cost-driven adoption
- **Europe**: Emerging market, urban last-mile delivery

### Fleet Lifetime Notes
- 10-year lifetime reflects commercial intensity
- Higher utilization than personal vehicles
- May vary by region (8-12 years)
