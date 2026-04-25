
from pvlib import location, irradiance, pvsystem, modelchain
import pandas as pd 
import matplotlib.pyplot as plt
latitude, longitude, altitude = 48.13, 11.5, 520
times = pd.date_range('2023-01-01', '2023-12-31', freq='1h', tz='Europe/Berlin')
site = location.Location(latitude, longitude,tz='Europe/Berlin', altitude=altitude)
solar_position = site.get_solarposition(times)
print(solar_position.head(10))
clear_sky = site.get_clearsky(times)
surface_tilt = 30
surface_azimuth = 180
poa_irradiance = irradiance.get_total_irradiance(surface_tilt = surface_tilt, surface_azimuth = surface_azimuth,dni=clear_sky['dni'],ghi=clear_sky['ghi'],dhi=clear_sky['dhi'], solar_zenith=solar_position['apparent_zenith'], solar_azimuth=solar_position['azimuth'])
print(poa_irradiance.head(10))

panel_efficiency = 0.20  # 20% efficient
panel_area = 1.7         # 1.7 m² standard panel size

# Calculate power output in Watts
power_output = poa_irradiance['poa_global'] * panel_efficiency * panel_area

# Calculate energy in kWh
energy_kwh = power_output / 1000

# Print results
print(f"Total annual energy: {energy_kwh.sum():.2f} kWh")
print(f"Average daily energy: {energy_kwh.sum()/365:.2f} kWh")
print(f"Best month: {energy_kwh.resample('M').sum().idxmax().strftime('%B')} - {energy_kwh.resample('M').sum().max():.2f} kWh")
print(f"Worst month: {energy_kwh.resample('M').sum().idxmin().strftime('%B')} - {energy_kwh.resample('M').sum().min():.2f} kWh")
# Define a real solar panel system
module_parameters = {
    'pdc0': 400,    # panel power in watts
    'gamma_pdc': -0.004  # temperature coefficient
}

inverter_parameters = {
    'pdc0': 400,    # inverter power
    'eta_inv_nom': 0.96  # inverter efficiency 96%
}

# Create PV system
system = pvsystem.PVSystem(
    surface_tilt=surface_tilt,
    surface_azimuth=surface_azimuth,
    module_parameters=module_parameters,
    inverter_parameters=inverter_parameters,
    racking_model='open_rack',
    module_type='glass_polymer'
)


print(system)
print("✅ PV System created!")
# Create weather dataframe
weather = pd.DataFrame({
    'ghi': clear_sky['ghi'],
    'dni': clear_sky['dni'],
    'dhi': clear_sky['dhi'],
    'temp_air': 10,  # average temperature in celsius
    'wind_speed': 3  # average wind speed m/s
})

# Run modelchain simulation
mc = modelchain.ModelChain(system, site, aoi_model="no_loss", spectral_model="no_loss")
mc.run_model(weather)

# Get results
ac_power = mc.results.ac
print(f"Total AC energy: {ac_power.sum()/1000:.2f} kWh")
print("✅ ModelChain simulation complete!")
print(len(ac_power), "hours of data simulated.")
# Manual monthly
manual_monthly = energy_kwh.resample('M').sum()

# ModelChain monthly  
ac_monthly = ac_power.resample('M').sum() / 1000

# Plot both together
fig, ax = plt.subplots(figsize=(12,5))

manual_monthly.plot(kind='bar', ax=ax, color='orange', 
                    label='Manual', position=1, width=0.4)
ac_monthly.plot(kind='bar', ax=ax, color='green', 
                label='ModelChain', position=0, width=0.4)

ax.set_xticklabels(manual_monthly.index.strftime('%b'), rotation=45)
plt.legend()
plt.title('Manual vs ModelChain — Munich 2023')
plt.xlabel('Month')
plt.ylabel('Energy (kWh)')
plt.grid(True)
plt.tight_layout()
plt.show()