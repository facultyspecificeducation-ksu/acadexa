"""
================================================================================
Reports API Endpoints
================================================================================

Endpoints for report generation and management:
- Generate reports (11 types)
- List reports with filtering
- Get report by ID
- Download report PDF (MVP - returns JSON data with PDF instructions)
- Delete reports

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_current_user, get_report_service, require_staff
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportListResponse,
)
from app.services.report_service import ReportService

logger = logging.getLogger("acadexa.api.reports")

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: ReportGenerateRequest,
    service: ReportService = Depends(get_report_service),
    current_user=Depends(get_current_user),
    _=Depends(require_staff),
):
    """
    Generate a report.
    
    Accessible by all staff members.
    Report types:
    - student_profile: Full academic profile (requires student_id)
    - course_completion: Passed/failed/repeated courses (requires student_id)
    - academic_plan: Plan vs transcript comparison (requires student_id)
    - graduation_eligibility: Graduation checklist (requires student_id)
    - academic_risk: Risk assessment (requires student_id)
    - advisor_action: Recommended actions (requires student_id)
    - semester_performance: GPA trend per semester (requires student_id)
    - prerequisite_violations: Prerequisite issues (requires student_id)
    - students_overview: Department summary (requires department_id)
    - at_risk_students: High-risk students list (requires department_id)
    - department_analytics: Department statistics (requires department_id)
    """
    report = await service.generate_report(
        report_type=request.report_type,
        generated_by=current_user.user_id,
        student_id=request.student_id,
        department_id=request.department_id,
    )
    
    return ReportResponse(**report)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    student_id: Optional[UUID] = Query(None, description="Filter by student"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    generated_by: Optional[UUID] = Query(None, description="Filter by generator"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: ReportService = Depends(get_report_service),
    _=Depends(require_staff),
):
    """
    List reports with filtering.
    
    Accessible by all staff members.
    """
    reports, total = await service.get_reports(
        student_id=student_id,
        department_id=department_id,
        report_type=report_type,
        generated_by=generated_by,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return ReportListResponse(
        items=[ReportResponse(**r) for r in reports],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
    _=Depends(require_staff),
):
    """
    Get a single report by ID.
    
    Accessible by all staff members.
    """
    report = await service.get_report_by_id(report_id)
    return ReportResponse(**report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
    _=Depends(require_staff),
):
    """
    Download report data as JSON.
    
    Accessible by all staff members.
    
    Note: PDF generation requires ReportLab integration.
    For MVP, returns the report data as JSON with a message.
    The frontend can use this data to render the report.
    """
    report = await service.get_report_by_id(report_id)
    
    return {
        "report_id": str(report_id),
        "report_type": report.get("report_type"),
        "data": report.get("data", {}),
        "generated_at": report.get("created_at"),
        "message": "PDF generation will be implemented in V2. Use the report data to render the report.",
    }


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    service: ReportService = Depends(get_report_service),
    current_user=Depends(get_current_user),
    _=Depends(require_staff),
):
    """
    Delete a report.
    
    Accessible by the report author or admin.
    """
    report = await service.get_report_by_id(report_id)
    
    # Check permission: author or admin
    if str(report["generated_by"]) != current_user.user_id and not current_user.is_admin:
        raise ForbiddenError("Only the report author or admin can delete this report")
    
    await service.delete_report(report_id)
    return None