"""
================================================================================
Expert System Inference Engine for Acadexa
================================================================================

This module implements the complete inference engine for academic advising:
- Academic Status Diagnosis (good_standing, delayed, needs_support, probation)
- Risk Prediction (low, medium, high)
- Graduation Eligibility Evaluation
- Prerequisite Violation Detection
- Recommendation Generation
- Explanation Generation

All rules are database-driven - thresholds come from:
- academic_rules table
- graduation_requirements table
- course_prerequisites table

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.core.supabase import get_service_role_client

logger = logging.getLogger("acadexa.expert_engine")


# =============================================================================
# Enums and Data Classes
# =============================================================================

class AcademicStatus(str, Enum):
    """Academic status values from database enum."""
    GOOD_STANDING = "good_standing"
    DELAYED = "delayed"
    NEEDS_SUPPORT = "needs_support"
    PROBATION = "probation"


class RiskLevel(str, Enum):
    """Risk level values from database enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueSeverity(str, Enum):
    """
    Issue severity levels for database storage.
    
    Maps to issue_severity_enum in database:
    - ERROR → Critical issues requiring immediate action
    - WARNING → Issues that need attention
    - INFO → Informational notes
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class RuleResult:
    """Result from a single rule evaluation."""
    rule_code: str
    severity: IssueSeverity
    title_ar: str
    description_ar: str
    recommendation_ar: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResult:
    """
    Complete analysis result for a student.
    
    Note: student_data is NOT stored here. The student data is already
    persisted in the database. This class only contains the analysis results.
    """
    student_id: UUID
    academic_status: AcademicStatus
    risk_level: RiskLevel
    graduation_eligible: bool
    issues: List[RuleResult] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# Expert System Engine
# =============================================================================

class ExpertSystemEngine:
    """
    Inference engine for academic advising.
    
    Rules are organized by category and evaluated in order:
    1. Academic Status (probation, delayed, needs_support, good_standing)
    2. Risk Assessment (graduation delay, performance decline, requirement risk)
    3. Graduation Eligibility (hours, GPA, field training, community course)
    4. Prerequisite Violations
    5. Recommendations (derived from issues)
    
    All thresholds are loaded from database at evaluation time.
    """
    
    def __init__(self):
        self._supabase = get_service_role_client()
        self._rules_cache = {}  # Cache for academic_rules per curriculum
        self._grad_req_cache = {}  # Cache for graduation_requirements
    
    # =========================================================================
    # Data Loading Methods
    # =========================================================================
    
    async def _get_academic_rules(self, curriculum_id: UUID) -> Dict[str, Any]:
        """
        Load academic rules for a curriculum.
        
        Returns:
            Dictionary with rule thresholds:
            - probation_min_gpa
            - max_hours_regular_term
            - min_hours_regular_term
            - max_hours_summer
            - level_2_min_hours
            - level_3_min_hours
            - level_4_min_hours
        """
        cache_key = str(curriculum_id)
        if cache_key in self._rules_cache:
            return self._rules_cache[cache_key]
        
        result = self._supabase.table("academic_rules")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        rules = result.data[0] if result.data else {}
        self._rules_cache[cache_key] = rules
        return rules
    
    async def _get_graduation_requirements(self, curriculum_id: UUID) -> Dict[str, Any]:
        """
        Load graduation requirements for a curriculum.
        
        Returns:
            Dictionary with requirements:
            - required_hours
            - min_gpa
            - requires_field_training
            - field_training_levels
            - requires_community_course
            - community_course_name_ar
        """
        cache_key = str(curriculum_id)
        if cache_key in self._grad_req_cache:
            return self._grad_req_cache[cache_key]
        
        result = self._supabase.table("graduation_requirements")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        reqs = result.data[0] if result.data else {}
        self._grad_req_cache[cache_key] = reqs
        return reqs
    
    async def _get_student_data(self, student_id: UUID) -> Dict[str, Any]:
        """
        Load complete student data for analysis.
        
        Returns:
            Student dictionary with:
            - Basic info (name, code, department, curriculum, enrollment_year)
            - Current academic stats (GPA, hours, level)
            - Semesters with courses
            - Passed/failed course lists
        """
        # Get student basic info
        student_result = self._supabase.table("students")\
            .select("*")\
            .eq("id", str(student_id))\
            .execute()
        
        if not student_result.data:
            raise ValueError(f"Student {student_id} not found")
        
        student = student_result.data[0]
        
        # Get all semesters with courses
        semesters_result = self._supabase.table("student_semesters")\
            .select("*")\
            .eq("student_id", str(student_id))\
            .order("semester_number")\
            .execute()
        
        semesters = semesters_result.data or []
        
        # Get all courses for this student
        courses_result = self._supabase.table("student_courses")\
            .select("*")\
            .eq("student_id", str(student_id))\
            .execute()
        
        courses = courses_result.data or []
        
        # Organize courses by semester
        semester_courses = {}
        for course in courses:
            sem_id = course.get("semester_id")
            if sem_id:
                if sem_id not in semester_courses:
                    semester_courses[sem_id] = []
                semester_courses[sem_id].append(course)
        
        # Calculate derived stats
        passed_courses = [c for c in courses if c.get("passed", False) and c.get("is_latest_attempt", True)]
        failed_courses = [c for c in courses if not c.get("passed", False) and c.get("is_latest_attempt", True)]
        repeated_courses = [c for c in courses if c.get("attempt_number", 1) > 1]
        
        # Get curriculum info
        curriculum_id = student.get("curriculum_id")
        curriculum_result = self._supabase.table("curricula")\
            .select("*")\
            .eq("id", str(curriculum_id))\
            .execute()
        
        curriculum = curriculum_result.data[0] if curriculum_result.data else {}
        
        # Get required courses for this curriculum
        required_courses_result = self._supabase.table("curriculum_courses")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .eq("is_active", True)\
            .execute()
        
        required_courses = required_courses_result.data or []
        
        # Get course prerequisites
        prereq_result = self._supabase.table("course_prerequisites")\
            .select("course_id, required_course_id, minimum_grade")\
            .execute()
        
        prerequisites = {}
        for prereq in prereq_result.data or []:
            course_id = prereq.get("course_id")
            if course_id not in prerequisites:
                prerequisites[course_id] = []
            prerequisites[course_id].append(prereq)
        
        return {
            "student": student,
            "curriculum": curriculum,
            "semesters": semesters,
            "courses": courses,
            "semester_courses": semester_courses,
            "passed_courses": passed_courses,
            "failed_courses": failed_courses,
            "repeated_courses": repeated_courses,
            "required_courses": required_courses,
            "prerequisites": prerequisites,
        }
    
    # =========================================================================
    # Rule 1: Academic Status Diagnosis
    # =========================================================================
    
    async def _evaluate_probation_status(
        self, 
        student_data: Dict, 
        academic_rules: Dict
    ) -> Optional[RuleResult]:
        """
        Check if student is on academic probation.
        
        Rule: IF cumulative_gpa < probation_min_gpa THEN status = probation
        """
        student = student_data.get("student", {})
        cumulative_gpa = student.get("cumulative_gpa", 0.0)
        
        probation_min_gpa = academic_rules.get("probation_min_gpa")
        if probation_min_gpa is None:
            return None
        
        if cumulative_gpa < probation_min_gpa:
            return RuleResult(
                rule_code="PROBATION",
                severity=IssueSeverity.ERROR,
                title_ar="إنذار أكاديمي",
                description_ar=f"المعدل التراكمي {cumulative_gpa} أقل من الحد الأدنى المطلوب {probation_min_gpa}",
                recommendation_ar="يجب تحسين المعدل التراكمي. يُنصح بالتواصل مع المرشد الأكاديمي لوضع خطة دراسة محسنة.",
                data={"current_gpa": cumulative_gpa, "required_gpa": probation_min_gpa}
            )
        return None
    
    async def _evaluate_delayed_status(
        self, 
        student_data: Dict,
        academic_rules: Dict
    ) -> Optional[RuleResult]:
        """
        Check if student is academically delayed.
        
        Rules for delayed status:
        1. Completed hours less than expected for current level
        2. Missing mandatory courses from previous levels
        """
        student = student_data.get("student", {})
        current_level = student.get("current_level", 1)
        completed_hours = student.get("completed_hours", 0)
        required_courses = student_data.get("required_courses", [])
        passed_course_ids = [c.get("curriculum_course_id") for c in student_data.get("passed_courses", [])]
        
        # Check hours requirement for level
        level_hours_key = f"level_{current_level}_min_hours"
        expected_hours = academic_rules.get(level_hours_key, 0)
        
        hours_issues = []
        course_issues = []
        
        if completed_hours < expected_hours:
            hours_issues.append(f"الساعات المكتملة {completed_hours} أقل من المتوقع {expected_hours} للمستوى {current_level}")
        
        # Check for missing mandatory courses from previous levels
        for course in required_courses:
            course_level = course.get("level", 0)
            if course_level < current_level:
                category = course.get("category", "")
                if category in ["university_required", "college_required", "major_required"]:
                    if course.get("id") not in passed_course_ids:
                        course_issues.append(course.get("name_ar", course.get("course_code", "مقرر")))
        
        if hours_issues or course_issues:
            description = ""
            if hours_issues:
                description += " • " + "\n • ".join(hours_issues) + "\n"
            if course_issues:
                description += " • مقررات إجبارية غير مكتملة: " + ", ".join(course_issues[:3])
                if len(course_issues) > 3:
                    description += f" و {len(course_issues) - 3} أخرى"
            
            return RuleResult(
                rule_code="ACADEMIC_DELAY",
                severity=IssueSeverity.WARNING,
                title_ar="تأخر أكاديمي",
                description_ar=description,
                recommendation_ar="يُنصح بتسجيل المقررات المتأخرة في الفصول القادمة ومراجعة الخطة الدراسية مع المرشد الأكاديمي.",
                data={"hours_shortfall": expected_hours - completed_hours if completed_hours < expected_hours else 0}
            )
        return None
    
    async def _evaluate_needs_support_status(
        self,
        student_data: Dict
    ) -> Optional[RuleResult]:
        """
        Check if student needs academic support.
        
        Rules:
        1. Multiple failures (3+ failed courses)
        2. Repeated failures (same course failed twice)
        3. Very low GPA trend
        """
        failed_courses = student_data.get("failed_courses", [])
        repeated_courses = student_data.get("repeated_courses", [])
        
        issues = []
        
        # Check multiple failures
        if len(failed_courses) >= 3:
            issues.append(f"عدد المقررات الراسبة: {len(failed_courses)}")
        
        # Check repeated failures (same course failed multiple times)
        repeated_failures = [c for c in repeated_courses if not c.get("passed", False)]
        if repeated_failures:
            course_names = [c.get("course_name", "") for c in repeated_failures[:3]]
            issues.append(f"مقررات راسب تم إعادتها: {', '.join(course_names)}")
        
        # Check GPA trend (decreasing)
        semesters = student_data.get("semesters", [])
        if len(semesters) >= 2:
            gpa_trend = [s.get("gpa", 0) for s in semesters[-3:]]
            if len(gpa_trend) >= 2 and gpa_trend[-1] < gpa_trend[-2]:
                issues.append("انخفاض مستمر في المعدل الفصلي")
        
        if issues:
            return RuleResult(
                rule_code="NEEDS_SUPPORT",
                severity=IssueSeverity.WARNING,
                title_ar="يحتاج دعم أكاديمي",
                description_ar="\n".join(f" • {i}" for i in issues),
                recommendation_ar="يُنصح بحضور جلسات الدعم الأكاديمي والتواصل مع المرشد لتحسين الأداء.",
                data={"failed_count": len(failed_courses), "repeated_failures": len(repeated_failures)}
            )
        return None
    
    async def _determine_academic_status(
        self,
        student_data: Dict,
        academic_rules: Dict
    ) -> Tuple[AcademicStatus, List[RuleResult]]:
        """
        Determine overall academic status by evaluating all status rules.
        
        Order of evaluation (highest severity first):
        1. Probation (most severe)
        2. Delayed
        3. Needs Support
        4. Good Standing (default)
        """
        issues = []
        
        # Check probation first (most severe)
        probation_issue = await self._evaluate_probation_status(student_data, academic_rules)
        if probation_issue:
            issues.append(probation_issue)
            return AcademicStatus.PROBATION, issues
        
        # Check delayed
        delayed_issue = await self._evaluate_delayed_status(student_data, academic_rules)
        if delayed_issue:
            issues.append(delayed_issue)
            return AcademicStatus.DELAYED, issues
        
        # Check needs support
        support_issue = await self._evaluate_needs_support_status(student_data)
        if support_issue:
            issues.append(support_issue)
            return AcademicStatus.NEEDS_SUPPORT, issues
        
        # Good standing
        return AcademicStatus.GOOD_STANDING, issues
    
    # =========================================================================
    # Rule 2: Risk Prediction
    # =========================================================================
    
    async def _evaluate_graduation_delay_risk(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> Optional[RuleResult]:
        """
        Predict risk of graduation delay.
        
        Factors:
        1. Low completion rate vs expected timeline
        2. Accumulated failed courses
        3. Prerequisite chain blocking progress
        
        Severity mapping:
        - Multiple risk factors → ERROR
        - Single significant risk factor → WARNING
        """
        student = student_data.get("student", {})
        completed_hours = student.get("completed_hours", 0)
        required_hours = graduation_reqs.get("required_hours", 0)
        current_level = student.get("current_level", 1)
        failed_courses = student_data.get("failed_courses", [])
        prerequisites = student_data.get("prerequisites", {})
        
        risk_factors = []
        
        # Factor 1: Completion rate
        if required_hours > 0:
            completion_rate = (completed_hours / required_hours) * 100
            expected_rate = (current_level / 4) * 100
            
            if completion_rate < expected_rate - 15:
                risk_factors.append(f"نسبة الإنجاز {completion_rate:.1f}% أقل من المتوقع {expected_rate:.1f}%")
        
        # Factor 2: Failed courses
        if len(failed_courses) >= 3:
            risk_factors.append(f"وجود {len(failed_courses)} مقررات راسبة")
        
        # Factor 3: Blocked courses (prerequisites not met)
        passed_course_ids = [c.get("curriculum_course_id") for c in student_data.get("passed_courses", [])]
        blocked_courses = []
        
        for course_id, prereqs in prerequisites.items():
            # Check if any prerequisite is not passed
            unmet = [p for p in prereqs if p.get("required_course_id") not in passed_course_ids]
            if unmet:
                blocked_courses.append(course_id)
        
        if len(blocked_courses) >= 2:
            risk_factors.append(f"{len(blocked_courses)} مقررات تنتظر اجتياز متطلباتها السابقة")
        
        if risk_factors:
            # Map risk factor count to IssueSeverity
            severity = IssueSeverity.ERROR if len(risk_factors) >= 2 else IssueSeverity.WARNING
            
            return RuleResult(
                rule_code="GRADUATION_DELAY_RISK",
                severity=severity,
                title_ar="خطر تأخر التخرج",
                description_ar="\n".join(f" • {f}" for f in risk_factors),
                recommendation_ar="يُنصح بتسجيل المقررات الراسبة والمتأخرة في الفصول القادمة والتركيز على اجتياز المتطلبات السابقة.",
                data={"risk_factors": risk_factors}
            )
        return None
    
    async def _evaluate_performance_decline_risk(
        self,
        student_data: Dict
    ) -> Optional[RuleResult]:
        """
        Predict risk of continued performance decline.
        
        Factors:
        1. Decreasing GPA trend
        2. High failure rate in recent semesters
        
        Severity: Always WARNING (performance decline is a warning, not critical)
        """
        semesters = student_data.get("semesters", [])
        
        if len(semesters) < 2:
            return None
        
        risk_factors = []
        
        # Check GPA trend
        recent_gpas = [s.get("gpa", 0) for s in semesters[-3:]]
        if len(recent_gpas) >= 2:
            if all(recent_gpas[i] > recent_gpas[i+1] for i in range(len(recent_gpas)-1)):
                risk_factors.append(f"انخفاض مستمر في المعدل الفصلي: {recent_gpas[0]} ← {recent_gpas[-1]}")
        
        # Check failure rate
        for semester in semesters[-2:]:
            failed = semester.get("failed_courses", 0)
            total = semester.get("total_courses", 1)
            if total > 0 and failed / total > 0.5:
                risk_factors.append(f"نسبة رسوب عالية في فصل {semester.get('academic_year', '')}")
        
        if risk_factors:
            return RuleResult(
                rule_code="PERFORMANCE_DECLINE_RISK",
                severity=IssueSeverity.WARNING,
                title_ar="خطر انخفاض الأداء الأكاديمي",
                description_ar="\n".join(f" • {f}" for f in risk_factors),
                recommendation_ar="يُنصح بمراجعة أساليب الدراسة والاستفادة من ساعات المكتبة والمراجعة مع أساتذة المقررات.",
                data={"risk_factors": risk_factors}
            )
        return None
    
    async def _determine_risk_level(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> Tuple[RiskLevel, List[RuleResult]]:
        """
        Determine overall risk level.
        
        Risk levels (RiskLevel enum, not IssueSeverity):
        - HIGH: Graduation delay risk present (ERROR severity)
        - MEDIUM: Other risk factors present (WARNING severity)
        - LOW: No significant risks
        
        Note: RiskLevel is separate from IssueSeverity.
        RiskLevel classifies the student's overall risk status.
        IssueSeverity classifies individual issue severity.
        """
        issues = []
        
        # Evaluate specific risks
        delay_risk = await self._evaluate_graduation_delay_risk(student_data, graduation_reqs)
        performance_risk = await self._evaluate_performance_decline_risk(student_data)
        
        if delay_risk:
            issues.append(delay_risk)
        if performance_risk:
            issues.append(performance_risk)
        
        # Determine overall risk level using RiskLevel enum
        # A graduation delay risk is always HIGH because it affects graduation
        if delay_risk:
            # Check if the delay risk has ERROR severity (multiple risk factors)
            if delay_risk.severity == IssueSeverity.ERROR:
                return RiskLevel.HIGH, issues
            else:
                # Delay risk with only one factor is still significant
                return RiskLevel.HIGH, issues
        elif performance_risk:
            return RiskLevel.MEDIUM, issues
        else:
            return RiskLevel.LOW, issues
    
    # =========================================================================
    # Rule 3: Graduation Eligibility
    # =========================================================================
    
    async def _evaluate_hours_requirement(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> RuleResult:
        """Check if student has completed required hours."""
        student = student_data.get("student", {})
        completed_hours = student.get("completed_hours", 0)
        required_hours = graduation_reqs.get("required_hours", 0)
        
        is_met = completed_hours >= required_hours
        
        return RuleResult(
            rule_code="GRAD_HOURS_REQUIREMENT",
            severity=IssueSeverity.ERROR if not is_met else IssueSeverity.INFO,
            title_ar="متطلبات الساعات المعتمدة",
            description_ar=f"الساعات المطلوبة: {required_hours} | الساعات المكتملة: {completed_hours}",
            recommendation_ar="يُحتاج إلى تسجيل المقررات المتبقية" if not is_met else None,
            data={"completed": completed_hours, "required": required_hours, "met": is_met}
        )
    
    async def _evaluate_gpa_requirement(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> RuleResult:
        """Check if student meets minimum GPA requirement."""
        student = student_data.get("student", {})
        cumulative_gpa = student.get("cumulative_gpa", 0)
        min_gpa = graduation_reqs.get("min_gpa", 0)
        
        is_met = cumulative_gpa >= min_gpa
        
        return RuleResult(
            rule_code="GRAD_GPA_REQUIREMENT",
            severity=IssueSeverity.ERROR if not is_met else IssueSeverity.INFO,
            title_ar="متطلبات المعدل التراكمي",
            description_ar=f"الحد الأدنى المطلوب: {min_gpa} | المعدل الحالي: {cumulative_gpa}",
            recommendation_ar="يُنصح بتحسين المعدل من خلال تحقيق درجات أعلى في المقررات المتبقية" if not is_met else None,
            data={"current_gpa": cumulative_gpa, "required": min_gpa, "met": is_met}
        )
    
    async def _evaluate_field_training_requirement(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> RuleResult:
        """Check if student has completed field training."""
        requires_training = graduation_reqs.get("requires_field_training", True)
        
        if not requires_training:
            return RuleResult(
                rule_code="GRAD_FIELD_TRAINING",
                severity=IssueSeverity.INFO,
                title_ar="التدريب الميداني",
                description_ar="غير مطلوب لهذه اللائحة",
                data={"required": False, "met": True}
            )
        
        # Find field training courses in student's passed courses
        passed_courses = student_data.get("passed_courses", [])
        required_courses = student_data.get("required_courses", [])
        
        # Get field training course IDs from curriculum
        field_training_course_ids = [
            c.get("id") for c in required_courses 
            if c.get("is_field_training", False)
        ]
        
        completed_training = any(
            c.get("curriculum_course_id") in field_training_course_ids 
            for c in passed_courses
        )
        
        return RuleResult(
            rule_code="GRAD_FIELD_TRAINING",
            severity=IssueSeverity.ERROR if not completed_training else IssueSeverity.INFO,
            title_ar="التدريب الميداني",
            description_ar="تم اجتياز التدريب الميداني" if completed_training else "لم يتم اجتياز التدريب الميداني بعد",
            recommendation_ar="يجب تسجيل التدريب الميداني واجتيازه بنجاح" if not completed_training else None,
            data={"required": True, "met": completed_training}
        )
    
    async def _evaluate_community_course_requirement(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> RuleResult:
        """Check if student has completed the community issues course."""
        requires_course = graduation_reqs.get("requires_community_course", True)
        course_name = graduation_reqs.get("community_course_name_ar", "القضايا المجتمعية")
        
        if not requires_course:
            return RuleResult(
                rule_code="GRAD_COMMUNITY_COURSE",
                severity=IssueSeverity.INFO,
                title_ar="مقرر القضايا المجتمعية",
                description_ar="غير مطلوب لهذه اللائحة",
                data={"required": False, "met": True}
            )
        
        # Check if student passed the community course
        passed_courses = student_data.get("passed_courses", [])
        completed = any(
            course_name in c.get("course_name", "") 
            for c in passed_courses
        )
        
        return RuleResult(
            rule_code="GRAD_COMMUNITY_COURSE",
            severity=IssueSeverity.ERROR if not completed else IssueSeverity.INFO,
            title_ar=f"مقرر {course_name}",
            description_ar="تم اجتياز المقرر" if completed else "لم يتم اجتياز مقرر القضايا المجتمعية بعد",
            recommendation_ar="يجب تسجيل مقرر القضايا المجتمعية واجتيازه بنجاح" if not completed else None,
            data={"required": True, "course_name": course_name, "met": completed}
        )
    
    async def _evaluate_mandatory_courses_requirement(
        self,
        student_data: Dict
    ) -> RuleResult:
        """Check if all mandatory courses are completed."""
        required_courses = student_data.get("required_courses", [])
        passed_course_ids = [c.get("curriculum_course_id") for c in student_data.get("passed_courses", [])]
        
        # Find mandatory courses not passed
        mandatory_categories = ["university_required", "college_required", "major_required"]
        missing_courses = []
        
        for course in required_courses:
            category = course.get("category", "")
            if category in mandatory_categories:
                if course.get("id") not in passed_course_ids:
                    missing_courses.append(course.get("name_ar", course.get("course_code", "")))
        
        is_complete = len(missing_courses) == 0
        
        return RuleResult(
            rule_code="GRAD_MANDATORY_COURSES",
            severity=IssueSeverity.ERROR if not is_complete else IssueSeverity.INFO,
            title_ar="المقررات الإجبارية",
            description_ar=(
                "جميع المقررات الإجبارية مكتملة" if is_complete
                else f"المقررات الإجبارية غير المكتملة: {', '.join(missing_courses[:5])}"
            ),
            recommendation_ar="يجب تسجيل المقررات الإجبارية المتبقية" if not is_complete else None,
            data={"missing_count": len(missing_courses), "missing_courses": missing_courses[:10]}
        )
    
    async def _determine_graduation_eligibility(
        self,
        student_data: Dict,
        graduation_reqs: Dict
    ) -> Tuple[bool, List[RuleResult]]:
        """
        Determine if student is eligible for graduation.
        
        All requirements must be met:
        - Hours requirement
        - GPA requirement
        - Field training (if required)
        - Community course (if required)
        - Mandatory courses
        """
        issues = []
        
        # Evaluate each requirement
        hour_result = await self._evaluate_hours_requirement(student_data, graduation_reqs)
        issues.append(hour_result)
        
        gpa_result = await self._evaluate_gpa_requirement(student_data, graduation_reqs)
        issues.append(gpa_result)
        
        training_result = await self._evaluate_field_training_requirement(student_data, graduation_reqs)
        issues.append(training_result)
        
        community_result = await self._evaluate_community_course_requirement(student_data, graduation_reqs)
        issues.append(community_result)
        
        mandatory_result = await self._evaluate_mandatory_courses_requirement(student_data)
        issues.append(mandatory_result)
        
        # Check if all critical requirements are met
        is_eligible = all([
            hour_result.data.get("met", False),
            gpa_result.data.get("met", False),
            training_result.data.get("met", training_result.data.get("required", True) is False),
            community_result.data.get("met", community_result.data.get("required", True) is False),
            mandatory_result.data.get("met", False),
        ])
        
        return is_eligible, issues
    
    # =========================================================================
    # Rule 4: Prerequisite Violations
    # =========================================================================
    
    async def _evaluate_prerequisite_violations(
        self,
        student_data: Dict
    ) -> List[RuleResult]:
        """
        Detect prerequisite violations.
        
        A violation occurs when a student takes a course without passing its prerequisite.
        """
        violations = []
        
        prerequisites = student_data.get("prerequisites", {})
        passed_course_ids = [c.get("curriculum_course_id") for c in student_data.get("passed_courses", [])]
        
        # Get course name mapping
        required_courses = student_data.get("required_courses", [])
        course_names = {c.get("id"): c.get("name_ar", c.get("course_code", "")) for c in required_courses}
        
        # For each course taken, check if prerequisites were met
        for course in student_data.get("courses", []):
            curriculum_course_id = course.get("curriculum_course_id")
            if not curriculum_course_id:
                continue
            
            course_prereqs = prerequisites.get(curriculum_course_id, [])
            if not course_prereqs:
                continue
            
            # Check each prerequisite
            unmet_prereqs = []
            for prereq in course_prereqs:
                required_id = prereq.get("required_course_id")
                if required_id and required_id not in passed_course_ids:
                    prereq_name = course_names.get(required_id, "مقرر")
                    unmet_prereqs.append(prereq_name)
            
            if unmet_prereqs:
                course_name = course.get("course_name", "")
                violations.append(RuleResult(
                    rule_code="PREREQ_VIOLATION",
                    severity=IssueSeverity.ERROR,
                    title_ar=f"مشكلة في المتطلبات السابقة - {course_name}",
                    description_ar=f"تم تسجيل مقرر {course_name} دون اجتياز المتطلبات السابقة: {', '.join(unmet_prereqs)}",
                    recommendation_ar=f"يجب عدم تسجيل {course_name} قبل اجتياز {', '.join(unmet_prereqs)}",
                    data={"course_id": curriculum_course_id, "unmet_prereqs": unmet_prereqs}
                ))
        
        return violations
    
    # =========================================================================
    # Main Analysis Method
    # =========================================================================
    
    async def analyze_student(self, student_id: UUID) -> AnalysisResult:
        """
        Run complete expert system analysis for a student.
        
        This is the main entry point for the inference engine.
        
        Args:
            student_id: UUID of the student to analyze
            
        Returns:
            AnalysisResult with status, risk, eligibility, and all issues
        """
        logger.info(f"Starting expert system analysis for student {student_id}")
        
        # Load all required data
        student_data = await self._get_student_data(student_id)
        
        curriculum_id = student_data["student"].get("curriculum_id")
        if not curriculum_id:
            logger.error(f"No curriculum found for student {student_id}")
            raise ValueError(f"Student {student_id} has no curriculum assigned")
        
        # Load rules from database (these are the dynamic thresholds)
        academic_rules = await self._get_academic_rules(curriculum_id)
        graduation_reqs = await self._get_graduation_requirements(curriculum_id)
        
        # Evaluate all rule categories
        all_issues = []
        
        # 1. Academic Status
        status, status_issues = await self._determine_academic_status(student_data, academic_rules)
        all_issues.extend(status_issues)
        
        # 2. Risk Level
        risk, risk_issues = await self._determine_risk_level(student_data, graduation_reqs)
        all_issues.extend(risk_issues)
        
        # 3. Graduation Eligibility
        eligible, grad_issues = await self._determine_graduation_eligibility(student_data, graduation_reqs)
        all_issues.extend(grad_issues)
        
        # 4. Prerequisite Violations
        prereq_issues = await self._evaluate_prerequisite_violations(student_data)
        all_issues.extend(prereq_issues)
        
        logger.info(f"Analysis complete for student {student_id}: status={status.value}, risk={risk.value}, eligible={eligible}, issues={len(all_issues)}")
        
        return AnalysisResult(
            student_id=student_id,
            academic_status=status,
            risk_level=risk,
            graduation_eligible=eligible,
            issues=all_issues,
        )
    
    async def save_analysis(self, analysis: AnalysisResult) -> Tuple[str, List[str]]:
        """
        Save analysis results to database.
        
        Creates:
        1. academic_analyses row
        2. analysis_issues rows for each issue
        
        Args:
            analysis: AnalysisResult from analyze_student()
            
        Returns:
            Tuple of (analysis_id, issue_ids)
        """
        issue_ids = []
        
        # Insert academic_analysis
        analysis_result = self._supabase.table("academic_analyses").insert({
            "student_id": str(analysis.student_id),
            "academic_status": analysis.academic_status.value,
            "risk_level": analysis.risk_level.value,
            "graduation_eligible": analysis.graduation_eligible,
            "analyzed_at": analysis.analyzed_at.isoformat(),
        }).execute()
        
        if not analysis_result.data:
            logger.error(f"Failed to save academic_analysis for student {analysis.student_id}")
            raise Exception("Failed to save analysis")
        
        analysis_id = analysis_result.data[0]["id"]
        
        # Insert analysis_issues
        for issue in analysis.issues:
            issue_result = self._supabase.table("analysis_issues").insert({
                "analysis_id": analysis_id,
                "rule_code": issue.rule_code,
                "severity": issue.severity.value,
                "title_ar": issue.title_ar,
                "description_ar": issue.description_ar,
                "recommendation_ar": issue.recommendation_ar,
                "resolved": False,
            }).execute()
            
            if issue_result.data:
                issue_ids.append(issue_result.data[0]["id"])
        
        logger.info(f"Saved analysis {analysis_id} with {len(issue_ids)} issues")
        return analysis_id, issue_ids
    
    def clear_cache(self) -> None:
        """Clear all cached rules and requirements."""
        self._rules_cache.clear()
        self._grad_req_cache.clear()
        logger.info("Expert system cache cleared")