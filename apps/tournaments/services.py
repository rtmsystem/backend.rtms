from django.db import transaction
from typing import Optional, List, Dict, Tuple
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging
import random
import math

from .models import TournamentDivision, TournamentGroup, GroupStanding, InvolvementStatus
from apps.matches.models import Match, MatchStatus, SetWinner

logger = logging.getLogger(__name__)
User = get_user_model()


class DivisionCompletionService:

    def __init__(self, division: TournamentDivision, user: Optional[User] = None) -> None:
        self.division = division
        self.user = user

    @transaction.atomic
    def publish_division(self) -> TournamentDivision:
        self.division.publish(user=self.user)
        
        logger.info(
            f"Division {self.division.id} ({self.division.name}) "
            f"published by user {self.user.id if self.user else 'system'}"
        )
        
        return self.division


class GroupGenerationService:
    """Service to generate groups for Round Robin + Knockout format."""
    
    def __init__(
        self,
        division: TournamentDivision,
        min_per_group: int = 3,
        max_per_group: int = 5,
        user: Optional[User] = None
    ) -> None:
        self.division = division
        self.min_per_group = min_per_group
        self.max_per_group = max_per_group
        self.user = user
        self.created_groups: List[TournamentGroup] = []
    
    def validate_division(self) -> None:
        """Validate division can have groups generated."""
        from .exceptions import DivisionInsufficientApprovedPlayersError
        
        # Validate format
        from .models import TournamentFormat
        if self.division.format != TournamentFormat.ROUND_ROBIN_KNOCKOUT:
            raise ValueError(
                f"Group generation is only available for ROUND_ROBIN_KNOCKOUT format. "
                f"Current format: {self.division.get_format_display()}"
            )
        
        # Validate division is published
        if not self.division.is_published:
            raise ValueError("Division must be published before generating groups.")
        
        # Validate minimum participants
        approved_count = self.division.involvements.filter(
            status=InvolvementStatus.APPROVED
        ).count()
        
        if approved_count < self.min_per_group:
            raise DivisionInsufficientApprovedPlayersError(approved_count)
        
        # Validate min and max per group
        if self.min_per_group < 3:
            raise ValueError("min_per_group must be at least 3")
        if self.max_per_group > 5:
            raise ValueError("max_per_group cannot exceed 5")
        if self.min_per_group > self.max_per_group:
            raise ValueError("min_per_group cannot be greater than max_per_group")
        
        # Check if groups already exist
        existing_groups = TournamentGroup.objects.filter(division=self.division).exists()
        if existing_groups:
            raise ValueError("Groups already exist for this division. Delete existing groups first.")
    
    def get_participants(self) -> List:
        """Get approved participants from division."""
        return list(
            self.division.involvements.filter(
                status=InvolvementStatus.APPROVED
            ).select_related('player', 'partner')
        )
    
    def distribute_participants(self, participants: List) -> List[List]:
        """Distribute participants into groups of 3-5 players."""
        num_participants = len(participants)
        
        # Shuffle for random distribution
        shuffled = participants.copy()
        random.shuffle(shuffled)
        
        # Calculate optimal group sizes
        # Try to balance groups as much as possible
        num_groups = math.ceil(num_participants / self.max_per_group)
        
        # If we can fit everyone in groups of min_per_group, use that
        if num_participants <= num_groups * self.min_per_group:
            num_groups = math.ceil(num_participants / self.min_per_group)
        
        groups = []
        participant_index = 0
        
        for group_idx in range(num_groups):
            # Calculate how many participants for this group
            remaining_participants = num_participants - participant_index
            remaining_groups = num_groups - group_idx
            
            # Distribute evenly, but respect min and max
            participants_per_group = remaining_participants // remaining_groups
            
            # Ensure it's within bounds
            if participants_per_group < self.min_per_group:
                participants_per_group = self.min_per_group
            elif participants_per_group > self.max_per_group:
                participants_per_group = self.max_per_group
            
            # Take participants for this group
            group_participants = shuffled[
                participant_index:participant_index + participants_per_group
            ]
            groups.append(group_participants)
            participant_index += participants_per_group
        
        return groups
    
    @transaction.atomic
    def generate_groups(self) -> List[TournamentGroup]:
        """Generate groups and distribute participants."""
        self.validate_division()
        
        participants = self.get_participants()
        participant_groups = self.distribute_participants(participants)
        
        created_groups = []
        
        for group_idx, group_participants in enumerate(participant_groups, start=1):
            # Create group
            group = TournamentGroup.objects.create(
                division=self.division,
                name=f"Grupo {chr(64 + group_idx)}",  # A, B, C, etc.
                group_number=group_idx
            )
            created_groups.append(group)
            
            # Create standings for each participant in the group
            for involvement in group_participants:
                GroupStanding.objects.create(
                    group=group,
                    involvement=involvement
                )
            
            # Validate group has correct number of participants
            group.refresh_from_db()
            group.validate_participant_count()
        
        self.created_groups = created_groups
        
        logger.info(
            f"Generated {len(created_groups)} groups for division {self.division.id} "
            f"({self.division.name}) by user {self.user.id if self.user else 'system'}"
        )
        
        return created_groups
    
    @transaction.atomic
    def execute(self) -> List[TournamentGroup]:
        """Execute group generation."""
        return self.generate_groups()


class StandingCalculationService:
    """Service to calculate standings for groups and global positions."""
    
    def __init__(
        self,
        division: TournamentDivision,
        user: Optional[User] = None
    ) -> None:
        self.division = division
        self.user = user
    
    def validate_division(self) -> None:
        """Validate division can have standings calculated."""
        from .models import TournamentFormat
        
        if self.division.format != TournamentFormat.ROUND_ROBIN_KNOCKOUT:
            raise ValueError(
                f"Standing calculation is only available for ROUND_ROBIN_KNOCKOUT format. "
                f"Current format: {self.division.get_format_display()}"
            )
    
    def get_group_matches(self, group: TournamentGroup) -> List[Match]:
        """Get all completed group phase matches for a group."""
        # Group phase matches have negative round_number
        return Match.objects.filter(
            division=self.division,
            round_number=-group.group_number,
            status=MatchStatus.COMPLETED
        ).select_related('player1', 'player2', 'partner1', 'partner2')
    
    def update_standing_from_match(
        self, 
        standing: GroupStanding, 
        match: Match, 
        is_winner: bool
    ) -> None:
        """Update standing statistics from a match."""
        standing.matches_played += 1
        
        if is_winner:
            standing.matches_won += 1
            standing.points += 3  # 3 points for win
        else:
            standing.matches_lost += 1
            standing.points += 1  # 1 point for loss
        
        # Calculate sets won/lost
        sets_won = 0
        sets_lost = 0
        
        for set_obj in match.sets.all():
            if set_obj.winner == SetWinner.PLAYER1:
                # Check if this standing's involvement is player1
                if (match.player1 == standing.involvement.player and 
                    (not match.partner1 or match.partner1 == standing.involvement.partner)):
                    sets_won += 1
                else:
                    sets_lost += 1
            elif set_obj.winner == SetWinner.PLAYER2:
                # Check if this standing's involvement is player2
                if (match.player2 == standing.involvement.player and 
                    (not match.partner2 or match.partner2 == standing.involvement.partner)):
                    sets_won += 1
                else:
                    sets_lost += 1
        
        standing.sets_won += sets_won
        standing.sets_lost += sets_lost
        standing.save()
    
    def get_head_to_head_result(
        self, 
        standing1: GroupStanding, 
        standing2: GroupStanding, 
        group: TournamentGroup
    ) -> Optional[bool]:
        """Get head-to-head result between two standings. Returns True if standing1 won, False if standing2 won, None if no match."""
        matches = self.get_group_matches(group)
        
        for match in matches:
            inv1 = standing1.involvement
            inv2 = standing2.involvement
            
            # Check if this match is between these two involvements
            is_match = False
            inv1_is_player1 = False
            
            if (match.player1 == inv1.player and 
                (not match.partner1 or match.partner1 == inv1.partner) and
                match.player2 == inv2.player and
                (not match.partner2 or match.partner2 == inv2.partner)):
                is_match = True
                inv1_is_player1 = True
            elif (match.player1 == inv2.player and 
                  (not match.partner1 or match.partner1 == inv2.partner) and
                  match.player2 == inv1.player and
                  (not match.partner2 or match.partner2 == inv1.partner)):
                is_match = True
                inv1_is_player1 = False
            
            if is_match and match.winner:
                if inv1_is_player1:
                    return match.winner == match.player1
                else:
                    return match.winner == match.player2
        
        return None
    
    def calculate_group_standings(self, group: TournamentGroup) -> List[GroupStanding]:
        """Calculate standings within a group."""
        # Reset all standings
        standings = list(group.standings.all())
        
        for standing in standings:
            standing.matches_played = 0
            standing.matches_won = 0
            standing.matches_lost = 0
            standing.sets_won = 0
            standing.sets_lost = 0
            standing.points = 0
            standing.save()
        
        # Process all completed matches
        matches = self.get_group_matches(group)
        
        for match in matches:
            # Find standings for both players
            standing1 = None
            standing2 = None
            
            for standing in standings:
                inv = standing.involvement
                if (match.player1 == inv.player and 
                    (not match.partner1 or match.partner1 == inv.partner)):
                    standing1 = standing
                elif (match.player2 == inv.player and 
                      (not match.partner2 or match.partner2 == inv.partner)):
                    standing2 = standing
            
            if standing1 and standing2 and match.winner:
                # Determine winner
                is_winner1 = match.winner == match.player1
                
                # Update standings
                self.update_standing_from_match(standing1, match, is_winner1)
                self.update_standing_from_match(standing2, match, not is_winner1)
        
        # Refresh standings from DB
        standings = list(group.standings.all())
        
        # Sort standings by criteria:
        # 1. Points (descending)
        # 2. Sets difference (descending)
        # 3. Sets won (descending)
        # 4. Head-to-head (if applicable)
        
        def sort_key(standing: GroupStanding) -> Tuple:
            # Get head-to-head result for tie-breaking
            # We'll do a simple comparison for now
            return (
                -standing.points,  # Negative for descending
                -standing.sets_difference,
                -standing.sets_won,
            )
        
        standings.sort(key=sort_key)
        
        # Handle head-to-head ties
        i = 0
        while i < len(standings):
            # Find all standings with same points, sets_diff, and sets_won
            tie_group = [standings[i]]
            j = i + 1
            while (j < len(standings) and 
                   standings[j].points == standings[i].points and
                   standings[j].sets_difference == standings[i].sets_difference and
                   standings[j].sets_won == standings[i].sets_won):
                tie_group.append(standings[j])
                j += 1
            
            # If there's a tie, check head-to-head
            if len(tie_group) > 1:
                # Simple approach: if two players are tied, check their match
                if len(tie_group) == 2:
                    h2h = self.get_head_to_head_result(tie_group[0], tie_group[1], group)
                    if h2h is True:
                        # tie_group[0] won head-to-head, keep order
                        pass
                    elif h2h is False:
                        # tie_group[1] won head-to-head, swap
                        standings[i], standings[i+1] = standings[i+1], standings[i]
            
            i = j
        
        # Assign positions
        for idx, standing in enumerate(standings, start=1):
            standing.position_in_group = idx
            standing.save()
        
        return standings
    
    def calculate_global_standings(self) -> List[GroupStanding]:
        """Calculate global standings across all groups."""
        self.validate_division()
        
        # First, calculate standings for each group
        groups = TournamentGroup.objects.filter(division=self.division).order_by('group_number')
        
        all_standings = []
        for group in groups:
            group_standings = self.calculate_group_standings(group)
            all_standings.extend(group_standings)
        
        # Sort all standings globally by same criteria
        def sort_key(standing: GroupStanding) -> Tuple:
            return (
                -standing.points,
                -standing.sets_difference,4
                -standing.sets_won,
            )
        
        all_standings.sort(key=sort_key)
        
        # Assign global positions
        for idx, standing in enumerate(all_standings, start=1):
            standing.global_position = idx
            standing.save()
        
        logger.info(
            f"Calculated global standings for division {self.division.id} "
            f"({self.division.name}) by user {self.user.id if self.user else 'system'}"
        )
        
        return all_standings
    
    @transaction.atomic
    def execute(self) -> List[GroupStanding]:
        """Execute standing calculation."""
        return self.calculate_global_standings()