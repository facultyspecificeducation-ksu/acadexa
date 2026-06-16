"""
================================================================================
Security Utilities for Acadexa API
================================================================================

JWT verification, role extraction, and security helpers.

Role caching strategy:
- Roles are fetched from user_roles table on first request
- Cached in memory with TTL (60 seconds by default)
- No Redis required - simple dict cache with expiration

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import jwt
from fastapi import Request

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.supabase import get_supabase_client, get_service_role_client

logger = logging.getLogger("acadexa.security")

# Simple in-memory cache for user roles
# Structure: {user_id: (roles_list, expiry_timestamp)}
_user_roles_cache: Dict[str, Tuple[List[str], float]] = {}
CACHE_TTL_SECONDS = 60  # Cache roles for 60 seconds


def _get_cached_roles(user_id: str) -> Optional[List[str]]:
    """Get cached roles for a user if not expired."""
    if user_id in _user_roles_cache:
        roles, expiry = _user_roles_cache[user_id]
        if time.time() < expiry:
            return roles
        else:
            del _user_roles_cache[user_id]
    return None


def _cache_roles(user_id: str, roles: List[str]) -> None:
    """Cache roles for a user with TTL."""
    _user_roles_cache[user_id] = (roles, time.time() + CACHE_TTL_SECONDS)


async def fetch_user_roles(user_id: str) -> List[str]:
    """
    Fetch user roles from database.
    
    Checks cache first, then queries user_roles table.
    
    NOTE: This uses service_role client because:
    - user_roles table requires admin access to read
    - The user's own JWT cannot read user_roles via RLS
    - This is a read-only operation scoped to the authenticated user's ID
    - The result is cached to minimize service_role usage
    
    Args:
        user_id: The user's UUID from auth.users
        
    Returns:
        List of role codes (e.g., ['admin'], ['academic_advisor'], or [])
    """
    cached_roles = _get_cached_roles(user_id)
    if cached_roles is not None:
        return cached_roles
    
    try:
        # Use service_role for reading user_roles (read-only, user-scoped)
        supabase = get_service_role_client()
        result = supabase.table("user_roles")\
            .select("roles!inner(code)")\
            .eq("user_id", user_id)\
            .execute()
        
        roles = []
        if result.data:
            roles = [item["roles"]["code"] for item in result.data if item.get("roles")]
        
        _cache_roles(user_id, roles)
        
        logger.debug(f"Fetched roles for user {user_id}: {roles}")
        return roles
        
    except Exception as e:
        logger.warning(f"Failed to fetch roles for user {user_id}: {e}")
        return []


def clear_user_role_cache(user_id: Optional[str] = None) -> None:
    """
    Clear role cache for a specific user or all users.
    
    Call this after role assignment changes.
    
    Args:
        user_id: If provided, clear only this user's cache. Otherwise clear all.
    """
    if user_id:
        _user_roles_cache.pop(user_id, None)
        logger.debug(f"Cleared role cache for user {user_id}")
    else:
        _user_roles_cache.clear()
        logger.debug("Cleared all role caches")


def verify_jwt_token(token: str) -> Dict:
    """
    Verify and decode a Supabase JWT token.
    
    Security: Audience verification is enabled to prevent cross-project token replay.
    
    Args:
        token: The JWT token from Authorization header (without 'Bearer ' prefix)
        
    Returns:
        Decoded token payload
        
    Raises:
        UnauthorizedError: If token is invalid, expired, or malformed
    """
    if not token:
        raise UnauthorizedError("No token provided")
    
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",  # ← FIXED: Prevents cross-project token replay
        )
        
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise UnauthorizedError("Token has expired")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token: missing user ID")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise UnauthorizedError(f"Invalid token: {str(e)}")


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from the Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Token string or None if not present
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return auth_header


def hash_rate_limit_key(key: str) -> str:
    """
    Hash a rate limit key for storage.
    
    Used to avoid storing raw IPs/emails in rate limit store.
    """
    return hashlib.md5(key.encode()).hexdigest()[:16]


class SecurityContext:
    """
    Holds security information for the current request.
    
    Created by get_current_user dependency after JWT verification
    and role fetching.
    
    Attributes:
        user_id: The authenticated user's UUID
        email: The user's email address
        roles: List of role codes assigned to the user
        is_admin: True if user has admin role
        is_advisor: True if user has academic_advisor role
        is_staff: True if user has any staff role (admin or advisor)
        access_token: The raw JWT token (for creating authenticated Supabase clients)
    """
    
    def __init__(
        self,
        user_id: str,
        email: str,
        roles: List[str],
        access_token: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.roles = roles
        self.access_token = access_token
        self.is_admin = "admin" in roles
        self.is_advisor = "academic_advisor" in roles
        self.is_staff = self.is_admin or self.is_advisor
    
    @classmethod
    async def from_token(cls, token: str) -> "SecurityContext":
        """
        Create SecurityContext from JWT token.
        
        Fetches roles from database (with caching).
        
        Args:
            token: JWT token string
            
        Returns:
            SecurityContext instance
            
        Raises:
            UnauthorizedError: If token is invalid
        """
        payload = verify_jwt_token(token)
        user_id = payload.get("sub")
        email = payload.get("email", "")
        
        roles = await fetch_user_roles(user_id)
        
        return cls(
            user_id=user_id,
            email=email,
            roles=roles,
            access_token=token,
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "roles": self.roles,
            "is_admin": self.is_admin,
            "is_advisor": self.is_advisor,
            "is_staff": self.is_staff,
        }