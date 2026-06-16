"""
================================================================================
API v1 Router
================================================================================

Aggregates all v1 API endpoints under a single router.

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    analyses,
    auth,
    advisor_assignments,
    courses,  # ← ADDED: previously missing
    curricula,
    dashboard,
    departments,
    export,
    grade_scale,
    health,
    import_,
    notifications,
    reports,
    students,
    users,
)

router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(departments.router)
router.include_router(grade_scale.router)
router.include_router(curricula.router)
router.include_router(courses.router)  
router.include_router(students.router)
router.include_router(analyses.router)
router.include_router(advisor_assignments.router)
router.include_router(dashboard.router)
router.include_router(import_.router)
router.include_router(reports.router)
router.include_router(export.router)
router.include_router(ai.router)
router.include_router(notifications.router)