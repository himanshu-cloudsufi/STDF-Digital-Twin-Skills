# Parameters Reference - Energy Forecasting (SWB)

## Command-Line Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--region` | Required | - | China, USA, Europe, Rest_of_World, Global |
| `--end-year` | Integer | 2040 | Final forecast year (2025-2100) |
| `--battery-duration` | Integer | 4 | Battery duration: 2, 4, or 8 hours |
| `--output` | String | csv | Output format: csv, json, or both |

## Configuration Parameters (config.json)

### Default Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `end_year` | 2040 | Default forecast horizon |
| `smoothing_window` | 3 | Rolling median window for cost curves |
| `battery_duration_hours` | 4 | Battery storage duration |
| `battery_cycle_life` | 5000 | Battery lifetime cycles |
| `battery_cycles_per_year` | 250 | Annual battery cycles |
| `battery_rte` | 0.88 | Round-trip efficiency (88%) |
| `battery_fixed_om` | 5.0 | Fixed O&M ($/MWh) |
| `coal_reserve_floor` | 0.10 | Minimum coal capacity (10%) |
| `gas_reserve_floor` | 0.15 | Minimum gas capacity (15%) |
| `capacity_factor_improvement` | 0.003 | Annual CF improvement (0.3%) |
| `energy_balance_tolerance` | 0.02 | Energy balance tolerance (2%) |
| `csp_threshold` | 0.01 | CSP inclusion threshold (1% of solar) |
| `max_yoy_growth` | 0.50 | Maximum year-over-year growth (50%) |
| `min_capacity_factor` | 0.05 | Minimum CF (5%) |
| `max_capacity_factor` | 0.70 | Maximum CF for renewables (70%) |

### Displacement Sequences

| Region | Sequence | Description |
|--------|----------|-------------|
| China | coal_first | Displace coal before gas |
| USA | gas_first | Displace gas before coal |
| Europe | coal_first | Displace coal before gas |
| Rest_of_World | coal_first | Default: coal first |

### Default Capacity Factors

| Technology | CF | Description |
|------------|----|-----------  |
| Solar_PV | 0.15 | 15% capacity factor |
| CSP | 0.25 | 25% (thermal storage advantage) |
| Onshore_Wind | 0.30 | 30% capacity factor |
| Offshore_Wind | 0.40 | 40% (better wind resources) |
| Coal_Power | 0.55 | 55% (baseload) |
| Natural_Gas_Power | 0.50 | 50% (flexible dispatch) |
| Nuclear | 0.85 | 85% (baseload) |
| Hydro | 0.45 | 45% (seasonal variation) |

## Battery Duration Options

| Duration | Dataset Suffix | Typical Use Case |
|----------|---------------|------------------|
| 2 hours | 2_Hour | Short-duration, frequency regulation |
| 4 hours | 4_Hour | **Standard** - daily peak shifting |
| 8 hours | 8_Hour | Long-duration, multi-hour storage |

## Validation Thresholds

| Check | Threshold | Description |
|-------|-----------|-------------|
| Energy Balance | 2% | Max deviation from SWB+Coal+Gas+Other = Total |
| Capacity Factor Bounds | 5%-70% | Valid CF range for renewables |
| Non-Negativity | 0 | All generation/capacity must be ≥ 0 |
| Max YoY Growth | 50% | Cap on year-over-year capacity growth |

## Regions

| Code | Full Name | Notes |
|------|-----------|-------|
| China | China | Largest energy market, coal-first |
| USA | United States | Gas-heavy grid, gas-first |
| Europe | Europe | Aggregated EU + UK, coal-first |
| Rest_of_World | Rest of World | All other countries, coal-first |
| Global | Global | Aggregated from 4 regions above |

## Example Usages

**Standard forecast (4-hour battery, 2040):**
```bash
./run_forecast.sh --region China --output csv
```

**Long-duration battery, 2040:**
```bash
./run_forecast.sh --region USA --end-year 2040 --battery-duration 8 --output both
```

**Global aggregation:**
```bash
./run_forecast.sh --region Global --end-year 2040 --output json
```

## Modifying Parameters

Edit `config.json` to change:
- Battery parameters (cycles, RTE, OM)
- Reserve floors
- CF defaults
- Displacement sequences
- Validation tolerances

**Note**: Command-line parameters override config.json defaults.
