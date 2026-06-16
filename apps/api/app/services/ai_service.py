"""
================================================================================
AI Service for Acadexa API
================================================================================

Business logic for AI assistant:
- Chat with context (student data + recommendations)
- Explain recommendations in plain Arabic
- Scope guard to prevent AI from inventing academic decisions

Security: Accepts authenticated Supabase client for RLS compliance.
Rate limiting applied at endpoint level.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import json
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError

logger = logging.getLogger("acadexa.services.ai")


class AIService:
    """
    Service for AI assistant functionality.
    
    Note: AI integration is optional. This service provides the interface
    for future OpenAI/Anthropic integration. For MVP, returns canned responses.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize AIService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
        """
        self._supabase = supabase_client
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        Process chat message with context.
        
        Args:
            messages: List of message objects with role and content
            context: Optional context (student_id, etc.)
            
        Returns:
            Assistant response with context
        """
        student_id = context.get("student_id") if context else None
        
        # Build context from student data if provided
        student_context = ""
        if student_id:
            student_context = await self._build_student_context(student_id)
        
        # Get last user message
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # For MVP, return rule-based response
        # In production, integrate with OpenAI API
        response = await self._generate_response(last_user_message, student_context)
        
        return {
            "role": "assistant",
            "content": response,
            "context_used": {"has_student_context": bool(student_id)},
        }
    
    async def explain_recommendation(self, issue_id: UUID) -> Dict:
        """
        Generate plain Arabic explanation for a recommendation.
        
        Args:
            issue_id: Analysis issue UUID
            
        Returns:
            Explanation dictionary with original and plain versions
        """
        # Get issue
        issue_result = self._supabase.table("analysis_issues")\
            .select("*, academic_analyses!inner(student_id)")\
            .eq("id", str(issue_id))\
            .execute()
        
        if not issue_result.data:
            raise NotFoundError("AnalysisIssue", str(issue_id))
        
        issue = issue_result.data[0]
        analysis = issue.get("academic_analyses", {})
        student_id = analysis.get("student_id")
        
        # Get student info
        student_result = self._supabase.table("students")\
            .select("name, student_code, cumulative_gpa")\
            .eq("id", str(student_id))\
            .execute()
        
        student_name = student_result.data[0]["name"] if student_result.data else "الطالب"
        
        # Generate plain explanation
        plain_explanation = self._generate_plain_explanation(
            title_ar=issue.get("title_ar", ""),
            description_ar=issue.get("description_ar", ""),
            recommendation_ar=issue.get("recommendation_ar"),
            student_name=student_name,
        )
        
        return {
            "original_title": issue.get("title_ar"),
            "original_description": issue.get("description_ar"),
            "original_recommendation": issue.get("recommendation_ar"),
            "plain_explanation": plain_explanation,
            "issue_id": str(issue_id),
        }
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    async def _build_student_context(self, student_id: UUID) -> str:
        """
        Build context string from student data for AI.
        
        Args:
            student_id: Student UUID
            
        Returns:
            Context string
        """
        # Get student basic info
        student_result = self._supabase.table("students")\
            .select("name, student_code, cumulative_gpa, completed_hours, attempted_hours, current_level")\
            .eq("id", str(student_id))\
            .execute()
        
        if not student_result.data:
            return ""
        
        student = student_result.data[0]
        
        # Get latest analysis
        analysis_result = self._supabase.table("latest_academic_analyses")\
            .select("academic_status, risk_level, graduation_eligible")\
            .eq("student_id", str(student_id))\
            .execute()
        
        analysis = analysis_result.data[0] if analysis_result.data else {}
        
        # Get top unresolved issues
        if analysis:
            issues_result = self._supabase.table("analysis_issues")\
                .select("title_ar, description_ar")\
                .eq("analysis_id", analysis.get("id"))\
                .eq("resolved", False)\
                .order("severity", desc=True)\
                .limit(5)\
                .execute()
            
            issues = issues_result.data or []
        else:
            issues = []
        
        # Build context
        context_parts = [
            f"الطالب: {student.get('name')} (كود: {student.get('student_code')})",
            f"المعدل التراكمي: {student.get('cumulative_gpa', 0)}",
            f"الساعات المكتملة: {student.get('completed_hours', 0)} من {student.get('attempted_hours', 0)}",
            f"المستوى الحالي: {student.get('current_level', 'غير محدد')}",
        ]
        
        if analysis.get("academic_status"):
            status_labels = {
                "good_standing": "حالة جيدة",
                "delayed": "متأخر أكاديمياً",
                "needs_support": "يحتاج دعم أكاديمي",
                "probation": "تحت الإنذار الأكاديمي",
            }
            context_parts.append(f"الحالة الأكاديمية: {status_labels.get(analysis['academic_status'], analysis['academic_status'])}")
        
        if analysis.get("risk_level"):
            risk_labels = {"low": "منخفض", "medium": "متوسط", "high": "مرتفع"}
            context_parts.append(f"مستوى الخطر: {risk_labels.get(analysis['risk_level'], analysis['risk_level'])}")
        
        if issues:
            context_parts.append("\nالمشكلات الأكاديمية:")
            for i, issue in enumerate(issues[:3], 1):
                context_parts.append(f"{i}. {issue.get('title_ar')}")
        
        return "\n".join(context_parts)
    
    async def _generate_response(self, user_message: str, context: str) -> str:
        """
        Generate AI response (MVP rule-based, replace with OpenAI later).
        
        Args:
            user_message: User's message
            context: Student context string
            
        Returns:
            Assistant response
        """
        user_message_lower = user_message.lower()
        
        # Check for graduation-related questions
        if "تخرج" in user_message_lower or "graduation" in user_message_lower:
            if context:
                return self._check_graduation_in_context(context)
            return "يرجى تحديد الطالب أولاً للاستعلام عن حالة التخرج."
        
        # Check for GPA-related questions
        if "معدل" in user_message_lower or "gpa" in user_message_lower:
            if context:
                return self._check_gpa_in_context(context)
            return "يرجى تحديد الطالب أولاً للاستعلام عن المعدل التراكمي."
        
        # Check for course recommendations
        if "مقرر" in user_message_lower or "تسجيل" in user_message_lower or "course" in user_message_lower:
            if context:
                return self._get_course_recommendation(context)
            return "يرجى تحديد الطالب أولاً للحصول على توصيات بشأن المقررات."
        
        # Default response
        if context:
            return "أنا هنا لمساعدتك في الاستشارات الأكاديمية. يمكنك سؤالي عن حالة الطالب، التخرج، المعدل التراكمي، أو توصيات المقررات."
        
        return "أنا هنا لمساعدتك في الاستشارات الأكاديمية. يرجى اختيار طالب أولاً للحصول على معلومات مخصصة، أو اسألني عن النظام بشكل عام."
    
    def _check_graduation_in_context(self, context: str) -> str:
        """Extract graduation status from context."""
        if "أهلية التخرج" in context:
            return "بناءً على البيانات المتاحة، الطالب غير مؤهل للتخرج حالياً. يرجى مراجعة متطلبات التخرج المتبقية في ملف الطالب."
        return "لم يتم العثور على معلومات حول حالة التخرج. يرجى تشغيل التحليل الأكاديمي أولاً."
    
    def _check_gpa_in_context(self, context: str) -> str:
        """Extract GPA from context."""
        import re
        match = re.search(r'المعدل التراكمي: ([\d.]+)', context)
        if match:
            gpa = float(match.group(1))
            if gpa < 2.0:
                return f"المعدل التراكمي للطالب هو {gpa}. هذا أقل من المعدل الموصى به. يُنصح الطالب بتحسين أدائه الأكاديمي."
            elif gpa < 3.0:
                return f"المعدل التراكمي للطالب هو {gpa}. هذا معدل مقبول، لكن يمكن تحسينه."
            else:
                return f"المعدل التراكمي للطالب هو {gpa}. هذا معدل جيد جداً. استمر بنفس المستوى."
        return "لم يتم العثور على معلومات المعدل التراكمي."
    
    def _get_course_recommendation(self, context: str) -> str:
        """Generate course recommendation based on context."""
        if "المشكلات الأكاديمية" in context:
            return "بناءً على التحليل، يُنصح الطالب بالتركيز على اجتياز المقررات الراسبة والمتطلبات السابقة قبل التسجيل في مقررات متقدمة."
        return "يُنصح الطالب بمراجعة الخطة الدراسية مع المرشد الأكاديمي لتحديد المقررات المناسبة للفصل القادم."
    
    def _generate_plain_explanation(
        self,
        title_ar: str,
        description_ar: str,
        recommendation_ar: Optional[str],
        student_name: str,
    ) -> str:
        """
        Generate plain Arabic explanation for a recommendation.
        
        Args:
            title_ar: Issue title in Arabic
            description_ar: Issue description in Arabic
            recommendation_ar: Recommendation in Arabic (if any)
            student_name: Student name
            
        Returns:
            Plain explanation string
        """
        parts = [f"بالنسبة للطالب {student_name}:"]
        parts.append(description_ar)
        
        if recommendation_ar:
            parts.append(f"\nالتوصية: {recommendation_ar}")
        
        return "\n".join(parts)