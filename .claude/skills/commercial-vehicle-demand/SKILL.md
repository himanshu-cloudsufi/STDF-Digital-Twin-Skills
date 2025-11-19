# Commercial Vehicle Demand Forecasting Skill

## Overview

This skill forecasts commercial vehicle (CV) demand with EV disruption analysis, segment-level tipping point detection, and NGV (Natural Gas Vehicle) chimera modeling.

### Market Segments
- **LCV** (Light Duty Commercial Vehicles): Vans, small trucks
- **MCV** (Medium Duty Commercial Vehicles): Medium trucks, delivery vehicles
- **HCV** (Heavy Duty Commercial Vehicles): Large trucks, heavy haulers

### Powertrains
- **EV** (Electric Vehicles): Battery-electric disruptor
- **ICE** (Internal Combustion Engine): Incumbent technology
- **NGV** (Natural Gas Vehicles): Transitional "chimera" technology

### Regions
- China
- USA
- Europe
- Rest_of_World
- Global (aggregated)

### Time Horizon
- Historical: 2015-2024
- Forecast: 2025-2040 (configurable)

## Key Features

### 1. Segment-Level Analysis
- Independent forecasting for LCV, MCV, HCV
- Segment-specific tipping points (cost parity years)
- Differentiated EV adoption ceilings:
  - LCV: 95% (easier to electrify)
  - MCV: 85% (moderate challenges)
  - HCV: 75% (range/weight constraints)

### 2. Tipping Point Detection
- Cost curve forecasting with 3-year rolling median smoothing
- Log-CAGR extrapolation for cost trends
- Automatic detection of EV-ICE cost parity year per segment
- Different tipping points reflect segment-specific economics

### 3. NGV Chimera Modeling
- Peak detection in historical NGV data
- Exponential decline with 6-year half-life (configurable)
- Constraint: near-zero share by 2040
- Triggers after max(peak_year, tipping_point)

### 4. Logistic EV Adoption
- S-curve modeling post-tipping point
- Differential evolution optimization for curve fitting
- Segment-specific growth rates and inflection points

### 5. Multi-Level Aggregation
- Segment level: EV + ICE + NGV = Segment Total
- Product level: LCV + MCV + HCV = Total CV
- Regional level: Sum to Global

### 6. Fleet Tracking (Optional)
- Stock-flow accounting for vehicle fleets
- Segment-specific lifetimes:
  - LCV: 12 years
  - MCV: 15 years
  - HCV: 18 years

## Installation

### Prerequisites
```bash
python3 -m pip install -r requirements.txt
```

Required packages:
- numpy >= 1.20.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- matplotlib >= 3.4.0

### Data Requirements
- `Commercial_Vehicle.json`: Historical cost and demand curves
- `commercial_vehicle_taxonomy_and_datasets.json`: Dataset definitions
- `commercial_vehicle_demand_instructions.md`: Methodology documentation

## Usage

### Basic Forecast (Single Segment)
```bash
python3 scripts/forecast.py --region China --segment LCV --end-year 2040 --output csv
```

### All Segments
```bash
python3 scripts/forecast.py --region USA --all-segments --end-year 2040 --output both
```

### With Fleet Tracking
```bash
python3 scripts/forecast.py --region Europe --segment MCV --track-fleet --output json
```

### Using Shell Script
```bash
./run_forecast.sh China all 2040 csv         # All segments
./run_forecast.sh USA LCV 2035 json          # Single segment
```

## Command-Line Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--region` | string | *required* | China, USA, Europe, Rest_of_World |
| `--segment` | string | all | LCV, MCV, or HCV (omit for all) |
| `--all-segments` | flag | false | Forecast all segments |
| `--end-year` | int | 2040 | Final forecast year |
| `--output` | string | csv | Output format: csv, json, or both |
| `--output-dir` | string | ./output | Output directory path |
| `--track-fleet` | flag | false | Enable fleet evolution tracking |
| `--ngv-half-life` | float | 6.0 | NGV decline half-life (years) |

## Output Formats

### CSV Structure (Segment-Level)
```csv
Region,Segment,Year,Market,EV,ICE,NGV,EV_Share,ICE_Share,NGV_Share,EV_Fleet,ICE_Fleet,NGV_Fleet,Total_Fleet
China,LCV,2025,1500000,150000,1200000,150000,0.10,0.80,0.10,1800000,14000000,1500000,17300000
China,LCV,2030,1600000,500000,950000,150000,0.31,0.59,0.09,3500000,12000000,1400000,16900000
...
China,Total_CV,2040,5000000,3500000,1300000,200000,0.70,0.26,0.04,42000000,15000000,1000000,58000000
```

### JSON Structure
```json
{
  "region": "China",
  "segment_results": {
    "LCV": {
      "cost_analysis": {
        "tipping_point": 2028,
        "ev_cagr": -0.05,
        "ice_cagr": 0.01
      },
      "demand_forecast": {
        "years": [2020, 2021, ...],
        "market": [1000000, 1050000, ...],
        "ev": [50000, 75000, ...],
        "ngv_metadata": {...}
      }
    }
  },
  "total_cv": {...}
}
```

## Methodology

### Phase 1: Cost Analysis (Per Segment)
1. Load segment-specific cost curves (EV: range-adjusted, ICE: price)
2. Apply 3-year rolling median smoothing
3. Forecast costs using log-CAGR extrapolation
4. Detect tipping point (year when EV crosses below ICE)

### Phase 2: Demand Forecasting (Per Segment)
1. **Market Growth**: Theil-Sen regression with ±5% CAGR cap
2. **EV Adoption**:
   - Pre-tipping: Linear extrapolation of historical share
   - Post-tipping: Logistic S-curve with segment-specific ceiling
3. **NGV Modeling**:
   - Detect peak year in historical data
   - Apply exponential decline: `share(t) = peak_share * exp(-ln(2) * (t - t0) / half_life)`
4. **ICE Residual**: `ICE = Market - EV - NGV`

### Phase 3: Validation
- Non-negativity checks
- Sum consistency: EV + ICE + NGV ≈ Market (±2% tolerance)
- Share bounds: 0 ≤ share ≤ 1.0
- Segment aggregation: LCV + MCV + HCV ≈ Total CV

### Phase 4: Fleet Tracking (Optional)
- Stock-flow accounting: `Fleet(t) = Fleet(t-1) + Sales(t) - Scrappage(t)`
- Scrappage rate: `Fleet(t-1) / lifetime_years`

## Scenarios

### Baseline
- Moderate EV adoption following cost parity
- LCV: 95%, MCV: 85%, HCV: 75% ceilings
- NGV: 6-year half-life

### Accelerated EV
- Policy support, faster adoption
- LCV: 98%, MCV: 90%, HCV: 80% ceilings
- NGV: 5-year half-life (faster decline)
- Tipping acceleration: -2 years

### Conservative
- Infrastructure constraints, slower adoption
- LCV: 90%, MCV: 75%, HCV: 65% ceilings
- NGV: 7-year half-life (persists longer)
- Tipping delay: +3 years

## Key Insights

### Segment Differences
- **LCV tipping earliest**: Lower upfront costs, shorter routes → faster EV adoption
- **HCV tipping latest**: Higher costs, range anxiety, payload impact → slower adoption
- **MCV in between**: Moderate challenges

### NGV Dynamics
- Peak typically in 2020-2025 (China especially)
- Serves as bridge technology during EV cost decline
- Policy-driven (subsidies, clean air mandates)
- Declines as EV total cost of ownership improves

### Regional Variations
- **China**: Strongest NGV presence, rapid EV policy push
- **USA**: Limited NGV, diesel dominance, slower transition
- **Europe**: Emissions regulations drive faster EV adoption

## Troubleshooting

### Common Issues

**1. "Dataset not found in taxonomy"**
- Solution: Verify data file names match taxonomy definitions
- Check: `data/commercial_vehicle_taxonomy_and_datasets.json`

**2. "No tipping point found"**
- Meaning: EV costs remain above ICE through forecast horizon
- Expected for HCV in some regions (very high battery costs)

**3. "Sum consistency violated"**
- Cause: Numerical precision in segment aggregation
- Tolerance: ±2% acceptable
- Check NGV modeling if larger discrepancy

**4. "Negative values detected"**
- Rare edge case in residual ICE calculation
- Usually due to overly aggressive EV + NGV shares
- Review segment-specific ceilings

### Data Quality Checks
```bash
# Verify data loader
python3 scripts/data_loader.py

# Test cost analysis
python3 scripts/cost_analysis.py

# Test demand forecasting
python3 scripts/demand_forecast.py
```

## Advanced Configuration

### Custom Segment Ceilings
Edit `config.json`:
```json
{
  "logistic_ceiling": {
    "LCV": 0.97,  // More aggressive
    "MCV": 0.80,  // More conservative
    "HCV": 0.70
  }
}
```

### Custom Fleet Lifetimes
```json
{
  "fleet_tracking": {
    "lcv_lifetime_years": 10.0,  // Shorter for delivery vans
    "mcv_lifetime_years": 15.0,
    "hcv_lifetime_years": 20.0   // Longer for heavy trucks
  }
}
```

### NGV Decline Rate
```bash
python3 scripts/forecast.py --region China --all-segments --ngv-half-life 5.0
```

## References

### Methodology Documents
- `reference/methodology-reference.md`: Detailed algorithms
- `reference/parameters-reference.md`: Parameter catalog with sensitivity
- `reference/output-formats-reference.md`: Schema specifications
- `reference/data-schema-reference.md`: Input data requirements

### Evaluation Scenarios
- `evaluations/eval_lcv_forecast.json`: Light duty test
- `evaluations/eval_mcv_forecast.json`: Medium duty test
- `evaluations/eval_hcv_forecast.json`: Heavy duty test
- `evaluations/eval_all_segments.json`: Full aggregation test

## Version History

### v1.0.0 (2024)
- Initial release
- LCV, MCV, HCV segment support
- NGV chimera modeling
- Multi-level aggregation
- Fleet tracking option

## Support

For issues or questions:
1. Check troubleshooting section
2. Review reference documentation
3. Examine evaluation scenarios for examples
4. Verify data quality using test scripts

## License

CloudSufi Analytics (c) 2024
