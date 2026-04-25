# Munich Solar PV Analysis 🌞

## Project Overview
Complete solar PV energy analysis for Munich, Germany 
using Python and pvlib library.

## What this project does
- Calculates solar position for Munich throughout 2023
- Analyzes clear sky irradiance (GHI, DNI, DHI)
- Calculates POA irradiance on tilted panel (30° south facing)
- Manual energy calculation using panel efficiency
- Professional ModelChain simulation
- Compares both methods visually

## Results
- Manual calculation: 713.89 kWh/year
- ModelChain simulation: 819.55 kWh/year
- Best month: July (~90 kWh)
- Worst month: December (~38 kWh)
- ModelChain is ~15% higher due to temperature 
  and inverter modeling

## System Specifications
- Panel power: 400W
- Panel efficiency: 20%
- Surface tilt: 30°
- Surface azimuth: 180° (south facing)
- Inverter efficiency: 96%
- Mounting: Open rack

## Tools Used
- Python
- pvlib
- pandas
- matplotlib

## Author
Bhanuchander — Renewable Energy & E-Mobility Engineer
Location: Germany
