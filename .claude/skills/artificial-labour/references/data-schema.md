# Artificial Labour Data Schema

Complete reference for the AL_JSON.json data structure.

## Files

- **AL_JSON.json** - Raw time series data (93 datasets)
- **artificial_labour_taxonomy_and_datasets.json** - Taxonomy, disruption pairs, convergence products, service metrics

## AL_JSON.json Structure Overview

```
{
  "Category": {
    "Dataset_Name": {
      "metadata": {...},
      "regions": {
        "Region_Name": {
          "X": [years],
          "Y": [values]
        }
      }
    }
  }
}
```

## Categories

### 1. Artificial Intelligence
68 datasets covering AI capabilities, performance benchmarks, and adoption metrics.

**Key datasets:**
- `Artificial_Intelligence_Traning_Dataset_Size` - Training data volume (tokens)
- `Artificial_Intelligence_MMLU_Accuracy` - Multitask language understanding (%)
- `Artificial_Intelligence_GSM8K_Accuracy` - Grade-school math reasoning (%)
- `Artificial_Intelligence_HumanEval_Accuracy` - Code generation performance (%)
- `Artificial_Intelligence_GPQA_Diamond_Accuracy` - Expert-level Q&A (%)
- Plus: adoption metrics, inference costs, model parameters, and more

### 2. Industrial Robot
12 datasets on industrial robot installations and operational stock.

**Key datasets:**
- `Industrial_Robot_Annual_Installation` - New installations per year
- `Industrial_Robot_Operational_stock` - Total active robots
- By industry:
  - `Industrial_Robot_Annual_Installation_(Automotive)`
  - `Industrial_Robot_Annual_Installation_(Electrical_Electronics)`
  - `Industrial_Robot_Annual_Installation_(Metal_and_Machinery)`
  - `Industrial_Robot_Annual_Installation_(Plastics_and_Chemical_Products)`
  - `Industrial_Robot_Annual_Installation_(Food)`
  - `Industrial_Robot_Annual_Installation_(Others)`

### 3. Service Robot (Professional)
6 datasets on professional service robot deployments.

**Key datasets:**
- `Service_Robot_(Professional)_Annual_Installation`
- By sector:
  - `Service_Robot_(Professional)_Annual_Installation_(Agriculture)`
  - `Service_Robot_(Professional)_Annual_Installation_(Hospitality)`
  - `Service_Robot_(Professional)_Annual_Installation_(Logistics)`
  - `Service_Robot_(Professional)_Annual_Installation_(Medical)`
  - `Service_Robot_(Professional)_Annual_Installation_(Others)`

### 4. Humanoid Robot
1 dataset on humanoid robot market.

**Key dataset:**
- `Humanoid_Robot_Market_Size` - Market size projections

### 5. GPU
6 datasets on GPU pricing and performance.

**Key datasets:**
- `GPU_NVIDIA_Tesla_V100_Price`
- `GPU_NVIDIA_A100_Tensor_Core_Price`
- `GPU_NVIDIA_H100_Tensor_Core_Price`
- `GPU_AMD_MI300X_Price`
- `GPU_AMD_MI250X_Price`
- `GPU_AMD_MI210_Price`

## Metadata Fields

Each dataset includes metadata with the following fields:

### type
Classification of the metric. Common values:
- `"adoption"` - Adoption or deployment metric
- `"Performance Benchmark"` - Capability/performance measure
- `"cost"` - Economic/pricing data
- `"annual adoption"` - Yearly adoption figures

### units
Measurement units. Examples:
- `"%"` - Percentage
- `"Token"` - Data tokens
- `"USD"` - US Dollars
- `"Unit"` - Count/quantity
- `"million USD"` - Millions of dollars

### source
Data source attribution. Examples:
- `"Epoch AI"`
- `"Stanford"`
- `"IFR"` (International Federation of Robotics)
- `"ARK Invest"`
- `"Goldman Sachs"`
- `"Various"` or `"Public Data"`

### category
Broader classification. Examples:
- `"annual adoption"`
- `"Performance Benchmark"`
- `"operational stock"`
- `"market size"`

### entity_type
Role in disruption framework:
- `"disruptor"` - Disruptive technology/metric
- `"incumbent"` - Established technology/baseline
- `"enabler"` - Enabling technology
- `"mixed"` - Hybrid or unclear role

### description
Text description explaining what the metric measures, context, and methodology.

## Regional Coverage

Most datasets include one or more of these regions:

- `"Global"` - Worldwide aggregate
- `"China"`
- `"USA"` (or `"US"`)
- `"Europe"`
- `"Rest_of_World"`
- `"Asia_Pacific"`
- `"Americas"`

**Note:** Not all datasets have all regions. Use `get_regions()` to check available regions for a dataset.

## Time Series Format

### X (Years)
- Array of strings representing years
- Format: `"YYYY"` (e.g., `"2020"`, `"2023"`)
- May include future projection years
- Not always evenly spaced (gaps are common)

### Y (Values)
- Array of numeric values
- Units specified in metadata
- Same length as X array
- May include very large ranges (e.g., GPU performance: 1e12 to 1e18)

## Example Queries

### Get all categories
```python
loader = ALDataLoader()
categories = loader.get_categories()
# Returns: ['Artificial Intelligence', 'Industrial Robot', ...]
```

### Get datasets in a category
```python
datasets = loader.get_datasets('Artificial Intelligence')
# Returns list of 68 AI datasets
```

### Get time series data
```python
X, Y = loader.get_time_series(
    'Artificial Intelligence',
    'Artificial_Intelligence_MMLU_Accuracy',
    'Global'
)
# X: array([2019., 2020., 2021., 2022., 2023., 2024.])
# Y: array([33., 55., 60., 75., 85., 92.3])
```

### Get metadata
```python
meta = loader.get_metadata(
    'Artificial Intelligence',
    'Artificial_Intelligence_MMLU_Accuracy'
)
# Returns: {
#   'type': 'Performance Benchmark',
#   'units': '%',
#   'source': 'Stanford',
#   'entity_type': 'disruptor',
#   'description': '...'
# }
```

### Search for datasets
```python
results = loader.search_datasets('robot')
# Returns all datasets with 'robot' in the name
```

## Data Quality Notes

- **Coverage varies:** Not all datasets have the same time span
- **Projection data:** Some datasets include future projections (post-2024)
- **Source diversity:** Data comes from academic, industry, and financial sources
- **Units matter:** Always check metadata units before comparing datasets
- **Regional gaps:** Some datasets only have Global data
- **Sparse series:** Some metrics have only a few data points (e.g., 2-3 years)

## Common Patterns

### AI Capabilities (Benchmarks)
- Typically annual or less frequent
- Measured in percentage (0-100%)
- Exponential improvement trend
- Global region only

### Robot Installations
- Annual data (installation counts)
- Regional breakdowns available
- Linear to exponential growth
- Units are typically raw counts or thousands

### GPU Pricing
- Point-in-time pricing
- USD units
- Declining cost curves (exponential)
- May have sparse data (product release dates)

### Training Data / Model Size
- Exponential growth
- Very large ranges (10^6 to 10^12+)
- Global aggregates
- Annual or per-model snapshots

---

## Taxonomy File (artificial_labour_taxonomy_and_datasets.json)

### Purpose
Provides structured mapping of:
- Product taxonomy and hierarchy
- Dataset to entity type mappings
- Disruption pairs (disruptor vs incumbent)
- Convergence products and capabilities
- Service-level cost metrics
- Tipping point thresholds

### Key Sections

#### 1. Taxonomy
Hierarchical structure of artificial labour categories:
- **Artificial_Intelligence:** Language models, code gen, reasoning, vision, multimodal
- **Physical_Automation:** Industrial, service, humanoid robots
- **Compute_Infrastructure:** GPUs, AI accelerators

#### 2. Data Mappings
Links datasets to entity types and use cases:
- **AI capabilities:** MMLU, GSM8K, HumanEval, etc.
- **Robot demand:** Installations by region and sector
- **GPU costs:** Pricing by model (V100, A100, H100)
- **Human labour:** Cost benchmarks by task type

#### 3. Disruption Pairs
Defines disruptor-incumbent matchups with:
- Use case (task being automated)
- Disruptor capability metric
- Incumbent cost benchmark
- Service unit ($/task, $/hour)

**Examples:**
- AI code generation vs human developers
- Industrial robots vs assembly workers
- Service robots vs warehouse pickers

#### 4. Convergence Products
Multi-technology combinations creating new capabilities:
- **AI + Industrial Robots** → Adaptive manufacturing
- **AI + Service Robots** → Autonomous navigation
- **AI + Humanoid Robots** → General-purpose labor
- **AI + GPU + Cloud** → AI-as-a-Service

#### 5. Service Metrics
Standard cost calculations for each AL type:
- **AI:** `(GPU cost + energy + overhead) / throughput` = $/inference
- **Robots:** `(CAPEX / lifetime + OPEX) / tasks per hour` = $/task

#### 6. Tipping Point Thresholds
Standard thresholds for disruption analysis:
- **AI capability:** 85-95% = human-level, >95% = superhuman
- **Cost parity:** <50% of incumbent cost = tipping zone
- **Adoption:** 10% early, 50% mainstream, 80% late

### Usage Examples

**Load taxonomy:**
```python
import json
with open('data/artificial_labour_taxonomy_and_datasets.json', 'r') as f:
    taxonomy = json.load(f)
```

**Get disruption pairs:**
```python
for pair in taxonomy['disruption_pairs']:
    print(f"{pair['disruptor']} vs {pair['incumbent']}")
    for use_case in pair['use_cases']:
        print(f"  Task: {use_case['task']}")
        print(f"  Service unit: {use_case['service_unit']}")
```

**Calculate service cost:**
```python
service_metrics = taxonomy['service_metrics']
ai_formula = service_metrics['AI']['calculation']
print(f"AI cost formula: {ai_formula}")
```

**Check tipping thresholds:**
```python
thresholds = taxonomy['tipping_point_thresholds']
human_level = thresholds['AI_capability']['human_level']
print(f"Human-level AI: {human_level}")
```

### Integration with AL_JSON.json

The taxonomy maps friendly names to actual dataset keys:

**Example mapping:**
```
Taxonomy: "language_understanding" 
→ Dataset: "Artificial_Intelligence_MMLU_Accuracy"
→ AL_JSON.json: data['Artificial Intelligence']['Artificial_Intelligence_MMLU_Accuracy']
```

This allows queries like:
```python
# Using taxonomy
capability_ds = taxonomy['data']['Artificial_Intelligence']['capability']['Global']['language_understanding']

# Load from AL_JSON
X, Y = loader.get_time_series('Artificial Intelligence', capability_ds, 'Global')
```
