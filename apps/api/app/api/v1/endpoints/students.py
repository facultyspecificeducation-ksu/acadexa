"""
================================================================================
Students API Endpoints
================================================================================

CRUD operations and data retrieval for students.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_student_service, require_admin, require_staff
from app.core.exceptions import NotFoundError
from app.schemas.student import (
    StudentListResponse,
    StudentResponse,
    StudentUpdateRequest,
    TranscriptResponse,
    AcademicPlanResponse,
    GraduationStatusResponse,
    PrerequisiteStatusResponse,
)
from app.services.student_service import StudentService

logger = logging.getLogger("acadexa.api.students")

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=StudentListResponse)
async def list_students(
    search: Optional[str] = Query(None, description="Search by name or student code"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    curriculum_id: Optional[UUID] = Query(None, description="Filter by curriculum"),
    current_level: Optional[int] = Query(None, ge=1, le=4, description="Filter by current level"),
    academic_status: Optional[str] = Query(None, description="Filter by academic status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    enrollment_year: Optional[int] = Query(None, ge=2000, description="Filter by enrollment year"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("student_code", description="Sort field"),
    sort_dir: str = Query("asc", description="Sort direction"),
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get paginated list of students with filters.
    
    Accessible by all staff members.
    """
    students, total = await service.get_students(
        search=search,
        department_id=department_id,
        curriculum_id=curriculum_id,
        current_level=current_level,
        academic_status=academic_status,
        risk_level=risk_level,
        enrollment_year=enrollment_year,
        is_active=is_active,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return StudentListResponse(
        items=[StudentResponse(**s) for s in students],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get a single student by ID with full profile.
    
    Accessible by all staff members.
    """
    student = await service.get_student_by_id(student_id)
    return StudentResponse(**student)


@router.get("/{student_id}/summary")
async def get_student_summary(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get academic summary for a student.
    
    Calls fn_student_academic_summary RPC.
    Returns student data + semester list.
    """
    summary = await service.get_academic_summary(student_id)
    return summary


@router.get("/{student_id}/transcript", response_model=TranscriptResponse)
async def get_student_transcript(
    student_id: UUID,
    level: Optional[int] = Query(None, ge=1, le=4, description="Filter by semester level"),
    term: Optional[str] = Query(None, description="Filter by term (fall, spring, summer)"),
    show_non_counting: bool = Query(False, description="Include non-counting attempts"),
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get student transcript with semesters and courses.
    
    Accessible by all staff members.
    """
    transcript = await service.get_transcript(
        student_id=student_id,
        level=level,
        term=term,
        show_non_counting=show_non_counting,
    )
    return TranscriptResponse(semesters=transcript)


@router.get("/{student_id}/academic-plan", response_model=AcademicPlanResponse)
async def get_student_academic_plan(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Compare student's completed courses against curriculum plan.
    
    Returns category summary, course statuses, and elective group completion.
    """
    plan = await service.get_academic_plan(student_id)
    return AcademicPlanResponse(**plan)


@router.get("/{student_id}/graduation-status", response_model=GraduationStatusResponse)
async def get_student_graduation_status(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Evaluate student's graduation eligibility.
    
    Checks hours, GPA, field training, and community course.
    """
    status = await service.get_graduation_status(student_id)
    return GraduationStatusResponse(**status)


@router.get("/{student_id}/prerequisites", response_model=PrerequisiteStatusResponse)
async def get_student_prerequisite_status(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get prerequisite compliance for student.
    
    Returns violations and upcoming blocked courses.
    """
    status = await service.get_prerequisite_status(student_id)
    return PrerequisiteStatusResponse(**status)


@router.get("/{student_id}/completion-percentage")
async def get_student_completion_percentage(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get graduation completion percentage.
    
    Returns float between 0 and 100.
    """
    percentage = await service.get_completion_percentage(student_id)
    return {"student_id": student_id, "completion_percentage": percentage}


@router.get("/{student_id}/semesters")
async def get_student_semesters(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_staff),
):
    """
    Get student semesters (lightweight, no nested courses).
    
    Used for semester filter dropdowns and GPA trend.
    """
    semesters = await service.get_student_semesters(student_id)
    return {"student_id": student_id, "semesters": semesters}


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    update_data: StudentUpdateRequest,
    service: StudentService = Depends(get_student_service),
    _=Depends(require_admin),  # Admin only
):
    """
    Update student record manually.
    
    Admin only. For manual corrections bypassing import pipeline.
    """
    updated = await service.update_student(
        student_id=student_id,
        current_level=update_data.current_level,
        is_active=update_data.is_active,
        cumulative_gpa=update_data.cumulative_gpa,
    )
    return StudentResponse(**updated)