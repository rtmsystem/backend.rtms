"""
Serializers for PlayerProfile model.
"""
from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Gender, PlayerProfile


class PlayerProfileSerializer(serializers.ModelSerializer):
    """
    Complete serializer for PlayerProfile.
    Used to show data (GET).
    """
    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    emergency_contact_full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = PlayerProfile
        fields = [
            'id',
            'user',
            # Personal Information
            'first_name',
            'middle_name',
            'last_name',
            'full_name',
            'short_bio',
            'long_description',
            'date_of_birth',
            'gender',
            'nationality',
            'avatar',
            # Social Links
            'instagram_url',
            'facebook_url',
            'linkedin_url',
            # Contact Information
            'email',
            'phone',
            'document_type',
            'document_number',
            # Current Address
            'street_number',
            'street_location',
            'city',
            'state',
            'country',
            'postal_code',
            'full_address',
            # Physical Information
            'height_cm',
            'weight_kg',
            'handedness',
            # Emergency Contact
            'emergency_contact_first_name',
            'emergency_contact_last_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            # Emergency Contact
            'emergency_contact_first_name',
            'emergency_contact_last_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'emergency_contact_full_name',
            # Medical Information
            'health_insurance',
            'blood_type',
            'medical_conditions',
            # Timestamps
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlayerProfileCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to create PlayerProfile.
    User is taken from request.user.
    """
    
    class Meta:
        model = PlayerProfile
        fields = [
            # Required fields
            'first_name',
            'last_name',
            'gender',
            'nationality',
            'email',
            # Optional fields
            'middle_name',
            'short_bio',
            'long_description',
            'date_of_birth',
            'avatar',
            'instagram_url',
            'facebook_url',
            'linkedin_url',
            'phone',
            'document_type',
            'document_number',
            'street_number',
            'street_location',
            'city',
            'state',
            'country',
            'postal_code',
            'height_cm',
            'weight_kg',
            'handedness',
            'emergency_contact_first_name',
            'emergency_contact_last_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'health_insurance',
            'blood_type',
            'medical_conditions'
        ]
    
    def validate_email(self, value):
        """Validate that email matches user email if authenticated."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            from django.contrib.auth.models import AnonymousUser
            user = request.user
            if user is not None and not isinstance(user, AnonymousUser) and user.is_authenticated:
                if value != user.email:
                    raise serializers.ValidationError(
                        'Email must match your user email.'
                    )
        return value
    
    def validate(self, attrs):
        """Validate that user does not already have a profile if authenticated."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            from django.contrib.auth.models import AnonymousUser
            user = request.user
            if user is not None and not isinstance(user, AnonymousUser) and user.is_authenticated:
                if hasattr(user, 'player_profile'):
                    raise serializers.ValidationError(
                        'You already have a player profile.'
                    )
        
        return attrs
    
    def create(self, validated_data):
        """
        Create player profile. Associate with user if authenticated.
        """
        request = self.context.get('request')
        user = None
        
        if request and hasattr(request, 'user'):
            from django.contrib.auth.models import AnonymousUser
            user = request.user
            if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
                user = None
        
        # Create profile (with or without user)
        player_profile = PlayerProfile.objects.create(
            user=user,
            **validated_data
        )
        
        return player_profile


class PlayerProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer to update PlayerProfile.
    Does not allow changing user.
    """
    
    class Meta:
        model = PlayerProfile
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'short_bio',
            'long_description',
            'date_of_birth',
            'gender',
            'nationality',
            'avatar',
            'instagram_url',
            'facebook_url',
            'linkedin_url',
            'email',
            'phone',
            'document_type',
            'document_number',
            'street_number',
            'street_location',
            'city',
            'state',
            'country',
            'postal_code',
            'height_cm',
            'weight_kg',
            'handedness',
            'emergency_contact_first_name',
            'emergency_contact_last_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'health_insurance',
            'blood_type',
            'medical_conditions'
        ]
    
    def validate_email(self, value):
        """Validate that email matches user email if it exists."""
        if self.instance.user and value != self.instance.user.email:
            raise serializers.ValidationError(
                'Email must match your user email.'
            )
        return value


class InvolvementSubscriptionSerializer(serializers.Serializer):
    """Serializer for involvements in subscription."""
    division_id = serializers.IntegerField()
    partner_first_name = serializers.CharField(required=False, allow_blank=True)
    partner_last_name = serializers.CharField(required=False, allow_blank=True)
    partner_email = serializers.CharField(required=False, allow_blank=True)  # CharField to handle "undefined"
    is_doubles = serializers.BooleanField()
    
    def validate_partner_email(self, value):
        """Validate and clean partner_email."""
        if not value or value.strip().lower() in ['undefined', 'null', '']:
            return ''
        # Validate email format if it has value
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(value)
            return value.strip().lower()
        except ValidationError:
            raise serializers.ValidationError("Invalid email format for partner.")


class InvolvementsField(serializers.Field):
    """
    Custom field to handle involvements that may come as JSON string
    in multipart/form-data or as a list directly.
    """
    def to_internal_value(self, data):
        import json
        
        # If list (can come from QueryDict), take first item if string
        if isinstance(data, list):
            if len(data) == 0:
                raise serializers.ValidationError("Involvements cannot be empty.")
            # If first element is string, parse it
            if isinstance(data[0], str):
                data = data[0]
            else:
                # If already a list of dicts, return it directly
                return data
        
        # If string, parse it
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return parsed
                else:
                    raise serializers.ValidationError("Involvements must be a list/array.")
            except json.JSONDecodeError as e:
                raise serializers.ValidationError(f"Invalid JSON format: {str(e)}")
        
        # Si ya es una lista de diccionarios, retornarla
        if isinstance(data, list):
            return data
        
        raise serializers.ValidationError("Involvements must be a list or valid JSON string.")
    
    def to_representation(self, value):
        return value


class PlayerSubscriptionSerializer(serializers.Serializer):
    """
    Serializer to complete full player subscription.
    Includes profile, involvements and consent.
    """
    # Profile fields
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    gender = serializers.ChoiceField(choices=Gender.choices)
    second_last_name = serializers.CharField(required=False, allow_blank=True)
    nationality_id = serializers.IntegerField()
    email = serializers.EmailField()
    middle_name = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateTimeField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    handedness = serializers.CharField(required=False, allow_blank=True)  # Accepts 'left', 'right', 'left_handed', etc.
    shirt_size = serializers.CharField(required=False, allow_blank=True)  # Not used in model, but accepted
    emergency_contact_first_name = serializers.CharField(required=False, allow_blank=True)
    emergency_contact_last_name = serializers.CharField(required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(required=False, allow_blank=True)

    emergency_contact_relationship = serializers.CharField(required=False, allow_blank=True)
    
    # Medical Information
    health_insurance = serializers.CharField(required=False, allow_blank=True)
    blood_type = serializers.CharField(required=False, allow_blank=True)
    medical_conditions = serializers.CharField(required=False, allow_blank=True)
    
    # Involvements - custom field that handles JSON string or list
    involvements = InvolvementsField()
    
    # Consent
    privacy_policy_accepted = serializers.BooleanField()
    terms_conditions_accepted = serializers.BooleanField()
    
    # Avatar (optional, can be file or URL)
    avatar = serializers.ImageField(required=False, allow_null=True)
    
    # Payment fields (optional)
    payment_proof = serializers.FileField(required=False, allow_null=True)
    total_paid = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text='Total amount paid'
    )
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text='Subtotal before discounts'
    )
    total_discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text='Total discount applied'
    )
    payment_method = serializers.ChoiceField(
        choices=[],  # Will be set in __init__
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='Payment method'
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize serializer and set payment method choices."""
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from apps.payments.models import PaymentMethod
        self.fields['payment_method'].choices = PaymentMethod.choices
    
    def to_internal_value(self, data):
        """
        Override to handle 'null' string in payment_method.
        Frontend might send 'null' as string for empty values.
        """
        # Create a mutable copy if necessary
        if hasattr(data, 'copy'):
            data = data.copy()
        
        # Handle payment_method 'null' string
        if 'payment_method' in data and data.get('payment_method') == 'null':
            data['payment_method'] = None
            
        return super().to_internal_value(data)
    
    def validate_email(self, value):
        """Validate email. If user authenticated, must match."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            from django.contrib.auth.models import AnonymousUser
            if (
                request.user is not None and
                not isinstance(request.user, AnonymousUser) and
                request.user.is_authenticated
            ):
                user_email = getattr(request.user, 'email', '')
                if user_email and value != user_email:
                    raise serializers.ValidationError(
                        'Email must match your user email.'
                    )
        return value
    
    def validate_involvements(self, value):
        """Validate involvements."""
        if not value or not isinstance(value, list):
            raise serializers.ValidationError("At least one involvement is required.")
        
        if len(value) == 0:
            raise serializers.ValidationError("At least one involvement is required.")
        
        # Validate each involvement using serializer
        validated_involvements = []
        for inv in value:
            serializer = InvolvementSubscriptionSerializer(data=inv)
            if not serializer.is_valid():
                raise serializers.ValidationError(serializer.errors)
            
            validated_data = serializer.validated_data
            # Validate business rules
            # if validated_data.get('is_doubles') and not validated_data.get('partner_email'):
            #     raise serializers.ValidationError(
            #         "Partner email is required for doubles involvements."
            #     )

            # if  validated_data.get('is_doubles') and not validated_data.get('partner_name'):
            #     raise serializers.ValidationError(
            #         "Partner name is required for doubles involvements."
            #     )
            validated_involvements.append(validated_data)
        
        return validated_involvements

    
    def validate(self, attrs):
        """Additional validations."""
        if not attrs.get('privacy_policy_accepted'):
            raise serializers.ValidationError({
                'privacy_policy_accepted': 'You must accept the privacy policy.'
            })
        
        if not attrs.get('terms_conditions_accepted'):
            raise serializers.ValidationError({
                'terms_conditions_accepted': 'You must accept the terms and conditions.'
            })

        # payment_method y total_paid solo son requeridos cuando alguna división acepta pagos
        from apps.tournaments.models import TournamentDivision

        involvements = attrs.get('involvements') or []
        any_division_has_payment = False
        for inv in involvements:
            division_id = inv.get('division_id')
            if not division_id:
                continue
            try:
                division = TournamentDivision.objects.get(id=division_id)
                if division.has_payment_subscription:
                    any_division_has_payment = True
                    break
            except TournamentDivision.DoesNotExist:
                continue

        if any_division_has_payment:
            total_paid = attrs.get('total_paid')
            payment_method = attrs.get('payment_method')
            if total_paid is None:
                raise serializers.ValidationError({
                    'total_paid': 'Total paid is required when the division accepts payments.'
                })
            if not payment_method:
                raise serializers.ValidationError({
                    'payment_method': 'Payment method is required when the division accepts payments.'
                })
        
        return attrs

