"""
================================================================================
Grade Scale API Endpoints
================================================================================

View and manage grade scale (grading system).

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_admin, require_staff
from app.core.exceptions import NotFoundError
from app.schemas.grade_scale import GradeScaleResponse, GradeScaleUpdate
from app.services.grade_scale_service import GradeScaleService

logger = logging.getLogger("acadexa.api.grade_scale")

router = APIRouter(prefix="/grade-scale", tags=["Grade Scale"])


def get_grade_scale_service() -> GradeScaleService:
    """Dependency for grade scale service."""
    return GradeScaleService()


@router.get("", response_model=List[GradeScaleResponse])
async def list_grade_scale(
    service: GradeScaleService = Depends(get_grade_scale_service),
    _=Depends(require_staff),
):
    """
    Get all grade scale entries.
    
    Accessible by all staff members.
    """
    entries = await service.get_all()
    return [GradeScaleResponse(**entry) for entry in entries]


@router.get("/{grade_letter}", response_model=GradeScaleResponse)
async def get_grade_scale_entry(
    grade_letter: str,
    service: GradeScaleService = Depends(get_grade_scale_service),
    _=Depends(require_staff),
):
    """
    Get a single grade scale entry by letter.
    
    Accessible by all staff members.
    """
    entry = await service.get_by_letter(grade_letter)
    if not entry:
        raise NotFoundError("GradeScale", grade_letter)
    return GradeScaleResponse(**entry)


@router.patch("/{grade_letter}", response_model=GradeScaleResponse)
async def update_grade_scale_entry(
    grade_letter: str,
    update_data: GradeScaleUpdate,
    service: GradeScaleService = Depends(get_grade_scale_service),
    _=Depends(require_admin),  # Admin only
):
    """
    Update a grade scale entry.
    
    Admin only.
    """
    try:
        updated = await service.update(grade_letter, update_data)
        return GradeScaleResponse(**updated)
    except NotFoundError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update grade scale entry {grade_letter}: {e}")
        raise