"""
================================================================================
FastAPI Middleware for Acadexa API
================================================================================

Provides:
- Request ID generation for tracing
- Consistent error response formatting
- Request logging

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AcadexaException

logger = logging.getLogger("acadexa.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique request ID to every request for tracing.
    
    The request ID is:
    - Generated as a UUID
    - Added to response headers as X-Request-ID
    - Added to log context for correlation
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = str(uuid.uuid4())
        
        # Add to request state for access in endpoints
        request.state.request_id = request_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Catches exceptions and returns consistent error responses.
    
    Handles:
    - AcadexaException (custom exceptions)
    - ValidationError (Pydantic validation)
    - Unexpected exceptions (500)
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except AcadexaException as exc:
            # Our custom exceptions - return formatted response
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_response(),
            )
        except Exception as exc:
            # Unexpected error - log and return generic 500
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(
                f"Unhandled exception for request {request_id}",
                exc_info=exc,
                extra={"request_id": request_id, "path": request.url.path}
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "An internal server error occurred",
                        "status_code": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "details": {"request_id": request_id},
                    }
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all requests with method, path, status, and duration.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI app.
    
    Order matters:
    1. RequestID (earliest) - generates ID for all subsequent middleware
    2. RequestLogging - logs after processing
    3. ErrorHandling - catches exceptions from later middleware
    """
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)