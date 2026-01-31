"""
Admin configuration for tournaments app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Tournament, TournamentDivision, Involvement, InvolvementStatus,
    TournamentGroup, GroupStanding
)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """Admin configuration for Tournament model."""
    
    list_display = [
        'name', 'organization', 'status', 'start_date', 
        'end_date', 'is_active', 'created_at'
    ]
    
    list_filter = [
        'status', 'is_active', 'organization', 'start_date',
        'created_at', 'country', 'city'
    ]
    
    search_fields = [
        'name', 'description', 'contact_name', 'contact_email',
        'city', 'country', 'organization__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'organization', 'logo')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_phone', 'contact_email')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'registration_deadline')
        }),
        ('Location', {
            'fields': (
                'address', 'street_number', 'street_location',
                'city', 'state', 'country', 'postal_code'
            )
        }),
        ('Status & Metadata', {
            'fields': ('status', 'is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    raw_id_fields = ['organization', 'created_by']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('organization', 'created_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating a new tournament."""
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TournamentDivision)
class TournamentDivisionAdmin(admin.ModelAdmin):
    """Admin configuration for TournamentDivision model."""
    
    list_display = [
        'name', 'tournament', 'format', 'participant_type',
        'gender', 'max_participants', 'is_active'
    ]
    
    list_filter = [
        'format', 'participant_type', 'gender', 'is_active',
        'tournament__organization', 'tournament__status'
    ]
    
    search_fields = [
        'name', 'description', 'tournament__name',
        'tournament__organization__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'tournament')
        }),
        ('Configuration', {
            'fields': ('format', 'participant_type', 'gender', 'max_participants')
        }),
        ('Age Restriction', {
            'fields': ('born_after',)
        }),
        ('Status & Metadata', {
            'fields': ('is_active','is_published','published_at', 'published_by', 'created_at', 'updated_at')
        }),
    )
    
    raw_id_fields = ['tournament']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('tournament', 'tournament__organization')


@admin.register(Involvement)
class InvolvementAdmin(admin.ModelAdmin):
    """Admin configuration for Involvement model."""
    
    list_display = [
        'player', 'partner', 'tournament', 'division', 'status', 'paid',
        'created_at', 'approved_at'
    ]
    
    list_filter = [
        'status', 'paid', 'tournament', 'division',
        'division__participant_type', 'created_at', 'approved_at'
    ]
    
    search_fields = [
        'player__email', 'player__first_name', 'player__last_name',
        'partner__email', 'partner__first_name', 'partner__last_name',
        'tournament__name', 'division__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tournament',  'player', 'partner', 'division')
        }),
        ('Status', {
            'fields': ('status', 'paid',)
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('knockout_points', {
            'fields': ('knockout_points',)
        })
    )
    
    raw_id_fields = ['player', 'partner', 'tournament', 'division', 'approved_by']
    
    actions = ['approve_selected', 'reject_selected', 'mark_as_paid', 'mark_as_unpaid']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'player', 'partner', 'tournament', 'division', 'approved_by'
        )
    
    def approve_selected(self, request, queryset):
        """Approve selected involvements."""
        for involvement in queryset:
            involvement.approve(user=request.user)
        self.message_user(request, f'{queryset.count()} involvements approved.')
    approve_selected.short_description = 'Approve selected involvements'
    
    def reject_selected(self, request, queryset):
        """Reject selected involvements."""
        count = 0
        for involvement in queryset:
            involvement.reject()
            count += 1
        self.message_user(request, f'{count} involvements rejected.')
    reject_selected.short_description = 'Reject selected involvements'
    
    def mark_as_paid(self, request, queryset):
        """Mark selected involvements as paid."""
        queryset.update(paid=True)
        self.message_user(request, f'{queryset.count()} involvements marked as paid.')
    mark_as_paid.short_description = 'Mark as paid'
    
    def mark_as_unpaid(self, request, queryset):
        """Mark selected involvements as unpaid."""
        queryset.update(paid=False)
        self.message_user(request, f'{queryset.count()} involvements marked as unpaid.')
    mark_as_unpaid.short_description = 'Mark as unpaid'


class GroupStandingInline(admin.TabularInline):
    """Inline administration for GroupStanding."""
    model = GroupStanding
    extra = 0
    raw_id_fields = ['involvement']
    fields = [
        'involvement', 'matches_played', 'matches_won', 'matches_lost',
        'sets_won', 'sets_lost', 'points', 'position_in_group'
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TournamentGroup)
class TournamentGroupAdmin(admin.ModelAdmin):
    """Admin configuration for TournamentGroup model."""
    
    list_display = [
        'name', 'division', 'group_number', 'participant_count', 'created_at'
    ]
    
    list_filter = [
        'division__tournament',
        'division'
    ]
    
    search_fields = [
        'name', 'division__name', 'division__tournament__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [GroupStandingInline]
    
    raw_id_fields = ['division']