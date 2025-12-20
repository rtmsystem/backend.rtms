"""
API views for geographical data.
"""
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Country
from .serializers import CountrySerializer
from apps.api.mixins import StandardResponseMixin


class CountryViewSet(StandardResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar países.
    
    - list: API pública para obtener todos los países (sin autenticación)
    Solo permite métodos GET (read-only).
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]  # API pública, no requiere autenticación
    pagination_class = None  # Sin paginación, devuelve todos los registros
    
    @swagger_auto_schema(
        operation_description="Obtiene la lista de todos los países disponibles. Esta API es pública y no requiere autenticación.",
        responses={
            200: CountrySerializer(many=True),
        },
        security=[]  # No requiere autenticación
    )
    def list(self, request, *args, **kwargs):
        """Lista todos los países disponibles sin paginación."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(
                data=serializer.data,
                message="Countries retrieved successfully"
            )
        except Exception:
            return self.error_response(
                message="Error retrieving countries",
                error_code="LIST_ERROR",
                status_code=500
            )

