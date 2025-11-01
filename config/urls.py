from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def live(_):  return JsonResponse({"status": "ok"})
def ready(_): return JsonResponse({"status": "ok"})

# --- v1 patterns (all versioned) ---
api_v1_patterns = [
    path("auth/", include("accounts.api.v1.urls")),
    path("orgs/", include("orgs.api.v1.urls")),
    path("rooms/", include("rooms.api.v1.urls")),
    path("messages/", include("messages_app.api.v1.urls")),
    path("uploads/", include("uploads.api.v1.urls")),         # versioned
    path("webhooks/", include("webhooks.api.v1.urls")),       # versioned
    path("notifications/", include("notifications.api.v1.urls")),  # versioned

    # JWT under v1
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

def api_version_not_found(request, version, *args, **kwargs):
    return JsonResponse({"detail": f"Unknown API version: {version}"}, status=404)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live", live),
    path("health/ready", ready),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),

    # Only here; no legacy '', no 'api/'
    path("api/v1/", include(api_v1_patterns)),

    # Optional: return 404 for future versions until implemented
    re_path(r"^api/(?P<version>v[0-9]+)/", api_version_not_found),
]

# Serve media files in development (for local file storage)
if settings.DEBUG and not settings.USE_AWS_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
