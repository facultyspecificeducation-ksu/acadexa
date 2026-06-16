"""
================================================================================
Supabase Client Initialization for Acadexa API
================================================================================

This module provides Supabase client initialization for:
- Database operations (with RLS-compatible auth)
- Storage bucket operations
- RPC function calls

Security:
- Service role client is ONLY for background jobs (parser, expert system)
- Authenticated client is for endpoint handlers (uses user's JWT via PostgREST)
- NEVER expose service role key to frontend

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger("acadexa.supabase")


class SupabaseClientManager:
    """
    Manages Supabase client instances with proper authentication.
    
    Two client types:
    1. service_role_client: Uses service role key (bypasses RLS)
       - ONLY for background jobs (parser, expert system)
       - NEVER exposed via API endpoints
    
    2. auth_client: Uses user's JWT token via PostgREST auth header
       - For API endpoints (respects RLS)
       - Created per request with user's token
    """
    
    def __init__(self):
        self._service_role_client: Optional[Client] = None
        self._url = settings.SUPABASE_URL
        self._service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self._anon_key = settings.SUPABASE_ANON_KEY
        
        if not self._url or not self._service_role_key or not self._anon_key:
            logger.error("Supabase configuration incomplete")
            raise ValueError("Supabase configuration incomplete - check environment variables")
    
    def get_service_role_client(self) -> Client:
        """
        Get client with service role (bypasses RLS).
        
        WARNING: Use ONLY for background jobs, NEVER for API endpoints.
        
        Returns:
            Supabase client with admin privileges
        """
        if self._service_role_client is None:
            logger.info("Initializing Supabase service role client")
            self._service_role_client = create_client(
                self._url,
                self._service_role_key
            )
        return self._service_role_client
    
    def get_authenticated_client(self, access_token: str) -> Client:
        """
        Get client with user's JWT token (respects RLS).
        
        CORRECT Supabase v2 usage:
        - Client is created with ANON KEY (not service role)
        - JWT is attached as PostgREST auth header for RLS enforcement
        
        Args:
            access_token: User's JWT token from Authorization header
            
        Returns:
            Supabase client authenticated as the user with RLS enforced
        """
        if not access_token:
            raise ValueError("Access token required for authenticated client")
        
        # Create client with ANON KEY (safe for frontend)
        # Then attach JWT for RLS via the auth header
        client = create_client(
            self._url,
            self._anon_key,
            headers={
                "Authorization": f"Bearer {access_token}",
            }
        )
        
        return client


# Singleton instance
_client_manager: Optional[SupabaseClientManager] = None


def get_supabase_manager() -> SupabaseClientManager:
    """Get singleton Supabase client manager."""
    global _client_manager
    if _client_manager is None:
        _client_manager = SupabaseClientManager()
    return _client_manager


def get_service_role_client() -> Client:
    """
    Get service role client for background jobs.
    
    Use this for:
    - ExcelParser (saving to Supabase)
    - Expert system (writing analyses)
    - Batch operations
    
    Returns:
        Supabase client with admin privileges
    """
    return get_supabase_manager().get_service_role_client()


def get_authenticated_client(access_token: str) -> Client:
    """
    Get authenticated client for API endpoints.
    
    CORRECT Supabase v2 usage:
    - Uses ANON KEY + JWT token for RLS enforcement
    - NEVER uses service role for user-facing operations
    
    Args:
        access_token: User's JWT token
        
    Returns:
        Supabase client with user's permissions (RLS enforced)
    """
    return get_supabase_manager().get_authenticated_client(access_token)


# Legacy compatibility - for existing code that expects a single client
# DEPRECATED: Use get_service_role_client() for background jobs
# or get_authenticated_client() for endpoint handlers.
@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Legacy: Get service role client.
    
    DEPRECATED: Use get_service_role_client() for background jobs
    or get_authenticated_client() for endpoint handlers.
    
    Returns:
        Supabase client with service role
    """
    logger.warning(
        "Using deprecated get_supabase_client() - "
        "specify client type explicitly. "
        "This bypasses RLS and is insecure for request handlers."
    )
    return get_service_role_client()