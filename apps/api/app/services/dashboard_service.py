"""
================================================================================
Dashboard Service for Acadexa API
================================================================================

Business logic for dashboard analytics:
- KPI aggregation (total students, high risk, probation, graduation eligible)
- Academic status distribution chart data
- GPA distribution histogram
- At-risk students list (top N)
- Department status overview
- Department statistics (historical snapshots)

Security: Accepts authenticated Supabase client for RLS compliance.
All queries are optimized with proper indexes and aggregated queries.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError

logger = logging.getLogger("acadexa.services.dashboard")


class DashboardService:
    """Service for dashboard analytics and KPIs."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize DashboardService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    # =========================================================================
    # KPI Aggregation
    # =========================================================================
    
    async def get_kpi_overview(self, department_id: Optional[UUID] = None) -> Dict:
        """
        Get KPI data for dashboard cards.
        
        Single aggregated query - optimized to avoid multiple round trips.
        
        Args:
            department_id: Optional department filter (admin only)
            
        Returns:
            Dictionary with KPI values
        """
        # Build student query
        student_query = self._supabase.table("students")\
            .select("id", count="exact")\
            .eq("is_active", True)
        
        if department_id:
            student_query = student_query.eq("department_id", str(department_id))
        
        student_result = student_query.execute()
        total_active_students = student_result.count or 0
        
        # Get at-risk and probation counts from latest_academic_analyses view
        # Single query with conditional aggregation
        risk_query = self._supabase.table("latest_academic_analyses")\
            .select("risk_level, academic_status", count="exact")
        
        if department_id:
            # Need to join with students table
            risk_query = self._supabase.table("latest_academic_analyses")\
                .select("risk_level, academic_status, students!inner(department_id)", count="exact")\
                .eq("students.department_id", str(department_id))
        
        risk_result = risk_query.execute()
        
        high_risk_count = 0
        probation_count = 0
        graduation_eligible_count = 0
        
        for item in risk_result.data or []:
            if item.get("risk_level") == "high":
                high_risk_count += 1
            if item.get("academic_status") == "probation":
                probation_count += 1
        
        # Get graduation eligible count
        eligible_query = self._supabase.table("latest_academic_analyses")\
            .select("id", count="exact")\
            .eq("graduation_eligible", True)
        
        if department_id:
            eligible_query = self._supabase.table("latest_academic_analyses")\
                .select("id, students!inner(department_id)", count="exact")\
                .eq("graduation_eligible", True)\
                .eq("students.department_id", str(department_id))
        
        eligible_result = eligible_query.execute()
        graduation_eligible_count = eligible_result.count or 0
        
        return {
            "total_active_students": total_active_students,
            "high_risk_count": high_risk_count,
            "probation_count": probation_count,
            "graduation_eligible_count": graduation_eligible_count,
        }
    
    # =========================================================================
    # Academic Status Distribution (Donut Chart)
    # =========================================================================
    
    async def get_academic_status_distribution(self, department_id: Optional[UUID] = None) -> Dict:
        """
        Get counts by academic_status for donut chart.
        
        Uses department_status_overview view for efficient aggregation.
        
        Args:
            department_id: Optional department filter
            
        Returns:
            Dictionary with status counts
        """
        if department_id:
            result = self._supabase.table("department_status_overview")\
                .select("*")\
                .eq("department_id", str(department_id))\
                .execute()
            
            data = result.data[0] if result.data else {}
            
            return {
                "good_standing": data.get("good_standing_count", 0),
                "delayed": data.get("delayed_count", 0),
                "needs_support": data.get("needs_support_count", 0),
                "probation": data.get("probation_count", 0),
            }
        else:
            # Aggregate across all departments
            result = self._supabase.table("department_status_overview")\
                .select("good_standing_count, delayed_count, needs_support_count, probation_count")\
                .execute()
            
            total_good = 0
            total_delayed = 0
            total_needs_support = 0
            total_probation = 0
            
            for row in result.data or []:
                total_good += row.get("good_standing_count", 0)
                total_delayed += row.get("delayed_count", 0)
                total_needs_support += row.get("needs_support_count", 0)
                total_probation += row.get("probation_count", 0)
            
            return {
                "good_standing": total_good,
                "delayed": total_delayed,
                "needs_support": total_needs_support,
                "probation": total_probation,
            }
    
    # =========================================================================
    # GPA Distribution Histogram
    # =========================================================================
    
    async def get_gpa_distribution(self, department_id: Optional[UUID] = None) -> List[Dict]:
        """
        Get GPA distribution histogram (bucketed).
        
        Buckets: 0-1, 1-2, 2-3, 3-4
        
        Args:
            department_id: Optional department filter
            
        Returns:
            List of bucket objects with count
        """
        query = self._supabase.table("students")\
            .select("cumulative_gpa")\
            .eq("is_active", True)
        
        if department_id:
            query = query.eq("department_id", str(department_id))
        
        result = query.execute()
        
        buckets = {
            "0-1": 0,
            "1-2": 0,
            "2-3": 0,
            "3-4": 0,
        }
        
        for student in result.data or []:
            gpa = student.get("cumulative_gpa", 0)
            if gpa < 1:
                buckets["0-1"] += 1
            elif gpa < 2:
                buckets["1-2"] += 1
            elif gpa < 3:
                buckets["2-3"] += 1
            else:
                buckets["3-4"] += 1
        
        return [
            {"range": "0-1", "count": buckets["0-1"]},
            {"range": "1-2", "count": buckets["1-2"]},
            {"range": "2-3", "count": buckets["2-3"]},
            {"range": "3-4", "count": buckets["3-4"]},
        ]
    
    # =========================================================================
    # At-Risk Students List (Top N)
    # =========================================================================
    
    async def get_at_risk_students(
        self,
        department_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get top N at-risk students (high risk level).
        
        Uses latest_academic_analyses view with proper indexes.
        
        Args:
            department_id: Optional department filter
            limit: Maximum number of students to return
            
        Returns:
            List of student dictionaries with risk details
        """
        query = self._supabase.table("latest_academic_analyses")\
            .select(
                "student_id, risk_level, analyzed_at, "
                "students!inner(id, student_code, name, cumulative_gpa, department_id, departments!inner(name_ar))"
            )\
            .eq("risk_level", "high")\
            .order("analyzed_at", desc=True)\
            .limit(limit)
        
        if department_id:
            query = query.eq("students.department_id", str(department_id))
        
        result = query.execute()
        
        students = []
        for item in result.data or []:
            student_info = item.get("students", {})
            dept_info = student_info.get("departments", {}) if student_info else {}
            
            students.append({
                "student_id": item.get("student_id"),
                "student_code": student_info.get("student_code"),
                "name": student_info.get("name"),
                "cumulative_gpa": student_info.get("cumulative_gpa", 0),
                "department_name_ar": dept_info.get("name_ar"),
                "risk_level": item.get("risk_level"),
                "analyzed_at": item.get("analyzed_at"),
            })
        
        return students
    
    # =========================================================================
    # Department Status Overview (Table)
    # =========================================================================
    
    async def get_department_status(self, department_id: Optional[UUID] = None) -> List[Dict]:
        """
        Get department status overview from view.
        
        Uses department_status_overview view - single efficient query.
        
        Args:
            department_id: Optional single department filter
            
        Returns:
            List of department status dictionaries
        """
        query = self._supabase.table("department_status_overview")\
            .select("*")
        
        if department_id:
            query = query.eq("department_id", str(department_id))
        
        result = query.order("department_name_ar").execute()
        
        return result.data or []
    
    # =========================================================================
    # Department Statistics (Historical)
    # =========================================================================
    
    async def get_department_statistics(
        self,
        department_id: UUID,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get historical department statistics snapshots.
        
        Used for trend charts (Report #11).
        
        Args:
            department_id: Department UUID
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            
        Returns:
            List of statistics snapshots
        """
        query = self._supabase.table("department_statistics")\
            .select("*")\
            .eq("department_id", str(department_id))\
            .order("calculated_at", desc=True)
        
        if date_from:
            query = query.gte("calculated_at", date_from)
        
        if date_to:
            query = query.lte("calculated_at", date_to)
        
        result = query.execute()
        
        return result.data or []
    
    async def create_department_snapshot(self, department_id: UUID) -> Dict:
        """
        Create a new department statistics snapshot.
        
        Calculates live data and inserts into department_statistics table.
        
        Args:
            department_id: Department UUID
            
        Returns:
            Created snapshot dictionary
        """
        # Get department status from view
        status_result = self._supabase.table("department_status_overview")\
            .select("*")\
            .eq("department_id", str(department_id))\
            .execute()
        
        if not status_result.data:
            raise NotFoundError("Department", str(department_id))
        
        status = status_result.data[0]
        
        # Calculate graduation rate
        total_students = status.get("total_students", 0)
        
        # Get graduation eligible count
        eligible_result = self._supabase.table("latest_academic_analyses")\
            .select("id", count="exact")\
            .eq("students.department_id", str(department_id))\
            .eq("graduation_eligible", True)\
            .execute()
        
        graduation_eligible = eligible_result.count or 0
        graduation_rate = (graduation_eligible / total_students * 100) if total_students > 0 else 0
        
        # Get average GPA (already in view)
        average_gpa = status.get("average_gpa", 0)
        
        # Get risk students count (already in view)
        risk_students_count = status.get("high_risk_count", 0)
        
        # Create snapshot
        snapshot_data = {
            "department_id": str(department_id),
            "total_students": total_students,
            "average_gpa": average_gpa,
            "graduation_rate": round(graduation_rate, 2),
            "risk_students_count": risk_students_count,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = self._supabase.table("department_statistics")\
            .insert(snapshot_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create department snapshot")
        
        logger.info(f"Created department snapshot for {department_id}")
        return result.data[0]
    
    # =========================================================================
    # Recent Import Activity
    # =========================================================================
    
    async def get_recent_imports(self, limit: int = 5) -> List[Dict]:
        """
        Get recent import jobs for dashboard widget.
        
        Args:
            limit: Number of jobs to return
            
        Returns:
            List of recent import jobs
        """
        result = self._supabase.table("import_jobs")\
            .select("id, file_name, status, created_at, completed_at, total_students, successful_records, failed_records, departments(name_ar), profiles(full_name)")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        jobs = []
        for job in result.data or []:
            jobs.append({
                "id": job["id"],
                "file_name": job["file_name"],
                "status": job["status"],
                "created_at": job["created_at"],
                "completed_at": job.get("completed_at"),
                "total_students": job.get("total_students", 0),
                "successful_records": job.get("successful_records", 0),
                "failed_records": job.get("failed_records", 0),
                "department_name_ar": job.get("departments", {}).get("name_ar") if job.get("departments") else None,
                "uploaded_by_name": job.get("profiles", {}).get("full_name") if job.get("profiles") else None,
            })
        
        return jobs