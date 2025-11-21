# Data Schema Reference

Complete documentation of input data requirements, taxonomy mappings, dataset structures, and data handling protocols for the Datacenter UPS Battery Technology Transition model.

## Contents

- [Overview](#overview)
- [Taxonomy Structure](#taxonomy-structure)
- [Dataset Catalog](#dataset-catalog)
- [Data File Formats](#data-file-formats)
- [Dataset Mapping Rules](#dataset-mapping-rules)
- [Missing Data Handling](#missing-data-handling)
- [Data Validation Rules](#data-validation-rules)
- [Regional Data Requirements](#regional-data-requirements)
- [Example Data Files](#example-data-files)

---

## Overview

The model uses a hierarchical taxonomy to organize datasets:

```
Market (Datacenter_UPS)
├── Product (Batteries)
    ├── Subproduct (VRLA)
    └── Subproduct (Li_ion)
```

Data files are stored in JSON format in the `data/` directory, with standardized naming conventions and structure.

---

## Taxonomy Structure

### Market Level
```json
{
  "market": "Datacenter_UPS",
  "description": "Uninterruptible Power Supply batteries for datacenters",
  "metrics": ["demand", "installed_base", "growth_rate"],
  "units": {
    "demand": "GWh/year",
    "installed_base": "GWh",
    "growth_rate": "percent/year"
  }
}
```

### Product Level
```json
{
  "products": {
    "Batteries": {
      "subproducts": ["VRLA", "Li_ion"],
      "attributes": {
        "VRLA": {
          "type": "incumbent",
          "aliases": ["LAB", "Lead_Acid", "Lead-acid"],
          "lifespan": 5,
          "technology": "Valve-Regulated Lead-Acid"
        },
        "Li_ion": {
          "type": "disruptor",
          "aliases": ["Lithium", "Li-Ion", "Lithium_Ion"],
          "lifespan": 12,
          "technology": "Lithium-ion (LFP/NMC)"
        }
      }
    }
  }
}
```

---

## Dataset Catalog

### Demand Datasets

#### Total Market Demand
- **Dataset Pattern**: `Data_Center_Battery_Demand_Annual_Capacity_Demand_<region>`
- **Entity**: Datacenter_UPS (market level)
- **Type**: historical_or_input
- **Units**: GWh/year
- **Time Range**: 2015-2024 (historical), 2025+ (projected if available)
- **Regions**: China, USA, Europe, Rest_of_World, Global
- **Usage**: Validation target for VRLA + Li-ion sum

#### VRLA Demand
- **Dataset Pattern**: `Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_<region>`
- **Entity**: VRLA (product level)
- **Type**: historical_or_input
- **Units**: GWh/year
- **Notes**: "LAB" = Lead-Acid Battery in dataset names
- **Required**: Yes (core input)

#### Li-ion Demand
- **Dataset Pattern**: `Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_<region>`
- **Entity**: Li_ion (product level)
- **Type**: historical_or_input
- **Units**: GWh/year
- **Required**: Yes (core input)

### Cost Datasets

#### VRLA Costs
- **Dataset**: `VRLA_Battery_Cost_Global`
- **Entity**: VRLA
- **Type**: assumption_or_input
- **Units**: $/kWh
- **Structure**: Single value or flat time series
- **Default**: $220/kWh (2024 dollars)
- **Regional Adjustment**: Apply multipliers (China 0.9×, Europe 1.15×)

#### Li-ion Costs (via BESS Proxy)
- **Dataset Pattern**: `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>`
- **Entity**: Li_ion (proxy)
- **Type**: historical_or_input
- **Units**: $/kWh (turnkey, including installation)
- **Time Range**: 2015-2024 (historical)
- **Notes**:
  - Grid-scale BESS used as proxy for UPS batteries
  - Apply 8% reliability premium for UPS applications
  - 4-hour duration matches UPS typical configuration

#### Alternative Duration Costs
- **Dataset Pattern**: `Battery_Energy_Storage_System_(2-hour_Turnkey)_Cost_<region>`
- **Usage**: Sensitivity analysis for different duration requirements
- **Conversion**: Cost_4h ≈ Cost_2h × 0.65 (duration scaling)

#### Power-Basis Costs
- **Dataset**: `Battery_Energy_Storage_System_Installed_Cost_Global`
- **Units**: $/kW (power basis)
- **Conversion**: Cost_per_kWh = Cost_per_kW / Duration_hours

### Installed Base Datasets

#### VRLA Installed Base
- **Dataset Pattern**: `Lead_acid_batteries_UPS_Datacenter_Installed_Base_<region>`
- **Entity**: VRLA
- **Type**: historical_or_estimated
- **Units**: GWh (cumulative stock)
- **Time Range**: Snapshot at specific years (e.g., 2020, 2023)
- **Required**: Preferred but can be estimated

#### Li-ion Installed Base
- **Dataset**: Not directly available
- **Initialization**:
  - Conservative: Start at 0 in base year
  - Derived: Sum of last 12 years of Li-ion demand
  - Back-cast: If >12 years history available

### Growth Driver Datasets

#### Datacenter Growth Projections
- **Dataset Pattern**: `Datacenter_capacity_growth_projections_<region>`
- **Entity**: Datacenter_UPS (market driver)
- **Type**: assumption_or_input
- **Units**: Decimal (0.077 = 7.7% growth)
- **Time Range**: 2025-2035 (projections)
- **Usage**: Drive total market demand growth
- **Typical Values**:
  - China: 0.10-0.12 (10-12%)
  - USA: 0.07-0.09 (7-9%)
  - Europe: 0.06-0.08 (6-8%)
  - RoW: 0.08-0.10 (8-10%)

### Lifetime/Replacement Datasets

#### VRLA Replacement Cycle
- **Dataset**: `Lead_acid_batteries_UPS_Datacenter_Replacement_cycle_Battery_Replacement_cycle_Global`
- **Entity**: VRLA
- **Type**: assumption_or_input
- **Units**: years
- **Default**: 5 years
- **Usage**: Calculate retirement rate (20%/year)

#### Li-ion Replacement Cycle
- **Dataset**: `Li_ion_UPS_Replacement_cycle_Global`
- **Entity**: Li_ion
- **Type**: assumption_or_input
- **Units**: years
- **Default**: 12 years
- **Usage**: Calculate retirement rate (8.3%/year)

### Material Intensity Datasets

#### Lithium Content
- **Dataset**: `Data_Center_UPS_Battery_(Li-Ion)_Average_Lithium_content_Global`
- **Entity**: Li_ion
- **Type**: assumption_or_input
- **Units**: kg Li per kWh
- **Typical Value**: 0.12-0.15 kg/kWh (LFP lower, NMC higher)
- **Usage**: Optional - for material flow analysis

---

## Data File Formats

### JSON Structure for Time Series

```json
{
  "dataset_name": "Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_China",
  "metadata": {
    "units": "GWh/year",
    "source": "Industry reports, vendor data",
    "last_updated": "2024-10-15",
    "confidence": "high",
    "region": "China",
    "entity": "VRLA",
    "type": "historical"
  },
  "data": {
    "2015": 12.34,
    "2016": 14.56,
    "2017": 17.89,
    "2018": 21.23,
    "2019": 25.67,
    "2020": 28.91,
    "2021": 31.45,
    "2022": 33.78,
    "2023": 35.23,
    "2024": 36.45
  }
}
```

### Aggregated Data File (Datacenter_UPS.json)

```json
{
  "file_type": "aggregated_datasets",
  "market": "Datacenter_UPS",
  "regions": ["China", "USA", "Europe", "Rest_of_World", "Global"],
  "datasets": {
    "Data_Center_Battery_Demand_Annual_Capacity_Demand_China": {
      "2020": 28.91,
      "2021": 31.45,
      "2022": 33.78,
      "2023": 35.23,
      "2024": 36.45
    },
    "Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_China": {
      "2020": 26.02,
      "2021": 27.25,
      "2022": 27.89,
      "2023": 27.45,
      "2024": 26.12
    },
    "Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_China": {
      "2020": 2.89,
      "2021": 4.20,
      "2022": 5.89,
      "2023": 7.78,
      "2024": 10.33
    }
  }
}
```

### Cost Data Structure (Energy_Storage.json)

```json
{
  "file_type": "cost_datasets",
  "category": "energy_storage",
  "datasets": {
    "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_China": {
      "2018": 420.50,
      "2019": 380.25,
      "2020": 340.80,
      "2021": 295.60,
      "2022": 255.40,
      "2023": 220.30,
      "2024": 195.75
    },
    "VRLA_Battery_Cost_Global": {
      "constant_value": 220.0,
      "notes": "Mature technology, minimal cost reduction"
    }
  }
}
```

---

## Dataset Mapping Rules

### Variable to Dataset Mapping

| Model Variable | Primary Dataset | Fallback Strategy |
|---------------|-----------------|-------------------|
| `vrla_demand` | `Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_<region>` | Initialize from total × 0.9 (if pre-2020) |
| `lithium_demand` | `Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_<region>` | Initialize from total × 0.1 (if pre-2020) |
| `total_demand` | `Data_Center_Battery_Demand_Annual_Capacity_Demand_<region>` | Sum of VRLA + Li-ion |
| `vrla_installed_base` | `Lead_acid_batteries_UPS_Datacenter_Installed_Base_<region>` | Estimate: demand × lifespan |
| `lithium_installed_base` | Not available | Initialize at 0 or back-cast |
| `vrla_cost` | `VRLA_Battery_Cost_Global` | Use $220/kWh constant |
| `lithium_cost` | `Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_<region>` | Use Global if regional missing |
| `growth_rate` | `Datacenter_capacity_growth_projections_<region>` | Use 8% default |
| `vrla_lifespan` | `Lead_acid_batteries_UPS_Datacenter_Replacement_cycle_Battery_Replacement_cycle_Global` | Use 5 years default |
| `lithium_lifespan` | `Li_ion_UPS_Replacement_cycle_Global` | Use 12 years default |

### Regional Data Mapping

```python
# Priority order for regional data
def get_regional_data(dataset_pattern, region):
    # 1. Try exact region match
    dataset_name = dataset_pattern.replace("<region>", region)
    if dataset_exists(dataset_name):
        return load_dataset(dataset_name)

    # 2. Try Global with regional adjustment
    global_name = dataset_pattern.replace("<region>", "Global")
    if dataset_exists(global_name):
        data = load_dataset(global_name)
        return apply_regional_multiplier(data, region)

    # 3. Use default values
    return get_default_values(dataset_pattern)
```

### Alias Resolution

```python
ENTITY_ALIASES = {
    "VRLA": ["LAB", "Lead_Acid", "Lead-acid", "Lead_acid_batteries"],
    "Li_ion": ["Li-Ion", "Lithium_Ion", "Lithium", "Li_ion_batteries"],
    "Datacenter_UPS": ["Data_Center", "UPS", "Datacenter"]
}

def resolve_entity(dataset_name):
    for canonical, aliases in ENTITY_ALIASES.items():
        if any(alias in dataset_name for alias in aliases):
            return canonical
    return None
```

---

## Missing Data Handling

### Initialization Rules

#### Missing Li-ion Installed Base
```python
if lithium_installed_base_data is None:
    if len(lithium_demand_history) >= 12:
        # Sum last 12 years of demand (assumes 12-year lifespan)
        lithium_ib_start = sum(lithium_demand_history[-12:])
    else:
        # Conservative: start at zero
        lithium_ib_start = 0.0
```

#### Missing VRLA Installed Base
```python
if vrla_installed_base_data is None:
    # Estimate from demand and lifespan
    if vrla_demand_data:
        vrla_ib_start = vrla_demand_data[start_year] * vrla_lifespan
    else:
        # Use total market estimate
        vrla_ib_start = total_market_demand * 0.9 * vrla_lifespan
```

#### Missing Growth Rates
```python
if growth_rate_data is None:
    # Regional defaults
    DEFAULT_GROWTH_RATES = {
        "China": 0.10,
        "USA": 0.08,
        "Europe": 0.07,
        "Rest_of_World": 0.09,
        "Global": 0.085
    }
    growth_rate = DEFAULT_GROWTH_RATES.get(region, 0.08)
```

### Interpolation Rules

#### Linear Interpolation for Gaps
```python
def interpolate_gaps(data, max_gap=2):
    """Fill gaps up to max_gap years with linear interpolation"""
    years = sorted(data.keys())
    filled = data.copy()

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        gap = y2 - y1

        if 1 < gap <= max_gap + 1:
            v1, v2 = data[y1], data[y2]
            for y in range(y1 + 1, y2):
                t = (y - y1) / gap
                filled[y] = v1 * (1 - t) + v2 * t

    return filled
```

#### Forward Fill for Missing Recent Data
```python
def forward_fill_recent(data, target_year):
    """Use last known value for recent missing years"""
    last_year = max(data.keys())
    last_value = data[last_year]

    if target_year - last_year <= 2:  # Max 2 years forward fill
        for year in range(last_year + 1, target_year + 1):
            data[year] = last_value

    return data
```

### Regional Proxy Rules

```python
REGIONAL_PROXIES = {
    "Rest_of_World": {
        "proxy": "USA",
        "cost_multiplier": 1.10,  # 10% higher costs
        "demand_multiplier": 0.40  # 40% of USA demand
    },
    "Europe": {
        "proxy": "USA",
        "cost_multiplier": 1.15,  # 15% higher costs
        "demand_multiplier": 0.85  # 85% of USA demand
    }
}

def apply_proxy_data(region, data_type):
    if region in REGIONAL_PROXIES:
        proxy_config = REGIONAL_PROXIES[region]
        proxy_data = load_data(proxy_config["proxy"], data_type)

        if data_type == "cost":
            return proxy_data * proxy_config["cost_multiplier"]
        elif data_type == "demand":
            return proxy_data * proxy_config["demand_multiplier"]

    return None
```

---

## Data Validation Rules

### Consistency Checks

```python
def validate_demand_consistency(vrla, lithium, total, tolerance=0.05):
    """VRLA + Li-ion should approximately equal Total"""
    calculated_total = vrla + lithium
    error = abs(calculated_total - total) / total

    assert error <= tolerance, f"Demand inconsistency: {error:.1%} exceeds {tolerance:.1%}"
    return True
```

### Range Validation

```python
VALID_RANGES = {
    "demand_gwh": (0, 1000),  # 0-1000 GWh/year reasonable for single region
    "growth_rate": (-0.1, 0.3),  # -10% to +30% growth
    "cost_per_kwh": (50, 1000),  # $50-1000/kWh reasonable range
    "lifespan_years": (3, 20),  # 3-20 years battery life
    "market_share": (0, 1)  # 0-100% share
}

def validate_ranges(data, data_type):
    min_val, max_val = VALID_RANGES[data_type]
    for year, value in data.items():
        assert min_val <= value <= max_val, \
            f"Value {value} for {year} outside valid range [{min_val}, {max_val}]"
```

### Temporal Validation

```python
def validate_time_series(data):
    """Check for temporal consistency"""
    years = sorted(data.keys())

    # No duplicate years
    assert len(years) == len(set(years)), "Duplicate years found"

    # Reasonable year range
    assert min(years) >= 2000, "Data before year 2000 unlikely"
    assert max(years) <= 2050, "Data beyond 2050 too speculative"

    # Check for large jumps (>50% YoY change)
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        if y2 - y1 == 1:  # Adjacent years
            change = abs(data[y2] - data[y1]) / data[y1]
            if change > 0.5:
                print(f"Warning: Large jump ({change:.1%}) between {y1} and {y2}")
```

### Cross-Dataset Validation

```python
def validate_cross_dataset(datasets):
    """Validate relationships between datasets"""

    # Li-ion share should be increasing over time
    li_share = datasets["li_demand"] / (datasets["vrla_demand"] + datasets["li_demand"])
    assert all(li_share[i] <= li_share[i+1] for i in range(len(li_share)-1)), \
        "Li-ion share not monotonically increasing"

    # Installed base should be > annual demand (except early years)
    for year in range(2020, 2025):
        if year in datasets["vrla_installed_base"]:
            assert datasets["vrla_installed_base"][year] > datasets["vrla_demand"][year], \
                f"Installed base less than annual demand in {year}"

    # Cost trajectories (Li-ion declining, VRLA flat/slight decline)
    li_costs = datasets["lithium_costs"]
    years = sorted(li_costs.keys())
    for i in range(len(years) - 1):
        assert li_costs[years[i+1]] <= li_costs[years[i]] * 1.05, \
            "Li-ion costs increasing too rapidly"
```

---

## Regional Data Requirements

### Minimum Required Datasets by Region

| Region | Required Datasets | Optional but Recommended |
|--------|------------------|--------------------------|
| **China** | • VRLA demand<br>• Li-ion demand<br>• Growth projections<br>• BESS 4h costs | • VRLA installed base<br>• Total market demand |
| **USA** | • VRLA demand<br>• Li-ion demand<br>• Growth projections<br>• BESS 4h costs | • VRLA installed base<br>• Total market demand |
| **Europe** | • VRLA demand<br>• Li-ion demand<br>• Growth projections | • BESS 4h costs (can use USA×1.15)<br>• VRLA installed base |
| **Rest_of_World** | • Growth projections | • All others (use proxies) |
| **Global** | • Should not be run with individual regions | • Aggregate from regions |

### Regional Data Quality Matrix

| Dataset Type | China | USA | Europe | RoW | Global |
|-------------|-------|-----|--------|-----|--------|
| Demand Data | ✓✓✓ High | ✓✓✓ High | ✓✓ Good | ✓ Limited | ✓✓ Aggregate |
| Cost Data | ✓✓✓ High | ✓✓✓ High | ✓✓ Good | ✗ Use proxy | ✓✓ Average |
| Installed Base | ✓✓ Good | ✓✓ Good | ✓ Limited | ✗ Estimate | ✓ Estimate |
| Growth Rates | ✓✓✓ High | ✓✓ Good | ✓✓ Good | ✓ Estimate | ✓✓ Average |

Legend: ✓✓✓ High quality, ✓✓ Good, ✓ Limited, ✗ Missing/Use proxy

---

## Example Data Files

### Example: Datacenter_UPS.json (excerpt)

```json
{
  "file_version": "1.0",
  "last_updated": "2024-10-15",
  "market": "Datacenter_UPS",
  "data_quality": {
    "China": "high",
    "USA": "high",
    "Europe": "good",
    "Rest_of_World": "estimated",
    "Global": "aggregated"
  },
  "datasets": {
    "Data_Center_Battery_Demand_(LAB)_Annual_Capacity_Demand_China": {
      "2018": 24.5,
      "2019": 25.8,
      "2020": 26.0,
      "2021": 27.3,
      "2022": 27.9,
      "2023": 27.5,
      "2024": 26.1
    },
    "Data_Center_Battery_Demand_(Li-Ion)_Annual_Capacity_Demand_China": {
      "2018": 1.2,
      "2019": 1.8,
      "2020": 2.9,
      "2021": 4.2,
      "2022": 5.9,
      "2023": 7.8,
      "2024": 10.3
    },
    "Datacenter_capacity_growth_projections_China": {
      "2025": 0.105,
      "2026": 0.098,
      "2027": 0.092,
      "2028": 0.088,
      "2029": 0.085,
      "2030": 0.082
    }
  }
}
```

### Example: Energy_Storage.json (excerpt)

```json
{
  "file_version": "1.0",
  "category": "energy_storage_costs",
  "currency": "USD_2024",
  "datasets": {
    "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_China": {
      "metadata": {
        "units": "$/kWh",
        "duration": "4 hours",
        "includes": ["battery", "PCS", "installation", "commissioning"],
        "source": "BNEF, industry surveys"
      },
      "data": {
        "2018": 420.5,
        "2019": 380.3,
        "2020": 340.8,
        "2021": 295.6,
        "2022": 255.4,
        "2023": 220.3,
        "2024": 195.8
      }
    },
    "Battery_Energy_Storage_System_(4-hour_Turnkey)_Cost_USA": {
      "data": {
        "2018": 485.2,
        "2019": 445.6,
        "2020": 405.3,
        "2021": 365.8,
        "2022": 325.4,
        "2023": 285.6,
        "2024": 250.3
      }
    }
  }
}
```

---

## Data Loading Implementation

### DataLoader Class Structure

```python
class DatacenterUPSDataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.taxonomy = self._load_taxonomy()
        self.datacenter_data = None
        self.energy_storage_data = None

    def _load_taxonomy(self):
        """Load taxonomy mapping file"""
        with open(self.data_dir / "datacenter_ups_taxonomy_and_datasets.json") as f:
            return json.load(f)

    def load_all_data(self):
        """Load all required datasets"""
        # Load main data files
        self.datacenter_data = self._load_json("Datacenter_UPS.json")
        self.energy_storage_data = self._load_json("Energy_Storage.json")

        # Parse into structured format
        return {
            "vrla_demand": self._extract_demand("LAB"),
            "lithium_demand": self._extract_demand("Li-Ion"),
            "total_demand": self._extract_demand("total"),
            "vrla_installed_base": self._extract_installed_base("VRLA"),
            "bess_costs_4h": self._extract_costs("4-hour"),
            "growth_rates": self._extract_growth_rates()
        }

    def _extract_demand(self, technology):
        """Extract demand data by technology and region"""
        result = {}
        for dataset_name, data in self.datacenter_data["datasets"].items():
            if technology in dataset_name and "Demand" in dataset_name:
                region = self._extract_region(dataset_name)
                if region:
                    result[region] = pd.Series(data)
        return result
```

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Maintainer**: Datacenter UPS Battery Forecasting Team