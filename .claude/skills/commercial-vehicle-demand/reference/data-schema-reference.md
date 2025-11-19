# Commercial Vehicle Demand Forecasting - Data Schema Reference

## Input Data Files

### 1. Commercial_Vehicle.json
Primary data file containing historical cost and demand curves.

#### Structure
```json
{
  "Commercial Vehicle": {
    "metric_name": {
      "regions": {
        "region_name": {
          "X": [years],
          "Y": [values]
        }
      }
    }
  }
}
```

### 2. Required Metrics

#### Cost Series (Per Segment)
- `LCV_commercial_vehicle_(Range-100_KM)_Lowest_Cost`
- `MCV_commercial_vehicle_(Range-200_KM)_Lowest_Cost`
- `HCV_commercial_vehicle_(Range-400_KM)_Lowest_Cost`
- `Light_Duty_Commercial_Vehicle_(ICE)_Price`
- `Medium_Duty_Commercial_Vehicle_(ICE)_Price`
- `Heavy_Duty_Commercial_Vehicle_(ICE)_Price`

#### Demand Series (Total Market)
- `Commercial_Vehicle_Annual_Sales`
- `Commercial_Vehicle_(EV)_Annual_Sales`
- `Commercial_Vehicle_(ICE)_Annual_Sales`
- `Commercial_Vehicle_(NGV)_Annual_Sales`

#### Demand Series (Per Segment)
- `Light_Duty_Commercial_Vehicle_(EV)_Annual_Sales`
- `Light_Duty_Commercial_Vehicle_(ICE)_Annual_Sales`
- `Light_Duty_Commercial_Vehicle_(NGV)_Annual_Sales`
- (Repeat for Medium_Duty and Heavy_Duty)

#### Fleet Series (Optional)
- `Light_Duty_Commercial_Vehicle_(EV)_Total_Fleet`
- `Light_Duty_Commercial_Vehicle_(ICE)_Total_Fleet`
- `Light_Duty_Commercial_Vehicle_(NGV)_Total_Fleet`
- (Repeat for Medium_Duty and Heavy_Duty)

### 3. Example Data Structure

```json
{
  "Commercial Vehicle": {
    "LCV_commercial_vehicle_(Range-100_KM)_Lowest_Cost": {
      "regions": {
        "China": {
          "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
          "Y": [55000, 52000, 49000, 46000, 43000, 40000, 38000, 36000, 34000]
        },
        "USA": { ... }
      }
    },
    "Light_Duty_Commercial_Vehicle_(ICE)_Price": {
      "regions": {
        "China": {
          "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
          "Y": [35000, 35500, 36000, 36500, 37000, 37500, 38000, 38500, 39000]
        }
      }
    },
    "Light_Duty_Commercial_Vehicle_(EV)_Annual_Sales": {
      "regions": {
        "China": {
          "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
          "Y": [5000, 8000, 15000, 30000, 50000, 80000, 120000, 180000, 250000]
        }
      }
    },
    "Light_Duty_Commercial_Vehicle_(NGV)_Annual_Sales": {
      "regions": {
        "China": {
          "X": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
          "Y": [50000, 80000, 120000, 160000, 180000, 190000, 180000, 150000, 120000]
        }
      }
    }
  }
}
```

## Data Requirements

### Minimum Data Requirements
- **Cost data**: At least 3 years of historical data per segment
- **Demand data**: At least 5 years of historical data
- **Time coverage**: Recommended 2015-2023 or later

### Data Quality Guidelines
1. **Consistency**: Sales should sum correctly (EV+ICE+NGV ≈ Total)
2. **Non-negativity**: All values >= 0
3. **Continuity**: No large unexplained gaps in time series
4. **Units**: Consistent across all metrics
   - Costs in USD
   - Sales in units per year
   - Fleet in total units

### Handling Missing Data
- **Missing cost years**: Tool will interpolate if gaps < 3 years
- **Missing NGV data**: Tool treats as negligible presence
- **Missing fleet data**: Fleet tracking disabled automatically

## Taxonomy File

### File: commercial_vehicle_taxonomy_and_datasets.json

#### Purpose
Maps dataset names to metadata for discovery and validation.

#### Structure
```json
{
  "datasets": {
    "dataset_name": {
      "entity": "Light_Duty_Commercial_Vehicles",
      "region": "China",
      "category": "cost" | "demand" | "fleet",
      "powertrain": "EV" | "ICE" | "NGV" | "Total",
      "metadata": {
        "description": "...",
        "unit": "USD" | "units",
        "source": "..."
      }
    }
  }
}
```

#### Example
```json
{
  "datasets": {
    "LCV_commercial_vehicle_(Range-100_KM)_Lowest_Cost_China": {
      "entity": "Light_Duty_Commercial_Vehicles",
      "region": "China",
      "category": "cost",
      "powertrain": "EV",
      "metadata": {
        "description": "LCV EV lowest cost with 100km range",
        "unit": "USD",
        "range_km": 100
      }
    },
    "Light_Duty_Commercial_Vehicle_(EV)_Annual_Sales_China": {
      "entity": "Light_Duty_Commercial_Vehicles",
      "region": "China",
      "category": "demand",
      "powertrain": "EV",
      "metadata": {
        "description": "LCV EV annual sales",
        "unit": "units"
      }
    }
  }
}
```

## Data Validation

### Validation Script
```bash
python3 scripts/data_loader.py
```

Expected output:
```
✓ Data loader initialized
Available regions: ['China', 'USA', 'Europe', 'Rest_of_World']
Available segments: ['LCV', 'MCV', 'HCV']

✓ LCV EV Cost Data for China:
  Years: [2015, 2016, 2017]
  Costs: [55000, 52000, 49000]

✓ Total Market Demand Data for China:
  Years: [2015, 2016, 2017]
  Demand: [1000000, 1050000, 1100000]
```

### Common Issues

**1. "Dataset not found in taxonomy"**
- Check dataset name spelling
- Verify taxonomy file is up to date
- Ensure region name matches exactly (case-sensitive)

**2. "No data for region X"**
- Check that region exists in curves file
- Verify nested structure: `Commercial Vehicle → metric → regions → region`

**3. "Unexpected data structure"**
- Ensure data follows either:
  - Nested: `{regions: {region: {X: [...], Y: [...]}}}`
  - Flat: `{X: [...], Y: [...]}`

**4. "Sum consistency violated"**
- Check EV + ICE + NGV = Total for each segment
- Verify segment totals: LCV + MCV + HCV = Total CV

## Data Update Workflow

### Adding New Historical Data
1. Update `Commercial_Vehicle.json` with new years/values
2. Maintain consistent structure
3. Validate using `data_loader.py`
4. Run test forecasts to verify

### Adding New Regions
1. Add region data to all required metrics
2. Update taxonomy file
3. Test with: `python3 scripts/forecast.py --region NewRegion --segment LCV`

### Adding New Segments
Requires code changes - not recommended without developer support

## See Also

- `SKILL.md`: Usage guide
- `methodology-reference.md`: Algorithm details
- `output-formats-reference.md`: Output format specifications
