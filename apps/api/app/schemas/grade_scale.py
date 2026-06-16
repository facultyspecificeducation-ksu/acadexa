"""
================================================================================
Grade Scale Pydantic Schemas
================================================================================

Request/response validation schemas for grade scale management.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GradeScaleBase(BaseModel):
    """Base grade scale schema."""
    
    grade_letter: str = Field(..., min_length=1, max_length=3, description="Grade letter (A, B+, W, etc.)")
    name_ar: str = Field(..., min_length=1, max_length=50, description="Arabic name")
    points: float = Field(..., ge=0, le=4, description="Grade points (0-4)")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum score for this grade")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum score for this grade")
    affects_gpa: bool = Field(True, description="Whether this grade affects GPA calculation")
    is_passing: bool = Field(False, description="Whether this grade is considered passing")
    description: Optional[str] = Field(None, max_length=500, description="Description in Arabic")


class GradeScaleCreate(GradeScaleBase):
    """Schema for creating a new grade scale entry."""
    
    @field_validator("grade_letter")
    @classmethod
    def validate_grade_letter(cls, v: str) -> str:
        """Validate grade letter format."""
        return v.upper()


class GradeScaleUpdate(BaseModel):
    """Schema for updating an existing grade scale entry."""
    
    name_ar: Optional[str] = Field(None, min_length=1, max_length=50)
    points: Optional[float] = Field(None, ge=0, le=4)
    min_score: Optional[float] = Field(None, ge=0, le=100)
    max_score: Optional[float] = Field(None, ge=0, le=100)
    affects_gpa: Optional[bool] = None
    is_passing: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator("min_score", "max_score")
    @classmethod
    def validate_score_range(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure min_score <= max_score if both provided."""
        if v is not None and info.data.get("min_score") is not None and info.data.get("max_score") is not None:
            if info.data["min_score"] > info.data["max_score"]:
                raise ValueError("min_score must be less than or equal to max_score")
        return v


class GradeScaleResponse(GradeScaleBase):
    """Schema for grade scale API responses."""
    
    class Config:
        from_attributes = True


class GradeScaleListResponse(BaseModel):
    """Grade scale list response."""
    
    items: list[GradeScaleResponse]
    total: int