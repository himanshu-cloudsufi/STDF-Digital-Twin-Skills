#!/bin/bash
# Wrapper script for disruption analysis
# Runs the Python disruption_impact.py script with provided arguments

cd "$(dirname "$0")"
python3.12 scripts/disruption_impact.py "$@"
