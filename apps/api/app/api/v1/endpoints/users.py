"""
================================================================================
Users API Endpoints
================================================================================

User management endpoints for admin role:
- List users with filtering
- Get user details
- Update user profiles
- Delete users
- Manage role assignments

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_user_service, require_admin
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import clear_user_role_cache
from app.schemas.user import (
    ProfileUpdate,
    ProfileResponse,
    UserWithRolesResponse,
    UserListResponse,
    UserRoleAssignment,
)
from app.services.user_service import UserService

logger = logging.getLogger("acadexa.api.users")

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role (admin, academic_advisor)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: UserService = Depends(get_user_service),
    _=Depends(require_admin),
):
    """
    List all staff users with filtering.
    
    Admin only.
    """
    users, total = await service.get_users(
        is_active=is_active,
        role=role,
        search=search,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return UserListResponse(
        items=[UserWithRolesResponse(**u) for u in users],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserWithRolesResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    _=Depends(require_admin),
):
    """
    Get a single user by ID.
    
    Admin only.
    """
    user = await service.get_user_by_id(user_id)
    return UserWithRolesResponse(**user)


@router.patch("/{user_id}", response_model=ProfileResponse)
async def update_user(
    user_id: UUID,
    update_data: ProfileUpdate,
    service: UserService = Depends(get_user_service),
    current_user=Depends(require_admin),
):
    """
    Update a user's profile.
    
    Admin only. Cannot change own is_active via this endpoint.
    """
    # Prevent admin from deactivating themselves
    if update_data.is_active is False and str(user_id) == current_user.user_id:
        raise BusinessRuleError(
            "You cannot deactivate your own account",
            "SELF_DEACTIVATION_NOT_ALLOWED"
        )
    
    updated = await service.update_user(user_id, update_data.model_dump(exclude_unset=True))
    return ProfileResponse(**updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    current_user=Depends(require_admin),
):
    """
    Delete a user account.
    
    Admin only. Cannot delete own account.
    Cannot delete the last admin account.
    """
    # Prevent admin from deleting themselves
    if str(user_id) == current_user.user_id:
        raise BusinessRuleError(
            "You cannot delete your own account",
            "SELF_DELETION_NOT_ALLOWED"
        )
    
    await service.delete_user(user_id)
    return None


@router.get("/{user_id}/roles", response_model=list[str])
async def get_user_roles(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    _=Depends(require_admin),
):
    """
    Get roles assigned to a user.
    
    Admin only.
    """
    roles = await service.get_user_roles(user_id)
    return roles


@router.post("/{user_id}/roles", status_code=status.HTTP_201_CREATED)
async def assign_role(
    user_id: UUID,
    assignment: UserRoleAssignment,
    service: UserService = Depends(get_user_service),
    _=Depends(require_admin),
):
    """
    Assign a role to a user.
    
    Admin only.
    """
    await service.assign_role(user_id, assignment.role_code)
    # Clear role cache for this user
    clear_user_role_cache(str(user_id))
    return {"message": f"Role {assignment.role_code} assigned successfully"}


@router.delete("/{user_id}/roles/{role_code}")
async def remove_role(
    user_id: UUID,
    role_code: str,
    service: UserService = Depends(get_user_service),
    current_user=Depends(require_admin),
):
    """
    Remove a role from a user.
    
    Admin only.
    Cannot remove admin role if it would leave zero admins.
    """
    # Check if removing admin role would leave zero admins
    if role_code == "admin":
        admins = await service.get_admin_count()
        if admins <= 1:
            raise BusinessRuleError(
                "Cannot remove the last admin role from the system",
                "LAST_ADMIN_REMOVAL_NOT_ALLOWED"
            )
    
    await service.remove_role(user_id, role_code)
    # Clear role cache for this user
    clear_user_role_cache(str(user_id))
    return {"message": f"Role {role_code} removed successfully"}