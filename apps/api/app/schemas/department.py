"""
================================================================================
Department Pydantic Schemas
================================================================================

Request/response validation schemas for department-related endpoints.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DepartmentBase(BaseModel):
    """Base department schema with common fields."""
    
    code: str = Field(..., min_length=1, max_length=20, description="Department code (unique)")
    name_ar: str = Field(..., min_length=1, max_length=200, description="Arabic name")
    name_en: str = Field(..., min_length=1, max_length=200, description="English name")
    short_name: Optional[str] = Field(None, max_length=50, description="Short name/abbreviation")
    is_active: bool = Field(True, description="Whether department is active")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate department code format."""
        if not v.isalnum() and "_" not in v:
            raise ValueError("Code must contain only letters, numbers, and underscores")
        return v.upper()


class DepartmentUpdate(BaseModel):
    """Schema for updating an existing department."""
    
    name_ar: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, min_length=1, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department API responses."""
    
    id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class DepartmentWithStats(DepartmentResponse):
    """Department response with additional statistics."""
    
    curriculum_count: int = 0
    student_count: int = 0
    active_student_count: int = 0


class DepartmentListResponse(BaseModel):
    """Paginated department list response."""
    
    items: list[DepartmentResponse]
    total: int
    page: int
    limit: int
    pages: int