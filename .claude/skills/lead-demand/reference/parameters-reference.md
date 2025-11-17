# Parameters Reference

## Contents
- Lead Content Coefficients (kg/unit)
- Battery Lifetimes (Replacement Cycle)
- Asset Lifetimes (Scrappage Calculation)
- Econometric Parameters

---

## Lead Content Coefficients (kg/unit)

These coefficients represent the average lead content in batteries for each vehicle type and powertrain configuration.

### Passenger Cars
- **ICE**: 11.5 kg/unit
- **BEV**: 9.0 kg/unit
- **PHEV**: Dataset-specific (fallback: 10.5 kg/unit)
- **HEV**: 10.5 kg/unit

### Two-Wheelers
- **ICE**: 2.5 kg/unit
- **EV**: 1.8 kg/unit

### Three-Wheelers
- **ICE**: 7.0 kg/unit
- **EV**: 5.0 kg/unit

### Commercial Vehicles
- **ICE**: 22.0 kg/unit
- **EV**: 18.0 kg/unit
- **NGV**: 22.0 kg/unit

### Industrial Applications
- **Motive Power**: 875 kg/unit (forklifts, range: 750-1000 kg)
- **Stationary Power**: 300,000 kg/MWh (UPS systems)

---

## Battery Lifetimes (Replacement Cycle)

Battery lifetimes determine replacement demand frequency. These are shorter than asset lifetimes.

- **SLI batteries**: 4.5 years
- **Motive batteries**: 7.0 years
- **Stationary batteries**: 6.0 years

---

## Asset Lifetimes (Scrappage Calculation)

Asset lifetimes determine when vehicles/equipment are scrapped from the installed base.

- **Passenger cars**: 18.0 years
- **Two-wheelers**: 11.0 years
- **Three-wheelers**: 9.0 years
- **Commercial vehicles**: 20.0 years
- **Forklifts**: 14.0 years
- **UPS systems**: 10.0 years

---

## Econometric Parameters

Used for modeling "Other Uses" (non-battery applications) demand:

- **Other Uses Price Elasticity**: -0.3
  - Demand decreases 0.3% per 1% price increase
  - Negative elasticity indicates inverse relationship

- **Other Uses Base Growth**: 1.5% annual
  - Baseline growth rate when prices are stable

- **GDP Elasticity**: 0.7
  - Applied when IPI/GDP data is available
  - Demand grows 0.7% per 1% GDP increase

---

## Parameter Modification

All parameters are configured in `config.json`. To modify:

1. Edit `config.json` in the skill directory
2. Locate the relevant section (e.g., `lead_coefficients`, `battery_lifetimes`)
3. Update values as needed
4. Run forecast to see impact

For automated parameter tuning based on validation variance, use `calibrate_coefficients.py`.
