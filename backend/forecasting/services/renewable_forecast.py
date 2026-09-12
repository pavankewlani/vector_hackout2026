def solar_generation_kw(solar_radiation, cloud_cover, capacity_kw, temperature=25):
    irradiance_factor = max(0, min(float(solar_radiation or 0) / 1000, 1))
    cloud_factor = max(0, 1 - float(cloud_cover or 0) / 100)
    temperature_factor = max(0.85, 1 - max(float(temperature) - 25, 0) * 0.004)
    return round(capacity_kw * irradiance_factor * cloud_factor * temperature_factor, 2)

def wind_generation_kw(wind_speed, capacity_kw):
    speed = max(float(wind_speed or 0), 0)
    if speed < 3 or speed >= 25:
        return 0.0 if speed < 3 else round(capacity_kw, 2)
    return round(capacity_kw * min(((speed - 3) / 12) ** 3, 1), 2)
