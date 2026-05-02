# Solar PV System Design Tool 🌞

## Project Overview
Complete off-grid solar PV system design tool built 
in Python — from resource analysis to full system sizing.

## What this tool does
- Calculates solar resource for any location using pvlib
- Analyzes clear sky irradiance (GHI, DNI, DHI)
- Simulates PV energy production using ModelChain
- Performs complete household load analysis
- Sizes complete off-grid solar system

## System Sizing Outputs
- Number of solar panels needed
- Battery bank capacity and configuration
- MPPT charge controller rating
- Inverter rating
- DC and AC cable sizes

## Example Results (Munich, Germany)
- Daily load: 10.42 kWh/day
- Annual load: 3803 kWh/year
- Solar panels: 6 × 400W = 2.4 kW
- Battery bank: 24 × 12V 100Ah = 26 kWh
- MPPT: 150V / 40A
- Inverter: 10 kVA
- DC cable: 4 mm²
- AC cable: 1.5 mm²

## Tools Used
- Python
- pvlib
- pandas
- matplotlib
- math

## Author
Bhanuchander — Renewable Energy & E-Mobility Engineer
Location: Germany
GitHub: github.com/donthulapalli
