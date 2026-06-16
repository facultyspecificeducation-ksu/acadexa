"""
================================================================================
Notifications API Endpoints
================================================================================

Endpoints for in-app notifications:
- List notifications with filtering
- Get unread count
- Mark notifications as read
- Mark all as read
- Delete read notifications

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_notification_service, require_staff
from app.services.notification_service import NotificationService

logger = logging.getLogger("acadexa.api.notifications")

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[str] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    service: NotificationService = Depends(get_notification_service),
    _=Depends(require_staff),
):
    """
    Get notifications for the current user.
    
    Accessible by all staff members.
    """
    notifications, total = await service.get_notifications(
        is_read=is_read,
        notification_type=notification_type,
        page=page,
        limit=limit,
    )
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return {
        "items": notifications,
        "total": total,
        "unread_count": await service.get_unread_count(),
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/unread-count")
async def get_unread_count(
    service: NotificationService = Depends(get_notification_service),
    _=Depends(require_staff),
):
    """
    Get unread notification count for badge.
    
    Accessible by all staff members.
    """
    count = await service.get_unread_count()
    return {"unread_count": count}


@router.patch("/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service),
    _=Depends(require_staff),
):
    """
    Mark a single notification as read.
    
    Accessible by all staff members.
    """
    notification = await service.mark_as_read(notification_id)
    
    if not notification:
        return {"message": "Notification not found", "updated": False}
    
    return {"message": "Notification marked as read", "updated": True}


@router.post("/mark-all-read")
async def mark_all_read(
    service: NotificationService = Depends(get_notification_service),
    _=Depends(require_staff),
):
    """
    Mark all notifications as read.
    
    Accessible by all staff members.
    """
    updated_count = await service.mark_all_as_read()
    return {"message": f"{updated_count} notifications marked as read", "updated_count": updated_count}


@router.delete("/read")
async def delete_read_notifications(
    service: NotificationService = Depends(get_notification_service),
    _=Depends(require_staff),
):
    """
    Delete all read notifications.
    
    Accessible by all staff members.
    """
    deleted_count = await service.delete_read_notifications()
    return {"message": f"{deleted_count} read notifications deleted", "deleted_count": deleted_count}