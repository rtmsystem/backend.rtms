"""
Admin configuration for geographical models.
"""
from django.contrib import admin

from .models import Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin interface for Country model."""
    list_display = ['id', 'name', 'phone_code', 'flag']
    list_filter = ['name']
    search_fields = ['name', 'phone_code']
    ordering = ['name']

