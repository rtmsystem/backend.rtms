"""
Admin configuration for Organization model.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Organization

User = get_user_model()


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model."""
    
    list_display = [
        'name',
        'nit',
        'administrator_count',
        'created_by',
        'is_active',
        'created_at'
    ]
    
    list_filter = ['is_active', 'created_at']
    
    search_fields = ['name', 'nit']
    
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la Organización', {
            'fields': ('name', 'nit', 'is_active','logo')
        }),
        ('Usuarios', {
            'fields': ('administrators', 'created_by')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    filter_horizontal = ['administrators']
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Filter administrators to only show admin users."""
        if db_field.name == 'administrators':
            kwargs['queryset'] = User.objects.filter(role='admin')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def administrator_count(self, obj):
        """Display administrator count."""
        return obj.administrator_count
    administrator_count.short_description = 'Admins'

