from django.db import transaction
from django.utils import timezone
from pathlib import Path
import joblib
from django.conf import settings
from datetime import date, timedelta

from core.models import ForecastModel, WeatherReading
from weather.services.open_meteo import fetch_historical_weather
from .evaluator import select_best

TARGETS = ("temperature", "wind_speed", "solar_radiation")


def train_models(community):
    try:
        from .lstm_model import train_lstm
        from .xgboost_model import train_xgboost
    except ImportError as error:
        raise RuntimeError("Install the ML dependencies from requirements.txt before training models.") from error
    readings = WeatherReading.objects.filter(community=community).order_by("timestamp")
    if readings.count() < 96:
        end = date.today() - timedelta(days=1)
        try:
            fetch_historical_weather(community, end - timedelta(days=30), end)
        except (ValueError, OSError, RuntimeError) as error:
            raise RuntimeError(f"Unable to fetch historical weather for model training: {error}") from error
        except Exception as error:
            raise RuntimeError("Open-Meteo historical weather is unavailable for model training.") from error
        readings = WeatherReading.objects.filter(community=community).order_by("timestamp")
    results = []
    for target in TARGETS:
        metrics = {}
        trained = {}
        try:
            trained["xgboost"], _, metrics["xgboost"] = train_xgboost(readings, target)
        except (ValueError, TypeError):
            raise
        try:
            trained["lstm"], trained["lstm_scaler"], metrics["lstm"] = train_lstm(readings, target)
        except RuntimeError:
            metrics["lstm"] = None
        available = {name: value for name, value in metrics.items() if value}
        selected = select_best(available) if available else None
        with transaction.atomic():
            ForecastModel.objects.filter(community=community, target_variable=target).update(selected=False)
            artifact_dir = Path(settings.BASE_DIR) / "ml_models" / f"community_{community.pk}"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            for name, value in available.items():
                artifact_path = ""
                if name == "xgboost":
                    artifact_file = artifact_dir / f"{target}_xgboost.pkl"
                    features = [column for column in trained["xgboost"].feature_names_in_]
                    joblib.dump({"model": trained["xgboost"], "features": features}, artifact_file)
                    artifact_path = str(artifact_file.relative_to(settings.BASE_DIR))
                elif name == "lstm":
                    artifact_file = artifact_dir / f"{target}_lstm.keras" if hasattr(trained["lstm"], "save") else artifact_dir / f"{target}_lstm.pkl"
                    if hasattr(trained["lstm"], "save"):
                        trained["lstm"].save(artifact_file)
                    else:
                        joblib.dump(trained["lstm"], artifact_file)
                    joblib.dump(trained["lstm_scaler"], artifact_dir / f"{target}_lstm_scaler.pkl")
                    artifact_path = str(artifact_file.relative_to(settings.BASE_DIR))
                ForecastModel.objects.create(community=community, model_name=name.upper(), target_variable=target, mae=value["mae"], rmse=value["rmse"], selected=name == selected, model_version="v1" if name == "xgboost" or hasattr(trained.get(name), "save") else "v1-neural-fallback", artifact_path=artifact_path)
        results.append({"target_variable": target, "metrics": metrics, "selected_model": selected})
    return results


def latest_model_summary(community):
    rows = ForecastModel.objects.filter(community=community).order_by("target_variable", "-training_date")
    return list(rows.values("model_name", "target_variable", "training_date", "mae", "rmse", "selected", "model_version", "artifact_path"))