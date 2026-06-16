"""
================================================================================
Department Service for Acadexa API
================================================================================

Business logic for department management:
- CRUD operations on departments table
- Department statistics (curriculum count, student count)
- Validation for unique department codes

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from supabase import Client

from app.core.exceptions import ConflictError, NotFoundError

logger = logging.getLogger("acadexa.services.department")


class DepartmentService:
    """Service for department management with RLS-compliant client."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize DepartmentService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get all departments with pagination and filtering.
        """
        query = self._supabase.table("departments").select("*", count="exact")
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        if search:
            query = query.or_(
                f"code.ilike.%{search}%,"
                f"name_ar.ilike.%{search}%,"
                f"name_en.ilike.%{search}%"
            )
        
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1).order("code")
        
        result = query.execute()
        
        return result.data or [], result.count or 0
    
    async def get_by_id(self, department_id: UUID) -> Dict:
        """
        Get a department by ID.
        """
        result = self._supabase.table("departments")\
            .select("*")\
            .eq("id", str(department_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("Department", str(department_id))
        
        return result.data[0]
    
    async def get_by_code(self, code: str) -> Optional[Dict]:
        """
        Get a department by code.
        """
        result = self._supabase.table("departments")\
            .select("*")\
            .eq("code", code.upper())\
            .execute()
        
        return result.data[0] if result.data else None
    
    async def create(self, department: Dict) -> Dict:
        """
        Create a new department.
        """
        existing = await self.get_by_code(department["code"])
        if existing:
            raise ConflictError(
                f"Department with code '{department['code']}' already exists",
                error_code="DEPARTMENT_CODE_EXISTS"
            )
        
        result = self._supabase.table("departments")\
            .insert(department)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create department")
        
        logger.info(f"Created department: {department['code']}")
        return result.data[0]
    
    async def update(self, department_id: UUID, update_data: Dict) -> Dict:
        """
        Update an existing department.
        """
        await self.get_by_id(department_id)
        
        if not update_data:
            return await self.get_by_id(department_id)
        
        result = self._supabase.table("departments")\
            .update(update_data)\
            .eq("id", str(department_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update department")
        
        logger.info(f"Updated department: {department_id}")
        return result.data[0]
    
    async def delete(self, department_id: UUID) -> bool:
        """
        Delete a department.
        """
        await self.get_by_id(department_id)
        
        student_result = self._supabase.table("students")\
            .select("id", count="exact")\
            .eq("department_id", str(department_id))\
            .limit(1)\
            .execute()
        
        if student_result.count and student_result.count > 0:
            raise ConflictError(
                "Cannot delete department with associated students",
                error_code="DEPARTMENT_HAS_STUDENTS"
            )
        
        result = self._supabase.table("departments")\
            .delete()\
            .eq("id", str(department_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted department: {department_id}")
        
        return deleted
    
    async def get_with_stats(self, department_id: UUID) -> Dict:
        """
        Get department with statistics (curriculum count, student count).
        
        FUTURE OPTIMIZATION:
        Consider adding index on curricula.department_id for faster department filtering
        CREATE INDEX idx_curricula_department ON curricula(department_id);
        Not required for MVP - acceptable for moderate data volumes.
        """
        department = await self.get_by_id(department_id)
        
        curriculum_result = self._supabase.table("curricula")\
            .select("id", count="exact")\
            .eq("department_id", str(department_id))\
            .execute()
        
        student_result = self._supabase.table("students")\
            .select("id", count="exact")\
            .eq("department_id", str(department_id))\
            .execute()
        
        active_student_result = self._supabase.table("students")\
            .select("id", count="exact")\
            .eq("department_id", str(department_id))\
            .eq("is_active", True)\
            .execute()
        
        department["curriculum_count"] = curriculum_result.count or 0
        department["student_count"] = student_result.count or 0
        department["active_student_count"] = active_student_result.count or 0
        
        return department