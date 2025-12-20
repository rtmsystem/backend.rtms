"""
Geographical models for managing countries.
"""
from django.db import models


class Country(models.Model):
    """
    Country model with basic information.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Country Name'
    )
    
    phone_code = models.CharField(
        max_length=10,
        verbose_name='Phone Code',
        help_text='International phone code (e.g., +1, +51, +34)'
    )
    
    flag = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Flag',
        help_text='Flag emoji or URL'
    )
    
    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.phone_code})"

