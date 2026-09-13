from datetime import timedelta

from django.utils import timezone

from core.models import Alert, WeatherForecast


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


def renewable_forecast(community, limit=48):
    rows = WeatherForecast.objects.filter(community=community, timestamp__gte=timezone.now()).order_by("timestamp")[:limit]
    forecast = []
    for row in rows:
        forecast.append({
            "timestamp": row.timestamp,
            "solar_kw": solar_generation_kw(row.solar_radiation, row.cloud_cover, community.solar_capacity_kw, row.temperature),
            "wind_kw": wind_generation_kw(row.wind_speed, community.wind_capacity_kw),
            "solar_radiation": row.solar_radiation,
            "wind_speed": row.wind_speed,
        })
    if forecast:
        _create_forecast_alerts(community, forecast)
    return forecast


def _create_forecast_alerts(community, forecast):
    if len(forecast) < 2:
        return
    current = forecast[0]["solar_kw"] + forecast[0]["wind_kw"]
    later = forecast[min(5, len(forecast) - 1)]["solar_kw"] + forecast[min(5, len(forecast) - 1)]["wind_kw"]
    if current and later < current * 0.62:
        recent = timezone.now() - timedelta(hours=6)
        if not Alert.objects.filter(community=community, title="Low renewable generation", created_at__gte=recent).exists():
            Alert.objects.create(community=community, severity="WARNING", title="Low renewable generation", message=f"Solar and wind generation is expected to decrease by {round((1 - later / current) * 100)}% in the next 6 hours. Recommendation: charge the battery while availability is high.")
