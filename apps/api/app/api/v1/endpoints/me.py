"""
================================================================================
Current User (me) & Roles Endpoints
================================================================================

Implements the current authenticated user endpoints required by the API spec:
- GET /api/v1/me
- PATCH /api/v1/me
- PATCH /api/v1/me/password
- GET /api/v1/roles

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from supabase import Client

from app.core.dependencies import get_authenticated_supabase_client, get_current_user
from app.core.security import SecurityContext
from app.core.exceptions import ForbiddenError, UnauthorizedError

router = APIRouter(prefix="/me", tags=["Current User"])


class MePasswordUpdate(BaseModel):
    current_password: str
    new_password: str


@router.get("", status_code=status.HTTP_200_OK)
async def get_me(
    current_user: SecurityContext = Depends(get_current_user),
    supabase: Client = Depends(get_authenticated_supabase_client),
):
    """Returns the authenticated user's profile and roles."""
    # Fetch profile (RLS should allow the user to select their own row)
    profile = supabase.table("profiles").select("*").eq("id", current_user.user_id).single().execute()
    data = profile.data or {}

    # current_user.roles already loaded by get_current_user
    return {
        "id": data.get("id") or current_user.user_id,
        "full_name": data.get("full_name"),
        "email": current_user.email,
        "phone": data.get("phone"),
        "avatar_url": data.get("avatar_url"),
        "is_active": data.get("is_active"),
        "roles": current_user.roles,
    }


@router.patch("", status_code=status.HTTP_200_OK)
async def patch_me(
    payload: dict,
    current_user: SecurityContext = Depends(get_current_user),
    supabase: Client = Depends(get_authenticated_supabase_client),
):
    """Updates user-owned profile fields (full_name, phone, avatar_url)."""
    allowed_keys = {"full_name", "phone", "avatar_url"}
    update_data = {k: v for k, v in payload.items() if k in allowed_keys}

    if not update_data:
        return await get_me(current_user=current_user, supabase=supabase)

    supabase.table("profiles").update(update_data).eq("id", current_user.user_id).execute()

    # Re-fetch to ensure response reflects persisted values
    profile = supabase.table("profiles").select("*").eq("id", current_user.user_id).single().execute()
    data = profile.data or {}

    return {
        "id": data.get("id") or current_user.user_id,
        "full_name": data.get("full_name"),
        "email": current_user.email,
        "phone": data.get("phone"),
        "avatar_url": data.get("avatar_url"),
        "is_active": data.get("is_active"),
        "roles": current_user.roles,
    }


@router.patch("/password", status_code=status.HTTP_200_OK)
async def patch_me_password(
    payload: MePasswordUpdate,
    current_user: SecurityContext = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    # Delegate to existing Supabase admin/service implementation by reusing auth update flow.
    # To keep changes minimal and not redesign auth logic, we call Supabase directly using service role.
    from app.core.supabase import get_supabase_manager
    from supabase import create_client

    manager = get_supabase_manager()
    temp_client = create_client(manager._url, manager._service_role_key)

    # Re-authenticate with current password
    auth_response = temp_client.auth.sign_in_with_password({
        "email": current_user.email,
        "password": payload.current_password,
    })

    if not auth_response.user:
        raise UnauthorizedError("Current password is incorrect")

    # Update password
    temp_client.auth.update_user(
        {"password": payload.new_password},
        jwt=auth_response.session.access_token,
    )

    return {"message": "Password changed successfully"}


# -----------------------------------------------------------------------------
# Roles lookup (spec Group 21.1)
# -----------------------------------------------------------------------------

roles_router = APIRouter(tags=["Roles"], prefix="")


@roles_router.get("/roles", status_code=status.HTTP_200_OK)
async def get_roles(supabase: Client = Depends(get_authenticated_supabase_client)):
    roles = supabase.table("roles").select("code, name_ar, name_en").in_("code", ["admin", "academic_advisor"]).execute()
    rows = roles.data or []

    return [
        {
            "code": r.get("code"),
            "name_ar": r.get("name_ar"),
            "name_en": r.get("name_en"),
        }
        for r in rows
    ]


# Mount the roles router under the same file's module.
router.include_router(roles_router)

