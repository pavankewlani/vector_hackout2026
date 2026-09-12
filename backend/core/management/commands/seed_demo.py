from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Community, UserProfile

COMMUNITIES = [
    ("Rampur", "Kutch", "Gujarat", 23.73, 69.86, 100, 60, 25, 500, 100, "NORMAL"),
    ("Devgarh", "Udaipur", "Rajasthan", 24.58, 73.71, 132, 74, 32, 600, 130, "NORMAL"),
    ("Lakshmi Nagar", "Koraput", "Odisha", 18.81, 82.71, 88, 46, 18, 400, 90, "WARNING"),
    ("Bharatpur", "Churu", "Rajasthan", 27.22, 74.69, 156, 58, 28, 700, 160, "CRITICAL"),
    ("Surajpur", "Bastar", "Chhattisgarh", 21.19, 81.35, 112, 68, 21, 550, 120, "NORMAL"),
]

class Command(BaseCommand):
    help = "Create VECTOR's clearly simulated demo communities and accounts."
    def handle(self, *args, **options):
        communities = []
        for values in COMMUNITIES:
            name, district, state, latitude, longitude, demand, solar, wind, battery, diesel, status = values
            community, _ = Community.objects.update_or_create(name=name, defaults={"district": district, "state": state, "latitude": latitude, "longitude": longitude, "average_demand_kw": demand, "solar_capacity_kw": solar, "wind_capacity_kw": wind, "battery_capacity_kwh": battery, "diesel_capacity_kw": diesel, "status": status})
            communities.append(community)
        admin, created = User.objects.get_or_create(username="admin@vector.local", defaults={"email": "admin@vector.local", "first_name": "Arjun", "last_name": "Kapoor"})
        if created:
            admin.set_password("VectorDemo!2026")
            admin.save()
        UserProfile.objects.update_or_create(user=admin, defaults={"role": UserProfile.ADMIN, "company": "VECTOR"})
        operator, created = User.objects.get_or_create(username="operator@vector.local", defaults={"email": "operator@vector.local", "first_name": "Mira", "last_name": "Shah"})
        if created:
            operator.set_password("VectorDemo!2026")
            operator.save()
        UserProfile.objects.update_or_create(user=operator, defaults={"role": UserProfile.OPERATOR, "company": "VECTOR", "assigned_community": communities[0]})
        self.stdout.write(self.style.SUCCESS("Seeded 5 simulated communities and demo admin/operator accounts."))
