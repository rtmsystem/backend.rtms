"""
Mixins for standard API responses.
"""
from typing import Any, Dict, List, Optional

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .utils import APIResponse


class StandardResponseMixin:
    """
    Mixin that provides methods for standard responses in ViewSets.
    """
    
    def success_response(
        self,
        data: Any = None,
        message: str = "Operation successful",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Generate a standard successful response."""
        return APIResponse.success(data, message, status_code, meta)
    
    def error_response(
        self,
        message: str = "Operation failed",
        errors: Optional[Dict[str, List[str]]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Generate a standard error response."""
        return APIResponse.error(message, errors, status_code, error_code, meta)
    
    def created_response(
        self,
        data: Any = None,
        message: str = "Resource created successfully",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Generate a successful creation response."""
        return APIResponse.created(data, message, meta)
    
    def not_found_response(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Generate a resource not found response."""
        return APIResponse.not_found(message, error_code, meta)
    
    def forbidden_response(
        self,
        message: str = "You do not have permission to perform this action",
        error_code: str = "FORBIDDEN",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Generate an access denied response."""
        return APIResponse.forbidden(message, error_code, meta)
    
    def validation_error_response(
        self,
        errors: Dict[str, List[str]],
        message: str = "Validation error",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Generate a validation error response."""
        return APIResponse.validation_error(errors, message, meta)


class StandardModelViewSet(StandardResponseMixin, ModelViewSet):
    """
    ViewSet that extends ModelViewSet with standard responses.
    
    Overrides main methods to use standard response format.
    """
    
    def list(self, request, *args, **kwargs):
        """List resources with standard format."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.paginator.get_paginated_response(serializer.data)
                
                # Convert to standard format
                return self.success_response(
                    data=paginated_response.data['results'],
                    message="List retrieved successfully",
                    meta={
                        'pagination': {
                            'count': paginated_response.data['count'],
                            'next': paginated_response.data['next'],
                            'previous': paginated_response.data['previous'],
                            'page': request.query_params.get('page', 1),
                            'page_size': self.paginator.page_size,
                            'total_pages': (paginated_response.data['count'] + self.paginator.page_size - 1) // self.paginator.page_size
                        }
                    }
                )
            
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(
                data=serializer.data,
                message="List retrieved successfully"
            )
            
        except Exception as e:
            return self.error_response(
                message="Error retrieving list",
                error_code="LIST_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific resource with standard format."""
        from django.http import Http404
        from rest_framework.exceptions import PermissionDenied
        
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data,
                message="Resource retrieved successfully"
            )
        except Http404:
            return self.not_found_response(
                message="Resource not found"
            )
        except PermissionDenied:
            return self.forbidden_response(
                message="You do not have permission to perform this action"
            )
        except Exception as e:
            return self.error_response(
                message="Error retrieving resource",
                error_code="RETRIEVE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """Create a resource with standard format."""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                instance = serializer.save()
                output_serializer = self.get_serializer(instance)
                return self.created_response(
                    data=output_serializer.data,
                    message="Resource created successfully"
                )
            else:
                return self.validation_error_response(
                    errors=serializer.errors,
                    message="Validation error in submitted data"
                )
        except Exception as e:
            return self.error_response(
                message="Error creating resource",
                error_code="CREATE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """Update a resource with standard format."""
        from django.http import Http404
        from rest_framework.exceptions import PermissionDenied
        
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if serializer.is_valid():
                instance = serializer.save()
                output_serializer = self.get_serializer(instance)
                return self.success_response(
                    data=output_serializer.data,
                    message="Resource updated successfully"
                )
            else:
                return self.validation_error_response(
                    errors=serializer.errors,
                    message="Validation error in submitted data"
                )
        except Http404:
            return self.not_found_response(
                message="Resource not found"
            )
        except PermissionDenied:
            return self.forbidden_response(
                message="You do not have permission to perform this action"
            )
        except Exception as e:
            return self.error_response(
                message="Error updating resource",
                error_code="UPDATE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update with standard format."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a resource with standard format."""
        from django.http import Http404
        from rest_framework.exceptions import PermissionDenied
        
        try:
            instance = self.get_object()
            instance.delete()
            return self.success_response(
                data=None,
                message="Resource deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Http404:
            return self.not_found_response(
                message="Resource not found"
            )
        except PermissionDenied:
            return self.forbidden_response(
                message="You do not have permission to perform this action"
            )
        except Exception as e:
            return self.error_response(
                message="Error deleting resource",
                error_code="DELETE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
