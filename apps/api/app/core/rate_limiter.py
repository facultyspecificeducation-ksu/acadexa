"""
================================================================================
Rate Limiter for Acadexa API
================================================================================

Simple in-memory rate limiter for critical endpoints.
No Redis required - uses Python dict with cleanup.

Rate limits applied to:
- Auth endpoints (login, password reset) - 10 per minute
- AI endpoints - 30 per minute per user
- Import endpoints - 5 per minute per user

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitError
from app.core.security import hash_rate_limit_key

# Rate limit configuration
# Structure: {(endpoint_pattern, key): [(timestamp, count), ...]}
_rate_limit_store: Dict[Tuple[str, str], List[float]] = defaultdict(list)

# Cleanup interval (seconds) - remove old entries every 5 minutes
CLEANUP_INTERVAL = 300
_last_cleanup = time.time()


class RateLimiter:
    """
    In-memory rate limiter for API endpoints.
    
    Uses a sliding window algorithm.
    """
    
    def __init__(self):
        self._store: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    
    def _cleanup_old_entries(self, max_age_seconds: int = 3600) -> None:
        """Remove entries older than max_age_seconds to prevent memory bloat."""
        global _last_cleanup
        now = time.time()
        
        if now - _last_cleanup < CLEANUP_INTERVAL:
            return
        
        _last_cleanup = now
        
        for key in list(self._store.keys()):
            # Filter timestamps that are still valid (within max_age)
            valid_timestamps = [ts for ts in self._store[key] if now - ts < max_age_seconds]
            if valid_timestamps:
                self._store[key] = valid_timestamps
            else:
                del self._store[key]
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """
        Check if a request is within rate limits.
        
        Args:
            key: Unique identifier (e.g., "auth:login:ip_hash")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Clean up old entries periodically
        self._cleanup_old_entries()
        
        # Get request timestamps for this key
        timestamps = self._store[key]
        
        # Remove timestamps outside the window
        valid_timestamps = [ts for ts in timestamps if ts > window_start]
        self._store[key] = valid_timestamps
        
        # Check if limit is exceeded
        if len(valid_timestamps) >= limit:
            # Calculate retry after - oldest timestamp in window + window_seconds
            oldest = min(valid_timestamps)
            retry_after = int(oldest + window_seconds - now) + 1
            return False, max(1, retry_after)
        
        # Add current request timestamp
        self._store[key].append(now)
        return True, 0


# Singleton instance
_rate_limiter = RateLimiter()


def rate_limit(
    limit: int,
    window_seconds: int = 60,
    key_func=None,
):
    """
    Decorator or dependency for rate limiting endpoints.
    
    Args:
        limit: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_func: Function that takes request and returns rate limit key
        
    Usage:
        @router.post("/login")
        @rate_limit(limit=10, window_seconds=60)
        async def login(request: Request):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]
            
            if request is None:
                # If no request found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Determine rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use endpoint path + client IP hash
                client_ip = request.client.host if request.client else "unknown"
                key = f"{request.url.path}:{hash_rate_limit_key(client_ip)}"
            
            # Check rate limit
            allowed, retry_after = _rate_limiter.check_rate_limit(key, limit, window_seconds)
            
            if not allowed:
                raise RateLimitError(retry_after)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_rate_limit_key_for_auth(request: Request) -> str:
    """Get rate limit key for auth endpoints (by IP)."""
    client_ip = request.client.host if request.client else "unknown"
    return f"auth:{hash_rate_limit_key(client_ip)}"


def get_rate_limit_key_for_user(request: Request) -> str:
    """Get rate limit key for user-specific endpoints."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_rate_limit_key_for_auth(request)