"""
Match models for managing tournament matches.
"""
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from .constants import MatchType, MatchStatus, SetWinner
from .exceptions import (
    DivisionNotPublishedError,
    PartnersInSinglesError,
    MissingPlayersInDoublesError,
    MissingPartnersInDoublesError,
    PlayerNotApprovedError,
    PartnerNotApprovedError,
    MissingPlayersError,
    SetNumberExceedsMaxError,
    NegativeScoreError,
    InsufficientPointsToWinError,
    WinnerScoreNotHigherError,
)


class Match(models.Model):
    """
    Model representing a match in a tournament division.
    Supports singles and doubles matches with configurable sets and points.
    """
    # Relations
    division = models.ForeignKey(
        'tournaments.TournamentDivision',
        on_delete=models.CASCADE,
        related_name='matches',
        verbose_name='Division',
        help_text='Division in which the match is played'
    )
    
    match_code = models.CharField(
        max_length=20,
        verbose_name='Match Code',
        help_text='Unique match code within division (M1, M2, LM1, etc.)'
    )
    
    # Players
    player1 = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='matches_as_player1',
        null=True,
        blank=True,
        verbose_name='Player 1',
        help_text='Player 1 or Team 1 player 1. Can be NULL for byes.'
    )
    
    player2 = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='matches_as_player2',
        null=True,
        blank=True,
        verbose_name='Player 2',
        help_text='Player 2 in singles. Can be NULL for byes.'
    )
    
    partner1 = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='matches_as_partner1',
        null=True,
        blank=True,
        verbose_name='Partner 1',
        help_text='Partner of player 1 for doubles matches'
    )
    
    partner2 = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='matches_as_partner2',
        null=True,
        blank=True,
        verbose_name='Partner 2',
        help_text='Partner of player 2 for doubles matches'
    )
    
    # Match configuration (CONFIGURABLE)
    max_sets = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(10)],
        verbose_name='Maximum Sets',
        help_text='Maximum number of sets for this match (3-10)'
    )
    
    points_per_set = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='Points Per Set',
        help_text='Points required to win a set (1-50)'
    )
    
    # Match type and status
    match_type = models.CharField(
        max_length=10,
        choices=MatchType.choices,
        verbose_name='Match Type',
        help_text='Type of match (singles or doubles)'
    )
    
    status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.PENDING,
        verbose_name='Status',
        help_text='Current status of the match'
    )
    
    # Bracket structure
    round_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Round Number',
        help_text='Round number in the bracket'
    )
    
    is_losers_bracket = models.BooleanField(
        default=False,
        verbose_name='Losers Bracket',
        help_text='Whether this match is in the losers bracket'
    )
    
    next_match = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_matches',
        verbose_name='Next Match',
        help_text='Next match in the bracket that the winner will play'
    )
    
    # Winner
    winner = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches_won',
        verbose_name='Winner',
        help_text='Winner of the match (player or team player 1)'
    )
    
    winner_partner = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches_won_as_partner',
        verbose_name='Winner Partner',
        help_text='Winner partner for doubles matches'
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Scheduled At',
        help_text='Scheduled date and time for the match'
    )

    location = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Location',
        help_text='Court or location where the match is played'
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Started At',
        help_text='Actual start date and time of the match'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
        help_text='Completion date and time of the match'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_matches',
        verbose_name='Created By',
        help_text='User who created the match'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Notes',
        help_text='Additional notes about the match'
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
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'
        ordering = ['division', 'round_number', 'match_code']
        unique_together = [
            ('division', 'match_code'),
        ]
        indexes = [
            models.Index(fields=['division']),
            models.Index(fields=['match_code']),
            models.Index(fields=['status']),
            models.Index(fields=['match_type']),
            models.Index(fields=['round_number']),
            models.Index(fields=['is_losers_bracket']),
            models.Index(fields=['player1', 'player2']),
        ]
    
    def __str__(self) -> str:
        division_name = self.division.name if self.division else 'Unknown'
        return f"{self.match_code} - {division_name} ({self.get_status_display()})"
    
    def clean(self) -> None:
        """Validate match data."""
        from apps.tournaments.models import InvolvementStatus
        
        # Validate byes (at least one player must be set)
        # Exception: allow empty players for future round matches (placeholders)
        # These will be populated when previous matches complete
        is_placeholder = (
            self.status == MatchStatus.PENDING and (
                # Future rounds in any bracket (round > 1)
                (self.round_number and self.round_number > 1) or
                # Grand Final (round_number 999) - special case
                (self.round_number == 999) or
                # First round in losers bracket (will be populated from winners bracket)
                (self.round_number == 1 and self.is_losers_bracket)
            )
        )

        # Validate division is published
        if self.division and not self.division.is_published:
            raise DivisionNotPublishedError()
        
        # Validate match type logic
        if self.match_type == MatchType.SINGLES:
            if self.partner1 or self.partner2:
                raise PartnersInSinglesError()
        elif self.match_type == MatchType.DOUBLES:
            # Skip validation if it is a placeholder match
            if not is_placeholder:
                if not (self.player1 and self.player2):
                    raise MissingPlayersInDoublesError()
                if not (self.partner1 and self.partner2):
                    raise MissingPartnersInDoublesError()
        
        # Validate players are approved in division
        if self.division:
            approved_involvements = self.division.involvements.filter(
                status=InvolvementStatus.APPROVED
            )
            
            if self.player1:
                if not approved_involvements.filter(player=self.player1).exists():
                    raise PlayerNotApprovedError(self.player1.full_name)
            
            if self.player2:
                if not approved_involvements.filter(player=self.player2).exists():
                    raise PlayerNotApprovedError(self.player2.full_name)
            
            # Validate partners for doubles
            if self.match_type == MatchType.DOUBLES:
                if self.partner1:
                    partner_involvement = approved_involvements.filter(
                        player=self.partner1
                    ).exists()
                    # Also check if partner is partner in another involvement
                    partner_as_partner = approved_involvements.filter(
                        partner=self.partner1
                    ).exists()
                    
                    if not (partner_involvement or partner_as_partner):
                        raise PartnerNotApprovedError(self.partner1.full_name, 'partner1')
                
                if self.partner2:
                    partner_involvement = approved_involvements.filter(
                        player=self.partner2
                    ).exists()
                    partner_as_partner = approved_involvements.filter(
                        partner=self.partner2
                    ).exists()
                    
                    if not (partner_involvement or partner_as_partner):
                        raise PartnerNotApprovedError(self.partner2.full_name, 'partner2')
        
        if not self.player1 and not self.player2 and not is_placeholder:
            raise MissingPlayersError()
    
    def save(self, *args, **kwargs) -> None:
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def sets_to_win(self) -> int:
        """Calculate number of sets needed to win."""
        return (self.max_sets // 2) + 1
    
    @property
    def sets_won_by_player1(self) -> int:
        """Get number of sets won by player 1."""
        return self.sets.filter(winner=SetWinner.PLAYER1).count()
    
    @property
    def sets_won_by_player2(self) -> int:
        """Get number of sets won by player 2."""
        return self.sets.filter(winner=SetWinner.PLAYER2).count()
    
    @property
    def is_completed(self) -> bool:
        """Check if match is completed."""
        return self.status == MatchStatus.COMPLETED
    
    @property
    def has_winner(self) -> bool:
        """Check if match has a winner."""
        return self.winner is not None


class Set(models.Model):
    """
    Model representing a set within a match.
    """
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='sets',
        verbose_name='Match',
        help_text='Match this set belongs to'
    )
    
    set_number = models.PositiveIntegerField(
        verbose_name='Set Number',
        help_text='Set number (1, 2, 3, ...)'
    )
    
    player1_score = models.PositiveIntegerField(
        default=0,
        verbose_name='Player 1 Score',
        help_text='Score of player/team 1'
    )
    
    player2_score = models.PositiveIntegerField(
        default=0,
        verbose_name='Player 2 Score',
        help_text='Score of player/team 2'
    )
    
    winner = models.CharField(
        max_length=10,
        choices=SetWinner.choices,
        null=True,
        blank=True,
        verbose_name='Winner',
        help_text='Winner of this set'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
        help_text='Completion date and time of the set'
    )
    
    class Meta:
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'
        ordering = ['match', 'set_number']
        unique_together = [
            ('match', 'set_number'),
        ]
        indexes = [
            models.Index(fields=['match']),
            models.Index(fields=['set_number']),
        ]
    
    def __str__(self) -> str:
        return f"Set {self.set_number} - {self.match.match_code} ({self.player1_score}-{self.player2_score})"
    
    def clean(self) -> None:
        """Validate set data."""
        # Validate set number doesn't exceed max_sets
        if self.match and self.set_number > self.match.max_sets:
            raise SetNumberExceedsMaxError(self.set_number, self.match.max_sets)
        
        # Validate scores
        if self.player1_score < 0 or self.player2_score < 0:
            raise NegativeScoreError()
        
        # Validate winner has required points
        if self.winner:
            required_points = self.match.points_per_set if self.match else 15
            
            if self.winner == SetWinner.PLAYER1 and self.player1_score < required_points:
                raise InsufficientPointsToWinError('Player 1', required_points)
            
            if self.winner == SetWinner.PLAYER2 and self.player2_score < required_points:
                raise InsufficientPointsToWinError('Player 2', required_points)
            
            # Validate winner has higher score
            if self.winner == SetWinner.PLAYER1 and self.player1_score <= self.player2_score:
                raise WinnerScoreNotHigherError('Player 1')
            
            if self.winner == SetWinner.PLAYER2 and self.player2_score <= self.player1_score:
                raise WinnerScoreNotHigherError('Player 2')
    
    def save(self, *args, **kwargs) -> None:
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

