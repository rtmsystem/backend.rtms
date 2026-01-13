"""
Player Profile models for managing player information.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Gender(models.TextChoices):
    """Gender choices."""
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'


class DocumentType(models.TextChoices):
    """Document type choices."""
    DNI = 'dni', 'DNI'
    PASSPORT = 'passport', 'Passport'
    DRIVER_LICENSE = 'driver_license', 'Driver License'
    OTHER = 'other', 'Other'


class Handedness(models.TextChoices):
    """Handedness choices."""
    LEFT_HANDED = 'left_handed', 'Left-Handed'
    RIGHT_HANDED = 'right_handed', 'Right-Handed'
    AMBIDEXTROUS = 'ambidextrous', 'Ambidextrous'


class PlayerProfile(models.Model):
    """
    Player profile with detailed information.
    OneToOne relationship with User (optional).
    A PlayerProfile can exist without an associated User.
    """
    # Relación con User (OneToOne) - Opcional
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='player_profile',
        verbose_name='User',
        null=True,
        blank=True
    )
    
    # 👤 Personal Information
    first_name = models.CharField(
        max_length=150,
        verbose_name='First Name'
    )
    
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Middle Name'
    )
    
    last_name = models.CharField(
        max_length=150,
        verbose_name='Last Name'
    )
    
    short_bio = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Short Bio'
    )
    
    long_description = models.TextField(
        blank=True,
        verbose_name='Long Description'
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date of Birth'
    )
    
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
        null=True,
        verbose_name='Gender'
    )
    
    nationality = models.ForeignKey(
        'geographical.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Nationality'
    )
    
    # Avatar
    avatar = models.ImageField(
        upload_to='player_avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar',
        help_text='Player profile image'
    )
    
    # 🌐 Social Links
    instagram_url = models.URLField(
        max_length=255,
        blank=True,
        verbose_name='Instagram URL'
    )
    
    facebook_url = models.URLField(
        max_length=255,
        blank=True,
        verbose_name='Facebook URL'
    )
    
    linkedin_url = models.URLField(
        max_length=255,
        blank=True,
        verbose_name='LinkedIn URL'
    )
    
    # 📞 Contact Information
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Must match user email'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Phone Number'
    )
    
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        blank=True,
        verbose_name='Document Type'
    )
    
    document_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Document Number'
    )
    
    # 🏠 Current Address
    street_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Street / Door Number'
    )
    
    street_location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Street / Location'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='City'
    )
    
    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='State'
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Country'
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='PIN / Postal Code'
    )
    
    # 💪 Physical Information
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Height (cm)'
    )
    
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Weight (kg)'
    )
    
    handedness = models.CharField(
        max_length=20,
        choices=Handedness.choices,
        blank=True,
        verbose_name='Handedness'
    )
    
    # 🚨 Emergency Contact
    emergency_contact_first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Emergency Contact First Name'
    )
    
    emergency_contact_last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Emergency Contact Last Name'
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Emergency Contact Phone'
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Emergency Contact Relationship'
    )
    
    # 🏥 Medical Information
    health_insurance = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Health Insurance'
    )

    shirt_size = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Shirt Size'
    )
    
    blood_type = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name='Blood Type'
    )
    
    medical_conditions = models.TextField(
        blank=True,
        null=True,
        verbose_name='Medical Conditions',
        help_text='Allergies, chronic conditions, etc.'
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
        verbose_name = 'Player Profile'
        verbose_name_plural = 'Player Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self) -> str:
        if self.user:
            return f"{self.first_name} {self.last_name} - {self.user.email}"
        return f"{self.first_name} {self.last_name} - {self.email}"
    
    @property
    def full_name(self) -> str:
        """Returns full name."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self) -> str:
        """Returns formatted full address."""
        parts = [
            self.street_number,
            self.street_location,
            self.city,
            self.state,
            self.country,
            self.postal_code
        ]
        return ', '.join(filter(None, parts))
    
    @property
    def emergency_contact_full_name(self) -> str:
        """Returns emergency contact full name."""
        return f"{self.emergency_contact_first_name} {self.emergency_contact_last_name}".strip()
    
    def clean(self):
        """Validate that email matches user email if user exists."""
        from django.core.exceptions import ValidationError
        
        if self.user and self.email != self.user.email:
            raise ValidationError({
                'email': 'Email must match user email.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to validate email."""
        self.full_clean()
        super().save(*args, **kwargs)


class PlayerConsent(models.Model):
    """
    Player consent for privacy policy and terms of service.
    """
    profile = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='consents',
        verbose_name='Profile'
    )
    
    accepted_privacy_policy = models.BooleanField(
        default=False,
        verbose_name='Accepted Privacy Policy'
    )
    
    privacy_policy_version = models.CharField(
        max_length=20,
        verbose_name='Privacy Policy Version'
    )
    
    accepted_terms = models.BooleanField(
        default=False,
        verbose_name='Accepted Terms'
    )
    
    terms_version = models.CharField(
        max_length=20,
        verbose_name='Terms Version'
    )
    
    consent_accepted_at = models.DateTimeField(
        verbose_name='Consent Accepted At'
    )
    
    terms_accepted_at = models.DateTimeField(
        verbose_name='Terms Accepted At'
    )
    
    consent_ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Consent IP Address'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Player Consent'
        verbose_name_plural = 'Player Consents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['consent_accepted_at']),
        ]
    
    def __str__(self) -> str:
        return f"Consent for {self.profile.full_name} - {self.consent_accepted_at}"

