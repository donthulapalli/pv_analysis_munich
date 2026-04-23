
from pvlib import location, irradiance
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
monthly_energy = energy_kwh.resample('M').sum().rename('Energy (kWh)')
monthly_energy.plot(kind='bar',color='green')
plt.xlabel('month')
plt.gca().set_xticklabels(monthly_energy.index.strftime('%b'), rotation=45)
plt.ylabel('Energy (kWh)')
plt.title('Monthly Energy Production')
plt.grid(True)
plt.tight_layout()
plt.show()