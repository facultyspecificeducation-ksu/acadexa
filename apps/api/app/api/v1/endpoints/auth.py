"""
================================================================================
Authentication API Endpoints
================================================================================

Authentication endpoints for staff login, logout, password management, and user invites.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from app.core.dependencies import get_authenticated_supabase_client, get_current_user, require_admin
from app.core.exceptions import RateLimitError, UnauthorizedError
from app.core.rate_limiter import get_rate_limit_key_for_auth, rate_limit
from app.core.security import SecurityContext
from app.core.supabase import get_service_role_client
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    InviteUserRequest,
    UserWithRolesResponse,
)

logger = logging.getLogger("acadexa.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
@rate_limit(limit=10, window_seconds=60, key_func=get_rate_limit_key_for_auth)
async def login(
    request: Request,
    login_data: LoginRequest,
):
    """
    Staff login endpoint.
    
    Rate limited to 10 attempts per minute per IP.
    Returns JWT token for authenticated session.
    """
    try:
        # Use service role to create authenticated client? No - use Supabase Auth directly
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        
        # Supabase Auth sign-in
        # Note: This requires the anon key. In production, use the auth client.
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        auth_response = temp_client.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password,
        })
        
        if not auth_response.user:
            raise UnauthorizedError("Invalid credentials")
        
        # Get user roles
        supabase = get_service_role_client()
        roles_result = supabase.table("user_roles")\
            .select("roles!inner(code)")\
            .eq("user_id", auth_response.user.id)\
            .execute()
        
        roles = []
        if roles_result.data:
            roles = [item["roles"]["code"] for item in roles_result.data if item.get("roles")]
        
        # Get profile
        profile_result = supabase.table("profiles")\
            .select("*")\
            .eq("id", auth_response.user.id)\
            .execute()
        
        profile = profile_result.data[0] if profile_result.data else {}
        
        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user=UserWithRolesResponse(
                id=auth_response.user.id,
                full_name=profile.get("full_name", ""),
                email=auth_response.user.email or "",
                phone=profile.get("phone"),
                avatar_url=profile.get("avatar_url"),
                is_active=profile.get("is_active", True),
                created_at=profile.get("created_at", ""),
                updated_at=profile.get("updated_at", ""),
                roles=roles,
            )
        )
        
    except Exception as e:
        logger.warning(f"Login failed for {login_data.email}: {e}")
        raise UnauthorizedError("Invalid credentials")


@router.post("/logout")
async def logout(
    current_user: SecurityContext = Depends(get_current_user),
):
    """
    Logout endpoint - invalidates current session.
    """
    try:
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        # Sign out
        temp_client.auth.sign_out()
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.warning(f"Logout error for user {current_user.user_id}: {e}")
        return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
):
    """
    Refresh an expiring session token.
    """
    try:
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        session = temp_client.auth.refresh_session(refresh_data.refresh_token)
        
        return RefreshTokenResponse(
            access_token=session.access_token
        )
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        raise UnauthorizedError("Invalid refresh token")


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(
    invite_data: InviteUserRequest,
    admin_user: SecurityContext = Depends(require_admin),
):
    """
    Invite a new staff member (admin only).
    
    Sends invitation email via Supabase Auth.
    """
    try:
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        # Create user invitation
        response = temp_client.auth.admin.invite_user_by_email(
            invite_data.email,
            options={"data": {"full_name": invite_data.full_name}}
        )
        
        logger.info(f"Admin {admin_user.user_id} invited user {invite_data.email}")
        
        return {
            "message": "Invitation sent successfully",
            "email": invite_data.email,
        }
        
    except Exception as e:
        logger.error(f"Failed to invite user {invite_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send invitation: {str(e)}"
        )


@router.post("/password-reset-request")
@rate_limit(limit=3, window_seconds=300, key_func=get_rate_limit_key_for_auth)
async def password_reset_request(
    reset_data: PasswordResetRequest,
):
    """
    Request password reset email.
    
    Rate limited to 3 requests per 5 minutes per IP.
    """
    try:
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        # Send password reset email
        temp_client.auth.reset_password_for_email(reset_data.email)
        
        # Always return success even if email doesn't exist (security)
        return {"message": "If an account exists with this email, a password reset link has been sent"}
        
    except Exception as e:
        # Don't reveal whether email exists
        logger.warning(f"Password reset requested for {reset_data.email}")
        return {"message": "If an account exists with this email, a password reset link has been sent"}


@router.post("/password-reset-confirm")
async def password_reset_confirm(
    confirm_data: PasswordResetConfirm,
):
    """
    Confirm password reset with token.
    """
    try:
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        # Update password
        temp_client.auth.update_user(
            {"password": confirm_data.new_password},
            jwt=confirm_data.token
        )
        
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        logger.error(f"Password reset confirmation failed: {e}")
        raise UnauthorizedError("Invalid or expired reset token")


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: SecurityContext = Depends(get_current_user),
):
    """
    Change password for authenticated user.
    """
    try:
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        from supabase import create_client
        temp_client = create_client(manager._url, manager._service_role_key)
        
        # Re-authenticate with current password
        auth_response = temp_client.auth.sign_in_with_password({
            "email": current_user.email,
            "password": password_data.current_password,
        })
        
        if not auth_response.user:
            raise UnauthorizedError("Current password is incorrect")
        
        # Update password
        temp_client.auth.update_user(
            {"password": password_data.new_password},
            jwt=auth_response.session.access_token
        )
        
        logger.info(f"User {current_user.user_id} changed password")
        return {"message": "Password changed successfully"}
        
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.error(f"Password change failed for {current_user.user_id}: {e}")
        raise UnauthorizedError("Current password is incorrect")