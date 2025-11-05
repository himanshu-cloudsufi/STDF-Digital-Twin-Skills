#!/usr/bin/env python3
"""
Test script to verify all imports from forecasting core library
"""

import sys
import os

# Add library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Forecasting Core Library Imports...")
print("=" * 60)

# Test core.utils
print("\n1. Testing core.utils...")
try:
    from core.utils import (
        rolling_median,
        calculate_cagr,
        theil_sen_slope,
        linear_extrapolation,
        log_cagr_forecast,
        clamp,
        clamp_array,
        find_intersection,
        validate_forecast_consistency
    )
    print("   ✓ All utils functions imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test core.cost_analyzer
print("\n2. Testing core.cost_analyzer...")
try:
    from core.cost_analyzer import CostAnalyzer
    print("   ✓ CostAnalyzer class imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test core.logistic_models
print("\n3. Testing core.logistic_models...")
try:
    from core.logistic_models import (
        logistic_function,
        fit_logistic_curve,
        forecast_logistic_share,
        linear_to_logistic_transition,
        forecast_chimera_hump
    )
    print("   ✓ All logistic model functions imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test core.data_loader
print("\n4. Testing core.data_loader...")
try:
    from core.data_loader import DataLoader
    print("   ✓ DataLoader class imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test core.validators
print("\n5. Testing core.validators...")
try:
    from core.validators import (
        validate_forecast_consistency,
        validate_non_negative,
        validate_monotonic_within_tolerance,
        validate_cagr_bounds,
        validate_smooth_transitions,
        validate_shares_sum_to_one,
        validate_data_availability,
        validate_forecast_result,
        run_comprehensive_validation
    )
    print("   ✓ All validator functions imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Quick functional test
print("\n6. Running functional tests...")
try:
    import numpy as np

    # Test rolling_median
    data = np.array([1, 5, 2, 8, 3])
    smoothed = rolling_median(data, window=3)
    assert len(smoothed) == len(data), "rolling_median length mismatch"
    print("   ✓ rolling_median works")

    # Test calculate_cagr
    values = np.array([100, 110, 121])
    years = np.array([2020, 2021, 2022])
    cagr = calculate_cagr(values, years)
    assert abs(cagr - 0.1) < 0.01, f"CAGR calculation error: {cagr}"
    print("   ✓ calculate_cagr works")

    # Test logistic_function
    t = np.array([2020, 2025, 2030])
    shares = logistic_function(t, L=1.0, k=0.4, t0=2025)
    assert len(shares) == len(t), "logistic_function length mismatch"
    assert 0 <= shares[0] <= 1, "logistic_function out of bounds"
    print("   ✓ logistic_function works")

    # Test CostAnalyzer instantiation
    analyzer = CostAnalyzer(smoothing_window=3)
    assert analyzer.smoothing_window == 3, "CostAnalyzer init failed"
    print("   ✓ CostAnalyzer instantiation works")

    # Test validation
    market = np.array([100, 110, 120])
    bev = np.array([10, 20, 30])
    phev = np.array([5, 10, 15])
    ice = np.array([85, 80, 75])
    is_valid, msg = validate_forecast_consistency(market, [bev, phev, ice])
    assert is_valid, f"Validation failed: {msg}"
    print("   ✓ validate_forecast_consistency works")

except Exception as e:
    print(f"   ✗ Functional test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED!")
print("=" * 60)
print("\nForecast Core Library is ready for use.")
