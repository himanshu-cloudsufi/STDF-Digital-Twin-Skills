#!/bin/bash

# Light Vehicle Demand Forecasting - Shell Wrapper
# Usage: ./run_forecast.sh <vehicle_type> <region> <end_year> [output_format]

set -e

# Default values
VEHICLE_TYPE=${1:-"two_wheeler"}
REGION=${2:-"China"}
END_YEAR=${3:-2030}
OUTPUT_FORMAT=${4:-"csv"}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validate vehicle type
if [[ "$VEHICLE_TYPE" != "two_wheeler" ]] && [[ "$VEHICLE_TYPE" != "three_wheeler" ]]; then
    echo "Error: Vehicle type must be 'two_wheeler' or 'three_wheeler'"
    echo "Usage: $0 <vehicle_type> <region> <end_year> [output_format]"
    exit 1
fi

echo "========================================"
echo "Light Vehicle Demand Forecasting"
echo "========================================"
echo "Vehicle Type: $VEHICLE_TYPE"
echo "Region: $REGION"
echo "End Year: $END_YEAR"
echo "Output Format: $OUTPUT_FORMAT"
echo "========================================"
echo ""

# Run forecast
python3 "$SCRIPT_DIR/scripts/forecast.py" \
    --vehicle-type "$VEHICLE_TYPE" \
    --region "$REGION" \
    --end-year "$END_YEAR" \
    --output "$OUTPUT_FORMAT"

echo ""
echo "✓ Forecast complete!"
