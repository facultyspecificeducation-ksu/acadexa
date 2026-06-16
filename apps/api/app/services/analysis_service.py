"""
================================================================================
Analysis Service for Acadexa API
================================================================================

Business logic for expert system analysis:
- Retrieve student analyses
- Trigger single student analysis
- Trigger batch analysis
- Manage analysis issues (resolve)
- Aggregate rule analytics

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.2.0
================================================================================
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError
from app.core.expert_engine import ExpertSystemEngine, AnalysisResult
from app.core.supabase import get_service_role_client

logger = logging.getLogger("acadexa.services.analysis")

# In-memory job store for batch analysis tracking
# In production, this should be replaced with a database table
_analysis_jobs: Dict[str, Dict[str, Any]] = {}


class AnalysisService:
    """Service for expert system analysis management."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize AnalysisService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
        self._expert_engine = ExpertSystemEngine()
        self._background_tasks = set()
    
    async def get_student_analyses(
        self,
        student_id: UUID,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get all analyses for a student (history).
        
        Args:
            student_id: Student UUID
            limit: Maximum number of analyses to return
            
        Returns:
            List of analysis dictionaries
        """
        result = self._supabase.table("academic_analyses")\
            .select("*")\
            .eq("student_id", str(student_id))\
            .order("analyzed_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data or []
    
    async def get_latest_analysis(self, student_id: UUID) -> Optional[Dict]:
        """
        Get the most recent analysis for a student with its issues.
        
        Args:
            student_id: Student UUID
            
        Returns:
            Dictionary with analysis and issues, or None if no analysis exists
        """
        # Use the latest_academic_analyses view
        analysis_result = self._supabase.table("latest_academic_analyses")\
            .select("*")\
            .eq("student_id", str(student_id))\
            .execute()
        
        if not analysis_result.data:
            return None
        
        analysis = analysis_result.data[0]
        
        # Get issues for this analysis
        issues_result = self._supabase.table("analysis_issues")\
            .select("*")\
            .eq("analysis_id", analysis["id"])\
            .order("severity", desc=True)\
            .execute()
        
        return {
            "analysis": analysis,
            "issues": issues_result.data or [],
        }
    
    async def run_single_analysis(self, student_id: UUID) -> Dict:
        """
        Run expert system analysis for a single student.
        
        Args:
            student_id: Student UUID
            
        Returns:
            Dictionary with analysis_id and status
        """
        # Verify student exists
        student_result = self._supabase.table("students")\
            .select("id")\
            .eq("id", str(student_id))\
            .execute()
        
        if not student_result.data:
            raise NotFoundError("Student", str(student_id))
        
        # Run expert system analysis
        analysis_result = await self._expert_engine.analyze_student(student_id)
        
        # Save to database
        analysis_id, issue_ids = await self._expert_engine.save_analysis(analysis_result)
        
        logger.info(f"Analysis completed for student {student_id}: {analysis_id}")
        
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "issues_count": len(issue_ids),
        }
    
    async def _save_analysis_result(self, analysis_result: AnalysisResult) -> Tuple[str, List[str]]:
        """
        Save analysis results to database.
        
        Args:
            analysis_result: AnalysisResult from expert engine
            
        Returns:
            Tuple of (analysis_id, list of issue_ids)
        """
        return await self._expert_engine.save_analysis(analysis_result)
    
    async def run_batch_analysis(self, student_ids: List[UUID]) -> Dict:
        """
        Run expert system analysis for multiple students.
        
        Starts a background task and returns job_id immediately.
        
        Args:
            student_ids: List of student UUIDs
            
        Returns:
            Dictionary with job_id and total count
        """
        job_id = str(uuid.uuid4())
        total = len(student_ids)
        
        # Initialize job state
        _analysis_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "total": total,
            "processed": 0,
            "failed": 0,
            "completed_at": None,
            "error": None,
        }
        
        # Start background task
        task = asyncio.create_task(
            self._run_batch_analysis_background(job_id, student_ids)
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        logger.info(f"Batch analysis job {job_id} started for {total} students")
        
        return {
            "job_id": job_id,
            "total": total,
            "status": "pending",
        }
    
    async def _run_batch_analysis_background(self, job_id: str, student_ids: List[UUID]) -> None:
        """
        Background task for batch analysis.
        
        Args:
            job_id: Job ID
            student_ids: List of student UUIDs
        """
        # Update status to processing
        _analysis_jobs[job_id]["status"] = "processing"
        
        processed = 0
        failed = 0
        results = []
        
        # Process with concurrency limit to avoid overwhelming the database
        semaphore = asyncio.Semaphore(5)
        
        async def process_one(student_id: UUID, index: int):
            nonlocal processed, failed
            async with semaphore:
                try:
                    result = await self.run_single_analysis(student_id)
                    processed += 1
                    _analysis_jobs[job_id]["processed"] = processed
                    results.append({"student_id": str(student_id), "status": "success", **result})
                    return True
                except Exception as e:
                    failed += 1
                    _analysis_jobs[job_id]["failed"] = failed
                    logger.error(f"Failed to analyze student {student_id}: {e}")
                    results.append({"student_id": str(student_id), "status": "failed", "error": str(e)})
                    return False
        
        # Run all tasks with concurrency limit
        tasks = [process_one(sid, idx) for idx, sid in enumerate(student_ids)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update job status
        _analysis_jobs[job_id]["status"] = "completed"
        _analysis_jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _analysis_jobs[job_id]["results"] = results
        
        logger.info(f"Batch analysis job {job_id} completed: {processed} success, {failed} failed")
    
    async def get_batch_job_status(self, job_id: str) -> Dict:
        """
        Get status of a batch analysis job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dictionary
        """
        job = _analysis_jobs.get(job_id)
        if not job:
            raise NotFoundError("BatchJob", job_id)
        
        return job
    
    async def resolve_issue(self, issue_id: UUID, resolved: bool = True) -> Dict:
        """
        Mark an analysis issue as resolved or unresolved.
        
        Args:
            issue_id: Issue UUID
            resolved: New resolved status
            
        Returns:
            Updated issue dictionary
        """
        # Verify issue exists
        issue_result = self._supabase.table("analysis_issues")\
            .select("id")\
            .eq("id", str(issue_id))\
            .execute()
        
        if not issue_result.data:
            raise NotFoundError("AnalysisIssue", str(issue_id))
        
        result = self._supabase.table("analysis_issues")\
            .update({"resolved": resolved})\
            .eq("id", str(issue_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update issue")
        
        logger.info(f"Issue {issue_id} marked as resolved={resolved}")
        return result.data[0]
    
    async def resolve_bulk_issues(self, issue_ids: List[UUID], resolved: bool = True) -> Dict:
        """
        Mark multiple analysis issues as resolved.
        
        Optimized with single update query using .in_().
        
        Args:
            issue_ids: List of issue UUIDs
            resolved: New resolved status
            
        Returns:
            Dictionary with updated count
        """
        if not issue_ids:
            return {"total": 0, "updated": 0, "resolved": resolved}
        
        # Single update query instead of per-issue loop
        str_ids = [str(i) for i in issue_ids]
        result = self._supabase.table("analysis_issues")\
            .update({"resolved": resolved})\
            .in_("id", str_ids)\
            .execute()
        
        updated = len(result.data) if result.data else 0
        
        logger.info(f"Bulk resolved {updated} issues")
        
        return {
            "total": len(issue_ids),
            "updated": updated,
            "resolved": resolved,
        }
    
    async def get_issues(
        self,
        rule_code: Optional[str] = None,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        department_id: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get analysis issues with filtering.
        
        Args:
            rule_code: Filter by rule code
            severity: Filter by severity (info, warning, error)
            resolved: Filter by resolved status
            department_id: Filter by department (via student)
            date_from: Start date filter
            date_to: End date filter
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (issues list, total count)
        """
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        query = self._supabase.table("analysis_issues")\
            .select(
                "*, academic_analyses!inner(student_id, analyzed_at, academic_status, risk_level), "
                "students!inner(name, student_code, department_id)",
                count="exact"
            )
        
        if rule_code:
            query = query.eq("rule_code", rule_code)
        
        if severity:
            query = query.eq("severity", severity)
        
        if resolved is not None:
            query = query.eq("resolved", resolved)
        
        if department_id:
            query = query.eq("academic_analyses.students.department_id", str(department_id))
        
        if date_from:
            query = query.gte("created_at", date_from)
        
        if date_to:
            query = query.lte("created_at", date_to)
        
        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        issues = result.data or []
        total = result.count or 0
        
        # Flatten nested structures
        for issue in issues:
            analysis = issue.pop("academic_analyses", {})
            issue["student_id"] = analysis.get("student_id")
            issue["analyzed_at"] = analysis.get("analyzed_at")
        
        return issues, total
    
    async def get_issue_analytics(self) -> Dict:
        """
        Get aggregated analytics over analysis issues.
        
        Returns:
            Dictionary with top_rules, severity_distribution, weekly_firings
        """
        # Get all issues
        result = self._supabase.table("analysis_issues")\
            .select("rule_code, severity, created_at")\
            .execute()
        
        issues = result.data or []
        
        # Count by rule code
        rule_counts = {}
        severity_counts = {"info": 0, "warning": 0, "error": 0}
        weekly_counts = {}
        
        for issue in issues:
            rule_code = issue.get("rule_code", "unknown")
            rule_counts[rule_code] = rule_counts.get(rule_code, 0) + 1
            
            severity = issue.get("severity", "info")
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            created_at = issue.get("created_at")
            if created_at:
                # Extract week (simplified)
                week = created_at[:10]  # YYYY-MM-DD
                weekly_counts[week] = weekly_counts.get(week, 0) + 1
        
        # Get top 10 rules
        top_rules = sorted(
            [{"rule_code": k, "count": v} for k, v in rule_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        # Format weekly firings
        weekly_firings = [{"week": k, "count": v} for k, v in sorted(weekly_counts.items())]
        
        return {
            "top_rules": top_rules,
            "severity_distribution": severity_counts,
            "weekly_firings": weekly_firings[-12:],  # Last 12 weeks
        }