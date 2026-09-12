from datetime import date, datetime, timedelta, timezone
import requests
from django.conf import settings
from django.utils import timezone
from core.models import Community, WeatherForecast, WeatherReading

HOURLY = "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m,shortwave_radiation"

def _validate(community, start, end):
    if not (-90 <= community.latitude <= 90 and -180 <= community.longitude <= 180):
        raise ValueError("Community coordinates are invalid.")
    if start > end or (end - start).days > 366:
        raise ValueError("Date range must be valid and no longer than one year.")

def fetch_historical_weather(community: Community, start: date, end: date):
    _validate(community, start, end)
    response = requests.get(f"{settings.OPEN_METEO_BASE_URL}/archive", params={"latitude": community.latitude, "longitude": community.longitude, "start_date": start.isoformat(), "end_date": end.isoformat(), "hourly": HOURLY, "timezone": "UTC"}, timeout=20)
    response.raise_for_status()
    payload = response.json().get("hourly", {})
    times = payload.get("time", [])
    fields = {"temperature": payload.get("temperature_2m", []), "humidity": payload.get("relative_humidity_2m", []), "precipitation": payload.get("precipitation", []), "cloud_cover": payload.get("cloud_cover", []), "wind_speed": payload.get("wind_speed_10m", []), "wind_direction": payload.get("wind_direction_10m", []), "solar_radiation": payload.get("shortwave_radiation", [])}
    for index, raw_time in enumerate(times):
        timestamp = datetime.fromisoformat(raw_time).replace(tzinfo=timezone.utc)
        values = {name: values[index] if index < len(values) else None for name, values in fields.items()}
        WeatherReading.objects.update_or_create(community=community, timestamp=timestamp, defaults=values)
    return len(times)

def fetch_forecast(community: Community):
    response = requests.get(f"{settings.OPEN_METEO_BASE_URL}/forecast", params={"latitude": community.latitude, "longitude": community.longitude, "hourly": HOURLY, "forecast_days": 7, "timezone": "UTC"}, timeout=20)
    response.raise_for_status()
    payload = response.json().get("hourly", {})
    times = payload.get("time", [])
    fields = {"temperature": payload.get("temperature_2m", []), "humidity": payload.get("relative_humidity_2m", []), "precipitation": payload.get("precipitation", []), "cloud_cover": payload.get("cloud_cover", []), "wind_speed": payload.get("wind_speed_10m", []), "wind_direction": payload.get("wind_direction_10m", []), "solar_radiation": payload.get("shortwave_radiation", [])}
    for index, raw_time in enumerate(times):
        timestamp = datetime.fromisoformat(raw_time).replace(tzinfo=timezone.utc)
        values = {name: values[index] if index < len(values) else None for name, values in fields.items()}
        WeatherForecast.objects.update_or_create(community=community, timestamp=timestamp, defaults=values)
    return list(WeatherForecast.objects.filter(community=community, timestamp__gte=timezone.now()).order_by("timestamp").values())
