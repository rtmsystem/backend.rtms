"""
Custom exceptions for payments app with error codes for i18n.
"""
from decimal import Decimal
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any


class PaymentBusinessError(ValidationError):
    """Base exception for payment business logic errors with error code."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        errors: Optional[Dict[str, Any]] = None
    ) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(message)
        if errors:
            self.error_dict = errors


class PaymentNotFoundError(PaymentBusinessError):
    """Raised when payment configuration is not found."""
    
    def __init__(self, division_id: Optional[int] = None, tournament_id: Optional[int] = None) -> None:
        if division_id and tournament_id:
            message = (
                f'Payment configuration not found for division {division_id}. '
                f'No division-specific or tournament-level payment configuration exists for tournament {tournament_id}.'
            )
        elif division_id:
            message = (
                f'Payment configuration not found for division {division_id}. '
                'No division-specific or tournament-level payment configuration exists.'
            )
        elif tournament_id:
            message = f'Payment configuration not found for tournament {tournament_id}.'
        else:
            message = 'Payment configuration not found.'
        super().__init__(
            message=message,
            error_code="ERROR_PAYMENT_NOT_FOUND",
            errors={'payment': [message]}
        )


class PaymentNotActiveError(PaymentBusinessError):
    """Raised when payment is not active for a division or tournament."""
    
    def __init__(self, division_id: Optional[int] = None, tournament_id: Optional[int] = None) -> None:
        if division_id:
            message = (
                f'Payment subscription is not active for division {division_id}. '
                'The payment configuration exists but is currently inactive.'
            )
        elif tournament_id:
            message = (
                f'Payment subscription is not active for tournament {tournament_id}. '
                'The payment configuration exists but is currently inactive.'
            )
        else:
            message = 'Payment subscription is not active.'
        super().__init__(
            message=message,
            error_code="ERROR_PAYMENT_NOT_ACTIVE",
            errors={'payment': [message]}
        )


class PaymentTransactionNotFoundError(PaymentBusinessError):
    """Raised when payment transaction is not found."""
    
    def __init__(self, transaction_id: Optional[int] = None) -> None:
        if transaction_id:
            message = f'Payment transaction {transaction_id} not found.'
        else:
            message = 'Payment transaction not found.'
        super().__init__(
            message=message,
            error_code="ERROR_PAYMENT_TRANSACTION_NOT_FOUND",
            errors={'transaction': [message]}
        )


class PaymentAlreadyCompletedError(PaymentBusinessError):
    """Raised when trying to process an already completed payment."""
    
    def __init__(self) -> None:
        message = 'This payment has already been completed.'
        super().__init__(
            message=message,
            error_code="ERROR_PAYMENT_ALREADY_COMPLETED",
            errors={'payment': [message]}
        )


class InvalidPaymentAmountError(PaymentBusinessError):
    """Raised when payment amount is invalid."""
    
    def __init__(self, expected: Decimal, received: Decimal) -> None:
        message = f'Invalid payment amount. Expected: {expected}, Received: {received}'
        super().__init__(
            message=message,
            error_code="ERROR_INVALID_PAYMENT_AMOUNT",
            errors={'amount': [message]}
        )


class TournamentHasNoDivisionsError(PaymentBusinessError):
    """Raised when tournament has no divisions."""
    
    def __init__(self, tournament_id: Optional[int] = None) -> None:
        if tournament_id:
            message = f'Tournament {tournament_id} has no divisions. Cannot create payments.'
        else:
            message = 'Tournament has no divisions. Cannot create payments.'
        super().__init__(
            message=message,
            error_code="ERROR_TOURNAMENT_HAS_NO_DIVISIONS",
            errors={'tournament': [message]}
        )


class InvalidPaymentSubtotalError(PaymentBusinessError):
    """Raised when payment subtotal does not match expected value."""
    
    def __init__(self, expected: Decimal, received: Decimal) -> None:
        message = f'Invalid payment subtotal. Expected: {expected}, Received: {received}'
        super().__init__(
            message=message,
            error_code="ERROR_INVALID_PAYMENT_SUBTOTAL",
            errors={'subtotal': [message]}
        )


class InvalidPaymentDiscountError(PaymentBusinessError):
    """Raised when payment discount does not match expected value."""
    
    def __init__(self, expected: Decimal, received: Decimal) -> None:
        message = f'Invalid payment discount. Expected: {expected}, Received: {received}'
        super().__init__(
            message=message,
            error_code="ERROR_INVALID_PAYMENT_DISCOUNT",
            errors={'total_discount': [message]}
        )

