# Data Schema Reference - Energy Forecasting (SWB)

## Data Files

| File | Location | Purpose |
|------|----------|---------|
| Energy_Generation.json | data/ | Solar, wind, coal, gas generation/capacity/LCOE |
| Energy_Storage.json | data/ | Battery costs and capacity |
| Electricity.json | data/ | Total electricity demand/production |
| swb_taxonomy_and_datasets.json | data/ | Product mappings and dataset names |

## Taxonomy Structure

```json
{
  "products": {
    "Solar_PV": {
      "entity_type": "disruptor",
      "lcoe": {"China": "Dataset_Name", "USA": "..."},
      "capacity": {"China": "Dataset_Name", "USA": "..."},
      "generation": {"China": "Dataset_Name", "USA": "..."},
      "capacity_factor": {"China": "Dataset_Name", ...}
    },
    "Coal_Power": {
      "entity_type": "incumbent",
      "lcoe": {...},
      "generation": {...}
    }
  },
  "electricity_system": {
    "demand": {"China": "Dataset_Name", ...}
  }
}
```

## Entity File Structure

```json
{
  "Energy Generation": {
    "Dataset_Name": {
      "metadata": {
        "type": "cost|adoption|capacity",
        "units": "$/MWh|GW|GWh",
        "entity_type": "disruptor|incumbent",
        "category": "annual adoption|cost"
      },
      "regions": {
        "China": {
          "X": [2015, 2016, 2017, ...],
          "Y": [123.4, 115.2, 108.7, ...]
        },
        "USA": {
          "standard": {
            "X": [years],
            "Y": [values]
          }
        }
      }
    }
  }
}
```

## Dataset Types

| Type | Units | Example Datasets |
|------|-------|-----------------|
| LCOE | $/MWh | Solar_LCOE_Utility, Coal_LCOE |
| Capacity | GW | Solar_PV_Capacity, Wind_Onshore_Capacity |
| Generation | GWh | Coal_Generation, Solar_Generation |
| Capacity Factor | Decimal (0-1) | Solar_CF, Wind_CF |
| Installed Cost | $/kW or $/kWh | Battery_Cost_4_Hour |

## Regional Data Variants

Some datasets have nested scenarios:
```json
"regions": {
  "China": {
    "standard": {"X": [...], "Y": [...]},
    "Prosperity": {"X": [...], "Y": [...]}
  }
}
```

**Default**: Always use `"standard"` scenario if available, otherwise use direct `{"X": [], "Y": []}`.

## Entity Types

| Entity Type | Description | Examples |
|-------------|-------------|----------|
| `disruptor` | New technology with declining costs | Solar_PV, Onshore_Wind, Battery_Storage |
| `incumbent` | Legacy technology being displaced | Coal_Power, Natural_Gas_Power |
| `chimera` | Bridge technology (not used in SWB) | - |
| `market` | Total market size | Electricity_System |

## Units

| Metric | Units | Conversion |
|--------|-------|-----------|
| Capacity | GW | Gigawatts |
| Generation | GWh | Gigawatt-hours per year |
| LCOE | $/MWh | Dollars per megawatt-hour |
| SCOE | $/MWh | Storage cost per megawatt-hour |
| Capacity Factor | Decimal | 0.0 to 1.0 (0% to 100%) |
| Battery Cost | $/kWh | Dollars per kilowatt-hour |

**Conversion Example:**
```
Capacity (GW) × Capacity Factor × 8760 hours = Generation (GWh)
100 GW × 0.30 × 8760 = 262,800 GWh
```

## Data Loading Examples

### Load LCOE
```python
from data_loader import DataLoader
loader = DataLoader()

years, lcoe = loader.get_lcoe_data("Solar_PV", "China")
# Returns: ([2015, 2016, ...], [123.4, 115.2, ...])
```

### Load Capacity
```python
years, capacity_gw = loader.get_capacity_data("Onshore_Wind", "USA")
```

### Load Generation
```python
years, generation_gwh = loader.get_generation_data("Coal_Power", "Europe")
```

### Load Capacity Factor
```python
years, cfs = loader.get_capacity_factor_data("Solar_PV", "China")
# May return (None, None) if not available → use default
```

## Data Quality Notes

- **Missing regions**: Some technologies lack data for all regions (fallback to estimates)
- **Missing CFs**: Capacity factors often not in datasets → use defaults
- **Historical coverage**: Datasets typically span 2000-2023, then forecasted
- **Nested structures**: Always check for "standard" key first
