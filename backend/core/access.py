from functools import wraps

from django.http import JsonResponse
from core.models import Community, UserProfile
from rest_framework_simplejwt.authentication import JWTAuthentication


def authenticate_request(request):
    if request.user.is_authenticated:
        return request.user
    try:
        result = JWTAuthentication().authenticate(request)
    except Exception:
        result = None
    if result:
        request.user, request.auth = result
    return request.user


def profile_for(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not authenticate_request(request).is_authenticated:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
        return view(request, *args, **kwargs)
    return wrapped


def visible_communities(user):
    profile = profile_for(user)
    if profile.role == UserProfile.ADMIN:
        return Community.objects.all()
    if profile.assigned_community_id:
        return Community.objects.filter(pk=profile.assigned_community_id)
    return Community.objects.none()


def community_access_required(view):
    @wraps(view)
    def wrapped(request, community_id, *args, **kwargs):
        if not authenticate_request(request).is_authenticated:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
        if not visible_communities(request.user).filter(pk=community_id).exists():
            return JsonResponse({"detail": "You do not have access to this community."}, status=403)
        return view(request, community_id, *args, **kwargs)
    return wrapped