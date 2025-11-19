#!/bin/bash
# Energy Forecasting Runner Script
# Wrapper for forecast.py with validation and error handling

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to display usage and examples
show_help() {
    cat << EOF
${BLUE}Energy Forecasting - Solar-Wind-Battery (SWB) Systems${NC}

${GREEN}Usage:${NC}
    ./run_forecast.sh --region <REGION> [OPTIONS]

${GREEN}Required:${NC}
    --region         China | USA | Europe | Rest_of_World | Global

${GREEN}Options:${NC}
    --end-year       Final forecast year (default: 2035)
    --battery-duration  Battery duration: 2, 4, or 8 hours (default: 4)
    --scenario       Scenario: baseline | accelerated | delayed (default: baseline)
    --output         Output format: csv | json | both (default: csv)
    -h, --help       Show this help message

${GREEN}Scenarios:${NC}
    ${YELLOW}baseline${NC}     - Current policy trajectories (Solar: 8%/yr, Wind: 5%/yr, Battery: 10%/yr)
    ${YELLOW}accelerated${NC}  - Faster transition with strong policy (Solar: 12%/yr, Wind: 8%/yr, Battery: 15%/yr)
    ${YELLOW}delayed${NC}      - Slower transition with incumbent advantages (Solar: 5%/yr, Wind: 3%/yr, Battery: 7%/yr)

${GREEN}Examples:${NC}
    # China baseline scenario (coal-first displacement)
    ./run_forecast.sh --region China --scenario baseline --output csv

    # USA accelerated transition (gas-first displacement)
    ./run_forecast.sh --region USA --end-year 2040 --scenario accelerated --output both

    # Europe delayed scenario with 8-hour battery
    ./run_forecast.sh --region Europe --battery-duration 8 --scenario delayed --output json

    # Global aggregation across all regions
    ./run_forecast.sh --region Global --scenario baseline --output json

${GREEN}Output:${NC}
    Files are saved to: ${YELLOW}output/{Region}_{EndYear}_{Scenario}.{format}${NC}

${GREEN}Reference:${NC}
    Detailed documentation: ${YELLOW}SKILL.md${NC}
    Parameters reference: ${YELLOW}reference/parameters-reference.md${NC}
    Output formats: ${YELLOW}reference/output-formats-reference.md${NC}

EOF
}

# Function to check dependencies
check_dependencies() {
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 is not installed or not in PATH${NC}"
        echo "Please install Python 3.7 or higher"
        exit 1
    fi

    # Check Python version (requires 3.7+)
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.7"

    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        echo -e "${RED}Error: Python version $python_version is too old${NC}"
        echo "Required: Python 3.7 or higher"
        exit 1
    fi

    # Check if required packages are installed
    if ! python3 -c "import numpy, pandas, scipy" 2>/dev/null; then
        echo -e "${YELLOW}Warning: Some required packages may be missing${NC}"
        echo "Run: pip install -r requirements.txt"
        echo ""
    fi
}

# Function to validate parameters
validate_parameters() {
    local has_region=false
    local i=1

    # Check if any arguments were provided
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: No arguments provided${NC}"
        echo "Use --help for usage information"
        exit 1
    fi

    # Check for help flag
    for arg in "$@"; do
        if [ "$arg" == "-h" ] || [ "$arg" == "--help" ]; then
            show_help
            exit 0
        fi
        if [ "$arg" == "--region" ]; then
            has_region=true
        fi
    done

    # Validate that region is provided
    if [ "$has_region" = false ]; then
        echo -e "${RED}Error: --region parameter is required${NC}"
        echo "Valid regions: China, USA, Europe, Rest_of_World, Global"
        echo ""
        echo "Use --help for more information"
        exit 1
    fi
}

# Function to run the forecast
run_forecast() {
    echo -e "${BLUE}=== Energy Forecasting (SWB) ===${NC}"
    echo ""

    # Show what we're running
    echo -e "${GREEN}Running forecast with parameters:${NC}"
    echo "  $@"
    echo ""

    # Change to script directory and run forecast
    cd "$SCRIPT_DIR"

    if python3 scripts/forecast.py "$@"; then
        echo ""
        echo -e "${GREEN}✓ Forecast completed successfully!${NC}"
        echo ""

        # Try to show output file location
        for arg in "$@"; do
            if [[ "$arg" =~ ^(China|USA|Europe|Rest_of_World|Global)$ ]]; then
                region="$arg"
            fi
        done

        if [ -n "$region" ]; then
            echo -e "${GREEN}Output files:${NC}"
            # List recent output files for this region
            if ls output/${region}_* 2>/dev/null | head -5; then
                echo ""
            fi
        fi

        return 0
    else
        echo ""
        echo -e "${RED}✗ Forecast failed${NC}"
        echo "Check error messages above for details"
        return 1
    fi
}

# Main execution
main() {
    # Check dependencies first
    check_dependencies

    # Validate parameters
    validate_parameters "$@"

    # Run the forecast
    run_forecast "$@"
}

# Run main with all arguments
main "$@"
