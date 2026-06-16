"""
================================================================================
Course Service for Acadexa API
================================================================================

Business logic for course management:
- Curriculum courses CRUD
- Course prerequisites management
- Elective groups management
- Cross-curriculum course search

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

logger = logging.getLogger("acadexa.services.course")


class CourseService:
    """Service for course and prerequisite management."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize CourseService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    # =========================================================================
    # Curriculum Courses CRUD
    # =========================================================================
    
    async def get_curriculum_courses(
        self,
        curriculum_id: UUID,
        level: Optional[int] = None,
        term: Optional[str] = None,
        category: Optional[str] = None,
        is_field_training: Optional[bool] = None,
        is_graduation_project: Optional[bool] = None,
        is_community_issues_course: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> List[Dict]:
        """
        Get all courses for a curriculum with filtering.
        
        Args:
            curriculum_id: Curriculum UUID
            level: Filter by level (1-4)
            term: Filter by term (fall, spring, summer)
            category: Filter by category
            is_field_training: Filter by field training flag
            is_graduation_project: Filter by graduation project flag
            is_community_issues_course: Filter by community issues flag
            is_active: Filter by active status
            
        Returns:
            List of course dictionaries
        """
        query = self._supabase.table("curriculum_courses")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .order("level", "term")
        
        if level:
            query = query.eq("level", level)
        
        if term:
            query = query.eq("term", term)
        
        if category:
            query = query.eq("category", category)
        
        if is_field_training is not None:
            query = query.eq("is_field_training", is_field_training)
        
        if is_graduation_project is not None:
            query = query.eq("is_graduation_project", is_graduation_project)
        
        if is_community_issues_course is not None:
            query = query.eq("is_community_issues_course", is_community_issues_course)
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.execute()
        
        return result.data or []
    
    async def get_course_by_id(self, course_id: UUID) -> Dict:
        """
        Get a single curriculum course by ID with prerequisites.
        
        Args:
            course_id: Course UUID
            
        Returns:
            Course dictionary with prerequisites list
        """
        result = self._supabase.table("curriculum_courses")\
            .select("*, curricula!inner(id, name_ar, regulation_year, department_id, departments!inner(name_ar))")\
            .eq("id", str(course_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("Course", str(course_id))
        
        course = result.data[0]
        
        # Flatten curriculum and department data
        curriculum = course.pop("curricula", {})
        dept = curriculum.pop("departments", {}) if curriculum else {}
        
        course["curriculum_id"] = curriculum.get("id")
        course["curriculum_name_ar"] = curriculum.get("name_ar")
        course["regulation_year"] = curriculum.get("regulation_year")
        course["department_name_ar"] = dept.get("name_ar")
        
        # Get prerequisites
        prereq_result = self._supabase.table("course_prerequisites")\
            .select("*, required_course:required_course_id(id, course_code, name_ar, credit_hours)")\
            .eq("course_id", str(course_id))\
            .execute()
        
        prerequisites = []
        for prereq in prereq_result.data or []:
            required = prereq.pop("required_course", {})
            prerequisites.append({
                "id": prereq["id"],
                "required_course_id": prereq["required_course_id"],
                "minimum_grade": prereq.get("minimum_grade"),
                "course_code": required.get("course_code"),
                "name_ar": required.get("name_ar"),
                "credit_hours": required.get("credit_hours"),
            })
        
        course["prerequisites"] = prerequisites
        
        return course
    
    async def create_course(self, curriculum_id: UUID, course_data: Dict) -> Dict:
        """
        Add a course to a curriculum.
        
        Args:
            curriculum_id: Curriculum UUID
            course_data: Course creation data
            
        Returns:
            Created course dictionary
            
        Raises:
            ConflictError: If course_code already exists in this curriculum
        """
        # Check for duplicate course_code within curriculum (allow null course_code)
        course_code = course_data.get("course_code")
        if course_code:
            existing = self._supabase.table("curriculum_courses")\
                .select("id")\
                .eq("curriculum_id", str(curriculum_id))\
                .eq("course_code", course_code)\
                .execute()
            
            if existing.data:
                raise ConflictError(
                    f"Course with code '{course_code}' already exists in this curriculum",
                    error_code="COURSE_CODE_EXISTS"
                )
        
        # Add curriculum_id to data
        course_data["curriculum_id"] = str(curriculum_id)
        
        result = self._supabase.table("curriculum_courses")\
            .insert(course_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create course")
        
        logger.info(f"Created course {result.data[0]['id']} in curriculum {curriculum_id}")
        return result.data[0]
    
    async def update_course(self, course_id: UUID, update_data: Dict) -> Dict:
        """
        Update a curriculum course.
        
        Args:
            course_id: Course UUID
            update_data: Fields to update
            
        Returns:
            Updated course dictionary
        """
        # Check if exists
        await self.get_course_by_id(course_id)
        
        # Remove None values
        data = {k: v for k, v in update_data.items() if v is not None}
        
        if not data:
            return await self.get_course_by_id(course_id)
        
        # Check if changing credit_hours would affect existing student records
        if "credit_hours" in data:
            student_count = self._supabase.table("student_courses")\
                .select("id", count="exact")\
                .eq("curriculum_course_id", str(course_id))\
                .execute()
            
            if student_count.count and student_count.count > 0:
                logger.warning(f"Updating credit_hours for course {course_id} affects {student_count.count} student records")
        
        result = self._supabase.table("curriculum_courses")\
            .update(data)\
            .eq("id", str(course_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update course")
        
        logger.info(f"Updated course {course_id}")
        return result.data[0]
    
    async def delete_course(self, course_id: UUID) -> bool:
        """
        Delete a curriculum course.
        
        Args:
            course_id: Course UUID
            
        Returns:
            True if deleted
            
        Raises:
            ConflictError: If course is referenced by student records
        """
        # Check if exists
        await self.get_course_by_id(course_id)
        
        # Check if course is referenced by student records
        student_result = self._supabase.table("student_courses")\
            .select("id", count="exact")\
            .eq("curriculum_course_id", str(course_id))\
            .limit(1)\
            .execute()
        
        if student_result.count and student_result.count > 0:
            raise ConflictError(
                "Cannot delete course referenced by student records",
                error_code="COURSE_HAS_STUDENT_RECORDS"
            )
        
        # Delete course (cascades to prerequisites and elective groups)
        result = self._supabase.table("curriculum_courses")\
            .delete()\
            .eq("id", str(course_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted course {course_id}")
        
        return deleted
    
    # =========================================================================
    # Cross-Curriculum Course Search
    # =========================================================================
    
    async def search_courses(
        self,
        search: Optional[str] = None,
        curriculum_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        category: Optional[str] = None,
        level: Optional[int] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Search courses across all curricula.
        
        Args:
            search: Search by course_code or name_ar
            curriculum_id: Filter by curriculum
            department_id: Filter by department (via curriculum)
            category: Filter by category
            level: Filter by level
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (courses list, total count)
        """
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        query = self._supabase.table("curriculum_courses")\
            .select(
                "*, curricula!inner(id, name_ar, regulation_year, department_id, departments!inner(id, name_ar, name_en))",
                count="exact"
            )
        
        if search:
            query = query.or_(
                f"course_code.ilike.%{search}%,"
                f"name_ar.ilike.%{search}%"
            )
        
        if curriculum_id:
            query = query.eq("curriculum_id", str(curriculum_id))
        
        if department_id:
            query = query.eq("curricula.department_id", str(department_id))
        
        if category:
            query = query.eq("category", category)
        
        if level:
            query = query.eq("level", level)
        
        query = query.order("curricula.regulation_year", desc=True).order("level", "term")
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        courses = result.data or []
        total = result.count or 0
        
        # Flatten nested structures
        for course in courses:
            curriculum = course.pop("curricula", {})
            dept = curriculum.pop("departments", {}) if curriculum else {}
            
            course["curriculum_id"] = curriculum.get("id")
            course["curriculum_name_ar"] = curriculum.get("name_ar")
            course["regulation_year"] = curriculum.get("regulation_year")
            course["department_id"] = dept.get("id")
            course["department_name_ar"] = dept.get("name_ar")
            course["department_name_en"] = dept.get("name_en")
        
        return courses, total
    
    # =========================================================================
    # Course Prerequisites Management
    # =========================================================================
    
    async def get_course_prerequisites(self, course_id: UUID) -> List[Dict]:
        """
        Get all prerequisites for a course.
        
        Args:
            course_id: Course UUID
            
        Returns:
            List of prerequisite dictionaries
        """
        # Verify course exists
        await self.get_course_by_id(course_id)
        
        result = self._supabase.table("course_prerequisites")\
            .select("*, required_course:required_course_id(id, course_code, name_ar, credit_hours, level, term)")\
            .eq("course_id", str(course_id))\
            .execute()
        
        prerequisites = []
        for prereq in result.data or []:
            required = prereq.pop("required_course", {})
            prerequisites.append({
                "id": prereq["id"],
                "required_course_id": prereq["required_course_id"],
                "minimum_grade": prereq.get("minimum_grade"),
                "course_code": required.get("course_code"),
                "name_ar": required.get("name_ar"),
                "credit_hours": required.get("credit_hours"),
                "level": required.get("level"),
                "term": required.get("term"),
            })
        
        return prerequisites
    
    async def add_prerequisite(
        self,
        course_id: UUID,
        required_course_id: UUID,
        minimum_grade: Optional[str] = None,
    ) -> Dict:
        """
        Add a prerequisite to a course.
        
        Args:
            course_id: Course UUID
            required_course_id: Required course UUID
            minimum_grade: Minimum grade required (optional)
            
        Returns:
            Created prerequisite dictionary
            
        Raises:
            ValidationError: If course_id equals required_course_id
            ConflictError: If prerequisite already exists
        """
        if str(course_id) == str(required_course_id):
            raise ValidationError("A course cannot be a prerequisite of itself", field="required_course_id")
        
        # Verify both courses exist and belong to same curriculum
        course = await self.get_course_by_id(course_id)
        required = await self.get_course_by_id(required_course_id)
        
        if course.get("curriculum_id") != required.get("curriculum_id"):
            raise ValidationError("Both courses must belong to the same curriculum", field="required_course_id")
        
        # Validate minimum_grade exists in grade_scale if provided
        if minimum_grade:
            grade_result = self._supabase.table("grade_scale")\
                .select("grade_letter")\
                .eq("grade_letter", minimum_grade)\
                .execute()
            
            if not grade_result.data:
                raise ValidationError(f"Invalid grade letter: {minimum_grade}", field="minimum_grade")
        
        # Check if prerequisite already exists
        existing = self._supabase.table("course_prerequisites")\
            .select("id")\
            .eq("course_id", str(course_id))\
            .eq("required_course_id", str(required_course_id))\
            .execute()
        
        if existing.data:
            raise ConflictError("Prerequisite already exists", error_code="PREREQUISITE_EXISTS")
        
        # Create prerequisite
        result = self._supabase.table("course_prerequisites")\
            .insert({
                "course_id": str(course_id),
                "required_course_id": str(required_course_id),
                "minimum_grade": minimum_grade,
            })\
            .execute()
        
        if not result.data:
            raise Exception("Failed to add prerequisite")
        
        logger.info(f"Added prerequisite {required_course_id} to course {course_id}")
        return result.data[0]
    
    async def remove_prerequisite(self, course_id: UUID, required_course_id: UUID) -> bool:
        """
        Remove a prerequisite from a course.
        
        Args:
            course_id: Course UUID
            required_course_id: Required course UUID
            
        Returns:
            True if removed
        """
        result = self._supabase.table("course_prerequisites")\
            .delete()\
            .eq("course_id", str(course_id))\
            .eq("required_course_id", str(required_course_id))\
            .execute()
        
        removed = len(result.data) > 0
        if removed:
            logger.info(f"Removed prerequisite {required_course_id} from course {course_id}")
        
        return removed
    
    # =========================================================================
    # Elective Groups Management
    # =========================================================================
    
    async def get_elective_groups(self, curriculum_id: UUID) -> List[Dict]:
        """
        Get all elective groups for a curriculum with their courses.
        
        Args:
            curriculum_id: Curriculum UUID
            
        Returns:
            List of elective group dictionaries with nested courses
        """
        # Verify curriculum exists
        from app.services.curriculum_service import CurriculumService
        curriculum_service = CurriculumService(self._supabase)
        await curriculum_service.get_curriculum_by_id(curriculum_id)
        
        # Get groups
        groups_result = self._supabase.table("elective_groups")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        groups = groups_result.data or []
        
        # Get courses for each group
        for group in groups:
            courses_result = self._supabase.table("elective_group_courses")\
                .select("course_id, curriculum_courses!inner(id, course_code, name_ar, credit_hours, level, term)")\
                .eq("group_id", group["id"])\
                .execute()
            
            courses = []
            for gc in courses_result.data or []:
                course = gc.get("curriculum_courses", {})
                courses.append({
                    "course_id": gc["course_id"],
                    "course_code": course.get("course_code"),
                    "name_ar": course.get("name_ar"),
                    "credit_hours": course.get("credit_hours"),
                    "level": course.get("level"),
                    "term": course.get("term"),
                })
            
            group["courses"] = courses
            group["course_count"] = len(courses)
        
        return groups
    
    async def create_elective_group(self, curriculum_id: UUID, group_data: Dict) -> Dict:
        """
        Create an elective group.
        
        Args:
            curriculum_id: Curriculum UUID
            group_data: Group creation data
            
        Returns:
            Created group dictionary
        """
        group_data["curriculum_id"] = str(curriculum_id)
        
        result = self._supabase.table("elective_groups")\
            .insert(group_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create elective group")
        
        logger.info(f"Created elective group {result.data[0]['id']} for curriculum {curriculum_id}")
        return result.data[0]
    
    async def update_elective_group(self, group_id: UUID, update_data: Dict) -> Dict:
        """
        Update an elective group.
        
        Args:
            group_id: Group UUID
            update_data: Fields to update
            
        Returns:
            Updated group dictionary
        """
        # Remove None values
        data = {k: v for k, v in update_data.items() if v is not None}
        
        if not data:
            result = self._supabase.table("elective_groups")\
                .select("*")\
                .eq("id", str(group_id))\
                .execute()
            return result.data[0] if result.data else {}
        
        result = self._supabase.table("elective_groups")\
            .update(data)\
            .eq("id", str(group_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update elective group")
        
        logger.info(f"Updated elective group {group_id}")
        return result.data[0]
    
    async def delete_elective_group(self, group_id: UUID) -> bool:
        """
        Delete an elective group.
        
        Args:
            group_id: Group UUID
            
        Returns:
            True if deleted
        """
        result = self._supabase.table("elective_groups")\
            .delete()\
            .eq("id", str(group_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted elective group {group_id}")
        
        return deleted
    
    async def add_course_to_elective_group(self, group_id: UUID, course_id: UUID) -> Dict:
        """
        Add a course to an elective group.
        
        Args:
            group_id: Group UUID
            course_id: Course UUID
            
        Returns:
            Created association dictionary
            
        Raises:
            ValidationError: If course doesn't belong to same curriculum
        """
        # Get group to check curriculum
        group_result = self._supabase.table("elective_groups")\
            .select("curriculum_id")\
            .eq("id", str(group_id))\
            .execute()
        
        if not group_result.data:
            raise NotFoundError("ElectiveGroup", str(group_id))
        
        group_curriculum_id = group_result.data[0]["curriculum_id"]
        
        # Get course to check curriculum
        course = await self.get_course_by_id(course_id)
        
        if course.get("curriculum_id") != group_curriculum_id:
            raise ValidationError("Course must belong to the same curriculum as the group", field="course_id")
        
        # Check if already in group
        existing = self._supabase.table("elective_group_courses")\
            .select("group_id, course_id")\
            .eq("group_id", str(group_id))\
            .eq("course_id", str(course_id))\
            .execute()
        
        if existing.data:
            raise ConflictError("Course already in this group", error_code="COURSE_ALREADY_IN_GROUP")
        
        # Add to group
        result = self._supabase.table("elective_group_courses")\
            .insert({
                "group_id": str(group_id),
                "course_id": str(course_id),
            })\
            .execute()
        
        if not result.data:
            raise Exception("Failed to add course to group")
        
        logger.info(f"Added course {course_id} to elective group {group_id}")
        return result.data[0]
    
    async def remove_course_from_elective_group(self, group_id: UUID, course_id: UUID) -> bool:
        """
        Remove a course from an elective group.
        
        Args:
            group_id: Group UUID
            course_id: Course UUID
            
        Returns:
            True if removed
        """
        result = self._supabase.table("elective_group_courses")\
            .delete()\
            .eq("group_id", str(group_id))\
            .eq("course_id", str(course_id))\
            .execute()
        
        removed = len(result.data) > 0
        if removed:
            logger.info(f"Removed course {course_id} from elective group {group_id}")
        
        return removed