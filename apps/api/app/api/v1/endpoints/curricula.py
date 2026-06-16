"""
================================================================================
Curricula API Endpoints
================================================================================

Endpoints for curriculum management:
- List curricula
- Get curriculum by ID with requirements
- Create/update/delete curricula
- Manage graduation requirements
- Manage academic rules
- Get all academic rules for comparison

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_curriculum_service, require_admin, require_staff
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.curriculum import (
    CurriculumResponse,
    CurriculumCreate,
    CurriculumUpdate,
    CurriculumListResponse,
    CurriculumDetailResponse,
    GraduationRequirementsResponse,
    GraduationRequirementsUpdate,
    AcademicRulesResponse,
    AcademicRulesUpdate,
)
from app.services.curriculum_service import CurriculumService

logger = logging.getLogger("acadexa.api.curricula")

router = APIRouter(prefix="/curricula", tags=["Curricula"])


# =============================================================================
# Curriculum Endpoints
# =============================================================================

@router.get("", response_model=CurriculumListResponse)
async def list_curricula(
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_staff),
):
    """
    Get list of curricula with pagination.
    
    Accessible by all staff members.
    """
    curricula, total = await service.get_curricula(
        department_id=department_id,
        is_active=is_active,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return CurriculumListResponse(
        items=[CurriculumResponse(**c) for c in curricula],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{curriculum_id}", response_model=CurriculumDetailResponse)
async def get_curriculum(
    curriculum_id: UUID,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_staff),
):
    """
    Get a single curriculum by ID with graduation requirements and academic rules.
    
    Accessible by all staff members.
    """
    curriculum = await service.get_curriculum_by_id(curriculum_id)
    return CurriculumDetailResponse(**curriculum)


@router.post("", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
async def create_curriculum(
    curriculum: CurriculumCreate,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_admin),
):
    """
    Create a new curriculum.
    
    Admin only.
    """
    try:
        created = await service.create_curriculum(curriculum.model_dump())
        return CurriculumResponse(**created)
    except ConflictError as e:
        raise e


@router.patch("/{curriculum_id}", response_model=CurriculumResponse)
async def update_curriculum(
    curriculum_id: UUID,
    update_data: CurriculumUpdate,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_admin),
):
    """
    Update an existing curriculum.
    
    Admin only.
    """
    updated = await service.update_curriculum(curriculum_id, update_data.model_dump(exclude_unset=True))
    return CurriculumResponse(**updated)


@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_curriculum(
    curriculum_id: UUID,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_admin),
):
    """
    Delete a curriculum.
    
    Admin only.
    Cannot delete curriculum with associated students.
    """
    try:
        await service.delete_curriculum(curriculum_id)
    except ConflictError as e:
        raise e


# =============================================================================
# Graduation Requirements Endpoints
# =============================================================================

@router.get("/{curriculum_id}/graduation-requirements", response_model=GraduationRequirementsResponse)
async def get_graduation_requirements(
    curriculum_id: UUID,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_staff),
):
    """
    Get graduation requirements for a curriculum.
    
    Accessible by all staff members.
    """
    requirements = await service.get_graduation_requirements(curriculum_id)
    return GraduationRequirementsResponse(**requirements)


@router.put("/{curriculum_id}/graduation-requirements", response_model=GraduationRequirementsResponse)
async def upsert_graduation_requirements(
    curriculum_id: UUID,
    requirements: GraduationRequirementsUpdate,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_admin),
):
    """
    Create or replace graduation requirements for a curriculum.
    
    Admin only.
    """
    saved = await service.upsert_graduation_requirements(
        curriculum_id,
        requirements.model_dump()
    )
    return GraduationRequirementsResponse(**saved)


# =============================================================================
# Academic Rules Endpoints
# =============================================================================

@router.get("/{curriculum_id}/academic-rules", response_model=AcademicRulesResponse)
async def get_academic_rules(
    curriculum_id: UUID,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_staff),
):
    """
    Get academic rules for a curriculum.
    
    Accessible by all staff members.
    """
    rules = await service.get_academic_rules(curriculum_id)
    return AcademicRulesResponse(**rules)


@router.put("/{curriculum_id}/academic-rules", response_model=AcademicRulesResponse)
async def upsert_academic_rules(
    curriculum_id: UUID,
    rules: AcademicRulesUpdate,
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_admin),
):
    """
    Create or replace academic rules for a curriculum.
    
    Admin only.
    """
    saved = await service.upsert_academic_rules(
        curriculum_id,
        rules.model_dump()
    )
    return AcademicRulesResponse(**saved)


# =============================================================================
# All Academic Rules (Comparison Table)
# =============================================================================

@router.get("/academic-rules/all")
async def get_all_academic_rules(
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    service: CurriculumService = Depends(get_curriculum_service),
    _=Depends(require_admin),
):
    """
    Get all academic rules with curriculum and department info.
    
    Used for the AcademicLoadRulesPage comparison table.
    Admin only.
    """
    rules = await service.get_all_academic_rules(department_id=department_id)
    return {
        "items": rules,
        "total": len(rules),
    }