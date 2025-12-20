"""
Custom exceptions for matches app with error codes for i18n.
"""
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any


class MatchBusinessError(ValidationError):
    """Base exception for match business logic errors with error code."""
    
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


class DivisionNotPublishedError(MatchBusinessError):
    """Raised when trying to create a match for an unpublished division."""
    
    def __init__(self) -> None:
        message = 'Matches can only be created for published divisions.'
        super().__init__(
            message=message,
            error_code="ERROR_DIVISION_NOT_PUBLISHED",
            errors={'division': [message]}
        )


class PlayerNotApprovedError(MatchBusinessError):
    """Raised when a player is not approved in the division."""
    
    def __init__(self, player_name: str) -> None:
        message = f'Player {player_name} is not approved in this division.'
        super().__init__(
            message=message,
            error_code="ERROR_PLAYER_NOT_APPROVED",
            errors={'player': [message]}
        )


class DuplicateMatchError(MatchBusinessError):
    """Raised when trying to create a duplicate match."""
    
    def __init__(self) -> None:
        message = 'A match between these players already exists in this division.'
        super().__init__(
            message=message,
            error_code="ERROR_DUPLICATE_MATCH",
            errors={'match': [message]}
        )


class MatchAlreadyCompletedError(MatchBusinessError):
    """Raised when trying to modify a completed match."""
    
    def __init__(self) -> None:
        message = 'This match is already completed and cannot be modified.'
        super().__init__(
            message=message,
            error_code="ERROR_MATCH_ALREADY_COMPLETED",
            errors={'match': [message]}
        )


class InvalidScoreError(MatchBusinessError):
    """Raised when score is invalid."""
    
    def __init__(self, reason: str) -> None:
        message = f'Invalid score: {reason}'
        super().__init__(
            message=message,
            error_code="ERROR_INVALID_SCORE",
            errors={'score': [message]}
        )


class InsufficientPlayersError(MatchBusinessError):
    """Raised when there are not enough players to generate bracket."""
    
    def __init__(self, required: int, current: int) -> None:
        message = (
            f'Insufficient players to generate bracket. '
            f'Required: {required}, Current: {current}'
        )
        super().__init__(
            message=message,
            error_code="ERROR_INSUFFICIENT_PLAYERS_FOR_GENERATION",
            errors={'division': [message]}
        )


class MatchNotFoundError(MatchBusinessError):
    """Raised when a match is not found."""
    
    def __init__(self, match_id: Optional[int] = None) -> None:
        if match_id:
            message = f'Match with id {match_id} not found.'
        else:
            message = 'Match not found.'
        super().__init__(
            message=message,
            error_code="ERROR_MATCH_NOT_FOUND",
            errors={'match': [message]}
        )


class InvalidMatchFormatError(MatchBusinessError):
    """Raised when division format is not supported for bracket generation."""
    
    def __init__(self, format_name: str) -> None:
        message = (
            f'Bracket generation is only supported for Single Elimination (KNOCKOUT) '
            f'and Double Elimination (DOUBLE_SLASH) formats. '
            f'Current format: {format_name}'
        )
        super().__init__(
            message=message,
            error_code="ERROR_INVALID_MATCH_FORMAT",
            errors={'division': [message]}
        )


class MatchCodeAlreadyExistsError(MatchBusinessError):
    """Raised when match code already exists in the division."""
    
    def __init__(self, match_code: str) -> None:
        message = f'Match code "{match_code}" already exists in this division.'
        super().__init__(
            message=message,
            error_code="ERROR_MATCH_CODE_ALREADY_EXISTS",
            errors={'match_code': [message]}
        )


class CannotDeleteMatchError(MatchBusinessError):
    """Raised when trying to delete a match that cannot be deleted."""
    
    def __init__(self, reason: str) -> None:
        message = f'Cannot delete match: {reason}'
        super().__init__(
            message=message,
            error_code="ERROR_CANNOT_DELETE_MATCH",
            errors={'match': [message]}
        )


class InvalidBracketStructureError(MatchBusinessError):
    """Raised when bracket structure is invalid."""
    
    def __init__(self, reason: str) -> None:
        message = f'Invalid bracket structure: {reason}'
        super().__init__(
            message=message,
            error_code="ERROR_INVALID_BRACKET_STRUCTURE",
            errors={'bracket': [message]}
        )


class DivisionHasExistingMatchesError(MatchBusinessError):
    """Raised when division already has matches."""
    
    def __init__(self) -> None:
        message = 'Division already has matches. Please delete existing matches before generating a new bracket.'
        super().__init__(
            message=message,
            error_code="ERROR_DIVISION_HAS_EXISTING_MATCHES",
            errors={'division': [message]}
        )


class PartnersInSinglesError(MatchBusinessError):
    """Raised when partners are set for singles matches."""
    
    def __init__(self) -> None:
        message = 'Partners cannot be set for singles matches.'
        super().__init__(
            message=message,
            error_code="ERROR_PARTNERS_IN_SINGLES",
            errors={'match_type': [message]}
        )


class MissingPlayersInDoublesError(MatchBusinessError):
    """Raised when players are missing for doubles matches."""
    
    def __init__(self) -> None:
        message = 'Both players are required for doubles matches.'
        super().__init__(
            message=message,
            error_code="ERROR_MISSING_PLAYERS_IN_DOUBLES",
            errors={'match_type': [message]}
        )


class MissingPartnersInDoublesError(MatchBusinessError):
    """Raised when partners are missing for doubles matches."""
    
    def __init__(self) -> None:
        message = 'Both partners are required for doubles matches.'
        super().__init__(
            message=message,
            error_code="ERROR_MISSING_PARTNERS_IN_DOUBLES",
            errors={'match_type': [message]}
        )


class PartnerNotApprovedError(MatchBusinessError):
    """Raised when a partner is not approved in the division."""
    
    def __init__(self, partner_name: str, field: str = 'partner') -> None:
        message = f'Partner {partner_name} is not approved in this division.'
        super().__init__(
            message=message,
            error_code="ERROR_PARTNER_NOT_APPROVED",
            errors={field: [message]}
        )


class MissingPlayersError(MatchBusinessError):
    """Raised when both players are missing and it's not a placeholder."""
    
    def __init__(self) -> None:
        message = 'At least one player must be set (both cannot be NULL unless it is a bye or a bracket placeholder).'
        super().__init__(
            message=message,
            error_code="ERROR_MISSING_PLAYERS",
            errors={'player1': [message]}
        )


class SetNumberExceedsMaxError(MatchBusinessError):
    """Raised when set number exceeds maximum sets."""
    
    def __init__(self, set_number: int, max_sets: int) -> None:
        message = f'Set number cannot exceed maximum sets ({max_sets}).'
        super().__init__(
            message=message,
            error_code="ERROR_SET_NUMBER_EXCEEDS_MAX",
            errors={'set_number': [message]}
        )


class NegativeScoreError(MatchBusinessError):
    """Raised when scores are negative."""
    
    def __init__(self) -> None:
        message = 'Scores cannot be negative.'
        super().__init__(
            message=message,
            error_code="ERROR_NEGATIVE_SCORE",
            errors={'score': [message]}
        )


class InsufficientPointsToWinError(MatchBusinessError):
    """Raised when winner doesn't have required points."""
    
    def __init__(self, player: str, required_points: int) -> None:
        message = f'{player} must have at least {required_points} points to win.'
        super().__init__(
            message=message,
            error_code="ERROR_INSUFFICIENT_POINTS_TO_WIN",
            errors={'winner': [message]}
        )


class WinnerScoreNotHigherError(MatchBusinessError):
    """Raised when winner doesn't have higher score."""
    
    def __init__(self, player: str) -> None:
        message = f'{player} must have a higher score to be the winner.'
        super().__init__(
            message=message,
            error_code="ERROR_WINNER_SCORE_NOT_HIGHER",
            errors={'winner': [message]}
        )

