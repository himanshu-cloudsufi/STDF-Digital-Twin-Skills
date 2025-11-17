#!/usr/bin/env python3
"""
Evidence Register Generator for Lead Demand Forecasting
Documents all parameters, sources, and assumptions used in the forecast
"""

import json
import pandas as pd
from pathlib import Path
import argparse
import sys
from datetime import datetime


class EvidenceRegister:
    """Generate evidence register for all forecast parameters"""

    def __init__(self, config_path):
        """Load configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def generate_register(self):
        """Generate comprehensive evidence register"""
        evidence = {
            'Parameter': [],
            'Value': [],
            'Unit': [],
            'Source': [],
            'Evidence Type': [],
            'Confidence': [],
            'Notes': []
        }

        # SLI Battery Coefficients
        sli_coeffs = self.config['lead_coefficients']['sli_batteries']

        # Passenger cars
        pc_coeffs = sli_coeffs.get('passenger_car', {})
        evidence['Parameter'].append('Lead content - Passenger car ICE')
        evidence['Value'].append(pc_coeffs.get('ice', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Industry data - Battery manufacturers')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Standard 12V SLI battery for ICE vehicles')

        evidence['Parameter'].append('Lead content - Passenger car BEV')
        evidence['Value'].append(pc_coeffs.get('bev', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Industry data - OEM specifications')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium-High')
        evidence['Notes'].append('Auxiliary 12V battery for BEVs (smaller than ICE)')

        evidence['Parameter'].append('Lead content - Passenger car PHEV')
        evidence['Value'].append(pc_coeffs.get('phev', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Dataset-derived or fallback value')
        evidence['Evidence Type'].append('Mixed')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Uses dynamic dataset when available, fallback to config')

        evidence['Parameter'].append('Lead content - Passenger car HEV')
        evidence['Value'].append(pc_coeffs.get('hev', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Industry data')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Similar to PHEV, auxiliary 12V system')

        # Two-wheelers
        tw_coeffs = sli_coeffs.get('two_wheeler', {})
        evidence['Parameter'].append('Lead content - Two-wheeler ICE')
        evidence['Value'].append(tw_coeffs.get('ice', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Industry data - Regional manufacturers')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Small 6V/12V battery')

        evidence['Parameter'].append('Lead content - Two-wheeler EV')
        evidence['Value'].append(tw_coeffs.get('ev', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Manufacturer specifications')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Auxiliary battery if present, may be zero for some models')

        # Three-wheelers
        thw_coeffs = sli_coeffs.get('three_wheeler', {})
        evidence['Parameter'].append('Lead content - Three-wheeler ICE')
        evidence['Value'].append(thw_coeffs.get('ice', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Regional industry data')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Typical rickshaw/auto battery')

        evidence['Parameter'].append('Lead content - Three-wheeler EV')
        evidence['Value'].append(thw_coeffs.get('ev', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Manufacturer data')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Smaller auxiliary battery')

        # Commercial vehicles
        cv_coeffs = sli_coeffs.get('commercial_vehicle', {})
        evidence['Parameter'].append('Lead content - Commercial vehicle ICE')
        evidence['Value'].append(cv_coeffs.get('ice', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('OEM specifications, aftermarket data')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Heavy-duty SLI batteries, often dual battery systems')

        evidence['Parameter'].append('Lead content - Commercial vehicle EV')
        evidence['Value'].append(cv_coeffs.get('ev', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('OEM specifications')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Auxiliary systems for electric CVs')

        evidence['Parameter'].append('Lead content - Commercial vehicle NGV')
        evidence['Value'].append(cv_coeffs.get('ngv', 'N/A'))
        evidence['Unit'].append('kg/vehicle')
        evidence['Source'].append('Industry data')
        evidence['Evidence Type'].append('Primary data')
        evidence['Confidence'].append('Medium-High')
        evidence['Notes'].append('Similar to ICE systems')

        # Industrial Batteries
        ind_coeffs = self.config['lead_coefficients']['industrial_batteries']

        evidence['Parameter'].append('Lead content - Motive power (forklifts)')
        evidence['Value'].append(ind_coeffs.get('motive_kg_per_unit', 'N/A'))
        evidence['Unit'].append('kg/unit')
        evidence['Source'].append('Industry standards, forklift battery specifications')
        evidence['Evidence Type'].append('Industry standard')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Typical range 750-1000 kg per forklift battery pack')

        evidence['Parameter'].append('Lead content - Stationary (UPS)')
        evidence['Value'].append(ind_coeffs.get('stationary_kg_per_mwh', 'N/A'))
        evidence['Unit'].append('kg/MWh')
        evidence['Source'].append('UPS system specifications, data center standards')
        evidence['Evidence Type'].append('Industry standard')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Standard conversion: 300 kg/kWh = 300,000 kg/MWh')

        # Battery Lifetimes
        batt_lifetimes = self.config['battery_lifetimes']

        evidence['Parameter'].append('Battery lifetime - SLI')
        evidence['Value'].append(batt_lifetimes.get('sli_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Industry average, warranty data')
        evidence['Evidence Type'].append('Statistical average')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Typical replacement cycle, varies by climate/usage')

        evidence['Parameter'].append('Battery lifetime - Motive power')
        evidence['Value'].append(batt_lifetimes.get('motive_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Industrial battery lifecycle studies')
        evidence['Evidence Type'].append('Industry data')
        evidence['Confidence'].append('Medium-High')
        evidence['Notes'].append('Depends on charge cycles and maintenance')

        evidence['Parameter'].append('Battery lifetime - Stationary')
        evidence['Value'].append(batt_lifetimes.get('stationary_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('UPS lifecycle data, data center reports')
        evidence['Evidence Type'].append('Industry data')
        evidence['Confidence'].append('Medium-High')
        evidence['Notes'].append('Float vs cycling applications affect lifetime')

        # Asset Lifetimes
        asset_lifetimes = self.config['asset_lifetimes']

        evidence['Parameter'].append('Asset lifetime - Passenger car')
        evidence['Value'].append(asset_lifetimes.get('passenger_car_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('OICA, regional transport statistics')
        evidence['Evidence Type'].append('Official statistics')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Average vehicle lifespan varies by region')

        evidence['Parameter'].append('Asset lifetime - Two-wheeler')
        evidence['Value'].append(asset_lifetimes.get('two_wheeler_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Regional transport data')
        evidence['Evidence Type'].append('Official statistics')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Shorter in developing markets with high usage')

        evidence['Parameter'].append('Asset lifetime - Three-wheeler')
        evidence['Value'].append(asset_lifetimes.get('three_wheeler_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Regional industry data')
        evidence['Evidence Type'].append('Industry estimates')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Commercial use leads to shorter lifespans')

        evidence['Parameter'].append('Asset lifetime - Commercial vehicle')
        evidence['Value'].append(asset_lifetimes.get('commercial_vehicle_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Fleet management data, industry reports')
        evidence['Evidence Type'].append('Industry data')
        evidence['Confidence'].append('High')
        evidence['Notes'].append('Varies significantly by vehicle class and usage')

        evidence['Parameter'].append('Asset lifetime - Forklift')
        evidence['Value'].append(asset_lifetimes.get('forklift_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Equipment lifecycle studies')
        evidence['Evidence Type'].append('Industry data')
        evidence['Confidence'].append('Medium-High')
        evidence['Notes'].append('Well-maintained units can exceed 20 years')

        evidence['Parameter'].append('Asset lifetime - UPS system')
        evidence['Value'].append(asset_lifetimes.get('ups_system_years', 'N/A'))
        evidence['Unit'].append('years')
        evidence['Source'].append('Data center equipment lifecycle')
        evidence['Evidence Type'].append('Industry data')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('System lifetime, batteries replaced more frequently')

        # Econometric Parameters
        econ_params = self.config.get('econometric_parameters', {})

        evidence['Parameter'].append('Other uses - Price elasticity')
        evidence['Value'].append(econ_params.get('other_uses_price_elasticity', 'N/A'))
        evidence['Unit'].append('dimensionless')
        evidence['Source'].append('Literature review, econometric studies')
        evidence['Evidence Type'].append('Econometric estimate')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Negative elasticity indicates demand decreases with price increases')

        evidence['Parameter'].append('Other uses - Base growth rate')
        evidence['Value'].append(econ_params.get('base_growth_rate', 'N/A'))
        evidence['Unit'].append('decimal (annual)')
        evidence['Source'].append('Historical trend analysis')
        evidence['Evidence Type'].append('Calibrated parameter')
        evidence['Confidence'].append('Medium')
        evidence['Notes'].append('Baseline trend independent of price effects')

        return pd.DataFrame(evidence)

    def save_register(self, output_path):
        """Generate and save evidence register"""
        register_df = self.generate_register()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save as CSV
        register_df.to_csv(output_file, index=False)
        print(f"✓ Evidence register saved to: {output_file}")

        # Also save as formatted text
        txt_file = output_file.with_suffix('.txt')
        with open(txt_file, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("LEAD DEMAND FORECASTING - EVIDENCE REGISTER\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            f.write(register_df.to_string(index=False))
            f.write("\n" + "=" * 100 + "\n")

        print(f"✓ Evidence register (text) saved to: {txt_file}")

        return register_df


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Generate Evidence Register')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to config file')
    parser.add_argument('--output', type=str, default=None,
                       help='Output path for evidence register')

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

    # Get output path
    if args.output:
        output_path = args.output
    else:
        skill_dir = Path(__file__).parent.parent
        output_path = skill_dir / 'output' / 'evidence_register.csv'

    # Generate register
    register = EvidenceRegister(config_path)
    register.save_register(output_path)


if __name__ == "__main__":
    main()
