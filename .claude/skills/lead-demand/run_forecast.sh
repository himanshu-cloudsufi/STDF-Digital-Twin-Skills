#!/bin/bash

# Lead Demand Forecasting Script

SKILL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SKILL_DIR"

# Default parameters
END_YEAR=${END_YEAR:-2030}
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

mkdir -p output

echo "Running Lead Demand Forecast..."
echo "  End Year: $END_YEAR"
echo "  Scenario: $SCENARIO"
echo "  Output Format: $OUTPUT_FORMAT"
echo "  Validation: $VALIDATE"

python3 scripts/forecast.py \
    --config config.json \
    --end-year "$END_YEAR" \
    --scenario "$SCENARIO" \
    --output-format "$OUTPUT_FORMAT" \
    --validate "$VALIDATE"

if [ $? -eq 0 ]; then
    echo "✓ Forecast completed successfully"
    echo "  Output saved to: output/"
else
    echo "✗ Forecast failed"
    exit 1
fi