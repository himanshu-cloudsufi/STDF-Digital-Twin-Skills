# Skill Test Queries

This directory contains comprehensive test queries for validating the Claude skills created for commodity and energy transition analysis.

## 📁 Structure

- `copper-demand-test-queries.md` - Test queries for copper demand forecasting skill
- `datacenter-ups-test-queries.md` - Test queries for datacenter UPS battery transition skill
- `lead-demand-test-queries.md` - Test queries for lead demand forecasting skill
- `swb-transition-test-queries.md` - Test queries for Solar-Wind-Battery energy transition skill

## 🎯 Purpose

These test queries serve multiple purposes:

1. **Validation**: Verify that each skill functions correctly and produces expected outputs
2. **Documentation**: Provide examples of how to use each skill effectively
3. **Testing**: Enable systematic testing of skill capabilities
4. **Training**: Help users understand what each skill can do

## 📋 Test Query Format

Each test query file contains:
- **10 Core Queries**: Primary test cases covering main functionality
- **Additional Test Cases**: Edge cases, error handling, and performance tests
- **Expected Outputs**: Detailed description of what the skill should return
- **Validation Criteria**: Specific metrics and tolerances to check

## 🚀 How to Use

### Running Individual Tests

To test a specific skill, you can use the queries as prompts:

```bash
# Example: Test copper demand forecast
"Forecast global copper demand through 2045 using the baseline scenario"

# Example: Test datacenter UPS TCO analysis
"Compare the Total Cost of Ownership between VRLA and Lithium-ion batteries for datacenter UPS systems"
```

### Systematic Testing

For comprehensive testing:
1. Run each query sequentially
2. Compare outputs with expected results
3. Document any discrepancies
4. Validate numerical accuracy and reconciliation

## ✅ Coverage Areas

### Functional Testing
- Basic forecasting operations
- Scenario analysis
- Regional calculations
- Technology transitions

### Validation Testing
- Data reconciliation
- Mass balance checks
- Non-negativity constraints
- Growth rate guards

### Edge Cases
- Extreme scenarios
- Missing data handling
- Invalid parameter combinations
- Boundary conditions

### Performance Testing
- Large time horizons (20+ years)
- Multiple regions simultaneously
- Complex scenario comparisons

## 📊 Skills Covered

### 1. Copper Demand (`copper-demand`)
- Hybrid bottom-up + top-down methodology
- EV and renewable energy impact
- Segment reconciliation
- Substitution risk analysis

### 2. Datacenter UPS (`datacenter-ups`)
- VRLA to Li-ion transition
- TCO-driven adoption
- S-curve modeling
- Regional variations

### 3. Lead Demand (`lead-demand`)
- Vehicle electrification impact
- Battery lifecycle modeling
- Industrial battery segments
- Fleet-based calculations

### 4. SWB Transition (`swb-transition`)
- Coal/gas displacement by renewables
- LCOE/SCOE cost analysis
- Battery storage sizing
- CO₂ emissions tracking

## 🔧 Maintenance

These test queries should be updated when:
- New features are added to skills
- Methodology changes are implemented
- New data sources become available
- Edge cases are discovered

## 📝 Notes

- All queries assume skills are properly installed and configured
- Expected outputs are based on the methodologies described in skill-instructions
- Actual results may vary based on input data and parameter settings
- Use these queries as a baseline and adapt for specific testing needs