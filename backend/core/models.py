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
    max_battery_charge_rate_kw = models.FloatField(default=100)
    max_battery_discharge_rate_kw = models.FloatField(default=100)
    co2_factor_kg_per_kwh = models.FloatField(default=0.72)

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
    artifact_path = models.CharField(max_length=255, blank=True, default="")

class Alert(models.Model):
    community = models.ForeignKey(Community, null=True, blank=True, on_delete=models.CASCADE)
    severity = models.CharField(max_length=10)
    title = models.CharField(max_length=120)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CommunityDevelopmentRequest(models.Model):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    STATUS_CHOICES = [(value, value.replace("_", " ").title()) for value in (PENDING, UNDER_REVIEW, MORE_INFORMATION_REQUIRED, APPROVED, REJECTED)]

    applicant_name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=30, blank=True)
    community_name = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    country = models.CharField(max_length=120, default="India")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    population = models.PositiveIntegerField(null=True, blank=True)
    solar_available = models.BooleanField(default=False)
    wind_available = models.BooleanField(default=False)
    battery_available = models.BooleanField(default=False)
    diesel_available = models.BooleanField(default=False)
    grid_available = models.BooleanField(default=False)
    other_infrastructure = models.CharField(max_length=500, blank=True)
    current_energy_situation = models.TextField(max_length=3000, blank=True)
    main_challenges = models.TextField(max_length=3000, blank=True)
    reason_for_request = models.TextField(max_length=3000)
    additional_information = models.TextField(max_length=3000, blank=True)
    status = models.CharField(max_length=35, choices=STATUS_CHOICES, default=PENDING)
    admin_notes = models.TextField(max_length=3000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_community_requests")
    created_community = models.OneToOneField(Community, null=True, blank=True, on_delete=models.SET_NULL, related_name="development_request")

    class Meta:
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["email", "created_at"])]

    @property
    def reference_id(self):
        return f"VEC-{self.created_at.year if self.created_at else 0:04d}-{self.pk:04d}"
