"""
================================================================================
Analysis & Expert System Pydantic Schemas
================================================================================

Request/response validation schemas for academic analyses and expert system output.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisIssueBase(BaseModel):
    """Base schema for analysis issues."""
    
    rule_code: str = Field(..., max_length=100)
    severity: str = Field(..., description="info, warning, error")
    title_ar: str = Field(..., max_length=200)
    description_ar: str = Field(..., max_length=1000)
    recommendation_ar: Optional[str] = Field(None, max_length=500)


class AnalysisIssueResponse(AnalysisIssueBase):
    """Schema for analysis issue API responses."""
    
    id: UUID
    analysis_id: UUID
    resolved: bool
    created_at: str
    
    class Config:
        from_attributes = True


class AcademicAnalysisResponse(BaseModel):
    """Schema for academic analysis API responses."""
    
    id: UUID
    student_id: UUID
    academic_status: str  # good_standing, delayed, needs_support, probation
    risk_level: str  # low, medium, high
    graduation_eligible: bool
    analyzed_at: str
    
    class Config:
        from_attributes = True


class AnalysisWithIssuesResponse(BaseModel):
    """Schema for analysis with its issues."""
    
    analysis: AcademicAnalysisResponse
    issues: List[AnalysisIssueResponse]


class BatchAnalysisRequest(BaseModel):
    """Request schema for batch analysis."""
    
    student_ids: List[UUID] = Field(..., min_length=1, max_length=500)


class BatchAnalysisResponse(BaseModel):
    """Response schema for batch analysis job."""
    
    job_id: str
    total_students: int
    message: str


class AnalysisJobStatusResponse(BaseModel):
    """Response schema for analysis job status polling."""
    
    job_id: str
    status: str  # pending, processing, completed, failed
    processed: int
    total: int
    completed_at: Optional[str]
    error: Optional[str] = None


class IssueResolveRequest(BaseModel):
    """Request schema for marking an issue as resolved."""
    
    resolved: bool = True


class BulkIssueResolveRequest(BaseModel):
    """Request schema for bulk resolving issues."""
    
    issue_ids: List[UUID]
    resolved: bool = True


class RuleCodeStats(BaseModel):
    """Statistics for a single rule code."""
    
    rule_code: str
    count: int
    severity: str
    students_affected: int


class RuleAnalyticsResponse(BaseModel):
    """Response schema for rule analytics."""
    
    top_rules: List[RuleCodeStats]
    severity_distribution: dict[str, int]
    weekly_firings: List[dict]  # List of {week: str, count: int}