"""
================================================================================
Advisor Service for Acadexa API
================================================================================

Business logic for advisor management:
- Advisor notes CRUD
- Advisor assignments management
- Student assignment lookup

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError, ConflictError

logger = logging.getLogger("acadexa.services.advisor")


class AdvisorService:
    """Service for advisor notes and assignments."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize AdvisorService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    # =========================================================================
    # Advisor Notes CRUD
    # =========================================================================
    
    async def get_student_notes(
        self,
        student_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """
        Get all notes for a student.
        
        RLS: Staff can SELECT from advisor_notes.
        
        Args:
            student_id: Student UUID
            limit: Maximum notes to return
            offset: Pagination offset
            
        Returns:
            Tuple of (notes list, total count)
        """
        # Verify student exists
        student_result = self._supabase.table("students")\
            .select("id")\
            .eq("id", str(student_id))\
            .execute()
        
        if not student_result.data:
            raise NotFoundError("Student", str(student_id))
        
        # Get notes with advisor info
        query = self._supabase.table("advisor_notes")\
            .select("*, profiles!advisor_id(id, full_name, email)", count="exact")\
            .eq("student_id", str(student_id))\
            .order("created_at", desc=True)
        
        if limit:
            query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        notes = []
        for note in result.data or []:
            advisor = note.pop("profiles", {})
            notes.append({
                "id": note["id"],
                "student_id": note["student_id"],
                "advisor_id": note["advisor_id"],
                "note": note["note"],
                "created_at": note["created_at"],
                "updated_at": note.get("updated_at"),
                "advisor_name": advisor.get("full_name"),
                "advisor_email": advisor.get("email"),
            })
        
        return notes, result.count or 0
    
    async def create_note(self, student_id: UUID, advisor_id: UUID, note_text: str) -> Dict:
        """
        Create an advisor note.
        
        RLS: Staff can INSERT into advisor_notes (advisor_id set to auth.uid()).
        
        Args:
            student_id: Student UUID
            advisor_id: Advisor UUID (should match authenticated user)
            note_text: Note content
            
        Returns:
            Created note dictionary
        """
        # Verify student exists
        student_result = self._supabase.table("students")\
            .select("id")\
            .eq("id", str(student_id))\
            .execute()
        
        if not student_result.data:
            raise NotFoundError("Student", str(student_id))
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        result = self._supabase.table("advisor_notes")\
            .insert({
                "student_id": str(student_id),
                "advisor_id": str(advisor_id),
                "note": note_text,
                "created_at": now_iso,
                "updated_at": now_iso,
            })\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create note")
        
        logger.info(f"Created note for student {student_id} by advisor {advisor_id}")
        return result.data[0]
    
    async def update_note(self, note_id: UUID, note_text: str, user_id: UUID, is_admin: bool) -> Dict:
        """
        Update an advisor note.
        
        RLS: Author or admin can UPDATE.
        
        Args:
            note_id: Note UUID
            note_text: New note content
            user_id: User attempting update
            is_admin: Whether user is admin
            
        Returns:
            Updated note dictionary
        """
        # Get note to check permissions
        note_result = self._supabase.table("advisor_notes")\
            .select("advisor_id")\
            .eq("id", str(note_id))\
            .execute()
        
        if not note_result.data:
            raise NotFoundError("AdvisorNote", str(note_id))
        
        note = note_result.data[0]
        
        # Check permission: author or admin
        if not is_admin and str(note["advisor_id"]) != str(user_id):
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("Only the note author or admin can update this note")
        
        result = self._supabase.table("advisor_notes")\
            .update({
                "note": note_text,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })\
            .eq("id", str(note_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update note")
        
        logger.info(f"Updated note {note_id}")
        return result.data[0]
    
    async def delete_note(self, note_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """
        Delete an advisor note.
        
        RLS: Author or admin can DELETE.
        
        Args:
            note_id: Note UUID
            user_id: User attempting deletion
            is_admin: Whether user is admin
            
        Returns:
            True if deleted
        """
        # Get note to check permissions
        note_result = self._supabase.table("advisor_notes")\
            .select("advisor_id")\
            .eq("id", str(note_id))\
            .execute()
        
        if not note_result.data:
            raise NotFoundError("AdvisorNote", str(note_id))
        
        note = note_result.data[0]
        
        # Check permission: author or admin
        if not is_admin and str(note["advisor_id"]) != str(user_id):
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("Only the note author or admin can delete this note")
        
        result = self._supabase.table("advisor_notes")\
            .delete()\
            .eq("id", str(note_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted note {note_id}")
        
        return deleted
    
    # =========================================================================
    # Advisor Assignments
    # =========================================================================
    
    async def get_active_assignments(
        self,
        advisor_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None,
    ) -> List[Dict]:
        """
        Get active advisor assignments.
        
        RLS: Staff can SELECT from advisor_assignments.
        
        Args:
            advisor_id: Filter by advisor
            student_id: Filter by student
            
        Returns:
            List of assignment dictionaries
        """
        query = self._supabase.table("advisor_assignments")\
            .select(
                "*, profiles!advisor_id(id, full_name, email), "
                "students!student_id(id, student_code, name, cumulative_gpa, department_id, departments!inner(name_ar))"
            )\
            .eq("is_active", True)
        
        if advisor_id:
            query = query.eq("advisor_id", str(advisor_id))
        
        if student_id:
            query = query.eq("student_id", str(student_id))
        
        result = query.execute()
        
        assignments = []
        for assignment in result.data or []:
            advisor = assignment.pop("profiles", {})
            student = assignment.pop("students", {})
            dept = student.pop("departments", {}) if student else {}
            
            assignments.append({
                "id": assignment["id"],
                "advisor_id": assignment["advisor_id"],
                "advisor_name": advisor.get("full_name"),
                "advisor_email": advisor.get("email"),
                "student_id": assignment["student_id"],
                "student_code": student.get("student_code"),
                "student_name": student.get("name"),
                "student_gpa": student.get("cumulative_gpa"),
                "department_name_ar": dept.get("name_ar"),
                "assigned_at": assignment["assigned_at"],
                "is_active": assignment["is_active"],
            })
        
        return assignments
    
    async def get_assigned_students(self, advisor_id: UUID) -> List[Dict]:
        """
        Get all students assigned to an advisor.
        
        Args:
            advisor_id: Advisor UUID
            
        Returns:
            List of student dictionaries with assignment info
        """
        result = self._supabase.table("advisor_assignments")\
            .select(
                "student_id, assigned_at, "
                "students!student_id(id, student_code, name, cumulative_gpa, current_level, enrollment_year, department_id, departments!inner(name_ar))"
            )\
            .eq("advisor_id", str(advisor_id))\
            .eq("is_active", True)\
            .execute()
        
        students = []
        for assignment in result.data or []:
            student = assignment.pop("students", {})
            dept = student.pop("departments", {}) if student else {}
            
            students.append({
                "student_id": assignment["student_id"],
                "assigned_at": assignment["assigned_at"],
                "student_code": student.get("student_code"),
                "name": student.get("name"),
                "cumulative_gpa": student.get("cumulative_gpa"),
                "current_level": student.get("current_level"),
                "enrollment_year": student.get("enrollment_year"),
                "department_name_ar": dept.get("name_ar"),
            })
        
        return students
    
    async def assign_advisor(self, advisor_id: UUID, student_id: UUID) -> Dict:
        """
        Assign an advisor to a student.
        
        Deactivates any existing active assignment for this student.
        
        Args:
            advisor_id: Advisor UUID
            student_id: Student UUID
            
        Returns:
            Created assignment dictionary
        """
        # Verify advisor exists and has academic_advisor role
        advisor_result = self._supabase.table("profiles")\
            .select("id, is_active")\
            .eq("id", str(advisor_id))\
            .execute()
        
        if not advisor_result.data:
            raise NotFoundError("Advisor", str(advisor_id))
        
        if not advisor_result.data[0].get("is_active", True):
            raise ConflictError("Advisor account is inactive", error_code="ADVISOR_INACTIVE")
        
        # Verify student exists
        student_result = self._supabase.table("students")\
            .select("id")\
            .eq("id", str(student_id))\
            .execute()
        
        if not student_result.data:
            raise NotFoundError("Student", str(student_id))
        
        # Deactivate existing active assignment for this student
        self._supabase.table("advisor_assignments")\
            .update({"is_active": False})\
            .eq("student_id", str(student_id))\
            .eq("is_active", True)\
            .execute()
        
        # Create new assignment
        result = self._supabase.table("advisor_assignments")\
            .insert({
                "advisor_id": str(advisor_id),
                "student_id": str(student_id),
                "is_active": True,
                "assigned_at": datetime.now(timezone.utc).isoformat(),
            })\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create advisor assignment")
        
        logger.info(f"Assigned advisor {advisor_id} to student {student_id}")
        return result.data[0]
    
    async def deactivate_assignment(self, assignment_id: UUID) -> bool:
        """
        Deactivate an advisor assignment.
        
        Args:
            assignment_id: Assignment UUID
            
        Returns:
            True if deactivated
        """
        result = self._supabase.table("advisor_assignments")\
            .update({"is_active": False})\
            .eq("id", str(assignment_id))\
            .execute()
        
        deactivated = len(result.data) > 0
        if deactivated:
            logger.info(f"Deactivated advisor assignment {assignment_id}")
        
        return deactivated
    
    async def get_advisor_list(self) -> List[Dict]:
        """
        Get all users with academic_advisor role.
        
        Returns:
            List of advisor dictionaries
        """
        # Get role ID for academic_advisor
        role_result = self._supabase.table("roles")\
            .select("id")\
            .eq("code", "academic_advisor")\
            .execute()
        
        if not role_result.data:
            return []
        
        role_id = role_result.data[0]["id"]
        
        # Get users with this role
        result = self._supabase.table("user_roles")\
            .select("user_id, profiles!inner(id, full_name, email, is_active)")\
            .eq("role_id", role_id)\
            .execute()
        
        advisors = []
        for item in result.data or []:
            profile = item.get("profiles", {})
            advisors.append({
                "id": profile.get("id"),
                "full_name": profile.get("full_name"),
                "email": profile.get("email"),
                "is_active": profile.get("is_active", True),
            })
        
        return advisors