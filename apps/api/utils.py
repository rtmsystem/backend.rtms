"""
Utilities for standard API responses.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


def get_client_ip(request) -> Optional[str]:
    """
    Get the client IP address from the request.
    
    Args:
        request: Django request object
        
    Returns:
        IP address as string or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class APIResponse:
    """
    Class for generating standard API responses.
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation successful",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate a standard successful response.
        
        Args:
            data: Data to return
            message: Descriptive message
            status_code: HTTP status code
            meta: Additional metadata
            
        Returns:
            Response with standard format
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "version": getattr(settings, 'API_VERSION', 'v1'),
                **(meta or {})
            }
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str = "Operation failed",
        errors: Optional[Union[Dict[str, List[str]], List[str]]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate a standard error response.
        
        Args:
            message: Main error message
            errors: Specific errors (can be dict or list)
            status_code: HTTP status code
            error_code: Custom error code
            meta: Additional metadata
            
        Returns:
            Response with standard error format
        """
        response_data = {
            "success": False,
            "message": message,
            "errors": errors,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "version": getattr(settings, 'API_VERSION', 'v1'),
                "error_code": error_code,
                **(meta or {})
            }
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def paginated(
        data: List[Any],
        count: int,
        page: int,
        page_size: int,
        next_url: Optional[str] = None,
        previous_url: Optional[str] = None,
        message: str = "List retrieved successfully",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate a standard paginated response.
        
        Args:
            data: List of data
            count: Total number of elements
            page: Current page
            page_size: Page size
            next_url: Next page URL
            previous_url: Previous page URL
            message: Descriptive message
            meta: Additional metadata
            
        Returns:
            Response with standard paginated format
        """
        total_pages = (count + page_size - 1) // page_size
        
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "count": count,
                "next": next_url,
                "previous": previous_url,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "version": getattr(settings, 'API_VERSION', 'v1'),
                **(meta or {})
            }
        }
        
        return Response(response_data)
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate a successful creation response (201).
        
        Args:
            data: Created resource data
            message: Descriptive message
            meta: Additional metadata
            
        Returns:
            Response with standard format
        """
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            meta=meta
        )
    
    @staticmethod
    def no_content(
        message: str = "Operation successful with no content",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate a no content response (204).
        
        Args:
            message: Descriptive message
            meta: Additional metadata
            
        Returns:
            Response with standard format
        """
        return APIResponse.success(
            data=None,
            message=message,
            status_code=status.HTTP_204_NO_CONTENT,
            meta=meta
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate a resource not found response (404).
        
        Args:
            message: Descriptive message
            error_code: Error code
            meta: Additional metadata
            
        Returns:
            Response with standard error format
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            meta=meta
        )
    
    @staticmethod
    def forbidden(
        message: str = "You do not have permission to perform this action",
        error_code: str = "FORBIDDEN",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate an access denied response (403).
        
        Args:
            message: Descriptive message
            error_code: Error code
            meta: Additional metadata
            
        Returns:
            Response with standard error format
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            meta=meta
        )
    
    @staticmethod
    def unauthorized(
        message: str = "You are not authenticated",
        error_code: str = "UNAUTHORIZED",
        meta: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Generate an unauthenticated response (401).
        
        Args:
            message: Descriptive message
            error_code: Error code
            meta: Additional metadata
            
        Returns:
            Response with standard error format
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            meta=meta
        )
    
    @staticmethod
    def validation_error(
        errors: Union[Dict[str, List[str]], List[str]],
        message: str = "Validation error",
        meta: Optional[Dict[str, Any]] = None,
        error_code: str = "VALIDATION_ERROR"
    ) -> Response:
        """
        Generate a validation error response (400).
        
        Args:
            errors: Validation errors
            message: Descriptive message
            meta: Additional metadata
            
        Returns:
            Response with standard error format
        """
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            meta=meta
        )
