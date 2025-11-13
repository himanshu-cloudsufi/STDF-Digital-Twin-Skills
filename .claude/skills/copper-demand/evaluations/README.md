# Copper Demand Skill Evaluations

This directory contains evaluation scenarios for testing the copper-demand skill's effectiveness.

## Evaluation Suite

### Core Functionality
- **eval-1-basic-forecast.json** - Tests basic forecast generation with segment breakdown
- **eval-2-scenario-comparison.json** - Tests scenario differentiation (baseline vs accelerated)
- **eval-3-regional-analysis.json** - Tests regional breakdown support

### Domain-Specific
- **eval-4-ev-impact.json** - Tests EV impact analysis and copper intensity calculations
- **eval-5-substitution-risk.json** - Tests substitution scenario modeling

## Running Evaluations

These evaluations are designed to be run manually or with a custom evaluation framework.

### Manual Testing

For each evaluation:

1. Load the copper-demand skill
2. Execute the query specified in the evaluation file
3. Verify the expected behaviors listed
4. Check that success criteria are met

### Example

```bash
# For eval-1-basic-forecast.json
claude "Forecast global copper demand through 2045 using the baseline scenario. Show me the breakdown by major segments and confidence levels."

# Verify:
# - Total demand 2045 is between 28-32 million tonnes
# - EV share is 15-20%
# - Automotive share is 17-21%
# - Reconciliation error < 0.1%
```

## Success Criteria

Each evaluation includes quantitative success criteria that can be programmatically verified:

- **Range checks**: Values within expected ranges
- **Ratio checks**: Calculated ratios match expected values
- **Boolean checks**: Features work as expected (e.g., scenarios differ)

## Baseline Performance

Run these evaluations **without** the skill loaded to establish baseline Claude performance, then compare with skill-enabled performance.

Expected improvements with skill:
- Accurate copper intensity coefficients
- Proper scenario parameter application
- Regional data handling
- Correct reconciliation methodology
- Appropriate confidence tagging

## Adding New Evaluations

When adding scenarios:

1. Create a new JSON file following the existing format
2. Include clear expected behaviors
3. Define quantitative success criteria
4. Test both with and without the skill
5. Document any special setup requirements
