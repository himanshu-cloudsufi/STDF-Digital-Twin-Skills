#!/usr/bin/env python3
"""
Coefficient Calibration for Lead Demand Forecasting
Automatically adjusts lead coefficients based on validation variance to improve accuracy
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from datetime import datetime
import shutil


class CoefficientCalibrator:
    """Calibrate lead coefficients based on validation variance"""

    def __init__(self, config_path, results_path):
        """Initialize with config and forecast results"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Load results
        results_file = Path(results_path)
        if results_file.suffix == '.csv':
            self.results = pd.read_csv(results_file)
        elif results_file.suffix == '.json':
            self.results = pd.read_json(results_file)
        elif results_file.suffix == '.parquet':
            self.results = pd.read_parquet(results_file)
        else:
            raise ValueError(f"Unsupported file format: {results_file.suffix}")

        self.config_path = Path(config_path)
        self.calibrated_config = self.config.copy()
        self.calibration_history = []

    def extract_validation_variance(self):
        """Extract validation variance metrics from results"""
        variance_metrics = {}

        variance_cols = [col for col in self.results.columns if 'variance_pct' in col]

        for col in variance_cols:
            if not pd.isna(self.results[col].iloc[0]):
                variance_metrics[col] = self.results[col].iloc[0]

        return variance_metrics

    def calibrate_coefficients(self, variance_threshold=10.0, adjustment_factor=0.5):
        """
        Calibrate coefficients based on validation variance

        Args:
            variance_threshold: Variance % threshold to trigger calibration (default: 10%)
            adjustment_factor: Factor to dampen adjustment (default: 0.5 for conservative updates)

        Returns:
            dict: Summary of calibration changes
        """
        variance_metrics = self.extract_validation_variance()

        if not variance_metrics:
            print("⚠️  No validation variance metrics found in results")
            return {}

        print(f"\n{'='*70}")
        print("COEFFICIENT CALIBRATION")
        print(f"{'='*70}")
        print(f"Variance threshold: {variance_threshold}%")
        print(f"Adjustment factor: {adjustment_factor}")
        print()

        calibration_summary = {}

        # Map variance metrics to coefficient paths
        coefficient_map = {
            'cars_oem_variance_pct': {
                'type': 'passenger_car',
                'segment': 'oem',
                'powertrains': ['ice', 'bev', 'phev']
            },
            'cars_replacement_variance_pct': {
                'type': 'passenger_car',
                'segment': 'replacement',
                'powertrains': ['ice', 'bev', 'phev']
            },
            '2w_oem_variance_pct': {
                'type': 'two_wheeler',
                'segment': 'oem',
                'powertrains': ['ice', 'ev']
            },
            '2w_replacement_variance_pct': {
                'type': 'two_wheeler',
                'segment': 'replacement',
                'powertrains': ['ice', 'ev']
            },
            '3w_oem_variance_pct': {
                'type': 'three_wheeler',
                'segment': 'oem',
                'powertrains': ['ice', 'ev']
            },
            '3w_replacement_variance_pct': {
                'type': 'three_wheeler',
                'segment': 'replacement',
                'powertrains': ['ice', 'ev']
            }
        }

        for variance_key, coeff_info in coefficient_map.items():
            if variance_key in variance_metrics:
                variance = variance_metrics[variance_key]

                # Check if variance exceeds threshold
                if abs(variance) > variance_threshold:
                    vehicle_type = coeff_info['type']
                    segment = coeff_info['segment']
                    powertrains = coeff_info['powertrains']

                    print(f"⚠️  {variance_key}: {variance:.1f}% (exceeds {variance_threshold}%)")
                    print(f"   Calibrating {vehicle_type} coefficients...")

                    # Calculate adjustment: negative variance means we overestimated
                    # so we need to reduce coefficients
                    adjustment_ratio = 1.0 - (variance / 100.0) * adjustment_factor

                    # Apply to all relevant powertrains
                    for powertrain in powertrains:
                        old_coeff = self.calibrated_config['lead_coefficients']['sli_batteries'][vehicle_type].get(powertrain)

                        if old_coeff:
                            new_coeff = old_coeff * adjustment_ratio

                            # Apply bounds (prevent unrealistic values)
                            if vehicle_type == 'passenger_car':
                                new_coeff = max(8.0, min(25.0, new_coeff))  # 8-25 kg range
                            elif vehicle_type == 'two_wheeler':
                                new_coeff = max(1.0, min(5.0, new_coeff))   # 1-5 kg range
                            elif vehicle_type == 'three_wheeler':
                                new_coeff = max(4.0, min(10.0, new_coeff))  # 4-10 kg range
                            elif vehicle_type == 'commercial_vehicle':
                                new_coeff = max(15.0, min(35.0, new_coeff)) # 15-35 kg range

                            # Update calibrated config
                            self.calibrated_config['lead_coefficients']['sli_batteries'][vehicle_type][powertrain] = round(new_coeff, 2)

                            # Record change
                            change_key = f"{vehicle_type}_{powertrain}"
                            calibration_summary[change_key] = {
                                'old_value': round(old_coeff, 2),
                                'new_value': round(new_coeff, 2),
                                'change_pct': round(((new_coeff - old_coeff) / old_coeff) * 100, 2),
                                'variance': round(variance, 2)
                            }

                            print(f"   - {powertrain.upper()}: {old_coeff:.2f} → {new_coeff:.2f} kg ({((new_coeff - old_coeff) / old_coeff) * 100:+.1f}%)")

                    self.calibration_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'metric': variance_key,
                        'variance': variance,
                        'changes': calibration_summary
                    })

                else:
                    print(f"✓ {variance_key}: {variance:.1f}% (within threshold)")

        print(f"\n✓ Calibration complete: {len(calibration_summary)} coefficients adjusted")
        return calibration_summary

    def save_calibrated_config(self, output_path=None, backup=True):
        """Save calibrated configuration"""
        if output_path is None:
            output_path = self.config_path

        output_file = Path(output_path)

        # Backup original config
        if backup and output_file.exists():
            backup_path = output_file.with_suffix('.json.backup')
            shutil.copy(output_file, backup_path)
            print(f"\n✓ Backed up original config to: {backup_path}")

        # Save calibrated config
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(self.calibrated_config, f, indent=2)

        print(f"✓ Saved calibrated config to: {output_file}")

        # Save calibration history
        if self.calibration_history:
            history_file = output_file.parent / 'calibration_history.json'
            with open(history_file, 'w') as f:
                json.dump(self.calibration_history, f, indent=2)
            print(f"✓ Saved calibration history to: {history_file}")

    def generate_calibration_report(self, output_path=None):
        """Generate calibration report"""
        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("COEFFICIENT CALIBRATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Config file: {self.config_path}")
        report_lines.append("")

        if self.calibration_history:
            report_lines.append("CALIBRATION CHANGES:")
            report_lines.append("-" * 80)

            for entry in self.calibration_history:
                report_lines.append(f"\nMetric: {entry['metric']}")
                report_lines.append(f"Variance: {entry['variance']:.2f}%")
                report_lines.append("\nCoefficient Adjustments:")

                for coeff_name, change_info in entry['changes'].items():
                    report_lines.append(f"  {coeff_name}:")
                    report_lines.append(f"    Old: {change_info['old_value']:.2f} kg")
                    report_lines.append(f"    New: {change_info['new_value']:.2f} kg")
                    report_lines.append(f"    Change: {change_info['change_pct']:+.2f}%")

        else:
            report_lines.append("No calibration changes made (all variances within threshold)")

        report_lines.append("\n" + "=" * 80)

        report_text = "\n".join(report_lines)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"\n✓ Calibration report saved to: {output_file}")
        else:
            print("\n" + report_text)

        return report_text


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Calibrate Lead Coefficients Based on Validation Variance')
    parser.add_argument('--results', type=str, required=True,
                       help='Path to forecast results file with validation variance')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file (defaults to ../config.json)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output path for calibrated config (defaults to overwriting input config)')
    parser.add_argument('--threshold', type=float, default=10.0,
                       help='Variance threshold (%%) to trigger calibration (default: 10.0)')
    parser.add_argument('--adjustment-factor', type=float, default=0.5,
                       help='Adjustment damping factor (default: 0.5 for conservative updates)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Do not backup original config')
    parser.add_argument('--report', type=str, default=None,
                       help='Output path for calibration report (optional)')

    args = parser.parse_args()

    # Get config path
    if args.config:
        config_path = args.config
    else:
        skill_dir = Path(__file__).parent.parent
        config_path = skill_dir / 'config.json'

    if not Path(config_path).exists():
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)

    if not Path(args.results).exists():
        print(f"Error: Results file not found at {args.results}")
        sys.exit(1)

    # Create calibrator
    calibrator = CoefficientCalibrator(config_path, args.results)

    # Calibrate coefficients
    calibration_summary = calibrator.calibrate_coefficients(
        variance_threshold=args.threshold,
        adjustment_factor=args.adjustment_factor
    )

    if calibration_summary:
        # Save calibrated config
        calibrator.save_calibrated_config(
            output_path=args.output,
            backup=not args.no_backup
        )

        # Generate report
        if args.report:
            calibrator.generate_calibration_report(args.report)
        else:
            skill_dir = Path(__file__).parent.parent
            default_report = skill_dir / 'output' / 'calibration_report.txt'
            calibrator.generate_calibration_report(default_report)
    else:
        print("\n✓ No calibration needed - all variances within threshold")


if __name__ == "__main__":
    main()
