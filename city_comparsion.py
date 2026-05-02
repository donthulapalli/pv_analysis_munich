from pvlib import location, irradiance
import pandas as pd 
import matplotlib.pyplot as plt
munich = {
    'latitude': 48.13,
    'longitude': 11.58,
    'altitude': 520,
    'name': 'Munich'
}
hamburg = {
    'latitude': 53.55,
    'longitude': 9.99,
    'altitude': 6,
    'name': 'Hamburg'
}
times = pd.date_range('2023-01-01', '2023-12-31', freq='1h', tz='Europe/Berlin')
def compare_locations(loc1, loc2):
    site1 = location.Location(loc1['latitude'], loc1['longitude'], tz='Europe/Berlin', altitude=loc1['altitude'], name=loc1['name'])
    site2 = location.Location(loc2['latitude'], loc2['longitude'], tz='Europe/Berlin', altitude=loc2['altitude'], name=loc2['name'])
    solar_position1 = site1.get_solarposition(times)
    solar_position2 = site2.get_solarposition(times)
    clear_sky1 = site1.get_clearsky(times)

    clear_sky2 = site2.get_clearsky(times)
    if clear_sky1['ghi'].mean() > clear_sky2['ghi'].mean():
        print(f"{loc1['name']} has better solar potential with an average GHI of {clear_sky1['ghi'].mean():.2f} W/m² compared to {loc2['name']} with {clear_sky2['ghi'].mean():.2f} W/m².")
    elif clear_sky1['ghi'].mean() < clear_sky2['ghi'].mean():
        print(f"{loc2['name']} has better solar potential with an average GHI of {clear_sky2['ghi'].mean():.2f} W/m² compared to {loc1['name']} with {clear_sky1['ghi'].mean():.2f} W/m².")
    else:
        print(f"Both locations have the same average GHI of {clear_sky1['ghi'].mean():.2f} W/m².")
    return(solar_position1, solar_position2, clear_sky1, clear_sky2)

surface_parameters = {
    'surface_tilt': 30,
    'surface_azimuth': 180
}
def calculate_poa_irradiance(solar_position, clear_sky, surface_parameters):
    poa_irradiance = irradiance.get_total_irradiance(
        surface_tilt=surface_parameters['surface_tilt'],
        surface_azimuth=surface_parameters['surface_azimuth'],
        dni=clear_sky['dni'],
        ghi=clear_sky['ghi'],
        dhi=clear_sky['dhi'],
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth']
    )
    return poa_irradiance
s = compare_locations(munich, hamburg)
poa_irradiance_munich = calculate_poa_irradiance(s[0], s[2], surface_parameters)
poa_irradiance_hamburg = calculate_poa_irradiance(s[1], s[3], surface_parameters)
print(poa_irradiance_munich.head(10))
print(poa_irradiance_hamburg.head(10))
