"""
================================================================================
Academic Analyses API Endpoints
================================================================================

Endpoints for expert system analysis:
- Get student analyses
- Get latest analysis with issues
- Trigger single/batch analysis
- Manage analysis issues (resolve)
- Get issue analytics

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_analysis_service, require_admin, require_staff
from app.core.exceptions import NotFoundError
from app.schemas.analysis import (
    AcademicAnalysisResponse,
    AnalysisWithIssuesResponse,
    AnalysisIssueResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    AnalysisJobStatusResponse,
    IssueResolveRequest,
    BulkIssueResolveRequest,
    RuleAnalyticsResponse,
)
from app.services.analysis_service import AnalysisService

logger = logging.getLogger("acadexa.api.analyses")

router = APIRouter(prefix="/analyses", tags=["Analyses"])


# =============================================================================
# Student Analysis Endpoints
# =============================================================================

@router.get("/students/{student_id}/analyses", response_model=List[AcademicAnalysisResponse])
async def get_student_analyses(
    student_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of analyses"),
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_staff),
):
    """
    Get all analyses for a student (history).
    
    Accessible by all staff members.
    """
    analyses = await service.get_student_analyses(student_id, limit)
    return [AcademicAnalysisResponse(**a) for a in analyses]


@router.get("/students/{student_id}/analyses/latest", response_model=AnalysisWithIssuesResponse)
async def get_latest_analysis(
    student_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_staff),
):
    """
    Get the most recent analysis for a student with its issues.
    
    Accessible by all staff members.
    """
    result = await service.get_latest_analysis(student_id)
    
    if not result:
        raise NotFoundError("Analysis", f"for student {student_id}")
    
    return AnalysisWithIssuesResponse(
        analysis=AcademicAnalysisResponse(**result["analysis"]),
        issues=[AnalysisIssueResponse(**i) for i in result["issues"]],
    )


@router.post("/students/{student_id}/analyses/run", status_code=status.HTTP_202_ACCEPTED)
async def run_single_analysis(
    student_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_admin),
):
    """
    Trigger expert system analysis for a single student.
    
    Admin only. Runs synchronously for single student (fast).
    """
    result = await service.run_single_analysis(student_id)
    return result


# =============================================================================
# Batch Analysis Endpoints
# =============================================================================

@router.post("/run-batch", status_code=status.HTTP_202_ACCEPTED, response_model=BatchAnalysisResponse)
async def run_batch_analysis(
    request: BatchAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_admin),
):
    """
    Trigger expert system analysis for multiple students.
    
    Admin only. Runs in background.
    Returns job_id for polling status.
    """
    result = await service.run_batch_analysis(request.student_ids)
    return BatchAnalysisResponse(
        job_id=result["job_id"],
        total_students=result["total"],
        message=f"Batch analysis started for {result['total']} students. Use /jobs/{result['job_id']} to poll status.",
    )


@router.get("/jobs/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_job_status(
    job_id: str,
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_admin),
):
    """
    Poll status of a batch analysis job.
    
    Admin only.
    Returns real job state from the in-memory job store.
    """
    job = await service.get_batch_job_status(job_id)
    
    return AnalysisJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        processed=job.get("processed", 0),
        total=job.get("total", 0),
        completed_at=job.get("completed_at"),
        error=job.get("error"),
    )


# =============================================================================
# Analysis Issues Endpoints
# =============================================================================

@router.patch("/issues/{issue_id}", response_model=AnalysisIssueResponse)
async def resolve_issue(
    issue_id: UUID,
    request: IssueResolveRequest,
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_staff),
):
    """
    Mark an analysis issue as resolved or unresolved.
    
    Accessible by all staff members.
    """
    updated = await service.resolve_issue(issue_id, request.resolved)
    return AnalysisIssueResponse(**updated)


@router.post("/issues/resolve-bulk")
async def resolve_bulk_issues(
    request: BulkIssueResolveRequest,
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_admin),
):
    """
    Mark multiple analysis issues as resolved.
    
    Admin only. Uses optimized single update query.
    """
    result = await service.resolve_bulk_issues(request.issue_ids, request.resolved)
    return result


@router.get("/issues", response_model=dict)
async def list_issues(
    rule_code: Optional[str] = Query(None, description="Filter by rule code"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, error)"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_admin),
):
    """
    Get analysis issues with filtering.
    
    Admin only.
    """
    issues, total = await service.get_issues(
        rule_code=rule_code,
        severity=severity,
        resolved=resolved,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return {
        "items": issues,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/issues/analytics", response_model=RuleAnalyticsResponse)
async def get_issue_analytics(
    service: AnalysisService = Depends(get_analysis_service),
    _=Depends(require_admin),
):
    """
    Get aggregated analytics over analysis issues.
    
    Admin only.
    """
    analytics = await service.get_issue_analytics()
    return RuleAnalyticsResponse(**analytics)