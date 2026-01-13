"""
API views for player profiles.
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from .models import PlayerProfile, PlayerConsent
from .permissions import CanCreatePlayerProfile, IsOwner
from .serializers import (
    PlayerProfileCreateSerializer,
    PlayerProfileSerializer,
    PlayerProfileUpdateSerializer,
    PlayerSubscriptionSerializer,
)
from apps.api.mixins import StandardModelViewSet
from apps.api.utils import get_client_ip
from apps.tournaments.models import TournamentDivision, Involvement, InvolvementStatus


class PlayerProfileViewSet(StandardModelViewSet):
    """
    ViewSet para gestionar perfiles de jugadores.
    
    - create: Cualquier usuario autenticado puede crear su perfil
    - me: Obtener el perfil del usuario actual
    - retrieve: Solo el propietario puede ver su perfil
    - update: Solo el propietario puede actualizar su perfil
    - destroy: Solo el propietario puede eliminar su perfil
    """
    queryset = PlayerProfile.objects.all()
    serializer_class = PlayerProfileSerializer
    
    def get_permissions(self):
        """Retorna los permisos según la acción."""
        if self.action == 'complete_subscription':
            # No requiere autenticación - crea PlayerProfile directamente
            permission_classes = []
        elif self.action == 'create':
            permission_classes = [CanCreatePlayerProfile]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwner]
        elif self.action == 'me':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'create':
            return PlayerProfileCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlayerProfileUpdateSerializer
        return PlayerProfileSerializer
    
    def get_queryset(self):
        """
        Retorna solo el perfil del usuario actual.
        Los usuarios solo pueden ver su propio perfil.
        """
        # Detectar si es una vista falsa de Swagger para generación de esquema
        if getattr(self, 'swagger_fake_view', False):
            return PlayerProfile.objects.none()
        
        user = self.request.user
        # Verificar que el usuario no sea AnonymousUser
        if not user.is_authenticated:
            return PlayerProfile.objects.none()
        
        return PlayerProfile.objects.filter(user=user)
    
    @swagger_auto_schema(
        operation_description="Crea un perfil de jugador para el usuario actual",
        request_body=PlayerProfileCreateSerializer,
        responses={
            201: PlayerProfileSerializer(),
            400: "Datos inválidos o ya tiene un perfil",
            401: "No autenticado"
        },
        security=[{'Bearer': []}]
    )
    def create(self, request, *args, **kwargs):
        """
        Crea un perfil de jugador.
        El usuario actual se vincula automáticamente.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            player_profile = serializer.save()
            output_serializer = PlayerProfileSerializer(player_profile)
            return self.created_response(
                data=output_serializer.data,
                message="Player profile created successfully"
            )
        else:
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in profile data"
            )
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="Obtiene el perfil del usuario actual",
        responses={
            200: PlayerProfileSerializer(),
            404: "No tiene perfil de jugador"
        },
        security=[{'Bearer': []}]
    )
    def me(self, request):
        """
        Retorna el perfil del usuario actual.
        """
        try:
            player_profile = request.user.player_profile
            serializer = PlayerProfileSerializer(player_profile)
            return self.success_response(
                data=serializer.data,
                message="Player profile retrieved successfully"
            )
        except PlayerProfile.DoesNotExist:
            return self.not_found_response(
                message="You do not have a player profile",
                error_code="PLAYER_PROFILE_NOT_FOUND"
            )
    
    @swagger_auto_schema(
        operation_description="Obtiene detalles del perfil de jugador",
        responses={
            200: PlayerProfileSerializer(),
            403: "No es el propietario",
            404: "Perfil no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def retrieve(self, request, *args, **kwargs):
        """Obtiene detalles del perfil."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza el perfil de jugador (solo propietario)",
        request_body=PlayerProfileUpdateSerializer,
        responses={
            200: PlayerProfileSerializer(),
            400: "Datos inválidos",
            403: "No es el propietario",
            404: "Perfil no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def update(self, request, *args, **kwargs):
        """Actualiza el perfil."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza parcialmente el perfil de jugador",
        request_body=PlayerProfileUpdateSerializer,
        responses={
            200: PlayerProfileSerializer(),
            400: "Datos inválidos",
            403: "No es el propietario",
            404: "Perfil no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente el perfil."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Elimina el perfil de jugador (solo propietario)",
        responses={
            204: "Perfil eliminado",
            403: "No es el propietario",
            404: "Perfil no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def destroy(self, request, *args, **kwargs):
        """Elimina el perfil."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], url_path='complete-subscription', permission_classes=[])
    @swagger_auto_schema(
        operation_summary="Completar suscripción del jugador",
        operation_description="""
        Completa la suscripción completa del jugador (no requiere autenticación):
        1. Crea o actualiza el perfil del jugador con first_name, last_name y email
        2. Crea los involvements en las divisiones seleccionadas
        3. Crea el consentimiento de términos y condiciones
        
        El JSON debe incluir:
        - Datos del perfil (first_name, last_name, email, gender, etc.)
        - Lista de involvements (division_id, partner_email si es doubles, is_doubles)
        - Aceptación de política de privacidad y términos
        
        El perfil se crea directamente sin necesidad de un usuario asociado.
        """,
        request_body=PlayerSubscriptionSerializer,
        responses={
            201: openapi.Response(
                description="Suscripción completada exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'profile': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Player profile data"
                                ),
                                'involvements': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                ),
                                'consent': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        )
                    }
                )
            ),
            400: "Datos inválidos",
            404: "División no encontrada"
        }
    )
    def complete_subscription(self, request):
        """
        Completa la suscripción completa del jugador.
        Crea/actualiza perfil, involvements y consent.
        No requiere autenticación - crea el PlayerProfile directamente.
        """
       
        serializer = PlayerSubscriptionSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in subscription data"
            )
        
        validated_data = serializer.validated_data
        email = validated_data['email'].lower()
        
        try:
            with transaction.atomic():
                # 1. Crear o actualizar PlayerProfile
                # Manejar second_last_name - agregarlo al last_name si viene
                # last_name = validated_data['last_name']
                # second_last_name = validated_data.get('second_last_name', '').strip()
                # if second_last_name:
                #     last_name = f"{last_name} {second_last_name}"
               
                
                profile_data = {
                    'first_name': validated_data['first_name'],
                    'last_name': validated_data['last_name'],
                    'gender': validated_data['gender'],
                    'nationality_id': validated_data['nationality_id'],
                    'email': validated_data['email'],
                    'middle_name': validated_data.get('middle_name', ''),
                    'date_of_birth': validated_data.get('date_of_birth'),
                    'phone': validated_data.get('phone', ''),
                    'height_cm': validated_data.get('height_cm'),
                    'shirt_size': validated_data.get('shirt_size', ''),
                    'weight_kg': validated_data.get('weight_kg'),
                    'handedness': validated_data.get('handedness', ''),
                    'emergency_contact_first_name': validated_data.get('emergency_contact_first_name', ''),
                    'emergency_contact_last_name': validated_data.get('emergency_contact_last_name', ''),
                    'emergency_contact_phone': validated_data.get('emergency_contact_phone', ''),
                    'emergency_contact_relationship': validated_data.get('emergency_contact_relationship', ''),
                    'health_insurance': validated_data.get('health_insurance', ''),
                    'blood_type': validated_data.get('blood_type', ''),
                    'medical_conditions': validated_data.get('medical_conditions', ''),
                    'avatar': validated_data.get('avatar'),
                }

                print('profile_data', profile_data)
                
                # Remover campos None o vacíos (excepto los que pueden ser 0 o avatar)
                profile_data = {k: v for k, v in profile_data.items() if v is not None and (v != '' or k in ['avatar'])}
               
                # Crear o actualizar PlayerProfile basado en email (sin usuario)
                profile, created = PlayerProfile.objects.update_or_create(
                    email=email,
                    defaults=profile_data
                )
               
                # 2. Crear involvements
                created_involvements = []
                for inv_data in validated_data['involvements']:
                    division_id = inv_data['division_id']
                    is_doubles = inv_data.get('is_doubles', False)
                    partner_email = inv_data.get('partner_email', '').strip()

                    
                    # Limpiar partner_email si viene como "undefined"
                    if partner_email.lower() in ['undefined', 'null']:
                        partner_email = ''
                    
                    try:
                        division = TournamentDivision.objects.select_related('tournament').get(id=division_id)
                    except TournamentDivision.DoesNotExist:
                        return self.not_found_response(
                            message=f"Division with id {division_id} not found",
                            error_code="DIVISION_NOT_FOUND"
                        )
                    
                    tournament = division.tournament
                   
                    # Si es doubles, buscar o crear el partner_profile
                    partner_profile = None
                    if is_doubles and partner_email:
                        if partner_email.lower() == email.lower():
                            return self.validation_error_response(
                                errors={'involvements': 'You cannot be your own partner.'},
                                message="Invalid partner email"
                            )
                        
                        
                        # Crear o obtener el PlayerProfile del partner
                        partner_profile, _ = PlayerProfile.objects.get_or_create(
                            email=partner_email.lower(),
                            defaults={
                                'first_name': inv_data.get('partner_first_name', ''),
                                'last_name': inv_data.get('partner_last_name', ''),
                            }
                        )
                    
                    # Verificar si ya existe un involvement para este perfil en esta división
                    existing_involvement = Involvement.objects.filter(
                        tournament=tournament,
                        player=profile,
                        division=division
                    ).first()
                    
                    if existing_involvement:
                        return self.validation_error_response(
                            errors={
                                'involvements': [
                                    f'Already exists a subscription for the player with email {email} in the category "{division.name}".'
                                ]
                            },
                            message=f"Already exists a subscription for the player with email {email} in the category '{division.name}'"
                        )
                    
                    # Crear involvement (solo si no existe)
                    involvement = Involvement.objects.create(
                        tournament=tournament,
                        player=profile,
                        division=division,
                        partner=partner_profile,
                        status=InvolvementStatus.PENDING,
                    )
                    created_involvements.append(involvement)
              
                # 3. Crear PlayerConsent
                client_ip = get_client_ip(request)
                now = timezone.now()
                
                consent = PlayerConsent.objects.create(
                    profile=profile,
                    accepted_privacy_policy=validated_data['privacy_policy_accepted'],
                    privacy_policy_version="1.0.0",
                    accepted_terms=validated_data['terms_conditions_accepted'],
                    terms_version="1.0.0",
                    consent_accepted_at=now,
                    terms_accepted_at=now,
                    consent_ip_address=client_ip
                )
                
                # 4. Crear PaymentTransaction si se proporcionan datos de pago
                payment_transaction = None
                if (
                    validated_data.get('total_paid') is not None and
                    validated_data.get('payment_method') is not None
                ):
                    from apps.payments.services import (
                        BulkPaymentValidationService,
                        BulkPaymentCalculationService
                    )
                    from apps.payments.models import PaymentTransaction, PaymentStatus
                    from decimal import Decimal
                    
                    # Validar que todos los involvements tengan Payment configurado
                    for involvement in created_involvements:
                        division = involvement.division
                        tournament = involvement.tournament
                        
                        # Verificar si existe configuración de pago
                        from apps.payments.models import Payment
                        has_payment = (
                            Payment.objects.filter(division=division, is_active=True).exists() or
                            Payment.objects.filter(tournament=tournament, is_active=True).exists()
                        )
                        
                        if not has_payment:
                            return self.validation_error_response(
                                errors={
                                    'payment': [
                                        f'Payment configuration not found for division "{division.name}". '
                                        'Cannot create payment transaction.'
                                    ]
                                },
                                message="Payment configuration required for all divisions"
                            )
                    
                    # Validar valores de pago
                    validation_service = BulkPaymentValidationService(
                        involvements=created_involvements,
                        player=profile,
                        total_paid=Decimal(str(validated_data['total_paid'])),
                        subtotal=Decimal(str(validated_data['subtotal'])) if validated_data.get('subtotal') else None,
                        total_discount=Decimal(str(validated_data['total_discount'])) if validated_data.get('total_discount') else None
                    )
                    
                    try:
                        validation_service.validate()
                    except Exception as e:
                        # Si es una excepción de negocio con error_code, retornarla con el formato correcto
                        if hasattr(e, 'error_code'):
                            return self.error_response(
                                message=str(e),
                                error_code=e.error_code,
                                errors=e.error_dict if hasattr(e, 'error_dict') else {'payment': [str(e)]},
                                status_code=status.HTTP_400_BAD_REQUEST
                            )
                        # Si no, retornar error genérico
                        return self.error_response(
                            message=f"Payment validation error: {str(e)}",
                            error_code="PAYMENT_VALIDATION_ERROR",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Obtener valores calculados
                    calculation_service = BulkPaymentCalculationService(
                        involvements=created_involvements,
                        player=profile
                    )
                    payment_details = calculation_service.calculate()
                    
                    # Obtener archivo de comprobante de pago
                    payment_proof = request.FILES.get('payment_proof') if hasattr(request, 'FILES') else None
                    
                    # Crear transacción de pago
                    payment_transaction = PaymentTransaction.objects.create(
                        amount=Decimal(str(validated_data['total_paid'])),
                        subtotal=payment_details['subtotal'],
                        total_discount=payment_details['total_discount'],
                        subscription_fee=payment_details['subtotal'],  # Total de subscription fees
                        early_payment_discount=payment_details['early_payment_discount'],
                        second_category_discount=payment_details['second_category_discount'],
                        payment_method=validated_data['payment_method'],
                        payment_proof=payment_proof,
                        status=PaymentStatus.PENDING
                    )
                    
                    # Asociar involvements a la transacción
                    payment_transaction.involvements.set(created_involvements)
                    
                    # Crear items detallados para cada involvement
                    from apps.payments.models import PaymentTransactionItem
                    from apps.payments.services import PaymentCalculationService
                    
                    previous_count = 0
                    for involvement in created_involvements:
                        # Calcular detalles de pago para este involvement específico
                        item_calculation = PaymentCalculationService(
                            tournament=involvement.tournament,
                            division=involvement.division,
                            player=involvement.player
                        )
                        item_details = item_calculation.get_payment_details()
                        
                        # Calcular descuento de segunda categoría considerando involvements previos
                        # La lógica debe coincidir con BulkPaymentCalculationService
                        second_category_discount = Decimal('0.00')
                        payment_config = involvement.division.get_active_payment_config()
                        if payment_config and payment_config.second_category_discount_amount:
                            # Contar involvements aprobados previos en el mismo torneo
                            approved_involvements = Involvement.objects.filter(
                                tournament=involvement.tournament,
                                player=involvement.player,
                                status=InvolvementStatus.APPROVED
                            ).exclude(division=involvement.division).count()
                            
                            # Si hay involvements aprobados previos O este no es el primero en la transacción
                            if approved_involvements >= 1 or previous_count > 0:
                                second_category_discount = payment_config.second_category_discount_amount
                        
                        # Calcular total del item
                        item_total = (
                            Decimal(str(item_details['subscription_fee'])) -
                            Decimal(str(item_details['early_payment_discount'])) -
                            second_category_discount
                        )
                        item_total = max(item_total, Decimal('0.00'))
                        
                        # Crear item de transacción
                        PaymentTransactionItem.objects.create(
                            transaction=payment_transaction,
                            involvement=involvement,
                            division_name=involvement.division.name,
                            subscription_fee=Decimal(str(item_details['subscription_fee'])),
                            early_payment_discount=Decimal(str(item_details['early_payment_discount'])),
                            second_category_discount=second_category_discount,
                            item_total=item_total
                        )
                        
                        previous_count += 1
                
                # Preparar respuesta
                profile_serializer = PlayerProfileSerializer(profile)
                from apps.tournaments.serializers import InvolvementSerializer
                involvements_serializer = InvolvementSerializer(created_involvements, many=True)
                
                response_data = {
                    'profile': profile_serializer.data,
                    'involvements': involvements_serializer.data,
                    'consent': {
                        'id': consent.id,
                        'accepted_privacy_policy': consent.accepted_privacy_policy,
                        'privacy_policy_version': consent.privacy_policy_version,
                        'accepted_terms': consent.accepted_terms,
                        'terms_version': consent.terms_version,
                        'consent_accepted_at': consent.consent_accepted_at.isoformat(),
                        'terms_accepted_at': consent.terms_accepted_at.isoformat(),
                    },
                }
                
                # Agregar información de pago si se creó la transacción
                if payment_transaction:
                    from apps.payments.serializers import PaymentTransactionSerializer
                    payment_serializer = PaymentTransactionSerializer(
                        payment_transaction,
                        context={'request': request}
                    )
                    response_data['payment_transaction'] = payment_serializer.data
                
                return self.created_response(
                    data=response_data,
                    message="Player subscription completed successfully"
                )
        
        except Exception as e:
            return self.error_response(
                message=f"Error completing subscription: {str(e)}",
                error_code="SUBSCRIPTION_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

