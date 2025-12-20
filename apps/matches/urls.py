"""
URL configuration for matches app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "matches"

# Router for MatchViewSet
router = DefaultRouter()
router.register(r'', views.MatchViewSet, basename='match')

urlpatterns = [
    # Generate bracket endpoint (must be before router to avoid route conflicts)
    path('generate-bracket/', views.generate_bracket, name='generate-bracket'),
    
    # Router URLs (includes: list, create, retrieve, update, delete, scores)
    path('', include(router.urls)),
]