"""
Services for match business logic.
"""
import logging
import math
import random
from typing import Optional, Dict, Any, List, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, datetime, timedelta

from apps.tournaments.models import TournamentDivision, InvolvementStatus, TournamentFormat, ParticipantType
from apps.players.models import PlayerProfile
from .models import Match, Set
from .constants import MatchType, MatchStatus, SetWinner
from .validators import MatchValidator
from .exceptions import (
    MatchBusinessError,
    MatchAlreadyCompletedError,
    CannotDeleteMatchError,
    InsufficientPlayersError,
    InvalidMatchFormatError,
    DivisionHasExistingMatchesError,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class MatchCreationService:
    """Service to handle match creation with business logic."""
    
    def __init__(
        self,
        division: TournamentDivision,
        match_code: str,
        match_type: str,
        user: Optional[User] = None,
        player1: Optional[PlayerProfile] = None,
        player2: Optional[PlayerProfile] = None,
        partner1: Optional[PlayerProfile] = None,
        partner2: Optional[PlayerProfile] = None,
        max_sets: int = 5,
        points_per_set: int = 15,
        round_number: Optional[int] = None,
        is_losers_bracket: bool = False,
        next_match: Optional[Match] = None,
        scheduled_at: Optional[timezone.datetime] = None,
        location: Optional[str] = None,
        notes: str = '',
    ) -> None:
        self.division = division
        self.match_code = match_code
        self.match_type = match_type
        self.user = user
        self.player1 = player1
        self.player2 = player2
        self.partner1 = partner1
        self.partner2 = partner2
        self.max_sets = max_sets
        self.points_per_set = points_per_set
        self.round_number = round_number
        self.is_losers_bracket = is_losers_bracket
        self.next_match = next_match
        self.scheduled_at = scheduled_at
        self.location = location
        self.notes = notes
        self.match = None
    
    def validate_business_rules(self) -> None:
        """Validate business rules."""
        MatchValidator.validate_match_creation_rules(
            division=self.division,
            player1=self.player1,
            player2=self.player2,
            partner1=self.partner1,
            partner2=self.partner2,
            match_type=self.match_type,
            match_code=self.match_code,
            max_sets=self.max_sets,
            points_per_set=self.points_per_set,
        )
    
    def create_match(self) -> Match:
        """Create the match."""
        self.match = Match.objects.create(
            division=self.division,
            match_code=self.match_code,
            match_type=self.match_type,
            player1=self.player1,
            player2=self.player2,
            partner1=self.partner1,
            partner2=self.partner2,
            max_sets=self.max_sets,
            points_per_set=self.points_per_set,
            round_number=self.round_number,
            is_losers_bracket=self.is_losers_bracket,
            next_match=self.next_match,
            scheduled_at=self.scheduled_at,
            location=self.location,
            notes=self.notes,
            created_by=self.user,
            status=MatchStatus.PENDING,
        )
        return self.match
    
    @transaction.atomic
    def execute(self) -> Match:
        """Execute the complete service flow."""
        self.validate_business_rules()
        self.create_match()
        
        logger.info(
            f"Match {self.match.id} ({self.match_code}) created in division "
            f"{self.division.id} by user {self.user.id if self.user else 'system'}"
        )
        
        return self.match


class MatchUpdateService:
    """Service to handle match updates with business logic."""
    
    def __init__(
        self,
        match: Match,
        data: Dict[str, Any],
        user: Optional[User] = None
    ) -> None:
        self.match = match
        self.data = data
        self.user = user
    
    def validate_business_rules(self) -> None:
        """Validate business rules."""
        # Cannot update completed matches
        if self.match.status == MatchStatus.COMPLETED:
            raise MatchAlreadyCompletedError()
        
        # Validate match code if being updated
        if 'match_code' in self.data:
            MatchValidator.validate_match_code_unique(
                division=self.match.division,
                match_code=self.data['match_code'],
                exclude_match_id=self.match.id
            )
        
        # Validate configuration if being updated
        max_sets = self.data.get('max_sets', self.match.max_sets)
        points_per_set = self.data.get('points_per_set', self.match.points_per_set)
        MatchValidator.validate_match_configuration(max_sets, points_per_set)
    
    def update_match(self) -> Match:
        """Update the match."""
        for key, value in self.data.items():
            if hasattr(self.match, key):
                setattr(self.match, key, value)
        
        self.match.save()
        return self.match
    
    @transaction.atomic
    def execute(self) -> Match:
        """Execute the complete service flow."""
        self.validate_business_rules()
        self.update_match()
        
        logger.info(
            f"Match {self.match.id} ({self.match.match_code}) updated by "
            f"user {self.user.id if self.user else 'system'}"
        )
        
        return self.match


class MatchDeletionService:
    """Service to handle match deletion with business logic."""
    
    def __init__(
        self,
        match: Match,
        user: Optional[User] = None
    ) -> None:
        self.match = match
        self.user = user
    
    def validate_business_rules(self) -> None:
        """Validate business rules."""
        # Only allow deletion of pending or cancelled matches
        if self.match.status not in [MatchStatus.PENDING, MatchStatus.CANCELLED]:
            raise CannotDeleteMatchError(
                'Only pending or cancelled matches can be deleted.'
            )
        
        # Check if match is referenced by another match
        if self.match.previous_matches.exists():
            raise CannotDeleteMatchError(
                'Cannot delete match that is referenced by other matches in the bracket.'
            )
    
    @transaction.atomic
    def execute(self) -> None:
        """Execute the complete service flow."""
        self.validate_business_rules()
        
        match_code = self.match.match_code
        match_id = self.match.id
        
        self.match.delete()
        
        logger.info(
            f"Match {match_id} ({match_code}) deleted by "
            f"user {self.user.id if self.user else 'system'}"
        )


class MatchListService:
    """Service to handle match listing with filters."""
    
    def __init__(
        self,
        division_id: Optional[int] = None,
        tournament_id: Optional[int] = None,
        match_type: Optional[str] = None,
        status: Optional[str] = None,
        player_id: Optional[int] = None,
        round_number: Optional[int] = None,
        is_losers_bracket: Optional[bool] = None,
        match_code: Optional[str] = None,
    ) -> None:
        self.division_id = division_id
        self.tournament_id = tournament_id
        self.match_type = match_type
        self.status = status
        self.player_id = player_id
        self.round_number = round_number
        self.is_losers_bracket = is_losers_bracket
        self.match_code = match_code
    
    def get_queryset(self):
        """Get filtered queryset with optimizations."""
        from django.db.models import Q
        
        queryset = Match.objects.select_related(
            'division',
            'division__tournament',
            'player1',
            'player2',
            'partner1',
            'partner2',
            'winner',
            'created_by',
            'next_match',
        ).prefetch_related(
            'sets'
        )
        
        # Apply filters
        if self.division_id:
            queryset = queryset.filter(division_id=self.division_id)
        
        if self.tournament_id:
            queryset = queryset.filter(division__tournament_id=self.tournament_id)
        
        if self.match_type:
            queryset = queryset.filter(match_type=self.match_type)
        
        if self.status:
            queryset = queryset.filter(status=self.status)
        
        if self.round_number is not None:
            queryset = queryset.filter(round_number=self.round_number)
        
        if self.is_losers_bracket is not None:
            queryset = queryset.filter(is_losers_bracket=self.is_losers_bracket)
        
        if self.match_code:
            queryset = queryset.filter(match_code__icontains=self.match_code)
        
        if self.player_id:
            queryset = queryset.filter(
                Q(player1_id=self.player_id) |
                Q(player2_id=self.player_id) |
                Q(partner1_id=self.player_id) |
                Q(partner2_id=self.player_id)
            )
        
        return queryset.order_by('scheduled_at','created_at')
    
    def execute(self):
        """Execute the service flow."""
        return self.get_queryset()


class MatchScoreService:
    """Service to handle match score registration and winner calculation."""
    
    def __init__(
        self,
        match: Match,
        sets_data: List[Dict[str, Any]],
        user: Optional[User] = None
    ) -> None:
        self.match = match
        self.sets_data = sets_data
        self.user = user
    
    def validate_match_status(self) -> None:
        """Validate that match can have scores registered."""
        if self.match.status == MatchStatus.COMPLETED:
            raise MatchAlreadyCompletedError()
        
        if self.match.status == MatchStatus.CANCELLED:
            raise MatchBusinessError(
                message='Cannot register scores for a cancelled match.',
                error_code="ERROR_MATCH_CANCELLED",
                errors={'match': ['Cannot register scores for a cancelled match.']}
            )
    
    def create_or_update_sets(self) -> List[Set]:
        """Create or update sets with scores."""
        created_sets = []
        
        for set_data in self.sets_data:
            set_number = set_data['set_number']
            player1_score = set_data.get('player1_score', 0)
            player2_score = set_data.get('player2_score', 0)
            
            # Determine winner
            winner = None
            if player1_score > player2_score and player1_score >= self.match.points_per_set:
                winner = SetWinner.PLAYER1
            elif player2_score > player1_score and player2_score >= self.match.points_per_set:
                winner = SetWinner.PLAYER2
            
            # Create or update set
            set_obj, created = Set.objects.update_or_create(
                match=self.match,
                set_number=set_number,
                defaults={
                    'player1_score': player1_score,
                    'player2_score': player2_score,
                    'winner': winner,
                    'completed_at': timezone.now() if winner else None,
                }
            )
            created_sets.append(set_obj)
        
        return created_sets
    
    def calculate_winner(self) -> Optional[Tuple[PlayerProfile, Optional[PlayerProfile]]]:
        """Calculate match winner based on sets won."""
        sets_won_p1 = self.match.sets_won_by_player1
        sets_won_p2 = self.match.sets_won_by_player2
        sets_to_win = self.match.sets_to_win
        
        # Check if player 1 won
        if sets_won_p1 >= sets_to_win:
            return (self.match.player1, self.match.partner1)
        
        # Check if player 2 won
        if sets_won_p2 >= sets_to_win:
            return (self.match.player2, self.match.partner2)
        
        return None
    
    def update_match_status(self, winner: Optional[Tuple[PlayerProfile, Optional[PlayerProfile]]]) -> None:
        """Update match status based on winner."""
        if winner:
            winner_player, winner_partner = winner
            self.match.winner = winner_player
            self.match.winner_partner = winner_partner
            self.match.status = MatchStatus.COMPLETED
            self.match.completed_at = timezone.now()
            
            # Update next match if exists
            if self.match.next_match:
                # Set winner as player in next match
                if not self.match.next_match.player1:
                    self.match.next_match.player1 = winner_player
                    if self.match.match_type == MatchType.DOUBLES and winner_partner:
                        self.match.next_match.partner1 = winner_partner
                elif not self.match.next_match.player2:
                    self.match.next_match.player2 = winner_player
                    if self.match.match_type == MatchType.DOUBLES and winner_partner:
                        self.match.next_match.partner2 = winner_partner
                
                self.match.next_match.save()
            
            self.match.save()
        else:
            # Match is in progress
            if self.match.status == MatchStatus.PENDING:
                self.match.status = MatchStatus.IN_PROGRESS
                self.match.started_at = timezone.now()
                self.match.save()
    
    @transaction.atomic
    def execute(self) -> Match:
        """Execute the complete service flow."""
        self.validate_match_status()
        self.create_or_update_sets()
        
        # Refresh match to get updated sets
        self.match.refresh_from_db()
        
        # Calculate and update winner
        winner = self.calculate_winner()
        self.update_match_status(winner)
        
        # Trigger standings calculation if applicable
        self.trigger_standings_calculation()
        
        logger.info(
            f"Scores registered for match {self.match.id} ({self.match.match_code}) "
            f"by user {self.user.id if self.user else 'system'}"
        )
        
        return self.match

    def trigger_standings_calculation(self) -> None:
        """Trigger standings calculation for the division."""
        # Only for ROUND_ROBIN_KNOCKOUT format
        # Import dynamically to avoid circular imports
        from apps.tournaments.models import TournamentFormat
        
        if self.match.division.format == TournamentFormat.ROUND_ROBIN_KNOCKOUT:
            try:
                from apps.tournaments.services import StandingCalculationService
                
                service = StandingCalculationService(
                    division=self.match.division,
                    user=self.user
                )
                service.execute()
                
                logger.info(
                    f"Standings calculated for division {self.match.division.id} "
                    f"triggered by match {self.match.id}"
                )
            except Exception as e:
                # Log error but don't fail the match score update
                logger.error(
                    f"Error calculating standings after match {self.match.id}: {e}"
                )


class MatchBracketGenerationService:
    """Service to generate complete brackets for a division."""
    
    def __init__(
        self,
        division: TournamentDivision,
        max_sets: int = 5,
        points_per_set: int = 15,
        user: Optional[User] = None
    ) -> None:
        self.division = division
        self.max_sets = max_sets
        self.points_per_set = points_per_set
        self.user = user
        self.created_matches: List[Match] = []
        self.match_counter = 1  # For winners bracket
        self.loser_match_counter = 1  # For losers bracket
    
    def validate_division(self) -> None:
        """Validate division can have brackets generated."""
        from .validators import MatchValidator
        
        # Validate division is published
        MatchValidator.validate_division_is_published(self.division)
        
        # Validate format is supported
        if self.division.format not in [
            TournamentFormat.KNOCKOUT, 
            TournamentFormat.DOUBLE_SLASH,
            TournamentFormat.ROUND_ROBIN_KNOCKOUT
        ]:
            raise InvalidMatchFormatError(self.division.get_format_display())
        
        # Check if division already has matches
        existing_matches = Match.objects.filter(division=self.division).exists()
        if existing_matches:
            raise DivisionHasExistingMatchesError()
    
    def get_participants(self) -> List[Any]:
        """Get approved participants from division."""
        involvements = self.division.involvements.filter(
            status=InvolvementStatus.APPROVED
        ).select_related('player', 'partner')
        
        if self.division.participant_type == ParticipantType.SINGLE:
            # For singles, return list of players
            participants = []
            for involvement in involvements:
                participants.append({
                    'player1': involvement.player,
                    'player2': None,
                    'partner1': None,
                    'partner2': None,
                })
            return participants
        else:
            # For doubles, return list of teams (player + partner)
            participants = []
            for involvement in involvements:
                if not involvement.partner:
                    # Skip if no partner (shouldn't happen in doubles, but just in case)
                    continue
                participants.append({
                    'player1': involvement.player,
                    'player2': None,
                    'partner1': involvement.partner,
                    'partner2': None,
                })
            return participants
    
    def validate_participants(self, participants: List[Any]) -> None:
        """Validate minimum number of participants."""
        min_required = 2
        
        if len(participants) < min_required:
            raise InsufficientPlayersError(min_required, len(participants))
    
    def generate_match_code(self, is_losers_bracket: bool = False) -> str:
        """Generate unique match code."""
        if is_losers_bracket:
            code = f"LM{self.loser_match_counter}"
            self.loser_match_counter += 1
        else:
            code = f"M{self.match_counter}"
            self.match_counter += 1
        return code
    
    def create_match(
        self,
        division: TournamentDivision,
        match_code: str,
        round_number: int,
        player1: Optional[PlayerProfile] = None,
        player2: Optional[PlayerProfile] = None,
        partner1: Optional[PlayerProfile] = None,
        partner2: Optional[PlayerProfile] = None,
        is_losers_bracket: bool = False,
        next_match: Optional[Match] = None,
    ) -> Match:
        """Create a match."""
        match_type = MatchType.DOUBLES if self.division.participant_type == ParticipantType.DOUBLES else MatchType.SINGLES
        
        match = Match.objects.create(
            division=division,
            match_code=match_code,
            match_type=match_type,
            player1=player1,
            player2=player2,
            partner1=partner1,
            partner2=partner2,
            max_sets=self.max_sets,
            points_per_set=self.points_per_set,
            round_number=round_number,
            is_losers_bracket=is_losers_bracket,
            next_match=next_match,
            status=MatchStatus.PENDING,
            created_by=self.user,
        )
        
        return match
    
    def generate_single_elimination_bracket(self, participants: List[Any]) -> List[Match]:
        """Generate single elimination bracket without bye matches."""
        # Shuffle participants for random seeding
        shuffled = participants.copy()
        random.shuffle(shuffled)
        
        num_participants = len(shuffled)
        
        # If only 1 participant, no matches needed
        if num_participants <= 1:
            return []
        
        all_matches = []
        round_matches = {}  # Store matches by round for connecting
        
        # Calculate the power of 2 we need to reach
        # We find the largest power of 2 that is <= num_participants
        # Then calculate how many participants we need to eliminate
        power_of_2 = 1
        while power_of_2 * 2 <= num_participants:
            power_of_2 *= 2
        
        participants_to_eliminate = num_participants - power_of_2
        preliminary_matches_needed = participants_to_eliminate
        
        participant_index = 0
        
        # Generate preliminary round if needed
        preliminary_matches = []
        if preliminary_matches_needed > 0:
            preliminary_round_number = 1  # Preliminary round uses round_number = 1
            
            for match_idx in range(preliminary_matches_needed):
                match_code = self.generate_match_code(is_losers_bracket=False)
                
                # Each preliminary match has 2 participants
                p1 = shuffled[participant_index] if participant_index < len(shuffled) else None
                p2 = shuffled[participant_index + 1] if participant_index + 1 < len(shuffled) else None
                
                match = self.create_match(
                    division=self.division,
                    match_code=match_code,
                    round_number=preliminary_round_number,
                    player1=p1['player1'] if p1 else None,
                    player2=p2['player1'] if p2 else None,
                    partner1=p1['partner1'] if p1 else None,
                    partner2=p2['partner1'] if p2 else None,
                )
                
                preliminary_matches.append(match)
                all_matches.append(match)
                participant_index += 2
            
            round_matches[preliminary_round_number] = preliminary_matches
        
        # Now we have power_of_2 participants remaining
        # Calculate number of rounds needed for the main bracket
        num_rounds = math.ceil(math.log2(power_of_2)) if power_of_2 > 1 else 1
        
        # Generate first round of main bracket
        # If we have preliminary matches, main bracket starts at round 2
        # Otherwise, it starts at round 1
        first_round_matches = []
        main_bracket_start_round = 2 if preliminary_matches_needed > 0 else 1
        round_number = main_bracket_start_round
        
        # Calculate how many matches we need in the first round
        first_round_matches_needed = power_of_2 // 2
        
        # Get participants that advance directly (didn't play preliminary)
        direct_participants = shuffled[participant_index:]
        
        # Create first round matches
        # Strategy: Pair preliminary winners with direct participants
        # First, assign direct participants to matches
        # Then, connect preliminary winners to the remaining slots
        
        direct_participant_idx = 0
        prelim_match_idx = 0
        
        for match_idx in range(first_round_matches_needed):
            match_code = self.generate_match_code(is_losers_bracket=False)
            
            player1 = None
            player2 = None
            partner1 = None
            partner2 = None
            
            # Fill player1 slot
            if direct_participant_idx < len(direct_participants):
                p = direct_participants[direct_participant_idx]
                player1 = p['player1']
                partner1 = p['partner1']
                direct_participant_idx += 1
            # If no more direct participants, player1 slot will be for a preliminary winner
            # (will be set when preliminary match completes)
            
            # Fill player2 slot
            if direct_participant_idx < len(direct_participants):
                # Use another direct participant
                p = direct_participants[direct_participant_idx]
                player2 = p['player1']
                partner2 = p['partner1']
                direct_participant_idx += 1
            # If no more direct participants, player2 slot will be for a preliminary winner
            # (will be set when preliminary match completes)
            
            match = self.create_match(
                division=self.division,
                match_code=match_code,
                round_number=round_number,
                player1=player1,
                player2=player2,
                partner1=partner1,
                partner2=partner2,
            )
            
            first_round_matches.append(match)
            all_matches.append(match)
        
        # Connect preliminary matches to first round matches
        # Each preliminary winner goes to the first available slot (None) in first round matches
        if preliminary_matches_needed > 0:
            prelim_match_idx = 0
            for first_round_match in first_round_matches:
                if prelim_match_idx >= len(preliminary_matches):
                    break
                
                # Find first available slot (None) in this first round match
                if first_round_match.player1 is None:
                    # Connect preliminary match to player1 slot
                    preliminary_matches[prelim_match_idx].next_match = first_round_match
                    preliminary_matches[prelim_match_idx].save()
                    prelim_match_idx += 1
                elif first_round_match.player2 is None:
                    # Connect preliminary match to player2 slot
                    preliminary_matches[prelim_match_idx].next_match = first_round_match
                    preliminary_matches[prelim_match_idx].save()
                    prelim_match_idx += 1
        
        round_matches[round_number] = first_round_matches
        
        # Generate subsequent rounds
        # Start from the round after the first round of main bracket
        for round_offset in range(1, num_rounds):
            round_num = main_bracket_start_round + round_offset
            previous_round_matches = round_matches[round_num - 1]
            current_round_matches = []
            
            # Each match in this round takes winners from 2 matches in previous round
            for i in range(0, len(previous_round_matches), 2):
                match1 = previous_round_matches[i]
                match2 = previous_round_matches[i + 1] if i + 1 < len(previous_round_matches) else None
                
                match_code = self.generate_match_code(is_losers_bracket=False)
                
                match = self.create_match(
                    division=self.division,
                    match_code=match_code,
                    round_number=round_num,
                    player1=None,  # Will be set when previous matches complete
                    player2=None,
                    partner1=None,
                    partner2=None,
                    next_match=None,
                )
                
                current_round_matches.append(match)
                all_matches.append(match)
                
                # Set next_match for previous round matches
                match1.next_match = match
                match1.save()
                if match2:
                    match2.next_match = match
                    match2.save()
            
            round_matches[round_num] = current_round_matches
        
        return all_matches
    
    def generate_double_elimination_bracket(self, participants: List[Any]) -> List[Match]:
        """Generate double elimination bracket."""
        # Shuffle participants for random seeding
        shuffled = participants.copy()
        random.shuffle(shuffled)
        
        all_matches = []
        
        # First, generate winners bracket (similar to single elimination)
        winners_matches = self._generate_winners_bracket(shuffled)
        all_matches.extend(winners_matches)
        
        # Then generate losers bracket
        losers_matches = self._generate_losers_bracket(winners_matches, shuffled)
        all_matches.extend(losers_matches)
        
        # Finally, create grand final
        grand_final = self._create_grand_final(winners_matches, losers_matches)
        if grand_final:
            all_matches.append(grand_final)
        
        return all_matches
    
    def _generate_winners_bracket(self, participants: List[Any]) -> List[Match]:
        """Generate winners bracket (similar to single elimination)."""
        # Reset counter for winners bracket
        self.match_counter = 1
        
        # Use same logic as single elimination
        return self.generate_single_elimination_bracket(participants)
    
    def _generate_losers_bracket(self, winners_matches: List[Match], participants: List[Any]) -> List[Match]:
        """Generate losers bracket."""
        # Reset counter for losers bracket
        self.loser_match_counter = 1
        
        losers_matches = []
        round_matches = {}  # Store matches by round
        
        # Get all winners bracket rounds
        max_winners_round = max((m.round_number for m in winners_matches), default=0)
        
        # Losers bracket structure:
        # Round 1: Losers from winners round 1 play each other
        # Round 2: Winners from losers round 1 play losers from winners round 2
        # And so on...
        
        # First round of losers bracket: losers from first round of winners bracket
        first_winners_round = [m for m in winners_matches if m.round_number == 1]
        first_losers_round = []
        round_number = 1
        
        # Create matches for first round of losers bracket
        # Losers from winners round 1 play each other
        losers_from_first_round = []
        for winners_match in first_winners_round:
            if winners_match.player2 and not winners_match.is_completed:
                # This match will have a loser (not a bye)
                losers_from_first_round.append(winners_match)
        
        # Create matches for losers (pair them up)
        for i in range(0, len(losers_from_first_round), 2):
            match_code = self.generate_match_code(is_losers_bracket=True)
            
            loser_match = self.create_match(
                division=self.division,
                match_code=match_code,
                round_number=round_number,
                player1=None,  # Will be set when match is lost
                player2=None,
                partner1=None,
                partner2=None,
                is_losers_bracket=True,
            )
            
            first_losers_round.append(loser_match)
            losers_matches.append(loser_match)
        
        round_matches[round_number] = first_losers_round
        
        # Generate subsequent losers bracket rounds
        # Structure: For each winners round after the first:
        # - Winners from previous losers round play against losers from corresponding winners round
        # - Continue until we have the losers bracket final
        for winners_round_num in range(2, max_winners_round + 1):
            losers_round_num = winners_round_num
            
            # Get losers from this winners round
            winners_round_matches = [m for m in winners_matches if m.round_number == winners_round_num]
            previous_losers_round = round_matches.get(losers_round_num - 1, [])
            
            current_losers_round = []
            
            # Calculate how many matches we need in this losers round
            # We need to pair: winners from previous losers round + losers from winners round
            num_matches_needed = len(previous_losers_round)
            
            # Match winners from previous losers round with losers from winners round
            for i in range(num_matches_needed):
                # Get the previous losers match winner (will advance here)
                previous_loser_match = previous_losers_round[i] if i < len(previous_losers_round) else None
                
                # Get corresponding winners match loser (will also play here)
                winners_match = winners_round_matches[i] if i < len(winners_round_matches) else None
                
                match_code = self.generate_match_code(is_losers_bracket=True)
                
                loser_match = self.create_match(
                    division=self.division,
                    match_code=match_code,
                    round_number=losers_round_num,
                    player1=None,  # Will be set when matches complete
                    player2=None,
                    partner1=None,
                    partner2=None,
                    is_losers_bracket=True,
                )
                
                current_losers_round.append(loser_match)
                losers_matches.append(loser_match)
                
                # Connect previous losers match to this one
                if previous_loser_match:
                    previous_loser_match.next_match = loser_match
                    previous_loser_match.save()
            
            if current_losers_round:
                round_matches[losers_round_num] = current_losers_round
        
        # If there's only one match left in the final losers round, that's the losers bracket final
        # Otherwise, we need to consolidate to get the final
        final_losers_round_num = max((m.round_number for m in losers_matches), default=0)
        if final_losers_round_num > 0:
            final_losers_round = [m for m in losers_matches if m.round_number == final_losers_round_num]
            
            # If there's more than one match in the final round, we need a consolidation match
            # (This happens when there are many participants)
            if len(final_losers_round) > 1:
                # Create a consolidation match for the losers bracket final
                match_code = self.generate_match_code(is_losers_bracket=True)
                losers_final = self.create_match(
                    division=self.division,
                    match_code=match_code,
                    round_number=final_losers_round_num + 1,
                    player1=None,
                    player2=None,
                    partner1=None,
                    partner2=None,
                    is_losers_bracket=True,
                )
                
                losers_matches.append(losers_final)
                
                # Connect both final round matches to the losers final
                for match in final_losers_round:
                    match.next_match = losers_final
                    match.save()
        
        return losers_matches
    
    def _create_grand_final(self, winners_matches: List[Match], losers_matches: List[Match]) -> Optional[Match]:
        """Create grand final match."""
        # Find final match from winners bracket
        winners_final = None
        max_winners_round = max((m.round_number for m in winners_matches), default=0)
        winners_final_candidates = [m for m in winners_matches if m.round_number == max_winners_round]
        
        if winners_final_candidates:
            winners_final = winners_final_candidates[0]
        
        # Find final match from losers bracket
        # The losers final should be the match in the highest round of the losers bracket
        losers_final = None
        if losers_matches:
            max_loser_round = max((m.round_number for m in losers_matches), default=0)
            losers_final_candidates = [m for m in losers_matches if m.round_number == max_loser_round]
            
            # If there are multiple matches in the final round, take the last one
            # (the one that doesn't have a next_match set yet)
            for match in losers_final_candidates:
                if not match.next_match:
                    losers_final = match
                    break
            
            # If we didn't find one without next_match, just take the first one
            if not losers_final and losers_final_candidates:
                losers_final = losers_final_candidates[0]
        
        if not winners_final:
            return None
        
        # Grand Final uses special round number 999 and code GF1
        grand_final = self.create_match(
            division=self.division,
            match_code="GF1",  # Grand Final 1
            round_number=999,  # Special round number for Grand Final
            player1=None,  # Will be set when brackets complete
            player2=None,
            partner1=None,
            partner2=None,
            is_losers_bracket=False,
        )
        
        # Connect previous finals
        if winners_final:
            winners_final.next_match = grand_final
            winners_final.save()
        
        if losers_final:
            losers_final.next_match = grand_final
            losers_final.save()
        
        return grand_final
    
    def generate_group_phase_matches(
        self, 
        groups,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        start_hour: Optional[time] = None,
        end_hour: Optional[time] = None,
        available_courts: int = 1,
        match_duration_minutes: int = 60
    ) -> List[Match]:
        """
        Generate round robin matches for group phase and optionally schedule them.
        """
        from apps.tournaments.models import TournamentGroup
        
        all_matches = []
        self.match_counter = 1  # Reset counter for group phase
        
        for group in groups:
            if not isinstance(group, TournamentGroup):
                continue
            
            # Get all standings (participants) in this group
            standings = group.standings.select_related(
                'involvement__player', 
                'involvement__partner'
            ).all()
            
            involvements = [standing.involvement for standing in standings]
            num_participants = len(involvements)
            
            # Generate all possible match combinations (round robin)
            # For n participants: n * (n-1) / 2 matches
            match_number = 1
            
            for i in range(num_participants):
                for j in range(i + 1, num_participants):
                    inv1 = involvements[i]
                    inv2 = involvements[j]
                    
                    # Create match code: G{group_number}-M{match_number}
                    match_code = f"G{group.group_number}-M{match_number}"
                    
                    # Determine players
                    player1 = inv1.player
                    player2 = inv2.player
                    partner1 = inv1.partner if self.division.participant_type == ParticipantType.DOUBLES else None
                    partner2 = inv2.partner if self.division.participant_type == ParticipantType.DOUBLES else None
                    
                    # Use negative round_number to identify group phase matches
                    match = self.create_match(
                        division=self.division,
                        match_code=match_code,
                        round_number=-group.group_number,  # Negative for group phase
                        player1=player1,
                        player2=player2,
                        partner1=partner1,
                        partner2=partner2,
                        is_losers_bracket=False,
                        next_match=None,  # No next_match in group phase
                    )
                    
                    all_matches.append(match)
                    match_number += 1
        
        # Schedule matches if scheduling parameters are provided
        if start_date and end_date and start_hour and end_hour:
            self._schedule_matches(
                all_matches,
                start_date,
                end_date,
                start_hour,
                end_hour,
                available_courts,
                match_duration_minutes
            )
        
        logger.info(
            f"Generated {len(all_matches)} group phase matches for division "
            f"{self.division.id} ({self.division.name})"
        )
        
        return all_matches

    def _schedule_matches(
        self,
        matches: List[Match],
        start_date: date,
        end_date: date,
        start_hour: time,
        end_hour: time,
        available_courts: int,
        match_duration_minutes: int
    ) -> None:
        """Schedule matches based on constraints."""
        current_date = start_date
        duration = timedelta(minutes=match_duration_minutes)
        
        # Generate time slots
        slots = []
        while current_date <= end_date:
            current_time = datetime.combine(current_date, start_hour)
            end_time_limit = datetime.combine(current_date, end_hour)
            
            while current_time + duration <= end_time_limit:
                slot_start = current_time
                slot_end = current_time + duration
                
                # Create slots for each court
                for court_num in range(1, available_courts + 1):
                    slots.append({
                        'start': timezone.make_aware(slot_start),
                        'end': timezone.make_aware(slot_end),
                        'location': f"Cancha {court_num}",
                        'court_id': court_num
                    })
                
                current_time += duration
            
            current_date += timedelta(days=1)
        
        # Sort slots by time
        slots.sort(key=lambda x: x['start'])
        
        # Track player schedules to avoid conflicts
        # Map: player_id -> List[(start, end)]
        player_schedules = {}
        
        # Assign matches to slots
        slot_index = 0
        scheduled_count = 0
        
        # Track used slots to prevent double booking
        used_slots = set()
        
        for match in matches:
            if slot_index >= len(slots):
                logger.warning(f"Not enough slots to schedule match {match.match_code}")
                break
                
            # Find a suitable slot
            assigned = False
            
            # Identify players in this match
            players_in_match = []
            if match.player1: players_in_match.append(match.player1.id)
            if match.player2: players_in_match.append(match.player2.id)
            if match.partner1: players_in_match.append(match.partner1.id)
            if match.partner2: players_in_match.append(match.partner2.id)
            
            for i in range(len(slots)):
                if i in used_slots:
                    continue
                
                slot = slots[i]
                start = slot['start']
                end = slot['end']
                
                # Check player conflicts
                has_conflict = False
                for player_id in players_in_match:
                    if player_id in player_schedules:
                        for busy_start, busy_end in player_schedules[player_id]:
                            # Check overlap
                            if (start < busy_end) and (end > busy_start):
                                has_conflict = True
                                break
                    if has_conflict:
                        break
                
                if not has_conflict:
                    # Assign match to this slot
                    match.scheduled_at = start
                    match.location = slot['location']
                    match.save()
                    
                    # Mark slot as used
                    used_slots.add(i)
                    
                    # Mark players as busy
                    for player_id in players_in_match:
                        if player_id not in player_schedules:
                            player_schedules[player_id] = []
                        player_schedules[player_id].append((start, end))
                    
                    assigned = True
                    scheduled_count += 1
                    break
            
            if not assigned:
                logger.warning(f"Could not find valid slot for match {match.match_code}")

        logger.info(f"Scheduled {scheduled_count} out of {len(matches)} matches.")
    
    def generate_knockout_phase_from_standings(self) -> List[Match]:
        """Generate knockout bracket from global standings."""
        from apps.tournaments.models import GroupStanding, TournamentFormat
        from apps.matches.models import MatchStatus
        
        # Validate format
        if self.division.format != TournamentFormat.ROUND_ROBIN_KNOCKOUT:
            raise InvalidMatchFormatError(
                "Knockout phase generation is only available for ROUND_ROBIN_KNOCKOUT format."
            )
        
        # Validate all group phase matches are completed
        group_matches = Match.objects.filter(
            division=self.division,
            round_number__lt=0  # Negative round numbers are group phase
        )
        
        incomplete_matches = group_matches.exclude(status=MatchStatus.COMPLETED)
        if incomplete_matches.exists():
            raise MatchBusinessError(
                message="All group phase matches must be completed before generating knockout phase.",
                error_code="GROUP_PHASE_INCOMPLETE",
                errors={'matches': ['Some group phase matches are not completed.']}
            )
        
        # Get standings ordered by global position
        standings = GroupStanding.objects.filter(
            group__division=self.division
        ).select_related(
            'involvement__player',
            'involvement__partner'
        ).order_by('global_position')
        
        if not standings.exists():
            raise InsufficientPlayersError(
                min_required=2,
                actual=0
            )
        
        # Convert standings to participants format
        participants = []
        for standing in standings:
            inv = standing.involvement
            participants.append({
                'player1': inv.player,
                'player2': None,
                'partner1': inv.partner if self.division.participant_type == ParticipantType.DOUBLES else None,
                'partner2': None,
            })
        
        # Generate single elimination bracket
        # Reset match counter for knockout phase
        self.match_counter = 1
        
        # Use the existing single elimination logic
        matches = self.generate_single_elimination_bracket(participants)
        
        logger.info(
            f"Generated {len(matches)} knockout phase matches for division "
            f"{self.division.id} ({self.division.name}) from standings"
        )
        
        return matches
    
    @transaction.atomic
    def execute(self) -> List[Match]:
        """Execute bracket generation."""
        self.validate_division()
        
        participants = self.get_participants()
        self.validate_participants(participants)
        
        if self.division.format == TournamentFormat.KNOCKOUT:
            matches = self.generate_single_elimination_bracket(participants)
        elif self.division.format == TournamentFormat.DOUBLE_SLASH:
            matches = self.generate_double_elimination_bracket(participants)
        elif self.division.format == TournamentFormat.ROUND_ROBIN_KNOCKOUT:
            # For ROUND_ROBIN_KNOCKOUT, we need groups first
            # This method should not be called directly for this format
            # Use generate_group_phase_matches instead
            raise InvalidMatchFormatError(
                "For ROUND_ROBIN_KNOCKOUT format, use generate_group_phase_matches() "
                "to create group phase matches first, then generate_knockout_phase_from_standings() "
                "after group phase is complete."
            )
        else:
            raise InvalidMatchFormatError(self.division.get_format_display())
        
        self.created_matches = matches
        
        logger.info(
            f"Bracket generated for division {self.division.id} ({self.division.name}): "
            f"{len(matches)} matches created by user {self.user.id if self.user else 'system'}"
        )
        
        return matches

