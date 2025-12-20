"""
Views for payments app.
"""
from decimal import Decimal
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.api.mixins import StandardResponseMixin
from apps.api.utils import APIResponse
from apps.tournaments.models import Tournament, TournamentDivision, Involvement
from apps.players.models import PlayerProfile
from .models import Payment, PaymentTransaction
from .serializers import (
    PaymentSerializer,
    PaymentDetailsSerializer,
    PaymentTransactionSerializer,
    CreatePaymentTransactionSerializer,
    BulkCreatePaymentsSerializer
)
from .services import (
    PaymentCalculationService,
    PaymentProcessingService,
    BulkPaymentCreationService
)
from .exceptions import (
    PaymentBusinessError,
    PaymentNotFoundError,
    PaymentNotActiveError,
    PaymentAlreadyCompletedError,
    InvalidPaymentAmountError,
    TournamentHasNoDivisionsError
)


class PaymentViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """ViewSet for Payment CRUD operations."""
    
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def _check_permission(self, tournament: Tournament) -> bool:
        """Check if user is admin of the tournament's organization."""
        return self.request.user.administered_organizations.filter(
            id=tournament.organization_id
        ).exists()
    
    def get_queryset(self):
        """Get payments for divisions or tournaments the user can manage."""
        division_id = self.kwargs.get('division_id')
        tournament_id = self.kwargs.get('tournament_id')
        
        if division_id:
            division = get_object_or_404(TournamentDivision, pk=division_id)
            tournament = division.tournament
            if self._check_permission(tournament):
                return Payment.objects.filter(division=division)
        elif tournament_id:
            tournament = get_object_or_404(Tournament, pk=tournament_id)
            if self._check_permission(tournament):
                return Payment.objects.filter(tournament=tournament)
        
        # Return empty queryset if user doesn't have permission
        return Payment.objects.none()
    
    def get_object(self):
        """Get payment object for division or tournament."""
        division_id = self.kwargs.get('division_id')
        tournament_id = self.kwargs.get('tournament_id')
        
        if division_id:
            division = get_object_or_404(TournamentDivision, pk=division_id)
            tournament = division.tournament
            if not self._check_permission(tournament):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to access this payment.")
            
            payment = Payment.objects.filter(division=division).first()
            if not payment:
                raise PaymentNotFoundError(division_id=division_id)
            return payment
        elif tournament_id:
            tournament = get_object_or_404(Tournament, pk=tournament_id)
            if not self._check_permission(tournament):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to access this payment.")
            
            payment = Payment.objects.filter(tournament=tournament).first()
            if not payment:
                raise PaymentNotFoundError(tournament_id=tournament_id)
            return payment
        else:
            from rest_framework.exceptions import NotFound
            raise NotFound("Either division_id or tournament_id must be provided.")
    
    @swagger_auto_schema(
        operation_summary="Get payment configuration",
        operation_description="Obtiene la configuraci?n de pago para una divisi?n espec?fica. El usuario debe ser administrador de la organizaci?n del torneo.",
        responses={
            200: PaymentSerializer(),
            404: "Payment configuration not found",
            403: "Permission denied"
        },
        tags=["Payments"],
        security=[{'Bearer': []}]
    )
    def retrieve(self, request, *args, **kwargs):
        """Handle payment retrieval."""
        try:
            obj = self.get_object()
            serializer = self.get_serializer(obj)
            return APIResponse.success(
                data=serializer.data,
                message="Payment configuration retrieved successfully"
            )
        except PaymentNotFoundError as e:
            return APIResponse.not_found(
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            return APIResponse.error(
                message=str(e),
                error_code="ERROR_PAYMENT_RETRIEVAL_FAILED",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Create payment configuration for division or tournament."""
        division_id = self.kwargs.get('division_id')
        tournament_id = self.kwargs.get('tournament_id')
        
        # Fallback: extraer tournament_id de la URL si no está en kwargs
        if not tournament_id and not division_id:
            from django.urls import resolve
            try:
                resolved = resolve(self.request.path)
                tournament_id = resolved.kwargs.get('tournament_id')
                division_id = resolved.kwargs.get('division_id')
            except Exception:
                pass
        
        if division_id:
            division = get_object_or_404(TournamentDivision, pk=division_id)
            tournament = division.tournament
            if not self._check_permission(tournament):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to create payment for this division.")
            
            # Check if payment already exists
            if Payment.objects.filter(division=division).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'division': 'Payment configuration already exists for this division.'
                })
            
            serializer.save(division=division)
        elif tournament_id:
            tournament = get_object_or_404(Tournament, pk=tournament_id)
            if not self._check_permission(tournament):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to create payment for this tournament.")
            
            # Check if payment already exists
            if Payment.objects.filter(tournament=tournament).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'tournament': 'Payment configuration already exists for this tournament.'
                })
            
            serializer.save(tournament=tournament)
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'tournament': 'Either tournament or division must be specified.',
                'division': 'Either tournament or division must be specified.'
            })
    
    @swagger_auto_schema(
        operation_summary="Create payment configuration",
        operation_description="Crea una nueva configuración de pago para un torneo o división. El usuario debe ser administrador de la organización del torneo.",
        request_body=PaymentSerializer,
        responses={
            201: PaymentSerializer(),
            400: "Invalid data or payment already exists",
            403: "Permission denied"
        },
        tags=["Payments"],
        security=[{'Bearer': []}]
    )
    def create(self, request, *args, **kwargs):
        """Handle payment creation."""
        try:
            # Actualizar self.kwargs con los kwargs de la URL antes de llamar a super().create()
            # Esto asegura que perform_create() tenga acceso a tournament_id y division_id
            if 'tournament_id' in kwargs:
                self.kwargs['tournament_id'] = kwargs['tournament_id']
            if 'division_id' in kwargs:
                self.kwargs['division_id'] = kwargs['division_id']
            
            response = super().create(request, *args, **kwargs)
            if isinstance(response, Response) and response.status_code == status.HTTP_201_CREATED:
                return APIResponse.created(
                    data=response.data,
                    message="Payment configuration created successfully"
                )
            return response
        except Exception as e:
            return APIResponse.error(
                message=str(e),
                error_code="ERROR_PAYMENT_CREATION_FAILED",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_summary="Update payment configuration",
        operation_description="Actualiza la configuraci?n de pago de una divisi?n. El usuario debe ser administrador de la organizaci?n del torneo.",
        request_body=PaymentSerializer,
        responses={
            200: PaymentSerializer(),
            400: "Invalid data",
            403: "Permission denied",
            404: "Payment configuration not found"
        },
        tags=["Payments"],
        security=[{'Bearer': []}]
    )
    def update(self, request, *args, **kwargs):
        """Handle payment update."""
        try:
            response = super().update(request, *args, **kwargs)
            if isinstance(response, Response) and response.status_code == status.HTTP_200_OK:
                return APIResponse.success(
                    data=response.data,
                    message="Payment configuration updated successfully"
                )
            return response
        except Exception as e:
            return APIResponse.error(
                message=str(e),
                error_code="ERROR_PAYMENT_UPDATE_FAILED",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_summary="Partially update payment configuration",
        operation_description="Actualiza parcialmente la configuración de pago de una división. El usuario debe ser administrador de la organización del torneo.",
        request_body=PaymentSerializer,
        responses={
            200: PaymentSerializer(),
            400: "Invalid data",
            403: "Permission denied",
            404: "Payment configuration not found"
        },
        tags=["Payments"],
        security=[{'Bearer': []}]
    )
    def partial_update(self, request, *args, **kwargs):
        """Handle partial payment update."""
        try:
            response = super().partial_update(request, *args, **kwargs)
            if isinstance(response, Response) and response.status_code == status.HTTP_200_OK:
                return APIResponse.success(
                    data=response.data,
                    message="Payment configuration updated successfully"
                )
            return response
        except Exception as e:
            return APIResponse.error(
                message=str(e),
                error_code="ERROR_PAYMENT_UPDATE_FAILED",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_summary="Delete payment configuration",
        operation_description="Elimina la configuraci?n de pago de una divisi?n. El usuario debe ser administrador de la organizaci?n del torneo.",
        responses={
            204: "Payment configuration deleted successfully",
            403: "Permission denied",
            404: "Payment configuration not found"
        },
        tags=["Payments"],
        security=[{'Bearer': []}]
    )
    def destroy(self, request, *args, **kwargs):
        """Handle payment deletion."""
        try:
            super().destroy(request, *args, **kwargs)
            return APIResponse.success(
                message="Payment configuration deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return APIResponse.error(
                message=str(e),
                error_code="ERROR_PAYMENT_DELETION_FAILED",
                status_code=status.HTTP_400_BAD_REQUEST
            )


@swagger_auto_schema(
    method='get',
    operation_summary="Get payment details",
    operation_description="Obtiene los detalles de pago para una suscripci?n a una divisi?n, incluyendo descuentos aplicables. Se puede especificar un player_id en los query parameters, de lo contrario se usa el perfil del jugador autenticado.",
    manual_parameters=[
        openapi.Parameter(
            'player_id',
            openapi.IN_QUERY,
            description="ID del jugador (opcional). Si no se proporciona, se usa el perfil del usuario autenticado.",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
    ],
    responses={
        200: PaymentDetailsSerializer(),
        400: "Payment not active or invalid data",
        404: "Tournament, division, payment or player profile not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_details(request, tournament_id: int, division_id: int):
    """
    Get payment details for a division subscription.
    
    Args:
        request: HTTP request
        tournament_id: Tournament ID
        division_id: Division ID
        player_id: Optional player ID (query parameter)
    
    Returns:
        Payment details with discounts applied
    """
    try:
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        division = get_object_or_404(TournamentDivision, pk=division_id, tournament=tournament)
        
        # Get player from query parameter or use authenticated user's player profile
        player_id = request.query_params.get('player_id')
        if player_id:
            player = get_object_or_404(PlayerProfile, pk=player_id)
        else:
            # Try to get player profile from authenticated user
            try:
                player = PlayerProfile.objects.get(user=request.user)
            except PlayerProfile.DoesNotExist:
                return APIResponse.error(
                    message="Player profile not found for authenticated user.",
                    error_code="ERROR_PLAYER_PROFILE_NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        
        # Calculate payment details
        service = PaymentCalculationService(
            tournament=tournament,
            division=division,
            player=player
        )
        
        payment_details = service.get_payment_details()
        serializer = PaymentDetailsSerializer(payment_details)
        
        return APIResponse.success(
            data=serializer.data,
            message="Payment details retrieved successfully"
        )
    
    except PaymentNotFoundError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    except PaymentNotActiveError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except PaymentBusinessError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception:
        return APIResponse.error(
            message="An unexpected error occurred while calculating payment details.",
            error_code="ERROR_PAYMENT_CALCULATION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Create payment transaction",
    operation_description="Crea una transacción de pago para una participación (involvement). Permite subir un comprobante de pago como archivo.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'involvement_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID de la participación'),
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Monto del pago'),
            'payment_method': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['CASH', 'BANK_TRANSFER', 'CREDIT_CARD', 'DEBIT_CARD', 'OTHER'],
                description='Método de pago'
            ),
            'transaction_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID de transacción (opcional)'),
            'payment_reference': openapi.Schema(type=openapi.TYPE_STRING, description='Referencia de pago (opcional)'),
            'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Notas adicionales (opcional)'),
            'payment_proof': openapi.Schema(type=openapi.TYPE_FILE, description='Comprobante de pago (PDF, PNG, JPG, JPEG, máx. 10MB)')
        },
        required=['involvement_id', 'amount', 'payment_method']
    ),
    responses={
        201: PaymentTransactionSerializer(),
        400: "Invalid data, payment already completed, or invalid amount"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_transaction(request):
    """
    Create a payment transaction for an involvement.
    
    POST /api/v1/payments/transactions/
    """
    try:
        serializer = CreatePaymentTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        involvement = get_object_or_404(
            Involvement,
            pk=serializer.validated_data['involvement_id']
        )
        
        # Get payment proof file if provided
        payment_proof = request.FILES.get('payment_proof')
        
        # Create payment transaction
        service = PaymentProcessingService(
            involvement=involvement,
            amount=serializer.validated_data['amount'],
            payment_method=serializer.validated_data['payment_method'],
            transaction_id=serializer.validated_data.get('transaction_id'),
            payment_reference=serializer.validated_data.get('payment_reference'),
            notes=serializer.validated_data.get('notes'),
            payment_proof=payment_proof,
            user=request.user
        )
        
        payment_transaction = service.create_payment_transaction()
        response_serializer = PaymentTransactionSerializer(
            payment_transaction,
            context={'request': request}
        )
        
        return APIResponse.created(
            data=response_serializer.data,
            message="Payment transaction created successfully"
        )
    
    except PaymentAlreadyCompletedError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except InvalidPaymentAmountError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception:
        return APIResponse.error(
            message="An error occurred while creating payment transaction.",
            error_code="ERROR_PAYMENT_TRANSACTION_CREATION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Confirm payment transaction",
    operation_description="Confirma una transacción de pago pendiente. Solo puede ser confirmada por un administrador de la organización.",
    responses={
        200: PaymentTransactionSerializer(),
        400: "Payment already completed or invalid transaction",
        404: "Transaction not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request, transaction_id: int):
    """
    Confirm a payment transaction.
    
    POST /api/v1/payments/transactions/{transaction_id}/confirm/
    """
    try:
        payment_transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
        
        # Check if already completed
        # if payment_transaction.status == PaymentStatus.COMPLETED:
        #     raise PaymentAlreadyCompletedError()
        
        # Mark as completed (updates all related involvements)
        payment_transaction.mark_as_completed(user=request.user)
        
        serializer = PaymentTransactionSerializer(
            payment_transaction,
            context={'request': request}
        )
        
        return APIResponse.success(
            data=serializer.data,
            message="Payment confirmed successfully"
        )
    
    except PaymentAlreadyCompletedError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception:
        return APIResponse.error(
            message="An error occurred while confirming payment.",
            error_code="ERROR_PAYMENT_CONFIRMATION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get involvement payment transactions",
    operation_description="Obtiene todas las transacciones de pago asociadas a una participación específica.",
    responses={
        200: PaymentTransactionSerializer(many=True),
        404: "Involvement not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_involvement_payments(request, involvement_id: int):
    """
    Get all payment transactions for an involvement.
    
    GET /api/v1/payments/involvements/{involvement_id}/transactions/
    """
    involvement = get_object_or_404(Involvement, pk=involvement_id)
    transactions = PaymentTransaction.objects.filter(involvements=involvement)
    serializer = PaymentTransactionSerializer(
        transactions,
        many=True,
        context={'request': request}
    )
    
    return APIResponse.success(
        data=serializer.data,
        message="Payment transactions retrieved successfully"
    )


@swagger_auto_schema(
    method='post',
    operation_summary="Bulk create tournament payments",
    operation_description="Crea o actualiza las configuraciones de pago para todas las divisiones de un torneo. El usuario debe ser administrador de la organización del torneo.",
    request_body=BulkCreatePaymentsSerializer,
    responses={
        200: openapi.Response(
            description="Payments created/updated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'meta': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'created_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'updated_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'total_divisions': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                }
            )
        ),
        400: "Invalid data or tournament has no divisions",
        403: "Permission denied",
        404: "Tournament not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_tournament_payments(request, tournament_id: int):
    """
    Create or update payments for all divisions of a tournament.
    
    POST /api/v1/tournaments/{tournament_id}/payments/bulk-create/
    
    Body:
    {
        "subscription_fee": "100.00",
        "early_payment_discount_amount": "10.00",
        "early_payment_discount_deadline": "2024-12-31T23:59:59Z",
        "second_category_discount_amount": "5.00"
    }
    """
    try:
        # Get tournament and validate user permissions
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        
        # Check if user is admin of the tournament's organization
        if not request.user.administered_organizations.filter(
            id=tournament.organization_id
        ).exists():
            return APIResponse.forbidden(
                message="You do not have permission to manage payments for this tournament.",
                error_code="ERROR_PERMISSION_DENIED"
            )
        
        # Validate request data
        serializer = BulkCreatePaymentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create or update payments for all divisions
        service = BulkPaymentCreationService(
            tournament=tournament,
            subscription_fee=serializer.validated_data['subscription_fee'],
            early_payment_discount_amount=serializer.validated_data.get(
                'early_payment_discount_amount',
                Decimal('0.00')
            ),
            early_payment_discount_deadline=serializer.validated_data.get(
                'early_payment_discount_deadline'
            ),
            second_category_discount_amount=serializer.validated_data.get(
                'second_category_discount_amount',
                Decimal('0.00')
            )
        )
        
        payments = service.execute()
        
        # Serialize payments
        payment_serializer = PaymentSerializer(
            payments,
            many=True,
            context={'request': request}
        )
        
        # Prepare response with metadata
        total_divisions = len(payments)
        meta = {
            'created_count': service.created_count,
            'updated_count': service.updated_count,
            'total_divisions': total_divisions
        }
        
        return APIResponse.success(
            data=payment_serializer.data,
            message="Payments created/updated successfully for all divisions",
            meta=meta
        )
    
    except TournamentHasNoDivisionsError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except PaymentBusinessError as e:
        return APIResponse.error(
            message=str(e),
            error_code=e.error_code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception:
        return APIResponse.error(
            message="An unexpected error occurred while creating payments.",
            error_code="ERROR_BULK_PAYMENT_CREATION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get tournament payment transactions",
    operation_description="""
    Obtiene todas las transacciones de pago de un torneo.
    El usuario debe ser administrador de la organización del torneo.
    
    Filtros disponibles:
    - status: Filtrar por estado (pending, completed, failed, cancelled, refunded)
    - player_id: Filtrar por jugador específico
    - date_from: Fecha desde (YYYY-MM-DD)
    - date_to: Fecha hasta (YYYY-MM-DD)
    - payment_method: Método de pago (cash, bank_transfer, credit_card, etc.)
    """,
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filtrar por estado de la transacción",
            type=openapi.TYPE_STRING,
            enum=['pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded'],
            required=False
        ),
        openapi.Parameter(
            'player_id',
            openapi.IN_QUERY,
            description="Filtrar por ID del jugador",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
        openapi.Parameter(
            'date_from',
            openapi.IN_QUERY,
            description="Fecha desde (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'date_to',
            openapi.IN_QUERY,
            description="Fecha hasta (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'payment_method',
            openapi.IN_QUERY,
            description="Método de pago",
            type=openapi.TYPE_STRING,
            enum=['cash', 'bank_transfer', 'credit_card', 'debit_card', 'stripe', 'paypal', 'other'],
            required=False
        ),
    ],
    responses={
        200: PaymentTransactionSerializer(many=True),
        403: "Permission denied",
        404: "Tournament not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tournament_transactions(request, tournament_id: int):
    """
    Get all payment transactions for a tournament.
    
    GET /api/v1/tournaments/{tournament_id}/transactions/
    """
    try:
        from django.utils.dateparse import parse_date
        
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        
        # Check if user is admin of the tournament's organization
        if not request.user.administered_organizations.filter(
            id=tournament.organization_id
        ).exists():
            return APIResponse.forbidden(
                message="You do not have permission to view transactions for this tournament.",
                error_code="ERROR_PERMISSION_DENIED"
            )
        
        # Get transactions for this tournament
        transactions = PaymentTransaction.objects.filter(
            involvements__tournament=tournament
        ).distinct().select_related(
            'processed_by'
        ).prefetch_related(
            'involvements',
            'involvements__player',
            'involvements__division',
            'items',
            'items__involvement'
        ).order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        player_id = request.query_params.get('player_id')
        if player_id:
            transactions = transactions.filter(involvements__player_id=player_id)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                date_from_parsed = parse_date(date_from)
                if date_from_parsed:
                    transactions = transactions.filter(created_at__date__gte=date_from_parsed)
            except (ValueError, TypeError):
                pass
        
        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                date_to_parsed = parse_date(date_to)
                if date_to_parsed:
                    transactions = transactions.filter(created_at__date__lte=date_to_parsed)
            except (ValueError, TypeError):
                pass
        
        payment_method = request.query_params.get('payment_method')
        if payment_method:
            transactions = transactions.filter(payment_method=payment_method)
        
        # Serialize transactions
        serializer = PaymentTransactionSerializer(
            transactions,
            many=True,
            context={'request': request}
        )
        
        return APIResponse.success(
            data=serializer.data,
            message="Tournament transactions retrieved successfully"
        )
    
    except Exception:
        return APIResponse.error(
            message="An error occurred while retrieving tournament transactions.",
            error_code="ERROR_TRANSACTIONS_RETRIEVAL_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get payment transaction details",
    operation_description="""
    Obtiene los detalles completos de una transacción de pago, incluyendo items detallados.
    Útil para generar facturas.
    
    El usuario debe ser:
    - Administrador de la organización del torneo, o
    - El jugador que realizó el pago
    """,
    responses={
        200: PaymentTransactionSerializer(),
        403: "Permission denied",
        404: "Transaction not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_detail(request, transaction_id: int):
    """
    Get detailed information about a payment transaction.
    
    GET /api/v1/payments/transactions/{transaction_id}/
    """
    try:
        transaction = PaymentTransaction.objects.select_related(
            'processed_by'
        ).prefetch_related(
            'involvements',
            'involvements__player',
            'involvements__tournament',
            'involvements__division',
            'items',
            'items__involvement',
            'items__involvement__player',
            'items__involvement__division'
        ).get(pk=transaction_id)
        
        # Check permissions: admin of tournament organization OR the player who made the payment
        first_involvement = transaction.involvements.first()
        if not first_involvement:
            return APIResponse.not_found(
                message="Transaction has no associated involvements.",
                error_code="ERROR_TRANSACTION_INVALID"
            )
        
        tournament = first_involvement.tournament
        is_admin = request.user.administered_organizations.filter(
            id=tournament.organization_id
        ).exists()
        
        is_player = False
        try:
            player_profile = PlayerProfile.objects.get(user=request.user)
            is_player = transaction.involvements.filter(player=player_profile).exists()
        except PlayerProfile.DoesNotExist:
            pass
        
        if not (is_admin or is_player):
            return APIResponse.forbidden(
                message="You do not have permission to view this transaction.",
                error_code="ERROR_PERMISSION_DENIED"
            )
        
        serializer = PaymentTransactionSerializer(
            transaction,
            context={'request': request}
        )
        
        return APIResponse.success(
            data=serializer.data,
            message="Transaction details retrieved successfully"
        )
    
    except PaymentTransaction.DoesNotExist:
        return APIResponse.not_found(
            message="Transaction not found.",
            error_code="ERROR_TRANSACTION_NOT_FOUND"
        )
    
    except Exception:
        return APIResponse.error(
            message="An error occurred while retrieving transaction details.",
            error_code="ERROR_TRANSACTION_RETRIEVAL_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get player transactions in tournament",
    operation_description="""
    Obtiene todas las transacciones de pago de un jugador específico en un torneo.
    
    El usuario debe ser:
    - Administrador de la organización del torneo, o
    - El mismo jugador
    """,
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filtrar por estado de la transacción",
            type=openapi.TYPE_STRING,
            enum=['pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded'],
            required=False
        ),
    ],
    responses={
        200: PaymentTransactionSerializer(many=True),
        403: "Permission denied",
        404: "Tournament or player not found"
    },
    tags=["Payments"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_player_tournament_transactions(request, tournament_id: int, player_id: int):
    """
    Get all payment transactions for a specific player in a tournament.
    
    GET /api/v1/tournaments/{tournament_id}/players/{player_id}/transactions/
    """
    try:
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        player = get_object_or_404(PlayerProfile, pk=player_id)
        
        # Check permissions: admin of tournament organization OR the same player
        is_admin = request.user.administered_organizations.filter(
            id=tournament.organization_id
        ).exists()
        
        is_player = False
        try:
            player_profile = PlayerProfile.objects.get(user=request.user)
            is_player = (player_profile.id == player.id)
        except PlayerProfile.DoesNotExist:
            pass
        
        if not (is_admin or is_player):
            return APIResponse.forbidden(
                message="You do not have permission to view these transactions.",
                error_code="ERROR_PERMISSION_DENIED"
            )
        
        # Get transactions for this player in this tournament
        transactions = PaymentTransaction.objects.filter(
            involvements__tournament=tournament,
            involvements__player=player
        ).distinct().select_related(
            'processed_by'
        ).prefetch_related(
            'involvements',
            'involvements__player',
            'involvements__division',
            'items',
            'items__involvement'
        ).order_by('-created_at')
        
        # Apply status filter if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        # Serialize transactions
        serializer = PaymentTransactionSerializer(
            transactions,
            many=True,
            context={'request': request}
        )
        
        return APIResponse.success(
            data=serializer.data,
            message="Player tournament transactions retrieved successfully"
        )
    
    except Exception:
        return APIResponse.error(
            message="An error occurred while retrieving player transactions.",
            error_code="ERROR_PLAYER_TRANSACTIONS_RETRIEVAL_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

