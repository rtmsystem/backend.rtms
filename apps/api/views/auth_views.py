"""
Authentication-related API views.
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.serializers import UserSerializer
from apps.api.utils import APIResponse


class CurrentUserView(APIView):
    """
    Get current authenticated user information.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Obtiene la información del usuario autenticado",
        responses={
            200: UserSerializer(),
            401: "No autenticado"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        """Return current user information."""
        serializer = UserSerializer(request.user)
        return APIResponse.success(
            data=serializer.data,
            message="User information retrieved successfully"
        )


class VerifyTokenView(APIView):
    """
    Verify JWT token and return user information.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Verifica el token JWT y retorna información del usuario",
        responses={
            200: openapi.Response(
                description="Token válido",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: "Token inválido"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        """Verify token and return user data."""
        serializer = UserSerializer(request.user)
        return APIResponse.success(
            data={
                'valid': True,
                'user': serializer.data
            },
            message="Token is valid"
        )


class LogoutView(APIView):
    """
    Logout user by blacklisting the refresh token.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Cierra sesión del usuario invalidando el token de actualización",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Token de actualización')
            },
            required=['refresh']
        ),
        responses={
            200: openapi.Response(
                description="Sesión cerrada exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Token de actualización requerido",
            401: "No autenticado"
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        """Logout user by blacklisting refresh token."""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return APIResponse.error(
                    message="Refresh token required",
                    error_code="MISSING_REFRESH_TOKEN",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return APIResponse.success(
                data=None,
                message="Session closed successfully"
            )
            
        except Exception as e:
            return APIResponse.error(
                message="Invalid token",
                error_code="INVALID_TOKEN",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns user data along with tokens.
    """
    
    @swagger_auto_schema(
        operation_description="Inicia sesión y obtiene tokens de acceso y actualización",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email del usuario'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Contraseña')
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response(
                description="Inicio de sesión exitoso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            401: "Credenciales inválidas"
        }
    )
    def post(self, request, *args, **kwargs):
        """Login and return tokens with user data."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get the user from the validated data
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            
            # Add user data to response
            user_serializer = UserSerializer(user)
            response.data['user'] = user_serializer.data
            
            # Convert to standard format
            return APIResponse.success(
                data=response.data,
                message="Login successful"
            )
        
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view.
    """
    
    @swagger_auto_schema(
        operation_description="Actualiza el token de acceso usando el token de actualización",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Token de actualización')
            },
            required=['refresh']
        ),
        responses={
            200: openapi.Response(
                description="Token actualizado exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: "Token de actualización inválido"
        }
    )
    def post(self, request, *args, **kwargs):
        """Refresh access token."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            return APIResponse.success(
                data=response.data,
                message="Token refreshed successfully"
            )
        
        return response

