"""
Validators for payments app.
"""
from decimal import Decimal
from typing import Any
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_discount_amount(
    discount_amount: Decimal,
    subscription_fee: Decimal,
    field_name: str = 'discount_amount'
) -> None:
    """
    Validate that discount amount does not exceed subscription fee.
    
    Args:
        discount_amount: The discount amount to validate
        subscription_fee: The subscription fee to compare against
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If discount exceeds subscription fee
    """
    if discount_amount < 0:
        raise ValidationError(
            f'{field_name} cannot be negative.',
            code='negative_discount'
        )
    
    if discount_amount > subscription_fee:
        raise ValidationError(
            f'{field_name} cannot exceed subscription fee ({subscription_fee}).',
            code='discount_exceeds_fee'
        )


def validate_discount_deadline(deadline: Any) -> None:
    """
    Validate that discount deadline is valid.
    
    Args:
        deadline: The deadline datetime to validate
        
    Raises:
        ValidationError: If deadline is in the past
    """
    if deadline and deadline < timezone.now():
        raise ValidationError(
            'Discount deadline cannot be in the past.',
            code='past_deadline'
        )

