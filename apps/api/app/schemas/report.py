"""
================================================================================
Report Pydantic Schemas
================================================================================

Request/response validation schemas for report generation and management.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ReportType(str):
    """Report type constants."""
    
    STUDENT_PROFILE = "student_profile"
    COURSE_COMPLETION = "course_completion"
    ACADEMIC_PLAN = "academic_plan"
    GRADUATION_ELIGIBILITY = "graduation_eligibility"
    ACADEMIC_RISK = "academic_risk"
    ADVISOR_ACTION = "advisor_action"
    SEMESTER_PERFORMANCE = "semester_performance"
    PREREQUISITE_VIOLATIONS = "prerequisite_violations"
    STUDENTS_OVERVIEW = "students_overview"
    AT_RISK_STUDENTS = "at_risk_students"
    DEPARTMENT_ANALYTICS = "department_analytics"


class ReportGenerateRequest(BaseModel):
    """Schema for report generation request."""
    
    report_type: str = Field(..., description="Type of report to generate")
    student_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    
    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, v: str) -> str:
        """Validate report type."""
        valid_types = [
            "student_profile", "course_completion", "academic_plan",
            "graduation_eligibility", "academic_risk", "advisor_action",
            "semester_performance", "prerequisite_violations",
            "students_overview", "at_risk_students", "department_analytics"
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid report type. Must be one of: {', '.join(valid_types)}")
        return v
    
    def model_post_init(self, __context):
        """Validate that student_id or department_id is provided."""
        if self.report_type != "students_overview":
            if not self.student_id and not self.department_id:
                raise ValueError("Either student_id or department_id must be provided")
        
        if self.report_type in ["student_profile", "course_completion", "academic_plan",
                                 "graduation_eligibility", "academic_risk", "advisor_action",
                                 "semester_performance", "prerequisite_violations"]:
            if not self.student_id:
                raise ValueError(f"student_id is required for report type: {self.report_type}")
        
        if self.report_type in ["students_overview", "at_risk_students", "department_analytics"]:
            if not self.department_id and self.report_type != "students_overview":
                raise ValueError(f"department_id is required for report type: {self.report_type}")


class ReportResponse(BaseModel):
    """Schema for report API response."""
    
    id: UUID
    student_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    report_type: str
    generated_by: UUID
    data: Dict[str, Any]
    created_at: str
    generated_by_name: Optional[str] = None
    student_name: Optional[str] = None
    department_name_ar: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Paginated report list response."""
    
    items: List[ReportResponse]
    total: int
    page: int
    limit: int
    pages: int


class ReportDownloadResponse(BaseModel):
    """Response for report download."""
    
    download_url: str
    expires_in: int = 3600


class StudentProfileReportData(BaseModel):
    """Data structure for student profile report."""
    
    student_id: UUID
    student_code: str
    student_name: str
    department_name_ar: str
    curriculum_name_ar: str
    regulation_year: int
    enrollment_year: int
    current_level: Optional[int]
    cumulative_gpa: float
    attempted_hours: int
    completed_hours: int
    remaining_hours: int
    completion_percentage: float
    academic_status: Optional[str]
    risk_level: Optional[str]
    graduation_eligible: Optional[bool]
    semesters: List[Dict[str, Any]]
    issues_summary: List[Dict[str, Any]]


class CourseCompletionReportData(BaseModel):
    """Data structure for course completion report."""
    
    student_id: UUID
    student_name: str
    student_code: str
    passed_courses: List[Dict[str, Any]]
    failed_courses: List[Dict[str, Any]]
    repeated_courses: List[Dict[str, Any]]


class AcademicPlanReportData(BaseModel):
    """Data structure for academic plan report."""
    
    student_id: UUID
    student_name: str
    category_summary: Dict[str, Dict[str, int]]
    completed_courses: List[Dict[str, Any]]
    missing_courses: List[Dict[str, Any]]
    elective_groups_status: List[Dict[str, Any]]


class GraduationEligibilityReportData(BaseModel):
    """Data structure for graduation eligibility report."""
    
    student_id: UUID
    student_name: str
    is_eligible: bool
    requirements_checklist: Dict[str, Dict[str, Any]]
    missing_items: List[str]
    recommendations: List[str]


class AcademicRiskReportData(BaseModel):
    """Data structure for academic risk report."""
    
    student_id: UUID
    student_name: str
    risk_level: str
    risk_factors: List[str]
    gpa_trend: List[Dict[str, Any]]
    failed_courses_count: int
    repeated_courses_count: int
    prediction: str


class AdvisorActionReportData(BaseModel):
    """Data structure for advisor action report."""
    
    student_id: UUID
    student_name: str
    recommended_actions: List[Dict[str, str]]
    priority_issues: List[str]
    suggested_courses: List[str]


class SemesterPerformanceReportData(BaseModel):
    """Data structure for semester performance report."""
    
    student_id: UUID
    student_name: str
    semester_performance: List[Dict[str, Any]]
    trend: str  # improving, declining, stable


class PrerequisiteViolationsReportData(BaseModel):
    """Data structure for prerequisite violations report."""
    
    student_id: UUID
    student_name: str
    violations: List[Dict[str, Any]]
    warnings: List[str]


class StudentsOverviewReportData(BaseModel):
    """Data structure for students overview report."""
    
    department_id: UUID
    department_name_ar: str
    total_students: int
    by_status: Dict[str, int]
    by_level: Dict[str, int]
    average_gpa: float


class AtRiskStudentsReportData(BaseModel):
    """Data structure for at-risk students report."""
    
    department_id: UUID
    department_name_ar: str
    students: List[Dict[str, Any]]
    total_at_risk: int


class DepartmentAnalyticsReportData(BaseModel):
    """Data structure for department analytics report."""
    
    department_id: UUID
    department_name_ar: str
    average_gpa: float
    pass_rate: float
    failure_rate: float
    graduation_rate: float
    most_failed_courses: List[Dict[str, Any]]
    risk_trend: List[Dict[str, Any]]