"""
Geographical app configuration.
"""
from django.apps import AppConfig


class GeographicalConfig(AppConfig):
    """Configuration for geographical app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.geographical'
    verbose_name = 'Geographical'

