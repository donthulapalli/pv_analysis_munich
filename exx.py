from pvlib.iotools import get_pvgis_hourly
import math
import matplotlib.pyplot as plt
import calendar
import pandas as pd

# ============================================================
# FETCH MUNICH DATA
# ============================================================
data, inputs = get_pvgis_hourly(
    latitude=48.13,
    longitude=11.58,
    start=2020,
    end=2020,
    raddatabase='PVGIS-SARAH3'
)

# Calculate total POA irradiance
data['poa_global'] = data['poa_direct'] + data['poa_sky_diffuse'] + data['poa_ground_diffuse']

# Panel specifications
panel_efficiency = 0.20
panel_area = 1.7

annual_solar_munich = ((data['poa_global'].sum()) * panel_efficiency * panel_area / 1000)
print(f"Munich - Total annual energy per panel: {annual_solar_munich:.2f} kWh")

# ============================================================
# COMPONENT 2: CHARGING LOSSES (added early - needed for all calcs)
# ============================================================
inverter_efficiency = 0.96   # 96% inverter efficiency
charging_efficiency = 0.88   # 88% AC/DC conversion loss
total_efficiency = inverter_efficiency * charging_efficiency

print("\n=== COMPONENT 2: CHARGING LOSSES ===")
print(f"Inverter efficiency: {inverter_efficiency*100:.0f}%")
print(f"AC/DC charging efficiency: {charging_efficiency*100:.0f}%")
print(f"Total system efficiency: {total_efficiency*100:.1f}%")
print(f"Energy lost in charging process: {(1-total_efficiency)*100:.1f}%")

# ============================================================
# COMPONENT 1: SELF CONSUMPTION RATE
# ============================================================
self_consumption_rate = 0.30  # 30% - car home during solar hours

print("\n=== COMPONENT 1: SELF CONSUMPTION RATE ===")
print(f"Self consumption rate: {self_consumption_rate*100:.0f}%")
print(f"Reason: EV at work during peak solar hours (10am-3pm)")
print(f"Annual solar production (1 panel): {annual_solar_munich:.1f} kWh")
print(f"Effective solar for EV: {annual_solar_munich * self_consumption_rate:.1f} kWh")
print(f"After charging losses: {annual_solar_munich * self_consumption_rate * total_efficiency:.1f} kWh")

# ============================================================
# EV SCENARIOS
# ============================================================
ev_scenarios = {
    'Efficient EV': {'consumption': 15, 'annual_km': 15000},
    'Average EV':   {'consumption': 18, 'annual_km': 15000},
    'Large EV':     {'consumption': 22, 'annual_km': 15000}
}

print("\n=== EV ANNUAL DEMAND vs SOLAR COVERAGE ===")
print("Without losses vs With losses comparison:")
for ev, specs in ev_scenarios.items():
    annual_ev_demand = specs['consumption'] * specs['annual_km'] / 100
    
    # Without losses (original)
    coverage_simple = (annual_solar_munich / annual_ev_demand) * 100
    
    # With self consumption + charging losses
    effective_solar = annual_solar_munich * self_consumption_rate * total_efficiency
    coverage_realistic = (effective_solar / annual_ev_demand) * 100
    
    print(f"\n{ev} - Annual demand: {annual_ev_demand:.0f} kWh")
    print(f"  Simple coverage:    {coverage_simple:.1f}%")
    print(f"  Realistic coverage: {coverage_realistic:.1f}% (with losses)")
    print(f"  Panels needed (realistic): {math.ceil(100/coverage_realistic)}")

# ============================================================
# CITY ANALYSIS FUNCTION
# ============================================================
def analyze_city(latitude, longitude, city_name):
    city_data, _ = get_pvgis_hourly(
        latitude=latitude,
        longitude=longitude,
        start=2020,
        end=2020,
        raddatabase='PVGIS-SARAH3'
    )
    city_data['poa_global'] = city_data['poa_direct'] + city_data['poa_sky_diffuse'] + city_data['poa_ground_diffuse']
    annual_energy = ((city_data['poa_global'].sum()) * panel_efficiency * panel_area / 1000)
    print(f"{city_name} - Annual energy per panel: {annual_energy:.2f} kWh")
    return annual_energy, city_data

Frankfurt_energy, frankfurt_data = analyze_city(50.11, 8.68, "Frankfurt")
Hamburg_energy, hamburg_data = analyze_city(53.55, 9.99, "Hamburg")
Munich_energy = annual_solar_munich

# Monthly solar data
frankfurt_data['poa_global'] = frankfurt_data['poa_direct'] + frankfurt_data['poa_sky_diffuse'] + frankfurt_data['poa_ground_diffuse']
hamburg_data['poa_global'] = hamburg_data['poa_direct'] + hamburg_data['poa_sky_diffuse'] + hamburg_data['poa_ground_diffuse']

monthly_solar_munich = data['poa_global'].resample('M').sum() * panel_efficiency * panel_area / 1000
monthly_solar_frankfurt = frankfurt_data['poa_global'].resample('M').sum() * panel_efficiency * panel_area / 1000
monthly_solar_hamburg = hamburg_data['poa_global'].resample('M').sum() * panel_efficiency * panel_area / 1000

# ============================================================
# MONTHLY EV DEMAND WITH SEASONAL FACTORS
# ============================================================
monthly_factors = [1.20, 1.15, 1.05, 1.00, 0.95, 0.90,
                   0.88, 0.89, 0.95, 1.00, 1.10, 1.18]

# Use Average EV for monthly analysis
annual_ev_demand_avg = 18 * 15000 / 100  # 2700 kWh

monthly_ev = []
for month in range(1, 13):
    days = calendar.monthrange(2020, month)[1]
    factor = monthly_factors[month - 1]
    daily_demand = annual_ev_demand_avg / 365
    monthly_demand = daily_demand * days * factor
    monthly_ev.append(monthly_demand)

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# ============================================================
# COMPONENT 3: LCOE ANALYSIS
# ============================================================
panels_for_ev = 7  # panels needed for average EV in Munich
panel_cost_each = 150  # € per panel
system_cost = panels_for_ev * panel_cost_each
lifetime = 25
annual_maintenance = 50  # € per year

total_cost = system_cost + (annual_maintenance * lifetime)
total_energy_lifetime = Munich_energy * panels_for_ev * lifetime

lcoe = total_cost / total_energy_lifetime
grid_price = 0.30  # €/kWh Germany 2020

print("\n=== COMPONENT 3: LCOE ANALYSIS ===")
print(f"System cost ({panels_for_ev} panels): €{system_cost}")
print(f"Maintenance over {lifetime} years: €{annual_maintenance * lifetime}")
print(f"Total cost: €{total_cost}")
print(f"Total energy over {lifetime} years: {total_energy_lifetime:.0f} kWh")
print(f"LCOE: €{lcoe:.3f}/kWh")
print(f"German grid price: €{grid_price:.3f}/kWh")
print(f"Solar is {((grid_price - lcoe) / grid_price) * 100:.1f}% cheaper than grid!")
print(f"25-year savings: €{(grid_price - lcoe) * total_energy_lifetime:.0f}")

# ============================================================
# COMPONENT 4: V2G/V2H DISCUSSION
# ============================================================
print("\n=== COMPONENT 4: V2G/V2H POTENTIAL ===")
print("Vehicle-to-Grid (V2G) allows EV to feed energy back to grid")
print("Vehicle-to-Home (V2H) allows EV to power home appliances")
print("German regulatory framework (EEG 2023) evolving to support V2G")
print("Potential additional revenue from V2G: €50-150/year estimated")
print("V2G could significantly improve solar self-consumption rate")

# ============================================================
# CITY COMPARISON WITH ALL LOSSES
# ============================================================
print("\n=== REALISTIC CITY COMPARISON (with all losses) ===")
cities_energy = {'Munich': Munich_energy, 'Frankfurt': Frankfurt_energy, 'Hamburg': Hamburg_energy}

for ev, specs in ev_scenarios.items():
    annual_ev_demand = specs['consumption'] * specs['annual_km'] / 100
    print(f"\n{ev} ({annual_ev_demand:.0f} kWh/year):")
    for city, solar in cities_energy.items():
        effective = solar * self_consumption_rate * total_efficiency
        coverage = (effective / annual_ev_demand) * 100
        panels = math.ceil(100 / coverage)
        print(f"  {city}: Realistic coverage={coverage:.1f}%, Panels needed={panels}")

# ============================================================
print("\n=== MONTHLY EV DEMAND (Average EV) ===")
for month, demand in zip(months, monthly_ev):
    print(f"{month}: EV demand = {demand:.1f} kWh")

print("\n=== MONTHLY SOLAR vs EV DEMAND ===")
print("Munich:")
for month, solar, ev in zip(months, monthly_solar_munich, monthly_ev):
    coverage = (solar / ev) * 100
    panels = math.ceil(100/coverage)
    print(f"  {month}: Solar={solar:.1f} kWh, EV={ev:.1f} kWh, Coverage={coverage:.1f}%, Panels={panels}")

print("\nFrankfurt:")
for month, solar, ev in zip(months, monthly_solar_frankfurt, monthly_ev):
    coverage = (solar / ev) * 100
    panels = math.ceil(100/coverage)
    print(f"  {month}: Solar={solar:.1f} kWh, EV={ev:.1f} kWh, Coverage={coverage:.1f}%, Panels={panels}")

print("\nHamburg:")
for month, solar, ev in zip(months, monthly_solar_hamburg, monthly_ev):
    coverage = (solar / ev) * 100
    panels = math.ceil(100/coverage)
    print(f"  {month}: Solar={solar:.1f} kWh, EV={ev:.1f} kWh, Coverage={coverage:.1f}%, Panels={panels}")
# ============================================================
# CHARTS
# ============================================================

# Chart 1 - Annual comparison
annual_solar_list = [Munich_energy, Frankfurt_energy, Hamburg_energy]
ev_demands_chart = {'Efficient EV': 2250, 'Average EV': 2700, 'Large EV': 3300}
cities_list = ['Munich', 'Frankfurt', 'Hamburg']

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

x = range(len(cities_list))
width = 0.25

for i, (ev_name, ev_demand) in enumerate(ev_demands_chart.items()):
    coverage_simple = [(solar / ev_demand) * 100 for solar in annual_solar_list]
    coverage_realistic = [(solar * self_consumption_rate * total_efficiency / ev_demand) * 100
                          for solar in annual_solar_list]
    axes[0].bar([xi + i * width for xi in x], coverage_simple, width=width, label=ev_name)
    axes[1].bar([xi + i * width for xi in x], coverage_realistic, width=width, label=ev_name)

for ax, title in zip(axes, ['Simple Coverage (no losses)', 'Realistic Coverage (with losses)']):
    ax.set_xticks([xi + width for xi in x])
    ax.set_xticklabels(cities_list)
    ax.set_title(title)
    ax.set_xlabel('City')
    ax.set_ylabel('Solar Coverage (%)')
    ax.axhline(y=100, color='red', linestyle='--', label='100% target')
    ax.legend()
    ax.grid(True)

plt.suptitle('Annual Solar Coverage of EV Demand — German Cities 2020', fontsize=14)
plt.tight_layout()
plt.savefig('annual_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Annual comparison chart saved!")

# Chart 2 - Monthly comparison
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(months, monthly_solar_munich.values, color='orange', marker='o', linewidth=2, label='Munich Solar')
ax.plot(months, monthly_solar_frankfurt.values, color='blue', marker='s', linewidth=2, label='Frankfurt Solar')
ax.plot(months, monthly_solar_hamburg.values, color='green', marker='^', linewidth=2, label='Hamburg Solar')
ax.plot(months, monthly_ev, color='red', linestyle='--', linewidth=2, label='Average EV Demand')
ax.set_title('Monthly Solar Production vs EV Demand — German Cities 2020')
ax.set_xlabel('Month')
ax.set_ylabel('Energy (kWh)')
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.savefig('monthly_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Monthly comparison chart saved!")

# Chart 3 - Panels needed
panels_munich = [math.ceil(ev / solar) for solar, ev in zip(monthly_solar_munich.values, monthly_ev)]
panels_frankfurt = [math.ceil(ev / solar) for solar, ev in zip(monthly_solar_frankfurt.values, monthly_ev)]
panels_hamburg = [math.ceil(ev / solar) for solar, ev in zip(monthly_solar_hamburg.values, monthly_ev)]

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(months, panels_munich, color='orange', marker='o', linewidth=2, label='Munich')
ax.plot(months, panels_frankfurt, color='blue', marker='s', linewidth=2, label='Frankfurt')
ax.plot(months, panels_hamburg, color='green', marker='^', linewidth=2, label='Hamburg')
ax.set_title('Panels Needed per Month — German Cities 2020')
ax.set_xlabel('Month')
ax.set_ylabel('Number of Panels')
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.savefig('panels_needed.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Panels needed chart saved!")

print("\n🎉 Complete EV Solar Analysis Done!")