"""
================================================================================
Advisor Assignments API Endpoints
================================================================================

Endpoints for advisor management:
- Get advisor assignments
- Get assigned students for an advisor
- Assign advisor to student
- Deactivate assignment
- Get advisor list

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_advisor_service, require_admin, require_staff
from app.core.exceptions import NotFoundError, ConflictError
from app.services.advisor_service import AdvisorService

logger = logging.getLogger("acadexa.api.advisor_assignments")

router = APIRouter(prefix="/advisor-assignments", tags=["Advisor Assignments"])


@router.get("")
async def get_assignments(
    advisor_id: Optional[UUID] = Query(None, description="Filter by advisor"),
    student_id: Optional[UUID] = Query(None, description="Filter by student"),
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    """
    Get active advisor assignments.
    
    Accessible by all staff members.
    """
    assignments = await service.get_active_assignments(
        advisor_id=advisor_id,
        student_id=student_id,
    )
    return {"assignments": assignments, "count": len(assignments)}


@router.get("/advisors/list")
async def get_advisor_list(
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    """
    Get all users with academic_advisor role.
    
    Accessible by all staff members.
    """
    advisors = await service.get_advisor_list()
    return {"advisors": advisors, "count": len(advisors)}


@router.get("/users/{user_id}/assigned-students")
async def get_assigned_students(
    user_id: UUID,
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    """
    Get all students assigned to a specific advisor.
    
    Accessible by all staff members.
    """
    students = await service.get_assigned_students(user_id)
    return {"advisor_id": user_id, "students": students, "count": len(students)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def assign_advisor(
    advisor_id: UUID,
    student_id: UUID,
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_admin),
):
    """
    Assign an advisor to a student.
    
    Admin only.
    Deactivates any existing active assignment for the student.
    """
    try:
        assignment = await service.assign_advisor(advisor_id, student_id)
        return {"message": "Advisor assigned successfully", "assignment": assignment}
    except (NotFoundError, ConflictError) as e:
        raise e


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_assignment(
    assignment_id: UUID,
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_admin),
):
    """
    Deactivate an advisor assignment.
    
    Admin only.
    """
    await service.deactivate_assignment(assignment_id)
    return None