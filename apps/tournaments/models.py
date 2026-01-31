"""
Tournament models for managing sports tournaments and divisions.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from .exceptions import (
    DivisionInsufficientApprovedPlayersError,
    DivisionHasPendingInvolvementsError,
    DivisionAlreadyPublishedError
)

class TournamentFormat(models.TextChoices):
    """Tournament format choices."""
    KNOCKOUT = 'knockout', 'Single Elimination'
    DOUBLE_SLASH = 'double_slash', 'Double Elimination'
    ROUND_ROBIN = 'round_robin', 'Round Robin'
    ROUND_ROBIN_KNOCKOUT = 'round_robin_knockout', 'Round Robin + Knockout'


class GenderType(models.TextChoices):
    """Gender type choices."""
    ANY = 'any', 'Any'
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'


class ParticipantType(models.TextChoices):
    """Participant type choices."""
    SINGLE = 'single', 'Single'
    DOUBLES = 'doubles', 'Doubles'


class InvolvementStatus(models.TextChoices):
    """Involvement status choices."""
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class TournamentStatus(models.TextChoices):
    """Tournament status choices."""
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    # REGISTRATION_OPEN = 'registration_open', 'Registration Open'
    # REGISTRATION_CLOSED = 'registration_closed', 'Registration Closed'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Tournament(models.Model):
    """
    Model representing a sports tournament.
    """
    # Basic tournament information
    name = models.CharField(
        max_length=255,
        verbose_name='Tournament Name',
        help_text='Name of the tournament'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='About this Tournament',
        help_text='Detailed description of the tournament'
    )
    
    # Logo
    logo = models.ImageField(
        upload_to='tournament_logos/',
        blank=True,
        null=True,
        verbose_name='Tournament Logo',
        help_text='Tournament logo or representative image'
    )
    
    # Banner
    banner = models.ImageField(
        upload_to='tournament_banners/',
        blank=True,
        null=True,
        verbose_name='Tournament Banner',
        help_text='Tournament banner or promotional image'
    )
    
    # Contact information
    contact_name = models.CharField(
        max_length=255,
        verbose_name='Contact Name',
        help_text='Name of the contact person'
    )
    
    contact_phone = models.CharField(
        max_length=20,
        verbose_name='Contact Phone',
        help_text='Contact phone number'
    )
    
    contact_email = models.EmailField(
        verbose_name='Contact Email',
        help_text='Contact email address'
    )
    
    # Timeline
    start_date = models.DateTimeField(
        verbose_name='Start Date',
        help_text='Tournament start date and time'
    )
    
    end_date = models.DateTimeField(
        verbose_name='End Date',
        help_text='Tournament end date and time'
    )
    
    registration_deadline = models.DateTimeField(
        verbose_name='Registration Deadline',
        help_text='Last date to register for the tournament'
    )
    
    # Location information
    address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Address',
        help_text='Full address of the tournament location'
    )
    
    street_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Street/Door Number',
        help_text='Street or door number'
    )
    
    street_location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Street/Location',
        help_text='Street or location details'
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name='City',
        help_text='City where the tournament takes place'
    )
    
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='State',
        help_text='State or province'
    )
    
    country = models.CharField(
        max_length=100,
        verbose_name='Country',
        help_text='Country where the tournament takes place'
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Postal Code',
        help_text='Postal or ZIP code'
    )
    
    # Organization relationship
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='tournaments',
        verbose_name='Organization',
        help_text='Organization organizing this tournament'
    )
    
    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=TournamentStatus.choices,
        default=TournamentStatus.DRAFT,
        verbose_name='Status'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether the tournament is active'
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
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tournaments',
        verbose_name='Created By'
    )
    
    class Meta:
        verbose_name = 'Tournament'
        verbose_name_plural = 'Tournaments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"
    
    def clean(self):
        """Validate tournament data."""
        from django.core.exceptions import ValidationError
        
        # Validate dates
        if self.registration_deadline > self.end_date:
            raise ValidationError(
                'Registration deadline must be before or equal to the end date.'
            )
        
        if self.end_date <= self.start_date:
            raise ValidationError(
                'End date must be after the start date.'
            )
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def division_count(self) -> int:
        """Return the number of divisions in this tournament."""
        return self.divisions.count()
    
    @property
    def is_registration_open(self) -> bool:
        """Check if registration is currently open."""
        now = timezone.now()
        return (
            self.status == TournamentStatus.REGISTRATION_OPEN and
            now <= self.registration_deadline
        )
    
    @property
    def is_upcoming(self) -> bool:
        """Check if tournament is upcoming."""
        return self.start_date > timezone.now()
    
    @property
    def is_ongoing(self) -> bool:
        """Check if tournament is currently ongoing."""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def logo_url(self) -> str:
        """Return logo URL or default logo."""
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        # Default SVG image
        return '/static/images/default-tournament-logo.svg'


class TournamentDivision(models.Model):
    """
    Model representing a division within a tournament.
    """
    # Basic division information
    name = models.CharField(
        max_length=255,
        verbose_name='Event Name',
        help_text='Name of the division or event'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description',
        help_text='Description of the division'
    )
    
    # Tournament relationship
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='divisions',
        verbose_name='Tournament',
        help_text='Tournament this division belongs to'
    )
    
    # Division configuration
    format = models.CharField(
        max_length=20,
        choices=TournamentFormat.choices,
        verbose_name='Format',
        help_text='Tournament format for this division'
    )
    
    max_participants = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Maximum Participants',
        help_text='Maximum number of participants allowed'
    )
    
    gender = models.CharField(
        max_length=10,
        choices=GenderType.choices,
        default=GenderType.ANY,
        verbose_name='Gender',
        help_text='Gender restriction for participants'
    )
    
    participant_type = models.CharField(
        max_length=10,
        choices=ParticipantType.choices,
        verbose_name='Participant Type',
        help_text='Type of participants (individual or team)'
    )
    
    born_after = models.DateField(
        blank=True,
        null=True,
        verbose_name='Born After',
        help_text='Participants must be born after this date'
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether the division is active'
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name='Published',
        help_text='Whether the division is published'
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Published At',
        help_text='When the division was published'
    )

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_divisions',
        verbose_name='Published By',
        help_text='User who published this division'
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
        verbose_name = 'Tournament Division'
        verbose_name_plural = 'Tournament Divisions'
        ordering = ['tournament', 'name']
        indexes = [
            models.Index(fields=['tournament']),
            models.Index(fields=['format']),
            models.Index(fields=['participant_type']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['tournament', 'name']
    
    def __str__(self) -> str:
        return f"{self.name} ({self.tournament.name})"
    
    @property
    def participant_count(self) -> int:
        """Return the number of approved participants."""
        return self.involvements.filter(status=InvolvementStatus.APPROVED).count()
    
    @property
    def is_full(self) -> bool:
        """Check if the division is full."""
        if not self.max_participants:
            return False
        return self.participant_count >= self.max_participants
    
    def get_active_payment_config(self):
        """
        Get active payment configuration for this division.
        
        Returns Payment object if found (division or tournament level), None otherwise.
        Implements inheritance: division payment first, then tournament payment.
        """
        from apps.payments.models import Payment
        
        # First check if division has its own payment configuration
        division_payment = Payment.objects.filter(
            division=self,
            is_active=True
        ).first()
        
        if division_payment:
            return division_payment
        
        # If not, check if tournament has payment configuration
        tournament_payment = Payment.objects.filter(
            tournament=self.tournament,
            is_active=True
        ).first()
        
        return tournament_payment
    
    @property
    def has_payment_subscription(self) -> bool:
        """Check if division has active payment subscription (division or tournament level)."""
        return self.get_active_payment_config() is not None
    
    @property
    def spots_remaining(self) -> int:
        """Return the number of spots remaining."""
        if not self.max_participants:
            return None
        return max(0, self.max_participants - self.participant_count)

    @property
    def approved_count(self) -> int:
        """Return the number of approved participants."""
        return self.involvements.filter(status=InvolvementStatus.APPROVED).count()

    @property
    def has_pending_involvements(self) -> bool:
        """Check if there are any pending involvements."""
        return self.involvements.filter(status=InvolvementStatus.PENDING).exists()

    def publish(self, user=None):
        """Publish the division."""

        # Verificar si ya está publicada
        if self.is_published:
           raise DivisionAlreadyPublishedError()

        if self.approved_count < 2:
            raise DivisionInsufficientApprovedPlayersError(self.approved_count)

        if self.has_pending_involvements:
            pending_count = self.involvements.filter(
            status=InvolvementStatus.PENDING
        ).count()
            raise DivisionHasPendingInvolvementsError(pending_count)

        self.is_published = True
        self.published_at = timezone.now()
        if user:
            self.published_by = user
        self.save(update_fields=['is_published', 'published_at', 'published_by'])
    


class Involvement(models.Model):
    """
    Model representing a player's involvement in a tournament division.
    Tracks registration, approval status, and payment.
    """
    # Relations
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='involvements',
        verbose_name='Tournament',
        help_text='Tournament the player is involved in'
    )
    
    player = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='tournament_involvements',
        verbose_name='Player',
        help_text='Primary player involved in the tournament'
    )
    
    partner = models.ForeignKey(
        'players.PlayerProfile',
        on_delete=models.CASCADE,
        related_name='tournament_partnerships',
        verbose_name='Partner',
        help_text='Partner for doubles tournaments',
        null=True,
        blank=True
    )
    
    division = models.ForeignKey(
        TournamentDivision,
        on_delete=models.CASCADE,
        related_name='involvements',
        verbose_name='Division',
        help_text='Division the player is involved in'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=InvolvementStatus.choices,
        default=InvolvementStatus.PENDING,
        verbose_name='Status',
        help_text='Registration status'
    )

    # Payment
    paid = models.BooleanField(
        default=False,
        verbose_name='Paid',
        help_text='Whether the player has paid the registration fee'
    )

    # Knockout Points
    knockout_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Knockout Points',
        help_text='Points accumulated from knockout/bracket match wins'
    )

    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Registered At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Approved At',
        help_text='When the involvement was approved'
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_involvements',
        verbose_name='Approved By',
        help_text='User who approved this involvement'
    )
    
    class Meta:
        verbose_name = 'Involvement'
        verbose_name_plural = 'Involvements'
        ordering = ['-created_at']
        unique_together = [
            ('tournament', 'player', 'division'),
        ]
        indexes = [
            models.Index(fields=['tournament']),
            models.Index(fields=['player']),
            models.Index(fields=['partner']),
            models.Index(fields=['division']),
            models.Index(fields=['status']),
            models.Index(fields=['paid']),
            models.Index(fields=['-knockout_points']),
        ]
    
    def __str__(self) -> str:
        base = f"{self.player.full_name} - {self.tournament.name} - {self.division.name} ({self.status})"
        if self.partner:
            base = f"{self.player.full_name} / {self.partner.full_name} - {self.tournament.name} - {self.division.name} ({self.status})"
        return base
    
    def clean(self):
        """Validate involvement data."""
        # Verify division belongs to tournament
        if self.division.tournament_id != self.tournament_id:
            raise ValidationError(
                'Division must belong to the specified tournament.'
            )
        
        # Check division gender restrictions
        if self.division.gender != GenderType.ANY:
            # Player is now directly a PlayerProfile
            player_gender = self.player.gender
            
            # Map PlayerProfile gender to TournamentDivision gender
            gender_map = {
                'male': GenderType.MALE,
                'female': GenderType.FEMALE
            }
            
            if gender_map.get(player_gender) != self.division.gender:
                raise ValidationError(
                    f'Player gender ({player_gender}) does not match division gender requirement ({self.division.gender}).'
                )
        
        # Check if division is full
        if self.division.max_participants and self.division.max_participants > 0:
            approved_count = Involvement.objects.filter(
                division=self.division,
                status=InvolvementStatus.APPROVED
            ).count()
            
            # If already approved, don't count this involvement
            if self.status == InvolvementStatus.APPROVED and self.pk:
                approved_count = approved_count - 1
            
            if approved_count >= self.division.max_participants:
                raise ValidationError(
                    f'Division is full. Maximum {self.division.max_participants} participants allowed.'
                )

            if not self.pk and self.division.is_published:
                raise ValidationError(
                    'Registration for this division is closed. No new registrations are allowed.'
            )
        
        # Check age restrictions
        # if self.division.born_after:
        #     from apps.players.models import PlayerProfile
        #     try:
        #         player_profile = PlayerProfile.objects.get(user=self.player)
        #         if player_profile.date_of_birth:
        #             if player_profile.date_of_birth < self.division.born_after:
        #                 raise ValidationError(
        #                     f'Player must be born after {self.division.born_after}.'
        #                 )
        #     except PlayerProfile.DoesNotExist:
        #         raise ValidationError(
        #             'Player must have a profile with date of birth information.'
        #         )
        
        # Validate doubles tournaments requirements
        if self.division.participant_type == ParticipantType.DOUBLES:
            if not self.partner:
                raise ValidationError(
                    'Partner is required for doubles tournaments.'
                )
            
            if self.player_id == self.partner_id:
                raise ValidationError(
                    'Player and partner must be different.'
                )
            
            # Partner is now directly a PlayerProfile
            # Validate partner gender if division has gender restrictions
            if self.division.gender != GenderType.ANY:
                partner_gender = self.partner.gender
                
                # Map PlayerProfile gender to TournamentDivision gender
                gender_map = {
                    'male': GenderType.MALE,
                    'female': GenderType.FEMALE
                }
                
                if gender_map.get(partner_gender) != self.division.gender:
                    raise ValidationError(
                        f'Partner gender ({partner_gender}) does not match division gender requirement ({self.division.gender}).'
                    )
            
            # # Validate partner age restrictions
            # if self.division.born_after and partner_profile.date_of_birth:
            #     if partner_profile.date_of_birth < self.division.born_after:
            #         raise ValidationError(
            #             f'Partner must be born after {self.division.born_after}.'
            #         )
            
            # Check that partner is not already registered in this division
            # existing_partner_involvement = Involvement.objects.filter(
            #     tournament=self.tournament,
            #     division=self.division,
            #     player=self.partner
            # ).exclude(pk=self.pk if self.pk else None).exists()
            
            # if existing_partner_involvement:
            #     raise ValidationError(
            #         'Partner is already registered in this division.'
            #     )
        
        # elif self.partner:
        #     raise ValidationError(
        #         'Partner is not allowed for singles tournaments.'
        #     )
    
    def save(self, *args, **kwargs):
        """Override save to run validation and update timestamps."""
        # Update approved_at if status changed to approved
        if self.status == InvolvementStatus.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()
        
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_approved(self) -> bool:
        """Check if involvement is approved."""
        return self.status == InvolvementStatus.APPROVED
    
    @property
    def is_pending(self) -> bool:
        """Check if involvement is pending."""
        return self.status == InvolvementStatus.PENDING
    
    @property
    def is_rejected(self) -> bool:
        """Check if involvement is rejected."""
        return self.status == InvolvementStatus.REJECTED
    
    def approve(self, user=None):
        """Approve the involvement."""
        self.status = InvolvementStatus.APPROVED
        self.approved_at = timezone.now()
        if user:
            self.approved_by = user
        self.save(update_fields=['status', 'approved_at', 'approved_by', 'updated_at'])
    
    def reject(self):
        """Reject the involvement."""
        self.status = InvolvementStatus.REJECTED
        self.save(update_fields=['status', 'updated_at'])


class TournamentGroup(models.Model):
    """
    Model representing a group within a tournament division.
    Used for Round Robin + Knockout format.
    """
    division = models.ForeignKey(
        TournamentDivision,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Division',
        help_text='Division this group belongs to'
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name='Group Name',
        help_text='Name of the group (e.g., "Grupo A", "Grupo B")'
    )
    
    group_number = models.PositiveIntegerField(
        verbose_name='Group Number',
        help_text='Number of the group within the division'
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
        verbose_name = 'Tournament Group'
        verbose_name_plural = 'Tournament Groups'
        ordering = ['division', 'group_number']
        unique_together = [
            ('division', 'group_number'),
        ]
        indexes = [
            models.Index(fields=['division']),
            models.Index(fields=['group_number']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.division.name}"
    
    def clean(self) -> None:
        """Validate group data."""
        # Validate division format
        if self.division.format != TournamentFormat.ROUND_ROBIN_KNOCKOUT:
            raise ValidationError(
                'Groups can only be created for divisions with ROUND_ROBIN_KNOCKOUT format.'
            )
        
        # Validate group number is unique within division
        existing = TournamentGroup.objects.filter(
            division=self.division,
            group_number=self.group_number
        ).exclude(pk=self.pk if self.pk else None)
        
        if existing.exists():
            raise ValidationError(
                f'Group number {self.group_number} already exists for this division.'
            )
    
    def save(self, *args, **kwargs) -> None:
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def participant_count(self) -> int:
        """Return the number of participants in this group."""
        return self.standings.count()
    
    def validate_participant_count(self) -> None:
        """Validate that group has between 3 and 5 participants."""
        count = self.participant_count
        if count < 3:
            raise ValidationError(
                f'Group must have at least 3 participants. Current: {count}'
            )
        if count > 5:
            raise ValidationError(
                f'Group cannot have more than 5 participants. Current: {count}'
            )


class GroupStanding(models.Model):
    """
    Model representing a player's standing within a tournament group.
    Tracks statistics and positions for Round Robin + Knockout format.
    """
    group = models.ForeignKey(
        TournamentGroup,
        on_delete=models.CASCADE,
        related_name='standings',
        verbose_name='Group',
        help_text='Group this standing belongs to'
    )
    
    involvement = models.ForeignKey(
        Involvement,
        on_delete=models.CASCADE,
        related_name='group_standings',
        verbose_name='Involvement',
        help_text='Player or team involvement in the tournament'
    )
    
    # Statistics
    matches_played = models.PositiveIntegerField(
        default=0,
        verbose_name='Matches Played',
        help_text='Number of matches played'
    )
    
    matches_won = models.PositiveIntegerField(
        default=0,
        verbose_name='Matches Won',
        help_text='Number of matches won'
    )
    
    matches_lost = models.PositiveIntegerField(
        default=0,
        verbose_name='Matches Lost',
        help_text='Number of matches lost'
    )
    
    sets_won = models.PositiveIntegerField(
        default=0,
        verbose_name='Sets Won',
        help_text='Total sets won'
    )
    
    sets_lost = models.PositiveIntegerField(
        default=0,
        verbose_name='Sets Lost',
        help_text='Total sets lost'
    )
    
    points = models.PositiveIntegerField(
        default=0,
        verbose_name='Points',
        help_text='Points accumulated (e.g., 3 for win, 1 for loss)'
    )
    
    # Positions
    position_in_group = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Position in Group',
        help_text='Position within the group'
    )
    
    global_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Global Position',
        help_text='Global position across all groups'
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
        verbose_name = 'Group Standing'
        verbose_name_plural = 'Group Standings'
        ordering = ['group', 'position_in_group', 'global_position']
        unique_together = [
            ('group', 'involvement'),
        ]
        indexes = [
            models.Index(fields=['group']),
            models.Index(fields=['involvement']),
            models.Index(fields=['position_in_group']),
            models.Index(fields=['global_position']),
            models.Index(fields=['points']),
        ]
    
    def __str__(self) -> str:
        player_name = self.involvement.player.full_name
        if self.involvement.partner:
            player_name = f"{player_name} / {self.involvement.partner.full_name}"
        return f"{player_name} - {self.group.name} (Pos: {self.position_in_group or 'N/A'})"
    
    @property
    def sets_difference(self) -> int:
        """Calculate sets difference (sets_won - sets_lost)."""
        return self.sets_won - self.sets_lost