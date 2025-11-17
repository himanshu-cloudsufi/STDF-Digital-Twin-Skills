#!/bin/bash

# Copper Demand Forecasting Skill Execution Script
# This script runs the copper demand forecast with specified parameters

# Set working directory to skill location
SKILL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SKILL_DIR"

# Default parameters
END_YEAR=${END_YEAR:-2035}
SCENARIO=${SCENARIO:-baseline}
OUTPUT_FORMAT=${OUTPUT_FORMAT:-csv}
VALIDATE=${VALIDATE:-false}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --end-year)
            END_YEAR="$2"
            shift 2
            ;;
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --validate)
            VALIDATE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output directory if it doesn't exist
mkdir -p output

# Run the forecast
echo "Running Copper Demand Forecast..."
echo "  End Year: $END_YEAR"
echo "  Scenario: $SCENARIO"
echo "  Output Format: $OUTPUT_FORMAT"
echo "  Validation: $VALIDATE"

# Execute Python script
python3 scripts/forecast.py \
    --config config.json \
    --end-year "$END_YEAR" \
    --scenario "$SCENARIO" \
    --output-format "$OUTPUT_FORMAT" \
    --validate "$VALIDATE"

# Check if execution was successful
if [ $? -eq 0 ]; then
    echo "✓ Forecast completed successfully"
    echo "  Output saved to: output/"

    # If validation was requested, show summary
    if [ "$VALIDATE" = true ]; then
        echo ""
        echo "Validation Summary:"
        python3 scripts/validate_results.py output/copper_demand_forecast.csv
    fi
else
    echo "✗ Forecast failed with error"
    exit 1
fi