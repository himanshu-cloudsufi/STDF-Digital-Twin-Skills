"""
NGV (Natural Gas Vehicle) Chimera Modeling

Models NGV as a transitional "chimera" technology that peaks and then declines
as EV adoption accelerates. Uses exponential decay with configurable half-life.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class NGVModel:
    """
    Models NGV demand as a declining chimera technology.

    Key behaviors:
    - Detects historical peak in NGV sales/share
    - Allows growth up to peak during historical period
    - Applies exponential decline after max(peak_year, tipping_point)
    - Targets near-zero share by 2040
    - Handles cases where NGV never had significant presence
    """

    def __init__(self, config: Dict):
        """
        Initialize NGV model with configuration.

        Args:
            config: Configuration dict with NGV parameters
        """
        self.half_life_years = config.get('half_life_years', 6.0)
        self.peak_detection_window = config.get('peak_detection_window', 5)
        self.target_share_2040 = config.get('target_share_2040', 0.0)
        self.min_significant_share = config.get('min_significant_share', 0.01)
        self.decline_start_mode = config.get('decline_start_mode', 'max_peak_or_tipping')

        logger.info(f"NGV Model initialized: half_life={self.half_life_years}yr, "
                   f"target_2040={self.target_share_2040}")

    def detect_peak(self,
                    historical_years: np.ndarray,
                    historical_ngv: np.ndarray,
                    historical_market: np.ndarray) -> Dict:
        """
        Detect peak in historical NGV data.

        Args:
            historical_years: Array of historical years
            historical_ngv: Array of historical NGV sales
            historical_market: Array of total market sales

        Returns:
            Dict with peak information:
                - peak_year: Year of peak NGV sales
                - peak_sales: Peak NGV sales value
                - peak_share: Peak NGV share of market
                - has_significant_presence: Boolean indicating if NGV is significant
        """
        if len(historical_ngv) == 0:
            return {
                'peak_year': None,
                'peak_sales': 0,
                'peak_share': 0,
                'has_significant_presence': False
            }

        # Calculate shares
        shares = np.divide(historical_ngv, historical_market,
                          where=historical_market > 0,
                          out=np.zeros_like(historical_ngv, dtype=float))

        # Check if NGV has significant presence
        max_share = np.max(shares) if len(shares) > 0 else 0
        has_significant = max_share >= self.min_significant_share

        if not has_significant:
            logger.info(f"NGV has negligible presence (max share: {max_share:.1%})")
            return {
                'peak_year': None,
                'peak_sales': 0,
                'peak_share': 0,
                'has_significant_presence': False
            }

        # Find peak year (use rolling average to smooth noise)
        if len(shares) >= self.peak_detection_window:
            window = self.peak_detection_window
            smoothed_shares = np.convolve(shares,
                                          np.ones(window)/window,
                                          mode='valid')
            # Adjust years to match smoothed array
            smooth_years = historical_years[window//2:len(smoothed_shares)+window//2]
            peak_idx = np.argmax(smoothed_shares)
            peak_year = smooth_years[peak_idx]
        else:
            peak_idx = np.argmax(shares)
            peak_year = historical_years[peak_idx]

        peak_sales = historical_ngv[peak_idx]
        peak_share = shares[peak_idx]

        logger.info(f"NGV peak detected: {peak_year} (share: {peak_share:.1%}, "
                   f"sales: {peak_sales:,.0f})")

        return {
            'peak_year': int(peak_year),
            'peak_sales': float(peak_sales),
            'peak_share': float(peak_share),
            'has_significant_presence': True
        }

    def forecast_ngv(self,
                     historical_years: np.ndarray,
                     historical_ngv: np.ndarray,
                     historical_market: np.ndarray,
                     forecast_years: np.ndarray,
                     forecast_market: np.ndarray,
                     tipping_point: Optional[float] = None,
                     peak_info: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """
        Forecast NGV demand with exponential decline.

        Args:
            historical_years: Historical years
            historical_ngv: Historical NGV sales
            historical_market: Historical total market
            forecast_years: Years to forecast
            forecast_market: Forecasted total market
            tipping_point: EV cost parity year (optional)
            peak_info: Pre-computed peak info (optional)

        Returns:
            Tuple of (forecast_ngv_sales, metadata_dict)
        """
        # Detect peak if not provided
        if peak_info is None:
            peak_info = self.detect_peak(historical_years,
                                        historical_ngv,
                                        historical_market)

        # If no significant NGV presence, return zeros
        if not peak_info['has_significant_presence']:
            forecast_ngv = np.zeros_like(forecast_years, dtype=float)
            metadata = {
                'model': 'zero',
                'reason': 'no_significant_presence',
                'peak_info': peak_info
            }
            logger.info("NGV forecast: zero (no significant presence)")
            return forecast_ngv, metadata

        # Determine decline start year
        peak_year = peak_info['peak_year']

        if self.decline_start_mode == 'max_peak_or_tipping':
            if tipping_point is not None:
                decline_start_year = max(peak_year, tipping_point)
            else:
                decline_start_year = peak_year
        elif self.decline_start_mode == 'tipping_only':
            decline_start_year = tipping_point if tipping_point else peak_year
        else:
            decline_start_year = peak_year

        logger.info(f"NGV decline starts: {decline_start_year} "
                   f"(peak: {peak_year}, tipping: {tipping_point})")

        # Build complete time series
        all_years = np.concatenate([historical_years, forecast_years])
        all_market = np.concatenate([historical_market, forecast_market])

        # Initialize NGV sales array
        ngv_sales = np.zeros_like(all_years, dtype=float)

        # Fill historical values
        hist_len = len(historical_years)
        ngv_sales[:hist_len] = historical_ngv

        # Forecast NGV for future years
        peak_share = peak_info['peak_share']

        for i in range(hist_len, len(all_years)):
            year = all_years[i]
            market = all_market[i]

            if year <= decline_start_year:
                # Before decline: maintain peak share
                share = peak_share
            else:
                # After decline start: exponential decay
                years_since_decline = year - decline_start_year
                decay_factor = np.exp(-np.log(2) * years_since_decline / self.half_life_years)
                share = peak_share * decay_factor

                # Apply 2040 target constraint
                if year >= 2040:
                    share = min(share, self.target_share_2040)

            ngv_sales[i] = share * market

        # Extract forecast portion
        forecast_ngv = ngv_sales[hist_len:]

        metadata = {
            'model': 'exponential_decline',
            'peak_info': peak_info,
            'decline_start_year': int(decline_start_year),
            'half_life_years': self.half_life_years,
            'final_share_2040': float(ngv_sales[-1] / all_market[-1]) if all_market[-1] > 0 else 0
        }

        logger.info(f"NGV forecast complete: final 2040 share = "
                   f"{metadata['final_share_2040']:.2%}")

        return forecast_ngv, metadata

    def validate_ngv_forecast(self,
                             forecast_years: np.ndarray,
                             forecast_ngv: np.ndarray,
                             forecast_market: np.ndarray) -> Dict:
        """
        Validate NGV forecast consistency.

        Args:
            forecast_years: Forecast years
            forecast_ngv: Forecasted NGV sales
            forecast_market: Forecasted market sales

        Returns:
            Dict with validation results
        """
        issues = []

        # Check non-negative
        if np.any(forecast_ngv < 0):
            issues.append("negative_values")

        # Check shares are within bounds
        shares = np.divide(forecast_ngv, forecast_market,
                          where=forecast_market > 0,
                          out=np.zeros_like(forecast_ngv, dtype=float))

        if np.any(shares > 1.0):
            issues.append("share_exceeds_100%")

        # Check declining trend after some point
        if len(forecast_ngv) > 5:
            # Should decline in later years
            early_avg = np.mean(forecast_ngv[:len(forecast_ngv)//3])
            late_avg = np.mean(forecast_ngv[-len(forecast_ngv)//3:])

            if late_avg > early_avg * 1.1:  # Allow 10% tolerance
                issues.append("increasing_trend_detected")

        # Check 2040 target
        if 2040 in forecast_years:
            idx_2040 = np.where(forecast_years == 2040)[0][0]
            share_2040 = shares[idx_2040]
            if share_2040 > self.target_share_2040 + 0.01:  # Allow 1% tolerance
                issues.append(f"2040_share_exceeds_target: {share_2040:.2%}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'share_range': (float(np.min(shares)), float(np.max(shares))),
            'final_share': float(shares[-1]) if len(shares) > 0 else 0
        }
