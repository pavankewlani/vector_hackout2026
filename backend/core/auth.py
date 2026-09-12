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
