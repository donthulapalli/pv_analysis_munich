from pvlib import location, irradiance, pvsystem, modelchain
import pandas as pd
import matplotlib.pyplot as plt
loc1 = {'latitude': 40.7128, 'longitude': -74.0060, 'altitude': 10, 'name': 'New York City'}
loc2 = {'latitude': 34.0522, 'longitude': -118.2437, 'altitude': 10, 'name': 'Los Angeles'}
times = pd.date_range('2024-01-01', end='2024-12-31', freq='1h', tz='UTC')
def monthly_energy_production(loc1,loc2,times):
    site1= location.Location(loc1['latitude'], loc1['longitude'], altitude =loc1['altitude'], name=loc1['name'])
    site2= location.Location(loc2['latitude'], loc2['longitude'], altitude =loc2['altitude'], name=loc2['name'])
    solpos1 = site1.get_solarposition(times)
    solpos2 = site2.get_solarposition(times)
    clear_sky1 = site1.get_clearsky(times)
    clear_sky2 = site2.get_clearsky(times)
    if clear_sky1['ghi'].mean() > clear_sky2['ghi'].mean():
        print(f"{loc1['name']} has higher average GHI: {clear_sky1['ghi'].mean():.2f} W/m²")
    else:        
        print(f"{loc2['name']} has higher average GHI: {clear_sky2['ghi'].mean():.2f} W/m²")
    return(solpos1, solpos2, clear_sky1, clear_sky2, site1, site2)
surface_parameters = {'surface_tilt': 30, 'surface_azimuth': 180}

module_parameters = {'pdc0': 300, 'gamma_pdc': -0.004}
inverter_parameters = {'pdc0': 300, 'gamma_pdc': -0.004}
def calculate_energy_production(module_parameters, inverter_parameters, surface_parameters, clear_sky1, clear_sky2, site1, site2):
    system = pvsystem.PVSystem(
        surface_tilt=surface_parameters['surface_tilt'],
        surface_azimuth=surface_parameters['surface_azimuth'],
        module_parameters=module_parameters,
        inverter_parameters=inverter_parameters,
        racking_model='open_rack',
        module_type='glass_polymer' 
    )
    weather1 = pd.DataFrame({
        'dni': clear_sky1['dni'],
        'ghi': clear_sky1['ghi'],
        'dhi': clear_sky1['dhi'],
       'wind_speed': 4,
        'temp_air': 10})
    weather2 = pd.DataFrame({
        'dni': clear_sky2['dni'],
        'ghi': clear_sky2['ghi'],
        'dhi': clear_sky2['dhi'],
       'wind_speed': 4,
        'temp_air': 10})
    mc_1 = modelchain.ModelChain(system, site1, aoi_model='no_loss', spectral_model='no_loss')
    mc_2 = modelchain.ModelChain(system, site2, aoi_model='no_loss', spectral_model='no_loss')

    mc_1.run_model(weather1)
    mc_2.run_model(weather2)
    energy_production1 = mc_1.results.ac.sum()/1000 # Convert Wh to kWh
    energy_production2= mc_2.results.ac.sum()/1000 # Convert Wh to kWh
    return energy_production1, energy_production2
solpos1, solpos2, clear_sky1, clear_sky2, site1, site2 = monthly_energy_production(loc1, loc2, times)

#poa_irradiance1 = calculate_poa_irradiance(s[0], s[2], surface_parameters)

energy1, energy2 = calculate_energy_production(module_parameters, inverter_parameters, surface_parameters, clear_sky1, clear_sky2, site1, site2)
print(f"Estimated annual energy production for {loc1['name']}: {energy1:.2f} kWh")
print(f"Estimated annual energy production for {loc2['name']}: {energy2:.2f} kWh")  



    

