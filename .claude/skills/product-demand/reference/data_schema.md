# Data Schema Documentation

## Overview

This document describes the JSON data structures used throughout the product demand forecasting system.

---

## 1. Entity Data Files

### Location
`.claude/skills/product-demand/data/[Entity_Name].json`

### Structure

```json
{
  "Entity Name": {
    "Metric_Name_1": {
      "metadata": {
        "type": "cost|demand|installed_base|capacity|generation",
        "units": "USD|vehicles|GWh|MW|barrels/day",
        "description": "Human-readable description",
        "source": "Data source attribution",
        "entity_type": "disruptor|incumbent|chimera|market",
        "last_updated": "YYYY-MM-DD"
      },
      "regions": {
        "China": {
          "X": [2010, 2011, 2012, ...],
          "Y": [value1, value2, value3, ...]
        },
        "USA": {
          "X": [2010, 2011, 2012, ...],
          "Y": [value1, value2, value3, ...]
        },
        "Europe": { ... },
        "Rest_of_World": { ... },
        "Global": { ... }
      }
    },
    "Metric_Name_2": { ... }
  }
}
```

### Field Descriptions

**Entity Name**: Top-level key matching entity file name (e.g., "Passenger Cars")

**Metric_Name**: Unique identifier for each dataset within entity
- Format: `Product_(Type)_Metric`
- Examples: `Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost`, `Commercial_Vehicle_(EV)_Annual_Sales`

**metadata** (optional): Descriptive information about the metric
- `type`: Category of data (cost, demand, installed_base, etc.)
- `units`: Measurement units
- `description`: What the metric represents
- `source`: Data provenance
- `entity_type`: Product classification
- `last_updated`: Data freshness timestamp

**regions**: Regional data breakdown
- Each region contains `X` (years) and `Y` (values) arrays
- Arrays must be equal length
- Years should be in ascending order
- Values must be non-negative

### Example

```json
{
  "Passenger Cars": {
    "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost": {
      "metadata": {
        "type": "cost",
        "units": "USD",
        "entity_type": "disruptor"
      },
      "regions": {
        "China": {
          "X": [2015, 2016, 2017, 2018, 2019, 2020],
          "Y": [45000, 42000, 38000, 35000, 32000, 29000]
        },
        "USA": {
          "X": [2015, 2016, 2017, 2018, 2019, 2020],
          "Y": [48000, 45000, 41000, 38000, 35000, 32000]
        }
      }
    }
  }
}
```

---

## 2. Taxonomy Files

### Location
`.claude/skills/product-demand/data/[Entity_Name]_taxonomy.json`

### Purpose
Define market structure, product relationships, and dataset mappings.

### Structure

```json
{
  "market": "Market_Product_Name",
  "taxonomy": {
    "Product_A": {
      "subproducts": ["Subproduct_A1", "Subproduct_A2"]
    },
    "Product_B": {
      "subproducts": []
    }
  },
  "data": {
    "Product_A": {
      "cost": {
        "China": "Dataset_Name_For_Product_A_Cost_China",
        "USA": "Dataset_Name_For_Product_A_Cost_USA",
        ...
      },
      "demand": {
        "China": "Dataset_Name_For_Product_A_Demand_China",
        "USA": "Dataset_Name_For_Product_A_Demand_USA",
        ...
      },
      "installed_base": {
        "China": "Dataset_Name_For_Product_A_Fleet_China",
        ...
      },
      "entity_type": "disruptor|incumbent|chimera|market"
    },
    "Product_B": { ... }
  }
}
```

### Field Descriptions

**market**: Name of the market-level product (aggregates all subproducts)

**taxonomy**: Hierarchical product relationships
- Lists which products contain subproducts
- Empty array `[]` means no further decomposition

**data**: Mapping of products to dataset names
- Each product can have multiple data types (cost, demand, installed_base, capacity, etc.)
- Each data type maps regions to specific dataset names from entity file
- Dataset names must match keys in entity JSON file
- `entity_type` classifies product role in market disruption

### Example

```json
{
  "market": "Passenger_Vehicles",
  "taxonomy": {
    "EV_Cars": {
      "subproducts": ["BEV_Cars", "PHEV_Cars"]
    },
    "ICE_Cars": {
      "subproducts": []
    }
  },
  "data": {
    "EV_Cars": {
      "cost": {
        "China": "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost",
        "USA": "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost"
      },
      "demand": {
        "China": "Passenger_Vehicle_(EV)_Annual_Sales",
        "USA": "Passenger_Vehicle_(EV)_Annual_Sales"
      },
      "entity_type": "disruptor"
    },
    "ICE_Cars": {
      "cost": {
        "China": "Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)",
        "USA": "Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)"
      },
      "demand": {
        "China": "Passenger_Vehicle_(ICE)_Annual_Sales",
        "USA": "Passenger_Vehicle_(ICE)_Annual_Sales"
      },
      "entity_type": "incumbent"
    },
    "Passenger_Vehicles": {
      "demand": {
        "China": "Passenger_Vehicle_Annual_Sales",
        "USA": "Passenger_Vehicle_Annual_Sales"
      },
      "entity_type": "market"
    }
  }
}
```

---

## 3. Products Catalog Index

### Location
`.claude/skills/product-demand/data/products_catalog_index.json`

### Purpose
Central registry mapping product names to entity files and types.

### Structure

```json
{
  "products": {
    "Product_Name_1": {
      "entity": "Entity_File_Name",
      "type": "disruptor|incumbent|chimera|market"
    },
    "Product_Name_2": { ... }
  },
  "entities": [
    "Entity_Name_1",
    "Entity_Name_2",
    ...
  ],
  "metadata": {
    "description": "Catalog purpose",
    "types": {
      "disruptor": "Description",
      "incumbent": "Description",
      "chimera": "Description",
      "market": "Description"
    }
  }
}
```

### Example

```json
{
  "products": {
    "EV_Cars": {"entity": "Passenger_Cars", "type": "disruptor"},
    "ICE_Cars": {"entity": "Passenger_Cars", "type": "incumbent"},
    "Solar_PV": {"entity": "Energy_Generation", "type": "disruptor"},
    "Coal_Power": {"entity": "Energy_Generation", "type": "incumbent"}
  },
  "entities": [
    "Passenger_Cars",
    "Energy_Generation",
    "Commercial_Vehicle"
  ]
}
```

---

## 4. Configuration File

### Location
`.claude/skills/product-demand/config.json`

### Structure

```json
{
  "default_parameters": {
    "end_year": 2040,
    "logistic_ceiling": 1.0,
    "market_cagr_cap": 0.05,
    "smoothing_window": 3,
    "chimera_decay_half_life": 3.0,
    "phev_peak_share": 0.15
  },
  "regions": [
    "China",
    "USA",
    "Europe",
    "Rest_of_World",
    "Global"
  ],
  "output_formats": [
    "csv",
    "json",
    "both"
  ]
}
```

### Parameter Descriptions

**end_year**: Default forecast horizon (year)

**logistic_ceiling**: Maximum adoption share for disruptors (0.0-1.0)
- 1.0 = 100% market capture possible
- 0.9 = 90% ceiling (accounts for niche incumbent segments)

**market_cagr_cap**: Maximum annual market growth/decline rate (decimal)
- 0.05 = ±5% per year cap

**smoothing_window**: Rolling median window size (years)
- Used for cost curve smoothing
- Typical range: 3-5 years

**chimera_decay_half_life**: Years for chimera share to halve after tipping (years)
- Controls how fast transitional technologies fade
- Typical range: 2-5 years

**phev_peak_share**: Maximum chimera market share at tipping point (decimal)
- 0.15 = 15% peak share for PHEVs

---

## 5. Forecast Output Format

### JSON Output Structure

```json
{
  "product": "Product_Name",
  "region": "Region_Name",
  "entity": "Entity_Name",
  "product_type": "disruptor|incumbent|chimera|market",
  "market_context": {
    "disrupted": true,
    "tipping_point": 2025,
    "disruptor_products": ["Product_A", "Product_B"],
    "incumbent_products": ["Product_C"],
    "chimera_products": ["Product_D"],
    "market_product": "Market_Total"
  },
  "forecast": {
    "years": [2020, 2021, 2022, ..., 2040],
    "demand": [value1, value2, value3, ..., valueN],
    "shares": [0.10, 0.15, 0.22, ..., 0.85],
    "market": [market1, market2, market3, ..., marketN],
    "method": "logistic|linear|chimera_hump|residual|baseline",
    "tipping_point": 2025,
    "logistic_params": {
      "L": 1.0,
      "k": 0.42,
      "t0": 2026
    }
  },
  "validation": {
    "is_valid": true,
    "warnings": ["Warning message 1", "Warning message 2"],
    "errors": []
  }
}
```

### CSV Output Structure

```
Year,Demand,Market,Share
2020,value1,market1,0.10
2021,value2,market2,0.15
2022,value3,market3,0.22
...
2040,valueN,marketN,0.85
```

---

## 6. Data Quality Requirements

### Minimum Data Requirements

**For Tipping Point Analysis:**
- Cost data for both disruptor and incumbent
- At least 3 historical years per product
- Overlapping time ranges for comparison

**For Logistic Fitting:**
- At least 3 historical demand data points
- Demand data spanning ≥5 years
- Market data for same time period

**For Baseline Forecasting:**
- At least 2 historical demand data points
- Continuous time series (no large gaps)

### Data Quality Checks

```python
# Check 1: Sufficient data points
assert len(years) >= 3, "Insufficient data for fitting"

# Check 2: Chronological order
assert all(years[i] < years[i+1] for i in range(len(years)-1)), "Years not sorted"

# Check 3: Non-negative values
assert all(values >= 0), "Negative values detected"

# Check 4: Matching array lengths
assert len(years) == len(values), "Year-value length mismatch"

# Check 5: No duplicate years
assert len(years) == len(set(years)), "Duplicate years found"
```

---

## 7. Region Codes

Standard region identifiers used throughout the system:

| Code | Description | Coverage |
|------|-------------|----------|
| `China` | People's Republic of China | Mainland China |
| `USA` | United States of America | 50 states + DC |
| `Europe` | European Union + UK + Norway + Switzerland | EU27 + UK + EFTA |
| `Rest_of_World` | All other regions | World - China - USA - Europe |
| `Global` | Worldwide aggregate | Sum of all regions |
| `India` | Republic of India | Used for two/three-wheelers |

---

## 8. Units and Conventions

### Standard Units

| Data Type | Standard Unit | Notes |
|-----------|---------------|-------|
| Vehicle Demand | vehicles/year | Annual sales |
| Vehicle Cost | USD | Real dollars (2023 baseline) |
| Energy Generation | GWh/year or TWh/year | Annual generation |
| Energy Capacity | GW or TW | Installed capacity |
| Battery Capacity | GWh | Annual production |
| Battery Cost | USD/kWh | Pack-level cost |
| Oil Demand | barrels/day or million barrels/day | Daily consumption |
| Commodity Demand | tonnes/year or kilotonnes/year | Annual consumption |

### Naming Conventions

**Product Names:**
- Use underscores: `EV_Cars`, `Solar_PV`
- Avoid spaces in programmatic names
- Use descriptive suffixes: `_Market`, `_Total_Fleet`

**Metric Names:**
- Format: `Product_(Detail)_Metric_Type`
- Examples: `Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost`
- Parentheses for clarifying details

**File Names:**
- Entity files: `Entity_Name.json` (spaces → underscores)
- Taxonomy files: `Entity_Name_taxonomy.json`
- Output files: `Product_Region_Year.csv`

---

## 9. Versioning and Updates

### Schema Version

Current schema version: **1.0**

### Changelog

**v1.0 (2025-11-05)**
- Initial schema definition
- Support for 8 entity types
- Regional breakdown structure
- Taxonomy and catalog indexes

### Backward Compatibility

When updating schema:
1. Increment version number
2. Maintain backward compatibility for 1 version
3. Provide migration scripts
4. Update documentation
5. Test with existing datasets

---

## 10. Validation Scripts

### Entity File Validation

```python
import json

def validate_entity_file(filepath):
    with open(filepath) as f:
        data = json.load(f)

    entity_name = list(data.keys())[0]
    entity_data = data[entity_name]

    for metric_name, metric_data in entity_data.items():
        assert 'regions' in metric_data, f"Missing regions in {metric_name}"

        for region, region_data in metric_data['regions'].items():
            assert 'X' in region_data and 'Y' in region_data, \
                f"Missing X or Y in {metric_name}/{region}"

            assert len(region_data['X']) == len(region_data['Y']), \
                f"Length mismatch in {metric_name}/{region}"

            assert all(isinstance(y, (int, float)) for y in region_data['Y']), \
                f"Non-numeric values in {metric_name}/{region}"

    print(f"✓ {filepath} validated successfully")
```

### Taxonomy File Validation

```python
def validate_taxonomy_file(filepath):
    with open(filepath) as f:
        taxonomy = json.load(f)

    assert 'market' in taxonomy, "Missing market field"
    assert 'taxonomy' in taxonomy, "Missing taxonomy field"
    assert 'data' in taxonomy, "Missing data field"

    for product, product_data in taxonomy['data'].items():
        assert 'entity_type' in product_data, \
            f"Missing entity_type for {product}"

        assert product_data['entity_type'] in \
            ['disruptor', 'incumbent', 'chimera', 'market'], \
            f"Invalid entity_type for {product}"

    print(f"✓ {filepath} validated successfully")
```

---

## Examples

See [examples.md](examples.md) for complete usage examples with sample data.
