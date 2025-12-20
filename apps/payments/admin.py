"""
Admin configuration for payments app.
"""
from django.contrib import admin
from .models import Payment, PaymentTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""
    
    list_display = [
        'payment_scope_display', 'division', 'tournament', 'tournament_name',
        'subscription_fee', 'is_active',
        'early_payment_discount_amount', 'second_category_discount_amount',
        'created_at', 'updated_at'
    ]
    
    list_filter = [
        'is_active', 'created_at', 'updated_at',
        ('tournament', admin.RelatedOnlyFieldListFilter),
        ('division', admin.RelatedOnlyFieldListFilter),
    ]
    
    search_fields = [
        'division__name', 'tournament__name',
        'division__tournament__name', 'tournament__organization__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'payment_scope']
    
    fieldsets = (
        ('Payment Scope', {
            'fields': ('payment_scope', 'tournament', 'division'),
            'description': 'Select either tournament (inherited by all divisions) or division (overrides tournament)',
            'payment_information': 'Payment information for the tournament'
        }),
        ('Subscription Fee', {
            'fields': ('subscription_fee',)
        }),
        ('Early Payment Discount', {
            'fields': (
                'early_payment_discount_amount',
                'early_payment_discount_deadline'
            )
        }),
        ('Second Category Discount', {
            'fields': ('second_category_discount_amount',)
        }),
        ('Status & Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    raw_id_fields = ['tournament', 'division']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'tournament', 'tournament__organization',
            'division', 'division__tournament', 'division__tournament__organization'
        )
    
    def tournament_name(self, obj):
        """Get tournament name."""
        tournament = obj.get_tournament()
        return tournament.name if tournament else None
    tournament_name.short_description = 'Tournament'
    
    def payment_scope_display(self, obj):
        """Display payment scope."""
        scope = obj.payment_scope
        return scope.capitalize()
    payment_scope_display.short_description = 'Scope'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentTransaction model."""
    
    list_display = [
        'id', 'get_involvements_count', 'amount', 'status', 'payment_method',
        'transaction_id', 'has_payment_proof', 'processed_by', 'created_at'
    ]
    
    list_filter = [
        'status', 'payment_method', 'created_at', 'processed_at'
    ]
    
    search_fields = [
        'transaction_id', 'payment_reference',
        'involvements__player__first_name',
        'involvements__player__last_name',
        'involvements__tournament__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    filter_horizontal = ['involvements']
    
    fieldsets = (
        ('Involvements', {
            'fields': ('involvements',)
        }),
        ('Payment Details', {
            'fields': (
                'amount', 'subtotal', 'total_discount',
                'subscription_fee',
                'early_payment_discount', 'second_category_discount'
            )
        }),
        ('Transaction Info', {
            'fields': (
                'status', 'payment_method', 'transaction_id',
                'payment_reference', 'notes', 'payment_proof'
            )
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    raw_id_fields = ['processed_by']
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        return super().get_queryset(request).prefetch_related(
            'involvements',
            'involvements__player',
            'involvements__tournament',
            'involvements__division',
            'processed_by'
        )
    
    def get_involvements_count(self, obj):
        """Get count of involvements."""
        return obj.involvements.count()
    get_involvements_count.short_description = 'Involvements'
    
    def has_payment_proof(self, obj):
        """Check if payment has proof file."""
        return bool(obj.payment_proof)
    has_payment_proof.boolean = True
    has_payment_proof.short_description = 'Has Proof'

