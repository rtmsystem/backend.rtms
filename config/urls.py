"""
URL configuration for RTMS project.
"""
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="RTMS API",
        default_version='v1',
        description="API documentation for RTMS - Real-Time Management System",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@rtms.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation - swagger/ debe ir antes de swagger<format>/
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path('api/', include('apps.api.urls')),
]

