# Scenarios Reference

## Contents
- Pre-Configured Scenarios
- Scenario Comparison Workflow
- Creating Custom Scenarios
- Scenario Parameter Modifications

---

## Pre-Configured Scenarios

The skill includes four pre-configured scenarios modeling different future pathways:

### 1. Baseline
**Description**: Moderate EV adoption with standard replacement cycles

**Key Assumptions**:
- Historical EV adoption trends continue
- Battery lifetimes remain at current averages (4.5 years SLI)
- Asset lifetimes follow typical scrappage patterns
- Standard lead coefficients apply

**Use Case**: Reference scenario for planning and comparison

**Run Command**:
```bash
python3 scripts/forecast.py --region Global --scenario baseline
```

---

### 2. Accelerated EV
**Description**: Faster electrification with reduced lead demand per vehicle

**Key Modifications**:
- Accelerated EV adoption rates (higher BEV/EV market share)
- Greater impact on lead demand reduction
- Faster ICE fleet decline

**Impact**: Lower total lead demand as EVs replace ICE vehicles

**Use Case**: Modeling aggressive climate policies or rapid technology adoption

**Run Command**:
```bash
python3 scripts/forecast.py --region China --scenario accelerated_ev
```

---

### 3. Extended Lifecycles
**Description**: Longer battery and vehicle lifetimes reduce replacement demand

**Key Modifications**:
- Extended battery lifetimes (e.g., 6 years vs 4.5 years for SLI)
- Longer asset lifetimes (slower scrappage)
- Reduced replacement demand frequency

**Impact**:
- Lower replacement demand (fewer battery cycles)
- Lower total lead demand
- Higher installed base (vehicles stay on road longer)

**Use Case**: Modeling technology improvements or economic downturn (delayed purchases)

**Run Command**:
```bash
python3 scripts/forecast.py --region Europe --scenario extended_lifecycles
```

---

### 4. High Growth
**Description**: Increased vehicle sales and higher total demand

**Key Modifications**:
- Higher vehicle sales growth rates
- Faster fleet expansion
- Increased total lead consumption

**Impact**: Higher total lead demand across all segments

**Use Case**: Modeling developing market expansion or economic boom

**Run Command**:
```bash
python3 scripts/forecast.py --region India --scenario high_growth
```

---

## Scenario Comparison Workflow

To compare multiple scenarios side-by-side:

```bash
# Step 1: Run each scenario
python3 scripts/forecast.py --region Global --scenario baseline
python3 scripts/forecast.py --region Global --scenario accelerated_ev
python3 scripts/forecast.py --region Global --scenario extended_lifecycles

# Step 2: Compare scenarios
python3 scripts/compare_scenarios.py --region Global \
                                      --scenarios baseline accelerated_ev extended_lifecycles \
                                      --output-report output/scenario_comparison.txt \
                                      --output-plots output/plots
```

**Comparison Outputs**:
- Differential analysis vs baseline (absolute and percentage differences)
- Growth rate comparisons across scenarios
- Share evolution (battery vs non-battery, SLI vs industrial)
- Comparative visualizations (line charts, stacked areas)
- Summary tables quantifying scenario divergence

---

## Creating Custom Scenarios

To create a custom scenario:

### Method 1: Modify config.json

1. **Open config.json** in the skill directory
2. **Locate the scenarios section**:
```json
"scenarios": {
    "baseline": {
        "EV_share_modifier": 1.0,
        "battery_life_modifier": 1.0,
        "sales_growth_modifier": 1.0
    },
    "your_custom_scenario": {
        "EV_share_modifier": 1.5,
        "battery_life_modifier": 1.2,
        "sales_growth_modifier": 0.8
    }
}
```

3. **Add your custom scenario** with appropriate modifiers
4. **Run forecast** with the new scenario name:
```bash
python3 scripts/forecast.py --region Global --scenario your_custom_scenario
```

### Method 2: Parameter Overrides

Modify specific parameters directly in config.json without creating a named scenario:

**Example**: Model 50% higher EV adoption
```json
"lead_coefficients": {
    "Passenger_Vehicle_BEV_kg": 9.0  # Keep BEV coefficient
},
"market_shares": {
    "BEV_share_2030": 0.45  # Increase from baseline 0.30
}
```

---

## Scenario Parameter Modifications

Common parameter modifications for scenario design:

### EV Adoption Rate
**Parameter**: EV market share projections
**Effect**: Higher EV share → lower lead demand per vehicle
**Typical Range**: 10-60% by 2035

**Example**:
- Baseline: 30% BEV by 2035
- Accelerated: 50% BEV by 2035
- Conservative: 15% BEV by 2035

---

### Battery Lifetime
**Parameter**: `battery_lifetimes` → `sli` (years)
**Effect**: Longer lifetime → lower replacement frequency → lower total demand
**Typical Range**: 3-7 years

**Example**:
- Baseline: 4.5 years
- Extended: 6.0 years
- Tropical climate: 3.5 years (heat stress)

**Formula Impact**:
```
Replacement_Demand = IB / Battery_Life
```
Doubling battery life halves replacement demand.

---

### Vehicle Sales Growth
**Parameter**: Sales growth rate (implicit in sales data)
**Effect**: Higher sales → higher OEM demand → higher installed base → higher replacement demand
**Typical Range**: -2% to +8% annual growth

**Example**:
- Baseline: 2% annual growth
- High growth: 5% annual growth
- Recession: -1% annual growth

---

### Lead Coefficients
**Parameter**: `lead_coefficients` → vehicle type and powertrain
**Effect**: Higher coefficient → higher demand per vehicle
**Typical Range**: See [PARAMETERS.md](PARAMETERS.md)

**Example** (modeling premium battery segment):
- Baseline passenger ICE: 11.5 kg
- Premium ICE: 13.5 kg (+17%)

---

## Scenario Analysis Best Practices

### 1. Always Run Baseline First
Baseline provides the reference point for all comparisons.

### 2. Vary One Dimension at a Time
To isolate effects:
- Scenario A: Baseline
- Scenario B: Only EV adoption changed
- Scenario C: Only battery lifetime changed

### 3. Document Scenario Assumptions
Use `evidence_register.py` to document parameter sources and rationale.

### 4. Validate Scenario Plausibility
Check that:
- EV shares + ICE shares = 100%
- Parameter values remain within realistic bounds
- Trends are consistent with policy/technology trajectories

### 5. Quantify Uncertainty
Run sensitivity analysis on key parameters:
```bash
python3 scripts/sensitivity_analysis.py --region Global --scenario baseline
```

This identifies which parameters have the largest impact on forecast uncertainty.

---

## Scenario Naming Conventions

For clarity when managing multiple scenarios:

**Good naming**:
- `baseline_2024`
- `high_ev_china`
- `extended_life_europe`
- `policy_compliant_usa`

**Avoid**:
- `scenario1`, `test`, `final` (not descriptive)
- Names with spaces or special characters
- Very long names (>30 characters)

---

## Example Use Cases

### Use Case 1: Policy Impact Assessment
**Question**: What is the impact of mandating 40% EV sales by 2030?

**Approach**:
1. Run baseline (current policy)
2. Create scenario with 40% EV share by 2030
3. Use `compare_scenarios.py` to quantify difference
4. Focus on 2025-2035 period

---

### Use Case 2: Technology Roadmap
**Question**: How much would 2-year longer battery life reduce demand?

**Approach**:
1. Baseline with 4.5-year SLI battery life
2. Extended lifecycle with 6.5-year battery life
3. Calculate percentage reduction in replacement demand
4. Assess impact on total demand

---

### Use Case 3: Regional Divergence
**Question**: How will China vs Europe lead demand evolve?

**Approach**:
1. Run China baseline and China accelerated_ev
2. Run Europe baseline and Europe accelerated_ev
3. Compare regional trajectories
4. Highlight policy/market differences driving divergence
