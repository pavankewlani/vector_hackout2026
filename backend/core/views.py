from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
import json
from django.db.models import Avg, Sum
from django.utils import timezone
from optimizer.engine import dispatch_energy
from .access import api_login_required, community_access_required, visible_communities
from .models import Alert, Community, EnergyReading, UserProfile
from forecasting.services.forecasting_service import latest_model_summary, train_models

COMMUNITIES = [
    {"id": 1, "name": "Rampur", "district": "Kutch", "state": "Gujarat", "lat": 23.73, "lng": 69.86, "demand": 100, "solar": 60, "wind": 25, "battery": 72, "status": "NORMAL", "renewable": 85},
    {"id": 2, "name": "Devgarh", "district": "Udaipur", "state": "Rajasthan", "lat": 24.58, "lng": 73.71, "demand": 132, "solar": 74, "wind": 32, "battery": 64, "status": "NORMAL", "renewable": 81},
    {"id": 3, "name": "Lakshmi Nagar", "district": "Koraput", "state": "Odisha", "lat": 18.81, "lng": 82.71, "demand": 88, "solar": 46, "wind": 18, "battery": 48, "status": "WARNING", "renewable": 73},
    {"id": 4, "name": "Bharatpur", "district": "Churu", "state": "Rajasthan", "lat": 27.22, "lng": 74.69, "demand": 156, "solar": 58, "wind": 28, "battery": 19, "status": "CRITICAL", "renewable": 55},
    {"id": 5, "name": "Surajpur", "district": "Bastar", "state": "Chhattisgarh", "lat": 21.19, "lng": 81.35, "demand": 112, "solar": 68, "wind": 21, "battery": 79, "status": "NORMAL", "renewable": 88},
]

@require_GET
@api_login_required
def dashboard(request):
    communities = list(visible_communities(request.user).values("id", "name", "district", "state", "latitude", "longitude", "average_demand_kw", "solar_capacity_kw", "wind_capacity_kw", "battery_minimum_percentage", "status"))
    readings = EnergyReading.objects.filter(community_id__in=[item["id"] for item in communities])
    latest = {}
    for reading in readings.order_by("community_id", "-timestamp"):
        latest.setdefault(reading.community_id, reading)
    serialized = []
    for item in communities:
        reading = latest.get(item["id"])
        serialized.append({**item, "lat": item.pop("latitude"), "lng": item.pop("longitude"), "demand": reading.demand_kw if reading else item["average_demand_kw"], "solar": reading.solar_kw if reading else item["solar_capacity_kw"] * 0.6, "wind": reading.wind_kw if reading else item["wind_capacity_kw"] * 0.5, "battery": reading.battery_kw if reading else 50, "renewable": round(((reading.solar_kw + reading.wind_kw) / reading.demand_kw) * 100) if reading and reading.demand_kw else 75})
    if not serialized:
        return JsonResponse({"communities": [], "demo": False, "kpis": {}, "weather": {}, "models": {}})
    demand = sum(item["demand"] for item in serialized)
    renewable = sum(item["solar"] + item["wind"] for item in serialized)
    return JsonResponse({"communities": serialized, "demo": False, "kpis": {"demand_mw": round(demand / 1000, 2), "renewable_share": round(renewable / demand * 100) if demand else 0, "battery_health": round(sum(item["battery"] for item in serialized) / len(serialized)), "diesel_l": 0, "co2_saved_tons": 0}, "weather": {}, "models": {}, "alerts": Alert.objects.filter(community_id__in=[item["id"] for item in serialized], read=False).count()})

@require_POST
@api_login_required
def optimize(request):
    try:
        payload = json.loads(request.body or "{}")
        result = dispatch_energy(payload["demand"], payload["solar_available"], payload["wind_available"], payload["battery_percent"], payload.get("battery_minimum", 20), payload.get("diesel_price", 92))
        return JsonResponse(result)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return JsonResponse({"error": f"Invalid optimizer input: {error}"}, status=400)


@require_GET
@api_login_required
def communities(request):
    return JsonResponse({"communities": list(visible_communities(request.user).values())})


@require_GET
@api_login_required
def alerts(request):
    ids = visible_communities(request.user).values_list("id", flat=True)
    return JsonResponse({"alerts": list(Alert.objects.filter(community_id__in=ids).order_by("-created_at").values())})


@require_POST
@api_login_required
def mark_alert_read(request, alert_id):
    alert = Alert.objects.filter(pk=alert_id, community_id__in=visible_communities(request.user).values_list("id", flat=True)).first()
    if not alert:
        return JsonResponse({"detail": "Alert not found."}, status=404)
    alert.read = True
    alert.save(update_fields=["read"])
    return JsonResponse({"id": alert.id, "read": True})


@require_GET
@api_login_required
def forecast_models(request, community_id):
    if not visible_communities(request.user).filter(pk=community_id).exists():
        return JsonResponse({"detail": "You do not have access to this community."}, status=403)
    community = Community.objects.get(pk=community_id)
    return JsonResponse({"community": community.name, "models": latest_model_summary(community)})


@require_POST
@api_login_required
def train_forecast_models(request, community_id):
    if not visible_communities(request.user).filter(pk=community_id).exists():
        return JsonResponse({"detail": "You do not have access to this community."}, status=403)
    try:
        community = Community.objects.get(pk=community_id)
        return JsonResponse({"community": community.name, "results": train_models(community)})
    except Community.DoesNotExist:
        return JsonResponse({"detail": "Community not found."}, status=404)
    except ValueError as error:
        return JsonResponse({"detail": str(error)}, status=422)
    except RuntimeError as error:
        return JsonResponse({"detail": str(error)}, status=503)
