# Artificial Labour Metrics Guide

Key metrics and benchmarks explained.

## AI Performance Benchmarks

### MMLU (Massive Multitask Language Understanding)
- **What it measures:** AI model performance across 57 subjects (humanities, STEM, social sciences)
- **Units:** Percentage accuracy (0-100%)
- **Human baseline:** ~90% (expert-level performance)
- **Significance:** Premier benchmark for general AI capability
- **Recent trend:** 33% (2019) → 92.3% (2024)
- **Interpretation:** >85% indicates near-human multitask reasoning

### GSM8K (Grade School Math 8K)
- **What it measures:** Math word problem solving ability
- **Units:** Percentage accuracy (0-100%)
- **Human baseline:** ~100% (grade school level)
- **Significance:** Tests multi-step reasoning and arithmetic
- **Recent trend:** 89% (2022) → 97.72% (2024)
- **Interpretation:** >95% indicates superhuman grade-school math

### HumanEval
- **What it measures:** Code generation accuracy
- **Units:** Percentage of correct solutions
- **Significance:** Programming capability benchmark
- **Use case:** Software automation potential

### GPQA Diamond
- **What it measures:** Expert-level question answering
- **Significance:** Tests PhD-level domain knowledge
- **Interpretation:** High scores indicate expert-level AI capability

## AI Training & Scale Metrics

### Training Dataset Size
- **Units:** Tokens (words/subwords)
- **Range:** 10^5 (early) to 10^13 (current)
- **Growth rate:** ~3.7x per year in language modeling
- **Significance:** Larger datasets → better generalization
- **Current frontier:** Tens of trillions of tokens

### Model Parameters
- **Units:** Count of trainable parameters
- **Range:** Millions to trillions
- **Significance:** Correlates with capability (with diminishing returns)

### Inference Cost
- **Units:** USD per query/inference
- **Trend:** Exponentially declining
- **Significance:** Economic viability for mass adoption

## Robot Metrics

### Industrial Robot Annual Installation
- **Units:** Number of units installed per year
- **Segments:** Automotive, Electronics, Metal, Plastics, Food, Other
- **Significance:** Rate of automation in manufacturing
- **Interpretation:** Growth rate indicates automation adoption speed

### Operational Stock
- **Units:** Total active robots in operation
- **Significance:** Cumulative automation deployment
- **Relationship:** Stock = Σ(Installations) - Retirements

### Service Robot Installations
- **Sectors:** Agriculture, Hospitality, Logistics, Medical, Other
- **Significance:** Automation beyond manufacturing
- **Trend:** Accelerating in logistics and medical sectors

### Humanoid Robot Market Size
- **Units:** USD (market value)
- **Significance:** Emerging segment with general-purpose potential
- **Use cases:** Warehouses, retail, elderly care

## GPU Economics

### GPU Pricing
- **Models tracked:** NVIDIA (V100, A100, H100), AMD (MI210, MI250X, MI300X)
- **Units:** USD per unit
- **Trend:** Declining on per-performance basis
- **Significance:** Enabler cost for AI compute

### Performance Metrics
- **FLOPS:** Floating-point operations per second
- **Memory:** VRAM capacity (GB)
- **Efficiency:** Performance per watt, per dollar

## Entity Types in Disruption Framework

### Disruptor
- **Examples:** AI models, industrial robots, humanoid robots
- **Characteristic:** Exponential improvement in cost-performance
- **Role:** Displaces incumbent labor/systems

### Incumbent
- **Examples:** Human labor (for specific tasks)
- **Characteristic:** Linear or flat cost-performance
- **Role:** Being displaced

### Enabler
- **Examples:** GPUs, cloud compute, training data
- **Characteristic:** Enables disruptor scaling
- **Role:** Infrastructure for disruption

### Chimera/Hybrid
- **Examples:** Human-AI collaborative systems
- **Characteristic:** Combines incumbent + disruptor
- **Role:** Transitional form

## Service-Level Metrics (Seba Framework)

Always convert hardware metrics to service metrics:

### $/Inference
- Cost per AI query/task
- **Calculation:** (GPU cost + energy + overhead) / throughput
- **Trend:** Exponentially declining

### $/Task
- Cost per automated task (e.g., picking, sorting, inspection)
- **Comparison:** vs human labor cost for same task
- **Tipping point:** When robot $/task < human $/task

### $/Automation-Hour
- Cost per hour of automated operation
- **Includes:** CAPEX amortization, energy, maintenance
- **Comparison:** vs human $/hour (wage + benefits)

## Interpretation Guidelines

### Capability Thresholds
- **<50%:** Below human performance
- **50-85%:** Approaching human performance
- **85-95%:** Human-level performance
- **>95%:** Superhuman performance

### Growth Rates (CAGR)
- **<10%:** Incremental improvement
- **10-30%:** Rapid improvement
- **>30%:** Exponential disruption territory
- **>100%:** Hypergrowth (early stage, unstable)

### Cost Parity Indicators
- **Cost ratio > 2:** Disruptor much more expensive
- **Cost ratio 1-2:** Approaching parity
- **Cost ratio 0.5-1:** At or near parity
- **Cost ratio < 0.5:** Disruptor significantly cheaper (tipping point zone)

## Data Sources

- **Epoch AI:** AI training data, model parameters, benchmarks
- **Stanford AI Index:** Comprehensive AI metrics
- **IFR (International Federation of Robotics):** Robot installation data
- **ARK Invest:** Market projections and cost curves
- **Goldman Sachs:** Financial forecasts
- **Academic papers:** Benchmark results (MMLU, GSM8K, etc.)
