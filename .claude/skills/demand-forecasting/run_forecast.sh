#!/bin/bash
# Wrapper script to run forecasts with the correct Python version

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run forecast with Python 3.12 (which has all dependencies installed)
cd "$SCRIPT_DIR" && python3.12 scripts/forecast.py "$@"
