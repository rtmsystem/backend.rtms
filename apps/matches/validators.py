"""
Business validators for matches app.
"""
from typing import Optional
from django.core.exceptions import ValidationError

from apps.tournaments.models import TournamentDivision, InvolvementStatus
from apps.players.models import PlayerProfile
from .models import Match
from .exceptions import (
    DivisionNotPublishedError,
    PlayerNotApprovedError,
    DuplicateMatchError,
)


class MatchValidator:
    """Validator for match-related business rules."""
    
    @staticmethod
    def validate_division_is_published(division: TournamentDivision) -> None:
        """Validate that division is published."""
        if not division.is_published:
            raise DivisionNotPublishedError()
    
    @staticmethod
    def validate_player_is_approved(
        player: PlayerProfile,
        division: TournamentDivision
    ) -> None:
        """Validate that player is approved in the division."""
        approved = division.involvements.filter(
            status=InvolvementStatus.APPROVED
        )
        
        # Check if player is approved as player or as partner
        player_approved = approved.filter(player=player).exists()
        partner_approved = approved.filter(partner=player).exists()
        
        if not (player_approved or partner_approved):
            raise PlayerNotApprovedError(player.full_name)
    
    @staticmethod
    def validate_team_is_approved(
        player: PlayerProfile,
        partner: Optional[PlayerProfile],
        division: TournamentDivision
    ) -> None:
        """Validate that both players of a team are approved in the division."""
        MatchValidator.validate_player_is_approved(player, division)
        
        if partner:
            MatchValidator.validate_player_is_approved(partner, division)
    
    @staticmethod
    def validate_no_duplicate_match(
        division: TournamentDivision,
        player1: Optional[PlayerProfile],
        player2: Optional[PlayerProfile],
        partner1: Optional[PlayerProfile],
        partner2: Optional[PlayerProfile],
        match_type: str,
        exclude_match_id: Optional[int] = None
    ) -> None:
        """Validate that no duplicate match exists between these players."""
        from .constants import MatchType
        
        query = Match.objects.filter(division=division)
        
        if exclude_match_id:
            query = query.exclude(id=exclude_match_id)
        
        if match_type == MatchType.SINGLES:
            # Check for duplicates in singles: same players in either order
            duplicate = query.filter(
                match_type=MatchType.SINGLES,
                player1__in=[player1, player2],
                player2__in=[player1, player2]
            ).exclude(player1=None).exclude(player2=None).exists()
            
            if duplicate:
                raise DuplicateMatchError()
        
        elif match_type == MatchType.DOUBLES:
            # Check for duplicates in doubles: same teams
            # Team 1: (player1, partner1) vs Team 2: (player2, partner2)
            duplicate = query.filter(
                match_type=MatchType.DOUBLES,
                player1__in=[player1, partner1],
                partner1__in=[player1, partner1],
                player2__in=[player2, partner2],
                partner2__in=[player2, partner2]
            ).exclude(player1=None).exclude(player2=None).exists()
            
            # Also check reverse order
            if not duplicate:
                duplicate = query.filter(
                    match_type=MatchType.DOUBLES,
                    player1__in=[player2, partner2],
                    partner1__in=[player2, partner2],
                    player2__in=[player1, partner1],
                    partner2__in=[player1, partner1]
                ).exclude(player1=None).exclude(player2=None).exists()
            
            if duplicate:
                raise DuplicateMatchError()
    
    @staticmethod
    def validate_match_code_unique(
        division: TournamentDivision,
        match_code: str,
        exclude_match_id: Optional[int] = None
    ) -> None:
        """Validate that match code is unique within the division."""
        from .exceptions import MatchCodeAlreadyExistsError
        
        query = Match.objects.filter(division=division, match_code=match_code)
        
        if exclude_match_id:
            query = query.exclude(id=exclude_match_id)
        
        if query.exists():
            raise MatchCodeAlreadyExistsError(match_code)
    
    @staticmethod
    def validate_match_configuration(
        max_sets: int,
        points_per_set: int
    ) -> None:
        """Validate match configuration values."""
        if not (3 <= max_sets <= 10):
            raise ValidationError({
                'max_sets': 'Maximum sets must be between 3 and 10.'
            })
        
        if not (1 <= points_per_set <= 50):
            raise ValidationError({
                'points_per_set': 'Points per set must be between 1 and 50.'
            })
    
    @classmethod
    def validate_match_creation_rules(
        cls,
        division: TournamentDivision,
        player1: Optional[PlayerProfile],
        player2: Optional[PlayerProfile],
        partner1: Optional[PlayerProfile],
        partner2: Optional[PlayerProfile],
        match_type: str,
        match_code: str,
        max_sets: int,
        points_per_set: int
    ) -> None:
        """Validate all rules for match creation."""
        # Validate division is published
        cls.validate_division_is_published(division)
        
        # Validate match code is unique
        cls.validate_match_code_unique(division, match_code)
        
        # Validate configuration
        cls.validate_match_configuration(max_sets, points_per_set)
        
        # Validate players are approved (skip if NULL for byes)
        if match_type == 'singles':
            if player1:
                cls.validate_player_is_approved(player1, division)
            if player2:
                cls.validate_player_is_approved(player2, division)
            
            # Validate no duplicate
            if player1 and player2:
                cls.validate_no_duplicate_match(
                    division, player1, player2, None, None, match_type
                )
        
        elif match_type == 'doubles':
            if player1 and partner1:
                cls.validate_team_is_approved(player1, partner1, division)
            if player2 and partner2:
                cls.validate_team_is_approved(player2, partner2, division)
            
            # Validate no duplicate
            if player1 and partner1 and player2 and partner2:
                cls.validate_no_duplicate_match(
                    division, player1, player2, partner1, partner2, match_type
                )

