"""
================================================================================
Dashboard API Endpoints
================================================================================

Endpoints for dashboard analytics:
- KPI overview cards
- Academic status distribution (donut chart)
- GPA distribution (histogram)
- At-risk students list
- Department status table
- Recent import activity

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_dashboard_service, require_admin, require_staff
from app.services.dashboard_service import DashboardService

logger = logging.getLogger("acadexa.api.dashboard")

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    department_id: Optional[UUID] = Query(None, description="Filter by department (admin only)"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user=Depends(require_staff),
):
    """
    Get KPI data for dashboard cards.
    
    Accessible by all staff members.
    Department filter only applies for admin users.
    """
    # Non-admin users cannot filter by department
    if department_id and not current_user.is_admin:
        department_id = None
    
    kpis = await service.get_kpi_overview(department_id=department_id)
    return kpis


@router.get("/academic-status-distribution")
async def get_academic_status_distribution(
    department_id: Optional[UUID] = Query(None, description="Filter by department (admin only)"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user=Depends(require_staff),
):
    """
    Get counts by academic_status for donut chart.
    
    Accessible by all staff members.
    """
    if department_id and not current_user.is_admin:
        department_id = None
    
    distribution = await service.get_academic_status_distribution(department_id=department_id)
    return distribution


@router.get("/gpa-distribution")
async def get_gpa_distribution(
    department_id: Optional[UUID] = Query(None, description="Filter by department (admin only)"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user=Depends(require_staff),
):
    """
    Get GPA distribution histogram.
    
    Accessible by all staff members.
    """
    if department_id and not current_user.is_admin:
        department_id = None
    
    distribution = await service.get_gpa_distribution(department_id=department_id)
    return {"buckets": distribution}


@router.get("/at-risk-students")
async def get_at_risk_students(
    department_id: Optional[UUID] = Query(None, description="Filter by department (admin only)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of students"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user=Depends(require_staff),
):
    """
    Get top at-risk students.
    
    Accessible by all staff members.
    """
    if department_id and not current_user.is_admin:
        department_id = None
    
    students = await service.get_at_risk_students(
        department_id=department_id,
        limit=limit,
    )
    return {"students": students, "count": len(students)}


@router.get("/department-status")
async def get_department_status(
    department_id: Optional[UUID] = Query(None, description="Get single department"),
    service: DashboardService = Depends(get_dashboard_service),
    _=Depends(require_staff),
):
    """
    Get department status overview.
    
    Accessible by all staff members.
    """
    status = await service.get_department_status(department_id=department_id)
    return {"departments": status}


@router.get("/recent-imports")
async def get_recent_imports(
    limit: int = Query(5, ge=1, le=20, description="Number of imports to return"),
    service: DashboardService = Depends(get_dashboard_service),
    _=Depends(require_staff),
):
    """
    Get recent import jobs for dashboard widget.
    
    Accessible by all staff members.
    """
    imports = await service.get_recent_imports(limit=limit)
    return {"imports": imports}