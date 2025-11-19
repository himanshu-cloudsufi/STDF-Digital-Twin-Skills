"""
Commercial Vehicle Demand Forecasting Skill

Forecasts commercial vehicle demand (LCV, MCV, HCV) with EV disruption analysis,
NGV chimera modeling, segment-level tipping point detection, and logistic adoption curves.

Usage:
    python3 scripts/forecast.py --region China --segment LCV --end-year 2040 --output csv
    python3 scripts/forecast.py --region USA --all-segments --track-fleet
"""

__version__ = "1.0.0"
__author__ = "CloudSufi Analytics"
__skill_name__ = "commercial-vehicle-demand"

from pathlib import Path

# Skill metadata
SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
SCRIPTS_DIR = SKILL_DIR / "scripts"
OUTPUT_DIR = SKILL_DIR / "output"
REFERENCE_DIR = SKILL_DIR / "reference"
EVALUATIONS_DIR = SKILL_DIR / "evaluations"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)
