"""
Serializers for matches app.
"""
from rest_framework import serializers
from django.utils import timezone

from .models import Match, Set
from .constants import MatchType, MatchStatus, SetWinner
from apps.tournaments.models import TournamentDivision
from apps.players.models import PlayerProfile


class SetSerializer(serializers.ModelSerializer):
    """Serializer for Set model."""
    
    class Meta:
        model = Set
        fields = [
            'id', 'set_number', 'player1_score', 'player2_score',
            'winner', 'completed_at'
        ]
        read_only_fields = ['id', 'completed_at']


class PlayerProfileBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for PlayerProfile in match context."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = PlayerProfile
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'avatar']
        read_only_fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'avatar']


class MatchListSerializer(serializers.ModelSerializer):
    """Optimized serializer for listing matches."""
    
    player1_name = serializers.CharField(source='player1.full_name', read_only=True)
    player2_name = serializers.CharField(source='player2.full_name', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    tournament_name = serializers.CharField(source='division.tournament.name', read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'match_code', 'division_name', 'tournament_name',
            'match_type', 'status', 'player1_name', 'player2_name',
            'round_number', 'is_losers_bracket', 'scheduled_at', 'location',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MatchReadSerializer(serializers.ModelSerializer):
    """Serializer for reading match details."""
    
    player1 = PlayerProfileBasicSerializer(read_only=True)
    player2 = PlayerProfileBasicSerializer(read_only=True)
    partner1 = PlayerProfileBasicSerializer(read_only=True)
    partner2 = PlayerProfileBasicSerializer(read_only=True)
    winner = PlayerProfileBasicSerializer(read_only=True)
    winner_partner = PlayerProfileBasicSerializer(read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    tournament_name = serializers.CharField(source='division.tournament.name', read_only=True)
    sets = SetSerializer(many=True, read_only=True)
    sets_to_win = serializers.ReadOnlyField()
    sets_won_by_player1 = serializers.ReadOnlyField()
    sets_won_by_player2 = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    next_match_code = serializers.CharField(source='next_match.match_code', read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'match_code', 'division', 'division_name', 'tournament_name',
            'player1', 'player2', 'partner1', 'partner2',
            'match_type', 'status', 'max_sets', 'points_per_set',
            'round_number', 'is_losers_bracket', 'next_match', 'next_match_code',
            'winner', 'winner_partner',
            'scheduled_at', 'location', 'started_at', 'completed_at',
            'sets', 'sets_to_win', 'sets_won_by_player1', 'sets_won_by_player2',
            'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'sets_to_win',
            'sets_won_by_player1', 'sets_won_by_player2'
        ]


class MatchWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating matches."""
    
    class Meta:
        model = Match
        fields = [
            'division', 'match_code', 'match_type',
            'player1', 'player2', 'partner1', 'partner2',
            'max_sets', 'points_per_set',
            'round_number', 'is_losers_bracket', 'next_match',
            'scheduled_at', 'location', 'notes'
        ]
    
    def validate_max_sets(self, value):
        """Validate max_sets is in valid range."""
        if not (3 <= value <= 10):
            raise serializers.ValidationError("Maximum sets must be between 3 and 10.")
        return value
    
    def validate_points_per_set(self, value):
        """Validate points_per_set is in valid range."""
        if not (1 <= value <= 50):
            raise serializers.ValidationError("Points per set must be between 1 and 50.")
        return value
    
    def validate(self, data):
        """Validate match data."""
        match_type = data.get('match_type')
        
        # Validate singles vs doubles logic
        if match_type == MatchType.SINGLES:
            if data.get('partner1') or data.get('partner2'):
                raise serializers.ValidationError({
                    'match_type': 'Partners cannot be set for singles matches.'
                })
        elif match_type == MatchType.DOUBLES:
            player1 = data.get('player1')
            player2 = data.get('player2')
            partner1 = data.get('partner1')
            partner2 = data.get('partner2')
            
            if not (player1 and player2 and partner1 and partner2):
                raise serializers.ValidationError({
                    'match_type': 'All players and partners are required for doubles matches.'
                })
        
        return data


class MatchScoreSetSerializer(serializers.Serializer):
    """Serializer for a single set score."""
    
    set_number = serializers.IntegerField(min_value=1)
    player1_score = serializers.IntegerField(min_value=0, default=0)
    player2_score = serializers.IntegerField(min_value=0, default=0)


class MatchScoreSerializer(serializers.Serializer):
    """Serializer for registering match scores."""
    
    sets = MatchScoreSetSerializer(many=True, required=True)
    
    def validate_sets(self, value):
        """Validate sets data."""
        if not value:
            raise serializers.ValidationError("At least one set must be provided.")
        
        set_numbers = [s['set_number'] for s in value]
        
        # Check for duplicate set numbers
        if len(set_numbers) != len(set(set_numbers)):
            raise serializers.ValidationError("Duplicate set numbers are not allowed.")
        
        # Validate set numbers are positive
        for set_data in value:
            if set_data['set_number'] <= 0:
                raise serializers.ValidationError("Set number must be positive.")
        
        return value


class BracketGenerationSerializer(serializers.Serializer):
    """Serializer for generating brackets."""
    
    division_id = serializers.IntegerField(required=True)
    max_sets = serializers.IntegerField(min_value=3, max_value=10, default=5, required=False)
    points_per_set = serializers.IntegerField(min_value=1, max_value=50, default=15, required=False)
    
    def validate_division_id(self, value):
        """Validate division exists and is published."""
        try:
            division = TournamentDivision.objects.get(id=value)
            if not division.is_published:
                raise serializers.ValidationError(
                    "Brackets can only be generated for published divisions."
                )
            return value
        except TournamentDivision.DoesNotExist:
            raise serializers.ValidationError("Division not found.")

