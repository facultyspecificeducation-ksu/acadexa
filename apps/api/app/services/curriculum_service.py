"""
================================================================================
Curriculum Service for Acadexa API
================================================================================

Business logic for curriculum management:
- Curriculum CRUD operations
- Graduation requirements management
- Academic rules management
- Curriculum validation (unique department+year)

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from supabase import Client

from app.core.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger("acadexa.services.curriculum")


class CurriculumService:
    """Service for curriculum and regulation management."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize CurriculumService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    # =========================================================================
    # Curriculum CRUD
    # =========================================================================
    
    async def get_curricula(
        self,
        department_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get paginated list of curricula.
        
        Args:
            department_id: Filter by department
            is_active: Filter by active status
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (curricula list, total count)
        """
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        query = self._supabase.table("curricula")\
            .select("*, departments(id, code, name_ar, name_en)", count="exact")\
            .order("regulation_year", desc=True)
        
        if department_id:
            query = query.eq("department_id", str(department_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        curricula = result.data or []
        total = result.count or 0
        
        # Flatten department data
        for curriculum in curricula:
            dept = curriculum.pop("departments", {})
            curriculum["department_code"] = dept.get("code")
            curriculum["department_name_ar"] = dept.get("name_ar")
            curriculum["department_name_en"] = dept.get("name_en")
        
        return curricula, total
    
    async def get_curriculum_by_id(self, curriculum_id: UUID) -> Dict:
        """
        Get a single curriculum by ID with nested requirements.
        
        Args:
            curriculum_id: Curriculum UUID
            
        Returns:
            Curriculum dictionary with graduation_requirements and academic_rules
        """
        result = self._supabase.table("curricula")\
            .select("*, departments(id, code, name_ar, name_en)")\
            .eq("id", str(curriculum_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("Curriculum", str(curriculum_id))
        
        curriculum = result.data[0]
        
        # Flatten department data
        dept = curriculum.pop("departments", {})
        curriculum["department_code"] = dept.get("code")
        curriculum["department_name_ar"] = dept.get("name_ar")
        curriculum["department_name_en"] = dept.get("name_en")
        
        # Get graduation requirements
        grad_req_result = self._supabase.table("graduation_requirements")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        curriculum["graduation_requirements"] = grad_req_result.data[0] if grad_req_result.data else None
        
        # Get academic rules
        rules_result = self._supabase.table("academic_rules")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        curriculum["academic_rules"] = rules_result.data[0] if rules_result.data else None
        
        return curriculum
    
    async def create_curriculum(self, curriculum_data: Dict) -> Dict:
        """
        Create a new curriculum.
        
        Args:
            curriculum_data: Curriculum creation data
            
        Returns:
            Created curriculum dictionary
            
        Raises:
            ConflictError: If department_id + regulation_year already exists
        """
        # Check for duplicate (department_id, regulation_year)
        existing = self._supabase.table("curricula")\
            .select("id")\
            .eq("department_id", curriculum_data["department_id"])\
            .eq("regulation_year", curriculum_data["regulation_year"])\
            .execute()
        
        if existing.data:
            raise ConflictError(
                f"Curriculum for department {curriculum_data['department_id']} and year {curriculum_data['regulation_year']} already exists",
                error_code="CURRICULUM_EXISTS"
            )
        
        result = self._supabase.table("curricula")\
            .insert(curriculum_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create curriculum")
        
        logger.info(f"Created curriculum {result.data[0]['id']} for year {curriculum_data['regulation_year']}")
        return result.data[0]
    
    async def update_curriculum(self, curriculum_id: UUID, update_data: Dict) -> Dict:
        """
        Update an existing curriculum.
        
        Args:
            curriculum_id: Curriculum UUID
            update_data: Fields to update
            
        Returns:
            Updated curriculum dictionary
        """
        # Check if exists
        await self.get_curriculum_by_id(curriculum_id)
        
        # Remove None values
        data = {k: v for k, v in update_data.items() if v is not None}
        
        if not data:
            return await self.get_curriculum_by_id(curriculum_id)
        
        result = self._supabase.table("curricula")\
            .update(data)\
            .eq("id", str(curriculum_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update curriculum")
        
        logger.info(f"Updated curriculum {curriculum_id}")
        return result.data[0]
    
    async def delete_curriculum(self, curriculum_id: UUID) -> bool:
        """
        Delete a curriculum.
        
        Note: Cascades to curriculum_courses, elective_groups, graduation_requirements, academic_rules.
        
        Args:
            curriculum_id: Curriculum UUID
            
        Returns:
            True if deleted
            
        Raises:
            ConflictError: If curriculum has associated students
        """
        # Check if exists
        await self.get_curriculum_by_id(curriculum_id)
        
        # Check if curriculum has students
        student_result = self._supabase.table("students")\
            .select("id", count="exact")\
            .eq("curriculum_id", str(curriculum_id))\
            .limit(1)\
            .execute()
        
        if student_result.count and student_result.count > 0:
            raise ConflictError(
                "Cannot delete curriculum with associated students",
                error_code="CURRICULUM_HAS_STUDENTS"
            )
        
        # Delete curriculum (cascades to related tables)
        result = self._supabase.table("curricula")\
            .delete()\
            .eq("id", str(curriculum_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted curriculum {curriculum_id}")
        
        return deleted
    
    # =========================================================================
    # Graduation Requirements
    # =========================================================================
    
    async def get_graduation_requirements(self, curriculum_id: UUID) -> Dict:
        """
        Get graduation requirements for a curriculum.
        
        Args:
            curriculum_id: Curriculum UUID
            
        Returns:
            Graduation requirements dictionary
        """
        # Verify curriculum exists
        await self.get_curriculum_by_id(curriculum_id)
        
        result = self._supabase.table("graduation_requirements")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        if not result.data:
            return {}
        
        return result.data[0]
    
    async def upsert_graduation_requirements(self, curriculum_id: UUID, requirements_data: Dict) -> Dict:
        """
        Create or replace graduation requirements for a curriculum.
        
        Args:
            curriculum_id: Curriculum UUID
            requirements_data: Graduation requirements data
            
        Returns:
            Created or updated requirements dictionary
        """
        # Verify curriculum exists
        await self.get_curriculum_by_id(curriculum_id)
        
        # Add curriculum_id to data
        requirements_data["curriculum_id"] = str(curriculum_id)
        
        # Use upsert (insert or update on conflict)
        result = self._supabase.table("graduation_requirements")\
            .upsert(requirements_data, on_conflict="curriculum_id")\
            .execute()
        
        if not result.data:
            raise Exception("Failed to save graduation requirements")
        
        logger.info(f"Saved graduation requirements for curriculum {curriculum_id}")
        return result.data[0]
    
    # =========================================================================
    # Academic Rules
    # =========================================================================
    
    async def get_academic_rules(self, curriculum_id: UUID) -> Dict:
        """
        Get academic rules for a curriculum.
        
        Args:
            curriculum_id: Curriculum UUID
            
        Returns:
            Academic rules dictionary
        """
        # Verify curriculum exists
        await self.get_curriculum_by_id(curriculum_id)
        
        result = self._supabase.table("academic_rules")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        if not result.data:
            return {}
        
        return result.data[0]
    
    async def upsert_academic_rules(self, curriculum_id: UUID, rules_data: Dict) -> Dict:
        """
        Create or replace academic rules for a curriculum.
        
        Args:
            curriculum_id: Curriculum UUID
            rules_data: Academic rules data
            
        Returns:
            Created or updated rules dictionary
        """
        # Verify curriculum exists
        await self.get_curriculum_by_id(curriculum_id)
        
        # Validate level progression
        level_2 = rules_data.get("level_2_min_hours", 0)
        level_3 = rules_data.get("level_3_min_hours", 0)
        level_4 = rules_data.get("level_4_min_hours", 0)
        
        if level_3 < level_2:
            raise ValidationError("level_3_min_hours must be >= level_2_min_hours", field="level_3_min_hours")
        
        if level_4 < level_3:
            raise ValidationError("level_4_min_hours must be >= level_3_min_hours", field="level_4_min_hours")
        
        # Add curriculum_id to data
        rules_data["curriculum_id"] = str(curriculum_id)
        
        # Use upsert (insert or update on conflict)
        result = self._supabase.table("academic_rules")\
            .upsert(rules_data, on_conflict="curriculum_id")\
            .execute()
        
        if not result.data:
            raise Exception("Failed to save academic rules")
        
        logger.info(f"Saved academic rules for curriculum {curriculum_id}")
        return result.data[0]
    
    # =========================================================================
    # All Academic Rules (for comparison table)
    # =========================================================================
    
    async def get_all_academic_rules(
        self,
        department_id: Optional[UUID] = None,
    ) -> List[Dict]:
        """
        Get all academic rules with curriculum and department info.
        
        Used for the AcademicLoadRulesPage comparison table.
        
        Args:
            department_id: Filter by department
            
        Returns:
            List of academic rules with curriculum context
        """
        query = self._supabase.table("academic_rules")\
            .select("*, curricula!inner(id, name_ar, regulation_year, department_id, departments!inner(id, name_ar, name_en))")
        
        if department_id:
            query = query.eq("curricula.department_id", str(department_id))
        
        result = query.order("curricula.regulation_year", desc=True).execute()
        
        rules_list = result.data or []
        
        # Flatten nested structures
        for rules in rules_list:
            curriculum = rules.pop("curricula", {})
            dept = curriculum.pop("departments", {}) if curriculum else {}
            
            rules["curriculum_id"] = curriculum.get("id")
            rules["curriculum_name_ar"] = curriculum.get("name_ar")
            rules["regulation_year"] = curriculum.get("regulation_year")
            rules["department_id"] = dept.get("id")
            rules["department_name_ar"] = dept.get("name_ar")
            rules["department_name_en"] = dept.get("name_en")
        
        return rules_list