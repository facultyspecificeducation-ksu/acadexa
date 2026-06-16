"""
================================================================================
User Service for Acadexa API
================================================================================

Business logic for user management:
- List users with roles
- Get user by ID
- Update user profile
- Delete user
- Role assignment and removal

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from supabase import Client

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.supabase import get_service_role_client

logger = logging.getLogger("acadexa.services.user")


class UserService:
    """
    Service for user management with RLS-compliant client.
    
    Note: Some operations (delete_user) require service_role client for auth.admin access.
    Those operations explicitly use get_service_role_client() only when needed.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize UserService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
                           Used for RLS-compliant read/write operations.
        """
        self._supabase = supabase_client
    
    async def get_users(
        self,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get paginated list of users with roles.
        
        RLS: Staff can SELECT from profiles (via admin policy).
        
        Args:
            is_active: Filter by active status
            role: Filter by role code
            search: Search by name or email
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (users list, total count)
        """
        offset = (page - 1) * limit
        
        query = self._supabase.table("profiles")\
            .select("*", count="exact")
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,",
                f"email.ilike.%{search}%"
            )
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        
        result = query.execute()
        
        users = result.data or []
        total = result.count or 0
        
        # Get roles for each user
        for user in users:
            roles_result = self._supabase.table("user_roles")\
                .select("roles!inner(code)")\
                .eq("user_id", user["id"])\
                .execute()
            
            roles = [r["roles"]["code"] for r in (roles_result.data or []) if r.get("roles")]
            user["roles"] = roles
        
        # Filter by role if specified
        if role:
            users = [u for u in users if role in u.get("roles", [])]
            total = len(users)
        
        return users, total
    
    async def get_user_by_id(self, user_id: UUID) -> Dict:
        """
        Get a single user by ID with roles.
        
        RLS: Admin can SELECT any profile.
        
        Args:
            user_id: User UUID
            
        Returns:
            User dictionary with roles
        """
        result = self._supabase.table("profiles")\
            .select("*")\
            .eq("id", str(user_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("User", str(user_id))
        
        user = result.data[0]
        
        roles_result = self._supabase.table("user_roles")\
            .select("roles!inner(code)")\
            .eq("user_id", str(user_id))\
            .execute()
        
        user["roles"] = [r["roles"]["code"] for r in (roles_result.data or []) if r.get("roles")]
        
        return user
    
    async def update_user(self, user_id: UUID, update_data: Dict) -> Dict:
        """
        Update a user's profile.
        
        RLS: Admin can UPDATE profiles.
        
        Args:
            user_id: User UUID
            update_data: Fields to update
            
        Returns:
            Updated user dictionary
        """
        await self.get_user_by_id(user_id)
        
        # Remove None values
        data = {k: v for k, v in update_data.items() if v is not None}
        
        if not data:
            return await self.get_user_by_id(user_id)
        
        result = self._supabase.table("profiles")\
            .update(data)\
            .eq("id", str(user_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update user")
        
        logger.info(f"Updated user {user_id}")
        return result.data[0]
    
    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user account.
        
        Note: This operation requires service_role client for auth.admin.delete_user.
        RLS policy does not cover auth.users deletion.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if deleted
        """
        user = await self.get_user_by_id(user_id)
        
        # Check if this is an admin
        if "admin" in user.get("roles", []):
            admin_count = await self.get_admin_count()
            if admin_count <= 1:
                raise BusinessRuleError(
                    "Cannot delete the last admin account",
                    "LAST_ADMIN_DELETION_NOT_ALLOWED"
                )
        
        # Delete from auth.users (requires service_role)
        # This is the only operation that needs service_role client
        try:
            service_client = get_service_role_client()
            service_client.auth.admin.delete_user(str(user_id))
        except Exception as e:
            logger.error(f"Failed to delete auth user {user_id}: {e}")
            raise Exception(f"Failed to delete user: {str(e)}")
        
        logger.info(f"Deleted user {user_id}")
        return True
    
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """
        Get roles for a user.
        
        RLS: Admin can SELECT from user_roles.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of role codes
        """
        await self.get_user_by_id(user_id)
        
        result = self._supabase.table("user_roles")\
            .select("roles!inner(code)")\
            .eq("user_id", str(user_id))\
            .execute()
        
        return [r["roles"]["code"] for r in (result.data or []) if r.get("roles")]
    
    async def assign_role(self, user_id: UUID, role_code: str) -> Dict:
        """
        Assign a role to a user.
        
        RLS: Admin can INSERT into user_roles.
        
        Args:
            user_id: User UUID
            role_code: Role code (admin, academic_advisor)
            
        Returns:
            Created assignment dictionary
        """
        # Get role ID
        role_result = self._supabase.table("roles")\
            .select("id")\
            .eq("code", role_code)\
            .execute()
        
        if not role_result.data:
            raise NotFoundError("Role", role_code)
        
        role_id = role_result.data[0]["id"]
        
        # Check if already assigned
        existing = self._supabase.table("user_roles")\
            .select("id")\
            .eq("user_id", str(user_id))\
            .eq("role_id", role_id)\
            .execute()
        
        if existing.data:
            return {"message": "Role already assigned"}
        
        # Assign role
        result = self._supabase.table("user_roles")\
            .insert({
                "user_id": str(user_id),
                "role_id": role_id,
            })\
            .execute()
        
        if not result.data:
            raise Exception("Failed to assign role")
        
        logger.info(f"Assigned role {role_code} to user {user_id}")
        return result.data[0]
    
    async def remove_role(self, user_id: UUID, role_code: str) -> bool:
        """
        Remove a role from a user.
        
        RLS: Admin can DELETE from user_roles.
        
        Args:
            user_id: User UUID
            role_code: Role code to remove
            
        Returns:
            True if removed
        """
        # Get role ID
        role_result = self._supabase.table("roles")\
            .select("id")\
            .eq("code", role_code)\
            .execute()
        
        if not role_result.data:
            raise NotFoundError("Role", role_code)
        
        role_id = role_result.data[0]["id"]
        
        # Remove role
        result = self._supabase.table("user_roles")\
            .delete()\
            .eq("user_id", str(user_id))\
            .eq("role_id", role_id)\
            .execute()
        
        removed = len(result.data) > 0
        if removed:
            logger.info(f"Removed role {role_code} from user {user_id}")
        
        return removed
    
    async def get_admin_count(self) -> int:
        """
        Get total number of admin users.
        
        RLS: Admin can SELECT from user_roles.
        
        Returns:
            Count of users with admin role
        """
        # Get role ID for admin
        role_result = self._supabase.table("roles")\
            .select("id")\
            .eq("code", "admin")\
            .execute()
        
        if not role_result.data:
            return 0
        
        role_id = role_result.data[0]["id"]
        
        result = self._supabase.table("user_roles")\
            .select("user_id", count="exact")\
            .eq("role_id", role_id)\
            .execute()
        
        return result.count or 0