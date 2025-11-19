"""
Emissions Tracking for Energy Forecasting
Calculates CO2 emissions from power generation sources
"""

import numpy as np
from typing import Dict, Tuple, Optional
from exceptions import DataNotFoundError


class EmissionsCalculator:
    """Calculate and track CO2 emissions from energy generation"""

    def __init__(self, config: dict, data_loader):
        """
        Initialize emissions calculator

        Args:
            config: Configuration dictionary
            data_loader: DataLoader instance
        """
        self.config = config
        self.data_loader = data_loader

        # Emission factors from config (kg CO2 per MWh)
        emission_config = config.get("emission_factors", {})
        self.emission_factors = {
            "coal": emission_config.get("coal_kg_co2_per_mwh", 1000),
            "gas": emission_config.get("gas_kg_co2_per_mwh", 450),
            "solar": emission_config.get("solar_kg_co2_per_mwh", 45),
            "wind": emission_config.get("wind_kg_co2_per_mwh", 12),
            "nuclear": emission_config.get("nuclear_kg_co2_per_mwh", 12),
            "hydro": emission_config.get("hydro_kg_co2_per_mwh", 24)
        }

    def calculate_emissions_trajectory(
        self,
        years: np.ndarray,
        coal_generation: np.ndarray,
        gas_generation: np.ndarray,
        solar_generation: np.ndarray,
        wind_generation: np.ndarray,
        nuclear_generation: Optional[np.ndarray] = None,
        hydro_generation: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Calculate emissions trajectory for all generation sources

        Args:
            years: Array of years
            coal_generation: Coal generation in GWh
            gas_generation: Gas generation in GWh
            solar_generation: Solar generation in GWh
            wind_generation: Wind generation in GWh
            nuclear_generation: Nuclear generation in GWh (optional)
            hydro_generation: Hydro generation in GWh (optional)

        Returns:
            Dictionary with emissions data
        """
        # Convert GWh to MWh for emission calculation
        # 1 GWh = 1000 MWh
        coal_mwh = coal_generation * 1000
        gas_mwh = gas_generation * 1000
        solar_mwh = solar_generation * 1000
        wind_mwh = wind_generation * 1000

        # Calculate emissions (kg CO2)
        coal_emissions = coal_mwh * self.emission_factors["coal"]
        gas_emissions = gas_mwh * self.emission_factors["gas"]
        solar_emissions = solar_mwh * self.emission_factors["solar"]
        wind_emissions = wind_mwh * self.emission_factors["wind"]

        # Add nuclear and hydro if provided
        nuclear_emissions = np.zeros_like(years)
        hydro_emissions = np.zeros_like(years)

        if nuclear_generation is not None:
            nuclear_mwh = nuclear_generation * 1000
            nuclear_emissions = nuclear_mwh * self.emission_factors["nuclear"]

        if hydro_generation is not None:
            hydro_mwh = hydro_generation * 1000
            hydro_emissions = hydro_mwh * self.emission_factors["hydro"]

        # Calculate totals
        fossil_emissions = coal_emissions + gas_emissions
        clean_emissions = solar_emissions + wind_emissions + nuclear_emissions + hydro_emissions
        total_emissions = fossil_emissions + clean_emissions

        # Convert to million tonnes CO2 for readability
        # 1 Mt = 1,000,000 tonnes = 1,000,000,000 kg
        coal_emissions_mt = coal_emissions / 1e9
        gas_emissions_mt = gas_emissions / 1e9
        fossil_emissions_mt = fossil_emissions / 1e9
        clean_emissions_mt = clean_emissions / 1e9
        total_emissions_mt = total_emissions / 1e9

        # Calculate cumulative emissions
        cumulative_coal = np.cumsum(coal_emissions_mt)
        cumulative_gas = np.cumsum(gas_emissions_mt)
        cumulative_fossil = np.cumsum(fossil_emissions_mt)
        cumulative_total = np.cumsum(total_emissions_mt)

        # Calculate emissions intensity (kg CO2 per MWh)
        total_generation_mwh = coal_mwh + gas_mwh + solar_mwh + wind_mwh
        if nuclear_generation is not None:
            total_generation_mwh += nuclear_generation * 1000
        if hydro_generation is not None:
            total_generation_mwh += hydro_generation * 1000

        emissions_intensity = np.divide(
            total_emissions,
            total_generation_mwh,
            out=np.zeros_like(total_emissions),
            where=total_generation_mwh != 0
        )

        return {
            "years": years.tolist(),
            "annual_emissions_mt": {
                "coal": coal_emissions_mt.tolist(),
                "gas": gas_emissions_mt.tolist(),
                "fossil_total": fossil_emissions_mt.tolist(),
                "clean_technologies": clean_emissions_mt.tolist(),
                "total": total_emissions_mt.tolist()
            },
            "cumulative_emissions_mt": {
                "coal": cumulative_coal.tolist(),
                "gas": cumulative_gas.tolist(),
                "fossil_total": cumulative_fossil.tolist(),
                "total": cumulative_total.tolist()
            },
            "emissions_intensity_kg_per_mwh": emissions_intensity.tolist(),
            "emission_factors": self.emission_factors
        }

    def calculate_emissions_avoided(
        self,
        years: np.ndarray,
        swb_generation: np.ndarray,
        displaced_coal: np.ndarray,
        displaced_gas: np.ndarray
    ) -> Dict:
        """
        Calculate emissions avoided by SWB displacing fossil fuels

        Args:
            years: Array of years
            swb_generation: SWB generation in GWh
            displaced_coal: Coal displaced by SWB in GWh
            displaced_gas: Gas displaced by SWB in GWh

        Returns:
            Dictionary with avoided emissions data
        """
        # Convert to MWh
        displaced_coal_mwh = displaced_coal * 1000
        displaced_gas_mwh = displaced_gas * 1000

        # Calculate emissions that would have occurred
        avoided_coal_emissions = displaced_coal_mwh * self.emission_factors["coal"]
        avoided_gas_emissions = displaced_gas_mwh * self.emission_factors["gas"]
        total_avoided = avoided_coal_emissions + avoided_gas_emissions

        # Calculate lifecycle emissions from SWB
        # Average of solar and wind emission factors
        swb_emission_factor = (self.emission_factors["solar"] + self.emission_factors["wind"]) / 2
        swb_emissions = swb_generation * 1000 * swb_emission_factor

        # Net emissions avoided (fossil avoided - clean lifecycle)
        net_avoided = total_avoided - swb_emissions

        # Convert to Mt CO2
        avoided_coal_mt = avoided_coal_emissions / 1e9
        avoided_gas_mt = avoided_gas_emissions / 1e9
        total_avoided_mt = total_avoided / 1e9
        swb_emissions_mt = swb_emissions / 1e9
        net_avoided_mt = net_avoided / 1e9

        # Calculate cumulative
        cumulative_net_avoided = np.cumsum(net_avoided_mt)

        return {
            "years": years.tolist(),
            "avoided_emissions_mt": {
                "from_coal_displacement": avoided_coal_mt.tolist(),
                "from_gas_displacement": avoided_gas_mt.tolist(),
                "total_fossil_avoided": total_avoided_mt.tolist(),
                "swb_lifecycle_emissions": swb_emissions_mt.tolist(),
                "net_avoided": net_avoided_mt.tolist()
            },
            "cumulative_net_avoided_mt": cumulative_net_avoided.tolist()
        }

    def validate_against_actual(
        self,
        region: str,
        calculated_years: np.ndarray,
        calculated_emissions_mt: np.ndarray
    ) -> Optional[Dict]:
        """
        Validate calculated emissions against actual historical data

        Args:
            region: Region name
            calculated_years: Years from calculation
            calculated_emissions_mt: Calculated emissions in Mt CO2

        Returns:
            Dictionary with validation results, or None if no actual data
        """
        try:
            # Try to load actual coal emissions data
            actual_years, actual_emissions_tonnes = self.data_loader.get_coal_emissions(region)

            # Convert actual from tonnes to Mt
            actual_emissions_mt = np.array(actual_emissions_tonnes) / 1e6

            # Find overlapping years
            overlap_years = np.intersect1d(calculated_years, actual_years)

            if len(overlap_years) == 0:
                print(f"  WARNING: No overlapping years for validation")
                return None

            # Extract values for overlap period
            calc_mask = np.isin(calculated_years, overlap_years)
            actual_mask = np.isin(actual_years, overlap_years)

            calc_overlap = calculated_emissions_mt[calc_mask]
            actual_overlap = actual_emissions_mt[actual_mask]

            # Calculate error metrics
            abs_error = calc_overlap - actual_overlap
            pct_error = (abs_error / actual_overlap) * 100
            mean_abs_pct_error = np.mean(np.abs(pct_error))
            rmse = np.sqrt(np.mean(abs_error ** 2))

            validation_result = {
                "validation_period": {
                    "start_year": int(overlap_years[0]),
                    "end_year": int(overlap_years[-1]),
                    "num_years": len(overlap_years)
                },
                "metrics": {
                    "mean_absolute_percentage_error": float(mean_abs_pct_error),
                    "root_mean_square_error_mt": float(rmse)
                },
                "sample_comparison": {
                    "years": overlap_years[:5].tolist(),
                    "calculated_mt": calc_overlap[:5].tolist(),
                    "actual_mt": actual_overlap[:5].tolist()
                }
            }

            print(f"  INFO: Validation against actual data:")
            print(f"        Period: {overlap_years[0]}-{overlap_years[-1]}")
            print(f"        MAPE: {mean_abs_pct_error:.1f}%")
            print(f"        RMSE: {rmse:.1f} Mt CO2")

            return validation_result

        except DataNotFoundError:
            print(f"  INFO: No actual emissions data available for validation")
            return None
        except Exception as e:
            print(f"  WARNING: Validation failed: {e}")
            return None


if __name__ == "__main__":
    print("Emissions Calculator module for SWB Energy Forecasting")
