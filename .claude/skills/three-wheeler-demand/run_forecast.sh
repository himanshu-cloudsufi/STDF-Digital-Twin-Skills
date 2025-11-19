#!/bin/bash
# Three-Wheeler Demand Forecasting Runner Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default parameters
REGION="${1:-China}"
END_YEAR="${2:-2040}"
OUTPUT_FORMAT="${3:-csv}"

# Run the forecast
python3 "$SCRIPT_DIR/scripts/forecast.py" \
    --region "$REGION" \
    --end-year "$END_YEAR" \
    --output "$OUTPUT_FORMAT" \
    --output-dir "$SCRIPT_DIR/output"

# Make script executable
# chmod +x run_forecast.sh
