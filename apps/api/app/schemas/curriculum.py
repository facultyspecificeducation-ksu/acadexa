"""
================================================================================
Curriculum Pydantic Schemas
================================================================================

Request/response validation schemas for curricula and related entities.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CurriculumBase(BaseModel):
    """Base curriculum schema."""
    
    department_id: UUID
    regulation_year: int = Field(..., ge=2000, le=2100)
    name_ar: str = Field(..., min_length=1, max_length=200)
    total_required_hours: int = Field(..., gt=0)
    min_gpa_to_graduate: float = Field(..., ge=0.0, le=4.0)
    is_active: bool = True


class CurriculumCreate(CurriculumBase):
    """Schema for creating a new curriculum."""
    
    pass


class CurriculumUpdate(BaseModel):
    """Schema for updating a curriculum."""
    
    name_ar: Optional[str] = Field(None, min_length=1, max_length=200)
    total_required_hours: Optional[int] = Field(None, gt=0)
    min_gpa_to_graduate: Optional[float] = Field(None, ge=0.0, le=4.0)
    is_active: Optional[bool] = None


class CurriculumResponse(CurriculumBase):
    """Schema for curriculum API response."""
    
    id: UUID
    created_at: str
    updated_at: str
    department_name_ar: Optional[str] = None
    department_name_en: Optional[str] = None
    
    class Config:
        from_attributes = True


class GraduationRequirementsBase(BaseModel):
    """Base graduation requirements schema."""
    
    required_hours: int = Field(..., gt=0)
    min_gpa: float = Field(..., ge=0.0, le=4.0)
    requires_field_training: bool = True
    field_training_levels: Optional[List[int]] = None
    requires_community_course: bool = True
    community_course_name_ar: str = "القضايا المجتمعية"
    max_study_years: Optional[int] = Field(None, gt=0)


class GraduationRequirementsCreate(GraduationRequirementsBase):
    """Schema for creating graduation requirements."""
    
    curriculum_id: UUID


class GraduationRequirementsUpdate(GraduationRequirementsBase):
    """Schema for updating graduation requirements."""
    
    pass


class GraduationRequirementsResponse(GraduationRequirementsBase):
    """Schema for graduation requirements API response."""
    
    id: UUID
    curriculum_id: UUID
    
    class Config:
        from_attributes = True


class AcademicRulesBase(BaseModel):
    """Base academic rules schema."""
    
    probation_min_gpa: float = Field(..., ge=0.0, le=4.0)
    max_hours_regular_term: int = Field(..., gt=0)
    min_hours_regular_term: int = Field(..., gt=0)
    max_hours_summer: int = Field(..., gt=0)
    level_2_min_hours: int = Field(..., ge=0)
    level_3_min_hours: int = Field(..., ge=0)
    level_4_min_hours: int = Field(..., ge=0)
    extra_rules: Optional[Dict[str, Any]] = None
    
    @field_validator('level_3_min_hours')
    @classmethod
    def validate_level_progression(cls, v, info):
        """Validate that level hours are progressive."""
        values = info.data
        if 'level_2_min_hours' in values and v < values['level_2_min_hours']:
            raise ValueError('level_3_min_hours must be >= level_2_min_hours')
        return v
    
    @field_validator('level_4_min_hours')
    @classmethod
    def validate_level_4_progression(cls, v, info):
        """Validate that level 4 hours are >= level 3."""
        values = info.data
        if 'level_3_min_hours' in values and v < values['level_3_min_hours']:
            raise ValueError('level_4_min_hours must be >= level_3_min_hours')
        return v


class AcademicRulesCreate(AcademicRulesBase):
    """Schema for creating academic rules."""
    
    curriculum_id: UUID


class AcademicRulesUpdate(AcademicRulesBase):
    """Schema for updating academic rules."""
    
    pass


class AcademicRulesResponse(AcademicRulesBase):
    """Schema for academic rules API response."""
    
    id: UUID
    curriculum_id: UUID
    
    class Config:
        from_attributes = True


class CurriculumListResponse(BaseModel):
    """Paginated curriculum list response."""
    
    items: List[CurriculumResponse]
    total: int
    page: int
    limit: int
    pages: int


class CurriculumDetailResponse(CurriculumResponse):
    """Curriculum detail response with nested requirements."""
    
    graduation_requirements: Optional[GraduationRequirementsResponse] = None
    academic_rules: Optional[AcademicRulesResponse] = None