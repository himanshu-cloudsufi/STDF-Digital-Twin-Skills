---
name: artificial-labour
description: >
  Analyzes artificial labour (AI, robotics, GPUs) using disruption framework. Tracks AI capabilities (MMLU, GSM8K, 68 metrics), robot installations, GPU economics. Performs cost-capability analysis, tipping point detection, S-curve adoption forecasting using Seba methodology. Use for AI performance trends, robot adoption, automation economics, AI benchmarks, GPU costs, or questions like "when will AI reach human-level?", "robot trends", "MMLU accuracy", "automation tipping points". Trigger keywords: artificial labour, AI, ML, MMLU, GSM8K, robot, robotics, humanoid, GPU, automation, benchmark, tipping point, disruption, forecast, adoption, cost parity.
---

# Artificial Labour Analysis

Analyze AI, robotics, and GPU trends using cost-capability disruption framework.

## Table of Contents
- [Available Datasets](#available-datasets)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Data Categories](#data-categories)
- [Analysis Types](#analysis-types)
- [Common Use Cases](#common-use-cases)
- [Scenarios](#scenarios)
- [Output Formats](#output-formats)
- [Taxonomy and Dataset Mapping](#taxonomy-and-dataset-mapping)
- [Tips](#tips)

## Available Datasets

**CRITICAL FOR PLANNING:** 68 AI benchmarks + 25 robot/GPU datasets available in `AL_JSON.json`:

### Artificial Intelligence (68 datasets - All Global)
- **Language Understanding:** `Artificial_Intelligence_MMLU_Accuracy` (33% → 92.3%, key benchmark)
- **Math Reasoning:** `Artificial_Intelligence_GSM8K_Accuracy` (89% → 97.72%)
- **Code Generation:** `Artificial_Intelligence_HumanEval_Accuracy`
- **Expert Q&A:** `Artificial_Intelligence_GPQA_Diamond_Accuracy`
- **Vision:** `Artificial_Intelligence_ImageNet_Top5_Accuracy`
- **Multimodal:** `Artificial_Intelligence_MMMU_Accuracy`
- **Training Data:** `Artificial_Intelligence_Traning_Dataset_Size` (tokens, growing 3.7×/year)
- **Model Parameters:** `Artificial_Intelligence_Model_Parameters`
- **Training Compute:** `Artificial_Intelligence_Training_Compute`
- **Inference Cost:** `Artificial_Intelligence_Inference_Cost` (declining exponentially)
- **Training Cost:** `Artificial_Intelligence_Training_Cost`
- **Enterprise Adoption:** `Artificial_Intelligence_Enterprise_Adoption`
- **API Usage:** `Artificial_Intelligence_API_Usage`

### Industrial Robots (12 datasets - Regional + Global)
- **Annual Installations:** `Industrial_Robot_Annual_Installation_{Region}`
- **Operational Stock:** `Industrial_Robot_Operational_stock_{Region}`
- **By Industry:**
  - Automotive: `Industrial_Robot_Annual_Installation_(Automotive)`
  - Electronics: `Industrial_Robot_Annual_Installation_(Electrical_Electronics)`
  - Metal: `Industrial_Robot_Annual_Installation_(Metal_and_Machinery)`
  - Plastics: `Industrial_Robot_Annual_Installation_(Plastics_and_Chemical_Products)`
  - Food: `Industrial_Robot_Annual_Installation_(Food)`
  - Other: `Industrial_Robot_Annual_Installation_(Others)`

### Service Robots (6 datasets - Global)
- **Total Demand:** `Service_Robot_(Professional)_Annual_Installation` (Global)
- **By Sector:**
  - Agriculture: `Service_Robot_(Professional)_Annual_Installation_(Agriculture)`
  - Hospitality: `Service_Robot_(Professional)_Annual_Installation_(Hospitality)`
  - Logistics: `Service_Robot_(Professional)_Annual_Installation_(Logistics)`
  - Medical: `Service_Robot_(Professional)_Annual_Installation_(Medical)`
  - Other: `Service_Robot_(Professional)_Annual_Installation_(Others)`

### Humanoid Robots (1 dataset - Global)
- **Market Size:** `Humanoid_Robot_Market_Size` (Global)

### GPU (6 datasets - Global)
- **NVIDIA:**
  - V100: `GPU_NVIDIA_Tesla_V100_Price`
  - A100: `GPU_NVIDIA_A100_Tensor_Core_Price`
  - H100: `GPU_NVIDIA_H100_Tensor_Core_Price`
- **AMD:**
  - MI210: `GPU_AMD_MI210_Price`
  - MI250X: `GPU_AMD_MI250X_Price`
  - MI300X: `GPU_AMD_MI300X_Price`

### Dataset File Location
- `AL_JSON.json` - Single comprehensive file with all 93 datasets
- `artificial_labour_taxonomy_and_datasets.json` - Complete taxonomy mapping

### Regional Coverage
- **Global:** Most comprehensive (all AI benchmarks, GPUs, humanoids)
- **China:** Industrial robots (leading adoption)
- **USA:** Industrial robots (AI development leader)
- **Europe:** Industrial robots (strong service robotics)
- **Asia_Pacific:** Industrial robots (excl. China)
- **Rest_of_World:** Emerging markets

### Critical Notes for Planning
1. **AI Capability Thresholds:** Human-level = 85-95%, Superhuman = >95%
2. **Cost Parity Thresholds:** Approaching = 70-100%, Parity = 50-70%, Tipping = <50% AND capability ≥ human
3. **Adoption Milestones:** Early = 10%, Mainstream = 50%, Late = 80-90%
4. **Service-Level View:** ALWAYS analyze as $/task, $/inference, $/hour (not just hardware costs)
5. **Growth Rates:** 20-40% annual CAGR typical for AI capability metrics
6. **Data Quality:** Sparse data (2-3 points) for some metrics, annual for benchmarks, 1-2 year lag for robots

## Quick Start

**Prerequisites:**
```bash
pip install -r requirements.txt
```

**Basic data query:**
```python
python3 scripts/data_loader.py
```

**Trend analysis:**
```python
from scripts.analyzer import ALAnalyzer

analyzer = ALAnalyzer()

# Get MMLU accuracy stats
stats = analyzer.summary_statistics(
    'Artificial Intelligence',
    'Artificial_Intelligence_MMLU_Accuracy'
)
print(f"Current MMLU: {stats['latest_value']}%")
print(f"CAGR: {stats['cagr']*100:.1f}%")
```

**Disruption analysis:**
```python
from scripts.disruptor_analysis import DisruptorAnalysis

analysis = DisruptorAnalysis()

# Forecast adoption milestones
milestones = analysis.forecast_adoption_milestones(
    'Industrial Robot',
    'Industrial_Robot_Annual_Installation'
)
print(f"Milestones: {milestones['milestone_years']}")
```

## Core Concepts

### Service-Level View
Always analyze in terms of service delivered, not just hardware:
- AI: **$/inference**, **$/task**, **$/automation-hour**
- Robots: **$/task**, **$/unit-output**, **$/hour**
- GPUs: **$/TFLOPS**, **$/inference**

### Disruption Framework (Tony Seba)
```
Cost + Capability → Tipping Point → S-Curve Adoption → Impacts
```

**Key stages:**
1. **Cost Parity:** Disruptor cost ≈ Incumbent cost
2. **Tipping Point:** Disruptor is cheaper AND better (50-70% cost, 2× capability)
3. **Adoption:** S-curve growth (10% → 50% → 80%)

### Entity Types
- **Disruptor:** AI models, robots (exponential improvement)
- **Incumbent:** Human labor for specific tasks
- **Enabler:** GPUs, cloud compute, training data
- **Chimera:** Human-AI hybrid systems

## Data Categories

### 1. Artificial Intelligence (68 datasets)
**Performance benchmarks:**
- MMLU (multitask understanding): 33% (2019) → 92.3% (2024)
- GSM8K (math reasoning): 89% (2022) → 97.72% (2024)
- HumanEval (code generation)
- GPQA Diamond (expert Q&A)

**Scale metrics:**
- Training dataset size (tokens): Growing 3.7× per year
- Model parameters
- Inference costs (declining exponentially)

**Adoption metrics:**
- Enterprise adoption rates
- API usage
- Market sizing

### 2. Industrial Robot (12 datasets)
- Annual installations (total + by industry)
- Operational stock
- Industries: Automotive, Electronics, Metal, Plastics, Food, Other

### 3. Service Robot (6 datasets)
- Professional service robots
- Sectors: Agriculture, Hospitality, Logistics, Medical, Other

### 4. Humanoid Robot (1 dataset)
- Market size projections

### 5. GPU (6 datasets)
- NVIDIA: V100, A100, H100
- AMD: MI210, MI250X, MI300X
- Pricing and performance trends

## Analysis Types

### 1. Trend Analysis
Calculate growth rates, fit trend lines, extrapolate:

```python
# CAGR calculation
cagr = analyzer.calculate_cagr(
    'Artificial Intelligence',
    'Artificial_Intelligence_Traning_Dataset_Size'
)

# Extrapolate to future year
future_val = analyzer.extrapolate(
    'Artificial Intelligence',
    'Artificial_Intelligence_MMLU_Accuracy',
    target_year=2026,
    method='cagr'
)
```

### 2. Capability Trajectory
Track when AI reaches human-level performance:

```python
capability = analysis.analyze_capability_trajectory(
    'Artificial Intelligence',
    'Artificial_Intelligence_MMLU_Accuracy',
    benchmark_value=90.0  # Human expert level
)
print(f"Benchmark reached: {capability['benchmark_year']}")
```

### 3. Disruption Timing
Detect cost parity and tipping points:

```python
timeline = analysis.create_disruption_timeline(
    disruptor=('Artificial Intelligence', 'AI_Cost_Metric'),
    incumbent=('Human Labour', 'Labour_Cost_Metric'),
    region='Global',
    scenarios=['Fast', 'Base', 'Slow']
)
```

### 4. Adoption Forecasting
Project S-curve adoption with milestones (10%, 50%, 80%):

```python
milestones = analysis.forecast_adoption_milestones(
    'Industrial Robot',
    'Industrial_Robot_Annual_Installation',
    milestones=[0.1, 0.5, 0.8],
    end_year=2030
)
```

### 5. Comparative Analysis
Compare datasets across time, regions, or technologies:

```python
comparison = analyzer.compare_datasets(
    dataset1=('Industrial Robot', 'Industrial_Robot_Annual_Installation_(Automotive)'),
    dataset2=('Industrial Robot', 'Industrial_Robot_Annual_Installation_(Electronics)'),
    region='Global'
)
```

## Common Use Cases

### "When will AI reach human-level performance on X?"
1. Query relevant benchmark (MMLU, GSM8K, HumanEval)
2. Get current value and growth rate (CAGR)
3. Project to human-level threshold (typically 85-95%)
4. Apply scenario adjustments (Fast/Base/Slow)

**Example:** MMLU reached 90% (human expert) in 2024

### "What's the AI capability improvement trend?"
1. Load benchmark time series
2. Calculate CAGR and fit exponential trend
3. Project forward with 3 scenarios
4. Identify inflection points

**Typical:** 20-40% annual CAGR on capability metrics

### "Forecast robot adoption in manufacturing"
1. Load industrial robot installation data
2. Segment by industry (automotive, electronics, etc.)
3. Calculate historical CAGR
4. Apply S-curve model post-tipping
5. Project to 10%/50%/80% milestones

### "GPU cost trajectory"
1. Load GPU pricing data
2. Calculate cost/performance decline rate
3. Extrapolate forward (typically 30-50% annual decline)
4. Link to AI inference cost

### "When does automation reach tipping point?"
1. Calculate service costs: $/task for robot vs human
2. Track cost ratio over time
3. Identify when ratio < 0.7 (tipping zone)
4. Model S-curve adoption from tipping point

## Scenarios

Always consider 3 scenarios:

**Fast / Tech-First:**
- Strong capability growth (40-50% CAGR)
- Rapid cost decline (40-50% CAGR)
- Supportive policy, fast infrastructure
- Adoption: 10% by 2026, 50% by 2030, 80% by 2033

**Base / Central:**
- Moderate growth (30-40% CAGR)
- Standard cost decline (30-40% CAGR)
- Mixed policy, gradual infrastructure
- Adoption: 10% by 2027, 50% by 2032, 80% by 2037

**Slow / Friction-Heavy:**
- Conservative growth (20-30% CAGR)
- Slower cost decline (20-30% CAGR)
- Regulatory drag, infrastructure delays
- Adoption: 10% by 2029, 50% by 2033, 80% by 2035

## Output Formats

**Summary statistics:**
```json
{
  "dataset": "Artificial_Intelligence_MMLU_Accuracy",
  "latest_value": 92.3,
  "cagr": 0.23,
  "total_growth": 179.7,
  "trend_r_squared": 0.98
}
```

**Disruption timeline:**
```json
{
  "disruptor": "AI_Model",
  "scenarios": {
    "Base": {
      "cost_parity_year": 2025,
      "tipping_point": 2027,
      "adoption_milestones": {
        "10%": 2028,
        "50%": 2032,
        "80%": 2037
      }
    }
  }
}
```

## Taxonomy and Dataset Mapping

### Market Definition
- **Market:** `Artificial_Labour` (AI and robotics disrupting human labor)

### Disruptor Technologies

**Artificial Intelligence**
- Entity Type: `disruptor`
- Subproducts: `AI_Language_Models`, `AI_Code_Generation`, `AI_Reasoning`, `AI_Vision`, `AI_Multimodal`
- Capability Metrics (Global):
  - Language Understanding: `Artificial_Intelligence_MMLU_Accuracy`
  - Math Reasoning: `Artificial_Intelligence_GSM8K_Accuracy`
  - Code Generation: `Artificial_Intelligence_HumanEval_Accuracy`
  - Expert Reasoning: `Artificial_Intelligence_GPQA_Diamond_Accuracy`
  - Vision: `Artificial_Intelligence_ImageNet_Top5_Accuracy`
  - Multimodal: `Artificial_Intelligence_MMMU_Accuracy`
- Cost Metrics (Global):
  - Inference: `Artificial_Intelligence_Inference_Cost`
  - Training: `Artificial_Intelligence_Training_Cost`
- Scale Metrics (Global):
  - Training Data: `Artificial_Intelligence_Traning_Dataset_Size`
  - Model Parameters: `Artificial_Intelligence_Model_Parameters`
  - Training Compute: `Artificial_Intelligence_Training_Compute`
- Adoption (Global):
  - Enterprise: `Artificial_Intelligence_Enterprise_Adoption`
  - API Usage: `Artificial_Intelligence_API_Usage`

**Industrial Robots**
- Entity Type: `disruptor`
- Demand: `Industrial_Robot_Annual_Installation` (by region)
- Installed Base: `Industrial_Robot_Operational_stock` (by region)
- Demand by Sector:
  - Automotive: `Industrial_Robot_Annual_Installation_(Automotive)`
  - Electronics: `Industrial_Robot_Annual_Installation_(Electrical_Electronics)`
  - Metal: `Industrial_Robot_Annual_Installation_(Metal_and_Machinery)`
  - Plastics: `Industrial_Robot_Annual_Installation_(Plastics_and_Chemical_Products)`
  - Food: `Industrial_Robot_Annual_Installation_(Food)`
  - Other: `Industrial_Robot_Annual_Installation_(Others)`

**Service Robots (Professional)**
- Entity Type: `disruptor`
- Demand: `Service_Robot_(Professional)_Annual_Installation` (Global)
- Demand by Sector:
  - Agriculture: `Service_Robot_(Professional)_Annual_Installation_(Agriculture)`
  - Hospitality: `Service_Robot_(Professional)_Annual_Installation_(Hospitality)`
  - Logistics: `Service_Robot_(Professional)_Annual_Installation_(Logistics)`
  - Medical: `Service_Robot_(Professional)_Annual_Installation_(Medical)`
  - Other: `Service_Robot_(Professional)_Annual_Installation_(Others)`

**Humanoid Robots**
- Entity Type: `disruptor`
- Market Size: `Humanoid_Robot_Market_Size` (Global)

### Enabling Infrastructure

**GPU (Graphics Processing Units)**
- Entity Type: `enabler`
- Cost Datasets:
  - NVIDIA V100: `GPU_NVIDIA_Tesla_V100_Price`
  - NVIDIA A100: `GPU_NVIDIA_A100_Tensor_Core_Price`
  - NVIDIA H100: `GPU_NVIDIA_H100_Tensor_Core_Price`
  - AMD MI210: `GPU_AMD_MI210_Price`
  - AMD MI250X: `GPU_AMD_MI250X_Price`
  - AMD MI300X: `GPU_AMD_MI300X_Price`

### Incumbent Technology

**Human Labour**
- Entity Type: `incumbent`
- Service Unit: USD per hour or USD per task
- Typical Cost Ranges (Global):
  - Data Entry: $15-30/hour
  - Customer Service: $15-35/hour
  - Junior Coding: $40-80/hour
  - Senior Coding: $80-150/hour
  - Analysis: $50-100/hour
  - Assembly/Manufacturing: $20-40/hour
  - Warehouse Picking: $15-25/hour
  - Inspection/QA: $20-35/hour

### Converged Disruptor Products

**AI-Powered Industrial Automation**
- Components: Artificial_Intelligence + Industrial_Robot
- Entity Type: `converged_disruptor`
- Capabilities: Adaptive manufacturing, visual inspection + reasoning, predictive maintenance, real-time optimization

**Autonomous Service Robots**
- Components: Artificial_Intelligence + Service_Robot
- Entity Type: `converged_disruptor`
- Capabilities: Navigation in dynamic environments, natural language interaction, task learning, human-robot collaboration

**General Purpose Humanoids**
- Components: Artificial_Intelligence + Humanoid_Robot
- Entity Type: `converged_disruptor`
- Capabilities: Multi-task capability, human environment operation, natural interaction, continuous learning

**AI as a Service**
- Components: Artificial_Intelligence + GPU + Cloud_Infrastructure
- Entity Type: `converged_disruptor`
- Capabilities: On-demand AI compute, zero marginal cost scaling, continuous improvement, API-accessible intelligence

### Available Regions
- **Global:** Worldwide aggregate (most AI benchmarks)
- **China:** Leading in industrial robot adoption
- **USA:** Leading in AI development
- **Europe:** Strong in service robotics
- **Asia_Pacific:** Asia-Pacific region excluding China
- **Rest_of_World:** Emerging markets

### Available Dataset Files
- `AL_JSON.json` - Comprehensive artificial labour data including AI benchmarks, robot installations, GPU costs, and adoption metrics
- `artificial_labour_taxonomy_and_datasets.json` - Taxonomy mapping (this section)

### Service Cost Metrics
- **AI:** USD per inference (primary), USD per task (secondary)
- **Industrial Robot:** USD per task (primary), USD per unit output (secondary)
- **Service Robot:** USD per task (primary), USD per delivery/pick (secondary)
- **Humanoid Robot:** USD per hour (primary)

### Tipping Point Thresholds
- **AI Capability:** Human-level = 85-95% on benchmarks, Superhuman = >95%
- **Cost Parity:** Approaching = 70-100% of incumbent, Parity = 50-70%, Tipping = <50% AND capability ≥ human-level
- **Adoption Milestones:** Early = 10%, Mainstream = 50%, Late = 80-90%

## Reference Documentation

- [references/data-schema.md](references/data-schema.md) - Complete AL_JSON.json structure and query patterns
- [references/metrics-guide.md](references/metrics-guide.md) - AI benchmarks, robot metrics, GPU economics explained
- [references/seba-framework.md](references/seba-framework.md) - Detailed disruption framework for artificial labour

## Tips

1. **Check metadata first:** Use `get_metadata()` to understand units and sources
2. **Verify regions:** Use `get_regions()` - not all datasets have all regions
3. **Handle sparse data:** Some metrics have only 2-3 data points
4. **Use log scale:** AI metrics often span orders of magnitude
5. **Compare apples-to-apples:** Convert to service costs ($/task) before comparing
6. **Consider convergence:** AI + Robotics > sum of parts
7. **Think scenarios:** Always analyze Fast/Base/Slow cases
8. **Service-level view:** Never just hardware costs, always $/service

## Data Quality Notes

- **Coverage varies:** AI benchmarks annual, robots 1-2 year lag, GPUs sparse
- **Projections included:** Some datasets extend beyond 2024 (forecasts)
- **Source diversity:** Academic (Stanford), industry (Epoch AI), financial (ARK)
- **Regional gaps:** Many datasets Global-only
- **Units matter:** Always check metadata units before analysis
