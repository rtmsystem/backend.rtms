"""
Views for tournaments app.
"""

import json
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q

from apps.api.mixins import StandardResponseMixin
from apps.api.utils import APIResponse

from .models import (
    Tournament,
    TournamentDivision,
    Involvement,
    TournamentFormat,
    GenderType,
    ParticipantType,
    TournamentStatus,
    InvolvementStatus,
)
from .serializers import (
    TournamentSerializer,
    TournamentCreateSerializer,
    TournamentUpdateSerializer,
    TournamentListSerializer,
    TournamentDivisionSerializer,
    InvolvementSerializer,
    InvolvementCreateSerializer,
    InvolvementUpdateSerializer,
    InvolvementListSerializer,
)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .permissions import CanViewPublishedTournament
from .exceptions import TournamentBusinessError

########################################################
# Tournament API Endpoints
########################################################


class TournamentListCreateView(StandardResponseMixin, generics.ListCreateAPIView):
    """
    List all tournaments or create a new tournament.
    - Usuarios no autenticados: pueden ver todos los torneos publicados
    - Usuarios autenticados: pueden ver torneos de sus organizaciones administradas
    - Crear torneo: requiere autenticación y se asigna a la organización del usuario
    """

    def get_permissions(self):
        """Permite acceso público para GET, requiere autenticación para POST."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TournamentCreateSerializer
        return TournamentListSerializer

    @swagger_auto_schema(
        operation_summary="List tournaments",
        operation_description="Gets the list of tournaments. Usuarios no autenticados solo ven torneos publicados. Usuarios autenticados ven torneos de sus organizaciones administradas.",
        tags=["Tournaments"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create tournament",
        operation_description="Creates a new tournament for the authenticated user's organization. El usuario debe ser administrador de al menos una organización.",
        tags=["Tournaments"],
    )
    def post(self, request, *args, **kwargs):
        # Obtener la organización del usuario autenticado
        user = request.user
        
        # Obtener organizaciones que el usuario administra
        user_organizations = user.administered_organizations.all()
        
        if not user_organizations.exists():
            return self.validation_error_response(
                errors={"organization": ["No tienes organizaciones administradas."]},
                message="You must be an administrator of at least one organization to create tournaments"
            )
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id
        
        # Preparar los datos del request
        data = request.data.copy()

        
        # Parsear divisions si viene como string JSON
        if 'divisions' in data:
            divisions_value = data.get('divisions')
            if isinstance(divisions_value, str):
                try:
                    divisions_data = json.loads(divisions_value)
                    data['divisions'] = divisions_data
                except json.JSONDecodeError:
                    return self.validation_error_response(
                        errors={"divisions": ["El formato JSON de divisions es inválido."]},
                        message="Invalid JSON format for divisions"
                    )
        else:
            # Asegurarse de que divisions esté presente como lista vacía si no está en los datos
            data['divisions'] = []
        

        serializer = self.get_serializer(data=data, context={'organization_id': organization_id, 'request': request})
        if serializer.is_valid():
            tournament = serializer.save()
            output_serializer = TournamentSerializer(tournament)
            return self.created_response(
                data=output_serializer.data,
                message="Tournament created successfully",
            )
        else:
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in tournament data"
            )

    def get_queryset(self):
        """Filter tournaments based on user authentication status."""
       # if user is not authenticated, return only published tournaments
        if not self.request.user.is_authenticated:
            queryset = Tournament.objects.select_related("organization").filter(
                status=TournamentStatus.PUBLISHED
            )
        else:
            user = self.request.user
            
            # get organization ids that the user manages
            user_organization_ids = list(user.administered_organizations.values_list('id', flat=True))
            
            # get tournaments from the organizations that the user manages (all statuses)
            queryset = Tournament.objects.select_related("organization").filter(
                Q(organization_id__in=user_organization_ids))

        # Apply filters
        search = self.request.query_params.get("search", None)
        status = self.request.query_params.get("status", None)
        city = self.request.query_params.get("city", None)
        country = self.request.query_params.get("country", None)
        is_active = self.request.query_params.get("is_active", None)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(city__icontains=search)
                | Q(country__icontains=search)
            )

        if status:
            queryset = queryset.filter(status=status)

        if city:
            queryset = queryset.filter(city__icontains=city)

        if country:
            queryset = queryset.filter(country__icontains=country)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Order by start date
        queryset = queryset.order_by("-start_date")

        return queryset

    def perform_create(self, serializer):
        """Set the organization and created_by field when creating a tournament."""
        # Esta función se llama después de post(), pero la lógica ya está en post()
        # Mantenemos esto por compatibilidad pero la lógica principal está en post()
        pass


class TournamentRetrieveUpdateDestroyView(
    StandardResponseMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    Retrieve, update or delete a tournament.
    La organización se obtiene del usuario autenticado.
    Permite acceso público a torneos publicados solo para lectura (GET).
    """

    permission_classes = [CanViewPublishedTournament]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return TournamentUpdateSerializer
        return TournamentSerializer

    @swagger_auto_schema(
        operation_summary="Get tournament",
        operation_description="Gets a specific tournament. La organización se obtiene del usuario autenticado. Usuarios no autenticados solo ven torneos publicados.",
        tags=["Tournaments"],
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        from django.http import Http404
        from rest_framework.exceptions import PermissionDenied
        
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data, message="Tournament retrieved successfully"
            )
        except Http404:
            return self.not_found_response(
                message="Tournament not found",
                error_code="TOURNAMENT_NOT_FOUND"
            )
        except PermissionDenied:
            return self.forbidden_response(
                message="You do not have permission to view this tournament",
                error_code="FORBIDDEN_VIEW_TOURNAMENT"
            )

    @swagger_auto_schema(
        operation_summary="Update tournament",
        operation_description="Updates a specific tournament. La organización se obtiene del usuario autenticado.",
        tags=["Tournaments"],
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update tournament",
        operation_description="Partially updates a specific tournament. La organización se obtiene del usuario autenticado.",
        tags=["Tournaments"],
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data, message="Tournament updated successfully"
            )
        else:
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in tournament data"
            )
       

    @swagger_auto_schema(
        operation_summary="Delete tournament",
        operation_description="Deletes a specific tournament. La organización se obtiene del usuario autenticado.",
        tags=["Tournaments"],
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):

        if not self.request.user.is_authenticated:
            queryset = Tournament.objects.select_related("organization", "created_by").prefetch_related("divisions").filter(
                status=TournamentStatus.PUBLISHED
            )
        else:
            user = self.request.user
            
            # Obtener IDs de organizaciones que el usuario administra
            user_organization_ids = list(user.administered_organizations.values_list('id', flat=True))
            
           # get tournaments from the organizations that the user manages (all statuses)
            queryset = Tournament.objects.select_related("organization", "created_by").prefetch_related("divisions").filter(
                Q(organization_id__in=user_organization_ids)
            )

        return queryset


@swagger_auto_schema(
    method="get",
    operation_summary="Get tournament form options",
    operation_description="Gets the available options for tournament forms (formats, genders, participant types, statuses)",
    tags=["Tournaments"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tournament_choices(request):
    """
    Get choice options for tournament forms.
    """
    choices = {
        "formats": [
            {"value": choice[0], "label": choice[1]}
            for choice in TournamentFormat.choices
        ],
        "genders": [
            {"value": choice[0], "label": choice[1]} for choice in GenderType.choices
        ],
        "participant_types": [
            {"value": choice[0], "label": choice[1]}
            for choice in ParticipantType.choices
        ],
        "statuses": [
            {"value": choice[0], "label": choice[1]}
            for choice in TournamentStatus.choices
        ],
        "involvement_statuses": [
            {"value": choice[0], "label": choice[1]}
            for choice in InvolvementStatus.choices
        ],
    }

    return APIResponse.success(
        data=choices, message="Tournament choices retrieved successfully"
    )


@swagger_auto_schema(
    method="post",
    operation_summary="Publish tournament",
    operation_description="Publishes a tournament by changing its status to published. El usuario debe ser administrador de la organización del torneo.",
    tags=["Tournaments"],
    manual_parameters=[
        openapi.Parameter(
            "pk",
            openapi.IN_PATH,
            description="Tournament ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tournament_publish(request, pk):
    """
    Publish a tournament (change status to published).
    El usuario debe ser administrador de la organización del torneo.
    """
    try:
        # Obtener el torneo
        tournament = Tournament.objects.filter(pk=pk).first()

        if not tournament:
            return APIResponse.not_found(
                message="Tournament not found.",
                error_code="TOURNAMENT_NOT_FOUND",
            )

        # Verificar que el usuario es administrador de la organización del torneo
        user_organizations = request.user.administered_organizations.all()
        if not user_organizations.filter(id=tournament.organization_id).exists():
            return APIResponse.forbidden(
                message="You do not have permission to publish this tournament. You must be an administrator of the tournament's organization.",
                error_code="FORBIDDEN_PUBLISH_TOURNAMENT",
            )

        # Check if tournament has at least one division
        if tournament.divisions.count() == 0:
            return APIResponse.error(
                message="Tournament must have at least one division before publishing.",
                error_code="TOURNAMENT_NO_DIVISIONS",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Publish the tournament
        tournament.status = TournamentStatus.PUBLISHED
        tournament.save()

        serializer = TournamentSerializer(tournament)
        return APIResponse.success(
            data=serializer.data, message="Tournament published successfully"
        )

    except Exception as e:
        return APIResponse.error(
            message="An error occurred while publishing the tournament.",
            error_code="TOURNAMENT_PUBLISH_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Cancel tournament",
    operation_description="Cancels a tournament by changing its status to cancelled. La organización se obtiene del usuario logueado.",
    tags=["Tournaments"],
    manual_parameters=[
        openapi.Parameter(
            "pk",
            openapi.IN_PATH,
            description="Tournament ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tournament_cancel(request, pk):
    """
    Cancel a tournament.
    La organización se obtiene del usuario logueado.
    """
    try:
        # Obtener la organización del usuario logueado
        user_organizations = request.user.administered_organizations.all()
        
        if not user_organizations.exists():
            return APIResponse.forbidden(
                message="You do not have managed organizations.",
                error_code="FORBIDDEN_CANCEL_TOURNAMENT",
            )
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            pk=pk, organization_id=organization_id
        ).first()

        if not tournament:
            return APIResponse.not_found(
                message="Tournament not found in this organization.",
                error_code="TOURNAMENT_NOT_FOUND",
            )

        # Check if user has permission to cancel this tournament
        if not request.user.is_admin:
            if not request.user.administered_organizations.filter(
                id=organization_id
            ).exists():
                return APIResponse.forbidden(
                    message="You do not have permission to cancel this tournament.",
                    error_code="FORBIDDEN_CANCEL_TOURNAMENT",
                )

        # Cancel the tournament
        tournament.status = TournamentStatus.CANCELLED
        tournament.save()

        serializer = TournamentSerializer(tournament)
        return APIResponse.success(
            data=serializer.data, message="Tournament cancelled successfully"
        )

    except Exception as e:
        return APIResponse.error(
            message="An error occurred while cancelling the tournament.",
            error_code="TOURNAMENT_CANCEL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


########################################################
# Division API Endpoints
########################################################


class TournamentDivisionListCreateView(
    StandardResponseMixin, generics.ListCreateAPIView
):
    """
    List all divisions for a tournament or create a new division.
    La organización se obtiene del usuario logueado.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TournamentDivisionSerializer

    @swagger_auto_schema(
        operation_summary="List tournament divisions",
        operation_description="Gets the list of divisions for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Divisions"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create tournament division",
        operation_description="Creates a new division for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Divisions"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        """Filter divisions by tournament and user permissions."""
        # Detectar si es una vista falsa de Swagger para generación de esquema
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return TournamentDivision.objects.none()
        
        # Obtener la organización del usuario logueado
        user = self.request.user
        user_organizations = user.administered_organizations.all()
        
        if not user_organizations.exists():
            return TournamentDivision.objects.none()
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verificar que el tournament_id exista en los kwargs
        tournament_id = self.kwargs.get("tournament_id")
        
        if not tournament_id:
            return TournamentDivision.objects.none()

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()
        if not tournament:
            return TournamentDivision.objects.none()

        return TournamentDivision.objects.filter(tournament_id=tournament_id)

    def perform_create(self, serializer):
        """Set the tournament when creating a division."""
        # Obtener la organización del usuario logueado
        user = self.request.user
        user_organizations = user.administered_organizations.all()
        
        if not user_organizations.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("No tienes organizaciones administradas.")
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        tournament_id = self.kwargs["tournament_id"]

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()
        if not tournament:
            from rest_framework.exceptions import NotFound

            raise NotFound("Tournament not found in this organization.")

        serializer.save(tournament=tournament)


class TournamentDivisionRetrieveUpdateDestroyView(
    StandardResponseMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    Retrieve, update or delete a tournament division.
    La organización se obtiene del usuario logueado.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TournamentDivisionSerializer

    @swagger_auto_schema(
        operation_summary="Get tournament division",
        operation_description="Gets a specific division from a tournament. La organización se obtiene del usuario logueado.",
        tags=["Divisions"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Division ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update tournament division",
        operation_description="Updates a specific division from a tournament. La organización se obtiene del usuario logueado.",
        tags=["Divisions"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Division ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update tournament division",
        operation_description="Partially updates a specific division from a tournament. La organización se obtiene del usuario logueado.",
        tags=["Divisions"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Division ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete tournament division",
        operation_description="Deletes a specific division from a tournament. La organización se obtiene del usuario logueado.",
        tags=["Divisions"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Division ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        """Filter divisions by tournament and user permissions."""
        # Detectar si es una vista falsa de Swagger para generación de esquema
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return TournamentDivision.objects.none()
        
        # Obtener la organización del usuario logueado
        user = self.request.user
        user_organizations = user.administered_organizations.all()
        
        if not user_organizations.exists():
            return TournamentDivision.objects.none()
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verificar que el tournament_id exista en los kwargs
        tournament_id = self.kwargs.get("tournament_id")
        
        if not tournament_id:
            return TournamentDivision.objects.none()

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()
        if not tournament:
            return TournamentDivision.objects.none()

        return TournamentDivision.objects.filter(tournament_id=tournament_id)


########################################################
# Involvement API Endpoints
########################################################


class InvolvementListCreateView(StandardResponseMixin, generics.ListCreateAPIView):
    """
    List all involvements for a tournament or create a new involvement.
    La organización se obtiene del usuario logueado.
    """

    # Permitir acceso sin autenticación para GET, pero requerir autenticación para POST
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvolvementCreateSerializer
        return InvolvementListSerializer

    def get_queryset(self):
        """Filter involvements by tournament, organization and user permissions."""
        # Detectar si es una vista falsa de Swagger para generación de esquema
        if getattr(self, 'swagger_fake_view', False):
            return Involvement.objects.none()
        
        from django.contrib.auth.models import AnonymousUser

        # Verificar que el tournament_id exista en los kwargs
        tournament_id = self.kwargs.get("tournament_id")
        
        if not tournament_id:
            return Involvement.objects.none()

        # Si el usuario NO está autenticado: devolver solo involvements APPROVED
        if (
            isinstance(self.request.user, AnonymousUser)
            or not self.request.user.is_authenticated
        ):
            return Involvement.objects.select_related(
                "player", "tournament", "division", "approved_by"
            ).filter(
                tournament_id=tournament_id,
                status=InvolvementStatus.APPROVED
            )

        # Usuario autenticado: verificar si es admin de la organización
        user = self.request.user
        user_organizations = user.administered_organizations.all()
        
        if not user_organizations.exists():
            # Si no es admin de ninguna organización, no devolver nada
            return Involvement.objects.none()
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()
        if not tournament:
            # Si el torneo no pertenece a la organización del admin, no devolver nada
            return Involvement.objects.none()

        # Usuario es admin de la organización: devolver todos los involvements
        return Involvement.objects.select_related(
            "player", "tournament", "division", "approved_by"
        ).filter(tournament_id=tournament_id)

    @swagger_auto_schema(
        operation_summary="List involvements",
        operation_description="Gets the list of involvements for a tournament. Si el usuario no está autenticado, devuelve lista única de jugadores aprobados. Si el usuario es admin de la organización, devuelve todos los involvements.",
        tags=["Involvements"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        from django.contrib.auth.models import AnonymousUser
        from django.db.models import Q
        from apps.players.models import PlayerProfile
        from .serializers import ApprovedPlayerListSerializer
        
        # Si el usuario NO está autenticado: devolver lista única de jugadores aprobados
        if (
            isinstance(request.user, AnonymousUser)
            or not request.user.is_authenticated
        ):
            tournament_id = self.kwargs.get("tournament_id")
            
            if not tournament_id:
                return APIResponse.success(data=[], message="No tournament ID provided")
            
            # Obtener todos los involvements aprobados del torneo
            approved_involvements = Involvement.objects.filter(
                tournament_id=tournament_id,
                status=InvolvementStatus.APPROVED
            ).select_related(
                "player", "player__nationality", "partner", "partner__nationality"
            )
            
            # Obtener IDs únicos de players y partners
            player_ids = set()
            partner_ids = set()
            
            for involvement in approved_involvements:
                if involvement.player:
                    player_ids.add(involvement.player.id)
                if involvement.partner:
                    partner_ids.add(involvement.partner.id)
            
            # Combinar ambos sets para obtener IDs únicos
            unique_player_ids = player_ids | partner_ids
            
            # Obtener los jugadores únicos
            players = PlayerProfile.objects.filter(
                id__in=unique_player_ids
            ).select_related('nationality').distinct()
            
            # Serializar los jugadores
            serializer = ApprovedPlayerListSerializer(players, many=True, context={'request': request})
            
            return APIResponse.success(
                data=serializer.data,
                message="Approved players retrieved successfully"
            )
        else:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            return APIResponse.success(
                data=serializer.data,
                message="Involvements retrieved successfully"
            )



    @swagger_auto_schema(
        operation_summary="Create involvement",
        operation_description="Creates a new involvement for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Involvements"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        # Verificar autenticación para POST
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.exceptions import NotAuthenticated
        
        if (
            isinstance(request.user, AnonymousUser)
            or not request.user.is_authenticated
        ):
            raise NotAuthenticated("Authentication credentials are required to create an involvement.")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return APIResponse.success(
                data=serializer.data,
                message="Involvement created successfully",
                status_code=status.HTTP_201_CREATED
            )
        else:
             return APIResponse.validation_error(
                 errors=serializer.errors,
                 message="Validation error in submitted data"
             )

    def perform_create(self, serializer):
        """Set the tournament when creating an involvement."""
        from rest_framework.exceptions import NotFound, ValidationError

        tournament_id = self.kwargs["tournament_id"]

        # Verify tournament exists
        tournament = Tournament.objects.filter(id=tournament_id).first()
        
        if not tournament:
            raise NotFound("Tournament not found.")

        # Check if user is admin of the tournament's organization
        is_admin = False
        if self.request.user.administered_organizations.filter(id=tournament.organization_id).exists():
            is_admin = True
            
        if not is_admin and tournament.status != TournamentStatus.PUBLISHED:
             raise NotFound("Tournament not found or not published.")

        try:
            serializer.save(tournament=tournament)
        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                 raise ValidationError("An involvement for this player in this division already exists.")
            raise


class InvolvementRetrieveUpdateDestroyView(
    StandardResponseMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    Retrieve, update or delete an involvement.
    La organización se obtiene del usuario logueado.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return InvolvementUpdateSerializer
        return InvolvementSerializer

    def get_queryset(self):
        """Filter involvements by tournament, organization and user permissions."""
        # Detectar si es una vista falsa de Swagger para generación de esquema
        if getattr(self, 'swagger_fake_view', False):
            return Involvement.objects.none()
        
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.exceptions import PermissionDenied

        # Ensure user is authenticated
        if (
            isinstance(self.request.user, AnonymousUser)
            or not self.request.user.is_authenticated
        ):
            from rest_framework.exceptions import NotAuthenticated

            raise NotAuthenticated("Authentication credentials were not provided.")

        # Obtener la organización del usuario logueado
        user = self.request.user
        user_organizations = user.administered_organizations.all()
        
        if not user_organizations.exists():
            return Involvement.objects.none()
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verificar que el tournament_id exista en los kwargs
        tournament_id = self.kwargs.get("tournament_id")
        
        if not tournament_id:
            return Involvement.objects.none()

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()
        if not tournament:
            return Involvement.objects.none()

        return Involvement.objects.select_related(
            "player", "tournament", "division", "approved_by"
        ).filter(tournament_id=tournament_id)

    @swagger_auto_schema(
        operation_summary="Get involvement",
        operation_description="Gets a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Involvements"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Involvement ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return APIResponse.success(
            data=response.data,
            message="Involvement retrieved successfully"
        )

    @swagger_auto_schema(
        operation_summary="Update involvement",
        operation_description="Updates a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Involvements"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Involvement ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
                
            return APIResponse.success(
                data=serializer.data,
                message="Involvement updated successfully"
            )
        else:
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Validation error"
            )

    @swagger_auto_schema(
        operation_summary="Partially update involvement",
        operation_description="Partially updates a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Involvements"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Involvement ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete involvement",
        operation_description="Deletes a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
        tags=["Involvements"],
        manual_parameters=[
            openapi.Parameter(
                "tournament_id",
                openapi.IN_PATH,
                description="Tournament ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Involvement ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
    )
    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return APIResponse.success(
            data=None,
            message="Involvement deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Approve involvement",
    operation_description="Approves a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
    tags=["Involvements"],
    manual_parameters=[
        openapi.Parameter(
            "tournament_id",
            openapi.IN_PATH,
            description="Tournament ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "pk",
            openapi.IN_PATH,
            description="Involvement ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_involvement(request, tournament_id, pk):
    """
    Approve an involvement.
    La organización se obtiene del usuario logueado.
    """
    try:
        # Obtener la organización del usuario logueado
        user_organizations = request.user.administered_organizations.all()
        
        if not user_organizations.exists():
            return APIResponse.forbidden(
                message="You do not have managed organizations.",
                error_code="FORBIDDEN_APPROVE_INVOLVEMENT",
            )
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()

        if not tournament:
            return APIResponse.not_found(
                message="Tournament not found in this organization.",
                error_code="TOURNAMENT_NOT_FOUND",
            )

        # Check if user has permission
        if not request.user.is_admin:
            if not request.user.administered_organizations.filter(
                id=organization_id
            ).exists():
                return APIResponse.forbidden(
                    message="You do not have permission to approve involvements.",
                    error_code="FORBIDDEN_APPROVE_INVOLVEMENT",
                )

        involvement = Involvement.objects.filter(
            pk=pk, tournament_id=tournament_id
        ).first()

        if not involvement:
            return APIResponse.not_found(
                message="Involvement not found.", error_code="INVOLVEMENT_NOT_FOUND"
            )


        if involvement.partner:
            partner_email = involvement.partner.email
            if partner_email:
                existing_approved = Involvement.objects.filter(
                    tournament_id=tournament_id,
                    division_id=involvement.division_id,
                    status=InvolvementStatus.APPROVED,
                    partner__email=partner_email
                ).exclude(pk=pk).first()
                if existing_approved:
                    return APIResponse.validation_error(
                        errors={
                            'involvements': [
                                f"Ya existe un jugador aprobado con el email {existing_approved.partner.email} en esta categoría."
                            ]
                        },
                        message=f"Ya existe un jugador aprobado con el email {existing_approved.partner.email} en esta categoría.",
                        error_code="PLAYER_ALREADY_APPROVED_IN_CATEGORY"
                    )

        # Validar si ya existe un jugador aprobado con el mismo email en la misma categoría
        # player_email = involvement.player.email
        # partner_email = involvement.partner.email
        # if player_email or partner_email:
        #     existing_approved = Involvement.objects.filter(
        #         tournament_id=tournament_id,
        #         division_id=involvement.division_id,
        #         status=InvolvementStatus.APPROVED,
        #     ).filter(Q(player__email=player_email) | Q(partner__email=partner_email)).exclude(pk=pk).first()
            
        #     if existing_approved:
        #         return APIResponse.validation_error(
        #             errors={
        #                 'involvements': [
        #                     f"Ya existe un jugador aprobado con el email {existing_approved.player.email if existing_approved.player else existing_approved.partner.email} en esta categoría."
        #                 ]
        #             },
        #             message=f"Ya existe un jugador aprobado con el email {existing_approved.player.email if existing_approved.player else existing_approved.partner.email} en esta categoría.",
        #             error_code="PLAYER_ALREADY_APPROVED_IN_CATEGORY"
        #         )

        involvement.approve(user=request.user)
        serializer = InvolvementSerializer(involvement)
        return APIResponse.success(
            data=serializer.data, message="Involvement approved successfully"
        )

    except Exception as e:
        return APIResponse.error(
            message=f"An error occurred while approving the involvement:{e}",
            error_code="INVOLVEMENT_APPROVAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Reject involvement",
    operation_description="Rejects a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
    tags=["Involvements"],
    manual_parameters=[
        openapi.Parameter(
            "tournament_id",
            openapi.IN_PATH,
            description="Tournament ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "pk",
            openapi.IN_PATH,
            description="Involvement ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_involvement(request, tournament_id, pk):
    """
    Reject an involvement.
    La organización se obtiene del usuario logueado.
    """
    try:
        # Obtener la organización del usuario logueado
        user_organizations = request.user.administered_organizations.all()
        
        if not user_organizations.exists():
            return APIResponse.forbidden(
                message="You do not have managed organizations.",
                error_code="FORBIDDEN_REJECT_INVOLVEMENT",
            )
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()

        if not tournament:
            return APIResponse.not_found(
                message="Tournament not found in this organization.",
                error_code="TOURNAMENT_NOT_FOUND",
            )

        # Check if user has permission
        if not request.user.is_admin:
            if not request.user.administered_organizations.filter(
                id=organization_id
            ).exists():
                return APIResponse.forbidden(
                    message="You do not have permission to reject involvements.",
                    error_code="FORBIDDEN_REJECT_INVOLVEMENT",
                )

        involvement = Involvement.objects.filter(
            pk=pk, tournament_id=tournament_id
        ).first()

        if not involvement:
            return APIResponse.not_found(
                message="Involvement not found.", error_code="INVOLVEMENT_NOT_FOUND"
            )

        involvement.reject()
        serializer = InvolvementSerializer(involvement)
        return APIResponse.success(
            data=serializer.data, message="Involvement rejected successfully"
        )

    except Exception as e:
        return APIResponse.error(
            message="An error occurred while rejecting the involvement.",
            error_code="INVOLVEMENT_REJECTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Toggle payment status",
    operation_description="Toggles the payment status of a specific involvement for a tournament. La organización se obtiene del usuario logueado.",
    tags=["Involvements"],
    manual_parameters=[
        openapi.Parameter(
            "tournament_id",
            openapi.IN_PATH,
            description="Tournament ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "pk",
            openapi.IN_PATH,
            description="Involvement ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_payment_status(request, tournament_id, pk):
    """
    Toggle the payment status of an involvement.
    La organización se obtiene del usuario logueado.
    """
    try:
        # Obtener la organización del usuario logueado
        user_organizations = request.user.administered_organizations.all()
        
        if not user_organizations.exists():
            return APIResponse.forbidden(
                message="You do not have managed organizations.",
                error_code="FORBIDDEN_MANAGE_PAYMENTS",
            )
        
        # Usar la primera organización que el usuario administra
        organization = user_organizations.first()
        organization_id = organization.id

        # Verify tournament belongs to the organization
        tournament = Tournament.objects.filter(
            id=tournament_id, organization_id=organization_id
        ).first()

        if not tournament:
            return APIResponse.not_found(
                message="Tournament not found in this organization.",
                error_code="TOURNAMENT_NOT_FOUND",
            )

        # Check if user has permission
        if not request.user.is_admin:
            if not request.user.administered_organizations.filter(
                id=organization_id
            ).exists():
                return APIResponse.forbidden(
                    message="You do not have permission to manage payments.",
                    error_code="FORBIDDEN_MANAGE_PAYMENTS",
                )

        involvement = Involvement.objects.filter(
            pk=pk, tournament_id=tournament_id
        ).first()

        if not involvement:
            return APIResponse.not_found(
                message="Involvement not found.", error_code="INVOLVEMENT_NOT_FOUND"
            )

        involvement.paid = not involvement.paid
        involvement.save()
        serializer = InvolvementSerializer(involvement)
        return APIResponse.success(
            data=serializer.data, message="Payment status updated successfully"
        )

    except Exception as e:
        return APIResponse.error(
            message="An error occurred while updating payment status.",
            error_code="PAYMENT_UPDATE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Publish division",
    operation_description="Publishes a division",
    tags=["Tournament Divisions"],
    manual_parameters=[
        openapi.Parameter(
            "tournament_id",
            openapi.IN_PATH,
            description="Tournament ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "pk",
            openapi.IN_PATH,
            description="Division ID",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def publish_division(request, tournament_id, pk):
    
    try:
        # Verificar que el torneo existe y pertenece a una organización del usuario
        Tournament.objects.select_related('organization').get(
            pk=tournament_id,
            organization__administrators=request.user
        )
    except Tournament.DoesNotExist:
        return APIResponse.not_found(
            message="Tournament not found or you don't have permission to access it",
            error_code="TOURNAMENT_NOT_FOUND"
        )
   
    try:
        division = TournamentDivision.objects.get(
            pk=pk,
            tournament_id=tournament_id
        )
    except TournamentDivision.DoesNotExist:
        return APIResponse.not_found(
            message="Division not found",
            error_code="DIVISION_NOT_FOUND")

    try:
        from .services import DivisionCompletionService
        
        service = DivisionCompletionService(division=division, user=request.user)
        published_division = service.publish_division()
        
        serializer = TournamentDivisionSerializer(published_division)
        return APIResponse.success(
            data=serializer.data,
            message="Division published successfully."
        )
    except TournamentBusinessError as e:
        return APIResponse.validation_error(
            errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
            message=str(e),
            error_code=e.error_code
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Unexpected error publishing division: {e}")
        return APIResponse.error(
            message="An unexpected error occurred",
            error_code="DIVISION_PUBLISH_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

          

    