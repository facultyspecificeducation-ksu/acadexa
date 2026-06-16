"""
================================================================================
Report Service for Acadexa API
================================================================================

Business logic for report generation:
- Generate all 11 report types
- Save reports to database
- Retrieve report history
- Delete reports

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError
from app.schemas.report import (
    StudentProfileReportData,
    CourseCompletionReportData,
    AcademicPlanReportData,
    GraduationEligibilityReportData,
    AcademicRiskReportData,
    AdvisorActionReportData,
    SemesterPerformanceReportData,
    PrerequisiteViolationsReportData,
    StudentsOverviewReportData,
    AtRiskStudentsReportData,
    DepartmentAnalyticsReportData,
)

logger = logging.getLogger("acadexa.services.report")


class ReportService:
    """Service for report generation and management."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize ReportService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    async def generate_report(
        self,
        report_type: str,
        generated_by: UUID,
        student_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
    ) -> Dict:
        """
        Generate and save a report.
        
        Args:
            report_type: Type of report to generate
            generated_by: User ID generating the report
            student_id: Student ID (for student-specific reports)
            department_id: Department ID (for department reports)
            
        Returns:
            Saved report dictionary
        """
        # Generate report data based on type
        if report_type == "student_profile":
            data = await self._generate_student_profile_report(student_id)
        elif report_type == "course_completion":
            data = await self._generate_course_completion_report(student_id)
        elif report_type == "academic_plan":
            data = await self._generate_academic_plan_report(student_id)
        elif report_type == "graduation_eligibility":
            data = await self._generate_graduation_eligibility_report(student_id)
        elif report_type == "academic_risk":
            data = await self._generate_academic_risk_report(student_id)
        elif report_type == "advisor_action":
            data = await self._generate_advisor_action_report(student_id)
        elif report_type == "semester_performance":
            data = await self._generate_semester_performance_report(student_id)
        elif report_type == "prerequisite_violations":
            data = await self._generate_prerequisite_violations_report(student_id)
        elif report_type == "students_overview":
            data = await self._generate_students_overview_report(department_id)
        elif report_type == "at_risk_students":
            data = await self._generate_at_risk_students_report(department_id)
        elif report_type == "department_analytics":
            data = await self._generate_department_analytics_report(department_id)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Save to database
        report_data = {
            "report_type": report_type,
            "generated_by": str(generated_by),
            "data": data,
        }
        
        if student_id:
            report_data["student_id"] = str(student_id)
        
        if department_id:
            report_data["department_id"] = str(department_id)
        
        result = self._supabase.table("reports")\
            .insert(report_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to save report")
        
        return result.data[0]
    
    async def get_reports(
        self,
        student_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        report_type: Optional[str] = None,
        generated_by: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get reports with filtering.
        
        Args:
            student_id: Filter by student
            department_id: Filter by department
            report_type: Filter by report type
            generated_by: Filter by generator user
            date_from: Start date
            date_to: End date
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (reports list, total count)
        """
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        query = self._supabase.table("reports")\
            .select(
                "*, profiles!inner(full_name)",
                count="exact"
            )
        
        if student_id:
            query = query.eq("student_id", str(student_id))
        
        if department_id:
            query = query.eq("department_id", str(department_id))
        
        if report_type:
            query = query.eq("report_type", report_type)
        
        if generated_by:
            query = query.eq("generated_by", str(generated_by))
        
        if date_from:
            query = query.gte("created_at", date_from)
        
        if date_to:
            query = query.lte("created_at", date_to)
        
        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        reports = result.data or []
        total = result.count or 0
        
        # Add generator name
        for report in reports:
            profile = report.pop("profiles", {})
            report["generated_by_name"] = profile.get("full_name")
        
        return reports, total
    
    async def get_report_by_id(self, report_id: UUID) -> Dict:
        """
        Get a single report by ID.
        
        Args:
            report_id: Report UUID
            
        Returns:
            Report dictionary
        """
        result = self._supabase.table("reports")\
            .select("*, profiles!inner(full_name)")\
            .eq("id", str(report_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("Report", str(report_id))
        
        report = result.data[0]
        profile = report.pop("profiles", {})
        report["generated_by_name"] = profile.get("full_name")
        
        return report
    
    async def delete_report(self, report_id: UUID) -> bool:
        """
        Delete a report.
        
        Args:
            report_id: Report UUID
            
        Returns:
            True if deleted
        """
        # Check if exists
        await self.get_report_by_id(report_id)
        
        result = self._supabase.table("reports")\
            .delete()\
            .eq("id", str(report_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted report: {report_id}")
        
        return deleted
    
    # =========================================================================
    # Report Generation Methods
    # =========================================================================
    
    async def _generate_student_profile_report(self, student_id: UUID) -> Dict:
        """Generate student profile report (Report #1)."""
        # Get student summary via RPC
        summary_result = self._supabase.rpc(
            "fn_student_academic_summary",
            {"p_student_id": str(student_id)}
        ).execute()
        
        student_data = summary_result.data.get("student", {}) if summary_result.data else {}
        semesters = summary_result.data.get("semesters", []) if summary_result.data else []
        
        # Get latest analysis issues
        issues_result = self._supabase.table("analysis_issues")\
            .select("title_ar, description_ar, recommendation_ar, severity")\
            .eq("analysis_id", student_data.get("analysis_id"))\
            .order("severity", desc=True)\
            .limit(10)\
            .execute()
        
        return {
            "student": student_data,
            "semesters": semesters,
            "issues": issues_result.data or [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def _generate_course_completion_report(self, student_id: UUID) -> Dict:
        """Generate course completion report (Report #2)."""
        # Get student courses
        courses_result = self._supabase.table("student_courses")\
            .select("course_code, course_name, credit_hours, grade_letter, passed, attempt_number, is_latest_attempt")\
            .eq("student_id", str(student_id))\
            .execute()
        
        courses = courses_result.data or []
        
        passed = [c for c in courses if c.get("passed") and c.get("is_latest_attempt")]
        failed = [c for c in courses if not c.get("passed") and c.get("is_latest_attempt")]
        repeated = [c for c in courses if c.get("attempt_number", 1) > 1]
        
        return {
            "passed_courses": passed,
            "failed_courses": failed,
            "repeated_courses": repeated,
            "total_passed": len(passed),
            "total_failed": len(failed),
            "total_repeated": len(repeated),
        }
    
    async def _generate_academic_plan_report(self, student_id: UUID) -> Dict:
        """Generate academic plan report (Report #3)."""
        from app.services.student_service import StudentService
        student_service = StudentService(self._supabase)
        plan = await student_service.get_academic_plan(student_id)
        return plan
    
    async def _generate_graduation_eligibility_report(self, student_id: UUID) -> Dict:
        """Generate graduation eligibility report (Report #4)."""
        from app.services.student_service import StudentService
        student_service = StudentService(self._supabase)
        status = await student_service.get_graduation_status(student_id)
        return status
    
    async def _generate_academic_risk_report(self, student_id: UUID) -> Dict:
        """Generate academic risk report (Report #5)."""
        analysis_result = await self.get_latest_analysis(student_id)
        
        if not analysis_result:
            return {
                "risk_level": "unknown",
                "risk_factors": [],
                "gpa_trend": [],
                "failed_courses_count": 0,
                "repeated_courses_count": 0,
                "prediction": "No analysis available",
            }
        
        analysis = analysis_result.get("analysis", {})
        issues = analysis_result.get("issues", [])
        
        semesters_result = self._supabase.table("student_semesters")\
            .select("semester_number, academic_year, gpa")\
            .eq("student_id", str(student_id))\
            .order("semester_number")\
            .execute()
        
        courses_result = self._supabase.table("student_courses")\
            .select("passed, attempt_number")\
            .eq("student_id", str(student_id))\
            .eq("is_latest_attempt", True)\
            .execute()
        
        courses = courses_result.data or []
        failed_count = len([c for c in courses if not c.get("passed")])
        repeated_count = len([c for c in courses if c.get("attempt_number", 1) > 1])
        
        return {
            "risk_level": analysis.get("risk_level", "low"),
            "risk_factors": [i.get("title_ar") for i in issues if i.get("severity") in ["error", "warning"]],
            "gpa_trend": semesters_result.data or [],
            "failed_courses_count": failed_count,
            "repeated_courses_count": repeated_count,
            "prediction": "High risk of graduation delay" if analysis.get("risk_level") == "high" else "Moderate risk" if analysis.get("risk_level") == "medium" else "Low risk",
        }
    
    async def _generate_advisor_action_report(self, student_id: UUID) -> Dict:
        """Generate advisor action report (Report #6)."""
        # FIXED: Step 1 - Get latest analysis ID
        analysis_result = self._supabase.table("latest_academic_analyses")\
            .select("id")\
            .eq("student_id", str(student_id))\
            .execute()
        
        analysis_id = analysis_result.data[0]["id"] if analysis_result.data else None
        
        issues = []
        if analysis_id:
            issues_result = self._supabase.table("analysis_issues")\
                .select("title_ar, description_ar, recommendation_ar, severity")\
                .eq("analysis_id", analysis_id)\
                .eq("resolved", False)\
                .order("severity", desc=True)\
                .execute()
            issues = issues_result.data or []
        
        # Get missing mandatory courses
        plan_result = await self._generate_academic_plan_report(student_id)
        missing_courses = [c for c in plan_result.get("courses", []) if c.get("status") == "not_taken" and c.get("category") in ["university_required", "college_required", "major_required"]]
        
        return {
            "recommended_actions": [
                {"action": i.get("recommendation_ar", i.get("title_ar")), "priority": "high" if i.get("severity") == "error" else "medium"}
                for i in issues[:5]
            ],
            "priority_issues": [i.get("title_ar") for i in issues if i.get("severity") == "error"][:3],
            "suggested_courses": [c.get("name_ar") for c in missing_courses[:5]],
        }
    
    async def _generate_semester_performance_report(self, student_id: UUID) -> Dict:
        """Generate semester performance report (Report #7)."""
        semesters_result = self._supabase.table("student_semesters")\
            .select("semester_number, academic_year, term, gpa, attempted_hours, completed_hours, passed_courses, failed_courses")\
            .eq("student_id", str(student_id))\
            .order("semester_number")\
            .execute()
        
        semesters = semesters_result.data or []
        
        trend = "stable"
        if len(semesters) >= 2:
            first_gpa = semesters[0].get("gpa", 0)
            last_gpa = semesters[-1].get("gpa", 0)
            if last_gpa > first_gpa:
                trend = "improving"
            elif last_gpa < first_gpa:
                trend = "declining"
        
        return {
            "semester_performance": semesters,
            "trend": trend,
        }
    
    async def _generate_prerequisite_violations_report(self, student_id: UUID) -> Dict:
        """Generate prerequisite violations report (Report #8)."""
        from app.services.student_service import StudentService
        student_service = StudentService(self._supabase)
        status = await student_service.get_prerequisite_status(student_id)
        return status
    
    async def _generate_students_overview_report(self, department_id: UUID) -> Dict:
        """Generate students overview report (Report #9)."""
        result = self._supabase.table("department_status_overview")\
            .select("*")\
            .eq("department_id", str(department_id))\
            .execute()
        
        data = result.data[0] if result.data else {}
        
        level_result = self._supabase.table("students")\
            .select("current_level", count="exact")\
            .eq("department_id", str(department_id))\
            .eq("is_active", True)\
            .execute()
        
        level_counts = {}
        for student in level_result.data or []:
            level = student.get("current_level", "unknown")
            level_str = str(level)
            level_counts[level_str] = level_counts.get(level_str, 0) + 1
        
        return {
            "department_name_ar": data.get("department_name_ar"),
            "total_students": data.get("total_students", 0),
            "by_status": {
                "good_standing": data.get("good_standing_count", 0),
                "delayed": data.get("delayed_count", 0),
                "needs_support": data.get("needs_support_count", 0),
                "probation": data.get("probation_count", 0),
            },
            "by_level": level_counts,
            "average_gpa": data.get("average_gpa", 0),
        }
    
    async def _generate_at_risk_students_report(self, department_id: UUID) -> Dict:
        """Generate at-risk students report (Report #10)."""
        result = self._supabase.table("latest_academic_analyses")\
            .select("student_id, students!inner(name, student_code, cumulative_gpa), risk_level")\
            .eq("risk_level", "high")\
            .execute()
        
        students = []
        for item in result.data or []:
            student_info = item.get("students", {})
            students.append({
                "student_id": item.get("student_id"),
                "name": student_info.get("name"),
                "student_code": student_info.get("student_code"),
                "gpa": student_info.get("cumulative_gpa", 0),
                "risk_level": item.get("risk_level"),
            })
        
        if department_id:
            dept_result = self._supabase.table("students")\
                .select("id")\
                .eq("department_id", str(department_id))\
                .execute()
            dept_student_ids = {s["id"] for s in dept_result.data or []}
            students = [s for s in students if s["student_id"] in dept_student_ids]
        
        return {
            "students": students,
            "total_at_risk": len(students),
        }
    
    async def _generate_department_analytics_report(self, department_id: UUID) -> Dict:
        """Generate department analytics report (Report #11)."""
        dept_result = self._supabase.table("departments")\
            .select("name_ar")\
            .eq("id", str(department_id))\
            .execute()
        
        department_name = dept_result.data[0]["name_ar"] if dept_result.data else "Unknown"
        
        students_result = self._supabase.table("students")\
            .select("id, cumulative_gpa")\
            .eq("department_id", str(department_id))\
            .eq("is_active", True)\
            .execute()
        
        students = students_result.data or []
        
        gpas = [s.get("cumulative_gpa", 0) for s in students]
        avg_gpa = sum(gpas) / len(gpas) if gpas else 0
        
        courses_result = self._supabase.table("student_courses")\
            .select("course_code, course_name, passed")\
            .in_("student_id", [s["id"] for s in students])\
            .eq("is_latest_attempt", True)\
            .execute()
        
        courses = courses_result.data or []
        
        course_stats = {}
        for course in courses:
            code = course.get("course_code", "unknown")
            if code not in course_stats:
                course_stats[code] = {"total": 0, "passed": 0, "name": course.get("course_name")}
            course_stats[code]["total"] += 1
            if course.get("passed"):
                course_stats[code]["passed"] += 1
        
        most_failed = []
        for code, stats in course_stats.items():
            if stats["total"] > 0:
                fail_rate = (stats["total"] - stats["passed"]) / stats["total"]
                most_failed.append({
                    "course_code": code,
                    "course_name": stats["name"],
                    "fail_rate": round(fail_rate * 100, 2),
                    "total_students": stats["total"],
                })
        
        most_failed.sort(key=lambda x: x["fail_rate"], reverse=True)
        
        graduated_result = self._supabase.table("academic_analyses")\
            .select("student_id")\
            .eq("graduation_eligible", True)\
            .in_("student_id", [s["id"] for s in students])\
            .execute()
        
        graduation_rate = (len(graduated_result.data or []) / len(students)) * 100 if students else 0
        
        return {
            "department_id": str(department_id),
            "department_name_ar": department_name,
            "average_gpa": round(avg_gpa, 2),
            "pass_rate": 0,
            "failure_rate": 0,
            "graduation_rate": round(graduation_rate, 2),
            "most_failed_courses": most_failed[:10],
            "risk_trend": [],
        }
    
    async def get_latest_analysis(self, student_id: UUID) -> Optional[Dict]:
        """Helper to get latest analysis for a student."""
        result = self._supabase.table("latest_academic_analyses")\
            .select("*")\
            .eq("student_id", str(student_id))\
            .execute()
        
        if not result.data:
            return None
        
        analysis = result.data[0]
        
        issues_result = self._supabase.table("analysis_issues")\
            .select("*")\
            .eq("analysis_id", analysis["id"])\
            .execute()
        
        return {
            "analysis": analysis,
            "issues": issues_result.data or [],
        }