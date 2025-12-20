"""
Custom User Model with role-based permissions.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    """User role choices."""
    ADMIN = 'admin', 'Admin'
    PLAYER = 'player', 'Player'


class UserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(self, email: str, password: str = None, **extra_fields) -> 'User':
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields) -> 'User':
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with role-based permissions.
    """
    
    # Basic information
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
    
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='First Name'
    )
    
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Last Name'
    )
    
    # Avatar
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar',
        help_text='User profile image'
    )
    
    # Role-based permissions
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PLAYER,
        verbose_name='Role'
    )
    
    # Status flags
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Staff'
    )
    
    # Timestamps
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date Joined'
    )
    
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Last Login'
    )
    
    # Manager
    objects = UserManager()
    
    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self) -> str:
        return self.email
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_player(self) -> bool:
        """Check if user is a player."""
        return self.role == UserRole.PLAYER
    
    @property
    def avatar_url(self) -> str:
        """Return avatar URL or default avatar."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        # Default SVG image
        return '/static/images/default-avatar.svg'
    
    def has_perm(self, perm, obj=None) -> bool:
        """Check if user has a specific permission."""
        if self.is_active and self.is_superuser:
            return True
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label) -> bool:
        """Check if user has permissions to view the app."""
        if self.is_active and self.is_superuser:
            return True
        return super().has_module_perms(app_label)

