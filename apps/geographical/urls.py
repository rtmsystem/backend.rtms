"""
URL configuration for geographical app.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CountryViewSet

app_name = 'geographical'

# Router for viewsets
router = DefaultRouter()
router.register(r'countries', CountryViewSet, basename='country')

urlpatterns = router.urls

