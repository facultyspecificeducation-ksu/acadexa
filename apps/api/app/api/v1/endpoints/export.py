"""
================================================================================
Export API Endpoints
================================================================================

Endpoints for data export:
- Export student list to Excel
- Export at-risk students to Excel/PDF
- Export analysis issues to Excel/PDF

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_export_service, require_admin, require_staff
from app.services.export_service import ExportService

logger = logging.getLogger("acadexa.api.export")

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/students")
async def export_students(
    search: Optional[str] = Query(None, description="Search by name or code"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    curriculum_id: Optional[UUID] = Query(None, description="Filter by curriculum"),
    current_level: Optional[int] = Query(None, ge=1, le=4, description="Filter by level"),
    academic_status: Optional[str] = Query(None, description="Filter by academic status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    enrollment_year: Optional[int] = Query(None, ge=2000, description="Filter by enrollment year"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: ExportService = Depends(get_export_service),
    _=Depends(require_staff),
):
    """
    Export filtered student list to Excel.
    
    Accessible by all staff members.
    Returns Excel file as download.
    """
    data = await service.export_students_list(
        search=search,
        department_id=department_id,
        curriculum_id=curriculum_id,
        current_level=current_level,
        academic_status=academic_status,
        risk_level=risk_level,
        enrollment_year=enrollment_year,
        is_active=is_active,
    )
    
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=students_export.xlsx"},
    )


@router.get("/students/at-risk")
async def export_at_risk_students(
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    format: str = Query("xlsx", description="Export format (xlsx or pdf)"),
    service: ExportService = Depends(get_export_service),
    _=Depends(require_staff),
):
    """
    Export at-risk students to Excel or PDF.
    
    Accessible by all staff members.
    """
    data = await service.export_at_risk_students(
        department_id=department_id,
        format=format,
    )
    
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "application/pdf"
    filename = f"at_risk_students_export.{format}"
    
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/students/{student_id}/analyses/issues")
async def export_analysis_issues(
    student_id: UUID,
    format: str = Query("xlsx", description="Export format (xlsx or pdf)"),
    service: ExportService = Depends(get_export_service),
    _=Depends(require_staff),
):
    """
    Export a student's analysis issues to Excel or PDF.
    
    Accessible by all staff members.
    """
    data = await service.export_analysis_issues(
        student_id=student_id,
        format=format,
    )
    
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "application/pdf"
    filename = f"analysis_issues_{student_id}.{format}"
    
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )