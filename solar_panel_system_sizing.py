
from pvlib import location, irradiance, pvsystem, modelchain
import pandas as pd 
import matplotlib.pyplot as plt
import math
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

appliances = {
    'LED Lights':      {'power': 50,   'hours': 5,    'quantity': 6},
    'Refrigerator':    {'power': 150,  'hours': 24,   'quantity': 1},
    'TV':              {'power': 100,  'hours': 4,    'quantity': 2},
    'Laptop':          {'power': 65,   'hours': 6,    'quantity': 2},
    'Washing Machine': {'power': 500,  'hours': 1,    'quantity': 1},
    'Microwave':       {'power': 1000, 'hours': 0.5,  'quantity': 1},
    'Phone Charger':   {'power': 20,   'hours': 3,    'quantity': 4},
    'Dishwasher':      {'power': 1500, 'hours': 1,    'quantity': 1},
    'Electric Kettle': {'power': 2000, 'hours': 0.5,  'quantity': 1},
}
total_daily_load = 0
for appliance,specs in appliances.items():
    energy = specs['power'] * specs['hours'] * specs['quantity']
    total_daily_load += energy
print(f"Total daily load:{total_daily_load/1000:.2f} Kwh")
annual_load = total_daily_load * 365
annual_load = annual_load/1000
print(f"total annual load is :{annual_load:.2f} kwh" )
# How many panels needed?
annual_solar_energy = ac_power.sum()/1000
print(f"Annual solar energy: {annual_solar_energy:.2f} kWh")
panels_needed = annual_load/annual_solar_energy
print(f"NUmber of panels needed: {panels_needed:.2f}")
print(f"panels needed to install to cover load:{math.ceil(panels_needed)}")

#Battersizing
#lets consider 2 days of autonomy
autonomy_days = 2
dod = 0.8
battery_voltage = 48
battery_capacity_kwh = (total_daily_load / 1000 * autonomy_days) / dod
battery_capacity_ah = battery_capacity_kwh * 1000 / battery_voltage
print(f"Battery capacity needed:{battery_capacity_ah:.2f} AH")
#battery_capacity_ah = 600
battery_ah_rating = 100
battery_single_voltage = 12
batteries_in_series = battery_voltage/ battery_single_voltage
batteries_in_parallel = math.ceil(battery_capacity_ah/battery_ah_rating)
total_batteries= batteries_in_series * batteries_in_parallel
print(f"Total batteries needed: {total_batteries:.2f}")
panel_specs = {
    'voc': 49.5,   # for MPPT voltage sizing
    'isc': 10.2,   # for MPPT current sizing
    'vmp': 41.2,   # for series configuration
    'imp': 9.71,   # for parallel configuration
    'pmax': 400    # panel power
}
panels_in_series =math.ceil(battery_voltage/panel_specs['vmp'])
panels_in_parallel = math.ceil(panels_needed/panels_in_series)
total_panels = math.ceil(panels_in_series)* math.ceil(panels_in_parallel)
print(f"Total panels is :{total_panels} ")
#MPPT Sizing
safety_factor = 1.25
mppt_voltage = panels_in_series * panel_specs['vmp'] * safety_factor
mppt_current = panels_in_parallel * panel_specs['imp'] * safety_factor
print(f"MPPT voltage rating: {mppt_voltage:.2f} V")
print(f"MPPT current rating: {mppt_current:.2f} A")
#Inverter Sizing
peak_load = 0 
for appliance, specs in appliances.items():
    peak_load += specs['power'] * specs['quantity']
power_factor = 0.8
safety_factor = 1.25
inverter_rating = (peak_load)/ power_factor * safety_factor
print(f"Inverter rating needed: {inverter_rating/1000:.2f} kva")
#cable sizing
# Cable sizing parameters
cable_length_dc = 10   # meters (panels to MPPT)
cable_length_ac = 15   # meters (inverter to load)
resistivity = 0.0000000168  # copper resistivity (Ω·m)
max_voltage_drop_dc = 0.03  # 3% maximum
max_voltage_drop_ac = 0.05  # 5% maximum

# DC side current (panels to MPPT)
dc_current = panel_specs['isc'] * panels_in_parallel
dc_voltage = panel_specs['voc'] * panels_in_series

# AC side current (inverter to load)
ac_power = peak_load
ac_voltage = 230  # European standard
ac_current = ac_power / ac_voltage

print(f"DC current: {dc_current:.2f} A")
print(f"DC voltage: {dc_voltage:.2f} V")
print(f"AC current: {ac_current:.2f} A")
# DC cable sizing
allowed_voltage_drop_dc = dc_voltage * max_voltage_drop_dc
required_area_dc = (2 * resistivity * cable_length_dc * dc_current * 1000000) / allowed_voltage_drop_dc

# AC cable sizing
allowed_voltage_drop_ac = ac_voltage * max_voltage_drop_ac
required_area_ac = (2 * resistivity * cable_length_ac * ac_current * 1000000) / allowed_voltage_drop_ac

print(f"DC cable size needed: {required_area_dc:.2f} mm²")
print(f"AC cable size needed: {required_area_ac:.2f} mm²")
standard_sizes = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50]

dc_cable = next(size for size in standard_sizes if size >= required_area_dc)
ac_cable = next(size for size in standard_sizes if size >= required_area_ac)

print(f"DC cable to use: {dc_cable} mm²")
print(f"AC cable to use: {ac_cable} mm²")
# Final system summary
print("\n--- Final System Summary ---")
print(f"Total annual load: {annual_load:.2f} kWh")
print(f"Annual solar energy: {annual_solar_energy:.2f} kWh")
print(f"Number of panels needed: {math.ceil(panels_needed)}")
print(f"Battery capacity needed: {battery_capacity_ah:.2f} AH")
print(f"Total batteries needed: {total_batteries}")
print(f"MPPT voltage rating: {mppt_voltage:.2f} V")
print(f"MPPT current rating: {mppt_current:.2f} A")
print(f"Inverter rating needed: {inverter_rating/1000:.2f} kVA")
print(f"DC cable to use: {dc_cable} mm²")
print(f"AC cable to use: {ac_cable} mm²")   
# Component costs (approximate market prices in €)
costs = {
    'panel_cost_per_unit': 150,      # € per panel
    'battery_cost_per_unit': 120,    # € per battery
    'mppt_cost': 300,                # € for MPPT
    'inverter_cost_per_kva': 200,    # € per kVA
    'dc_cable_cost_per_meter': 3,    # € per meter
    'ac_cable_cost_per_meter': 2,    # € per meter
    'installation_percent': 0.15     # 15% of equipment cost
}

# Calculate costs
panel_cost = total_panels * costs['panel_cost_per_unit']
battery_cost = total_batteries * costs['battery_cost_per_unit']
mppt_cost = costs['mppt_cost']
inverter_cost = (inverter_rating/1000) * costs['inverter_cost_per_kva']
dc_cable_cost = cable_length_dc * 2 * costs['dc_cable_cost_per_meter']
ac_cable_cost = cable_length_ac * costs['ac_cable_cost_per_meter']

equipment_cost = panel_cost + battery_cost + mppt_cost + inverter_cost + dc_cable_cost + ac_cable_cost
installation_cost = equipment_cost * costs['installation_percent']
total_cost = equipment_cost + installation_cost

print(f"\n=== SYSTEM COST ESTIMATION ===")
print(f"Solar Panels ({total_panels} × €{costs['panel_cost_per_unit']}): €{panel_cost:.0f}")
print(f"Batteries ({total_batteries} × €{costs['battery_cost_per_unit']}): €{battery_cost:.0f}")
print(f"MPPT Controller: €{mppt_cost:.0f}")
print(f"Inverter: €{inverter_cost:.0f}")
print(f"DC Cables: €{dc_cable_cost:.0f}")
print(f"AC Cables: €{ac_cable_cost:.0f}")
print(f"Equipment Total: €{equipment_cost:.0f}")
print(f"Installation (15%): €{installation_cost:.0f}")
print(f"TOTAL SYSTEM COST: €{total_cost:.0f}")
# Payback period calculation
electricity_price = 0.30  # €/kWh Germany average
annual_savings = annual_load * electricity_price

payback_years = total_cost / annual_savings

print(f"\n=== FINANCIAL ANALYSIS ===")
print(f"Annual electricity savings: €{annual_savings:.0f}")
print(f"Payback period: {payback_years:.1f} years")
print(f"25 year savings: €{(annual_savings * 25) - total_cost:.0f}")
print(f"Return on Investment (ROI) over 25 years: {((annual_savings * 25) - total_cost) / total_cost * 100:.1f}%")
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Chart 1 — Cost breakdown pie chart
cost_labels = ['Panels', 'Batteries', 'MPPT', 'Inverter', 'Cables', 'Installation']
cost_values = [panel_cost, battery_cost, mppt_cost, inverter_cost,
               dc_cable_cost + ac_cable_cost, installation_cost]
colors = ['orange', 'blue', 'green', 'red', 'purple', 'gray']

axes[0,0].pie(cost_values, labels=cost_labels, colors=colors,
              autopct='%1.1f%%', startangle=90)
axes[0,0].set_title('System Cost Breakdown')

# Chart 2 — Financial returns
years = [0, 5, 10, 15, 20, 25]
cumulative = [(-total_cost)] + [(annual_savings * y) - total_cost for y in years[1:]]
axes[0,1].bar(years, cumulative, color=['red' if x < 0 else 'green' for x in cumulative])
axes[0,1].axhline(y=0, color='black', linestyle='--')
axes[0,1].set_title('Financial Returns Over 25 Years')
axes[0,1].set_xlabel('Years')
axes[0,1].set_ylabel('€')
axes[0,1].grid(True)
# Chart 3 — Solar vs Load comparison
months = ['Jan','Feb','Mar','Apr','May','Jun',
          'Jul','Aug','Sep','Oct','Nov','Dec']
monthly_solar = [44, 51, 73, 81, 90, 88, 90, 84, 72, 62, 46, 38]
monthly_load_values = [350, 310, 290, 260, 240, 220, 
                       210, 215, 240, 270, 310, 340]

x = range(12)
axes[1,0].bar([i-0.2 for i in x], monthly_solar, width=0.4,
               label='Solar Production', color='orange')
axes[1,0].bar([i+0.2 for i in x], monthly_load_values, width=0.4,
               label='Household Load', color='blue')
axes[1,0].set_xticks(range(12))
axes[1,0].set_xticklabels(months, rotation=45)
axes[1,0].set_title('Solar Production vs Household Load')
axes[1,0].set_ylabel('Energy (kWh)')
axes[1,0].legend()
axes[1,0].grid(True)



# Chart 4 — System sizing summary
components = ['Panels\n(units)', 'Batteries\n(units)', 'MPPT\n(A)', 'Inverter\n(kVA)']
values = [total_panels, total_batteries, math.ceil(mppt_current), 
          math.ceil(inverter_rating/1000)]
colors4 = ['orange', 'blue', 'green', 'red']

axes[1,1].bar(components, values, color=colors4)
axes[1,1].set_title('System Components Summary')
axes[1,1].set_ylabel('Rating/Quantity')
axes[1,1].grid(True)

plt.suptitle('Complete Solar System Analysis — Munich 2023', fontsize=14)
plt.tight_layout()
plt.show()

