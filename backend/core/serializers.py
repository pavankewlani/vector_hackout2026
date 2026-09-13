from rest_framework import serializers
from .models import Community, Alert, CommunityDevelopmentRequest

class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = "__all__"

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = "__all__"


class CommunityDevelopmentRequestSerializer(serializers.ModelSerializer):
    reference_id = serializers.ReadOnlyField()

    class Meta:
        model = CommunityDevelopmentRequest
        fields = ["id", "reference_id", "applicant_name", "email", "phone", "community_name", "district", "state", "country", "latitude", "longitude", "population", "solar_available", "wind_available", "battery_available", "diesel_available", "grid_available", "other_infrastructure", "current_energy_situation", "main_challenges", "reason_for_request", "additional_information", "status", "admin_notes", "created_at", "updated_at", "reviewed_at", "reviewed_by", "created_community"]
        read_only_fields = ["status", "admin_notes", "created_at", "updated_at", "reviewed_at", "reviewed_by", "created_community"]

    def validate(self, attrs):
        latitude, longitude = attrs.get("latitude"), attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("Latitude and longitude must be provided together.")
        if latitude is not None and not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise serializers.ValidationError("Coordinates are outside valid geographic ranges.")
        return attrs
