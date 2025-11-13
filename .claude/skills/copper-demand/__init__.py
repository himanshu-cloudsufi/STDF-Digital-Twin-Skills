"""
Copper Demand Forecasting Skill

Hybrid bottom-up + top-down methodology for forecasting refined copper demand.
Combines installed-base accounting for vehicles and generation capacity with
top-down allocation for construction, industrial, and electronics segments.
"""

__version__ = "1.0.0"
__author__ = "Claude Code"

from .scripts.forecast import CopperDemandForecast

__all__ = ['CopperDemandForecast']