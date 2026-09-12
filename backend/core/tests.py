from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Community, UserProfile
from optimizer.engine import dispatch_energy


class AccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.first = Community.objects.create(name="A", district="D", state="S", latitude=10, longitude=20)
        self.second = Community.objects.create(name="B", district="D", state="S", latitude=11, longitude=21)
        self.admin = User.objects.create_user("admin@test", password="pass")
        UserProfile.objects.create(user=self.admin, role=UserProfile.ADMIN)
        self.operator = User.objects.create_user("operator@test", password="pass")
        UserProfile.objects.create(user=self.operator, role=UserProfile.OPERATOR, assigned_community=self.first)

    def test_dashboard_requires_authentication(self):
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 401)

    def test_operator_only_sees_assigned_community(self):
        self.client.force_login(self.operator)
        response = self.client.get("/api/communities/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["communities"]], [self.first.id])

    def test_operator_cannot_read_other_community_weather(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(f"/api/weather/{self.second.id}/forecast/").status_code, 403)


class OptimizerTests(TestCase):
    def test_dispatch_meets_demand_and_prioritizes_renewables(self):
        result = dispatch_energy(100, 60, 25, 80, 20, 92)
        total = result["solar_kw"] + result["wind_kw"] + result["battery_kw"] + result["diesel_kw"]
        self.assertGreaterEqual(total, 100)
        self.assertEqual(result["diesel_kw"], 0)