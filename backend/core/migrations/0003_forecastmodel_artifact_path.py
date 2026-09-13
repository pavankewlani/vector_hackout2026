from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_weatherforecast_userprofile_forecastmodel_alert_and_more")]

    operations = [migrations.AddField(model_name="forecastmodel", name="artifact_path", field=models.CharField(blank=True, default="", max_length=255))]