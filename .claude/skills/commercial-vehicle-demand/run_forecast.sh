#!/bin/bash
# Commercial Vehicle Demand Forecasting Runner Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default parameters
REGION="${1:-China}"
SEGMENT="${2:-all}"  # Options: LCV, MCV, HCV, or 'all'
END_YEAR="${3:-2040}"
OUTPUT_FORMAT="${4:-csv}"

# Build command
CMD="python3 $SCRIPT_DIR/scripts/forecast.py --region $REGION --end-year $END_YEAR --output $OUTPUT_FORMAT --output-dir $SCRIPT_DIR/output"

# Add segment parameter
if [ "$SEGMENT" = "all" ]; then
    CMD="$CMD --all-segments"
else
    CMD="$CMD --segment $SEGMENT"
fi

# Run the forecast
echo "Running Commercial Vehicle Demand Forecast..."
echo "Region: $REGION"
echo "Segment: $SEGMENT"
echo "End Year: $END_YEAR"
echo "Output Format: $OUTPUT_FORMAT"
echo ""

eval $CMD

# Usage examples:
# ./run_forecast.sh China all 2040 csv         # All segments, China
# ./run_forecast.sh USA LCV 2035 json          # LCV segment only, USA
# ./run_forecast.sh Europe MCV 2040 both       # MCV segment, Europe

# Make script executable:
# chmod +x run_forecast.sh
