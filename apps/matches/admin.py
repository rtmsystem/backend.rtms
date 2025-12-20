"""
Admin configuration for matches app.
"""
from django.contrib import admin

from .models import Match, Set


class SetInline(admin.TabularInline):
    """Inline admin for Set model."""
    model = Set
    extra = 0
    readonly_fields = ['completed_at']
    fields = ['set_number', 'player1_score', 'player2_score', 'winner', 'completed_at']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    """Admin configuration for Match model."""
    
    list_display = [
        'match_code', 'division', 'match_type', 'status',
        'player1', 'player2', 'round_number', 'is_losers_bracket',
        'scheduled_at', 'created_at'
    ]
    
    list_filter = [
        'status', 'match_type', 'is_losers_bracket', 'division__tournament',
        'division', 'round_number', 'created_at', 'scheduled_at'
    ]
    
    search_fields = [
        'match_code', 'division__name', 'division__tournament__name',
        'player1__first_name', 'player1__last_name', 'player1__email',
        'player2__first_name', 'player2__last_name', 'player2__email',
        'partner1__first_name', 'partner1__last_name',
        'partner2__first_name', 'partner2__last_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('division', 'match_code', 'match_type', 'status')
        }),
        ('Players', {
            'fields': ('player1', 'player2', 'partner1', 'partner2')
        }),
        ('Match Configuration', {
            'fields': ('max_sets', 'points_per_set')
        }),
        ('Bracket Structure', {
            'fields': ('round_number', 'is_losers_bracket', 'next_match')
        }),
        ('Winner', {
            'fields': ('winner', 'winner_partner')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'started_at', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    raw_id_fields = [
        'division', 'player1', 'player2', 'partner1', 'partner2',
        'winner', 'winner_partner', 'next_match', 'created_by'
    ]
    
    inlines = [SetInline]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'division', 'division__tournament', 'player1', 'player2',
            'partner1', 'partner2', 'winner', 'created_by', 'next_match'
        ).prefetch_related('sets')
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating a new match."""
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    """Admin configuration for Set model."""
    
    list_display = [
        'match', 'set_number', 'player1_score', 'player2_score',
        'winner', 'completed_at'
    ]
    
    list_filter = [
        'match__division', 'match__division__tournament',
        'match__match_type', 'winner', 'completed_at'
    ]
    
    search_fields = [
        'match__match_code', 'match__division__name',
        'match__division__tournament__name'
    ]
    
    readonly_fields = ['completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('match', 'set_number')
        }),
        ('Scores', {
            'fields': ('player1_score', 'player2_score', 'winner', 'completed_at')
        }),
    )
    
    raw_id_fields = ['match']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'match', 'match__division', 'match__division__tournament'
        )

