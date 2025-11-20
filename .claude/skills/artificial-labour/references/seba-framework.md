# Seba Disruption Framework for Artificial Labour

Adapted framework for analyzing AI and robotics disruption.

## Core Principle

**Cost + Capability → Tipping Points → S-Curve Adoption → Value Chain Impacts**

Disruption is driven by technologies that become both cheaper AND better than incumbents.

## Service-Level Thinking

Never analyze just hardware costs. Always convert to service costs:

### For AI/ML
- **$/inference** - Cost per AI query or task
- **$/automation-hour** - Cost per hour of AI-powered work
- **$/task** - Cost to complete a specific task (translation, analysis, generation)

### For Robots
- **$/task** - Cost per picking, sorting, welding, or assembly operation
- **$/unit-output** - Cost per manufactured unit
- **$/automation-hour** - Hourly cost of robotic operation vs human labor

### Calculation
```
Service Cost = (CAPEX / lifetime_hours + OPEX_per_hour) / throughput_per_hour
```

## Market Segmentation

Segment by use case economics, not just industry:

### AI Segments
- **Hyperscale:** Massive compute, lowest $/inference (Google, Meta, OpenAI)
- **Enterprise:** Mid-scale, higher $/inference, privacy needs
- **Edge:** Low latency, constrained compute, highest $/inference

### Robot Segments
- **High-volume manufacturing:** Automotive, electronics (24/7 operation, high ROI)
- **Variable manufacturing:** Food, plastics (batch production, moderate ROI)
- **Service/Logistics:** Warehouses, delivery (dynamic environments, emerging ROI)
- **Professional services:** Medical, agriculture (high-mix, specialized tasks)

## Disruption Timing

### Phase 1: Cost Parity
**When:** Disruptor cost/service ≈ Incumbent cost/service

- AI: When $/inference for AI ≈ human hourly wage / tasks per hour
- Robots: When robot $/task ≈ human labor $/task

**Indicator:** Cost ratio = Disruptor_cost / Incumbent_cost ≈ 1.0

### Phase 2: Tipping Point
**When:** Disruptor becomes decisively better:
- Cost: ≤50-70% of incumbent cost, AND/OR
- Capability: 2-3× better on key dimensions (speed, accuracy, reliability, convenience)

**For AL specifically:**
- AI reaches human-level accuracy (>85% on benchmarks) AND
- $/inference is 10-50% of human labor cost for equivalent task

### Phase 3: S-Curve Adoption
Follows logistic curve after tipping point:
- **10% adoption:** Early adopters, ~2-5 years after tipping
- **50% adoption:** Mainstream, ~5-10 years after tipping
- **80-90% adoption:** Late majority, ~10-15 years after tipping

**Factors affecting steepness:**
- Asset turnover rate (faster for software/AI, slower for physical robots)
- CAPEX intensity (higher = slower adoption)
- Infrastructure readiness
- Workforce retraining needs

## Cost-Capability Trajectory Analysis

### For AI Capabilities
1. **Identify benchmark:** MMLU, GSM8K, HumanEval, etc.
2. **Track improvement rate:** Typically 20-50% CAGR on performance metrics
3. **Project to human-level:** When does metric reach 85-95%?
4. **Estimate cost trajectory:** $/inference declining 30-50% per year

**Example:** MMLU
- 2019: 33% accuracy
- 2024: 92.3% accuracy
- CAGR: ~23% annual improvement
- Human-level (90%): Achieved in 2024

### For Robot Economics
1. **Calculate current $/task:** CAPEX + OPEX / tasks per lifetime
2. **Track installation growth:** Proxy for $/task decline via scale
3. **Compare to human $/task:** Typical assembly worker: $20-40/hour ÷ 60-100 tasks/hour = $0.20-0.67/task
4. **Estimate parity:** When robot $/task crosses human $/task

## Scenarios

Always analyze 3 scenarios:

### Fast/Tech-First
- Strong capability improvement (benchmarks reach 95%+ by 2027)
- Rapid cost decline (40-50% CAGR)
- Supportive policy, fast infrastructure
- Adoption: 10% by 2026, 50% by 2030, 80% by 2033

### Base/Central
- Moderate improvement (benchmarks reach 95% by 2028-2029)
- Standard cost decline (30-40% CAGR)
- Mixed policy, gradual infrastructure
- Adoption: 10% by 2027, 50% by 2032, 80% by 2037

### Slow/Friction-Heavy
- Slower improvement (benchmarks reach 95% by 2030+)
- Conservative cost decline (20-30% CAGR)
- Regulatory drag, slow infrastructure
- Adoption: 10% by 2029, 50% by 2035, 80% by 2040+

## Convergence Effects

AL is amplified by convergence:

### AI + Robotics
- **Capability synergy:** Robots gain perception, reasoning, adaptability
- **Cost synergy:** Shared compute infrastructure, software reuse
- **New products:** Autonomous vehicles, humanoid robots, warehouse automation
- **Value:** Converged system > sum of parts

### AI + Cloud + Data
- **Capability:** Continuous learning, real-time optimization
- **Cost:** Zero marginal cost for software, massive scale economies
- **Products:** AI-as-a-Service, autonomous systems

### AI + Energy
- **Dependency:** AI compute requires massive electricity
- **Feedback:** Cheaper energy → cheaper AI → more AI demand → more energy demand
- **Impact:** Grid transformation, renewable acceleration

## Value Chain Impacts

### Growing Nodes
- **Semiconductors:** GPUs, AI accelerators, memory
- **Cloud infrastructure:** Datacenters, networking
- **Electricity:** Massive consumption growth (hyperscale DCs)
- **Software/ML platforms:** Training, inference, monitoring
- **Data services:** Collection, labeling, curation

### Shrinking Nodes
- **Human labor (specific tasks):** Data entry, translation, coding, analysis, inspection, assembly
- **Legacy IT:** On-premise servers, traditional software
- **Labor-intensive services:** Call centers, back-office, manual QA

## Commodity Impacts

### Rising Demand
- **Copper:** Electrification of everything (EVs, renewables, DCs)
- **Lithium/Cobalt:** Battery storage for energy + mobility
- **Rare earths:** Motors, electronics
- **Electricity:** Exponential growth from AI compute

### Falling Demand
- **Oil (specific use cases):** Transportation (via EVs + TaaS), some petrochemicals
- **Labor (as commodity):** Displacement in automatable tasks

## Application Guide

When analyzing an AL query:

1. **Define the service:** What task is being automated? What's the service unit?
2. **Identify incumbent cost:** Human labor cost per task or per hour
3. **Calculate disruptor cost:** AI/robot cost per task (CAPEX + OPEX / throughput)
4. **Assess capability gap:** Is disruptor at/near/beyond human-level?
5. **Estimate parity:** When does cost_disruptor ≈ cost_incumbent?
6. **Estimate tipping:** When is disruptor both cheaper AND better?
7. **Project adoption:** Use S-curve with segment-specific parameters
8. **Assess impacts:** Value chain winners/losers, commodity shifts, convergence effects

## Example: AI Reaches Human-Level Coding

**Service:** Software development ($/line of code or $/task)

**Current state (2024):**
- AI: HumanEval ~85% accuracy, $/inference declining
- Human: $50-150/hour, ~100-200 lines/day → ~$0.25-0.75/line
- Cost ratio: Varies by task complexity

**Parity window:** 2024-2026 (already at parity for simple tasks)

**Tipping window:** 2025-2027 (when AI is both cheaper AND faster/more reliable)

**Adoption S-curve:**
- 10%: 2026 (early adopters, GitHub Copilot users)
- 50%: 2030 (mainstream enterprise adoption)
- 80%: 2033 (late majority, regulatory-constrained sectors slower)

**Impacts:**
- Growing: AI platforms, code review tools, semiconductor demand
- Shrinking: Junior developer roles, legacy IDEs, offshore coding centers
- Commodities: Electricity ↑, office space ↓
