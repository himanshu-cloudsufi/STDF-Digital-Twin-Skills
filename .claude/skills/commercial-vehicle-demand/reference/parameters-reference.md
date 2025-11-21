# Commercial Vehicle Demand Forecasting - Parameters Reference

## Configuration Parameters

### Segment-Specific Parameters

#### EV Adoption Ceilings
| Segment | Default | Range | Description |
|---------|---------|-------|-------------|
| LCV | 0.95 | 0.85-0.99 | Light duty - easier electrification |
| MCV | 0.85 | 0.75-0.92 | Medium duty - moderate constraints |
| HCV | 0.75 | 0.65-0.85 | Heavy duty - range/payload challenges |

**Sensitivity**: ±5% ceiling → ±3-5% final EV share

#### Fleet Lifetimes
| Segment | Default (years) | Range | Description |
|---------|----------------|-------|-------------|
| LCV | 12 | 10-15 | Delivery vans, light trucks |
| MCV | 15 | 12-18 | Medium trucks, distribution |
| HCV | 18 | 15-22 | Heavy haulers, long-haul |

**Impact**: Longer lifetime → slower fleet turnover → slower EV penetration in fleet

### NGV Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| half_life_years | 6.0 | 4.0-8.0 | Years for NGV share to halve |
| peak_detection_window | 5 | 3-7 | Smoothing window for peak detection |
| target_share_2035 | 0.0 | 0.0-0.05 | Maximum NGV share by 2035 |
| min_significant_share | 0.01 | 0.005-0.02 | Threshold for NGV presence |

**Sensitivity**: ±1 year half-life → ±15-20% change in 2030 NGV share

### Market Forecasting

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| max_market_cagr | 0.05 | 0.03-0.10 | Maximum annual market growth |
| smoothing_window | 3 | 3-5 | Years for rolling median |
| end_year | 2040 | 2030-2050 | Final forecast year |

**Sensitivity**: ±1% CAGR → ±8-12% change in 2040 market size

### Logistic Curve Fitting

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| k_bounds | [0.05, 1.5] | - | Growth rate bounds |
| t0_offset | [-5, 10] | - | Inflection point offset from tipping |
| optimization_iterations | 1000 | 500-2000 | Max iterations for fitting |
| convergence_tolerance | 1e-6 | - | Stopping criterion |

**Sensitivity**: k parameter most sensitive - affects adoption speed

### Validation Tolerances

| Check | Tolerance | Description |
|-------|-----------|-------------|
| Sum consistency | 2% | EV+ICE+NGV ≈ Market |
| Segment aggregation | 2% | LCV+MCV+HCV ≈ Total |
| Share bounds | [0, 1.0] | Valid probability range |
| Non-negativity | 0 | All values >= 0 |

## Scenario Configurations

### Baseline
```json
{
  "logistic_ceiling": {"LCV": 0.95, "MCV": 0.85, "HCV": 0.75},
  "market_growth_factor": 1.0,
  "ngv_half_life": 6.0
}
```

### Accelerated EV
```json
{
  "logistic_ceiling": {"LCV": 0.98, "MCV": 0.90, "HCV": 0.80},
  "market_growth_factor": 1.1,
  "ngv_half_life": 5.0,
  "tipping_acceleration": -2
}
```

### Conservative
```json
{
  "logistic_ceiling": {"LCV": 0.90, "MCV": 0.75, "HCV": 0.65},
  "market_growth_factor": 0.95,
  "ngv_half_life": 7.0,
  "tipping_delay": 3
}
```

## Calibration Guidance

### When to Adjust Ceilings
- **Increase** if: Strong policy support, robust charging infrastructure, declining battery costs
- **Decrease** if: Infrastructure gaps, high electricity costs, payload/range concerns

### When to Adjust NGV Half-Life
- **Shorter** (4-5 years) if: Rapid EV policy push, NGV subsidies ending
- **Longer** (7-8 years) if: Continued NGV investment, slow EV infrastructure build-out

### When to Adjust Market CAGR
- **Higher** (6-8%) if: Economic boom, freight demand surge, urbanization
- **Lower** (2-4%) if: Economic slowdown, efficiency gains reduce vehicle needs

## Regional Variations

### China
- Strong policy-driven EV adoption
- Significant NGV presence (peak 2020-2022)
- Suggested LCV ceiling: 0.97

### USA
- Limited NGV penetration
- Diesel dominance in HCV
- Suggested HCV ceiling: 0.70

### Europe
- Stringent emissions regulations
- Faster transition expected
- Suggested overall: +5% all ceilings

### Rest of World
- More conservative assumptions
- Infrastructure constraints
- Suggested overall: -5% all ceilings

## See Also

- `SKILL.md`: Usage and examples
- `methodology-reference.md`: Algorithm details
- `config.json`: Configuration file format
