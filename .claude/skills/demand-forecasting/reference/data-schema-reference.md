# Data Schema Reference

Complete documentation of data file structures, JSON formats, dataset naming conventions, and data access patterns.

## Contents
- Data Files Overview
- Passenger_Cars.json Structure
- Taxonomy File Structure
- Dataset Naming Conventions
- Entity Types
- Regional Data Organization
- Units and Normalization
- Data Loading Patterns

---

## Data Files Overview

### Primary Data Files

Located in `data/` directory:

**1. Passenger_Cars.json** (~100 KB)
- Main data file containing all cost and demand curves
- Organized by metric → regions → time series
- Includes metadata for each metric

**2. passenger_vehicles_taxonomy_and_datasets.json** (~3.5 KB)
- Maps product types to dataset names
- Defines entity types (disruptor, incumbent, chimera, market)
- Regional dataset name mappings

---

## Passenger_Cars.json Structure

### Top-Level Structure

```json
{
  "Passenger Cars": {
    "Metric_Name_1": { ... },
    "Metric_Name_2": { ... },
    ...
  }
}
```

All data is nested under `"Passenger Cars"` key.

### Metric Structure

Each metric has this structure:

```json
"Metric_Name": {
  "metadata": {
    "type": "cost" | "demand" | "installed_base",
    "units": "USD" | "units" | "vehicles",
    "source": "Source description",
    "category": "Category description",
    "entity_type": "disruptor" | "incumbent" | "chimera" | "market",
    "description": "Human-readable description"
  },
  "regions": {
    "China": {
      "X": [year1, year2, year3, ...],
      "Y": [value1, value2, value3, ...]
    },
    "USA": { ... },
    "Europe": { ... },
    "Rest_of_World": { ... },
    "Global": { ... }
  }
}
```

### Metadata Fields

**type**
- `"cost"`: Price or cost data (USD)
- `"demand"`: Annual sales (units)
- `"installed_base"`: Total fleet size (units)

**units**
- `"USD"`: US Dollars (usually real/inflation-adjusted)
- `"units"`: Number of vehicles
- `"vehicles"`: Same as units

**entity_type**
- `"disruptor"`: EV/BEV technology
- `"incumbent"`: ICE technology
- `"chimera"`: PHEV (transition technology)
- `"market"`: Total passenger vehicle market

### Regional Data Format

**X array**: Years (integers)
- Sorted chronologically
- Typically ranges from historical data (e.g., 2010-2023) to forecasts

**Y array**: Values (floats)
- Must have same length as X array
- Units specified in metadata.units
- Missing data represented by gaps (not null)

### Example: EV Cost Data

```json
"Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost": {
  "metadata": {
    "type": "cost",
    "units": "USD",
    "source": "RethinkX Analysis",
    "category": "cost per unit capability",
    "entity_type": "disruptor",
    "description": "Lowest cost for passenger EV cars with 200-mile range"
  },
  "regions": {
    "China": {
      "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
      "Y": [35000, 32000, 29000, 26000, 23000, 20000, 18000, 16000, 14500]
    },
    "USA": {
      "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
      "Y": [40000, 37000, 34000, 31000, 28000, 25000, 23000, 21000, 19000]
    }
  }
}
```

### Example: Demand Data

```json
"Passenger_Vehicle_(BEV)_Annual_Sales": {
  "metadata": {
    "type": "demand",
    "units": "units",
    "source": "Industry Data",
    "category": "annual sales",
    "entity_type": "disruptor",
    "description": "Annual sales of battery electric vehicles"
  },
  "regions": {
    "China": {
      "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
      "Y": [150000, 250000, 400000, 600000, 950000, 1200000, 1800000, 2500000, 3200000]
    }
  }
}
```

---

## Taxonomy File Structure

### Purpose

Maps logical product types (EV_Cars, ICE_Cars, etc.) to actual dataset names in Passenger_Cars.json for each region.

### Top-Level Structure

```json
{
  "market": "Passenger_Vehicles",
  "taxonomy": { ... },
  "data": { ... }
}
```

### Taxonomy Section

Defines product hierarchies:

```json
"taxonomy": {
  "EV_Cars": {
    "subproducts": ["BEV_Cars", "PHEV_Cars"]
  },
  "ICE_Cars": {
    "subproducts": []
  }
}
```

**Interpretation**:
- EV_Cars is aggregate of BEV_Cars + PHEV_Cars
- ICE_Cars has no subproducts (atomic)

### Data Section

Maps product types to dataset names by region:

```json
"data": {
  "EV_Cars": {
    "cost": {
      "China": "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost",
      "USA": "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost",
      "Europe": "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost",
      "Rest_of_World": "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost"
    },
    "demand": {
      "China": "Passenger_Vehicle_(EV)_Annual_Sales",
      "USA": "Passenger_Vehicle_(EV)_Annual_Sales",
      "Europe": "Passenger_Vehicle_(EV)_Annual_Sales",
      "Rest_of_World": "Passenger_Vehicle_(EV)_Annual_Sales",
      "Global": "Passenger_Vehicle_(EV)_Annual_Sales"
    },
    "entity_type": "disruptor"
  },
  "ICE_Cars": {
    "cost": {
      "China": "Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)",
      "USA": "Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)",
      "Europe": "Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)",
      "Rest_of_World": "Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)"
    },
    "demand": {
      "China": "Passenger_Vehicle_(ICE)_Annual_Sales",
      "USA": "Passenger_Vehicle_(ICE)_Annual_Sales",
      "Europe": "Passenger_Vehicle_(ICE)_Annual_Sales",
      "Rest_of_World": "Passenger_Vehicle_(ICE)_Annual_Sales",
      "Global": "Passenger_Vehicle_(ICE)_Annual_Sales"
    },
    "entity_type": "incumbent"
  }
}
```

**Data types**:
- `cost`: Price/cost datasets
- `demand`: Annual sales datasets
- `installed_base`: Total fleet datasets (optional)

---

## Dataset Naming Conventions

### Pattern Recognition

**Cost datasets**:
- Format: `Passenger_{Product}_Price` or `Passenger_{Product}_Lowest_Cost`
- Examples:
  - `Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost`
  - `Passenger_Vehicle_(ICE)_Median_Price_(Mid_Size_Sedan)`

**Demand datasets**:
- Format: `Passenger_Vehicle_({Product})_Annual_Sales`
- Examples:
  - `Passenger_Vehicle_(BEV)_Annual_Sales`
  - `Passenger_Vehicle_(PHEV)_Annual_Sales`
  - `Passenger_Vehicle_(ICE)_Annual_Sales`
  - `Passenger_Vehicle_Annual_Sales` (total market)

**Fleet datasets**:
- Format: `Passenger_Vehicle_({Product})_Total_Fleet`
- Examples:
  - `Passenger_Vehicle_(BEV)_Total_Fleet`
  - `Passenger_Vehicle_(ICE)_Total_Fleet`

### Product Identifiers

- `EV_Cars`: Electric vehicles (aggregate of BEV + PHEV)
- `BEV_Cars`: Battery Electric Vehicles
- `PHEV_Cars`: Plug-in Hybrid Electric Vehicles
- `ICE_Cars`: Internal Combustion Engine vehicles
- `Passenger_Vehicles`: Total market (all types)

---

## Entity Types

### Disruptor
**Products**: EV_Cars, BEV_Cars

**Characteristics**:
- Challenger technology
- Cost declining rapidly
- Growing market share
- Subject to logistic growth curve post-tipping

### Incumbent
**Products**: ICE_Cars

**Characteristics**:
- Established technology
- Mature cost structure (slow decline)
- Declining market share post-tipping
- Residual calculation (Market − Disruptor − Chimera)

### Chimera
**Products**: PHEV_Cars

**Characteristics**:
- Transition/hybrid technology
- Temporary bridge between incumbent and disruptor
- "Hump" trajectory: rises before tipping, declines after
- Decay with ~3-year half-life post-tipping

### Market
**Products**: Passenger_Vehicles

**Characteristics**:
- Total addressable market
- Sum of all product types
- Subject to CAGR capping (±5%)
- Forecasted independently via linear extrapolation

---

## Regional Data Organization

### Supported Regions

**1. China**
- Largest passenger vehicle market
- Rapid EV adoption
- Strong policy support

**2. USA**
- Large mature market
- Moderate EV adoption
- Mixed policy environment

**3. Europe**
- Aggregated European markets
- Strong EV policy
- Good infrastructure

**4. Rest_of_World**
- Calculated as: World − (China + USA + Europe)
- Diverse markets with varying adoption rates
- Limited infrastructure in many areas

**5. Global**
- World aggregate
- Sum of all regional demands
- Not independently forecasted; aggregated from regions

### Data Availability by Region

Not all datasets have all regions:
- Cost data typically has: China, USA, Europe, Rest_of_World
- Demand data typically has: China, USA, Europe, Rest_of_World, Global
- Global cost not meaningful (different currencies, price levels)

---

## Units and Normalization

### Cost Data Units

**Currency**: USD (US Dollars)
- Should be real/inflation-adjusted
- Normalize to same trim level or configuration
- Alternative: cost per mile/km for usage-based comparison

**Normalization requirements**:
- EV and ICE costs must be comparable
- Same vehicle class (e.g., mid-size sedan)
- Same capability level (e.g., 200-mile range)
- Same time basis (real USD, not nominal)

### Demand Data Units

**Units**: Vehicles
- Annual sales (not cumulative)
- Measured in units sold per year
- Must aggregate correctly: BEV + PHEV + ICE = Market

**Consistency checks**:
- No negative values
- BEV + PHEV + ICE ≤ Market (+ small epsilon)
- Smooth year-over-year transitions

---

## Data Loading Patterns

### Using DataLoader Class

Located in `scripts/data_loader.py`:

```python
from scripts.data_loader import DataLoader

# Initialize loader (auto-detects data/ directory)
loader = DataLoader()

# Load cost data for specific region
ev_cost = loader.load_cost_data("EV_Cars", "China")
# Returns: {"X": [years], "Y": [costs]}

ice_cost = loader.load_cost_data("ICE_Cars", "China")

# Load demand data
market_demand = loader.load_demand_data("Passenger_Vehicles", "China")
bev_demand = loader.load_demand_data("BEV_Cars", "China")
phev_demand = loader.load_demand_data("PHEV_Cars", "China")
ice_demand = loader.load_demand_data("ICE_Cars", "China")
```

### Direct JSON Access

```python
import json

# Load curves catalog
with open('data/Passenger_Cars.json') as f:
    curves = json.load(f)['Passenger Cars']

# Access specific dataset
dataset_name = "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost"
ev_data_china = curves[dataset_name]['regions']['China']
years = ev_data_china['X']
costs = ev_data_china['Y']

# Access metadata
metadata = curves[dataset_name]['metadata']
units = metadata['units']
entity_type = metadata['entity_type']
```

### Using Taxonomy for Dataset Resolution

```python
import json

# Load taxonomy
with open('data/passenger_vehicles_taxonomy_and_datasets.json') as f:
    taxonomy = json.load(f)

# Get dataset name for specific product and region
product = "EV_Cars"
region = "China"
dataset_name = taxonomy['data'][product]['cost'][region]
# Returns: "Passenger_EV_Cars_(Range_-200_miles)_Lowest_Cost"

# Then load from Passenger_Cars.json
with open('data/Passenger_Cars.json') as f:
    curves = json.load(f)['Passenger Cars']
    data = curves[dataset_name]['regions'][region]
```

---

## Data Quality Considerations

### Handling Missing Data

**Gaps in time series**:
- Not represented as null/None
- Simply missing years in X array
- Interpolate if needed for forecasting

**Missing regions**:
- Some datasets may not have all regions
- Check for KeyError when accessing
- Fallback to alternate region or skip

### Data Validation

**Required checks**:
1. X and Y arrays have same length
2. X array is sorted chronologically
3. No duplicate years in X
4. Y values are numeric (not strings)
5. Cost values are positive
6. Demand values are non-negative

**Implementation**:
```python
def validate_dataset(data):
    assert len(data['X']) == len(data['Y']), "X and Y length mismatch"
    assert data['X'] == sorted(data['X']), "X not sorted"
    assert len(data['X']) == len(set(data['X'])), "Duplicate years in X"
    assert all(isinstance(y, (int, float)) for y in data['Y']), "Non-numeric Y"
```

### Historical vs Forecast Data

The JSON files may contain both historical and forecasted data mixed in same arrays:
- Historical data: Observed actual values
- Forecast data: Model predictions or extrapolations
- No explicit flag distinguishes them
- Typically historical ends around 2023-2024

---

## Common Data Access Patterns

### Pattern 1: Load All Data for Region

```python
loader = DataLoader()
region = "China"

# Cost curves
ev_cost = loader.load_cost_data("EV_Cars", region)
ice_cost = loader.load_cost_data("ICE_Cars", region)

# Demand curves
market = loader.load_demand_data("Passenger_Vehicles", region)
bev = loader.load_demand_data("BEV_Cars", region)
phev = loader.load_demand_data("PHEV_Cars", region)
ice = loader.load_demand_data("ICE_Cars", region)
```

### Pattern 2: Check Data Availability

```python
try:
    data = loader.load_cost_data("EV_Cars", "China")
    print(f"Data available: {len(data['X'])} points from {data['X'][0]} to {data['X'][-1]}")
except KeyError:
    print("Dataset not found for this region")
```

### Pattern 3: Iterate Over All Regions

```python
regions = ["China", "USA", "Europe", "Rest_of_World"]
for region in regions:
    try:
        data = loader.load_demand_data("BEV_Cars", region)
        print(f"{region}: {data['Y'][-1]} units in {data['X'][-1]}")
    except KeyError:
        print(f"{region}: No data available")
```

---

## Summary

**Key points**:
- All data stored in `Passenger_Cars.json` under `"Passenger Cars"` key
- Each metric has metadata + regional time series (X, Y arrays)
- Taxonomy file maps logical products to dataset names
- Four entity types: disruptor, incumbent, chimera, market
- Five regions: China, USA, Europe, Rest_of_World, Global
- Use DataLoader class for convenient access
- Validate data structure and check for missing regions

**When troubleshooting data issues**:
1. Check dataset name spelling (case-sensitive)
2. Verify region exists for that dataset
3. Validate X and Y array lengths match
4. Ensure years are sorted
5. Check units in metadata match expected type
