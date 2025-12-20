"""
Views for matches app.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from apps.api.mixins import StandardModelViewSet
from apps.api.utils import APIResponse

from .models import Match
from .serializers import (
    MatchReadSerializer,
    MatchWriteSerializer,
    MatchListSerializer,
    MatchScoreSerializer,
    BracketGenerationSerializer,
)
from .services import (
    MatchCreationService,
    MatchUpdateService,
    MatchDeletionService,
    MatchListService,
    MatchScoreService,
    MatchBracketGenerationService,
)
from .permissions import (
    CanViewMatch,
    CanManageMatch,
    CanRecordMatchScore,
    CanGenerateBracket,
)
from .exceptions import MatchBusinessError

logger = logging.getLogger(__name__)


class MatchViewSet(StandardModelViewSet):
    """
    ViewSet for managing matches.
    """
    
    queryset = Match.objects.all()
    permission_classes = [CanViewMatch]
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanManageMatch()]
        elif self.action == 'scores':
            return [CanRecordMatchScore()]
        return [CanViewMatch()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return MatchReadSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MatchWriteSerializer
        return  MatchListSerializer
    
    def get_queryset(self):
        """Get queryset with filters."""
        service = MatchListService(
            division_id=self.request.query_params.get('division_id'),
            tournament_id=self.request.query_params.get('tournament_id'),
            match_type=self.request.query_params.get('match_type'),
            status=self.request.query_params.get('status'),
            player_id=self.request.query_params.get('player_id'),
            round_number=self.request.query_params.get('round_number'),
            is_losers_bracket=self.request.query_params.get('is_losers_bracket'),
            match_code=self.request.query_params.get('match_code'),
        )
        return service.execute()
    
    @swagger_auto_schema(
        operation_summary="List matches",
        operation_description="Get list of matches with optional filters",
        manual_parameters=[
            openapi.Parameter('division_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('tournament_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('match_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('player_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('round_number', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('is_losers_bracket', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('match_code', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        tags=["Matches"],
    )
    def list(self, request, *args, **kwargs):
        """List matches with filters."""
        
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create match",
        operation_description="Create a new match",
        request_body=MatchWriteSerializer,
        tags=["Matches"],
    )
    def create(self, request, *args, **kwargs):
        """Create a new match."""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in match data"
            )
        
        try:
            validated_data = serializer.validated_data
            
            # Extract division to validate
            division = validated_data['division']
            
            service = MatchCreationService(
                division=division,
                match_code=validated_data['match_code'],
                match_type=validated_data['match_type'],
                user=request.user,
                player1=validated_data.get('player1'),
                player2=validated_data.get('player2'),
                partner1=validated_data.get('partner1'),
                partner2=validated_data.get('partner2'),
                max_sets=validated_data.get('max_sets', 5),
                points_per_set=validated_data.get('points_per_set', 15),
                round_number=validated_data.get('round_number'),
                is_losers_bracket=validated_data.get('is_losers_bracket', False),
                next_match=validated_data.get('next_match'),
                scheduled_at=validated_data.get('scheduled_at'),
                notes=validated_data.get('notes', ''),
            )
            
            match = service.execute()
            output_serializer = MatchReadSerializer(match)
            
            return self.created_response(
                data=output_serializer.data,
                message="Match created successfully"
            )
        
        except MatchBusinessError as e:
            return self.validation_error_response(
                errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            logger.exception("Unexpected error creating match")
            return self.error_response(
                message="An unexpected error occurred while creating the match",
                error_code="MATCH_CREATE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Get match",
        operation_description="Get match details",
        tags=["Matches"],
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve match details."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update match",
        operation_description="Update a match",
        request_body=MatchWriteSerializer,
        tags=["Matches"],
    )
    def update(self, request, *args, **kwargs):
        """Update a match."""
        try:
            match = self.get_object()
            serializer = self.get_serializer(match, data=request.data, partial=False)
            
            if not serializer.is_valid():
                return self.validation_error_response(
                    errors=serializer.errors,
                    message="Validation error in match data"
                )
            
            validated_data = serializer.validated_data
            
            service = MatchUpdateService(
                match=match,
                data=validated_data,
                user=request.user
            )
            
            updated_match = service.execute()
            output_serializer = MatchReadSerializer(updated_match)
            
            return self.success_response(
                data=output_serializer.data,
                message="Match updated successfully"
            )
        
        except MatchBusinessError as e:
            return self.validation_error_response(
                errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            logger.exception("Unexpected error updating match")
            return self.error_response(
                message="An unexpected error occurred while updating the match",
                error_code="MATCH_UPDATE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Partially update match",
        operation_description="Partially update a match",
        request_body=MatchWriteSerializer,
        tags=["Matches"],
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a match."""
        try:
            match = self.get_object()
            serializer = self.get_serializer(match, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return self.validation_error_response(
                    errors=serializer.errors,
                    message="Validation error in match data"
                )
            
            validated_data = serializer.validated_data
            
            service = MatchUpdateService(
                match=match,
                data=validated_data,
                user=request.user
            )
            
            updated_match = service.execute()
            output_serializer = MatchReadSerializer(updated_match)
            
            return self.success_response(
                data=output_serializer.data,
                message="Match updated successfully"
            )
        
        except MatchBusinessError as e:
            return self.validation_error_response(
                errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            logger.exception("Unexpected error updating match")
            return self.error_response(
                message="An unexpected error occurred while updating the match",
                error_code="MATCH_UPDATE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Delete match",
        operation_description="Delete a match",
        tags=["Matches"],
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a match."""
        try:
            match = self.get_object()
            
            service = MatchDeletionService(
                match=match,
                user=request.user
            )
            
            service.execute()
            
            return self.success_response(
                data=None,
                message="Match deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT
            )
        
        except MatchBusinessError as e:
            return self.validation_error_response(
                errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            logger.exception("Unexpected error deleting match")
            return self.error_response(
                message="An unexpected error occurred while deleting the match",
                error_code="MATCH_DELETE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='scores')
    @swagger_auto_schema(
        operation_summary="Register match scores",
        operation_description="Register scores for a match and calculate winner",
        request_body=MatchScoreSerializer,
        tags=["Matches"],
    )
    def scores(self, request, pk=None):
        """Register scores for a match."""
        match = self.get_object()
        
        serializer = MatchScoreSerializer(data=request.data)
        
        if not serializer.is_valid():
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in score data"
            )
        
        try:
            sets_data = serializer.validated_data['sets']
            
            service = MatchScoreService(
                match=match,
                sets_data=sets_data,
                user=request.user
            )
            
            updated_match = service.execute()
            output_serializer = MatchReadSerializer(updated_match)
            
            return self.success_response(
                data=output_serializer.data,
                message="Scores registered successfully"
            )
        
        except MatchBusinessError as e:
            return self.validation_error_response(
                errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            logger.exception("Unexpected error registering scores")
            return self.error_response(
                message="An unexpected error occurred while registering scores",
                error_code="MATCH_SCORE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@swagger_auto_schema(
    method='post',
    operation_summary="Generate bracket",
    operation_description="Generate complete bracket for a division based on its format",
    request_body=BracketGenerationSerializer,
    tags=["Matches"],
)
@api_view(['POST'])
@permission_classes([CanGenerateBracket])
def generate_bracket(request):
    """Generate complete bracket for a division."""
    serializer = BracketGenerationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return APIResponse.validation_error(
            errors=serializer.errors,
            message="Validation error in bracket generation data"
        )
    
    try:
        division_id = serializer.validated_data['division_id']
        max_sets = serializer.validated_data.get('max_sets', 5)
        points_per_set = serializer.validated_data.get('points_per_set', 15)
        
        # Get division
        from apps.tournaments.models import TournamentDivision
        try:
            division = TournamentDivision.objects.get(id=division_id)
        except TournamentDivision.DoesNotExist:
            return APIResponse.not_found(
                message="Division not found",
                error_code="DIVISION_NOT_FOUND"
            )
        
        # Generate bracket
        service = MatchBracketGenerationService(
            division=division,
            max_sets=max_sets,
            points_per_set=points_per_set,
            user=request.user
        )
        
        matches = service.execute()
        
        # Serialize matches
        from .serializers import MatchReadSerializer
        matches_serializer = MatchReadSerializer(matches, many=True)
        
        return APIResponse.created(
            data=matches_serializer.data,
            message=f"Bracket generated successfully. {len(matches)} matches created."
        )
    
    except MatchBusinessError as e:
        return APIResponse.validation_error(
            errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
            message=str(e),
            error_code=e.error_code
        )
    except Exception as e:
        logger.exception("Unexpected error generating bracket")
        return APIResponse.error(
            message="An unexpected error occurred while generating bracket",
            error_code="BRACKET_GENERATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

