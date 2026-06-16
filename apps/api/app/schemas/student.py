"""
================================================================================
Student Pydantic Schemas
================================================================================

Request/response validation schemas for student-related endpoints.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StudentBase(BaseModel):
    """Base student schema."""
    
    student_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    department_id: UUID
    curriculum_id: UUID
    enrollment_year: int = Field(..., ge=2000, le=2100)
    current_level: Optional[int] = Field(None, ge=1, le=4)
    cumulative_gpa: float = Field(0.0, ge=0.0, le=4.0)
    cumulative_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    attempted_hours: int = Field(0, ge=0)
    completed_hours: int = Field(0, ge=0)
    completion_rate: float = Field(0.0, ge=0.0, le=100.0)
    total_passed_courses: int = Field(0, ge=0)
    total_failed_courses: int = Field(0, ge=0)
    is_active: bool = True


class StudentCreate(StudentBase):
    """Schema for creating a new student."""
    
    pass


class StudentUpdate(BaseModel):
    """Schema for updating a student (admin only)."""
    
    current_level: Optional[int] = Field(None, ge=1, le=4)
    is_active: Optional[bool] = None
    cumulative_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)


class StudentUpdateRequest(StudentUpdate):
    """Alias for student update request."""
    
    pass


class DepartmentInfo(BaseModel):
    """Department information nested in student response."""
    
    id: UUID
    code: str
    name_ar: str
    name_en: str
    short_name: Optional[str] = None


class CurriculumInfo(BaseModel):
    """Curriculum information nested in student response."""
    
    id: UUID
    name_ar: str
    regulation_year: int
    total_required_hours: int
    min_gpa_to_graduate: float


class AdvisorInfo(BaseModel):
    """Advisor information nested in student response."""
    
    id: UUID
    name: str
    email: str


class LatestAnalysisInfo(BaseModel):
    """Latest analysis information nested in student response."""
    
    academic_status: Optional[str] = None
    risk_level: Optional[str] = None
    graduation_eligible: Optional[bool] = None
    analyzed_at: Optional[str] = None


class StudentResponse(BaseModel):
    """Schema for student API response."""
    
    id: UUID
    student_code: str
    name: str
    department_id: UUID
    curriculum_id: UUID
    enrollment_year: int
    current_level: Optional[int] = None
    cumulative_gpa: float
    cumulative_percentage: Optional[float] = None
    attempted_hours: int
    completed_hours: int
    completion_rate: float
    total_passed_courses: int
    total_failed_courses: int
    is_active: bool
    created_at: str
    updated_at: str
    departments: Optional[DepartmentInfo] = None
    curricula: Optional[CurriculumInfo] = None
    advisor: Optional[AdvisorInfo] = None
    latest_analysis: Optional[LatestAnalysisInfo] = None
    academic_status: Optional[str] = None
    risk_level: Optional[str] = None
    graduation_eligible: Optional[bool] = None
    last_analyzed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    """Paginated student list response."""
    
    items: List[StudentResponse]
    total: int
    page: int
    limit: int
    pages: int


class SemesterCourse(BaseModel):
    """Course within a semester for transcript."""
    
    id: UUID
    course_code: Optional[str] = None
    course_name: str
    credit_hours: int
    grade_letter: str
    grade_letter_raw: Optional[str] = None
    grade_points: float
    grade_score: Optional[float] = None
    passed: bool
    attempt_number: int
    is_latest_attempt: bool
    grade_name_ar: Optional[str] = None
    affects_gpa: bool
    is_passing_grade: bool


class SemesterResponse(BaseModel):
    """Semester response for transcript."""
    
    id: UUID
    semester_number: int
    academic_year: Optional[str] = None
    level_semester_raw: Optional[str] = None
    term: Optional[str] = None
    level: Optional[int] = None
    gpa: float
    attempted_hours: int
    completed_hours: int
    passed_courses: int
    failed_courses: int
    total_courses: int
    quality_points: float
    courses: List[SemesterCourse] = []


class TranscriptResponse(BaseModel):
    """Transcript response."""
    
    semesters: List[SemesterResponse]


class CategorySummary(BaseModel):
    """Category summary for academic plan."""
    
    required_hours: int
    completed_hours: int


class PlanCourse(BaseModel):
    """Course in academic plan."""
    
    id: UUID
    course_code: Optional[str] = None
    name_ar: str
    credit_hours: int
    level: int
    term: str
    category: str
    status: str  # passed, failed, not_taken
    grade: Optional[str] = None
    is_field_training: bool
    is_graduation_project: bool
    is_community_issues_course: bool


class ElectiveGroupCourse(BaseModel):
    """Course within an elective group."""
    
    course_id: UUID
    name_ar: Optional[str] = None
    course_code: Optional[str] = None
    credit_hours: int
    is_completed: bool


class ElectiveGroupResponse(BaseModel):
    """Elective group response."""
    
    id: UUID
    name: str
    category: str
    required_hours: int
    min_courses: int
    completed_hours: int
    completed_courses: int
    is_complete: bool
    courses: List[ElectiveGroupCourse]


class AcademicPlanResponse(BaseModel):
    """Academic plan response."""
    
    student_id: UUID
    curriculum_id: UUID
    category_summary: Dict[str, CategorySummary]
    courses: List[PlanCourse]
    elective_groups: List[ElectiveGroupResponse]


class GraduationRequirementCheck(BaseModel):
    """Single graduation requirement check."""
    
    required: Any
    current: Any
    met: bool


class GraduationRequirementsResponse(BaseModel):
    """Graduation requirements response."""
    
    hours: GraduationRequirementCheck
    gpa: GraduationRequirementCheck
    field_training: GraduationRequirementCheck
    community_course: GraduationRequirementCheck


class GraduationStatusResponse(BaseModel):
    """Graduation status response."""
    
    student_id: UUID
    is_eligible: bool
    requirements: GraduationRequirementsResponse


class PrerequisiteViolation(BaseModel):
    """Prerequisite violation."""
    
    course_id: UUID
    course_code: Optional[str] = None
    course_name: str
    taken_in: str
    missing_prerequisites: List[str]


class UpcomingBlockedCourse(BaseModel):
    """Upcoming course blocked by missing prerequisites."""
    
    course_id: UUID
    course_code: Optional[str] = None
    course_name: str
    level: Optional[int] = None
    missing_prerequisites: List[str]


class PrerequisiteStatusResponse(BaseModel):
    """Prerequisite status response."""
    
    student_id: UUID
    violations: List[PrerequisiteViolation]
    upcoming_blocked_courses: List[UpcomingBlockedCourse]