#!/bin/bash
# Wrapper script to run energy forecasts with the correct Python version

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR" && python3 scripts/forecast.py "$@"
