from django.conf import settings
from django.db import models

class Community(models.Model):
    name = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, default="NORMAL")
    average_demand_kw = models.FloatField(default=100)
    solar_capacity_kw = models.FloatField(default=100)
    wind_capacity_kw = models.FloatField(default=50)
    battery_capacity_kwh = models.FloatField(default=500)
    diesel_capacity_kw = models.FloatField(default=100)
    battery_minimum_percentage = models.FloatField(default=20)
    diesel_fuel_price = models.FloatField(default=92)

class EnergyReading(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    demand_kw = models.FloatField()
    solar_kw = models.FloatField()
    wind_kw = models.FloatField()
    battery_kw = models.FloatField()
    diesel_kw = models.FloatField()

class OptimizationResult(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    demand_kw = models.FloatField()
    solar_kw = models.FloatField()
    wind_kw = models.FloatField()
    battery_kw = models.FloatField()
    diesel_kw = models.FloatField()
    cost = models.FloatField()
    co2 = models.FloatField()
    recommendation = models.TextField()

class UserProfile(models.Model):
    ADMIN = "COMPANY_ADMIN"
    OPERATOR = "COMMUNITY_OPERATOR"
    ROLE_CHOICES = [(ADMIN, "Company admin"), (OPERATOR, "Community operator")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=OPERATOR)
    company = models.CharField(max_length=120, default="VECTOR")
    assigned_community = models.ForeignKey(Community, null=True, blank=True, on_delete=models.SET_NULL)

class WeatherReading(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="weather_readings")
    timestamp = models.DateTimeField()
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    cloud_cover = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.FloatField(null=True, blank=True)
    solar_radiation = models.FloatField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["community", "timestamp"], name="unique_weather_timestamp")]
        indexes = [models.Index(fields=["community", "timestamp"])]

class WeatherForecast(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="forecasts")
    timestamp = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now=True)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    cloud_cover = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.FloatField(null=True, blank=True)
    solar_radiation = models.FloatField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["community", "timestamp"], name="unique_forecast_timestamp")]

class ForecastModel(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=30)
    target_variable = models.CharField(max_length=40)
    training_date = models.DateTimeField(auto_now=True)
    mae = models.FloatField()
    rmse = models.FloatField()
    selected = models.BooleanField(default=False)
    model_version = models.CharField(max_length=40, default="v1")

class Alert(models.Model):
    community = models.ForeignKey(Community, null=True, blank=True, on_delete=models.CASCADE)
    severity = models.CharField(max_length=10)
    title = models.CharField(max_length=120)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
