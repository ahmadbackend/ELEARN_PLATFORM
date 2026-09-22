"""
URL configuration for ELEARN_BACKEND.

The project is API-only: every page the user sees is served by the SPA in
ELEARN_FRONTEND/. Django exposes the JSON API, its OpenAPI docs, the admin and
(in DEBUG) the uploaded media files. In production media is served by nginx
straight off the shared volume.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('ELEARN_BACKEND.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# no-op when DEBUG is off; nginx serves /media/ from the volume instead
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
