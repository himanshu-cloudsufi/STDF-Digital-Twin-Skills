#!/bin/bash

# Datacenter UPS Battery Transition Forecast Script

SKILL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SKILL_DIR"

# Default parameters
END_YEAR=${END_YEAR:-2040}
REGION=${REGION:-Global}
OUTPUT_FORMAT=${OUTPUT_FORMAT:-csv}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --end-year)
            END_YEAR="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --analyze-tco)
            ANALYZE_TCO=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

mkdir -p output

echo "Running Datacenter UPS Battery Transition Forecast..."
echo "  Region: $REGION"
echo "  End Year: $END_YEAR"
echo "  Output Format: $OUTPUT_FORMAT"

python3 scripts/forecast.py \
    --config config.json \
    --region "$REGION" \
    --end-year "$END_YEAR" \
    --output-format "$OUTPUT_FORMAT"

if [ $? -eq 0 ]; then
    echo "✓ Forecast completed successfully"
    echo "  Output saved to: output/"
else
    echo "✗ Forecast failed"
    exit 1
fi