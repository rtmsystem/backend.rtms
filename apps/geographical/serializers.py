"""
Serializers for Country model.
"""
from rest_framework import serializers

from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    """
    Serializer for Country model.
    """
    
    class Meta:
        model = Country
        fields = [
            'id',
            'name',
            'phone_code',
            'flag',
        ]
        read_only_fields = ['id']

