"""
Serializers for payments app.
"""
from decimal import Decimal
from typing import List, Dict, Optional
from django.utils import timezone
from rest_framework import serializers
from .models import Payment, PaymentTransaction, PaymentTransactionItem, PaymentMethod



class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    division_name = serializers.SerializerMethodField()
    tournament_name = serializers.SerializerMethodField()
    tournament_id = serializers.SerializerMethodField()
    payment_scope = serializers.CharField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'tournament', 'division', 'payment_scope',
            'division_name', 'tournament_id', 'tournament_name',
            'subscription_fee', 'early_payment_discount_amount',
            'early_payment_discount_deadline', 'second_category_discount_amount',
            'is_active', 'created_at', 'updated_at', 'payment_information'
        ]
        read_only_fields = ['id', 'payment_scope', 'created_at', 'updated_at']
    
    def get_division_name(self, obj) -> str:
        """Get division name if payment is for a division."""
        if obj.division:
            return obj.division.name
        return None
    
    def get_tournament_name(self, obj) -> str:
        """Get tournament name."""
        tournament = obj.get_tournament()
        if tournament:
            return tournament.name
        return None
    
    def get_tournament_id(self, obj) -> int:
        """Get tournament ID."""
        tournament = obj.get_tournament()
        if tournament:
            return tournament.id
        return None
    
    def validate(self, data: dict) -> dict:
        """Validate payment configuration."""
        tournament = data.get('tournament')
        division = data.get('division')
        
        # When creating from URL (tournament_id/division_id in URL), these fields
        # are set in perform_create(), so we don't require them here.
        # Only validate if they are explicitly provided in the data.
        if tournament is not None or division is not None:
            # If one is provided, validate they're not both provided
            if tournament and division:
                raise serializers.ValidationError({
                    'tournament': 'Cannot specify both tournament and division. Choose one.',
                    'division': 'Cannot specify both tournament and division. Choose one.'
                })
        
        # Validate discount amounts
        subscription_fee = data.get('subscription_fee')
        early_discount = data.get('early_payment_discount_amount', 0)
        second_category_discount = data.get('second_category_discount_amount', 0)
        
        if subscription_fee is not None:
            if early_discount > subscription_fee:
                raise serializers.ValidationError({
                    'early_payment_discount_amount': 'Early payment discount cannot exceed subscription fee.'
                })
            
            if second_category_discount > subscription_fee:
                raise serializers.ValidationError({
                    'second_category_discount_amount': 'Second category discount cannot exceed subscription fee.'
                })
        
        return data


class PaymentDetailsSerializer(serializers.Serializer):
    """Serializer for payment details response."""
    
    subscription_fee = serializers.FloatField()
    early_payment_discount = serializers.FloatField()
    second_category_discount = serializers.FloatField()
    total_amount = serializers.FloatField()
    discounts_applied = serializers.ListField(
        child=serializers.CharField()
    )


class PaymentTransactionItemSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransactionItem model."""
    
    involvement_id = serializers.IntegerField(source='involvement.id', read_only=True)
    
    class Meta:
        model = PaymentTransactionItem
        fields = [
            'id', 'involvement_id', 'division_name',
            'subscription_fee', 'early_payment_discount',
            'second_category_discount', 'item_total',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'involvement_id', 'division_name',
            'subscription_fee', 'early_payment_discount',
            'second_category_discount', 'item_total',
            'created_at', 'updated_at'
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransaction model."""
    
    involvements = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    involvement_ids = serializers.SerializerMethodField()
    players_info = serializers.SerializerMethodField()
    processed_by_name = serializers.SerializerMethodField()
    payment_proof_url = serializers.SerializerMethodField()
    items = PaymentTransactionItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_discount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'invoice_number', 'involvements', 'involvement_ids', 'amount',
            'subtotal', 'total_discount',
            'subscription_fee', 'early_payment_discount', 'second_category_discount',
            'status', 'payment_method', 'transaction_id', 'payment_reference',
            'notes', 'payment_proof', 'payment_proof_url',
            'processed_by', 'processed_by_name', 'processed_at',
            'players_info', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subscription_fee', 'early_payment_discount',
            'second_category_discount', 'subtotal', 'total_discount',
            'processed_at', 'created_at', 'updated_at'
        ]
    
    def get_involvement_ids(self, obj) -> List[int]:
        """Get list of involvement IDs."""
        return list(obj.involvements.values_list('id', flat=True))
    
    def get_players_info(self, obj) -> Optional[Dict]:
        """Get information about the primary player in the transaction."""
        first_involvement = obj.involvements.first()
        if not first_involvement:
            return None
        
        player = first_involvement.player
        
        # Get avatar URL if available
        avatar_url = None
        if player.avatar:
            try:
                request = self.context.get('request')
                if request:
                    avatar_url = request.build_absolute_uri(player.avatar.url)
                else:
                    avatar_url = player.avatar.url
            except (ValueError, AttributeError):
                avatar_url = None
        
        return {
            'first_name': player.first_name,
            'last_name': player.last_name,
            'email': player.email,
            'avatar': avatar_url,
        }
    
    def get_processed_by_name(self, obj) -> str:
        """Get processed by user's full name."""
        if obj.processed_by:
            return obj.processed_by.get_full_name() if hasattr(obj.processed_by, 'get_full_name') else str(obj.processed_by)
        return None
    
    def get_payment_proof_url(self, obj) -> str:
        """Get payment proof file URL safely."""
        if obj.payment_proof:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.payment_proof.url)
                return obj.payment_proof.url
            except ValueError:
                return None
        return None


class CreatePaymentTransactionSerializer(serializers.Serializer):
    """Serializer for creating a payment transaction."""
    
    involvement_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    transaction_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    payment_reference = serializers.CharField(required=False, allow_blank=True, max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_proof = serializers.FileField(required=False, allow_null=True)
    
    def validate_payment_proof(self, value):
        """Validate payment proof file extension."""
        if value:
            ext = value.name.split('.')[-1].lower()
            if ext not in ['pdf', 'png', 'jpg', 'jpeg']:
                raise serializers.ValidationError(
                    "Payment proof must be a PDF or image file (PNG, JPG, JPEG)."
                )
            # Validate file size (max 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "Payment proof file size cannot exceed 10MB."
                )
        return value


class ConfirmPaymentSerializer(serializers.Serializer):
    """Serializer for confirming a payment."""
    
    transaction_id = serializers.IntegerField(required=False)
    payment_reference = serializers.CharField(required=False, allow_blank=True, max_length=255)


class BulkCreatePaymentsSerializer(serializers.Serializer):
    """Serializer for bulk creating payments for all tournament divisions."""
    
    subscription_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text='Base subscription fee for all divisions'
    )
    
    early_payment_discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
        help_text='Discount amount for early payment'
    )
    
    early_payment_discount_deadline = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Deadline date for applying early payment discount'
    )
    
    second_category_discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
        help_text='Discount amount for registering in a second category'
    )
    
    def validate_subscription_fee(self, value: Decimal) -> Decimal:
        """Validate subscription fee is not negative."""
        if value < 0:
            raise serializers.ValidationError(
                "Subscription fee cannot be negative."
            )
        return value
    
    def validate_early_payment_discount_amount(self, value: Decimal) -> Decimal:
        """Validate early payment discount amount."""
        if value < 0:
            raise serializers.ValidationError(
                "Early payment discount amount cannot be negative."
            )
        return value
    
    def validate_second_category_discount_amount(self, value: Decimal) -> Decimal:
        """Validate second category discount amount."""
        if value < 0:
            raise serializers.ValidationError(
                "Second category discount amount cannot be negative."
            )
        return value
    
    def validate(self, data: dict) -> dict:
        """Validate payment configuration."""
        subscription_fee = data.get('subscription_fee')
        early_discount = data.get('early_payment_discount_amount', Decimal('0.00'))
        second_category_discount = data.get('second_category_discount_amount', Decimal('0.00'))
        early_deadline = data.get('early_payment_discount_deadline')
        
        # Validate discounts don't exceed subscription fee
        if subscription_fee is not None:
            if early_discount > subscription_fee:
                raise serializers.ValidationError({
                    'early_payment_discount_amount': 'Early payment discount cannot exceed subscription fee.'
                })
            
            if second_category_discount > subscription_fee:
                raise serializers.ValidationError({
                    'second_category_discount_amount': 'Second category discount cannot exceed subscription fee.'
                })
        
        # Validate early payment deadline if provided
        if early_deadline:
            if early_deadline < timezone.now():
                raise serializers.ValidationError({
                    'early_payment_discount_deadline': 'Discount deadline cannot be in the past.'
                })
        
        return data

