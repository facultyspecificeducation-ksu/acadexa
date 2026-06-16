"""
================================================================================
User Pydantic Schemas
================================================================================

Request/response validation schemas for user management and roles.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class ProfileBase(BaseModel):
    """Base profile schema."""
    
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    is_active: bool = True


class ProfileCreate(ProfileBase):
    """Schema for creating a profile (via auth trigger)."""
    
    id: UUID


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProfileResponse(ProfileBase):
    """Schema for profile API response."""
    
    id: UUID
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema."""
    
    code: str = Field(..., min_length=1, max_length=50)
    name_ar: str = Field(..., min_length=1, max_length=100)
    name_en: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """Schema for role API response."""
    
    id: UUID
    
    class Config:
        from_attributes = True


class UserRoleAssignment(BaseModel):
    """Schema for assigning a role to a user."""
    
    role_code: str = Field(..., pattern="^(admin|academic_advisor)$")


class UserWithRolesResponse(ProfileResponse):
    """Profile response with roles."""
    
    roles: List[str] = []


class UserListResponse(BaseModel):
    """Paginated user list response."""
    
    items: List[UserWithRolesResponse]
    total: int
    page: int
    limit: int
    pages: int


class PasswordChangeRequest(BaseModel):
    """Schema for password change."""
    
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str
    new_password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Schema for login response."""
    
    access_token: str
    refresh_token: str
    user: UserWithRolesResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Schema for refresh token response."""
    
    access_token: str


class InviteUserRequest(BaseModel):
    """Schema for inviting a new user."""
    
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)