"""
================================================================================
Course Pydantic Schemas
================================================================================

Request/response validation schemas for courses, prerequisites, and elective groups.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Curriculum Course Schemas
# =============================================================================

class CurriculumCourseBase(BaseModel):
    """Base curriculum course schema."""
    
    course_code: Optional[str] = Field(None, max_length=50, description="Course code (can be null for special courses)")
    name_ar: str = Field(..., min_length=1, max_length=200, description="Arabic course name")
    name_en: Optional[str] = Field(None, max_length=200, description="English course name")
    credit_hours: int = Field(..., gt=0, le=12, description="Credit hours (1-12)")
    level: int = Field(..., ge=1, le=4, description="Study level (1-4)")
    term: str = Field(..., description="Term: fall, spring, summer")
    category: str = Field(..., description="Course category from enum")
    is_field_training: bool = False
    is_graduation_project: bool = False
    is_community_issues_course: bool = False
    is_active: bool = True
    
    @field_validator('term')
    @classmethod
    def validate_term(cls, v: str) -> str:
        """Validate term value."""
        allowed = ['fall', 'spring', 'summer']
        if v not in allowed:
            raise ValueError(f'Term must be one of: {", ".join(allowed)}')
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category value."""
        allowed = [
            'university_required', 'university_elective',
            'college_required', 'college_elective',
            'major_required', 'major_elective'
        ]
        if v not in allowed:
            raise ValueError(f'Category must be one of: {", ".join(allowed)}')
        return v


class CurriculumCourseCreate(CurriculumCourseBase):
    """Schema for creating a curriculum course."""
    
    pass


class CurriculumCourseUpdate(BaseModel):
    """Schema for updating a curriculum course."""
    
    course_code: Optional[str] = Field(None, max_length=50)
    name_ar: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    credit_hours: Optional[int] = Field(None, gt=0, le=12)
    level: Optional[int] = Field(None, ge=1, le=4)
    term: Optional[str] = None
    category: Optional[str] = None
    is_field_training: Optional[bool] = None
    is_graduation_project: Optional[bool] = None
    is_community_issues_course: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @field_validator('term')
    @classmethod
    def validate_term(cls, v: Optional[str]) -> Optional[str]:
        """Validate term value if provided."""
        if v:
            allowed = ['fall', 'spring', 'summer']
            if v not in allowed:
                raise ValueError(f'Term must be one of: {", ".join(allowed)}')
        return v
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category value if provided."""
        if v:
            allowed = [
                'university_required', 'university_elective',
                'college_required', 'college_elective',
                'major_required', 'major_elective'
            ]
            if v not in allowed:
                raise ValueError(f'Category must be one of: {", ".join(allowed)}')
        return v


class PrerequisiteInfo(BaseModel):
    """Prerequisite information nested in course response."""
    
    id: UUID
    required_course_id: UUID
    minimum_grade: Optional[str] = None
    course_code: Optional[str] = None
    name_ar: Optional[str] = None
    credit_hours: Optional[int] = None


class CurriculumCourseResponse(CurriculumCourseBase):
    """Schema for curriculum course API response."""
    
    id: UUID
    curriculum_id: UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    prerequisites: List[PrerequisiteInfo] = []
    curriculum_name_ar: Optional[str] = None
    regulation_year: Optional[int] = None
    department_name_ar: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# Course Search Schemas
# =============================================================================

class CourseSearchResult(BaseModel):
    """Schema for course search result."""
    
    id: UUID
    course_code: Optional[str] = None
    name_ar: str
    name_en: Optional[str] = None
    credit_hours: int
    level: int
    term: str
    category: str
    is_field_training: bool
    is_graduation_project: bool
    is_community_issues_course: bool
    curriculum_id: UUID
    curriculum_name_ar: Optional[str] = None
    regulation_year: Optional[int] = None
    department_id: Optional[UUID] = None
    department_name_ar: Optional[str] = None
    department_name_en: Optional[str] = None
    prerequisites_count: int = 0


class CourseSearchResponse(BaseModel):
    """Paginated course search response."""
    
    items: List[CourseSearchResult]
    total: int
    page: int
    limit: int
    pages: int


# =============================================================================
# Prerequisite Schemas
# =============================================================================

class PrerequisiteBase(BaseModel):
    """Base prerequisite schema."""
    
    required_course_id: UUID
    minimum_grade: Optional[str] = Field(None, max_length=3, description="Minimum grade required")


class PrerequisiteCreate(PrerequisiteBase):
    """Schema for creating a prerequisite."""
    
    pass


class PrerequisiteResponse(PrerequisiteBase):
    """Schema for prerequisite API response."""
    
    id: UUID
    course_id: UUID
    course_code: Optional[str] = None
    name_ar: Optional[str] = None
    credit_hours: Optional[int] = None
    level: Optional[int] = None
    term: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# Elective Group Schemas
# =============================================================================

class ElectiveGroupBase(BaseModel):
    """Base elective group schema."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Group name")
    category: str = Field(..., description="Course category for this group")
    required_hours: int = Field(..., gt=0, description="Required credit hours from this group")
    min_courses: int = Field(1, ge=1, description="Minimum number of courses required")
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category value."""
        allowed = ['university_elective', 'college_elective', 'major_elective']
        if v not in allowed:
            raise ValueError(f'Category must be one of: {", ".join(allowed)}')
        return v


class ElectiveGroupCreate(ElectiveGroupBase):
    """Schema for creating an elective group."""
    
    pass


class ElectiveGroupUpdate(BaseModel):
    """Schema for updating an elective group."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    required_hours: Optional[int] = Field(None, gt=0)
    min_courses: Optional[int] = Field(None, ge=1)
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category value if provided."""
        if v:
            allowed = ['university_elective', 'college_elective', 'major_elective']
            if v not in allowed:
                raise ValueError(f'Category must be one of: {", ".join(allowed)}')
        return v


class ElectiveGroupCourse(BaseModel):
    """Course within an elective group."""
    
    course_id: UUID
    course_code: Optional[str] = None
    name_ar: Optional[str] = None
    credit_hours: int
    level: int
    term: str


class ElectiveGroupResponse(ElectiveGroupBase):
    """Schema for elective group API response."""
    
    id: UUID
    curriculum_id: UUID
    course_count: int = 0
    
    class Config:
        from_attributes = True


class ElectiveGroupDetailResponse(ElectiveGroupResponse):
    """Schema for elective group with nested courses."""
    
    courses: List[ElectiveGroupCourse] = []


# =============================================================================
# Course Prerequisite Graph Schemas
# =============================================================================

class PrerequisiteGraphNode(BaseModel):
    """Node in prerequisite graph."""
    
    id: UUID
    course_code: Optional[str] = None
    name_ar: str
    level: int
    term: str
    status: str  # passed, failed, not_taken, blocked


class PrerequisiteGraphEdge(BaseModel):
    """Edge in prerequisite graph."""
    
    from_course_id: UUID
    to_course_id: UUID
    minimum_grade: Optional[str] = None


class PrerequisiteGraphResponse(BaseModel):
    """Prerequisite graph response."""
    
    nodes: List[PrerequisiteGraphNode]
    edges: List[PrerequisiteGraphEdge]