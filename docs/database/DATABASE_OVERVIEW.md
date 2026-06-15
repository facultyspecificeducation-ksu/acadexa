# Acadexa — Database Overview

## 1. Purpose

Acadexa is an academic advising **expert system** for the Faculty of Specific Education, Kafr El‑Sheikh University. The database is the single source of truth for:

- the college's academic structure (10 departments/programs, each with one or more regulations/curricula);
- every student's transcript (semesters, courses, grades, GPA, retakes);
- the **knowledge base** the expert system reasons over (academic rules, graduation requirements, grading scale, prerequisites — all data‑driven, never hardcoded);
- the **Excel import pipeline** that brings student transcripts into the system;
- the **expert system's output** (academic status, risk level, explainable issues/recommendations);
- and the **reports** generated for academic advisors and administrators (Arabic‑first).

The system is **staff‑only**: only `admin` and `academic_advisor` accounts ever authenticate. Students never log in — their data exists in the database purely as records managed by staff.

---

## 2. PostgreSQL + Supabase Architecture

The database runs on **Supabase** (managed PostgreSQL) and uses Supabase's platform features directly rather than building parallel systems:

| Supabase feature                 | How Acadexa uses it                                                                                                                                                                                                                                                                                    |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Postgres + `pgcrypto`**        | `gen_random_uuid()` is the default for every primary key — a single, consistent UUID strategy across all 25 tables.                                                                                                                                                                                    |
| **Supabase Auth (`auth.users`)** | Identity for staff accounts. A trigger (`handle_new_user`) automatically creates a matching row in `public.profiles` on signup.                                                                                                                                                                        |
| **Row Level Security (RLS)**     | Every table has RLS enabled. Access is computed from `profiles` → `user_roles` → `roles` via two helper functions, `is_admin()` and `is_advisor()` (see `RLS_SECURITY.md`).                                                                                                                            |
| **Storage**                      | Two private buckets — `imports` (uploaded Excel workbooks) and `reports` (optional rendered report files) — referenced from `imported_files.storage_path` and (optionally) `reports.data`.                                                                                                             |
| **`service_role` key**           | Backend jobs (the Excel parser and the expert‑system engine) run with the service role, which bypasses RLS — so import/analysis jobs are never blocked by the staff‑facing policies.                                                                                                                   |
| **Views & RPC functions**        | A small set of views (`latest_academic_analyses`, `student_academic_summary`, `department_status_overview`) and two RPC functions (`fn_student_completion_percentage`, `fn_student_academic_summary`) give the application pre‑joined, ready‑to‑render data without duplicating business logic in SQL. |

The schema is delivered as **10 ordered SQL migrations** (`001_extensions.sql` … `010_functions.sql`) — see `MIGRATION_GUIDE.md` for what each one does and why the order matters.

---

## 3. Main Modules

The 25 tables (plus 3 views, 2 functions) are organized into seven functional modules. Every module maps to a section of `TABLE_DOCUMENTATION.md`.

### 3.1 Authentication

`profiles`, `roles`, `user_roles`

Extends `auth.users` with a staff profile, and assigns each staff member one or both roles (`admin`, `academic_advisor`) via a join table. No custom auth system — Supabase Auth remains the source of truth for credentials; this module only adds _who they are_ and _what they can do_.

### 3.2 Academic Structure

`departments`

The 10 departments/programs of the college. Every other module hangs off this table — curricula belong to a department, students belong to a department, import jobs are scoped to a department, and so on.

### 3.3 Curriculum Management

`curricula`, `curriculum_courses`, `course_prerequisites`, `elective_groups`, `elective_group_courses`, `graduation_requirements`, `academic_rules`, `grade_scale`

This is the **knowledge base**. A `curriculum` is one regulation (لائحة) applied to one department for one enrollment‑year range. Everything the expert system needs to evaluate a student — required courses, prerequisites, elective requirements, graduation thresholds, GPA/probation rules, and the grading scale — is data here, not code. Updating a GPA threshold or adding a new regulation year is a data change, never a code/schema change.

### 3.4 Student Records

`students`, `student_semesters`, `student_courses`

The transcript data itself: one row per student, one row per semester, one row per course attempt. `student_courses.is_latest_attempt` implements the confirmed policy that **only the latest attempt of a repeated course counts toward cumulative GPA**.

### 3.5 Excel Import Pipeline

`import_jobs`, `imported_files`, `raw_students`, `raw_courses`

Every workbook upload is one `import_jobs` row, scoped to **one department** (chosen by the uploader — not inferred from the sheet). The parser first writes the **untouched** parsed data into `raw_students`/`raw_courses` (staging), then a transform step populates `students`/`student_semesters`/`student_courses`. If transform logic changes later, historical imports can be re‑processed from the raw staging tables without re‑uploading files. See `DATABASE_WORKFLOW.md`.

### 3.6 Expert System

`academic_analyses`, `analysis_issues`

The output of the inference engine: one `academic_analyses` row per analysis run (status, risk level, graduation eligibility), with each individual finding (low GPA, unmet prerequisite, elective hours incomplete, etc.) as its own `analysis_issues` row — so reports like "all students with a prerequisite violation" or "all high‑risk students" are simple filtered queries.

### 3.7 Reports (+ Advisory)

`reports`, `department_statistics`, `advisor_assignments`, `advisor_notes`

`reports` stores generated report payloads (jsonb, Arabic‑first) for students or departments. `department_statistics` is a periodic snapshot for trend analytics. `advisor_assignments` tracks which advisor is primarily responsible for which student (a dashboard filter, not an access boundary — any staff member can see any student). `advisor_notes` are shared across all staff.

---

## 4. High-Level Architecture

```text
                 ┌────────────────────────┐
                 │   Supabase Auth          │
                 │   (auth.users)           │
                 └────────────┬─────────────┘
                              │ trigger: handle_new_user()
                              ▼
   ┌──────────────────────────────────────────────────────────┐
   │  AUTHENTICATION: profiles ── user_roles ── roles           │
   │  (admin, academic_advisor)                                 │
   └───────────────────────────┬────────────────────────────────┘
                                │ RLS: is_admin() / is_advisor() / is_staff()
                                ▼
┌─────────────────────┐   ┌────────────────────────────────────────────┐
│ ACADEMIC STRUCTURE   │──▶│ CURRICULUM MANAGEMENT (knowledge base)       │
│ departments          │   │ curricula, curriculum_courses,               │
└──────────┬───────────┘   │ course_prerequisites, elective_groups(+_     │
           │                │ courses), graduation_requirements,           │
           │                │ academic_rules, grade_scale                  │
           │                └───────────────┬───────────────────────────┘
           │                                │
           ▼                                ▼
┌──────────────────────────────────────────────────────────┐
│ EXCEL IMPORT PIPELINE                                      │
│ import_jobs ─▶ imported_files                              │
│      └──▶ raw_students ─▶ raw_courses                      │
│              (staging — untouched parsed data)             │
└───────────────────────────┬────────────────────────────────┘
                             │ validation / transform
                             ▼
┌──────────────────────────────────────────────────────────┐
│ STUDENT RECORDS                                            │
│ students ─▶ student_semesters ─▶ student_courses           │
└───────────────────────────┬────────────────────────────────┘
                             │ inference engine reads
                             │ (academic_rules, graduation_requirements,
                             │  curriculum_courses, grade_scale, ...)
                             ▼
┌──────────────────────────────────────────────────────────┐
│ EXPERT SYSTEM                                              │
│ academic_analyses ─▶ analysis_issues                       │
└───────────────────────────┬────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ REPORTS & ADVISORY                                         │
│ reports, department_statistics,                            │
│ advisor_assignments, advisor_notes                          │
└──────────────────────────────────────────────────────────┘
```

See `images/database_architecture.png` for the rendered diagram, and `images/import_pipeline.png` for the detailed Excel import flow.

---

## 5. Document Map

| Document                 | Contents                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| `ERD.md`                 | Full Mermaid ER diagram (all 25 tables, keys, cardinalities) + rendered `images/erd.png` |
| `TABLE_DOCUMENTATION.md` | Every table: purpose, columns, types, constraints, relationships                         |
| `RELATIONSHIPS.md`       | Every FK relationship explained with cardinality and _why_ it exists                     |
| `MIGRATION_GUIDE.md`     | What each of the 10 migration files does, in order                                       |
| `RLS_SECURITY.md`        | Roles, helper functions, and the read/write policy for every table                       |
| `DATABASE_WORKFLOW.md`   | Excel import flow, student analysis flow, report generation flow                         |
| `SEED_DATA.md`           | `roles` and `grade_scale` seed data + initial setup steps                                |
| `VIEWS_AND_FUNCTIONS.md` | The 3 views and 2 RPC functions: purpose, parameters, return shape                       |
