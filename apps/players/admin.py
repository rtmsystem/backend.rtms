"""
Admin configuration for PlayerProfile model.
"""
from django.contrib import admin

from .models import PlayerConsent, PlayerProfile


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    """Admin interface for PlayerProfile model."""
    
    list_display = [
        'full_name',
        'user',
        'email',
        'gender',
        'nationality',
        'created_at'
    ]
    
    list_filter = ['gender', 'nationality', 'created_at']
    
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'user__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'middle_name',
                'last_name',
                'short_bio',
                'long_description',
                'date_of_birth',
                'gender',
                'nationality'
            )
        }),
        ('Social Links', {
            'fields': (
                'instagram_url',
                'facebook_url',
                'linkedin_url'
            )
        }),
        ('Contact Information', {
            'fields': (
                'email',
                'phone',
                'document_type',
                'document_number'
            )
        }),
        ('Current Address', {
            'fields': (
                'street_number',
                'street_location',
                'city',
                'state',
                'country',
                'postal_code'
            )
        }),
        ('Physical Information', {
            'fields': (
                'height_cm',
                'weight_kg',
                'shirt_size',
                'handedness'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_first_name',
                'emergency_contact_last_name',
                'emergency_contact_phone',
                'emergency_contact_relationship'
            )
        }),
        ('Medical Information', {
            'fields': (
                'health_insurance',
                'blood_type',
                'medical_conditions'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PlayerConsent)
class PlayerConsentAdmin(admin.ModelAdmin):
    """Admin interface for PlayerConsent model."""
    
    list_display = [
        'profile',
        'accepted_privacy_policy',
        'privacy_policy_version',
        'accepted_terms',
        'terms_version',
        'consent_accepted_at',
        'consent_ip_address',
        'created_at'
    ]
    
    list_filter = [
        'accepted_privacy_policy',
        'accepted_terms',
        'privacy_policy_version',
        'terms_version',
        'consent_accepted_at',
        'created_at'
    ]
    
    search_fields = [
        'profile__first_name',
        'profile__last_name',
        'profile__email',
        'profile__user__email',
        'consent_ip_address'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Profile', {
            'fields': ('profile',)
        }),
        ('Privacy Policy', {
            'fields': (
                'accepted_privacy_policy',
                'privacy_policy_version',
            )
        }),
        ('Terms of Service', {
            'fields': (
                'accepted_terms',
                'terms_version',
            )
        }),
        ('Consent Information', {
            'fields': (
                'consent_accepted_at',
                'terms_accepted_at',
                'consent_ip_address',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

