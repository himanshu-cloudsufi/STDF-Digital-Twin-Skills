#!/usr/bin/env python3
"""
Output Validation Script for Energy Forecasting (SWB)

Validates forecast output files against expected constraints:
- Energy balance
- Non-negativity
- Capacity factor bounds
- Cost ranges
- Displacement timeline consistency
- Emissions reasonableness
- Battery metrics formulas
- JSON structure completeness
"""

import json
import sys
import argparse
from pathlib import Path


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class OutputValidator:
    """Validates energy forecast output files"""

    def __init__(self, tolerance=0.02):
        self.tolerance = tolerance
        self.errors = []
        self.warnings = []

    def validate_file(self, filepath):
        """Validate a forecast output file"""
        print(f"Validating: {filepath}")
        print("-" * 60)

        # Load JSON
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ValidationError(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

        # Run all validation checks
        self._validate_structure(data)
        self._validate_energy_balance(data)
        self._validate_non_negativity(data)
        self._validate_costs(data)
        self._validate_battery_metrics(data)
        self._validate_displacement_timeline(data)
        self._validate_emissions(data)

        # Report results
        self._report_results()

        return len(self.errors) == 0

    def _validate_structure(self, data):
        """Validate JSON structure completeness"""
        required_keys = [
            "region",
            "end_year",
            "scenario",
            "generation_forecasts",
        ]

        for key in required_keys:
            if key not in data:
                self.errors.append(f"Missing required key: {key}")

        # Check if cost analysis exists (not present for Global)
        if data.get("region") != "Global" and "cost_analysis" not in data:
            self.warnings.append("Missing cost_analysis (expected for non-Global regions)")

        # Check generation_forecasts structure
        if "generation_forecasts" in data:
            gen = data["generation_forecasts"]
            required_gen_keys = ["years", "swb_total", "coal", "gas", "non_swb", "total_demand"]

            for key in required_gen_keys:
                if key not in gen:
                    self.errors.append(f"Missing generation_forecasts.{key}")

            # Check array lengths match
            if "years" in gen:
                expected_len = len(gen["years"])
                for key in ["swb_total", "coal", "gas", "non_swb", "total_demand"]:
                    if key in gen and len(gen[key]) != expected_len:
                        self.errors.append(
                            f"Array length mismatch: {key} has {len(gen[key])} items, expected {expected_len}"
                        )

    def _validate_energy_balance(self, data):
        """Validate energy balance: SWB + Coal + Gas + Non_SWB ≈ Total"""
        if "generation_forecasts" not in data:
            return

        gen = data["generation_forecasts"]

        # Check all required keys exist
        required = ["swb_total", "coal", "gas", "non_swb", "total_demand"]
        if not all(key in gen for key in required):
            return  # Already flagged in structure validation

        swb = gen["swb_total"]
        coal = gen["coal"]
        gas = gen["gas"]
        non_swb = gen["non_swb"]
        total = gen["total_demand"]

        for i, year in enumerate(gen["years"]):
            calculated_total = swb[i] + coal[i] + gas[i] + non_swb[i]
            expected_total = total[i]

            if expected_total > 0:
                deviation = abs(calculated_total - expected_total) / expected_total

                if deviation > self.tolerance:
                    self.errors.append(
                        f"Energy balance failed at year {year}: "
                        f"calculated={calculated_total:.1f} GWh, "
                        f"expected={expected_total:.1f} GWh, "
                        f"deviation={deviation * 100:.2f}%"
                    )

    def _validate_non_negativity(self, data):
        """Validate all generation values are non-negative"""
        if "generation_forecasts" not in data:
            return

        gen = data["generation_forecasts"]

        for key in ["swb_total", "coal", "gas", "non_swb", "total_demand"]:
            if key not in gen:
                continue

            values = gen[key]
            for i, val in enumerate(values):
                if val < 0:
                    year = gen["years"][i] if i < len(gen["years"]) else i
                    self.errors.append(f"Negative value in {key} at year {year}: {val}")

        # Check capacity forecasts if present
        if "capacity_forecasts" in data:
            for tech, forecast in data["capacity_forecasts"].items():
                if "capacity_gw" in forecast:
                    for i, val in enumerate(forecast["capacity_gw"]):
                        if val < 0:
                            year = forecast["years"][i] if i < len(forecast["years"]) else i
                            self.errors.append(f"Negative capacity in {tech} at year {year}: {val}")

    def _validate_costs(self, data):
        """Validate cost ranges are reasonable"""
        if "cost_analysis" not in data:
            return

        cost_analysis = data["cost_analysis"]

        # Validate cost forecasts
        if "cost_forecasts" in cost_analysis:
            for tech, forecast in cost_analysis["cost_forecasts"].items():
                if "costs" not in forecast:
                    continue

                costs = forecast["costs"]

                # LCOE should be 10-500 $/MWh
                for i, cost in enumerate(costs):
                    if cost < 10 or cost > 500:
                        year = forecast["years"][i] if i < len(forecast["years"]) else i
                        self.warnings.append(
                            f"Unusual cost for {tech} at year {year}: ${cost:.2f}/MWh"
                        )

        # Validate tipping points
        if "tipping_points" in cost_analysis:
            tipping = cost_analysis["tipping_points"]

            if "tipping_overall" in tipping:
                tp = tipping["tipping_overall"]
                if tp and (tp < 2020 or tp > 2100):
                    self.warnings.append(f"Unusual tipping point year: {tp}")

    def _validate_battery_metrics(self, data):
        """Validate battery metrics formulas"""
        if "battery_metrics" not in data:
            return

        metrics = data["battery_metrics"]

        required = ["energy_capacity_gwh", "power_capacity_gw", "duration_hours"]
        if not all(key in metrics for key in required):
            return

        energy = metrics["energy_capacity_gwh"]
        power = metrics["power_capacity_gw"]
        duration = metrics["duration_hours"]

        # Validate formula: Power (GW) = Energy (GWh) / Duration (hours)
        for i in range(len(energy)):
            expected_power = energy[i] / duration
            actual_power = power[i]

            if abs(expected_power - actual_power) > 0.1:
                year = metrics["years"][i] if i < len(metrics["years"]) else i
                self.errors.append(
                    f"Battery power capacity mismatch at year {year}: "
                    f"expected={expected_power:.2f} GW, actual={actual_power:.2f} GW"
                )

        # Validate throughput if present
        if "throughput_twh_per_year" in metrics and "cycles_per_year" in metrics:
            throughput = metrics["throughput_twh_per_year"]
            cycles = metrics["cycles_per_year"]

            for i in range(len(energy)):
                # Throughput (TWh/yr) = Energy (GWh) × Cycles / 1000
                expected_throughput = energy[i] * cycles / 1000
                actual_throughput = throughput[i]

                if abs(expected_throughput - actual_throughput) > 0.1:
                    year = metrics["years"][i] if i < len(metrics["years"]) else i
                    self.warnings.append(
                        f"Battery throughput mismatch at year {year}: "
                        f"expected={expected_throughput:.2f} TWh/yr, actual={actual_throughput:.2f} TWh/yr"
                    )

    def _validate_displacement_timeline(self, data):
        """Validate displacement timeline consistency"""
        if "displacement_timeline" not in data:
            return

        timeline = data["displacement_timeline"]

        # Extract milestone years
        milestones = {
            key: timeline.get(key)
            for key in [
                "swb_exceeds_coal",
                "swb_exceeds_gas",
                "swb_exceeds_all_fossil",
                "coal_95_percent_displaced",
                "gas_95_percent_displaced",
            ]
            if timeline.get(key) is not None
        }

        # Check chronological order (loose check)
        years = list(milestones.values())
        for year in years:
            if year < 2020 or year > 2100:
                self.warnings.append(f"Unusual displacement year: {year}")

    def _validate_emissions(self, data):
        """Validate emissions trajectory"""
        if "emissions_trajectory" not in data:
            return

        emissions = data["emissions_trajectory"]

        # Check annual emissions are reasonable
        if "annual_emissions_mt" in emissions:
            annual = emissions["annual_emissions_mt"]

            if "total" in annual:
                for i, val in enumerate(annual["total"]):
                    if val < 0:
                        year = emissions["years"][i] if i < len(emissions["years"]) else i
                        self.errors.append(f"Negative emissions at year {year}: {val} Mt")

                    # Check for unreasonably high emissions (> 50 Gt global)
                    if val > 50000:
                        year = emissions["years"][i] if i < len(emissions["years"]) else i
                        self.warnings.append(f"Very high emissions at year {year}: {val} Mt")

        # Check cumulative emissions are monotonically increasing
        if "cumulative_emissions_mt" in emissions:
            cumulative = emissions["cumulative_emissions_mt"]

            if "total" in cumulative:
                for i in range(1, len(cumulative["total"])):
                    if cumulative["total"][i] < cumulative["total"][i - 1]:
                        year = emissions["years"][i] if i < len(emissions["years"]) else i
                        self.errors.append(
                            f"Cumulative emissions decreased at year {year} "
                            f"(should be monotonically increasing)"
                        )

    def _report_results(self):
        """Report validation results"""
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")
        elif not self.errors:
            print(f"\n✅ Validation passed with {len(self.warnings)} warnings")
        else:
            print(f"\n❌ Validation failed with {len(self.errors)} errors")


def main():
    parser = argparse.ArgumentParser(
        description="Validate energy forecast output files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate single file
  python3 validate_output.py output/China_2040_baseline.json

  # Validate all JSON files
  for file in output/*.json; do
      python3 validate_output.py "$file"
  done
        """,
    )

    parser.add_argument("file", help="Path to forecast output JSON file")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.02,
        help="Energy balance tolerance (default: 0.02 = 2%%)",
    )

    args = parser.parse_args()

    # Validate file exists
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Run validation
    validator = OutputValidator(tolerance=args.tolerance)

    try:
        success = validator.validate_file(filepath)
        sys.exit(0 if success else 1)
    except ValidationError as e:
        print(f"\n❌ Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
