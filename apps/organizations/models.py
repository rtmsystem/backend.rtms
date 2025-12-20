"""
Organization models for managing companies/entities.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    """
    Model representing an organization/company.
    """
    # Información básica de la organización
    name = models.CharField(
        max_length=255,
        verbose_name='Nombre de la organización'
    )
    
    nit = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='NIT',
        help_text='Número de Identificación Tributaria'
    )
    
    # Relación con usuarios
    administrators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='administered_organizations',
        verbose_name='Administradores',
        help_text='Usuarios administradores de esta organización'
    )
    
    # Usuario que creó la organización (para referencia)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_organizations',
        verbose_name='Creado por'
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

    logo = models.ImageField(
        upload_to='organizations_logos/',
        blank=True,
        null=True,
        verbose_name='Logo de la organización'
    )
    
    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nit']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.nit})"
    
    # Propiedades útiles
    @property
    def administrator_count(self) -> int:
        """Retorna el número de administradores."""
        return self.administrators.count()

    @property
    def logo_url(self) -> str:
        """Return logo URL or default logo."""
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        # Imagen por defecto SVG
        return '/static/images/default-Organization-logo.svg'
    
    # Métodos de gestión
    def add_administrator(self, user):
        """Agrega un usuario como administrador."""
        from apps.users.models import UserRole
        
        # Cambiar rol a admin si no lo es
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            user.save(update_fields=['role'])
        
        self.administrators.add(user)
    
    def remove_administrator(self, user):
        """Remueve un usuario de los administradores."""
        self.administrators.remove(user)
    
    def is_administrator(self, user) -> bool:
        """Verifica si un usuario es administrador."""
        return self.administrators.filter(id=user.id).exists()

