"""
================================================================================
Import API Endpoints
================================================================================

Endpoints for Excel import pipeline:
- Upload Excel file
- Get import job status
- List import jobs
- Get import job details
- Cancel/delete import jobs
- Download original file

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.core.dependencies import get_current_user, get_import_service, require_admin, require_staff
from app.core.exceptions import NotFoundError
from app.schemas.import_job import (
    ImportJobResponse,
    ImportJobStatusResponse,
    ImportUploadResponse,
    ImportResultResponse,
)
from app.services.import_service import ImportService

logger = logging.getLogger("acadexa.api.import")

router = APIRouter(prefix="/import", tags=["Import"])


@router.post("/upload", response_model=ImportUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_excel(
    department_id: UUID = Form(..., description="Department ID for the import"),
    file: UploadFile = File(..., description="Excel file (.xlsx or .xls)"),
    service: ImportService = Depends(get_import_service),
    current_user=Depends(get_current_user),
    _=Depends(require_staff),
):
    """
    Upload an Excel workbook and start import.
    
    Accessible by all staff members.
    File size limit: 50MB. Accepted formats: .xlsx, .xls.
    Returns job_id for polling status.
    """
    # Validate file extension
    if not file.filename.endswith((".xlsx", ".xls")):
        from app.core.exceptions import ValidationError
        raise ValidationError("Only Excel files (.xlsx, .xls) are supported", field="file")
    
    # Read file content
    content = await file.read()
    
    # Get department code for parser
    from app.core.supabase import get_service_role_client
    supabase = get_service_role_client()
    dept_result = supabase.table("departments").select("code").eq("id", str(department_id)).execute()
    
    department_code = dept_result.data[0]["code"] if dept_result.data else None
    
    # Start import
    job = await service.upload_and_parse(
        department_id=department_id,
        file_content=content,
        file_name=file.filename,
        uploaded_by=current_user.user_id,
        department_code=department_code,
    )
    
    return ImportUploadResponse(
        job_id=job["id"],
        message="Import started successfully",
        status_url=f"/api/v1/import/jobs/{job['id']}/status",
    )


@router.get("/jobs", response_model=dict)
async def list_import_jobs(
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status (pending, processing, completed, failed)"),
    uploaded_by: Optional[UUID] = Query(None, description="Filter by uploader"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: ImportService = Depends(get_import_service),
    _=Depends(require_staff),
):
    """
    List import jobs with filtering.
    
    Accessible by all staff members.
    """
    jobs, total = await service.get_import_jobs(
        department_id=department_id,
        status=status,
        uploaded_by=uploaded_by,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return {
        "items": jobs,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: UUID,
    service: ImportService = Depends(get_import_service),
    _=Depends(require_staff),
):
    """
    Get import job details.
    
    Accessible by all staff members.
    """
    job = await service.get_import_job(job_id)
    return ImportJobResponse(**job)


@router.get("/jobs/{job_id}/status", response_model=ImportJobStatusResponse)
async def get_import_job_status(
    job_id: UUID,
    service: ImportService = Depends(get_import_service),
    _=Depends(require_staff),
):
    """
    Poll import job status.
    
    Accessible by all staff members.
    Used by frontend for live progress updates.
    """
    status_data = await service.get_import_job_status(job_id)
    return ImportJobStatusResponse(**status_data)


@router.patch("/jobs/{job_id}")
async def cancel_import_job(
    job_id: UUID,
    service: ImportService = Depends(get_import_service),
    current_user=Depends(get_current_user),
    _=Depends(require_staff),
):
    """
    Cancel a pending import job.
    
    Accessible by the uploader or admin.
    """
    job = await service.cancel_import_job(
        job_id=job_id,
        user_id=current_user.user_id,
        is_admin=current_user.is_admin,
    )
    return {"message": "Job cancelled", "job_id": job_id, "status": job.get("status")}


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_import_job(
    job_id: UUID,
    service: ImportService = Depends(get_import_service),
    _=Depends(require_admin),
):
    """
    Delete an import job (admin only).
    
    Admin only. Cascades to imported_files, raw_students, raw_courses.
    """
    await service.delete_import_job(job_id)
    return None


@router.get("/jobs/{job_id}/students")
async def get_import_job_students(
    job_id: UUID,
    service: ImportService = Depends(get_import_service),
    _=Depends(require_staff),
):
    """
    Get students imported from a specific job.
    
    Accessible by all staff members.
    """
    students = await service.get_students_by_import_job(job_id)
    return {
        "job_id": job_id,
        "students": students,
        "count": len(students),
    }


@router.get("/jobs/{job_id}/files/{file_id}/download")
async def download_imported_file(
    job_id: UUID,
    file_id: UUID,
    service: ImportService = Depends(get_import_service),
    _=Depends(require_staff),
):
    """
    Download original uploaded Excel file.
    
    Accessible by all staff members.
    Returns signed URL (valid for 1 hour).
    """
    file_url = await service.get_import_job_file_url(job_id, file_id)
    return {"download_url": file_url, "expires_in": 3600}