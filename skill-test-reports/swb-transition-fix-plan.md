# SWB Transition Skill - Detailed Fix Implementation Plan

**Date:** 2025-11-13
**Status:** Approved for Implementation
**Estimated Timeline:** 6 weeks
**Priority:** High - Critical blockers prevent production use

---

## Overview

This document provides a detailed implementation plan to fix all critical issues, major gaps, and moderate issues identified in the SWB transition skill test report. The plan is organized into three phases with clear deliverables and success criteria.

---

## Phase 1: Critical Blockers (Week 1-2)

**Goal:** Fix issues that make the skill completely unusable for any analysis

### 1.1 Fix Emissions Calculation Unit Error ⚠️ CRITICAL

**Issue:** Emissions are off by factor of 1000× (shows 11 Mt vs actual 13,000 Mt)

**Location:** `forecast.py:373-385`

**Current Code:**
```python
emissions['coal'] = generation['coal'] * self.emission_factors['coal_kg_co2_per_mwh'] / 1e6
```

**Problem:**
- TWh × kg/MWh gives wrong units
- Missing conversion: TWh → MWh (×1e6)

**Fix:**
```python
def calculate_emissions(self, generation):
    """Calculate CO2 emissions from generation mix"""
    emissions = {}

    # Convert TWh to MWh, multiply by kg/MWh, divide by 1000 to get Mt
    for tech, emission_factor_key in [
        ('coal', 'coal_kg_co2_per_mwh'),
        ('gas', 'gas_kg_co2_per_mwh'),
        ('solar', 'solar_kg_co2_per_mwh'),
        ('wind', 'wind_kg_co2_per_mwh')
    ]:
        if tech in generation:
            gen_twh = generation[tech]
            emission_factor = self.emission_factors[emission_factor_key]
            # TWh × 1e6 MWh/TWh × kg/MWh / 1e6 kg/Mt = TWh × kg/MWh / 1000
            emissions[tech] = gen_twh * emission_factor / 1000  # Mt

    # Calculate SWB emissions (solar + wind)
    emissions['swb'] = emissions.get('solar', 0) + emissions.get('wind', 0)

    # Calculate fossil emissions
    emissions['fossil'] = emissions.get('coal', 0) + emissions.get('gas', 0)

    # Total emissions
    emissions['total'] = emissions['fossil'] + emissions['swb']

    return emissions
```

**Validation:**
- Global 2020 total emissions should be ≈ 13,000 Mt CO₂ (±10%)
- China 2020 coal emissions ≈ 4,500 Mt CO₂
- USA 2020 total emissions ≈ 1,600 Mt CO₂

**Test Case:**
```python
# Known: 1000 TWh at 1000 kg/MWh = 1,000,000 Mt CO₂
assert calculate_emissions({'coal': 1000}) == {'coal': 1000, ...}
```

**Time Estimate:** 2 hours
**Priority:** P0 - Blocking

---

### 1.2 Load Real Fossil Fuel LCOE Data ⚠️ CRITICAL

**Issue:** Coal and gas LCOE hardcoded at $100/MWh, making tipping point analysis invalid

**Location:** `data_loader.py:37-48`, `forecast.py:124-150`

**Current Behavior:**
- Falls back to `pd.Series(100, index=self.years)` when data missing
- Silent failure - no warning to user

**Root Cause Analysis Needed:**
1. Check if `Coal_Power_LCOE_Derived` and `Gas_Power_LCOE_Derived` exist in Energy_Generation.json
2. Verify `_extract_series` method correctly parses the data structure
3. Check for regional data availability

**Fix Strategy:**

**Step 1: Add data validation to data_loader.py**
```python
def load_lcoe_data(self):
    """Load LCOE data for all technologies"""
    data = self._load_json('Energy_Generation.json')
    gen_data = data.get('Energy Generation', {})

    lcoe_data = {
        'solar': self._extract_series(gen_data, 'Solar_Photovoltaic_LCOE'),
        'onshore_wind': self._extract_series(gen_data, 'Onshore_Wind_LCOE'),
        'offshore_wind': self._extract_series(gen_data, 'Offshore_Wind_LCOE'),
        'coal': self._extract_series(gen_data, 'Coal_Power_LCOE_Derived'),
        'gas': self._extract_series(gen_data, 'Gas_Power_LCOE_Derived')
    }

    # Validate critical data loaded
    for tech, data_dict in lcoe_data.items():
        if not data_dict or all(len(v) == 0 for v in data_dict.values()):
            print(f"WARNING: No LCOE data found for {tech}")
            if tech in ['coal', 'gas']:
                raise ValueError(f"CRITICAL: Missing LCOE data for {tech}. Cannot proceed with forecast.")

    return lcoe_data
```

**Step 2: Add derivation from capacity/generation if needed**
```python
def derive_lcoe_from_capacity_generation(self, tech, region):
    """
    Derive approximate LCOE if direct data unavailable
    Using capacity factor and typical cost assumptions
    """
    capacity = self.capacity_data[tech].get(region)
    generation = self.generation_data[tech].get(region)

    if capacity is None or generation is None:
        return None

    # Calculate implied capacity factor
    cf = generation / (capacity * 8760)

    # Typical LCOE ranges by technology
    lcoe_ranges = {
        'coal': {'base': 60, 'cf_factor': 0.8},  # Lower CF → higher LCOE
        'gas': {'base': 70, 'cf_factor': 0.6}
    }

    if tech in lcoe_ranges:
        base = lcoe_ranges[tech]['base']
        cf_factor = lcoe_ranges[tech]['cf_factor']
        # Adjust for capacity factor
        lcoe = base / (cf / cf_factor)
        return pd.Series(lcoe, index=capacity.index)

    return None
```

**Step 3: Update forecast.py to use derived data as fallback**
```python
def forecast_all_lcoe(self):
    """Forecast LCOE for all technologies"""
    lcoe_data = self.data['lcoe']
    forecasts = {}

    for tech in ['solar', 'onshore_wind', 'offshore_wind']:
        # Renewable forecasting (existing logic)
        ...

    for tech in ['coal', 'gas']:
        if self.region in lcoe_data[tech] and len(lcoe_data[tech][self.region]) > 0:
            # Use direct data
            hist_data = lcoe_data[tech][self.region]
        elif self.data_loader.can_derive_lcoe(tech, self.region):
            # Derive from other sources
            print(f"INFO: Deriving {tech} LCOE from capacity/generation data")
            hist_data = self.data_loader.derive_lcoe_from_capacity_generation(tech, self.region)
        else:
            # Last resort: Use Global data
            if 'Global' in lcoe_data[tech] and len(lcoe_data[tech]['Global']) > 0:
                print(f"WARNING: Using Global {tech} LCOE for {self.region}")
                hist_data = lcoe_data[tech]['Global']
            else:
                raise ValueError(f"CRITICAL: Cannot find or derive {tech} LCOE data")

        # Forecast forward (existing logic with cost change rate)
        forecasts[tech] = self.forecast_lcoe(hist_data, tech)

    return forecasts
```

**Validation:**
- Coal LCOE should vary by region: $60-100/MWh
- Gas LCOE should vary: $50-120/MWh depending on fuel prices
- Should show regional differences
- Should not be exactly $100/MWh for all years

**Time Estimate:** 8 hours
**Priority:** P0 - Blocking

---

### 1.3 Add Nuclear, Hydro, and Other Renewables ⚠️ CRITICAL

**Issue:** Missing ~30% of grid generation (nuclear 10%, hydro 16%, other 2-3%)

**Location:** `data_loader.py:63-73`, `forecast.py:246-371`

**Impact:** Total generation doesn't match reality, fossil share overestimated

**Implementation:**

**Step 1: Extend data_loader.py**
```python
def load_generation_data(self):
    """Load power generation data"""
    data = self._load_json('Energy_Generation.json')
    gen_data = data.get('Energy Generation', {})

    return {
        'solar': self._extract_series(gen_data, 'Solar_Annual_Power_Generation'),
        'wind': self._extract_series(gen_data, 'Wind_Annual_Power_Generation'),
        'coal': self._extract_series(gen_data, 'Coal_Annual_Power_Generation'),
        'gas': self._extract_series(gen_data, 'Natural_Gas_Annual_Power_Generation'),
        # NEW: Add baseline technologies
        'nuclear': self._extract_series(gen_data, 'Nuclear_Annual_Power_Generation'),
        'hydro': self._extract_series(gen_data, 'Hydro_Annual_Power_Generation'),
        'geothermal': self._extract_series(gen_data, 'Geothermal_Annual_Power_Generation'),
        'biomass': self._extract_series(gen_data, 'Biomass_Annual_Power_Generation'),
        'other_renewables': self._extract_series(gen_data, 'Other_Renewables_Annual_Power_Generation')
    }
```

**Step 2: Add baseline trajectory calculation to forecast.py**
```python
def calculate_baseline_trajectory(self):
    """
    Calculate trajectory for non-SWB, non-fossil technologies
    Nuclear: slight decline or flat
    Hydro: stable (capacity-constrained)
    Other: slight growth
    """
    generation_data = self.data['generation']
    baseline = {
        'nuclear': pd.Series(index=self.years, dtype=float),
        'hydro': pd.Series(index=self.years, dtype=float),
        'other': pd.Series(index=self.years, dtype=float)
    }

    for tech in ['nuclear', 'hydro']:
        if self.region in generation_data[tech]:
            hist = generation_data[tech][self.region]
        else:
            hist = generation_data[tech].get('Global', pd.Series())

        # Get annual change rate from config
        decline_rate = self.config['baseline_technologies'][tech].get('annual_change', 0.0)

        for year in self.years:
            if year in hist.index:
                baseline[tech][year] = hist[year]
            else:
                last_year = hist.index.max() if len(hist) > 0 else self.start_year
                last_value = hist[last_year] if len(hist) > 0 else 0
                years_ahead = year - last_year
                baseline[tech][year] = last_value * ((1 + decline_rate) ** years_ahead)

    # Other renewables (geothermal, biomass, etc.)
    other_techs = ['geothermal', 'biomass', 'other_renewables']
    baseline['other'] = pd.Series(0, index=self.years)
    for tech in other_techs:
        if self.region in generation_data.get(tech, {}):
            hist = generation_data[tech][self.region]
            # Project with slight growth (2% annually)
            for year in self.years:
                if year in hist.index:
                    baseline['other'][year] += hist[year]
                elif len(hist) > 0:
                    last_year = hist.index.max()
                    last_value = hist[last_year]
                    years_ahead = year - last_year
                    baseline['other'][year] += last_value * (1.02 ** years_ahead)

    return baseline
```

**Step 3: Update displacement calculation**
```python
def calculate_generation_displacement(self, swb_cost, coal_lcoe, gas_lcoe,
                                     tipping_vs_coal, tipping_vs_gas):
    """
    Calculate how SWB displaces fossil fuel generation over time
    NOW: Account for baseline (nuclear, hydro, other) first
    """
    # Get baseline trajectory
    baseline = self.calculate_baseline_trajectory()

    # Get total demand
    electricity_demand = self.data['electricity_demand']
    if self.region in electricity_demand:
        total_demand = electricity_demand[self.region]
    else:
        total_demand = electricity_demand.get('Global', pd.Series())

    results = {
        'solar': pd.Series(index=self.years, dtype=float),
        'wind': pd.Series(index=self.years, dtype=float),
        'coal': pd.Series(index=self.years, dtype=float),
        'gas': pd.Series(index=self.years, dtype=float),
        'nuclear': baseline['nuclear'],
        'hydro': baseline['hydro'],
        'other': baseline['other'],
        'total_demand': pd.Series(index=self.years, dtype=float)
    }

    for year in self.years:
        # Get total demand
        if year in total_demand.index:
            demand = total_demand[year]
        else:
            last_year = total_demand.index.max()
            last_demand = total_demand[last_year]
            years_ahead = year - last_year
            demand = last_demand * (1.02 ** years_ahead)

        results['total_demand'][year] = demand

        # Calculate residual demand after baseline technologies
        baseline_total = (baseline['nuclear'][year] +
                         baseline['hydro'][year] +
                         baseline['other'][year])

        residual_demand = demand - baseline_total

        # SWB and fossils compete to fill residual demand
        # (rest of logic similar to before, but now working with residual_demand)
        ...

    return results
```

**Step 4: Add to config.json**
```json
{
  "baseline_technologies": {
    "nuclear": {
      "annual_change": -0.01,
      "description": "Slight decline due to plant retirements"
    },
    "hydro": {
      "annual_change": 0.005,
      "description": "Stable, limited growth potential"
    },
    "geothermal": {
      "annual_change": 0.03,
      "description": "Modest growth"
    },
    "biomass": {
      "annual_change": 0.02,
      "description": "Slight growth"
    }
  }
}
```

**Step 5: Update output to include baseline technologies**
```python
# In forecast_transition method, add:
self.results['nuclear_generation_twh'] = generation['nuclear'].values
self.results['hydro_generation_twh'] = generation['hydro'].values
self.results['other_generation_twh'] = generation['other'].values
self.results['baseline_generation_twh'] = (
    generation['nuclear'] + generation['hydro'] + generation['other']
).values
self.results['baseline_share_pct'] = (
    (generation['nuclear'] + generation['hydro'] + generation['other']) /
    generation['total_demand'] * 100
).values
```

**Validation:**
- Global 2020: Nuclear ~2700 TWh (10%), Hydro ~4300 TWh (16%)
- Baseline + SWB + Fossil ≈ Total Demand (±2%)
- Check China: High hydro (~30%), growing nuclear
- Check USA: Significant nuclear (~20%), stable hydro

**Time Estimate:** 10 hours
**Priority:** P0 - Blocking

---

### 1.4 Fix Historical Generation Mix ⚠️ CRITICAL

**Issue:** Regional data doesn't match reality (China 85% gas vs 65% coal)

**Location:** `data_loader.py:28-35, 63-73`

**Root Cause:** Either data loading bug or data quality issue

**Investigation Steps:**

**Step 1: Add data inspection script**
```python
# scripts/inspect_data.py
import json
from pathlib import Path

def inspect_generation_data():
    """Inspect what's actually in the data files"""
    data_path = Path(__file__).parent.parent / 'data' / 'Energy_Generation.json'

    with open(data_path, 'r') as f:
        data = json.load(f)

    gen_data = data.get('Energy Generation', {})

    # Check what technologies exist
    print("Available metrics:")
    for key in gen_data.keys():
        if 'Generation' in key or 'LCOE' in key:
            print(f"  - {key}")
            if 'regions' in gen_data[key]:
                regions = list(gen_data[key]['regions'].keys())
                print(f"    Regions: {regions}")
                # Check China 2020 value
                if 'China' in gen_data[key]['regions']:
                    region_data = gen_data[key]['regions']['China']
                    if 'X' in region_data and 'Y' in region_data:
                        years = region_data['X']
                        values = region_data['Y']
                        if 2020 in years:
                            idx = years.index(2020)
                            print(f"    China 2020: {values[idx]}")

if __name__ == "__main__":
    inspect_generation_data()
```

**Step 2: Add validation to _extract_series**
```python
def _extract_series(self, data_dict, metric_name):
    """Extract time series with validation"""
    result = {}
    if metric_name in data_dict:
        regions_data = data_dict[metric_name].get('regions', {})
        for region, region_data in regions_data.items():
            if 'X' in region_data and 'Y' in region_data:
                years = region_data['X']
                values = region_data['Y']

                # Validation
                if len(years) != len(values):
                    print(f"WARNING: {metric_name} {region} has mismatched X/Y lengths")
                    continue

                if any(v < 0 for v in values):
                    print(f"WARNING: {metric_name} {region} has negative values")

                series = pd.Series(values, index=years, name=metric_name)
                result[region] = series
            else:
                print(f"WARNING: {metric_name} {region} missing X or Y data")
    else:
        print(f"WARNING: Metric {metric_name} not found in data")

    return result
```

**Step 3: Add sanity checks after data loading**
```python
def validate_generation_mix(self):
    """Validate loaded generation data matches expected reality"""
    gen_data = self.data['generation']

    # Known reality checks (2020 data)
    checks = {
        'China': {
            'coal': (0.55, 0.70),  # 55-70% coal
            'gas': (0.02, 0.08),   # 2-8% gas
            'hydro': (0.15, 0.35)  # 15-35% hydro
        },
        'USA': {
            'coal': (0.15, 0.25),  # 15-25% coal
            'gas': (0.35, 0.45),   # 35-45% gas
            'nuclear': (0.18, 0.22) # 18-22% nuclear
        },
        'Europe': {
            'coal': (0.10, 0.20),  # 10-20% coal
            'gas': (0.15, 0.25),   # 15-25% gas
            'nuclear': (0.20, 0.30) # 20-30% nuclear
        }
    }

    year = 2020
    for region, expected in checks.items():
        # Calculate total generation
        total = 0
        actual = {}
        for tech in ['coal', 'gas', 'nuclear', 'hydro', 'solar', 'wind']:
            if tech in gen_data and region in gen_data[tech]:
                if year in gen_data[tech][region].index:
                    val = gen_data[tech][region][year]
                    actual[tech] = val
                    total += val

        if total > 0:
            # Check shares
            for tech, (min_share, max_share) in expected.items():
                if tech in actual:
                    share = actual[tech] / total
                    if not (min_share <= share <= max_share):
                        print(f"WARNING: {region} {year} {tech} share {share:.1%} "
                              f"outside expected range [{min_share:.1%}, {max_share:.1%}]")
                        print(f"  This suggests data quality issues")
```

**Step 4: If data is correct, fix the allocation logic**

If inspection shows data is actually correct, the issue may be in how generation is allocated in `calculate_generation_displacement`. Need to review logic at forecast.py:318-330.

**Validation:**
- China 2020: ~65% coal, ~5% gas, ~18% hydro, ~9% wind, ~3% solar
- USA 2020: ~20% coal, ~40% gas, ~20% nuclear, ~7% hydro, ~13% renewables
- Europe 2020: ~15% coal, ~20% gas, ~25% nuclear, ~12% hydro, ~28% renewables

**Time Estimate:** 8 hours
**Priority:** P0 - Blocking

---

## Phase 2: Core Functionality (Week 3-4)

**Goal:** Add missing core features needed for meaningful analysis

### 2.1 Implement Capacity Forecasting

**Issue:** Only generation modeled, not infrastructure capacity (GW)

**Location:** `forecast.py` (new methods), output columns

**Approach:** Capacity should be primary variable, generation derived

**Implementation:**

**Step 1: Add capacity calculation from historical generation**
```python
def calculate_capacity_from_generation(self, generation, technology):
    """
    Derive capacity from generation using capacity factors
    Capacity_GW = Generation_TWh / (CF × 8760) × 1000
    """
    cf_config = self.capacity_factors.get(technology, {})
    base_cf = cf_config.get('base', 0.25)
    cf_improvement = cf_config.get('improvement_per_year', 0.0)
    max_cf = cf_config.get('max', 0.50)

    capacity = pd.Series(index=self.years, dtype=float)

    for year in self.years:
        # Calculate CF for this year
        years_since_start = year - self.start_year
        cf = min(base_cf + cf_improvement * years_since_start, max_cf)

        # Derive capacity
        if year in generation.index:
            gen_twh = generation[year]
            # Capacity_GW = Gen_TWh × 1000 GWh/TWh / (CF × 8760 hours)
            capacity[year] = gen_twh * 1000 / (cf * 8760)
        else:
            capacity[year] = 0

    return capacity
```

**Step 2: Forecast new capacity additions**
```python
def forecast_capacity_additions(self, technology, target_generation):
    """
    Calculate new capacity needed to meet generation targets
    Returns: capacity_additions_gw per year
    """
    capacity = pd.Series(index=self.years, dtype=float)
    additions = pd.Series(index=self.years, dtype=float)
    retirements = pd.Series(index=self.years, dtype=float)

    # Get initial capacity from historical data
    if self.region in self.data['capacity'][technology]:
        hist_capacity = self.data['capacity'][technology][self.region]
    else:
        # Derive from generation
        hist_gen = self.data['generation'][technology].get(self.region, pd.Series())
        hist_capacity = self.calculate_capacity_from_generation(hist_gen, technology)

    # Retirement assumptions
    retirement_rate = 0.02 if technology in ['coal', 'gas'] else 0.01  # 1-2% per year

    for i, year in enumerate(self.years):
        # Get target generation
        target_gen = target_generation[year]

        # Calculate required capacity
        cf = self.get_capacity_factor(technology, year)
        required_capacity = target_gen * 1000 / (cf * 8760)

        if i == 0:
            # First year: use historical
            capacity[year] = hist_capacity.get(year, required_capacity)
        else:
            prev_year = self.years[i - 1]
            prev_capacity = capacity[prev_year]

            # Retirements (% of existing capacity)
            retirements[year] = prev_capacity * retirement_rate

            # Net new capacity needed
            net_new = max(0, required_capacity - prev_capacity + retirements[year])
            additions[year] = net_new

            capacity[year] = prev_capacity + additions[year] - retirements[year]

    return {
        'capacity': capacity,
        'additions': additions,
        'retirements': retirements
    }
```

**Step 3: Integrate into main forecast**
```python
def forecast_transition(self):
    """Run complete SWB transition forecast"""
    # ... existing LCOE and cost calculations ...

    # Calculate generation (existing logic)
    generation = self.calculate_generation_displacement(...)

    # NEW: Calculate capacity for all technologies
    capacity_results = {}
    for tech in ['solar', 'wind', 'coal', 'gas', 'nuclear', 'hydro']:
        tech_key = 'onshore_wind' if tech == 'wind' else tech
        capacity_results[tech] = self.forecast_capacity_additions(
            tech_key,
            generation[tech]
        )

    # Store capacity results
    for tech in ['solar', 'wind', 'coal', 'gas', 'nuclear', 'hydro']:
        self.results[f'{tech}_capacity_gw'] = capacity_results[tech]['capacity'].values
        self.results[f'{tech}_new_capacity_gw'] = capacity_results[tech]['additions'].values
        self.results[f'{tech}_retired_capacity_gw'] = capacity_results[tech]['retirements'].values

    # Calculate and validate capacity factors
    for tech in ['solar', 'wind']:
        cf_series = pd.Series(index=self.years, dtype=float)
        for year in self.years:
            cf_series[year] = self.get_capacity_factor(tech, year)
        self.results[f'{tech}_capacity_factor'] = cf_series.values

    # ... rest of existing code ...
```

**Validation:**
- Generation ≈ Capacity × CF × 8760 (±5%)
- Capacity additions are positive and realistic (10-100 GW/year for major technologies)
- Total capacity growth matches generation growth

**Time Estimate:** 12 hours
**Priority:** P1 - Major Gap

---

### 2.2 Add Battery Storage Capacity Calculation

**Issue:** Storage capacity (GWh) not calculated, not scaled to renewable penetration

**Location:** `forecast.py` (new methods)

**Implementation:**

**Step 1: Calculate peak load**
```python
def calculate_peak_load(self, annual_demand_twh, load_factor=0.60):
    """
    Calculate peak load from annual demand
    Peak_Load_GW = Annual_TWh × 1000 / (8760 × Load_Factor)

    Typical load_factor: 0.55-0.65 (higher in industrial regions)
    """
    peak_load_gw = annual_demand_twh * 1000 / (8760 * load_factor)
    return peak_load_gw
```

**Step 2: Dynamic storage sizing**
```python
def calculate_battery_storage_requirements(self, swb_share, peak_load_gw):
    """
    Calculate battery storage requirements based on renewable penetration

    Storage days scale with penetration:
    - <30%: 0.25 days (6 hours)
    - 30-50%: 0.5-1 days
    - 50-70%: 1-2 days
    - >70%: 2-4 days

    Returns: dict with power_gw, energy_gwh, throughput_gwh_per_year
    """
    duration_hours = self.battery_sizing['duration_hours']
    cycles_per_year = self.battery_sizing['cycles_per_year']

    # Dynamic resilience days based on SWB penetration
    if swb_share < 0.30:
        k_days = 0.25
    elif swb_share < 0.50:
        k_days = 0.5 + (swb_share - 0.30) * 2.5  # Linear from 0.5 to 1.0
    elif swb_share < 0.70:
        k_days = 1.0 + (swb_share - 0.50) * 5.0  # Linear from 1.0 to 2.0
    else:
        k_days = 2.0 + (swb_share - 0.70) * 6.67  # Linear from 2.0 to 4.0
        k_days = min(k_days, 4.0)  # Cap at 4 days

    # Energy capacity (GWh) = days × peak_load × 24 hours/day
    energy_gwh = k_days * peak_load_gw * 24

    # Power capacity (GW) = energy / duration
    power_gw = energy_gwh / duration_hours

    # Annual throughput (GWh/year)
    throughput_gwh_per_year = energy_gwh * cycles_per_year

    return {
        'k_days': k_days,
        'power_gw': power_gw,
        'energy_gwh': energy_gwh,
        'throughput_gwh_per_year': throughput_gwh_per_year,
        'duration_hours': duration_hours
    }
```

**Step 3: Integrate into forecast**
```python
def forecast_transition(self):
    # ... existing code ...

    # Calculate battery storage requirements
    battery_storage = pd.DataFrame(index=self.years)

    for year in self.years:
        demand = generation['total_demand'][year]
        swb_gen = generation['solar'][year] + generation['wind'][year]
        swb_share = swb_gen / demand if demand > 0 else 0

        peak_load = self.calculate_peak_load(demand)

        storage = self.calculate_battery_storage_requirements(swb_share, peak_load)

        battery_storage.loc[year, 'peak_load_gw'] = peak_load
        battery_storage.loc[year, 'battery_storage_days'] = storage['k_days']
        battery_storage.loc[year, 'battery_power_gw'] = storage['power_gw']
        battery_storage.loc[year, 'battery_energy_gwh'] = storage['energy_gwh']
        battery_storage.loc[year, 'battery_throughput_gwh_per_year'] = storage['throughput_gwh_per_year']

    # Add to results
    self.results['peak_load_gw'] = battery_storage['peak_load_gw'].values
    self.results['battery_storage_days'] = battery_storage['battery_storage_days'].values
    self.results['battery_power_gw'] = battery_storage['battery_power_gw'].values
    self.results['battery_energy_gwh'] = battery_storage['battery_energy_gwh'].values
    self.results['battery_throughput_gwh_per_year'] = battery_storage['battery_throughput_gwh_per_year'].values
```

**Validation:**
- At 50% SWB: Storage ≈ 0.5-1 days × peak_load
- At 75% SWB: Storage ≈ 2-3 days × peak_load
- Battery energy should scale with demand and penetration

**Time Estimate:** 8 hours
**Priority:** P1 - Major Gap

---

### 2.3 Implement Carbon Pricing

**Issue:** Critical economic driver missing from fossil fuel costs

**Location:** `config.json`, `forecast.py`

**Implementation:**

**Step 1: Add to config.json scenarios**
```json
{
  "scenarios": {
    "baseline": {
      "carbon_price_2020": 30,
      "carbon_price_2040": 80,
      "carbon_price_growth": "linear",
      ...
    },
    "accelerated": {
      "carbon_price_2020": 50,
      "carbon_price_2040": 150,
      "carbon_price_growth": "exponential",
      ...
    },
    "delayed": {
      "carbon_price_2020": 10,
      "carbon_price_2040": 40,
      "carbon_price_growth": "linear",
      ...
    },
    "high_carbon_price": {
      "description": "Strong climate policy",
      "carbon_price_2020": 80,
      "carbon_price_2040": 200,
      ...
    }
  }
}
```

**Step 2: Add carbon price calculation**
```python
def calculate_carbon_price(self, year):
    """Calculate carbon price for given year based on scenario"""
    start_price = self.scenario.get('carbon_price_2020', 0)
    end_price = self.scenario.get('carbon_price_2040', 0)
    growth_type = self.scenario.get('carbon_price_growth', 'linear')

    if year <= 2020:
        return start_price
    elif year >= 2040:
        return end_price
    else:
        t = (year - 2020) / (2040 - 2020)

        if growth_type == 'linear':
            return start_price + (end_price - start_price) * t
        elif growth_type == 'exponential':
            # Exponential growth
            growth_rate = (end_price / start_price) ** (1/20) - 1
            years_since_2020 = year - 2020
            return start_price * ((1 + growth_rate) ** years_since_2020)
        else:
            return start_price + (end_price - start_price) * t
```

**Step 3: Add to fossil fuel costs**
```python
def forecast_all_lcoe(self):
    """Forecast LCOE for all technologies"""
    # ... existing renewable LCOE forecasting ...

    for tech in ['coal', 'gas']:
        # Get base LCOE (existing logic)
        base_lcoe = ...

        # Add carbon costs
        emission_factor = self.emission_factors[f'{tech}_kg_co2_per_mwh']

        forecasted_with_carbon = pd.Series(index=self.years, dtype=float)
        for year in self.years:
            carbon_price = self.calculate_carbon_price(year)
            # Carbon cost in $/MWh = carbon_price $/tCO2 × emission_factor kg/MWh / 1000 kg/t
            carbon_cost = carbon_price * emission_factor / 1000

            forecasted_with_carbon[year] = base_lcoe[year] + carbon_cost

        forecasts[tech] = forecasted_with_carbon
        forecasts[f'{tech}_base'] = base_lcoe  # Store base LCOE separately
        forecasts[f'{tech}_carbon_cost'] = forecasted_with_carbon - base_lcoe

    return forecasts
```

**Step 4: Update tipping point detection to use total cost**
```python
def detect_tipping_points(self, swb_cost, coal_total_lcoe, gas_total_lcoe):
    """
    Detect when SWB becomes cheaper than coal and gas
    Now using total cost including carbon pricing
    """
    # ... existing logic, no changes needed ...
```

**Validation:**
- Coal with $80/tCO2 → +$80/MWh
- Gas with $80/tCO2 → +$36/MWh
- Tipping points should shift earlier with higher carbon prices

**Time Estimate:** 6 hours
**Priority:** P1 - Major Gap

---

### 2.4 Add Capacity Factor Evolution

**Issue:** CF improvement defined but not calculated or used

**Location:** `forecast.py` (new method)

**Implementation:**

```python
def get_capacity_factor(self, technology, year):
    """
    Get capacity factor for a technology in a given year
    Accounts for technology improvement over time
    """
    cf_config = self.capacity_factors.get(technology, {})

    if not cf_config:
        # Default values for technologies without explicit config
        defaults = {
            'solar': 0.20,
            'onshore_wind': 0.30,
            'offshore_wind': 0.40,
            'coal': 0.60,
            'gas': 0.40,
            'nuclear': 0.90,
            'hydro': 0.45
        }
        return defaults.get(technology, 0.25)

    base = cf_config.get('base', 0.20)
    improvement = cf_config.get('improvement_per_year', 0.0)
    max_cf = cf_config.get('max', 0.50)

    # For fossil/nuclear/hydro, use typical value (no improvement)
    if technology in ['coal', 'gas', 'nuclear', 'hydro']:
        return cf_config.get('typical', base)

    # For renewables, calculate improvement
    years_since_start = year - self.start_year
    cf = base + improvement * years_since_start
    cf = min(cf, max_cf)

    return cf

def calculate_capacity_factor_trajectory(self):
    """Calculate CF trajectory for all technologies"""
    cf_results = {}

    for tech in ['solar', 'onshore_wind', 'offshore_wind', 'coal', 'gas', 'nuclear', 'hydro']:
        cf_series = pd.Series(index=self.years, dtype=float)
        for year in self.years:
            cf_series[year] = self.get_capacity_factor(tech, year)
        cf_results[tech] = cf_series

    return cf_results
```

**Integrate into forecast:**
```python
def forecast_transition(self):
    # ... existing code ...

    # Calculate capacity factors
    cf_trajectories = self.calculate_capacity_factor_trajectory()

    # Add to results
    for tech in ['solar', 'wind']:
        tech_key = 'onshore_wind' if tech == 'wind' else tech
        self.results[f'{tech}_capacity_factor'] = cf_trajectories[tech_key].values

    # Validate Generation ≈ Capacity × CF × 8760
    for tech in ['solar', 'wind']:
        gen = self.results[f'{tech}_generation_twh']
        cap = self.results[f'{tech}_capacity_gw']
        cf = self.results[f'{tech}_capacity_factor']

        # Expected generation
        expected_gen = cap * cf * 8760 / 1000  # GW × hours → TWh

        # Check if close
        diff_pct = abs(gen - expected_gen) / expected_gen * 100
        if diff_pct.max() > 10:
            print(f"WARNING: {tech} generation/capacity mismatch (max {diff_pct.max():.1f}%)")
```

**Validation:**
- Solar CF: 2020: ~20% → 2040: ~25%
- Wind CF: 2020: ~30% → 2040: ~35%
- Offshore Wind CF: 2020: ~40% → 2040: ~48%
- Gen = Cap × CF × 8760 / 1000 (within 5%)

**Time Estimate:** 6 hours
**Priority:** P1 - Major Gap

---

## Phase 3: Enhancements (Week 5-6)

**Goal:** Remove limitations, add sophistication, improve quality

### 3.1 Remove Hardcoded Limits

**Issue:** 75% SWB maximum, fixed solar/wind split, static reserve floors

**Changes needed:**

**Step 1: Make max_swb_share scenario-dependent**
```json
{
  "scenarios": {
    "baseline": {
      "max_swb_share": 0.75,
      "reserve_floors": {"coal": 0.10, "gas": 0.15}
    },
    "high_renewable": {
      "max_swb_share": 0.85,
      "reserve_floors": {"coal": 0.05, "gas": 0.10}
    },
    "100pct_renewable": {
      "max_swb_share": 0.95,
      "reserve_floors": {"coal": 0.00, "gas": 0.05}
    }
  }
}
```

**Step 2: Make solar/wind split dynamic**
```python
def get_swb_technology_mix(self, year, region):
    """
    Determine solar/wind split based on year and region

    Regional preferences:
    - USA: More solar (60/40)
    - Europe: More offshore wind (40/60, with 20% offshore)
    - China: Balanced (55/45)

    Technology costs also influence mix over time
    """
    mix_config = self.config.get('swb_technology_mix', {})
    regional_mix = mix_config.get(region, {'solar': 0.60, 'wind': 0.40})

    # Could add cost-optimization here:
    # If solar much cheaper, shift to solar
    # If wind much cheaper, shift to wind

    return regional_mix
```

**Time Estimate:** 4 hours
**Priority:** P2 - Enhancement

---

### 3.2 Add Integration Costs and Regional Multipliers

**Integration costs increase with renewable penetration**

```python
def calculate_integration_cost(self, swb_share):
    """
    Calculate grid integration cost for renewables
    Increases non-linearly with penetration

    <20%: $2/MWh
    20-40%: $2-5/MWh
    40-60%: $5-10/MWh
    >60%: $10-20/MWh
    """
    if swb_share < 0.20:
        return 2.0
    elif swb_share < 0.40:
        return 2.0 + (swb_share - 0.20) * 15  # Linear 2→5
    elif swb_share < 0.60:
        return 5.0 + (swb_share - 0.40) * 25  # Linear 5→10
    else:
        return 10.0 + (swb_share - 0.60) * 25  # Linear 10→20
```

**Regional multipliers:**
```json
{
  "regional_cost_multipliers": {
    "USA": {
      "solar": 1.0,
      "onshore_wind": 1.1,
      "offshore_wind": 1.2,
      "coal": 1.0,
      "gas": 0.7
    },
    "China": {
      "solar": 0.8,
      "onshore_wind": 0.9,
      "coal": 0.9,
      "gas": 1.1
    },
    "Europe": {
      "solar": 1.1,
      "onshore_wind": 1.0,
      "offshore_wind": 1.3,
      "gas": 1.5
    }
  }
}
```

**Time Estimate:** 6 hours
**Priority:** P2 - Enhancement

---

### 3.3 Add Data Validation Framework

**Comprehensive validation at load time:**

```python
class DataValidator:
    """Validates loaded data against expected ranges and relationships"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []

    def validate_lcoe_data(self, lcoe_data):
        """Validate LCOE data quality"""
        ranges = {
            'solar': (10, 200),
            'onshore_wind': (20, 150),
            'offshore_wind': (40, 250),
            'coal': (40, 150),
            'gas': (30, 200)
        }

        for tech, (min_val, max_val) in ranges.items():
            if tech in lcoe_data:
                for region, series in lcoe_data[tech].items():
                    if len(series) == 0:
                        self.warnings.append(f"Empty {tech} LCOE data for {region}")
                        continue

                    if series.min() < min_val or series.max() > max_val:
                        self.warnings.append(
                            f"{tech} LCOE for {region} outside expected range "
                            f"[{min_val}, {max_val}]: [{series.min()}, {series.max()}]"
                        )

    def validate_generation_mix(self, generation_data, year=2020):
        """Validate generation mix matches reality"""
        # ... implementation from Phase 1.4 ...

    def validate_energy_balance(self, results):
        """Validate generation sums to demand"""
        total_gen = (
            results['solar_generation_twh'] +
            results['wind_generation_twh'] +
            results['coal_generation_twh'] +
            results['gas_generation_twh'] +
            results['nuclear_generation_twh'] +
            results['hydro_generation_twh'] +
            results['other_generation_twh']
        )

        demand = results['total_generation_twh']

        diff_pct = abs(total_gen - demand) / demand * 100

        if (diff_pct > 2).any():
            max_diff = diff_pct.max()
            self.errors.append(f"Energy balance violation: max {max_diff:.1f}% difference")

    def print_summary(self):
        """Print validation summary"""
        print(f"\n{'='*60}")
        print("Data Validation Summary")
        print(f"{'='*60}")
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")

        if self.warnings:
            print("\nWarnings:")
            for w in self.warnings:
                print(f"  ⚠️  {w}")

        if self.errors:
            print("\nErrors:")
            for e in self.errors:
                print(f"  ❌ {e}")
```

**Time Estimate:** 8 hours
**Priority:** P2 - Quality

---

### 3.4 Update Documentation and Create Test Cases

**Update SKILL.md with:**
- Corrected formulas
- Known limitations
- Data requirements
- Validation criteria

**Create test suite:**
```python
# tests/test_swb_forecast.py
import pytest
from forecast import SWBTransitionForecast

def test_emissions_calculation():
    """Test emissions calculation is correct magnitude"""
    # Known: Global 2020 ≈ 13,000 Mt CO₂
    forecast = SWBTransitionForecast(...)
    forecast.load_data()
    forecast.forecast_transition()

    emissions_2020 = forecast.results[forecast.results['year'] == 2020]['total_co2_emissions_mt'].values[0]

    assert 10000 < emissions_2020 < 16000, f"Global 2020 emissions {emissions_2020} outside expected range"

def test_energy_balance():
    """Test generation equals demand"""
    forecast = SWBTransitionForecast(...)
    forecast.load_data()
    forecast.forecast_transition()

    total_gen = (
        forecast.results['solar_generation_twh'] +
        forecast.results['wind_generation_twh'] +
        # ... all technologies ...
    )

    demand = forecast.results['total_generation_twh']

    diff_pct = abs(total_gen - demand) / demand * 100

    assert (diff_pct < 2).all(), "Energy balance violation"

def test_capacity_generation_relationship():
    """Test Gen = Cap × CF × 8760"""
    # ... implementation ...
```

**Time Estimate:** 10 hours
**Priority:** P2 - Quality

---

## Summary Timeline

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| Phase 1 | Week 1-2 | Critical Fixes | Working emissions, real LCOE, baseline techs, valid data |
| Phase 2 | Week 3-4 | Core Features | Capacity forecast, battery sizing, carbon pricing, CF evolution |
| Phase 3 | Week 5-6 | Enhancements | Remove limits, add costs, validation, tests, docs |

**Total Effort:** ~120-150 hours (6 weeks)

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Global 2020 emissions ≈ 13,000 Mt CO₂ (±10%)
- ✅ Coal/gas LCOE show regional variation, not $100/MWh
- ✅ China 2020 mix: ~65% coal, ~5% gas
- ✅ Nuclear + hydro account for ~26% of global generation

### Phase 2 Complete When:
- ✅ All capacity columns populated in output
- ✅ Battery storage scales with penetration (0.5 → 4 days)
- ✅ Tipping points shift with carbon price
- ✅ CF shows improvement (solar 20% → 25%)
- ✅ Gen ≈ Cap × CF × 8760 (±5%)

### Phase 3 Complete When:
- ✅ Can model 85%+ renewable scenarios
- ✅ Integration costs increase with penetration
- ✅ Regional cost differences evident
- ✅ All test queries pass
- ✅ Data validation runs without errors
- ✅ Documentation complete

---

## Risk Mitigation

### Risk: Data quality issues prevent fixes
**Mitigation:** Create data inspection tools early (Phase 1.4), document data issues, create synthetic test data if needed

### Risk: Complexity increases debugging time
**Mitigation:** Implement unit tests alongside features, validate after each change

### Risk: Scope creep
**Mitigation:** Strict prioritization, defer P3 items if timeline pressured

---

## Next Steps After Plan Approval

1. Create feature branch: `git checkout -b fix/swb-transition-issues`
2. Start with Phase 1.1 (emissions fix) - quick win
3. Move to Phase 1.2 (LCOE data) - highest impact
4. Continue sequentially through phases
5. Commit after each completed task
6. Re-run test queries after each phase
7. Create pull request after Phase 2 complete (core functionality)

---

**Plan Status:** READY FOR IMPLEMENTATION
**Estimated Start:** Upon approval
**Estimated Completion:** 6 weeks from start
