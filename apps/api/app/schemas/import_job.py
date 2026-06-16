"""
================================================================================
Import Job Pydantic Schemas
================================================================================

Request/response validation schemas for import job tracking.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ImportJobBase(BaseModel):
    """Base import job schema."""
    
    department_id: UUID
    file_name: str = Field(..., max_length=255)
    file_url: Optional[str] = None


class ImportJobCreate(ImportJobBase):
    """Schema for creating a new import job."""
    
    uploaded_by: UUID


class ImportJobResponse(BaseModel):
    """Schema for import job API responses."""
    
    id: UUID
    uploaded_by: UUID
    department_id: UUID
    file_name: str
    file_url: Optional[str]
    status: str  # pending, processing, completed, failed
    total_students: int
    successful_records: int
    failed_records: int
    error_log: Optional[List[Dict[str, Any]]]
    created_at: str
    completed_at: Optional[str]
    
    class Config:
        from_attributes = True


class ImportJobStatusResponse(BaseModel):
    """Schema for import job status polling."""
    
    job_id: UUID
    status: str
    total_students: int
    successful_records: int
    failed_records: int
    completed_at: Optional[str]
    is_complete: bool
    has_errors: bool


class ImportUploadResponse(BaseModel):
    """Response after initiating an import upload."""
    
    job_id: UUID
    message: str
    status_url: str


class ImportErrorLogEntry(BaseModel):
    """Single error log entry from import processing."""
    
    sheet_name: str
    error: str
    student_code: Optional[str] = None


class ImportResultResponse(BaseModel):
    """Response after import completion."""
    
    job_id: UUID
    status: str
    total_students: int
    successful_records: int
    failed_records: int
    errors: List[ImportErrorLogEntry]
    completed_at: Optional[str]