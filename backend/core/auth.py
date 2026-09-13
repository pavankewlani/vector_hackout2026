from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        user = authenticate(username=request.data.get("email"), password=request.data.get("password"))
        if not user:
            return Response({"detail": "Invalid email or password."}, status=401)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh), "user": {"id": user.id, "email": user.email, "name": user.get_full_name(), "role": profile.role, "assigned_community": profile.assigned_community_id}})

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response({"id": request.user.id, "email": request.user.email, "name": request.user.get_full_name(), "role": profile.role, "assigned_community": profile.assigned_community_id})
    
    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user = request.user
        email = request.data.get("email", user.email).strip()
        first_name = request.data.get("first_name", user.first_name).strip()
        last_name = request.data.get("last_name", user.last_name).strip()
        if not email:
            return Response({"detail": "Email is required."}, status=400)
        user.email = email
        user.username = email
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["email", "username", "first_name", "last_name"])
        return Response({"id": user.id, "email": user.email, "name": user.get_full_name(), "first_name": user.first_name, "last_name": user.last_name, "role": profile.role, "company": profile.company, "assigned_community": profile.assigned_community_id})
