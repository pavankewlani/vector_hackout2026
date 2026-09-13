from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta
from django.db.models import Avg, Sum
from django.utils import timezone
from optimizer.engine import dispatch_energy
from .access import admin_required, api_login_required, community_access_required, visible_communities
from .models import Alert, Community, CommunityDevelopmentRequest, EnergyReading, OptimizationResult, UserProfile, ForecastModel
from .serializers import CommunityDevelopmentRequestSerializer
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
    request_counts = {status: CommunityDevelopmentRequest.objects.filter(status=status).count() for status, _ in CommunityDevelopmentRequest.STATUS_CHOICES}
    return JsonResponse({"communities": serialized, "demo": False, "kpis": {"demand_mw": round(demand / 1000, 2), "renewable_share": round(renewable / demand * 100) if demand else 0, "battery_health": round(sum(item["battery"] for item in serialized) / len(serialized)), "diesel_l": 0, "co2_saved_tons": 0}, "weather": {}, "models": {}, "alerts": Alert.objects.filter(community_id__in=[item["id"] for item in serialized], read=False).count(), "community_requests": request_counts})

@require_POST
@csrf_exempt
@api_login_required
def optimize(request):
    try:
        payload = json.loads(request.body or "{}")
        result = dispatch_energy(payload["demand"], payload["solar_available"], payload["wind_available"], payload["battery_percent"], payload.get("battery_minimum", 20), payload.get("diesel_price", 92), payload.get("forecast_solar", 0), payload.get("forecast_wind", 0), payload.get("forecast_demand"), payload.get("battery_capacity_kw"))
        if payload.get("community_id"):
            community = visible_communities(request.user).filter(pk=payload["community_id"]).first()
            if community:
                OptimizationResult.objects.create(community=community, demand_kw=payload["demand"], solar_kw=result["solar_kw"], wind_kw=result["wind_kw"], battery_kw=result["battery_kw"], diesel_kw=result["diesel_kw"], cost=result["cost_per_hour"], co2=result["co2_kg_per_hour"], recommendation=result["recommendation"])
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
    queryset = Alert.objects.filter(community_id__in=ids)
    if profile_for(request.user).role == UserProfile.ADMIN:
        queryset = Alert.objects.filter(community_id__in=ids) | Alert.objects.filter(community__isnull=True)
    return JsonResponse({"alerts": list(queryset.order_by("-created_at").values())})


@require_POST
@csrf_exempt
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
@csrf_exempt
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


@require_GET
@api_login_required
def reports(request):
    communities = visible_communities(request.user)
    ids = communities.values_list("id", flat=True)
    readings = EnergyReading.objects.filter(community_id__in=ids)
    optimizations = OptimizationResult.objects.filter(community_id__in=ids)
    total_demand = sum(row.demand_kw for row in readings)
    total_solar = sum(row.solar_kw for row in readings)
    total_wind = sum(row.wind_kw for row in readings)
    total_battery = sum(abs(row.battery_kw) for row in readings)
    total_diesel = sum(row.diesel_kw for row in readings)
    metrics = {
        "energy_generated_kwh": round(total_solar + total_wind + total_battery + total_diesel, 2),
        "solar_contribution_kwh": round(total_solar, 2),
        "wind_contribution_kwh": round(total_wind, 2),
        "battery_utilization_kwh": round(total_battery, 2),
        "diesel_consumption_kwh": round(total_diesel, 2),
        "estimated_cost": round(sum(row.cost for row in optimizations), 2),
        "co2_emissions_kg": round(sum(row.co2 for row in optimizations), 2),
        "renewable_percentage": round((total_solar + total_wind) / total_demand * 100, 2) if total_demand else 0,
    }
    models = list(ForecastModel.objects.filter(community_id__in=ids, selected=True).values("community_id", "model_name", "target_variable", "mae", "rmse", "model_version", "training_date"))
    history = list(optimizations.order_by("-timestamp").values("timestamp", "community_id", "demand_kw", "solar_kw", "wind_kw", "battery_kw", "diesel_kw", "cost", "co2", "recommendation")[:100])
    return JsonResponse({"metrics": metrics, "models": models, "optimization_history": history})


def _public_request_payload(request):
    serializer = CommunityDevelopmentRequestSerializer(data=json.loads(request.body or "{}"))
    if not serializer.is_valid():
        return None, JsonResponse({"errors": serializer.errors}, status=400)
    email = serializer.validated_data["email"]
    if CommunityDevelopmentRequest.objects.filter(email=email, created_at__gte=timezone.now() - timedelta(minutes=10)).exists():
        return None, JsonResponse({"detail": "A request was already submitted from this email recently."}, status=429)
    return serializer.save(), None


@require_POST
@csrf_exempt
def community_request_create(request):
    try:
        record, error = _public_request_payload(request)
        if error:
            return error
        Alert.objects.create(title="New Community Development Request", severity="INFO", message=f"{record.community_name}, {record.state} has requested VECTOR support.")
        return JsonResponse({"message": "Your community development request has been submitted successfully.", "request_id": record.reference_id, "community_name": record.community_name, "status": record.status, "submitted_at": record.created_at}, status=201)
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)


@require_GET
def community_request_status(request):
    reference_id, email = request.GET.get("request_id", ""), request.GET.get("email", "")
    record = next((item for item in CommunityDevelopmentRequest.objects.filter(email__iexact=email) if item.reference_id == reference_id), None)
    if not record:
        return JsonResponse({"detail": "Request not found."}, status=404)
    return JsonResponse({"request_id": record.reference_id, "community_name": record.community_name, "status": record.status, "updated_at": record.updated_at, "submitted_at": record.created_at})


@require_GET
@admin_required
def community_requests(request):
    queryset = CommunityDevelopmentRequest.objects.all().order_by("-created_at")
    status = request.GET.get("status")
    search = request.GET.get("search", "").strip()
    if status:
        queryset = queryset.filter(status=status)
    if search:
        from django.db.models import Q
        queryset = queryset.filter(Q(community_name__icontains=search) | Q(district__icontains=search) | Q(state__icontains=search) | Q(applicant_name__icontains=search))
    return JsonResponse({"requests": [{**CommunityDevelopmentRequestSerializer(item).data, "request_id": item.reference_id} for item in queryset]})


@require_GET
@admin_required
def community_request_detail(request, request_id):
    record = CommunityDevelopmentRequest.objects.filter(pk=request_id).first()
    if not record:
        return JsonResponse({"detail": "Request not found."}, status=404)
    return JsonResponse(CommunityDevelopmentRequestSerializer(record).data)


@require_POST
@csrf_exempt
@admin_required
def community_request_action(request, request_id):
    record = CommunityDevelopmentRequest.objects.filter(pk=request_id).first()
    if not record:
        return JsonResponse({"detail": "Request not found."}, status=404)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)
    action_status = payload.get("status")
    if action_status not in dict(CommunityDevelopmentRequest.STATUS_CHOICES):
        return JsonResponse({"detail": "Invalid request status."}, status=400)
    record.status = action_status
    record.admin_notes = payload.get("admin_notes", record.admin_notes)
    record.reviewed_by = request.user
    record.reviewed_at = timezone.now()
    record.save(update_fields=["status", "admin_notes", "reviewed_by", "reviewed_at", "updated_at"])
    return JsonResponse(CommunityDevelopmentRequestSerializer(record).data)


@require_POST
@csrf_exempt
@admin_required
def community_request_convert(request, request_id):
    record = CommunityDevelopmentRequest.objects.filter(pk=request_id).first()
    if not record:
        return JsonResponse({"detail": "Request not found."}, status=404)
    if record.status != CommunityDevelopmentRequest.APPROVED:
        return JsonResponse({"detail": "Only approved requests can be converted."}, status=409)
    if record.created_community_id:
        return JsonResponse({"community_id": record.created_community_id, "detail": "Community already created."})
    community = Community.objects.create(name=record.community_name, district=record.district, state=record.state, latitude=record.latitude or 0, longitude=record.longitude or 0, solar_capacity_kw=0, wind_capacity_kw=0, battery_capacity_kwh=0, diesel_capacity_kw=0)
    record.created_community = community
    record.save(update_fields=["created_community", "updated_at"])
    return JsonResponse({"community_id": community.id, "community_name": community.name, "detail": "Community created. Configure its microgrid capacities before connecting services."}, status=201)
