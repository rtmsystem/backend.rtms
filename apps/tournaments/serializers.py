"""
Serializers for tournaments app.
"""
from rest_framework import serializers
from django.utils import timezone

from .models import (
    Tournament, TournamentDivision, Involvement,
    TournamentFormat, GenderType, ParticipantType, TournamentStatus, InvolvementStatus,
    TournamentGroup, GroupStanding
)
from apps.users.models import User
from apps.players.models import PlayerProfile
from apps.payments.serializers import PaymentSerializer


class TournamentDivisionSerializer(serializers.ModelSerializer):
    """Serializer for TournamentDivision model."""
    
    participant_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    subscription_fee = serializers.SerializerMethodField()
    early_payment_discount_amount = serializers.SerializerMethodField()
    early_payment_discount_deadline = serializers.SerializerMethodField()
    second_category_discount_amount = serializers.SerializerMethodField()
    has_payment_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = TournamentDivision
        fields = [
            'id', 'name', 'description', 'format', 'max_participants',
            'gender', 'participant_type', 'born_after', 'is_active','is_published',
            'participant_count', 'is_full', 'spots_remaining',
            'subscription_fee', 'early_payment_discount_amount',
            'early_payment_discount_deadline', 'second_category_discount_amount',
            'has_payment_subscription',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subscription_fee(self, obj) -> float:
        """Get subscription fee if division has active payment (division or tournament level)."""
        payment = obj.get_active_payment_config()
        if payment:
            return float(payment.subscription_fee)
        return None
    
    def get_early_payment_discount_amount(self, obj) -> float:
        """Get early payment discount amount if division has active payment (division or tournament level)."""
        payment = obj.get_active_payment_config()
        if payment:
            return float(payment.early_payment_discount_amount)
        return None
    
    def get_early_payment_discount_deadline(self, obj):
        """Get early payment discount deadline if division has active payment (division or tournament level)."""
        payment = obj.get_active_payment_config()
        if payment and payment.early_payment_discount_deadline:
            return payment.early_payment_discount_deadline
        return None
    
    def get_second_category_discount_amount(self, obj) -> float:
        """Get second category discount amount if division has active payment (division or tournament level)."""
        payment = obj.get_active_payment_config()
        if payment:
            return float(payment.second_category_discount_amount)
        return None
    
    def get_has_payment_subscription(self, obj) -> bool:
        """Check if division has active payment subscription (division or tournament level)."""
        return obj.has_payment_subscription


class TournamentDivisionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TournamentDivision."""
    
    class Meta:
        model = TournamentDivision
        fields = [
            'id','name', 'description', 'format', 'max_participants',
            'gender', 'participant_type', 'born_after', 'is_active','is_published','published_at', 'published_by'
        ]
    
    def validate_max_participants(self, value):
        """Validate max_participants is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Maximum participants must be a positive integer.")
        return value


class TournamentSerializer(serializers.ModelSerializer):
    """Serializer for Tournament model."""
    
    divisions = TournamentDivisionSerializer(many=True, read_only=True)
    division_count = serializers.ReadOnlyField()
    is_registration_open = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_logo = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    
    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'description', 'contact_name', 'contact_phone',
            'contact_email', 'start_date', 'end_date', 'registration_deadline',
            'address', 'street_number', 'street_location', 'city', 'state',
            'country', 'postal_code', 'organization', 'organization_name', 'organization_logo',
            'status', 'is_active', 'division_count', 'is_registration_open',
            'is_upcoming', 'is_ongoing', 'divisions', 'created_by_name',
            'created_at', 'updated_at','logo', 'banner', 'payment',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_organization_logo(self, obj):
        """Get organization logo URL safely."""
        if obj.organization and obj.organization.logo:
            try:
                return obj.organization.logo.url
            except ValueError:
                return None
        return None
    
    def get_logo(self, obj):
        """Get tournament logo URL safely."""
        if obj.logo:
            try:
                return obj.logo.url
            except ValueError:
                return None
        return None
    
    def get_banner(self, obj):
        """Get tournament banner URL safely."""
        if obj.banner:
            try:
                return obj.banner.url
            except ValueError:
                return None
        return None
    
    def get_payment(self, obj):
        """Get payment information when scope is tournament."""
        try:
            # Acceder al payment - puede lanzar RelatedObjectDoesNotExist si no existe
            payment = obj.payment
            if payment and payment.payment_scope == 'tournament':
                return PaymentSerializer(payment, context=self.context).data
        except (AttributeError, Exception):
            # Si no existe el payment o hay cualquier error, retornar None
            # Django lanza RelatedObjectDoesNotExist para OneToOneField cuando no existe
            pass
        return None
    
    def validate(self, data):
        """Validate tournament data."""
        # Validate dates
        if 'registration_deadline' in data and 'start_date' in data:
            if data['registration_deadline'] > data['end_date']:
                raise serializers.ValidationError(
                    "Registration deadline must be before or equal to the end date."
                )
        
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after the start date."
                )
        
        return data
    
    def validate_contact_email(self, value):
        """Validate contact email format."""
        if not value:
            raise serializers.ValidationError("Contact email is required.")
        return value


class TournamentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Tournament."""
    
    divisions = TournamentDivisionCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'description', 'contact_name', 'contact_phone',
            'contact_email', 'start_date', 'end_date', 'registration_deadline',
            'address', 'street_number', 'street_location', 'city', 'state',
            'country', 'postal_code', 'status', 'is_active', 'divisions', 'logo', 'banner'
        ]
    
    def validate(self, data):
        """Validate tournament data."""
        print("validate() - data keys:", data.keys())
        print("validate() - divisions en data:", 'divisions' in data)
        if 'divisions' in data:
            print("validate() - divisions value:", data.get('divisions'))
            print("validate() - divisions type:", type(data.get('divisions')))
        
        # Validate dates
        if data['registration_deadline'] > data['end_date']:
            raise serializers.ValidationError(
                "Registration deadline must be before or equal to the end date."
            )
        
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                "End date must be after the start date."
            )
        
        return data
    
    def create(self, validated_data):
        """Create tournament with divisions."""
       
        # Verificar si divisions está en validated_data, si no, buscar en initial_data
        if 'divisions' not in validated_data:
            initial_data = self.initial_data
            if 'divisions' in initial_data:
                # Si divisions está en initial_data pero no en validated_data,
                # significa que no pasó la validación o está vacío
                divisions_data = initial_data.get('divisions', [])
                # Intentar validar manualmente
                if divisions_data:
                    division_serializer = TournamentDivisionCreateSerializer(data=divisions_data, many=True)
                    if division_serializer.is_valid():
                        divisions_data = division_serializer.validated_data
                    else:
                        divisions_data = []
                else:
                    divisions_data = []
            else:
                divisions_data = []
        else:
            divisions_data = validated_data.pop('divisions', [])

        
        # Obtener organization_id y created_by del contexto
        organization_id = self.context.get('organization_id')
        created_by = self.context.get('request').user if self.context.get('request') else None
        
        if organization_id:
            validated_data['organization_id'] = organization_id
        
        if created_by:
            validated_data['created_by'] = created_by
        
        tournament = Tournament.objects.create(**validated_data)
        
        for division_data in divisions_data:
            TournamentDivision.objects.create(tournament=tournament, **division_data)
        
        return tournament


class TournamentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Tournament."""
    
    divisions = TournamentDivisionCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Tournament
        fields = [
            'name', 'description', 'contact_name', 'contact_phone','logo', 'banner',
            'contact_email', 'start_date', 'end_date', 'registration_deadline',
            'address', 'street_number', 'street_location', 'city', 'state',
            'country', 'postal_code', 'status', 'is_active', 'divisions'
        ]
    
    def validate(self, data):
        """Validate tournament data."""
        # Validate dates
        if 'registration_deadline' in data and 'start_date' in data:
            if data['registration_deadline'] > data['end_date']:
                raise serializers.ValidationError(
                    "Registration deadline must be before or equal to the end date."
                )
        
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after the start date."
                )
        
        return data
    
    def update(self, instance, validated_data):
        """Update tournament and handle divisions."""
        divisions_data = validated_data.pop('divisions', None)
        
        # Update tournament fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle divisions if provided
        if divisions_data is not None:
            # Clear existing divisions
            instance.divisions.all().delete()
            
            # Create new divisions
            for division_data in divisions_data:
                TournamentDivision.objects.create(tournament=instance, **division_data)
        
        return instance


class TournamentListSerializer(serializers.ModelSerializer):
    """Serializer for Tournament list view."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_logo = serializers.SerializerMethodField()
    division_count = serializers.ReadOnlyField()
    is_registration_open = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    
    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'organization_name', 'organization_logo', 'status', 'start_date','logo', 'banner', 'registration_deadline',
            'end_date', 'city', 'country', 'division_count',
            'is_registration_open', 'is_upcoming', 'is_ongoing',
            'is_active', 'created_at'
        ]
    
    def get_organization_logo(self, obj):
        """Get organization logo URL safely."""
        if obj.organization and obj.organization.logo:
            try:
                return obj.organization.logo.url
            except ValueError:
                return None
        return None
    
    def get_logo(self, obj):
        """Get tournament logo URL safely."""
        if obj.logo:
            try:
                return obj.logo.url
            except ValueError:
                return None
        return None
    
    def get_banner(self, obj):
        """Get tournament banner URL safely."""
        if obj.banner:
            try:
                return obj.banner.url
            except ValueError:
                return None
        return None


# Choice serializers for API documentation
class TournamentFormatSerializer(serializers.Serializer):
    """Serializer for tournament format choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class GenderTypeSerializer(serializers.Serializer):
    """Serializer for gender type choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class ParticipantTypeSerializer(serializers.Serializer):
    """Serializer for participant type choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class TournamentStatusSerializer(serializers.Serializer):
    """Serializer for tournament status choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class InvolvementSerializer(serializers.ModelSerializer):
    """Serializer for Involvement model."""

    player_email = serializers.CharField(source='player.email', read_only=True)
    partner_first_name = serializers.CharField(source='partner.first_name', read_only=True)
    partner_last_name = serializers.CharField(source='partner.last_name', read_only=True)
    partner_email = serializers.CharField(source='partner.email', read_only=True)
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    division_id = serializers.IntegerField(source='division.id', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)

    is_approved = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()
    is_rejected = serializers.ReadOnlyField()
    knockout_points = serializers.ReadOnlyField()

    class Meta:
        model = Involvement
        fields = [
            'id', 'tournament', 'player', 'partner', 'division',
            'status', 'paid', 'knockout_points', 'tournament_name',
            'player_email', 'partner_first_name', 'partner_last_name', 'partner_email',
            'division_id', 'division_name',
            'approved_by_name', 'is_approved', 'is_pending', 'is_rejected',
            'created_at', 'updated_at', 'approved_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_at', 'knockout_points']


class InvolvementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Involvement."""
    
    class Meta:
        model = Involvement
        fields = ['tournament', 'player', 'partner', 'division', 'status', 'paid']
        read_only_fields = ['tournament', 'player']
    
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
    
    def validate(self, data):
        """Validate involvement data."""
        request = self.context.get('request')
        view = self.context.get('view')
        tournament_id = view.kwargs.get('tournament_id')
        tournament = Tournament.objects.get(id=tournament_id)

        division = data.get('division')
        partner = data.get('partner')
        player = data.get('player')

        # Resolve player if not provided
        if not player:
            try:
                player = PlayerProfile.objects.get(user=request.user)
                data['player'] = player
            except PlayerProfile.DoesNotExist:
                raise serializers.ValidationError(
                    "You must have a player profile to register for tournaments."
                )

        if division and division.participant_type == ParticipantType.DOUBLES:
            if not partner:
                raise serializers.ValidationError("Partner is required for doubles tournaments.")
            
            if player == partner:
                raise serializers.ValidationError("Player and partner must be different.")
            
            # Check if partner is already registered in this division
            if Involvement.objects.filter(
                tournament=tournament, division=division, player=partner
            ).exists():
                raise serializers.ValidationError("Partner is already registered in this division.")

            # Check if partner is already a partner in this division
            if Involvement.objects.filter(
                tournament=tournament, division=division, partner=partner
            ).exists():
                 raise serializers.ValidationError("This player is already registered as a partner in this division.")

            # Check if current user (player) is already a partner in this division
            if Involvement.objects.filter(
                tournament=tournament, division=division, partner=player
            ).exists():
                 raise serializers.ValidationError("You are already registered as a partner in this division.")
        
        if division and division.participant_type == ParticipantType.SINGLE:
            if partner:
                 raise serializers.ValidationError("Singles division cannot have a partner.")

        # Check for duplicate involvement for player (uniqueness constraint handles it, but good to check)
        if Involvement.objects.filter(
            tournament=tournament, division=division, player=player
        ).exists():
             raise serializers.ValidationError("An involvement for this player in this division already exists.")

        return data


class InvolvementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Involvement."""
    
    class Meta:
        model = Involvement
        fields = ['status', 'paid']


class InvolvementListSerializer(serializers.ModelSerializer):
    """Serializer for Involvement list view."""

    # player_name = serializers.CharField(source='player.full_name', read_only=True)
    player_first_name = serializers.CharField(source='player.first_name', read_only=True)
    player_last_name = serializers.CharField(source='player.last_name', read_only=True)
    player_email = serializers.CharField(source='player.email', read_only=True)
    player_avatar = serializers.SerializerMethodField()
    partner_first_name = serializers.CharField(source='partner.first_name', read_only=True)
    partner_last_name = serializers.CharField(source='partner.last_name', read_only=True)
    partner_email = serializers.CharField(source='partner.email', read_only=True)
    partner_avatar = serializers.SerializerMethodField()
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)
    division_id = serializers.IntegerField(source='division.id', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    participant_type = serializers.CharField(source='division.participant_type', read_only=True)
    team_name = serializers.SerializerMethodField()
    knockout_points = serializers.ReadOnlyField()

    class Meta:
        model = Involvement
        fields = [
            'id', 'tournament', 'player', 'partner', 'division',
            'status', 'paid', 'knockout_points', 'tournament_name',
            'player_first_name', 'player_last_name', 'player_email', 'player_avatar',
            'partner_first_name', 'partner_last_name', 'partner_email', 'partner_avatar',
            'division_id', 'division_name', 'participant_type', 'team_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_player_avatar(self, obj):
        """Get player avatar URL safely."""
        if obj.player and obj.player.avatar:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.player.avatar.url)
                return obj.player.avatar.url
            except ValueError:
                return None
        return None
    
    def get_partner_avatar(self, obj):
        """Get partner avatar URL safely."""
        if obj.partner and obj.partner.avatar:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.partner.avatar.url)
                return obj.partner.avatar.url
            except ValueError:
                return None
        return None
    
    def get_team_name(self, obj):
        """Get team name for display."""
        if obj.partner:
            return f"{obj.player.full_name} / {obj.partner.full_name}"
        return obj.player.full_name


class InvolvementStatusSerializer(serializers.Serializer):
    """Serializer for involvement status choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class ApprovedPlayerListSerializer(serializers.ModelSerializer):
    """Serializer para lista de jugadores aprobados en involvements."""
    
    player_first_name = serializers.SerializerMethodField()
    player_last_name = serializers.SerializerMethodField()
    player_avatar = serializers.SerializerMethodField()
    nationality_name = serializers.SerializerMethodField()
    nationality_flag = serializers.SerializerMethodField()
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    handedness = serializers.CharField(read_only=True)
    knockout_points = serializers.SerializerMethodField()
    division_id = serializers.SerializerMethodField()
    
    class Meta:
        model = PlayerProfile
        fields = [
            'id',
            'player_first_name',
            'player_last_name',
            'player_avatar',
            'nationality_name',
            'nationality_flag',
            'height_cm',
            'handedness',
            'knockout_points',
            'division_id'
        ]
        read_only_fields = ['id']
    
    def get_player_avatar(self, obj):
        """Get player avatar URL safely."""
        if obj.avatar:
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.avatar.url)
                return obj.avatar.url
            except ValueError:
                return None
        return None
    
    def get_nationality_name(self, obj):
        """Get nationality name safely."""
        if obj.nationality:
            return obj.nationality.name
        return None
    
    def get_nationality_flag(self, obj):
        """Get nationality flag safely."""
        if obj.nationality:
            return obj.nationality.flag
        return None

    def get_player_first_name(self, obj):
        """Get player first name safely."""
        if obj.first_name:
            return obj.first_name
        return None

    def get_player_last_name(self, obj):
        """Get player last name safely."""
        if obj.last_name:
            return obj.last_name
        return None

    def get_knockout_points(self, obj):
        """Get knockout points safely."""
        return getattr(obj, 'knockout_points', None)

    def get_division_id(self, obj):
        """Get division id safely."""
        return getattr(obj, 'division_id', None)

class GroupStandingSerializer(serializers.ModelSerializer):
    """Serializer for GroupStanding model."""
    
    player_name = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    sets_difference = serializers.ReadOnlyField()
    
    class Meta:
        model = GroupStanding
        fields = [
            'id', 'group', 'involvement',
            'matches_played', 'matches_won', 'matches_lost',
            'sets_won', 'sets_lost', 'sets_difference',
            'points', 'position_in_group', 'global_position',
            'player_name', 'partner_name', 'team_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'matches_played', 'matches_won', 'matches_lost',
            'sets_won', 'sets_lost', 'points',
            'position_in_group', 'global_position',
            'created_at', 'updated_at'
        ]
    
    def get_player_name(self, obj):
        """Get player name."""
        if obj.involvement and obj.involvement.player:
            return obj.involvement.player.full_name
        return None
    
    def get_partner_name(self, obj):
        """Get partner name if exists."""
        if obj.involvement and obj.involvement.partner:
            return obj.involvement.partner.full_name
        return None
    
    def get_team_name(self, obj):
        """Get team name for display."""
        if obj.involvement:
            if obj.involvement.partner:
                return f"{obj.involvement.player.full_name} / {obj.involvement.partner.full_name}"
            return obj.involvement.player.full_name
        return None


class TournamentGroupSerializer(serializers.ModelSerializer):
    """Serializer for TournamentGroup model."""
    
    participant_count = serializers.ReadOnlyField()
    standings = GroupStandingSerializer(many=True, read_only=True)
    
    class Meta:
        model = TournamentGroup
        fields = [
            'id', 'division', 'name', 'group_number',
            'participant_count', 'standings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
