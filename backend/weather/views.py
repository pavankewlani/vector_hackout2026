from datetime import date, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from core.models import Community, WeatherForecast, WeatherReading
from .services.open_meteo import fetch_forecast, fetch_historical_weather
from forecasting.services.renewable_forecast import renewable_forecast
from core.access import community_access_required

def _community_or_404(community_id):
    return Community.objects.get(pk=community_id)

@require_GET
@community_access_required
def forecast(request, community_id):
    try:
        community = _community_or_404(community_id)
        rows = list(WeatherForecast.objects.filter(community=community, timestamp__gte=timezone.now()).order_by("timestamp").values())
        source = "database"
        if not rows:
            rows = fetch_forecast(community)
            source = "open-meteo"
        return JsonResponse({"community": community.name, "source": source, "forecast": rows})
    except Community.DoesNotExist:
        return JsonResponse({"error": "Community not found."}, status=404)
    except Exception:
        return JsonResponse({"error": "Forecast unavailable. No live weather data was returned."}, status=503)

@require_GET
@community_access_required
def history(request, community_id):
    try:
        community = _community_or_404(community_id)
        rows = list(WeatherReading.objects.filter(community=community).order_by("-timestamp").values()[:1000])
        if not rows:
            end = date.today() - timedelta(days=1)
            start = end - timedelta(days=7)
            fetch_historical_weather(community, start, end)
            rows = list(WeatherReading.objects.filter(community=community).order_by("-timestamp").values()[:1000])
        return JsonResponse({"community": community.name, "source": "database", "history": rows})
    except Community.DoesNotExist:
        return JsonResponse({"error": "Community not found."}, status=404)
    except Exception:
        return JsonResponse({"error": "Historical weather unavailable."}, status=503)


@require_GET
@community_access_required
def renewable(request, community_id):
    try:
        community = _community_or_404(community_id)
        return JsonResponse({"community": community.name, "forecast": renewable_forecast(community)})
    except Community.DoesNotExist:
        return JsonResponse({"error": "Community not found."}, status=404)
    except Exception:
        return JsonResponse({"error": "Renewable generation forecast unavailable."}, status=503)
