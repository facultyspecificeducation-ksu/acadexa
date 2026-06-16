"""
================================================================================
Custom Exceptions for Acadexa API
================================================================================

Provides consistent error handling across the API.
All exceptions include error_code for client-side handling.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class AcadexaException(HTTPException):
    """
    Base exception for all Acadexa custom exceptions.
    
    Attributes:
        status_code: HTTP status code
        detail: Human-readable error message
        error_code: Machine-readable error code for client handling
        details: Additional error context
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.details = details or {}
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        response = {
            "error": {
                "message": self.detail,
                "status_code": self.status_code,
            }
        }
        if self.error_code:
            response["error"]["code"] = self.error_code
        if self.details:
            response["error"]["details"] = self.details
        return response


class NotFoundError(AcadexaException):
    """Resource not found (404)."""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} not found: {identifier}",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "identifier": identifier},
        )


class ConflictError(AcadexaException):
    """Resource already exists or conflict (409)."""
    
    def __init__(self, detail: str, error_code: str = "CONFLICT", details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
            details=details or {},
        )


class ForbiddenError(AcadexaException):
    """Insufficient permissions (403)."""
    
    def __init__(self, detail: str = "Insufficient permissions", required_role: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
            details={"required_role": required_role} if required_role else {},
        )


class UnauthorizedError(AcadexaException):
    """Authentication required or invalid (401)."""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ValidationError(AcadexaException):
    """Request validation failed (422)."""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class BusinessRuleError(AcadexaException):
    """Business rule violation (400)."""
    
    def __init__(self, detail: str, rule_code: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=rule_code,
        )


class RateLimitError(AcadexaException):
    """Rate limit exceeded (429)."""
    
    def __init__(self, retry_after_seconds: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after_seconds} seconds.",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after_seconds},
        )


class ServiceUnavailableError(AcadexaException):
    """External service unavailable (503)."""
    
    def __init__(self, service: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail or f"{service} service is temporarily unavailable",
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
        )