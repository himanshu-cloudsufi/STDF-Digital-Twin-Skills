---
name: datacenter-ups
description: >
  Forecasts datacenter UPS battery technology transition from VRLA (lead-acid) to Lithium-ion based on TCO economics.
  Use when analyzing datacenter battery demand, UPS technology transition, VRLA vs Li-ion adoption, or backup power systems.
  Handles regions: China, USA, Europe, Rest_of_World, Global.
  Models S-curve adoption driven by Total Cost of Ownership (TCO) parity, with VRLA 5-year vs Li-ion 12-year lifespans.
  Tracks installed base, new-build demand, and replacement demand for both technologies.
  Trigger keywords: datacenter ups, ups batteries, VRLA lithium, datacenter battery transition, backup power, TCO analysis. (project)
---

# Datacenter UPS Battery Technology Transition Skill

This skill models the economic-driven transition from VRLA (Valve-Regulated Lead-Acid) to Lithium-ion batteries in datacenter UPS (Uninterruptible Power Supply) systems, using TCO-based tipping point analysis and S-curve adoption modeling.

## Overview

The skill forecasts battery demand for datacenter backup power systems across two competing technologies:
- **VRLA (Incumbent)**: Lower CapEx (~$220/kWh), higher OpEx ($18/kWh-yr), 5-year lifespan
- **Lithium-ion (Disruptor)**: Declining CapEx, lower OpEx ($6/kWh-yr), 12-year lifespan

## Key Features

### TCO-Driven Analysis
- **Total Cost of Ownership**: CapEx + PV(OpEx) + Replacement Costs over 15-year horizon
- **Tipping Point Detection**: Year when Li-ion TCO ≤ VRLA TCO (sustained for 3+ years)
- **Cost Forecasting**: Log-CAGR for Li-ion decline, flat trajectory for VRLA

### Market Decomposition
- **New-Build Demand**: Batteries for newly constructed datacenters
- **Replacement Demand**: End-of-life replacements from installed base
- **Contestable Market**: VRLA reaching 5-year life can switch to Li-ion

### S-Curve Adoption Model
- **Logistic Function**: M(t) = L / (1 + exp(-k × (t - t0)))
- **Economic Sensitivity**: Steepness k linked to cost advantage
- **Technology Ceiling**: L = 90-99% (residual VRLA niche)

### Installed Base Accounting
- Separate tracking for VRLA and Li-ion stocks
- Technology-specific retirement rates (VRLA: 5y, Li-ion: 12y)
- Mass balance reconciliation

## Usage

```bash
# Run the datacenter UPS forecast
skill datacenter-ups

# With custom parameters
skill datacenter-ups --end-year 2040 --region China

# Generate TCO comparison
skill datacenter-ups --analyze-tco --output-format csv
```

## Parameters

Key parameters configured in `config.json`:
- **Cost Parameters**:
  - VRLA CapEx: ~$220/kWh (flat)
  - Li-ion CapEx: Uses BESS 4-hour turnkey costs as proxy
  - OpEx: VRLA $18/kWh-yr, Li-ion $6/kWh-yr
- **Lifespans**:
  - VRLA: 5 years
  - Li-ion: 12 years
- **S-Curve Parameters**:
  - L: Technology ceiling (0.90-0.99)
  - t0: Midpoint year
  - k0: Base adoption rate
  - s: Cost sensitivity factor
- **Financial**:
  - Discount rate: 8% (6-10% range)
  - TCO horizon: 15 years

## Outputs

The skill generates:
1. Annual battery demand by technology (MWh)
2. TCO comparison ($/kWh) over time
3. Tipping point year identification
4. Installed base evolution (VRLA vs Li-ion)
5. New-build vs replacement breakdown
6. Adoption curve (Li-ion market share)
7. Regional analysis and aggregation

## Data Requirements

### Available Datasets
- **Demand**: `Data_Center_Battery_Demand_(Li-Ion/LAB)_Annual_Capacity_Demand_<region>`
- **Costs**: `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>` (Li-ion proxy)
- **Costs**: `VRLA_Battery_Cost_Global` (flat ~$220/kWh)
- **Growth**: `Datacenter_UPS_annual_growth_<region>` (7-10% typical)
- **Installed Base**: `Data_Center_Battery_Demand_(LAB)_Installed_base_<region>`

### Missing/Initialized
- Li-ion installed base often starts at 0 (conservative)
- Regional cost adjustments applied where needed

## Validation

The skill validates:
- VRLA_Demand + Li_Demand ≈ Total_Market_Demand (±5%)
- Mass balance: Adds - Retirements = ΔIB (±0.1%)
- Non-negativity constraints on all stocks and flows
- S-curve monotonicity and bounds

## Scenarios

Pre-configured scenarios:
- **Baseline**: Current cost trajectories, moderate adoption
- **Accelerated**: Faster Li-ion cost decline, early tipping
- **Delayed**: Slower cost parity, extended VRLA dominance
- **High OpEx**: Emphasize operational cost advantages

## Regional Considerations

- **China**: Lower costs, faster adoption typical
- **USA**: Moderate costs, reliability focus
- **Europe**: Higher costs, sustainability drivers
- **Rest_of_World**: Varied, often follows USA trends
- **Global**: Aggregate of regional results (avoid double-counting)

## Technical Details

- **Horizon**: 10-15 years typical, extendable to 2040
- **Time Step**: Annual
- **Primary Unit**: MWh/year (flows), MWh (stocks)
- **Duration**: 4-hour default for UPS systems
- **Cycles**: ~250/year for backup use
- **Round-trip Efficiency**: 88% for Li-ion

## Cost Data Adaptation

Using grid-scale BESS costs as UPS proxy:
- Duration match: Both 4-hour systems
- Cycle life: UPS cycles less (backup only)
- Reliability premium: Optional 5-10% adjustment
- Directional trends matter most for tipping point

## Examples

### Example 1: Single Region TCO Analysis (China)

**Objective:** Forecast datacenter UPS battery demand in China through 2040 and identify Li-ion tipping point

**Command:**
```bash
cd .claude/skills/datacenter-ups
python3 scripts/forecast.py --region China --end-year 2040 --output both
```

**Process:**
1. **Load Historical Data:**
   - VRLA costs: Flat ~$220/kWh
   - Li-ion costs: From BESS 4-hour turnkey proxy (declining from ~$400/kWh to ~$180/kWh)
   - OpEx: VRLA $18/kWh-yr, Li-ion $6/kWh-yr
   - Datacenter growth: 8-10% annual

2. **TCO Calculation:**
   - VRLA TCO (15yr): CapEx + 3 replacements (5yr life) + PV(OpEx)
   - Li-ion TCO (15yr): CapEx + 1 partial replacement (12yr life) + PV(OpEx)
   - Tipping point detected: ~2027 (Li-ion TCO < VRLA TCO sustained 3+ years)

3. **Demand Forecast:**
   - New-build demand: 7-10% annual growth
   - Replacement demand: VRLA contestable market (5yr cycles)
   - S-curve adoption: L=95%, t0=2027, k=0.4
   - 2040 result: 85% Li-ion share, 15% residual VRLA

**Output:**
- `output/datacenter_ups_China_2040.csv` - Annual demand (MWh) by technology
- `output/datacenter_ups_China_2040.json` - Full TCO analysis, tipping point, adoption curve

**Key Insights:**
- China's tipping point occurs ~2027 due to rapid Li-ion cost decline
- Replacement demand dominates post-2030 (70% of total)
- VRLA retains 10-15% niche (legacy systems, low-criticality sites)

---

### Example 2: USA Gas-Peaker Comparison

**Objective:** Compare datacenter UPS transition in USA with baseline vs accelerated Li-ion cost decline

**Command:**
```bash
# Baseline scenario
python3 scripts/forecast.py --region USA --scenario baseline --end-year 2040 --output csv

# Accelerated scenario (faster Li-ion decline)
python3 scripts/forecast.py --region USA --scenario accelerated --end-year 2040 --output csv

# Compare outputs
python3 scripts/compare_scenarios.py output/datacenter_ups_USA_baseline_2040.csv \
                                      output/datacenter_ups_USA_accelerated_2040.csv
```

**Process:**
1. **Baseline:** Tipping point ~2028, 80% Li-ion by 2040
2. **Accelerated:** Tipping point ~2025, 92% Li-ion by 2040
3. **Differential:** 3-year earlier tipping → 12 pp higher adoption

**Key Insights:**
- USA has higher VRLA costs (~$240/kWh) → earlier tipping vs global average
- OpEx savings drive rapid adoption in hyperscale datacenters
- Replacement market creates ~5-year lag in full transition

---

### Example 3: Global Aggregation with Sensitivity Analysis

**Objective:** Generate global forecast and test sensitivity to discount rate and Li-ion lifespan

**Command:**
```bash
# Global forecast (aggregates all regions)
python3 scripts/forecast.py --region Global --end-year 2040 --output both

# Sensitivity: Lower discount rate (6% vs 8%)
python3 scripts/forecast.py --region Global --discount-rate 0.06 --output csv

# Sensitivity: Extended Li-ion life (15yr vs 12yr)
python3 scripts/forecast.py --region Global --li-ion-lifespan 15 --output csv
```

**Results:**
| Scenario | Tipping Point | 2040 Li-ion Share | 2040 Total Demand (GWh) |
|----------|---------------|-------------------|------------------------|
| Baseline (8%, 12yr) | 2027 | 83% | 45 GWh |
| Low Discount (6%, 12yr) | 2026 | 87% | 45 GWh |
| Extended Life (8%, 15yr) | 2025 | 89% | 45 GWh |

**Key Insights:**
- Discount rate sensitivity: ±2% → ±1 year tipping, ±4 pp adoption
- Lifespan sensitivity: +3 years → -2 year tipping, +6 pp adoption
- Total market size driven by datacenter growth, not technology mix

---

## Troubleshooting

### Issue: "No tipping point detected within forecast horizon"

**Cause:** Li-ion costs remain higher than VRLA TCO throughout 2020-2040

**Solution:**
1. Verify Li-ion cost data loaded correctly:
   ```bash
   python3 scripts/validate_data.py --dataset "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_China"
   ```
2. Check VRLA cost assumptions (should be ~$220/kWh flat)
3. Extend forecast horizon:
   ```bash
   python3 scripts/forecast.py --region Rest_of_World --end-year 2050
   ```
4. Review OpEx assumptions (VRLA $18/kWh-yr vs Li-ion $6/kWh-yr)

**Note:** Rest_of_World may have delayed tipping due to higher financing costs and lower datacenter growth.

---

### Issue: "Installed base reconciliation failed"

**Cause:** Mass balance error: Adds - Retirements ≠ ΔInstalled_Base (>0.1% tolerance)

**Solution:**
1. Check for missing historical installed base data:
   ```bash
   python3 scripts/validate_data.py --check-installed-base --region China
   ```
2. Verify retirement rates match lifespans:
   - VRLA: IB / 5 years
   - Li-ion: IB / 12 years
3. Run with `--allow-ib-smoothing` flag to apply 3-year rolling adjustment:
   ```bash
   python3 scripts/forecast.py --region Europe --allow-ib-smoothing --output csv
   ```

---

### Issue: "S-curve fitting failed - parameters unrealistic"

**Cause:** Insufficient historical Li-ion adoption data or extreme cost trajectories

**Solution:**
1. Check historical adoption data quality:
   ```bash
   python3 scripts/inspect_data.py --dataset "Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_USA"
   ```
2. Use fallback heuristics for parameter initialization:
   - L (ceiling): 0.90-0.99 (default 0.95)
   - t0 (midpoint): tipping_year + 7 (heuristic)
   - k (steepness): 0.3-0.5 (default 0.4)
3. Manually override in `config.json`:
   ```json
   {
     "s_curve_overrides": {
       "Europe": {"L": 0.92, "t0": 2030, "k": 0.38}
     }
   }
   ```

---

### Issue: "TCO calculation returns negative values"

**Cause:** Invalid cost inputs or extreme parameter combinations

**Solution:**
1. Validate cost data non-negativity:
   ```bash
   python3 scripts/validate_data.py --check-costs --region USA
   ```
2. Check discount rate (should be 0.06-0.10, i.e., 6-10%)
3. Verify lifespan parameters:
   - VRLA: 3-7 years (default 5)
   - Li-ion: 10-15 years (default 12)
4. Review OpEx assumptions (should be positive)

---

### Issue: "Regional data missing or incomplete"

**Cause:** Some regions lack full historical datacenter or battery cost data

**Solution:**
1. Check data availability:
   ```bash
   python3 scripts/data_coverage.py --region Rest_of_World
   ```
2. Use proxy data from similar regions:
   - Rest_of_World → Use USA costs with +10% adjustment
   - Europe → Often complete, use as-is
3. Run with `--allow-proxy-data` flag:
   ```bash
   python3 scripts/forecast.py --region Rest_of_World --allow-proxy-data --output csv
   ```

---

## Common Analysis Patterns

### Pattern 1: Regional TCO Comparison

**Input:** "Compare datacenter UPS transition across China, USA, and Europe"

**Approach:**
```bash
# Run forecasts for each region
for region in China USA Europe; do
  python3 scripts/forecast.py --region $region --end-year 2040 --output csv
done

# Extract key metrics
python3 scripts/extract_metrics.py --regions China USA Europe \
                                    --metrics tipping_point,2040_li_share,2040_total_demand \
                                    --output output/regional_comparison.csv
```

**Analysis Focus:**
- Tipping point variance (China ~2027, USA ~2028, Europe ~2029)
- Cost drivers: China has lower Li-ion costs, USA has higher electricity costs
- Adoption rate differences: USA hyperscale vs Europe colocation mix

---

### Pattern 2: Sensitivity to OpEx Assumptions

**Input:** "How sensitive is the tipping point to operational cost differences?"

**Approach:**
```bash
# Baseline OpEx (VRLA $18, Li-ion $6)
python3 scripts/forecast.py --region Global --output csv

# Low OpEx differential (VRLA $15, Li-ion $8)
python3 scripts/forecast.py --region Global \
                             --vrla-opex 15 --li-ion-opex 8 \
                             --output csv

# High OpEx differential (VRLA $20, Li-ion $5)
python3 scripts/forecast.py --region Global \
                             --vrla-opex 20 --li-ion-opex 5 \
                             --output csv

# Compare tipping points
python3 scripts/compare_tipping.py output/datacenter_ups_Global_*.csv
```

**Expected Results:**
- Baseline: Tipping ~2027
- Low differential: Tipping ~2029 (2-year delay)
- High differential: Tipping ~2025 (2-year advance)
- **Insight:** OpEx advantage is critical for near-term tipping

---

### Pattern 3: Replacement Demand Decomposition

**Input:** "What share of demand is replacement vs new-build in 2035?"

**Approach:**
```bash
# Run with detailed output flag
python3 scripts/forecast.py --region USA --end-year 2040 --detailed-output --output json

# Extract replacement breakdown
python3 scripts/extract_demand.py --results output/datacenter_ups_USA_2040.json \
                                   --year 2035 \
                                   --breakdown new_build,replacement \
                                   --output output/demand_breakdown_2035.csv
```

**Typical Results (2035):**
- New-build: 25-30% of total demand
- Replacement: 70-75% of total demand
- **Insight:** Installed base drives demand post-2030; contestable VRLA market is key

---

### Pattern 4: Lifespan Extension Impact

**Input:** "What if Li-ion lifespan reaches 15 years instead of 12?"

**Approach:**
```bash
# Baseline (12-year Li-ion life)
python3 scripts/forecast.py --region Global --li-ion-lifespan 12 --output csv

# Extended (15-year Li-ion life)
python3 scripts/forecast.py --region Global --li-ion-lifespan 15 --output csv

# Calculate impact
python3 scripts/compare_scenarios.py --baseline output/datacenter_ups_Global_2040_12yr.csv \
                                      --scenario output/datacenter_ups_Global_2040_15yr.csv \
                                      --metrics tipping,adoption,total_demand
```

**Expected Impact:**
- Tipping point: -2 years earlier (better TCO)
- 2040 adoption: +6-8 pp (faster transition)
- Total demand: -5-8% (lower replacement frequency)
- **Insight:** Lifespan improvements accelerate adoption but reduce total battery demand

---

### Pattern 5: Scenario Planning for Industry Reports

**Input:** "Create baseline, accelerated, and delayed scenarios for 2030 report"

**Workflow Checklist:**
```
Scenario Planning Progress:
- [ ] Step 1: Define scenario parameters in config.json
- [ ] Step 2: Run all three scenarios
- [ ] Step 3: Generate comparison table
- [ ] Step 4: Create visualization plots
- [ ] Step 5: Export summary for report
```

**Step 1: Define scenarios in `config.json`**
```json
{
  "scenarios": {
    "baseline": {
      "li_ion_cagr": -0.08,
      "datacenter_growth": 0.09,
      "s_curve_ceiling": 0.95
    },
    "accelerated": {
      "li_ion_cagr": -0.12,
      "datacenter_growth": 0.11,
      "s_curve_ceiling": 0.98
    },
    "delayed": {
      "li_ion_cagr": -0.05,
      "datacenter_growth": 0.07,
      "s_curve_ceiling": 0.85
    }
  }
}
```

**Step 2: Run all scenarios**
```bash
for scenario in baseline accelerated delayed; do
  python3 scripts/forecast.py --region Global --scenario $scenario --end-year 2030 --output both
done
```

**Step 3: Generate comparison**
```bash
python3 scripts/scenario_comparison.py --scenarios baseline accelerated delayed \
                                        --output output/scenario_comparison_2030.csv
```

**Step 4: Create plots**
```bash
python3 scripts/visualize.py --comparison output/scenario_comparison_2030.csv \
                              --plot-types adoption_curve,demand_stack,tco_trajectory \
                              --output-dir output/plots
```

**Step 5: Export summary**
```bash
python3 scripts/export_summary.py --comparison output/scenario_comparison_2030.csv \
                                   --format markdown \
                                   --output output/executive_summary.md
```

---

## References

Based on:
- Datacenter UPS market analysis
- Battery technology cost curves
- TCO methodology for technology transitions
- S-curve adoption modeling literature

## Reference Documentation

- [reference/methodology-reference.md](reference/methodology-reference.md) - Detailed TCO calculation, S-curve fitting algorithms
- [reference/parameters-reference.md](reference/parameters-reference.md) - Complete parameter catalog and sensitivity ranges
- [reference/output-formats-reference.md](reference/output-formats-reference.md) - CSV/JSON schema specifications
- [reference/data-schema-reference.md](reference/data-schema-reference.md) - Input data requirements and taxonomy mappings
- [reference/troubleshooting-reference.md](reference/troubleshooting-reference.md) - Extended troubleshooting guide with advanced diagnostics