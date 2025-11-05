#!/bin/bash

# Product Demand Forecasting - Wrapper Script
# This script provides a convenient interface to the product forecasting module

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to script directory
cd "$SCRIPT_DIR"

# Run the Python forecasting script
python3 scripts/product_forecast.py "$@"
