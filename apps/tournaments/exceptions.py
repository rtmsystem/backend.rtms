from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any

class TournamentBusinessError(ValidationError):
    """Base exception for tournament business logic errors with error code."""
    
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

class DivisionInsufficientApprovedPlayersError(TournamentBusinessError):
    """Raised when a division is not ready for publication."""
    def __init__(self, approved_count: int) -> None:
        message = (
            f'Division cannot be published. '
            f'It must have at least 2 approved players. '
            f'Currently has {approved_count}.'
        )
        super().__init__(
            message=message,
            error_code="ERROR_LESS_TWO_INVOLVEMENT",
            errors={'division': [message]}
        )

class DivisionHasPendingInvolvementsError(TournamentBusinessError):
    """Raised when division has pending involvements."""
    
    def __init__(self, pending_count: int) -> None:
        message = (
            f'Division cannot be published. '
            f'It must have no pending players. '
            f'There are {pending_count} pending involvements.'
        )
        super().__init__(
            message=message,
            error_code="ERROR_PENDING_INVOLVEMENTS",
            errors={'division': [message]}
        )

class DivisionAlreadyPublishedError(TournamentBusinessError):
    """Raised when trying to publish an already published division."""
    
    def __init__(self) -> None:
        message = 'This division is already published.'
        super().__init__(
            message=message,
            error_code="ERROR_DIVISION_ALREADY_PUBLISHED",
            errors={'division': [message]}
        )

class DivisionRegistrationClosedError(TournamentBusinessError):
    """Raised when trying to register in a closed division."""
    
    def __init__(self) -> None:
        message = 'Registration for this division is closed. No new registrations are allowed.'
        super().__init__(
            message=message,
            error_code="ERROR_DIVISION_REGISTRATION_CLOSED",
            errors={'division': [message]}
        )