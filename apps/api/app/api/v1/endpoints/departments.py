"""
================================================================================
Departments API Endpoints
================================================================================

CRUD operations for departments.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import require_admin, require_staff
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.department import (
    DepartmentCreate,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentUpdate,
    DepartmentWithStats,
)
from app.services.department_service import DepartmentService

logger = logging.getLogger("acadexa.api.departments")

router = APIRouter(prefix="/departments", tags=["Departments"])


def get_department_service() -> DepartmentService:
    """Dependency for department service."""
    return DepartmentService()


@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by code or name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: DepartmentService = Depends(get_department_service),
    _=Depends(require_staff),  # Staff can view departments
):
    """
    Get list of departments with pagination and filtering.
    
    Accessible by all staff members.
    """
    departments, total = await service.get_all(
        is_active=is_active,
        search=search,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return DepartmentListResponse(
        items=[DepartmentResponse(**dept) for dept in departments],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{department_id}", response_model=DepartmentWithStats)
async def get_department(
    department_id: UUID,
    include_stats: bool = Query(True, description="Include statistics"),
    service: DepartmentService = Depends(get_department_service),
    _=Depends(require_staff),
):
    """
    Get a single department by ID.
    
    Accessible by all staff members.
    """
    if include_stats:
        department = await service.get_with_stats(department_id)
    else:
        department = await service.get_by_id(department_id)
    
    return DepartmentWithStats(**department)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service),
    _=Depends(require_admin),  # Admin only
):
    """
    Create a new department.
    
    Admin only.
    """
    try:
        created = await service.create(department)
        return DepartmentResponse(**created)
    except ConflictError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create department: {e}")
        raise


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    update_data: DepartmentUpdate,
    service: DepartmentService = Depends(get_department_service),
    _=Depends(require_admin),  # Admin only
):
    """
    Update an existing department.
    
    Admin only.
    """
    try:
        updated = await service.update(department_id, update_data)
        return DepartmentResponse(**updated)
    except NotFoundError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update department {department_id}: {e}")
        raise


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    service: DepartmentService = Depends(get_department_service),
    _=Depends(require_admin),  # Admin only
):
    """
    Delete a department.
    
    Admin only.
    Cannot delete department with associated students.
    """
    try:
        await service.delete(department_id)
    except (NotFoundError, ConflictError) as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete department {department_id}: {e}")
        raise