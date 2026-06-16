"""
================================================================================
FastAPI Dependencies for Acadexa API
================================================================================

This module provides dependency injection functions for:
- Authentication (current user with token)
- Role-based authorization (admin, advisor, staff)
- Authenticated Supabase client (for RLS-compatible queries)
- Service instantiation with authenticated clients

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from typing import Optional

from fastapi import Depends, Request
from supabase import Client

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import (
    SecurityContext,
    extract_token_from_request,
    fetch_user_roles,
    verify_jwt_token,
)
from app.core.supabase import get_authenticated_client, get_service_role_client

logger = logging.getLogger("acadexa.dependencies")


async def get_current_user(request: Request) -> SecurityContext:
    """
    Extract and validate the current user from the JWT token.
    
    Fetches user roles from the database using the security module's
    cached role fetching, and stores the access token in the SecurityContext
    for creating authenticated Supabase clients.
    
    Returns:
        SecurityContext with user info, roles, and access token
        
    Raises:
        UnauthorizedError: If token is missing or invalid
    """
    token = extract_token_from_request(request)
    if not token:
        raise UnauthorizedError("Authentication required")
    
    try:
        payload = verify_jwt_token(token)
    except UnauthorizedError:
        raise
    
    user_id = payload.get("sub")
    email = payload.get("email", "")
    
    if not user_id:
        raise UnauthorizedError("Invalid token: missing user ID")
    
    # Use the security module's cached role fetcher
    roles = await fetch_user_roles(user_id)
    
    logger.debug(f"User {user_id} has roles: {roles}")
    
    return SecurityContext(
        user_id=user_id,
        email=email,
        roles=roles,
        access_token=token,
    )


async def get_authenticated_supabase_client(
    current_user: SecurityContext = Depends(get_current_user),
) -> Client:
    """
    Get an authenticated Supabase client that respects RLS.
    
    Uses the user's JWT token from the SecurityContext.
    This client should be used for all API endpoint database operations.
    
    CORRECT Supabase v2 usage:
    - Client is created with ANON_KEY
    - JWT is attached as auth header for RLS enforcement
    - NEVER uses service_role for user-facing operations
    
    Args:
        current_user: The authenticated user's security context
        
    Returns:
        Supabase client authenticated with user's JWT token (RLS enforced)
    """
    if not current_user.access_token:
        raise UnauthorizedError("No access token available")
    
    return get_authenticated_client(current_user.access_token)


async def require_admin(current_user: SecurityContext = Depends(get_current_user)) -> SecurityContext:
    """
    Require admin role for the endpoint.
    
    Raises:
        ForbiddenError: If user is not an admin
    """
    if not current_user.is_admin:
        raise ForbiddenError("Admin access required")
    return current_user


async def require_advisor(current_user: SecurityContext = Depends(get_current_user)) -> SecurityContext:
    """
    Require academic_advisor role for the endpoint.
    
    Raises:
        ForbiddenError: If user is not an advisor or admin
    """
    if not current_user.is_staff:
        raise ForbiddenError("Academic advisor access required")
    return current_user


async def require_staff(current_user: SecurityContext = Depends(get_current_user)) -> SecurityContext:
    """
    Require any staff role (admin or advisor) for the endpoint.
    
    Raises:
        ForbiddenError: If user is not staff
    """
    if not current_user.is_staff:
        raise ForbiddenError("Staff access required")
    return current_user


async def optional_user(request: Request) -> Optional[SecurityContext]:
    """
    Get current user if authenticated, otherwise return None.
    
    Used for endpoints that optionally authenticate.
    """
    try:
        return await get_current_user(request)
    except UnauthorizedError:
        return None


# =============================================================================
# Service Dependency Factories with Authenticated Clients
# =============================================================================

async def get_student_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "StudentService":
    """Get student service instance with authenticated Supabase client."""
    from app.services.student_service import StudentService
    return StudentService(supabase_client)


async def get_department_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "DepartmentService":
    """Get department service instance with authenticated Supabase client."""
    from app.services.department_service import DepartmentService
    return DepartmentService(supabase_client)


async def get_grade_scale_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "GradeScaleService":
    """
    Get grade scale service instance with authenticated Supabase client.
    
    Uses authenticated client to respect RLS policies.
    """
    from app.services.grade_scale_service import GradeScaleService
    return GradeScaleService(supabase_client)


async def get_curriculum_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "CurriculumService":
    """Get curriculum service instance with authenticated Supabase client."""
    from app.services.curriculum_service import CurriculumService
    return CurriculumService(supabase_client)


async def get_course_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "CourseService":
    """Get course service instance with authenticated Supabase client."""
    from app.services.course_service import CourseService
    return CourseService(supabase_client)


async def get_advisor_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "AdvisorService":
    """Get advisor service instance with authenticated Supabase client."""
    from app.services.advisor_service import AdvisorService
    return AdvisorService(supabase_client)


async def get_dashboard_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "DashboardService":
    """Get dashboard service instance with authenticated Supabase client."""
    from app.services.dashboard_service import DashboardService
    return DashboardService(supabase_client)


async def get_ai_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "AIService":
    """Get AI service instance with authenticated Supabase client."""
    from app.services.ai_service import AIService
    return AIService(supabase_client)


async def get_analysis_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "AnalysisService":
    """Get analysis service instance with authenticated Supabase client."""
    from app.services.analysis_service import AnalysisService
    return AnalysisService(supabase_client)


async def get_report_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "ReportService":
    """Get report service instance with authenticated Supabase client."""
    from app.services.report_service import ReportService
    return ReportService(supabase_client)


async def get_import_service() -> "ImportService":
    """
    Get import service instance.
    
    Import service uses service_role client for background processing.
    No authenticated client needed - it handles its own auth.
    """
    from app.services.import_service import ImportService
    return ImportService()


async def get_export_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "ExportService":
    """
    Get export service instance with authenticated Supabase client.
    
    Uses authenticated client to respect RLS policies.
    """
    from app.services.export_service import ExportService
    return ExportService(supabase_client)


async def get_notification_service(
    current_user: SecurityContext = Depends(get_current_user),
) -> "NotificationService":
    """
    Get notification service instance.
    
    Notifications are user-specific, so we pass the user context.
    """
    from app.services.notification_service import NotificationService
    return NotificationService(current_user.user_id)


async def get_user_service(
    supabase_client: Client = Depends(get_authenticated_supabase_client),
) -> "UserService":
    """
    Get user service instance with authenticated Supabase client.
    
    Uses authenticated client to respect RLS policies.
    
    Note: delete_user operation internally uses service_role client for auth.admin access.
    This is intentional and documented in UserService.
    """
    from app.services.user_service import UserService
    return UserService(supabase_client)