"""
================================================================================
Notification Service for Acadexa API
================================================================================

Business logic for in-app notifications:
- Create notifications for import completion, analysis completion, at-risk alerts
- Retrieve notifications for current user
- Mark notifications as read
- Delete read notifications

Note: Notifications are application-layer (no database table in schema).
They are stored in memory with TTL. For production, consider adding a
notifications table.

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.core.supabase import get_service_role_client

logger = logging.getLogger("acadexa.services.notification")


class NotificationService:
    """
    Service for in-app notifications.
    
    Note: Notifications are stored in memory. For production with multiple
    workers, consider implementing a database-backed notification system.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize NotificationService for a specific user.
        
        Args:
            user_id: User ID for which to manage notifications
        """
        self._user_id = user_id
        self._supabase = get_service_role_client()
    
    def _get_user_notifications(self) -> List[Dict]:
        """Get notifications for current user (from global store)."""
        # This would be replaced with database query in production
        # For MVP, use a simple in-memory list
        if not hasattr(NotificationService, "_global_store"):
            NotificationService._global_store = {}
        
        if self._user_id not in NotificationService._global_store:
            NotificationService._global_store[self._user_id] = []
        
        # Clean old notifications (older than 30 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        store = NotificationService._global_store[self._user_id]
        NotificationService._global_store[self._user_id] = [
            n for n in store
            if datetime.fromisoformat(n["created_at"]) > cutoff
        ]
        
        return NotificationService._global_store[self._user_id]
    
    def _save_user_notifications(self, notifications: List[Dict]) -> None:
        """Save notifications for current user."""
        if not hasattr(NotificationService, "_global_store"):
            NotificationService._global_store = {}
        NotificationService._global_store[self._user_id] = notifications
    
    async def create_notification(
        self,
        notification_type: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a new notification for the user.
        
        Args:
            notification_type: Type (import_complete, analysis_complete, at_risk)
            title: Notification title in Arabic
            body: Notification body in Arabic
            data: Additional notification data
            
        Returns:
            Created notification dictionary
        """
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": self._user_id,
            "type": notification_type,
            "title": title,
            "body": body,
            "data": data or {},
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        notifications = self._get_user_notifications()
        notifications.insert(0, notification)  # Newest first
        self._save_user_notifications(notifications)
        
        logger.info(f"Created notification for user {self._user_id}: {title}")
        return notification
    
    async def get_notifications(
        self,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get notifications for the user.
        
        Args:
            is_read: Filter by read status
            notification_type: Filter by type
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (notifications list, total count)
        """
        notifications = self._get_user_notifications()
        
        # Apply filters
        if is_read is not None:
            notifications = [n for n in notifications if n.get("is_read") == is_read]
        
        if notification_type:
            notifications = [n for n in notifications if n.get("type") == notification_type]
        
        total = len(notifications)
        
        # Apply pagination
        offset = (page - 1) * limit
        paginated = notifications[offset:offset + limit]
        
        return paginated, total
    
    async def get_unread_count(self) -> int:
        """
        Get unread notification count.
        
        Returns:
            Number of unread notifications
        """
        notifications = self._get_user_notifications()
        return len([n for n in notifications if not n.get("is_read", False)])
    
    async def mark_as_read(self, notification_id: str) -> Optional[Dict]:
        """
        Mark a single notification as read.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Updated notification or None if not found
        """
        notifications = self._get_user_notifications()
        
        for i, notification in enumerate(notifications):
            if notification["id"] == notification_id:
                notification["is_read"] = True
                notifications[i] = notification
                self._save_user_notifications(notifications)
                return notification
        
        return None
    
    async def mark_all_as_read(self) -> int:
        """
        Mark all notifications as read.
        
        Returns:
            Number of notifications updated
        """
        notifications = self._get_user_notifications()
        unread_count = len([n for n in notifications if not n.get("is_read", False)])
        
        for notification in notifications:
            notification["is_read"] = True
        
        self._save_user_notifications(notifications)
        
        return unread_count
    
    async def delete_read_notifications(self) -> int:
        """
        Delete all read notifications.
        
        Returns:
            Number of notifications deleted
        """
        notifications = self._get_user_notifications()
        read_notifications = [n for n in notifications if n.get("is_read", False)]
        unread_notifications = [n for n in notifications if not n.get("is_read", False)]
        
        deleted_count = len(read_notifications)
        self._save_user_notifications(unread_notifications)
        
        return deleted_count


# =============================================================================
# Notification Helper - Wired to Real Events
# =============================================================================

class NotificationHelper:
    """
    Helper for creating notifications from background tasks.
    
    These are called from import_service and analysis_service
    when background jobs complete.
    """
    
    @staticmethod
    async def notify_import_complete(user_id: str, job_id: str, department_name: str, total_students: int) -> None:
        """
        Create notification for import completion.
        
        Called from ImportService._parse_and_save() after successful import.
        """
        try:
            service = NotificationService(user_id)
            await service.create_notification(
                notification_type="import_complete",
                title="اكتمل استيراد البيانات",
                body=f"تم استيراد {total_students} طالب بنجاح من ملف {department_name}",
                data={"job_id": job_id, "total_students": total_students},
            )
            logger.info(f"Import notification sent to user {user_id} for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to send import notification: {e}")
    
    @staticmethod
    async def notify_import_failed(user_id: str, job_id: str, department_name: str, error: str) -> None:
        """
        Create notification for import failure.
        
        Called from ImportService._parse_and_save() after failed import.
        """
        try:
            service = NotificationService(user_id)
            await service.create_notification(
                notification_type="import_failed",
                title="فشل استيراد البيانات",
                body=f"فشل استيراد ملف {department_name}. الخطأ: {error[:100]}",
                data={"job_id": job_id, "error": error},
            )
            logger.info(f"Import failure notification sent to user {user_id} for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to send import failure notification: {e}")
    
    @staticmethod
    async def notify_analysis_complete(user_id: str, student_id: str, student_name: str) -> None:
        """
        Create notification for analysis completion.
        
        Called from AnalysisService._run_batch_analysis_background() after analysis.
        """
        try:
            service = NotificationService(user_id)
            await service.create_notification(
                notification_type="analysis_complete",
                title="اكتمل التحليل الأكاديمي",
                body=f"تم الانتهاء من تحليل الحالة الأكاديمية للطالب {student_name}",
                data={"student_id": student_id, "student_name": student_name},
            )
        except Exception as e:
            logger.error(f"Failed to send analysis notification: {e}")
    
    @staticmethod
    async def notify_batch_analysis_complete(user_id: str, job_id: str, total: int, processed: int, failed: int) -> None:
        """
        Create notification for batch analysis completion.
        
        Called from AnalysisService._run_batch_analysis_background() after batch completes.
        """
        try:
            status = "اكتمل" if failed == 0 else "اكتمل مع أخطاء"
            service = NotificationService(user_id)
            await service.create_notification(
                notification_type="batch_analysis_complete",
                title=f"{status} التحليل الأكاديمي للمجموعة",
                body=f"تم تحليل {processed} طالب من أصل {total}. الفاشل: {failed}",
                data={"job_id": job_id, "total": total, "processed": processed, "failed": failed},
            )
            logger.info(f"Batch analysis notification sent to user {user_id} for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to send batch analysis notification: {e}")
    
    @staticmethod
    async def notify_at_risk_student(user_id: str, student_id: str, student_name: str, risk_reason: str) -> None:
        """
        Create notification for at-risk student alert.
        
        Called from analysis service when high-risk student detected.
        """
        try:
            service = NotificationService(user_id)
            await service.create_notification(
                notification_type="at_risk",
                title="تنبيه: طالب في خطر أكاديمي",
                body=f"الطالب {student_name} تم تصنيفه في خطر أكاديمي مرتفع. السبب: {risk_reason}",
                data={"student_id": student_id, "student_name": student_name, "risk_reason": risk_reason},
            )
        except Exception as e:
            logger.error(f"Failed to send at-risk notification: {e}")