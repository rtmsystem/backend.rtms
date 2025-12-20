"""
Services for payment calculations.
"""
from decimal import Decimal
from datetime import datetime
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from apps.tournaments.models import Tournament, TournamentDivision, Involvement, InvolvementStatus
from apps.players.models import PlayerProfile
from .models import Payment, PaymentTransaction, PaymentTransactionItem, PaymentStatus, PaymentMethod
from .exceptions import (
    PaymentNotFoundError,
    PaymentNotActiveError,
    PaymentAlreadyCompletedError,
    InvalidPaymentAmountError,
    PaymentTransactionNotFoundError,
    TournamentHasNoDivisionsError,
    InvalidPaymentSubtotalError,
    InvalidPaymentDiscountError
)


class PaymentCalculationService:
    """Service to calculate payment details for a subscription."""
    
    def __init__(
        self,
        tournament: Tournament,
        division: TournamentDivision,
        player: PlayerProfile
    ) -> None:
        """
        Initialize payment calculation service.
        
        Args:
            tournament: The tournament
            division: The division
            player: The player
        """
        self.tournament = tournament
        self.division = division
        self.player = player
        self.payment_config = None
        self._load_payment_config()
    
    def _load_payment_config(self) -> None:
        """
        Load payment configuration for the division.
        
        Implements inheritance logic:
        1. First, check if division has its own payment configuration
        2. If not, check if tournament has payment configuration
        3. If neither exists, raise PaymentNotFoundError
        """
        # First, try to get division-specific payment configuration
        division_payment = Payment.objects.filter(
            division=self.division,
            is_active=True
        ).first()
        
        if division_payment:
            self.payment_config = division_payment
            return
        
        # If no division payment, try tournament payment configuration
        tournament_payment = Payment.objects.filter(
            tournament=self.tournament,
            is_active=True
        ).first()
        
        if tournament_payment:
            self.payment_config = tournament_payment
            return
        
        # No payment configuration found
        raise PaymentNotFoundError(
            division_id=self.division.id,
            tournament_id=self.tournament.id
        )
    
    def _check_early_payment_discount(self) -> Decimal:
        """
        Check if early payment discount applies.
        
        Returns:
            Discount amount if applicable, otherwise 0
        """
        if not self.payment_config.early_payment_discount_amount:
            return Decimal('0.00')
        
        if not self.payment_config.early_payment_discount_deadline:
            return Decimal('0.00')
        
        now = timezone.now()
        if now <= self.payment_config.early_payment_discount_deadline:
            return self.payment_config.early_payment_discount_amount
        
        return Decimal('0.00')
    
    def _check_second_category_discount(self) -> Decimal:
        """
        Check if second category discount applies.
        
        Returns:
            Discount amount if applicable, otherwise 0
        """
        if not self.payment_config.second_category_discount_amount:
            return Decimal('0.00')
        
        # Count approved involvements for this player in this tournament
        approved_involvements = Involvement.objects.filter(
            tournament=self.tournament,
            player=self.player,
            status=InvolvementStatus.APPROVED
        ).exclude(division=self.division).count()
        
        # If player has 1+ other approved involvements, apply discount
        if approved_involvements >= 1:
            return self.payment_config.second_category_discount_amount
        
        return Decimal('0.00')
    
    def calculate(self) -> Decimal:
        """
        Calculate total amount to pay with discounts applied.
        
        Returns:
            Total amount after discounts
        """
        subscription_fee = self.payment_config.subscription_fee
        early_discount = self._check_early_payment_discount()
        second_category_discount = self._check_second_category_discount()
        
        total = subscription_fee - early_discount - second_category_discount
        
        # Ensure total is not negative
        return max(total, Decimal('0.00'))
    
    def get_payment_details(self) -> Dict[str, Any]:
        """
        Get complete payment details with all discounts.
        
        Returns:
            Dictionary with payment details
        """
        subscription_fee = self.payment_config.subscription_fee
        early_discount = self._check_early_payment_discount()
        second_category_discount = self._check_second_category_discount()
        total_amount = self.calculate()
        
        discounts_applied: List[str] = []
        if early_discount > 0:
            discounts_applied.append('early_payment')
        if second_category_discount > 0:
            discounts_applied.append('second_category')
        
        return {
            'subscription_fee': float(subscription_fee),
            'early_payment_discount': float(early_discount),
            'second_category_discount': float(second_category_discount),
            'total_amount': float(total_amount),
            'discounts_applied': discounts_applied
        }


class PaymentProcessingService:
    """Service to process payment transactions."""
    
    def __init__(
        self,
        involvement,
        amount: Decimal,
        payment_method: str,
        transaction_id: str = None,
        payment_reference: str = None,
        notes: str = None,
        payment_proof=None,
        user=None
    ) -> None:
        """
        Initialize payment processing service.
        
        Args:
            involvement: The involvement to process payment for
            amount: Payment amount
            payment_method: Payment method
            transaction_id: External transaction ID
            payment_reference: Payment reference number
            notes: Additional notes
            payment_proof: Payment proof file (PDF or image)
            user: User processing the payment
        """
        self.involvement = involvement
        self.amount = amount
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.payment_reference = payment_reference
        self.notes = notes
        self.payment_proof = payment_proof
        self.user = user
    
    def _calculate_expected_amount(self) -> Decimal:
        """Calculate expected payment amount."""
        service = PaymentCalculationService(
            tournament=self.involvement.tournament,
            division=self.involvement.division,
            player=self.involvement.player
        )
        return service.calculate()
    
    def _get_payment_details(self) -> Dict[str, Any]:
        """Get payment details for the involvement."""
        service = PaymentCalculationService(
            tournament=self.involvement.tournament,
            division=self.involvement.division,
            player=self.involvement.player
        )
        return service.get_payment_details()
    
    @transaction.atomic
    def create_payment_transaction(self) -> PaymentTransaction:
        """
        Create a payment transaction for a single involvement.
        Note: For multiple involvements, use BulkPaymentValidationService instead.
        
        Returns:
            Created PaymentTransaction
        """
        # Check if involvement already has a completed payment
        if self.involvement.paid:
            completed_payment = PaymentTransaction.objects.filter(
                involvements=self.involvement,
                status=PaymentStatus.COMPLETED
            ).first()
            if completed_payment:
                raise PaymentAlreadyCompletedError()
        
        # Calculate expected amount
        expected_amount = self._calculate_expected_amount()
        
        # Validate amount (allow small difference for rounding)
        if abs(self.amount - expected_amount) > Decimal('0.01'):
            raise InvalidPaymentAmountError(
                expected=expected_amount,
                received=self.amount
            )
        
        # Get payment details
        payment_details = self._get_payment_details()
        
        # Create transaction
        payment_transaction = PaymentTransaction.objects.create(
            amount=self.amount,
            subtotal=Decimal(str(payment_details['subscription_fee'])),
            total_discount=Decimal(str(payment_details['early_payment_discount'])) + Decimal(str(payment_details['second_category_discount'])),
            subscription_fee=Decimal(str(payment_details['subscription_fee'])),
            early_payment_discount=Decimal(str(payment_details['early_payment_discount'])),
            second_category_discount=Decimal(str(payment_details['second_category_discount'])),
            payment_method=self.payment_method,
            transaction_id=self.transaction_id,
            payment_reference=self.payment_reference,
            notes=self.notes,
            payment_proof=self.payment_proof,
            status=PaymentStatus.PENDING
        )
        
        # Associate involvement with transaction
        payment_transaction.involvements.add(self.involvement)
        
        # Create transaction item with detailed breakdown
        PaymentTransactionItem.objects.create(
            transaction=payment_transaction,
            involvement=self.involvement,
            division_name=self.involvement.division.name,
            subscription_fee=Decimal(str(payment_details['subscription_fee'])),
            early_payment_discount=Decimal(str(payment_details['early_payment_discount'])),
            second_category_discount=Decimal(str(payment_details['second_category_discount'])),
            item_total=self.amount
        )
        
        return payment_transaction
    
    @transaction.atomic
    def confirm_payment(self, transaction_id: int = None) -> PaymentTransaction:
        """
        Confirm and complete a payment transaction.
        
        Args:
            transaction_id: Optional transaction ID to confirm
            
        Returns:
            Confirmed PaymentTransaction
        """
        if transaction_id:
            payment_transaction = PaymentTransaction.objects.get(pk=transaction_id)
        else:
            # Get latest pending transaction for this involvement
            payment_transaction = PaymentTransaction.objects.filter(
                involvements=self.involvement,
                status=PaymentStatus.PENDING
            ).order_by('-created_at').first()
            
            if not payment_transaction:
                raise PaymentTransactionNotFoundError()
        
        if payment_transaction.status == PaymentStatus.COMPLETED:
            raise PaymentAlreadyCompletedError()
        
        # Mark as completed
        payment_transaction.mark_as_completed(user=self.user)
        
        return payment_transaction
    
    @transaction.atomic
    def cancel_payment(self, transaction_id: int) -> PaymentTransaction:
        """
        Cancel a payment transaction.
        
        Args:
            transaction_id: Transaction ID to cancel
            
        Returns:
            Cancelled PaymentTransaction
        """
        payment_transaction = PaymentTransaction.objects.get(pk=transaction_id)
        
        if payment_transaction.status == PaymentStatus.COMPLETED:
            raise PaymentAlreadyCompletedError()
        
        payment_transaction.status = PaymentStatus.CANCELLED
        payment_transaction.processed_at = timezone.now()
        if self.user:
            payment_transaction.processed_by = self.user
        payment_transaction.save()
        
        return payment_transaction


class BulkPaymentCalculationService:
    """Service to calculate payment details for multiple involvements."""
    
    def __init__(
        self,
        involvements: List[Involvement],
        player: PlayerProfile
    ) -> None:
        """
        Initialize bulk payment calculation service.
        
        Args:
            involvements: List of involvements to calculate payment for
            player: The player (all involvements must belong to this player)
        """
        self.involvements = involvements
        self.player = player
        self._validate_involvements()
        self.payment_configs = {}
        self._load_payment_configs()
    
    def _validate_involvements(self) -> None:
        """Validate that all involvements belong to the same player."""
        for involvement in self.involvements:
            if involvement.player != self.player:
                raise ValueError(
                    f"All involvements must belong to the same player. "
                    f"Involvement {involvement.id} belongs to a different player."
                )
    
    def _load_payment_configs(self) -> None:
        """Load payment configuration for each involvement's division."""
        for involvement in self.involvements:
            division = involvement.division
            tournament = involvement.tournament
            
            # Check if we already have this config
            if division.id in self.payment_configs:
                continue
            
            # First, try to get division-specific payment configuration
            division_payment = Payment.objects.filter(
                division=division,
                is_active=True
            ).first()
            
            if division_payment:
                self.payment_configs[division.id] = division_payment
                continue
            
            # If no division payment, try tournament payment configuration
            tournament_payment = Payment.objects.filter(
                tournament=tournament,
                is_active=True
            ).first()
            
            if tournament_payment:
                self.payment_configs[division.id] = tournament_payment
                continue
            
            # No payment configuration found
            raise PaymentNotFoundError(
                division_id=division.id,
                tournament_id=tournament.id
            )
    
    def _get_payment_config(self, division: TournamentDivision) -> Payment:
        """Get payment configuration for a division."""
        return self.payment_configs[division.id]
    
    def _check_early_payment_discount(self, payment_config: Payment) -> Decimal:
        """Check if early payment discount applies."""
        if not payment_config.early_payment_discount_amount:
            return Decimal('0.00')
        
        if not payment_config.early_payment_discount_deadline:
            return Decimal('0.00')
        
        now = timezone.now()
        if now <= payment_config.early_payment_discount_deadline:
            return payment_config.early_payment_discount_amount
        
        return Decimal('0.00')
    
    def _check_second_category_discount(
        self,
        payment_config: Payment,
        division: TournamentDivision,
        tournament: Tournament,
        previous_involvements_count: int
    ) -> Decimal:
        """
        Check if second category discount applies.
        
        Args:
            payment_config: Payment configuration
            division: Current division
            tournament: Tournament
            previous_involvements_count: Number of involvements processed before this one
        
        Returns:
            Discount amount if applicable, otherwise 0
        """
        if not payment_config.second_category_discount_amount:
            return Decimal('0.00')
        
        # Count approved involvements for this player in this tournament
        # excluding the current division and previous involvements in this transaction
        approved_involvements = Involvement.objects.filter(
            tournament=tournament,
            player=self.player,
            status=InvolvementStatus.APPROVED
        ).exclude(division=division).count()
        
        # If player has previous approved involvements OR this is not the first
        # involvement in this transaction, apply discount
        if approved_involvements >= 1 or previous_involvements_count > 0:
            return payment_config.second_category_discount_amount
        
        return Decimal('0.00')
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate total payment details for all involvements.
        
        Returns:
            Dictionary with payment details:
            - subtotal: Sum of all subscription fees
            - early_payment_discount: Total early payment discount
            - second_category_discount: Total second category discount
            - total_discount: Sum of all discounts
            - total_amount: Final amount to pay
        """
        subtotal = Decimal('0.00')
        total_early_discount = Decimal('0.00')
        total_second_category_discount = Decimal('0.00')
        previous_count = 0
        
        # Process each involvement
        for involvement in self.involvements:
            payment_config = self._get_payment_config(involvement.division)
            
            # Add subscription fee to subtotal
            subscription_fee = payment_config.subscription_fee
            subtotal += subscription_fee
            
            # Check early payment discount
            early_discount = self._check_early_payment_discount(payment_config)
            total_early_discount += early_discount
            
            # Check second category discount
            second_category_discount = self._check_second_category_discount(
                payment_config,
                involvement.division,
                involvement.tournament,
                previous_count
            )
            total_second_category_discount += second_category_discount
            
            previous_count += 1
        
        # Calculate total discount and final amount
        total_discount = total_early_discount + total_second_category_discount
        total_amount = subtotal - total_discount
        
        # Ensure total is not negative
        total_amount = max(total_amount, Decimal('0.00'))
        
        return {
            'subtotal': subtotal,
            'early_payment_discount': total_early_discount,
            'second_category_discount': total_second_category_discount,
            'total_discount': total_discount,
            'total_amount': total_amount
        }


class BulkPaymentValidationService:
    """Service to validate payment values against expected calculations."""
    
    def __init__(
        self,
        involvements: List[Involvement],
        player: PlayerProfile,
        total_paid: Decimal,
        subtotal: Optional[Decimal] = None,
        total_discount: Optional[Decimal] = None
    ) -> None:
        """
        Initialize bulk payment validation service.
        
        Args:
            involvements: List of involvements
            player: The player
            total_paid: Total amount paid (from user input)
            subtotal: Subtotal provided by user (optional)
            total_discount: Total discount provided by user (optional)
        """
        self.involvements = involvements
        self.player = player
        self.total_paid = total_paid
        self.subtotal_provided = subtotal
        self.total_discount_provided = total_discount
        
        self.calculation_service = BulkPaymentCalculationService(
            involvements=involvements,
            player=player
        )
        self.expected_values = self.calculation_service.calculate()
    
    def validate(self) -> None:
        """
        Validate that provided values match expected calculations.
        
        Raises:
            InvalidPaymentAmountError: If total_paid doesn't match expected total
            InvalidPaymentSubtotalError: If subtotal doesn't match expected subtotal
            InvalidPaymentDiscountError: If total_discount doesn't match expected discount
        """
        # Validate total amount (with tolerance for rounding)
        expected_total = self.expected_values['total_amount']
        if abs(self.total_paid - expected_total) > Decimal('0.01'):
            raise InvalidPaymentAmountError(
                expected=expected_total,
                received=self.total_paid
            )
        
        # Validate subtotal if provided
        if self.subtotal_provided is not None:
            expected_subtotal = self.expected_values['subtotal']
            if abs(self.subtotal_provided - expected_subtotal) > Decimal('0.01'):
                raise InvalidPaymentSubtotalError(
                    expected=expected_subtotal,
                    received=self.subtotal_provided
                )
        
        # Validate total discount if provided
        if self.total_discount_provided is not None:
            expected_discount = self.expected_values['total_discount']
            if abs(self.total_discount_provided - expected_discount) > Decimal('0.01'):
                raise InvalidPaymentDiscountError(
                    expected=expected_discount,
                    received=self.total_discount_provided
                )
    
    def get_expected_values(self) -> Dict[str, Any]:
        """Get expected payment values."""
        return self.expected_values


class BulkPaymentCreationService:
    """Service to create or update payments for all divisions of a tournament."""
    
    def __init__(
        self,
        tournament: Tournament,
        subscription_fee: Decimal,
        early_payment_discount_amount: Decimal = Decimal('0.00'),
        early_payment_discount_deadline: Optional[datetime] = None,
        second_category_discount_amount: Decimal = Decimal('0.00'),
        create_tournament_level: bool = False
    ) -> None:
        """
        Initialize bulk payment creation service.
        
        Args:
            tournament: The tournament
            subscription_fee: Base subscription fee for all divisions
            early_payment_discount_amount: Discount amount for early payment
            early_payment_discount_deadline: Deadline for early payment discount
            second_category_discount_amount: Discount amount for second category
            create_tournament_level: If True, create tournament-level payment (inherited by all divisions)
                                    If False, create individual payment for each division
        """
        self.tournament = tournament
        self.subscription_fee = subscription_fee
        self.early_payment_discount_amount = early_payment_discount_amount
        self.early_payment_discount_deadline = early_payment_discount_deadline
        self.second_category_discount_amount = second_category_discount_amount
        self.create_tournament_level = create_tournament_level
        self.created_count = 0
        self.updated_count = 0
    
    def _validate_tournament_has_divisions(self) -> None:
        """Validate that tournament has at least one division."""
        if not self.create_tournament_level:
            divisions_count = self.tournament.divisions.count()
            if divisions_count == 0:
                raise TournamentHasNoDivisionsError(tournament_id=self.tournament.id)
    
    @transaction.atomic
    def execute(self) -> List[Payment]:
        """
        Create or update payments.
        
        If create_tournament_level is True, creates a single tournament-level payment.
        If False, creates individual payments for each division.
        
        Returns:
            List of created/updated Payment objects
        """
        # Validate tournament has divisions if creating division-level payments
        self._validate_tournament_has_divisions()
        
        if self.create_tournament_level:
            # Create or update tournament-level payment
            payment = Payment.objects.filter(tournament=self.tournament).first()
            
            if payment:
                # Update existing payment
                payment.subscription_fee = self.subscription_fee
                payment.early_payment_discount_amount = self.early_payment_discount_amount
                payment.early_payment_discount_deadline = self.early_payment_discount_deadline
                payment.second_category_discount_amount = self.second_category_discount_amount
                payment.save()
                self.updated_count = 1
            else:
                # Create new payment
                payment = Payment.objects.create(
                    tournament=self.tournament,
                    subscription_fee=self.subscription_fee,
                    early_payment_discount_amount=self.early_payment_discount_amount,
                    early_payment_discount_deadline=self.early_payment_discount_deadline,
                    second_category_discount_amount=self.second_category_discount_amount
                )
                self.created_count = 1
            
            return [payment]
        else:
            # Create or update payments for all divisions
            divisions = self.tournament.divisions.all()
            payments = []
            
            for division in divisions:
                # Check if payment already exists
                payment = Payment.objects.filter(division=division).first()
                
                if payment:
                    # Update existing payment
                    payment.subscription_fee = self.subscription_fee
                    payment.early_payment_discount_amount = self.early_payment_discount_amount
                    payment.early_payment_discount_deadline = self.early_payment_discount_deadline
                    payment.second_category_discount_amount = self.second_category_discount_amount
                    payment.save()
                    self.updated_count += 1
                else:
                    # Create new payment
                    payment = Payment.objects.create(
                        division=division,
                        subscription_fee=self.subscription_fee,
                        early_payment_discount_amount=self.early_payment_discount_amount,
                        early_payment_discount_deadline=self.early_payment_discount_deadline,
                        second_category_discount_amount=self.second_category_discount_amount
                    )
                    self.created_count += 1
                
                payments.append(payment)
            
            return payments

