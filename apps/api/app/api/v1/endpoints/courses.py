"""
================================================================================
Courses API Endpoints
================================================================================

Endpoints for course management:
- Get curriculum courses (with filtering)
- Get course by ID with prerequisites
- Create/update/delete courses
- Manage course prerequisites
- Manage elective groups
- Cross-curriculum course search

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_course_service, require_admin, require_staff
from app.core.exceptions import ConflictError, NotFoundError, ValidationError  # ← FIXED: added ValidationError import
from app.schemas.course import (
    CurriculumCourseResponse,
    CurriculumCourseCreate,
    CurriculumCourseUpdate,
    CourseSearchResponse,
    CourseSearchResult,
    PrerequisiteResponse,
    PrerequisiteCreate,
    ElectiveGroupResponse,
    ElectiveGroupCreate,
    ElectiveGroupUpdate,
    ElectiveGroupDetailResponse,
)
from app.services.course_service import CourseService

logger = logging.getLogger("acadexa.api.courses")

router = APIRouter(prefix="/courses", tags=["Courses"])


# =============================================================================
# Curriculum Courses Endpoints
# =============================================================================

@router.get("/curricula/{curriculum_id}/courses", response_model=List[CurriculumCourseResponse])
async def get_curriculum_courses(
    curriculum_id: UUID,
    level: Optional[int] = Query(None, ge=1, le=4, description="Filter by level"),
    term: Optional[str] = Query(None, description="Filter by term (fall, spring, summer)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_field_training: Optional[bool] = Query(None, description="Filter by field training"),
    is_graduation_project: Optional[bool] = Query(None, description="Filter by graduation project"),
    is_community_issues_course: Optional[bool] = Query(None, description="Filter by community issues course"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: CourseService = Depends(get_course_service),
    _=Depends(require_staff),
):
    """
    Get all courses for a curriculum with filtering.
    
    Accessible by all staff members.
    """
    courses = await service.get_curriculum_courses(
        curriculum_id=curriculum_id,
        level=level,
        term=term,
        category=category,
        is_field_training=is_field_training,
        is_graduation_project=is_graduation_project,
        is_community_issues_course=is_community_issues_course,
        is_active=is_active,
    )
    return [CurriculumCourseResponse(**c) for c in courses]


@router.get("/{course_id}", response_model=CurriculumCourseResponse)
async def get_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_staff),
):
    """
    Get a single course by ID with prerequisites.
    
    Accessible by all staff members.
    """
    course = await service.get_course_by_id(course_id)
    return CurriculumCourseResponse(**course)


@router.post("/curricula/{curriculum_id}/courses", response_model=CurriculumCourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    curriculum_id: UUID,
    course: CurriculumCourseCreate,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Add a course to a curriculum.
    
    Admin only.
    """
    try:
        created = await service.create_course(curriculum_id, course.model_dump())
        return CurriculumCourseResponse(**created)
    except ConflictError as e:
        raise e


@router.patch("/{course_id}", response_model=CurriculumCourseResponse)
async def update_course(
    course_id: UUID,
    update_data: CurriculumCourseUpdate,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Update a curriculum course.
    
    Admin only.
    """
    updated = await service.update_course(course_id, update_data.model_dump(exclude_unset=True))
    return CurriculumCourseResponse(**updated)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Delete a curriculum course.
    
    Admin only.
    Cannot delete course referenced by student records.
    """
    try:
        await service.delete_course(course_id)
    except ConflictError as e:
        raise e


# =============================================================================
# Cross-Curriculum Course Search
# =============================================================================

@router.get("/search", response_model=CourseSearchResponse)
async def search_courses(
    search: Optional[str] = Query(None, description="Search by course code or name"),
    curriculum_id: Optional[UUID] = Query(None, description="Filter by curriculum"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    category: Optional[str] = Query(None, description="Filter by category"),
    level: Optional[int] = Query(None, ge=1, le=4, description="Filter by level"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: CourseService = Depends(get_course_service),
    _=Depends(require_staff),
):
    """
    Search courses across all curricula.
    
    Accessible by all staff members.
    """
    courses, total = await service.search_courses(
        search=search,
        curriculum_id=curriculum_id,
        department_id=department_id,
        category=category,
        level=level,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return CourseSearchResponse(
        items=[CourseSearchResult(**c) for c in courses],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


# =============================================================================
# Prerequisites Endpoints
# =============================================================================

@router.get("/{course_id}/prerequisites", response_model=List[PrerequisiteResponse])
async def get_course_prerequisites(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_staff),
):
    """
    Get all prerequisites for a course.
    
    Accessible by all staff members.
    """
    prerequisites = await service.get_course_prerequisites(course_id)
    return [PrerequisiteResponse(**p) for p in prerequisites]


@router.post("/{course_id}/prerequisites", response_model=PrerequisiteResponse, status_code=status.HTTP_201_CREATED)
async def add_prerequisite(
    course_id: UUID,
    prerequisite: PrerequisiteCreate,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Add a prerequisite to a course.
    
    Admin only.
    """
    try:
        created = await service.add_prerequisite(
            course_id=course_id,
            required_course_id=prerequisite.required_course_id,
            minimum_grade=prerequisite.minimum_grade,
        )
        return PrerequisiteResponse(**created)
    except (ConflictError, ValidationError) as e:
        raise e


@router.delete("/{course_id}/prerequisites/{required_course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_prerequisite(
    course_id: UUID,
    required_course_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Remove a prerequisite from a course.
    
    Admin only.
    """
    await service.remove_prerequisite(course_id, required_course_id)
    return None


# =============================================================================
# Elective Groups Endpoints
# =============================================================================

@router.get("/curricula/{curriculum_id}/elective-groups", response_model=List[ElectiveGroupDetailResponse])
async def get_elective_groups(
    curriculum_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_staff),
):
    """
    Get all elective groups for a curriculum with their courses.
    
    Accessible by all staff members.
    """
    groups = await service.get_elective_groups(curriculum_id)
    return [ElectiveGroupDetailResponse(**g) for g in groups]


@router.post("/curricula/{curriculum_id}/elective-groups", response_model=ElectiveGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_elective_group(
    curriculum_id: UUID,
    group: ElectiveGroupCreate,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Create an elective group.
    
    Admin only.
    """
    created = await service.create_elective_group(curriculum_id, group.model_dump())
    return ElectiveGroupResponse(**created)


@router.patch("/elective-groups/{group_id}", response_model=ElectiveGroupResponse)
async def update_elective_group(
    group_id: UUID,
    update_data: ElectiveGroupUpdate,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Update an elective group.
    
    Admin only.
    """
    updated = await service.update_elective_group(group_id, update_data.model_dump(exclude_unset=True))
    return ElectiveGroupResponse(**updated)


@router.delete("/elective-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_elective_group(
    group_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Delete an elective group.
    
    Admin only.
    """
    await service.delete_elective_group(group_id)
    return None


@router.post("/elective-groups/{group_id}/courses/{course_id}", status_code=status.HTTP_201_CREATED)
async def add_course_to_elective_group(
    group_id: UUID,
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Add a course to an elective group.
    
    Admin only.
    """
    try:
        await service.add_course_to_elective_group(group_id, course_id)
        return {"message": "Course added to group successfully"}
    except (ConflictError, ValidationError, NotFoundError) as e:
        raise e


@router.delete("/elective-groups/{group_id}/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course_from_elective_group(
    group_id: UUID,
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    _=Depends(require_admin),
):
    """
    Remove a course from an elective group.
    
    Admin only.
    """
    await service.remove_course_from_elective_group(group_id, course_id)
    return None