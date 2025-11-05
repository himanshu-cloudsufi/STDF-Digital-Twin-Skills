# Forecasting Core Library

Shared Python library for demand forecasting skills in the STDF (Superabundance, Technology, Disruption Framework) system.

## Overview

This library provides reusable utilities for cost-driven demand forecasting across multiple domains:
- Product demand (vehicles, energy generation, batteries)
- Commodity demand (metals, energy commodities)
- Disruption impact analysis

All three forecasting skills (`product-demand`, `commodity-demand`, `disruption-analysis`) import from this shared library to ensure consistency and reduce code duplication.

## Installation

No installation needed. Skills import directly by adding the library to Python's path:

```python
import sys
sys.path.insert(0, '.claude/skills/_forecasting_core')

from core.utils import calculate_cagr, rolling_median
from core.cost_analyzer import CostAnalyzer
from core.logistic_models import fit_logistic_curve
from core.data_loader import DataLoader
from core.validators import validate_forecast_consistency
```

## Dependencies

- Python 3.7+
- NumPy >= 1.20.0
- SciPy >= 1.7.0 (for differential_evolution)

## Modules

### core.utils

Mathematical and data manipulation utilities:

**Smoothing and Interpolation:**
- `rolling_median(data, window)` - Apply rolling median filter
- `clamp(value, min, max)` - Clamp value to bounds
- `clamp_array(arr, min, max)` - Clamp array to bounds

**Growth and Trend Analysis:**
- `calculate_cagr(values, years)` - Compound Annual Growth Rate
- `theil_sen_slope(x, y)` - Robust linear regression
- `linear_extrapolation(years, values, end_year, max_cagr)` - Linear trend forecast with CAGR cap

**Cost Forecasting:**
- `log_cagr_forecast(years, costs, end_year)` - Log-linear cost curve forecast (Wright's Law)

**Intersection Detection:**
- `find_intersection(years, series1, series2)` - Find first crossover year (for tipping points)

**Validation:**
- `validate_forecast_consistency(market, bev, phev, ice)` - Check sum constraints and non-negativity

### core.cost_analyzer

Cost curve analysis and tipping point detection for any disruptor/incumbent pair.

**CostAnalyzer Class:**

```python
analyzer = CostAnalyzer(smoothing_window=3)

# Prepare cost curves (smooth + forecast)
cost_curves = analyzer.prepare_cost_curves(
    disruptor_years, disruptor_costs,
    incumbent_years, incumbent_costs,
    end_year=2040
)

# Find tipping point (cost parity year)
tipping_point = analyzer.find_tipping_point(
    years, disruptor_costs, incumbent_costs
)

# Analyze cost trajectory (CAGRs, advantage)
summary = analyzer.analyze_cost_trajectory(
    years, disruptor_costs, incumbent_costs, tipping_point
)
```

**Methods:**
- `prepare_cost_curves()` - Smooth historical data and forecast to end_year using log-CAGR
- `find_tipping_point()` - Detect year when disruptor cost < incumbent cost
- `analyze_cost_trajectory()` - Calculate CAGRs and cost advantages over time
- `smooth_and_forecast_cost()` - Apply rolling median + log-CAGR forecast

### core.logistic_models

Logistic S-curve fitting and adoption modeling for disruptive technologies.

**Core Functions:**

```python
# Logistic function: s(t) = L / (1 + exp(-k * (t - t0)))
shares = logistic_function(years, L=1.0, k=0.4, t0=2025)

# Fit curve to historical data
L, k, t0 = fit_logistic_curve(historical_years, historical_shares, L=1.0)

# Forecast with fitted curve
forecast_years, forecast_shares, params = forecast_logistic_share(
    historical_years, historical_shares, end_year=2040, L=1.0
)

# Linear pre-tipping, logistic post-tipping
years, shares, info = linear_to_logistic_transition(
    hist_years, hist_shares, tipping_point=2024, end_year=2040
)

# Chimera (bridge technology) hump trajectory
chimera_shares = forecast_chimera_hump(
    years, tipping_point=2024, peak_share=0.15, decay_half_life=3.0
)
```

**Functions:**
- `logistic_function(t, L, k, t0)` - Evaluate S-curve
- `fit_logistic_curve(years, shares, L, initial_guess)` - Fit using differential evolution
- `forecast_logistic_share(...)` - Full forecast workflow
- `linear_to_logistic_transition(...)` - Hybrid linear/logistic model
- `forecast_chimera_hump(...)` - Hump trajectory for transitional technologies (e.g., PHEVs)

### core.data_loader

Generic JSON data loading with taxonomy support for any entity.

**DataLoader Class:**

```python
# Initialize with entity file and optional taxonomy
loader = DataLoader(
    entity_file_path='path/to/Passenger_Cars.json',
    taxonomy_file_path='path/to/Passenger_Cars_taxonomy.json'
)

# Get cost data
years, costs = loader.get_cost_data('EV_Cars', 'China')

# Get demand data
years, demand = loader.get_demand_data('Passenger_Vehicles', 'China')

# Get raw dataset
dataset = loader.get_dataset('EV_Cars_Cost')

# Get data for specific region
years, values = loader.get_data_for_region('BEV_Cars_Demand', 'Europe')

# Query metadata
entity_type = loader.get_entity_type('EV_Cars')  # Returns: "disruptor", "incumbent", "chimera", or "market"
regions = loader.get_all_regions()
datasets = loader.list_all_datasets()
```

**Methods:**
- `get_cost_data(product, region)` - Get cost curve using taxonomy mapping
- `get_demand_data(product, region)` - Get demand curve using taxonomy mapping
- `get_data_for_region(dataset, region, subkey)` - Get X/Y data for specific dataset
- `get_entity_type(product)` - Get classification (disruptor/incumbent/chimera/market)
- `get_all_regions()` - List available regions
- `list_all_datasets()` - List all datasets in entity
- `get_metadata(dataset)` - Get dataset metadata

### core.validators

Forecast validation and consistency checking.

**Validation Functions:**

```python
# Validate sum constraint (components <= market)
is_valid, msg = validate_forecast_consistency(market, [bev, phev, ice], tolerance=0.001)

# Validate non-negative
is_valid, msg = validate_non_negative(array, name="BEV demand")

# Validate monotonicity
is_valid, msg = validate_monotonic_within_tolerance(array, tolerance=0.5, direction="increasing")

# Validate CAGR bounds
is_valid, msg = validate_cagr_bounds(values, years, max_cagr=0.20)

# Validate smooth transitions (no abrupt jumps)
is_valid, msg = validate_smooth_transitions(array, max_jump=0.5)

# Validate shares sum to 1.0
is_valid, msg = validate_shares_sum_to_one([bev_share, phev_share, ice_share], tolerance=0.01)

# Comprehensive validation suite
results = run_comprehensive_validation(market, bev, phev, ice, years)
# Returns: {'all_passed': True/False, 'checks': [...]}
```

**Functions:**
- `validate_forecast_consistency()` - Check sum ≤ market and non-negativity
- `validate_non_negative()` - Check no negative values
- `validate_monotonic_within_tolerance()` - Check approximately monotonic
- `validate_cagr_bounds()` - Check reasonable growth rates
- `validate_smooth_transitions()` - Check no abrupt year-over-year jumps
- `validate_shares_sum_to_one()` - Check shares add to 100%
- `validate_data_availability()` - Check sufficient data points
- `validate_forecast_result()` - Check result dictionary structure
- `run_comprehensive_validation()` - Run full validation suite

## Usage Examples

### Example 1: Basic Cost Analysis

```python
import sys
sys.path.insert(0, '.claude/skills/_forecasting_core')
from core.cost_analyzer import CostAnalyzer

# Load your data (example)
ev_years = [2015, 2016, 2017, 2018, 2019, 2020]
ev_costs = [0.50, 0.45, 0.40, 0.35, 0.30, 0.25]  # USD per mile
ice_years = [2015, 2016, 2017, 2018, 2019, 2020]
ice_costs = [0.35, 0.35, 0.34, 0.34, 0.33, 0.33]

# Analyze
analyzer = CostAnalyzer(smoothing_window=3)
curves = analyzer.prepare_cost_curves(
    ev_years, ev_costs, ice_years, ice_costs, end_year=2040
)
tipping = analyzer.find_tipping_point(
    curves['years'], curves['disruptor_costs'], curves['incumbent_costs']
)

print(f"Tipping point: {tipping}")
```

### Example 2: Logistic Adoption Forecast

```python
from core.logistic_models import forecast_logistic_share

# Historical EV market share
hist_years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]
hist_shares = [0.01, 0.015, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18]

# Forecast to 2040 with 95% ceiling
years, shares, params = forecast_logistic_share(
    hist_years, hist_shares, end_year=2040, L=0.95
)

print(f"Logistic parameters: L={params['L']}, k={params['k']:.2f}, t0={params['t0']:.1f}")
print(f"Forecast for 2040: {shares[-1]:.1%}")
```

### Example 3: Loading Data

```python
from core.data_loader import DataLoader

# Load entity data
loader = DataLoader(
    entity_file_path='.claude/skills/product-demand/data/Passenger_Cars.json',
    taxonomy_file_path='.claude/skills/product-demand/data/Passenger_Cars_taxonomy.json'
)

# Get cost data
ev_years, ev_costs = loader.get_cost_data('EV_Cars', 'China')
ice_years, ice_costs = loader.get_cost_data('ICE_Cars', 'China')

# Get demand data
market_years, market_demand = loader.get_demand_data('Passenger_Vehicles', 'China')

# Check entity type
print(loader.get_entity_type('EV_Cars'))  # Output: "disruptor"
```

### Example 4: Validation

```python
from core.validators import run_comprehensive_validation
import numpy as np

# Your forecast arrays
years = np.arange(2000, 2041)
market = np.array([...])  # Market demand
bev = np.array([...])     # BEV demand
phev = np.array([...])    # PHEV demand
ice = np.array([...])     # ICE demand

# Run validation
results = run_comprehensive_validation(market, bev, phev, ice, years)

if results['all_passed']:
    print("✓ All validation checks passed")
else:
    print("✗ Validation failed:")
    for check in results['checks']:
        if not check['passed']:
            print(f"  - {check['name']}: {check['message']}")
```

## Design Principles

1. **Taxonomy-Driven**: DataLoader uses taxonomy files to map product names to dataset names, enabling flexible entity organization

2. **Generic Abstractions**: All classes work with "disruptor"/"incumbent" instead of specific products (e.g., "EV"/"ICE")

3. **Fail-Safe Defaults**: Functions provide sensible defaults and graceful fallbacks for edge cases (sparse data, missing files)

4. **Validation-First**: Comprehensive validation utilities ensure forecasts meet physical constraints

5. **No External Dependencies**: Core library has no dependencies on specific skills or data files

6. **Stateless Functions**: Most utilities are pure functions for easy testing and reuse

## Version History

- **v1.0** (2025-11-05): Initial release with 5 core modules extracted from demand-forecasting skill

## Contributing

This is a shared library used by multiple skills. Changes should:
- Maintain backward compatibility
- Not introduce skill-specific logic
- Include comprehensive docstrings
- Be tested across all dependent skills

## License

Internal use for Tony Seba STDF forecasting system.
