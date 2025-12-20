"""
Payment models for managing tournament subscription payments.
"""
from decimal import Decimal
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.conf import settings

from .validators import validate_discount_amount, validate_discount_deadline


class Payment(models.Model):
    """
    Model representing payment configuration for a tournament or division.
    
    Can be configured at tournament level (inherited by all divisions) or
    at division level (overrides tournament configuration).
    """
    tournament = models.OneToOneField(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='payment',
        null=True,
        blank=True,
        verbose_name='Tournament',
        help_text='Tournament this payment configuration belongs to (inherited by all divisions)'
    )
    
    division = models.ForeignKey(
        'tournaments.TournamentDivision',
        on_delete=models.CASCADE,
        related_name='payment',
        null=True,
        blank=True,
        verbose_name='Division',
        help_text='Division this payment configuration belongs to (overrides tournament configuration)'
    )
    
    subscription_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Subscription Fee',
        help_text='Base subscription fee for this division'
    )
    
    early_payment_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Early Payment Discount Amount',
        help_text='Discount amount for early payment'
    )
    
    early_payment_discount_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Early Payment Discount Deadline',
        help_text='Deadline date for applying early payment discount'
    )
    
    second_category_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Second Category Discount Amount',
        help_text='Discount amount for registering in a second category'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether payment subscription is active'
    )

    payment_information = models.TextField(
        blank=True,
        null=True,
        verbose_name='Payment Information',
        help_text='Payment information for the tournament'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tournament']),
            models.Index(fields=['division']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(tournament__isnull=False, division__isnull=True) |
                    models.Q(tournament__isnull=True, division__isnull=False)
                ),
                name='payment_must_have_tournament_or_division'
            ),
        ]
    
    def __str__(self) -> str:
        if self.division:
            return f"Payment for {self.division.name} ({self.division.tournament.name})"
        elif self.tournament:
            return f"Payment for Tournament {self.tournament.name}"
        return f"Payment {self.id}"
    
    def clean(self) -> None:
        """Validate payment configuration."""
        from django.core.exceptions import ValidationError
        
        # Validate that exactly one of tournament or division is set
        if not self.tournament and not self.division:
            raise ValidationError({
                'tournament': 'Either tournament or division must be specified.',
                'division': 'Either tournament or division must be specified.'
            })
        
        if self.tournament and self.division:
            raise ValidationError({
                'tournament': 'Cannot specify both tournament and division. Choose one.',
                'division': 'Cannot specify both tournament and division. Choose one.'
            })
        
        # Validate early payment discount
        if self.early_payment_discount_amount > 0:
            validate_discount_amount(
                self.early_payment_discount_amount,
                self.subscription_fee,
                'Early payment discount amount'
            )
            if self.early_payment_discount_deadline:
                validate_discount_deadline(self.early_payment_discount_deadline)
        
        # Validate second category discount
        if self.second_category_discount_amount > 0:
            validate_discount_amount(
                self.second_category_discount_amount,
                self.subscription_fee,
                'Second category discount amount'
            )
    
    def save(self, *args, **kwargs) -> None:
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def payment_scope(self) -> str:
        """Get payment scope: 'tournament' or 'division'."""
        if self.tournament:
            return 'tournament'
        elif self.division:
            return 'division'
        return 'unknown'
    
    def get_tournament(self):
        """Get tournament associated with this payment."""
        if self.tournament:
            return self.tournament
        elif self.division:
            return self.division.tournament
        return None


class PaymentStatus(models.TextChoices):
    """Payment transaction status choices."""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUNDED = 'refunded', 'Refunded'


class PaymentMethod(models.TextChoices):
    """Payment method choices."""
    CASH = 'cash', 'Cash'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    CREDIT_CARD = 'credit_card', 'Credit Card'
    DEBIT_CARD = 'debit_card', 'Debit Card'
    STRIPE = 'stripe', 'Stripe'
    PAYPAL = 'paypal', 'PayPal'
    OTHER = 'other', 'Other'


class PaymentTransaction(models.Model):
    """
    Model representing a payment transaction for one or more involvements.
    """
    involvements = models.ManyToManyField(
        'tournaments.Involvement',
        related_name='payment_transactions',
        verbose_name='Involvements',
        help_text='Involvements this payment is for'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Amount',
        help_text='Payment amount (total)'
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Subtotal',
        help_text='Subtotal before discounts (sum of all subscription fees)'
    )
    
    total_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total Discount',
        help_text='Total discount applied (early payment + second category)'
    )
    
    subscription_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Subscription Fee',
        help_text='Total subscription fee (sum of all subscription fees)'
    )
    
    early_payment_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Early Payment Discount',
        help_text='Early payment discount applied'
    )
    
    second_category_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Second Category Discount',
        help_text='Second category discount applied'
    )
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='Status',
        help_text='Payment transaction status'
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name='Payment Method',
        help_text='Method used for payment'
    )
    
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Transaction ID',
        help_text='External transaction ID (from payment gateway)'
    )
    
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Payment Reference',
        help_text='Payment reference number'
    )
    
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Invoice Number',
        help_text='Auto-generated sequential invoice number (e.g., INV-1, INV-2)'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notes',
        help_text='Additional notes about the payment'
    )
    
    payment_proof = models.FileField(
        upload_to='payment_proofs/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])
        ],
        verbose_name='Payment Proof',
        help_text='Payment proof document (PDF or image)'
    )
    
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payments',
        verbose_name='Processed By',
        help_text='User who processed this payment'
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Processed At',
        help_text='When the payment was processed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self) -> str:
        involvements_count = self.involvements.count()
        if involvements_count == 1:
            involvement = self.involvements.first()
            return f"Payment {self.id} - {involvement.player.full_name} - {self.amount}"
        return f"Payment {self.id} - {involvements_count} involvements - {self.amount}"
    
    def mark_as_completed(self, user=None) -> None:
        """Mark payment as completed and update all related involvements."""
        self.status = PaymentStatus.COMPLETED
        self.processed_at = timezone.now()
        if user:
            self.processed_by = user
        self.save()
        
        # Update paid status for all related involvements
        self.involvements.update(paid=True)
    
    def mark_as_failed(self, user=None) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED
        self.processed_at = timezone.now()
        if user:
            self.processed_by = user
        self.save()
    
    def generate_invoice_number(self) -> str:
        """
        Generate sequential invoice number (INV-1, INV-2, etc.).
        
        Returns:
            Generated invoice number string
        """
        if self.invoice_number:
            return self.invoice_number
        
        # Get the highest invoice number
        last_invoice = PaymentTransaction.objects.filter(
            invoice_number__isnull=False
        ).exclude(
            invoice_number=''
        ).order_by('-id').first()
        
        if last_invoice and last_invoice.invoice_number:
            # Extract number from last invoice (e.g., "INV-18" -> 18)
            try:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                # If parsing fails, use ID-based numbering
                next_number = PaymentTransaction.objects.count() + 1
        else:
            # First invoice
            next_number = 1
        
        return f"INV-{next_number}"
    
    def save(self, *args, **kwargs) -> None:
        """Override save to auto-generate invoice number if not set."""
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)


class PaymentTransactionItem(models.Model):
    """
    Model representing a detailed breakdown of each division in a payment transaction.
    
    Stores snapshot of pricing and discount information for each involvement
    at the time of transaction creation, enabling accurate invoice generation.
    """
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Transaction',
        help_text='Payment transaction this item belongs to'
    )
    
    involvement = models.OneToOneField(
        'tournaments.Involvement',
        on_delete=models.CASCADE,
        related_name='payment_transaction_item',
        verbose_name='Involvement',
        help_text='Involvement (division registration) this item represents'
    )
    
    division_name = models.CharField(
        max_length=255,
        verbose_name='Division Name',
        help_text='Snapshot of division name at time of transaction'
    )
    
    subscription_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Subscription Fee',
        help_text='Base subscription fee for this division'
    )
    
    early_payment_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Early Payment Discount',
        help_text='Early payment discount applied to this item'
    )
    
    second_category_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Second Category Discount',
        help_text='Second category discount applied to this item'
    )
    
    item_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Item Total',
        help_text='Total amount for this item after discounts (subscription_fee - discounts)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Payment Transaction Item'
        verbose_name_plural = 'Payment Transaction Items'
        ordering = ['transaction', 'created_at']
        indexes = [
            models.Index(fields=['transaction']),
            models.Index(fields=['involvement']),
        ]
    
    def __str__(self) -> str:
        return f"{self.transaction.invoice_number} - {self.division_name} - {self.item_total}"
    
    def clean(self) -> None:
        """Validate item calculations."""
        from django.core.exceptions import ValidationError
        
        # Validate item_total matches calculation
        calculated_total = (
            self.subscription_fee -
            self.early_payment_discount -
            self.second_category_discount
        )
        
        if calculated_total < Decimal('0.00'):
            raise ValidationError({
                'item_total': 'Item total cannot be negative. Discounts exceed subscription fee.'
            })
        
        # Allow small rounding differences (0.01)
        if abs(self.item_total - calculated_total) > Decimal('0.01'):
            raise ValidationError({
                'item_total': f'Item total ({self.item_total}) does not match calculation ({calculated_total}).'
            })
    
    def save(self, *args, **kwargs) -> None:
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)

