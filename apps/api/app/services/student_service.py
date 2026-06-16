"""
================================================================================
Student Service for Acadexa API
================================================================================

Business logic for student management.

IMPORTANT SECURITY NOTE:
This service accepts an authenticated Supabase client that carries the user's JWT.
RLS policies in the database enforce authorization - service layer does NOT
bypass security.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError

logger = logging.getLogger("acadexa.services.student")


class StudentService:
    """
    Service for student management and academic data retrieval.
    
    Security: All methods require an authenticated Supabase client
    that carries the user's JWT token. RLS policies enforce authorization.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize StudentService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
                           Created via get_authenticated_client(access_token).
        """
        self._supabase = supabase_client
    
    async def get_students(
        self,
        search: Optional[str] = None,
        department_id: Optional[UUID] = None,
        curriculum_id: Optional[UUID] = None,
        current_level: Optional[int] = None,
        academic_status: Optional[str] = None,
        risk_level: Optional[str] = None,
        enrollment_year: Optional[int] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 25,
        sort_by: str = "student_code",
        sort_dir: str = "asc",
    ) -> Tuple[List[Dict], int]:
        """
        Get paginated list of students with filters.
        
        RLS: Staff can SELECT from students table.
        """
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        allowed_sort_fields = ["student_code", "name", "cumulative_gpa", "current_level", "enrollment_year"]
        if sort_by not in allowed_sort_fields:
            sort_by = "student_code"
        
        sort_dir = "asc" if sort_dir.lower() != "desc" else "desc"
        
        query = self._supabase.table("students")\
            .select(
                "id, student_code, name, department_id, curriculum_id, "
                "enrollment_year, current_level, cumulative_gpa, cumulative_percentage, "
                "attempted_hours, completed_hours, completion_rate, is_active, "
                "departments!inner(name_ar, name_en, code), "
                "curricula!inner(name_ar, regulation_year)",
                count="exact"
            )
        
        if search:
            query = query.or_(
                f"student_code.ilike.%{search}%,"
                f"name.ilike.%{search}%"
            )
        
        if department_id:
            query = query.eq("department_id", str(department_id))
        
        if curriculum_id:
            query = query.eq("curriculum_id", str(curriculum_id))
        
        if current_level:
            query = query.eq("current_level", current_level)
        
        if enrollment_year:
            query = query.eq("enrollment_year", enrollment_year)
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.order(sort_by, desc=(sort_dir == "desc"))
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        students = result.data or []
        total = result.count or 0
        
        if students:
            student_ids = [s["id"] for s in students]
            analyses_result = self._supabase.table("latest_academic_analyses")\
                .select("student_id, academic_status, risk_level, graduation_eligible, analyzed_at")\
                .in_("student_id", student_ids)\
                .execute()
            
            analyses_map = {a["student_id"]: a for a in (analyses_result.data or [])}
            
            for student in students:
                analysis = analyses_map.get(student["id"], {})
                student["academic_status"] = analysis.get("academic_status")
                student["risk_level"] = analysis.get("risk_level")
                student["graduation_eligible"] = analysis.get("graduation_eligible")
                student["last_analyzed_at"] = analysis.get("analyzed_at")
        
        return students, total
    
    async def get_student_by_id(self, student_id: UUID) -> Dict:
        """
        Get a single student by ID with related data.
        
        RLS: Staff can SELECT from students table.
        """
        result = self._supabase.table("students")\
            .select(
                "*, "
                "departments(id, code, name_ar, name_en, short_name), "
                "curricula(id, name_ar, regulation_year, total_required_hours, min_gpa_to_graduate)"
            )\
            .eq("id", str(student_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("Student", str(student_id))
        
        student = result.data[0]
        
        advisor_result = self._supabase.table("advisor_assignments")\
            .select("advisor_id, profiles!inner(full_name, email)")\
            .eq("student_id", str(student_id))\
            .eq("is_active", True)\
            .execute()
        
        if advisor_result.data:
            student["advisor"] = {
                "id": advisor_result.data[0]["advisor_id"],
                "name": advisor_result.data[0]["profiles"]["full_name"],
                "email": advisor_result.data[0]["profiles"]["email"],
            }
        else:
            student["advisor"] = None
        
        analysis_result = self._supabase.table("latest_academic_analyses")\
            .select("academic_status, risk_level, graduation_eligible, analyzed_at")\
            .eq("student_id", str(student_id))\
            .execute()
        
        if analysis_result.data:
            student["latest_analysis"] = analysis_result.data[0]
        else:
            student["latest_analysis"] = None
        
        return student
    
    async def get_academic_summary(self, student_id: UUID) -> Dict:
        """
        Get complete academic summary for a student.
        
        RLS: Function is SECURITY INVOKER - runs with caller's permissions.
        """
        result = self._supabase.rpc(
            "fn_student_academic_summary",
            {"p_student_id": str(student_id)}
        ).execute()
        
        if not result.data:
            await self.get_student_by_id(student_id)
            return {"student": None, "semesters": []}
        
        return result.data
    
    async def get_transcript(
        self,
        student_id: UUID,
        level: Optional[int] = None,
        term: Optional[str] = None,
        show_non_counting: bool = False,
    ) -> List[Dict]:
        """
        Get student transcript with semesters and nested courses.
        
        RLS: Staff can SELECT from student_semesters and student_courses.
        """
        await self.get_student_by_id(student_id)
        
        semester_query = self._supabase.table("student_semesters")\
            .select("*")\
            .eq("student_id", str(student_id))\
            .order("semester_number")
        
        if level:
            semester_query = semester_query.eq("level", level)
        
        if term:
            semester_query = semester_query.eq("term", term)
        
        semesters_result = semester_query.execute()
        semesters = semesters_result.data or []
        
        if not semesters:
            return []
        
        semester_ids = [s["id"] for s in semesters]
        
        course_query = self._supabase.table("student_courses")\
            .select(
                "id, course_code, course_name, credit_hours, grade_letter, "
                "grade_letter_raw, grade_points, grade_score, passed, "
                "attempt_number, is_latest_attempt, semester_id, "
                "grade_scale!inner(name_ar, points, affects_gpa, is_passing)"
            )\
            .in_("semester_id", semester_ids)\
            .order("created_at")
        
        if not show_non_counting:
            course_query = course_query.eq("is_latest_attempt", True)
        
        courses_result = course_query.execute()
        courses = courses_result.data or []
        
        courses_by_semester = {}
        for course in courses:
            sem_id = course["semester_id"]
            if sem_id not in courses_by_semester:
                courses_by_semester[sem_id] = []
            
            grade_info = course.pop("grade_scale", {})
            course["grade_name_ar"] = grade_info.get("name_ar")
            course["affects_gpa"] = grade_info.get("affects_gpa", True)
            course["is_passing_grade"] = grade_info.get("is_passing", False)
            
            courses_by_semester[sem_id].append(course)
        
        for semester in semesters:
            semester["courses"] = courses_by_semester.get(semester["id"], [])
        
        return semesters
    
    async def get_academic_plan(self, student_id: UUID) -> Dict:
        """
        Compare student's completed courses against curriculum plan.
        
        RLS: Staff can SELECT from curriculum_courses, student_courses, elective_groups.
        """
        student = await self.get_student_by_id(student_id)
        curriculum_id = student.get("curriculum_id")
        
        if not curriculum_id:
            raise ValueError(f"Student {student_id} has no curriculum assigned")
        
        curriculum_courses_result = self._supabase.table("curriculum_courses")\
            .select(
                "id, course_code, name_ar, name_en, credit_hours, level, term, "
                "category, is_field_training, is_graduation_project, is_community_issues_course"
            )\
            .eq("curriculum_id", str(curriculum_id))\
            .eq("is_active", True)\
            .order("level", "term")
        
        curriculum_courses = curriculum_courses_result.data or []
        
        passed_courses_result = self._supabase.table("student_courses")\
            .select("curriculum_course_id, course_code, course_name, grade_letter, passed, attempt_number")\
            .eq("student_id", str(student_id))\
            .eq("is_latest_attempt", True)\
            .eq("passed", True)\
            .execute()
        
        passed_course_ids = set()
        passed_by_curriculum_id = {}
        for course in passed_courses_result.data or []:
            if course.get("curriculum_course_id"):
                passed_course_ids.add(course["curriculum_course_id"])
                passed_by_curriculum_id[course["curriculum_course_id"]] = course
        
        failed_courses_result = self._supabase.table("student_courses")\
            .select("curriculum_course_id, course_code, course_name, grade_letter")\
            .eq("student_id", str(student_id))\
            .eq("is_latest_attempt", True)\
            .eq("passed", False)\
            .execute()
        
        failed_course_ids = set()
        for course in failed_courses_result.data or []:
            if course.get("curriculum_course_id"):
                failed_course_ids.add(course["curriculum_course_id"])
        
        category_requirements = {
            "university_required": {"required_hours": 0, "completed_hours": 0},
            "university_elective": {"required_hours": 0, "completed_hours": 0},
            "college_required": {"required_hours": 0, "completed_hours": 0},
            "college_elective": {"required_hours": 0, "completed_hours": 0},
            "major_required": {"required_hours": 0, "completed_hours": 0},
            "major_elective": {"required_hours": 0, "completed_hours": 0},
        }
        
        plan_courses = []
        for course in curriculum_courses:
            course_id = course["id"]
            category = course["category"]
            hours = course["credit_hours"]
            
            if category in category_requirements:
                category_requirements[category]["required_hours"] += hours
            
            if course_id in passed_course_ids:
                status = "passed"
                completed_hours = hours
                grade = passed_by_curriculum_id[course_id].get("grade_letter")
            elif course_id in failed_course_ids:
                status = "failed"
                completed_hours = 0
                grade = None
            else:
                status = "not_taken"
                completed_hours = 0
                grade = None
            
            if status == "passed" and category in category_requirements:
                category_requirements[category]["completed_hours"] += completed_hours
            
            plan_courses.append({
                "id": course_id,
                "course_code": course.get("course_code"),
                "name_ar": course["name_ar"],
                "credit_hours": hours,
                "level": course["level"],
                "term": course["term"],
                "category": category,
                "status": status,
                "grade": grade,
                "is_field_training": course.get("is_field_training", False),
                "is_graduation_project": course.get("is_graduation_project", False),
                "is_community_issues_course": course.get("is_community_issues_course", False),
            })
        
        elective_groups_result = self._supabase.table("elective_groups")\
            .select("id, name, category, required_hours, min_courses")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        elective_groups = []
        for group in elective_groups_result.data or []:
            group_courses_result = self._supabase.table("elective_group_courses")\
                .select("course_id, curriculum_courses!inner(name_ar, course_code, credit_hours)")\
                .eq("group_id", group["id"])\
                .execute()
            
            group_courses = []
            completed_hours = 0
            completed_count = 0
            
            for gc in group_courses_result.data or []:
                course = gc.get("curriculum_courses", {})
                course_id = gc["course_id"]
                is_completed = course_id in passed_course_ids
                
                if is_completed:
                    completed_hours += course.get("credit_hours", 0)
                    completed_count += 1
                
                group_courses.append({
                    "course_id": course_id,
                    "name_ar": course.get("name_ar"),
                    "course_code": course.get("course_code"),
                    "credit_hours": course.get("credit_hours", 0),
                    "is_completed": is_completed,
                })
            
            elective_groups.append({
                "id": group["id"],
                "name": group["name"],
                "category": group["category"],
                "required_hours": group["required_hours"],
                "min_courses": group["min_courses"],
                "completed_hours": completed_hours,
                "completed_courses": completed_count,
                "is_complete": completed_hours >= group["required_hours"] and completed_count >= group["min_courses"],
                "courses": group_courses,
            })
        
        return {
            "student_id": student_id,
            "curriculum_id": curriculum_id,
            "category_summary": category_requirements,
            "courses": plan_courses,
            "elective_groups": elective_groups,
        }
    
    async def get_graduation_status(self, student_id: UUID) -> Dict:
        """
        Evaluate student's graduation eligibility.
        
        RLS: Staff can SELECT from graduation_requirements, curriculum_courses, student_courses.
        """
        student = await self.get_student_by_id(student_id)
        curriculum_id = student.get("curriculum_id")
        
        if not curriculum_id:
            raise ValueError(f"Student {student_id} has no curriculum assigned")
        
        grad_req_result = self._supabase.table("graduation_requirements")\
            .select("*")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        grad_reqs = grad_req_result.data[0] if grad_req_result.data else {}
        
        required_hours = grad_reqs.get("required_hours", 0)
        min_gpa = grad_reqs.get("min_gpa", 0)
        requires_training = grad_reqs.get("requires_field_training", True)
        requires_community = grad_reqs.get("requires_community_course", True)
        community_course_name = grad_reqs.get("community_course_name_ar", "القضايا المجتمعية")
        
        completed_hours = student.get("completed_hours", 0)
        cumulative_gpa = student.get("cumulative_gpa", 0)
        
        field_training_completed = False
        if requires_training:
            training_courses_result = self._supabase.table("curriculum_courses")\
                .select("id")\
                .eq("curriculum_id", str(curriculum_id))\
                .eq("is_field_training", True)\
                .execute()
            
            training_course_ids = [c["id"] for c in training_courses_result.data or []]
            
            if training_course_ids:
                training_passed = self._supabase.table("student_courses")\
                    .select("id", count="exact")\
                    .eq("student_id", str(student_id))\
                    .in_("curriculum_course_id", training_course_ids)\
                    .eq("passed", True)\
                    .eq("is_latest_attempt", True)\
                    .execute()
                
                field_training_completed = (training_passed.count or 0) > 0
        
        community_course_completed = False
        if requires_community:
            community_result = self._supabase.table("curriculum_courses")\
                .select("id")\
                .eq("curriculum_id", str(curriculum_id))\
                .eq("is_community_issues_course", True)\
                .execute()
            
            community_course_ids = [c["id"] for c in community_result.data or []]
            
            if community_course_ids:
                community_passed = self._supabase.table("student_courses")\
                    .select("id", count="exact")\
                    .eq("student_id", str(student_id))\
                    .in_("curriculum_course_id", community_course_ids)\
                    .eq("passed", True)\
                    .eq("is_latest_attempt", True)\
                    .execute()
                
                community_course_completed = (community_passed.count or 0) > 0
            else:
                name_passed = self._supabase.table("student_courses")\
                    .select("id", count="exact")\
                    .eq("student_id", str(student_id))\
                    .ilike("course_name", f"%{community_course_name}%")\
                    .eq("passed", True)\
                    .eq("is_latest_attempt", True)\
                    .execute()
                
                community_course_completed = (name_passed.count or 0) > 0
        
        hours_met = completed_hours >= required_hours
        gpa_met = cumulative_gpa >= min_gpa
        training_met = not requires_training or field_training_completed
        community_met = not requires_community or community_course_completed
        
        is_eligible = hours_met and gpa_met and training_met and community_met
        
        return {
            "student_id": student_id,
            "is_eligible": is_eligible,
            "requirements": {
                "hours": {
                    "required": required_hours,
                    "completed": completed_hours,
                    "met": hours_met,
                },
                "gpa": {
                    "required": min_gpa,
                    "current": cumulative_gpa,
                    "met": gpa_met,
                },
                "field_training": {
                    "required": requires_training,
                    "completed": field_training_completed,
                    "met": training_met,
                },
                "community_course": {
                    "required": requires_community,
                    "course_name": community_course_name,
                    "completed": community_course_completed,
                    "met": community_met,
                },
            },
        }
    
    async def get_prerequisite_status(self, student_id: UUID) -> Dict:
        """
        Get prerequisite compliance for student.
        
        RLS: Staff can SELECT from curriculum_courses, course_prerequisites, student_courses.
        """
        student = await self.get_student_by_id(student_id)
        curriculum_id = student.get("curriculum_id")
        
        if not curriculum_id:
            raise ValueError(f"Student {student_id} has no curriculum assigned")
        
        courses_result = self._supabase.table("curriculum_courses")\
            .select("id, course_code, name_ar, level")\
            .eq("curriculum_id", str(curriculum_id))\
            .execute()
        
        courses = {c["id"]: c for c in courses_result.data or []}
        
        prereq_result = self._supabase.table("course_prerequisites")\
            .select("course_id, required_course_id, minimum_grade")\
            .execute()
        
        prerequisites = {}
        for prereq in prereq_result.data or []:
            course_id = prereq["course_id"]
            if course_id not in prerequisites:
                prerequisites[course_id] = []
            prerequisites[course_id].append(prereq)
        
        passed_result = self._supabase.table("student_courses")\
            .select("curriculum_course_id, course_code, course_name")\
            .eq("student_id", str(student_id))\
            .eq("passed", True)\
            .eq("is_latest_attempt", True)\
            .execute()
        
        passed_course_ids = set()
        for course in passed_result.data or []:
            if course.get("curriculum_course_id"):
                passed_course_ids.add(course["curriculum_course_id"])
        
        taken_result = self._supabase.table("student_courses")\
            .select("curriculum_course_id, course_code, course_name, semester_id, student_semesters!inner(academic_year, semester_number)")\
            .eq("student_id", str(student_id))\
            .execute()
        
        taken_courses = []
        for course in taken_result.data or []:
            semester = course.get("student_semesters", {})
            taken_courses.append({
                "curriculum_course_id": course.get("curriculum_course_id"),
                "course_code": course.get("course_code"),
                "course_name": course.get("course_name"),
                "academic_year": semester.get("academic_year"),
                "semester_number": semester.get("semester_number"),
            })
        
        violations = []
        for taken in taken_courses:
            course_id = taken.get("curriculum_course_id")
            if not course_id or course_id not in prerequisites:
                continue
            
            unmet = []
            for prereq in prerequisites[course_id]:
                required_id = prereq["required_course_id"]
                if required_id not in passed_course_ids:
                    req_course = courses.get(required_id, {})
                    unmet.append(req_course.get("name_ar", req_course.get("course_code", "مقرر")))
            
            if unmet:
                violations.append({
                    "course_id": course_id,
                    "course_code": taken["course_code"],
                    "course_name": taken["course_name"],
                    "taken_in": f"{taken['academic_year']} - فصل {taken['semester_number']}",
                    "missing_prerequisites": unmet,
                })
        
        upcoming_blocked = []
        for course_id, prereq_list in prerequisites.items():
            if any(t.get("curriculum_course_id") == course_id for t in taken_courses):
                continue
            
            unmet = []
            for prereq in prereq_list:
                required_id = prereq["required_course_id"]
                if required_id not in passed_course_ids:
                    req_course = courses.get(required_id, {})
                    unmet.append(req_course.get("name_ar", req_course.get("course_code", "مقرر")))
            
            if unmet:
                course = courses.get(course_id, {})
                upcoming_blocked.append({
                    "course_id": course_id,
                    "course_code": course.get("course_code"),
                    "course_name": course.get("name_ar"),
                    "level": course.get("level"),
                    "missing_prerequisites": unmet,
                })
        
        return {
            "student_id": student_id,
            "violations": violations,
            "upcoming_blocked_courses": upcoming_blocked,
        }
    
    async def get_completion_percentage(self, student_id: UUID) -> float:
        """
        Get graduation completion percentage.
        
        RLS: Function is SECURITY INVOKER - runs with caller's permissions.
        """
        result = self._supabase.rpc(
            "fn_student_completion_percentage",
            {"p_student_id": str(student_id)}
        ).execute()
        
        return float(result.data) if result.data else 0.0
    
    async def update_student(
        self,
        student_id: UUID,
        current_level: Optional[int] = None,
        is_active: Optional[bool] = None,
        cumulative_gpa: Optional[float] = None,
    ) -> Dict:
        """
        Update student record manually.
        
        RLS: Admin can UPDATE students table.
        This method should only be called after admin role verification.
        """
        await self.get_student_by_id(student_id)
        
        update_data = {}
        if current_level is not None:
            if current_level < 1 or current_level > 4:
                raise ValueError("Current level must be between 1 and 4")
            update_data["current_level"] = current_level
        
        if is_active is not None:
            update_data["is_active"] = is_active
        
        if cumulative_gpa is not None:
            if cumulative_gpa < 0 or cumulative_gpa > 4:
                raise ValueError("Cumulative GPA must be between 0 and 4")
            update_data["cumulative_gpa"] = cumulative_gpa
        
        if not update_data:
            return await self.get_student_by_id(student_id)
        
        result = self._supabase.table("students")\
            .update(update_data)\
            .eq("id", str(student_id))\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update student")
        
        logger.info(f"Updated student {student_id}: {update_data}")
        return result.data[0]
    
    async def get_student_semesters(self, student_id: UUID) -> List[Dict]:
        """
        Get student semesters (lightweight, no nested courses).
        
        RLS: Staff can SELECT from student_semesters.
        """
        await self.get_student_by_id(student_id)
        
        result = self._supabase.table("student_semesters")\
            .select("id, semester_number, academic_year, term, level, gpa, attempted_hours, completed_hours")\
            .eq("student_id", str(student_id))\
            .order("semester_number")\
            .execute()
        
        return result.data or []