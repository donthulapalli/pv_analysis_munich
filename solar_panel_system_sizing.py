from pvlib import location, irradiance, pvsystem, modelchain
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Location setup
latitude, longitude, altitude = 48.13, 11.5, 520
times = pd.date_range('2023-01-01', '2023-12-31', freq='1h', tz='Europe/Berlin')
site = location.Location(latitude, longitude, tz='Europe/Berlin', altitude=altitude)
solar_position = site.get_solarposition(times)
clear_sky = site.get_clearsky(times)

# POA irradiance
surface_tilt = 30
surface_azimuth = 180
poa_irradiance = irradiance.get_total_irradiance(
    surface_tilt=surface_tilt, surface_azimuth=surface_azimuth,
    dni=clear_sky['dni'], ghi=clear_sky['ghi'], dhi=clear_sky['dhi'],
    solar_zenith=solar_position['apparent_zenith'],
    solar_azimuth=solar_position['azimuth'])

# Manual energy calculation
panel_efficiency = 0.20
panel_area = 1.7
power_output = poa_irradiance['poa_global'] * panel_efficiency * panel_area
energy_kwh = power_output / 1000

# ModelChain simulation
module_parameters = {'pdc0': 400, 'gamma_pdc': -0.004}
inverter_parameters = {'pdc0': 400, 'eta_inv_nom': 0.96}
system = pvsystem.PVSystem(
    surface_tilt=surface_tilt, surface_azimuth=surface_azimuth,
    module_parameters=module_parameters, inverter_parameters=inverter_parameters,
    racking_model='open_rack', module_type='glass_polymer')
weather = pd.DataFrame({
    'ghi': clear_sky['ghi'], 'dni': clear_sky['dni'], 'dhi': clear_sky['dhi'],
    'temp_air': 10, 'wind_speed': 3})
mc = modelchain.ModelChain(system, site, aoi_model="no_loss", spectral_model="no_loss")
mc.run_model(weather)
ac_power = mc.results.ac
annual_solar_energy = ac_power.sum() / 1000

# Load analysis
appliances = {
    'LED Lights':      {'power': 50,   'hours': 5,   'quantity': 6},
    'Refrigerator':    {'power': 150,  'hours': 24,  'quantity': 1},
    'TV':              {'power': 100,  'hours': 4,   'quantity': 2},
    'Laptop':          {'power': 65,   'hours': 6,   'quantity': 2},
    'Washing Machine': {'power': 500,  'hours': 1,   'quantity': 1},
    'Microwave':       {'power': 1000, 'hours': 0.5, 'quantity': 1},
    'Phone Charger':   {'power': 20,   'hours': 3,   'quantity': 4},
    'Dishwasher':      {'power': 1500, 'hours': 1,   'quantity': 1},
    'Electric Kettle': {'power': 2000, 'hours': 0.5, 'quantity': 1},
}
total_daily_load = 0
peak_load = 0
for appliance, specs in appliances.items():
    energy = specs['power'] * specs['hours'] * specs['quantity']
    total_daily_load += energy
    peak_load += specs['power'] * specs['quantity']

annual_load = (total_daily_load / 1000) * 365

# Panel sizing
panels_needed = annual_load / annual_solar_energy
panel_specs = {
    'voc': 49.5, 'isc': 10.2, 'vmp': 41.2, 'imp': 9.71, 'pmax': 400}
panels_in_series = math.ceil(48 / panel_specs['vmp'])
panels_in_parallel = math.ceil(panels_needed / panels_in_series)
total_panels = panels_in_series * panels_in_parallel

# Battery sizing
autonomy_days = 2
dod = 0.8
battery_voltage = 48
battery_capacity_ah = (total_daily_load / 1000 * autonomy_days) / dod * 1000 / battery_voltage
battery_ah_rating = 100
battery_single_voltage = 12
batteries_in_series = battery_voltage / battery_single_voltage
batteries_in_parallel = math.ceil(battery_capacity_ah / battery_ah_rating)
total_batteries = batteries_in_series * batteries_in_parallel

# MPPT sizing
safety_factor = 1.25
mppt_voltage = panels_in_series * panel_specs['vmp'] * safety_factor
mppt_current = panels_in_parallel * panel_specs['imp'] * safety_factor

# Inverter sizing
power_factor = 0.8
inverter_rating = peak_load / power_factor * safety_factor

# Cable sizing
cable_length_dc = 10
cable_length_ac = 15
resistivity = 0.0000000168
dc_current = panel_specs['isc'] * panels_in_parallel
dc_voltage = panel_specs['voc'] * panels_in_series
ac_voltage = 230
ac_current = peak_load / ac_voltage
allowed_voltage_drop_dc = dc_voltage * 0.03
allowed_voltage_drop_ac = ac_voltage * 0.05
required_area_dc = (2 * resistivity * cable_length_dc * dc_current * 1000000) / allowed_voltage_drop_dc
required_area_ac = (2 * resistivity * cable_length_ac * ac_current * 1000000) / allowed_voltage_drop_ac
standard_sizes = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50]
dc_cable = next(size for size in standard_sizes if size >= required_area_dc)
ac_cable = next(size for size in standard_sizes if size >= required_area_ac)

# Cost estimation
costs = {
    'panel_cost_per_unit': 150,
    'battery_cost_per_unit': 120,
    'mppt_cost': 300,
    'inverter_cost_per_kva': 200,
    'dc_cable_cost_per_meter': 3,
    'ac_cable_cost_per_meter': 2,
    'installation_percent': 0.15
}
panel_cost = total_panels * costs['panel_cost_per_unit']
battery_cost = total_batteries * costs['battery_cost_per_unit']
mppt_cost = costs['mppt_cost']
inverter_cost = (inverter_rating / 1000) * costs['inverter_cost_per_kva']
dc_cable_cost = cable_length_dc * 2 * costs['dc_cable_cost_per_meter']
ac_cable_cost = cable_length_ac * costs['ac_cable_cost_per_meter']
equipment_cost = panel_cost + battery_cost + mppt_cost + inverter_cost + dc_cable_cost + ac_cable_cost
installation_cost = equipment_cost * costs['installation_percent']
total_cost = equipment_cost + installation_cost
electricity_price = 0.30
annual_savings = annual_load * electricity_price
payback_years = total_cost / annual_savings

# Print summary
print(f"Annual load: {annual_load:.2f} kWh")
print(f"Annual solar: {annual_solar_energy:.2f} kWh")
print(f"Panels: {total_panels}")
print(f"Batteries: {total_batteries:.0f}")
print(f"MPPT: {mppt_voltage:.0f}V / {mppt_current:.0f}A")
print(f"Inverter: {inverter_rating/1000:.1f} kVA")
print(f"DC Cable: {dc_cable} mm²")
print(f"AC Cable: {ac_cable} mm²")
print(f"Total Cost: €{total_cost:.0f}")
print(f"Payback: {payback_years:.1f} years")
print(f"ROI: {((annual_savings * 25) - total_cost) / total_cost * 100:.1f}%")

# Dashboard charts
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

pie_colors = ['orange', 'blue', 'green', 'red', 'purple', 'gray']
cost_labels = ['Panels', 'Batteries', 'MPPT', 'Inverter', 'Cables', 'Installation']
cost_values = [panel_cost, battery_cost, mppt_cost, inverter_cost,
               dc_cable_cost + ac_cable_cost, installation_cost]
axes[0, 0].pie(cost_values, labels=cost_labels, colors=pie_colors,
               autopct='%1.1f%%', startangle=90)
axes[0, 0].set_title('System Cost Breakdown')

years = [0, 5, 10, 15, 20, 25]
cumulative = [(-total_cost)] + [(annual_savings * y) - total_cost for y in years[1:]]
bar_colors = ['red' if x < 0 else 'green' for x in cumulative]
axes[0, 1].bar(years, cumulative, color=bar_colors)
axes[0, 1].axhline(y=0, color='black', linestyle='--')
axes[0, 1].set_title('Financial Returns Over 25 Years')
axes[0, 1].set_xlabel('Years')
axes[0, 1].set_ylabel('€')
axes[0, 1].grid(True)

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
monthly_solar = [44, 51, 73, 81, 90, 88, 90, 84, 72, 62, 46, 38]
monthly_load_values = [350, 310, 290, 260, 240, 220, 210, 215, 240, 270, 310, 340]
x = range(12)
axes[1, 0].bar([i - 0.2 for i in x], monthly_solar, width=0.4,
               label='Solar Production', color='orange')
axes[1, 0].bar([i + 0.2 for i in x], monthly_load_values, width=0.4,
               label='Household Load', color='blue')
axes[1, 0].set_xticks(range(12))
axes[1, 0].set_xticklabels(months, rotation=45)
axes[1, 0].set_title('Solar Production vs Household Load')
axes[1, 0].set_ylabel('Energy (kWh)')
axes[1, 0].legend()
axes[1, 0].grid(True)

components = ['Panels\n(units)', 'Batteries\n(units)', 'MPPT\n(A)', 'Inverter\n(kVA)']
values = [total_panels, total_batteries, math.ceil(mppt_current), math.ceil(inverter_rating / 1000)]
axes[1, 1].bar(components, values, color=['orange', 'blue', 'green', 'red'])
axes[1, 1].set_title('System Components Summary')
axes[1, 1].set_ylabel('Rating/Quantity')
axes[1, 1].grid(True)

plt.suptitle('Complete Solar System Analysis — Munich 2023', fontsize=14)
plt.tight_layout()
plt.savefig('solar_dashboard.png', dpi=150, bbox_inches='tight')
plt.show()