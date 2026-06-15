# Acadexa — Database Workflows

This document walks through the four main data flows in the system, table-by-table, in the order rows are created/updated. A rendered diagram of the import flow is at [`images/import_pipeline.png`](images/import_pipeline.png).

![Import Pipeline](images/import_pipeline.png)

---

## A. Excel Import Flow

```
Excel Workbook
   ↓
import_jobs            (status = pending, department_id chosen by uploader)
   ↓
imported_files          (file stored in 'imports' Storage bucket)
   ↓
raw_students / raw_courses   (parser output, untouched, status = processing)
   ↓
validation / transform
   ↓
students / student_semesters / student_courses   (upserted)
   ↓
import_jobs updated      (status = completed/failed, counts, error_log)
```

### Step-by-step

1. **Upload** — A staff member (admin or advisor) selects an Excel workbook **and** the department it belongs to (confirmed: one workbook = one department, chosen at upload — not inferred from sheet contents).

2. **`import_jobs` row created** — `status = 'pending'`, `uploaded_by = auth.uid()`, `department_id = <chosen department>`, `total_students = 0`.

3. **File stored** — The workbook is uploaded to the `imports` Storage bucket; an `imported_files` row records `storage_path`, `original_name`, and `hash` (for re-upload detection), linked via `import_job_id`.

4. **Parser runs** (`service_role`, bypasses RLS) — `status` set to `'processing'`. For each sheet (= one student):
   - `parse_student_info()` + `parse_semesters_with_offset()` produce the raw structure.
   - A **`raw_students`** row is inserted: `import_job_id`, `sheet_name`, `raw_data` (full untouched JSON), `parsed = false`.
   - For each course line, a **`raw_courses`** row is inserted: `raw_student_id`, `semester_raw`, `course_raw_data`.
   - `import_jobs.total_students` is incremented per sheet found.

   This staging step exists so the **original Excel data is never lost** — if transform/business logic changes later, every historical import can be re-processed from `raw_students`/`raw_courses` without re-uploading files.

5. **Validation & transform** (`service_role`) — for each `raw_students` row not yet `parsed`:
   - `resolve_repeated_courses()` marks each course attempt with `attempt_number` and `is_latest_attempt` (chronological order by academic year + term).
   - GPA/hours are computed (`calculate_semester_stats`, `calculate_cumulative_stats`), using `grade_scale` for grade→points mapping and `affects_gpa`/`is_passing` for special symbols.
   - `curriculum_id` is resolved from `(import_jobs.department_id, enrollment_year)` — picking the curriculum with the largest `regulation_year ≤ enrollment_year` for that department.
   - Each course is matched to a `curriculum_courses` row by `course_code` (within the resolved curriculum) to set `student_courses.curriculum_course_id`; unmatched courses (e.g. no-code community-issues course) are left `NULL` and identified later by `curriculum_courses.is_community_issues_course` + name.

6. **Upserts into student-record tables**:
   - **`students`** — upsert by `student_code` (globally unique). Sets `department_id`, `curriculum_id`, `enrollment_year`, `current_level`, and all cached cumulative stats (`cumulative_gpa`, `attempted_hours`, `completed_hours`, `completion_rate`, `total_passed_courses`, `total_failed_courses`). `last_import_job_id` is set to this job.
   - **`student_semesters`** — one row per parsed semester, `UNIQUE (student_id, semester_number)`.
   - **`student_courses`** — one row per course attempt, `UNIQUE (semester_id, course_code, course_name)`, with `grade_letter`, `grade_letter_raw`, `grade_points`, `grade_score`, `passed`, `passed_raw`, `attempt_number`, `is_latest_attempt`.
   - `raw_students.student_id` is set to the matched/created student, and `raw_students.parsed = true` (or `parse_error` populated on failure).

7. **Job completion** — `import_jobs.successful_records` / `failed_records` are updated as each sheet is processed; `error_log` (jsonb) accumulates `{sheet, error}` entries for any sheet that failed (mirrors `ExcelParser.errors`). Finally `status = 'completed'` or `'failed'`, `completed_at = now()`.

---

## B. Student Processing Pipeline

This is the "shape" of one student's data once import is complete — i.e. what exists for every student row and how it's structured for querying.

```
students (1)
   ├─ department_id  ──► departments       (fixed at enrollment, never changes)
   ├─ curriculum_id   ──► curricula         (fixed at enrollment, never changes)
   │
   ├─► student_semesters (N)
   │       └─► student_courses (N)
   │               ├─ curriculum_course_id ──► curriculum_courses (optional match)
   │               └─ grade_letter           ──► grade_scale
   │
   ├─► advisor_assignments (N, 1 active)
   ├─► advisor_notes (N)
   ├─► academic_analyses (N) ──► analysis_issues (N)
   └─► reports (N)
```

Key invariants enforced by the schema:

- **Department/curriculum immutability** — `students.department_id` and `students.curriculum_id` are set once at enrollment and never updated by subsequent imports (the transform step should _not_ overwrite these on re-import; only the cached statistics and transcript tables are refreshed).
- **Latest-attempt-only GPA** — `student_courses.is_latest_attempt` is recomputed by `resolve_repeated_courses()` on every import; `students.cumulative_gpa`/`attempted_hours`/`completed_hours` are derived **only** from rows where `is_latest_attempt = true` (per `calculate_cumulative_stats`).
- **Electives are inferred, not stored separately** — there is no "student's chosen electives" table. A student's elective completion is computed on demand by joining `student_courses` (where `passed = true` and `is_latest_attempt = true`) to `elective_group_courses` to `elective_groups`, and comparing totals against `required_hours`/`min_courses`.

---

## C. Expert System Analysis Flow

```
students + student_semesters + student_courses
        +
curricula / curriculum_courses / course_prerequisites /
elective_groups+elective_group_courses / graduation_requirements /
academic_rules / grade_scale
        ↓
   Inference Engine (application layer)
        ↓
academic_analyses  (1 row: academic_status, risk_level, graduation_eligible)
        ↓
analysis_issues    (N rows: rule_code, severity, title_ar, description_ar,
                     recommendation_ar, resolved)
```

### What the engine reads (all from the knowledge base — nothing hardcoded)

- **`academic_rules`** (one row per `curriculum_id`): `probation_min_gpa`, term/summer load limits, `level_2/3/4_min_hours` — drives Academic Status Diagnosis (`IF student_gpa < probation_min_gpa THEN status = Probation`) and level-progression checks.
- **`graduation_requirements`** (one row per `curriculum_id`): `required_hours`, `min_gpa`, field-training requirement/levels, community-issues course requirement — drives Graduation Requirement Evaluation.
- **`curriculum_courses`** + **`course_prerequisites`**: drives Prerequisite Violation detection — "student registered/needs course X but hasn't passed required_course_id".
- **`elective_groups`** + **`elective_group_courses`**: drives the elective-completion check (hours **and** course-count, per group).
- **`grade_scale`**: `affects_gpa`/`is_passing` for special symbols, and `min_score`/`max_score` for optional `grade_score` vs `grade_letter` cross-validation (`GRADE_SCORE_MISMATCH`).

### What the engine writes

1. **One `academic_analyses` row** per run, summarizing:
   - `academic_status` — `good_standing`, `delayed`, `needs_support`, or `probation`, per the diagnosis rules (hours appropriate for level, required courses for level complete, no overdue mandatory courses, GPA within bounds → `good_standing`; shortfalls → `delayed`/`needs_support`; `gpa < probation_min_gpa` → `probation`).
   - `risk_level` — `low`/`medium`/`high`, from Academic Risk Prediction (graduation-delay risk from hours/level mismatch and unmet prerequisites; performance risk from GPA trend and repeated failures; graduation-requirement risk from hours/GPA/field-training/special-course checks).
   - `graduation_eligible` — `true` only if **all** of: completed hours ≥ `required_hours`, cumulative GPA ≥ `min_gpa`, field training passed (if required), community-issues course passed (if required), and no missing required courses.

2. **One `analysis_issues` row per finding**, e.g.:
   - `rule_code = 'PROBATION'`, severity `error`, explaining the GPA shortfall against `probation_min_gpa`.
   - `rule_code = 'PREREQ_VIOLATION'`, severity `error`, naming the course and its missing prerequisite (feeds report #8).
   - `rule_code = 'ELECTIVE_HOURS_INCOMPLETE'` / `'ELECTIVE_COUNT_INCOMPLETE'`, severity `warning`.
   - `rule_code = 'GRADUATION_DELAY_RISK'`, severity `warning`, with `recommendation_ar` text (e.g. "ينصح الطالب بتسجيل مقرر البرمجة... لأن مقرر البرمجة متطلب سابق لمقررات المستوى الثالث").

The `latest_academic_analyses` view (see `VIEWS_AND_FUNCTIONS.md`) always resolves to the most recent run per student, so historical runs remain available (e.g. to detect "GPA decreased from 2.7 to 1.9" by comparing two `academic_analyses` rows).

---

## D. Report Generation Flow

```
student_academic_summary (view)  ──┐
fn_student_academic_summary() ──────┼──► report payload assembled (application layer)
latest_academic_analyses (view) ────┤
analysis_issues ─────────────────────┘
        ↓
reports row inserted
   (student_id and/or department_id, report_type, generated_by, data jsonb)
        ↓
returned to UI / optionally rendered to PDF and stored in
the 'reports' Storage bucket (path referenced inside data, e.g. data->>'file_path')
```

### Per report type (from the Academic Reporting System spec)

| Report                                         | Primary data sources                                                                                                                   |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| #1 Student Academic Profile / Academic Summary | `student_academic_summary` view, or `fn_student_academic_summary()` RPC (includes per-semester GPA trend)                              |
| #2 Course Completion Report                    | `student_courses` grouped by `passed` and `attempt_number` (passed / failed / repeated, with first vs. latest attempt)                 |
| #3 Academic Plan Progress Report               | `student_courses` (passed) vs `curriculum_courses` (by category), plus `elective_groups`/`elective_group_courses` for elective buckets |
| #4 Graduation Eligibility Report               | `latest_academic_analyses.graduation_eligible` + related `analysis_issues` (reasons)                                                   |
| #5 Academic Risk Report                        | `latest_academic_analyses.risk_level` + `analysis_issues` (`GRADUATION_DELAY_RISK`, etc.)                                              |
| #6 Advisor Action Report                       | `analysis_issues.recommendation_ar` for the student, `resolved = false`                                                                |
| #7 Semester Performance Report                 | `student_semesters` ordered by `semester_number`, with GPA trend (improving/declining)                                                 |
| #8 Prerequisite Violation Report               | `analysis_issues` where `rule_code = 'PREREQ_VIOLATION'`                                                                               |
| #9 Students Overview Report                    | `department_status_overview` view                                                                                                      |
| #10 At-Risk Students Report                    | `latest_academic_analyses` joined to `students`, filtered `risk_level = 'high'`                                                        |
| #11 Department Academic Analytics              | `department_statistics` (historical snapshots) and/or `department_status_overview` (live)                                              |

### Persisting a report

1. The application assembles the report payload (Arabic-first, per the "أهم نقطة التقارير تكون باللغة العربية" requirement) from the sources above.
2. A **`reports`** row is inserted: `report_type`, `generated_by = auth.uid()`, `data = <jsonb payload>`, and either `student_id`, `department_id`, or `report_type = 'college_overview'` (enforced by the table's `CHECK` constraint).
3. If a rendered file (e.g. PDF) is produced, it is uploaded to the `reports` Storage bucket and its path can be embedded inside `data` — no schema change required.
4. The report remains visible to **all staff** (`reports_select_staff` policy) and editable/removable by its `generated_by` author or an admin.
