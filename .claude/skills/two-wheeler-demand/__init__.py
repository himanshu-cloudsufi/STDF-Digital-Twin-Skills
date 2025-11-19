"""
Two-Wheeler Demand Forecasting Skill

Forecasts two-wheeler demand with EV disruption analysis, tipping point detection,
and logistic adoption curves.

Usage:
    python3 scripts/forecast.py --region China --end-year 2040 --output csv
"""

__version__ = "1.0.0"
__author__ = "CloudSufi Analytics"
__skill_name__ = "two-wheeler-demand"

from pathlib import Path

# Skill metadata
SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
SCRIPTS_DIR = SKILL_DIR / "scripts"
OUTPUT_DIR = SKILL_DIR / "output"
REFERENCE_DIR = SKILL_DIR / "reference"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)
