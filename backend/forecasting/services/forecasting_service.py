from django.db import transaction
from django.utils import timezone

from core.models import ForecastModel, WeatherReading
from .evaluator import select_best

TARGETS = ("temperature", "wind_speed", "solar_radiation")


def train_models(community):
    try:
        from .lstm_model import train_lstm
        from .xgboost_model import train_xgboost
    except ImportError as error:
        raise RuntimeError("Install the ML dependencies from requirements.txt before training models.") from error
    readings = WeatherReading.objects.filter(community=community).order_by("timestamp")
    results = []
    for target in TARGETS:
        metrics = {}
        try:
            _, _, metrics["xgboost"] = train_xgboost(readings, target)
        except (ValueError, TypeError):
            raise
        try:
            _, _, metrics["lstm"] = train_lstm(readings, target)
        except RuntimeError:
            metrics["lstm"] = None
        available = {name: value for name, value in metrics.items() if value}
        selected = select_best(available) if available else None
        with transaction.atomic():
            ForecastModel.objects.filter(community=community, target_variable=target).update(selected=False)
            for name, value in available.items():
                ForecastModel.objects.create(community=community, model_name=name.upper(), target_variable=target, mae=value["mae"], rmse=value["rmse"], selected=name == selected, model_version="v1")
        results.append({"target_variable": target, "metrics": metrics, "selected_model": selected})
    return results


def latest_model_summary(community):
    rows = ForecastModel.objects.filter(community=community).order_by("target_variable", "-training_date")
    return list(rows.values("model_name", "target_variable", "training_date", "mae", "rmse", "selected", "model_version"))