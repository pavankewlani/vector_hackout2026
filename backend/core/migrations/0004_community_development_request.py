from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0003_forecastmodel_artifact_path"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.AddField(model_name="community", name="co2_factor_kg_per_kwh", field=models.FloatField(default=0.72)),
        migrations.AddField(model_name="community", name="max_battery_charge_rate_kw", field=models.FloatField(default=100)),
        migrations.AddField(model_name="community", name="max_battery_discharge_rate_kw", field=models.FloatField(default=100)),
        migrations.CreateModel(
            name="CommunityDevelopmentRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("applicant_name", models.CharField(max_length=120)), ("email", models.EmailField(max_length=254)), ("phone", models.CharField(blank=True, max_length=30)),
                ("community_name", models.CharField(max_length=120)), ("district", models.CharField(max_length=120)), ("state", models.CharField(max_length=120)), ("country", models.CharField(default="India", max_length=120)),
                ("latitude", models.FloatField(blank=True, null=True)), ("longitude", models.FloatField(blank=True, null=True)), ("population", models.PositiveIntegerField(blank=True, null=True)),
                ("solar_available", models.BooleanField(default=False)), ("wind_available", models.BooleanField(default=False)), ("battery_available", models.BooleanField(default=False)), ("diesel_available", models.BooleanField(default=False)), ("grid_available", models.BooleanField(default=False)),
                ("other_infrastructure", models.CharField(blank=True, max_length=500)), ("current_energy_situation", models.TextField(blank=True, max_length=3000)), ("main_challenges", models.TextField(blank=True, max_length=3000)), ("reason_for_request", models.TextField(max_length=3000)), ("additional_information", models.TextField(blank=True, max_length=3000)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("UNDER_REVIEW", "Under Review"), ("MORE_INFORMATION_REQUIRED", "More Information Required"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=35)), ("admin_notes", models.TextField(blank=True, max_length=3000)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_community", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="development_request", to="core.community")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_community_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["status", "created_at"], name="core_commun_status_53f4cb_idx"), models.Index(fields=["email", "created_at"], name="core_commun_email_139397_idx")]},
        ),
    ]