# Data Schema Reference - Three-Wheeler Demand Forecasting

## Overview

This document describes the input data schema required for three-wheeler demand forecasting.

## Taxonomy File Structure

### File: `data/three_wheeler_taxonomy_and_datasets.json`

This file maps logical dataset names to their metadata and structure.

```json
{
  "taxonomy": {
    "market": "Three_Wheelers",
    "products": {
      "EV_3_Wheelers": {
        "subproducts": []
      },
      "ICE_3_Wheelers": {
        "subproducts": []
      }
    }
  },
  "datasets": {
    "{dataset_name}": {
      "entity": "string",
      "region": "string",
      "level_name": "string",
      "metadata": {
        "type": "historical",
        "tags": {
          "entity_type": "disruptor|incumbent|market",
          "category": "cost|demand|installed_base"
        },
        "description": "string"
      }
    }
  }
}
```

### Dataset Naming Convention

**Pattern:** `{Metric}_{Region}`

**Examples:**
- `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_China`
- `Three_Wheeler_Annual_Sales_Europe`
- `Three_Wheeler_(ICE)_Total_Fleet_Rest_of_World`

## Required Datasets

### Cost Data (Required for Forecasting)

#### EV Primary Cost
- **Pattern**: `EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_{Region}`
- **Entity Type**: disruptor
- **Category**: cost
- **Purpose**: Primary tipping point detection
- **Unit**: USD per vehicle (real terms)

**Required Regions:**
- China
- Europe
- Rest_of_World

#### ICE Cost
- **Pattern**: `Three_Wheeler_(ICE)_Median_Cost_{Region}`
- **Entity Type**: incumbent
- **Category**: cost
- **Purpose**: Tipping point baseline
- **Unit**: USD per vehicle (real terms)

**Required Regions:**
- China
- Europe
- Rest_of_World

#### EV Secondary Cost (Optional - for sensitivity)
- **Pattern**: `Three_Wheeler_(EV)_Median_Cost_{Region}`
- **Entity Type**: disruptor
- **Category**: cost
- **Purpose**: Sensitivity analysis
- **Unit**: USD per vehicle (real terms)

### Demand/Sales Data (Required for Forecasting)

#### Total Market Sales
- **Pattern**: `Three_Wheeler_Annual_Sales_{Region}`
- **Entity Type**: market
- **Category**: demand
- **Purpose**: Market trend forecasting
- **Unit**: Units per year

**Required Regions:**
- China
- Europe
- Rest_of_World
- Global (optional, can be computed)

#### EV Sales
- **Pattern**: `Three_Wheeler_(EV)_Annual_Sales_{Region}`
- **Entity Type**: disruptor
- **Category**: demand
- **Purpose**: Historical EV share calculation
- **Unit**: Units per year

**Required Regions:**
- China
- Europe
- Rest_of_World
- Global (optional)

#### ICE Sales (Optional - for validation)
- **Pattern**: `Three_Wheeler_(ICE)_Annual_Sales_{Region}`
- **Entity Type**: incumbent
- **Category**: demand
- **Purpose**: Cross-validation
- **Unit**: Units per year

### Fleet Data (Optional - for validation)

#### EV Fleet
- **Pattern**: `Three_Wheeler_(EV)_Total_Fleet_{Region}`
- **Entity Type**: disruptor
- **Category**: installed_base
- **Purpose**: Fleet consistency validation
- **Unit**: Units (cumulative stock)

#### ICE Fleet
- **Pattern**: `Three_Wheeler_(ICE)_Total_Fleet_{Region}`
- **Entity Type**: incumbent
- **Category**: installed_base
- **Purpose**: Fleet consistency validation
- **Unit**: Units (cumulative stock)

## Data Curves File Structure

### File: `data/Three_Wheeler.json`

This file contains the actual time-series data.

```json
{
  "{dataset_name}": {
    "regions": {
      "{region}": {
        "X": [int],  // Years
        "Y": [float] // Values
      }
    }
  }
}
```

**Alternative flat structure:**
```json
{
  "{dataset_name}": {
    "X": [int],  // Years
    "Y": [float] // Values
  }
}
```

### Example Data Curve

```json
{
  "EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_China": {
    "regions": {
      "China": {
        "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "Y": [4500, 4200, 3900, 3600, 3200, 2800, 2500, 2200, 2000, 1850]
      }
    }
  },
  "Three_Wheeler_Annual_Sales_China": {
    "regions": {
      "China": {
        "X": [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "Y": [2000000, 2200000, 2400000, 2600000, 2800000, 3000000, 3200000, 3400000, 3600000, 3700000, 3800000, 3900000, 4000000, 4100000, 4200000]
      }
    }
  }
}
```

## Data Quality Requirements

### Minimum Historical Coverage

**For reliable forecasting:**
- **Cost data**: Minimum 5 years (recommended: 8-10 years)
- **Sales data**: Minimum 5 years (recommended: 10-15 years)
- **Fleet data**: Minimum 3 years (optional, for validation)

### Data Consistency

1. **Temporal Alignment**:
   - All datasets should overlap in historical period
   - Recommended overlap: At least 5 years

2. **Regional Consistency**:
   - Cost and demand data must exist for same regions
   - Global = sum of regional (no double counting)
   - USA excluded (minimal three-wheeler market)

3. **Unit Consistency**:
   - Costs in same currency (USD recommended)
   - All costs in real terms (inflation-adjusted to base year)
   - Sales/fleet in consistent units (vehicles, not thousands)

### Data Validation Checks

The data loader performs these checks:

1. **Existence**: Dataset exists in taxonomy and data file
2. **Structure**: X and Y arrays present and equal length
3. **Non-empty**: At least 2 data points
4. **Sorted**: X values (years) are monotonically increasing
5. **Positive**: Cost and demand values > 0

## Creating Custom Data Files

### Step 1: Prepare Taxonomy

1. Copy `three_wheeler_taxonomy_and_datasets.json`
2. Add your dataset entries:

```json
{
  "datasets": {
    "My_Custom_Metric_MyRegion": {
      "entity": "EV_3_Wheelers",
      "region": "MyRegion",
      "level_name": "product",
      "metadata": {
        "type": "historical",
        "tags": {
          "entity_type": "disruptor",
          "category": "cost"
        },
        "description": "Custom EV cost metric"
      }
    }
  }
}
```

### Step 2: Prepare Data Curves

1. Create or modify `Three_Wheeler.json`
2. Add your data:

```json
{
  "My_Custom_Metric_MyRegion": {
    "regions": {
      "MyRegion": {
        "X": [2020, 2021, 2022, 2023, 2024],
        "Y": [3000, 2850, 2700, 2550, 2400]
      }
    }
  }
}
```

### Step 3: Update Config

1. Open `config.json`
2. Add your region to `regions` array if needed
3. Update data sources if using custom filenames

### Step 4: Test

```bash
python3 scripts/forecast.py --region MyRegion --end-year 2040 --output csv
```

## Data Sources and Collection

### Recommended Sources

**Cost Data:**
- Manufacturer MSRPs (list prices)
- Industry pricing databases
- Market research reports (e.g., IHS Markit, McKinsey)
- Online marketplace data (e.g., Alibaba for China, IndiaMART for India)
- Commercial vehicle fleet operators

**Sales Data:**
- National vehicle registration databases
- Industry associations (e.g., CAAM for China, SIAM for India)
- Manufacturer financial reports
- Market research firms
- Government transportation statistics

**Fleet Data:**
- Government transportation departments
- Registration databases
- Census data
- Commercial fleet surveys
- Ride-hailing platform data

### Data Processing Guidelines

1. **Currency Conversion**: Convert all to USD at constant exchange rate
2. **Inflation Adjustment**: Adjust to base year (e.g., 2023 USD)
3. **Regional Aggregation**: Sum constituent countries for "Rest_of_World" (primarily India)
4. **Missing Values**: Interpolate short gaps (<2 years), flag longer gaps
5. **Outliers**: Use domain knowledge to validate or correct

### Three-Wheeler Specific Considerations

**Rest_of_World Region:**
- Heavily dominated by India's three-wheeler market
- Include other emerging markets: Southeast Asia, Latin America, Africa
- Weight India appropriately (typically >80% of Rest_of_World)

**Commercial Use Context:**
- Most three-wheelers are commercial vehicles
- Pricing data should reflect commercial/fleet pricing, not retail
- Consider TCO (Total Cost of Ownership) not just purchase price

## Troubleshooting Data Issues

### Error: "Dataset not found in taxonomy"

**Cause**: Mismatch between requested dataset and taxonomy entries

**Solution**:
1. Check spelling of dataset name
2. Verify region name matches exactly
3. Confirm entry exists in taxonomy JSON

### Error: "No data for region X in dataset Y"

**Cause**: Data curves file missing region data

**Solution**:
1. Check if dataset uses "regions" nested structure
2. Verify region name matches exactly (case-sensitive)
3. Confirm X and Y arrays are present

### Warning: "No curve data, returning dummy data"

**Cause**: Data curves file not found or dataset missing

**Solution**:
1. Ensure `Three_Wheeler.json` exists in `data/` directory
2. Check file is valid JSON (no syntax errors)
3. Verify dataset name matches taxonomy exactly

### Error: "USA region not available"

**Cause**: USA excluded from three-wheeler analysis

**Solution**:
- Use China, Europe, Rest_of_World, or Global regions only
- Three-wheeler market in USA is negligible

## Example: Complete Data Setup

**Directory structure:**
```
.claude/skills/three-wheeler-demand/data/
├── three_wheeler_taxonomy_and_datasets.json
├── Three_Wheeler.json
└── three_wheeler_demand_instructions.md
```

**Minimal working example:**

`taxonomy.json` (excerpt):
```json
{
  "datasets": {
    "EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_China": { ... },
    "Three_Wheeler_(ICE)_Median_Cost_China": { ... },
    "Three_Wheeler_Annual_Sales_China": { ... },
    "Three_Wheeler_(EV)_Annual_Sales_China": { ... }
  }
}
```

`Three_Wheeler.json` (excerpt):
```json
{
  "EV_3_Wheeler_(Range-100_KM)_Lowest_Cost_China": {
    "regions": {
      "China": {
        "X": [2015, 2016, ..., 2024],
        "Y": [4500, 4200, ..., 1850]
      }
    }
  },
  ...
}
```

Then run:
```bash
python3 scripts/forecast.py --region China --end-year 2040 --output csv
```

## Regional Data Notes

### China
- Well-established three-wheeler market
- Strong urban delivery and taxi use
- Good data availability

### Europe
- Emerging three-wheeler market
- Limited to urban delivery applications
- Sparse historical data

### Rest_of_World (India-dominated)
- Largest global three-wheeler market
- India represents >80% of this category
- Rich data availability through SIAM and government sources
- Strong commercial use case (auto-rickshaws, delivery)
