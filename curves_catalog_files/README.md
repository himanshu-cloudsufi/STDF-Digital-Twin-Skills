# Curves Catalog - Split by Entity

This folder contains the optimized curves catalog split into individual files, one per entity/level.

## Overview

- **Total Files**: 20 entities
- **Total Metrics**: 235
- **Total Datasets**: 825
- **Total Size**: 0.83 MB

## Structure

Each file contains one entity with its metrics and regional data:

```
{
  "Entity Name": {
    "Metric_Name": {
      "metadata": {
        "type": "...",
        "units": "...",
        "source": "...",
        "category": "...",
        "entity_type": "...",
        "description": "..."
      },
      "regions": {
        "China": {"X": [...], "Y": [...]},
        "Europe": {"X": [...], "Y": [...]},
        "Global": {"X": [...], "Y": [...]},
        ...
      }
    }
  }
}
```

## Files

| Entity | Filename | Size | Datasets |
|--------|----------|------|----------|
| Energy Generation | `Energy_Generation.json` | 174 KB | 106 |
| Passenger Cars | `Passenger_Cars.json` | 125 KB | 128 |
| Commercial Vehicle | `Commercial_Vehicle.json` | 107 KB | 144 |
| Copper | `Copper.json` | 71 KB | 48 |
| Crude Oil | `Crude_Oil.json` | 53 KB | 35 |
| Aluminium | `Aluminium.json` | 47 KB | 44 |
| Two Wheeler | `Two_Wheeler.json` | 38 KB | 40 |
| Datacenter UPS | `Datacenter_UPS.json` | 33 KB | 35 |
| Three Wheeler | `Three_Wheeler.json` | 32 KB | 34 |
| Telecom UPS | `Telecom_UPS.json` | 32 KB | 35 |
| Battery Pack | `Battery_Pack.json` | 29 KB | 37 |
| Forklift | `Forklift.json` | 25 KB | 26 |
| Energy Storage | `Energy_Storage.json` | 23 KB | 46 |
| Electricity | `Electricity.json` | 21 KB | 22 |
| Compute Chipsets | `Compute_Chipsets.json` | 12 KB | 13 |
| Coal | `Coal.json` | 12 KB | 5 |
| Agentic AI | `Agentic_AI.json` | 8 KB | 19 |
| Lead | `Lead.json` | 7 KB | 6 |
| Artificial Intelligence | `Artificial_Intelligence.json` | 1 KB | 2 |
| Polysilicon | `Polysilicon.json` | 1 KB | 1 |

## Usage

### Load Specific Entity

```python
import json

# Load only the data you need
with open('curves_catalog_files/Agentic_AI.json', 'r') as f:
    agentic_ai_data = json.load(f)

# Access metrics
entity = agentic_ai_data['Agentic AI']
deployment_cost = entity['Deployment_Cost']

# Access regional data
china_data = deployment_cost['regions']['China']
print(f"X: {china_data['X']}")
print(f"Y: {china_data['Y']}")
```

### Browse Available Entities

```python
import json

# Load the index to see what's available
with open('curves_catalog_files/_index.json', 'r') as f:
    index = json.load(f)

for entity_name, info in index['entities'].items():
    print(f"{entity_name}: {info['datasets_count']} datasets, {info['metrics_count']} metrics")
    print(f"  File: {info['filename']}")
```

## Benefits

1. **Selective Loading**: Load only the entities you need instead of the entire 1 MB file
2. **Reduced Memory**: Smaller memory footprint when working with specific entities
3. **Faster Access**: Quicker to parse smaller JSON files
4. **Better Organization**: Easy to navigate and understand what data is available
5. **LLM Optimization**: Include only relevant entity files in LLM context

## Comparison with Original

| Format | Files | Size | Loading |
|--------|-------|------|---------|
| Original Flat | 1 file | 1.03 MB | Load all 825 datasets |
| Optimized Single | 1 file | 0.83 MB | Load all 825 datasets |
| **Split Files** | **20 files** | **0.83 MB** | **Load only what you need** |

---

Generated from `curves_catalog_v2.json` using hierarchical optimization and splitting.
