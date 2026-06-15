# Acadexa — Migration Guide

The schema is delivered as **10 ordered SQL migrations**. Each migration depends only on objects created by earlier migrations — they must be applied in order **001 → 010** on a fresh Supabase project.

```
001_extensions.sql           → 002_enums.sql → 003_schema.sql → 004_constraints_indexes.sql
→ 005_triggers.sql → 006_rls.sql → 007_storage_notes.sql → 008_seed.sql
→ 009_views.sql → 010_functions.sql
```

---

## 001_extensions.sql

**Purpose**: Enable the PostgreSQL extension required for UUID generation, used as the default for every `uuid` primary key in the schema.

**Creates**

- Extension `pgcrypto` (provides `gen_random_uuid()`).

**Dependencies**: None — this is the first migration. Safe to re-run (`create extension if not exists`).

---

## 002_enums.sql

**Purpose**: Define every custom enum type referenced by table columns in `003_schema.sql`. Postgres requires enum types to exist before they can be used as a column type, so this must run before `003`.

**Creates** (6 enum types)

| Enum                   | Values                                                                                                                   | Used by                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| `term_enum`            | `fall`, `spring`, `summer`                                                                                               | `curriculum_courses.term`, `student_semesters.term`       |
| `course_category_enum` | `university_required`, `university_elective`, `college_required`, `college_elective`, `major_required`, `major_elective` | `curriculum_courses.category`, `elective_groups.category` |
| `academic_status_enum` | `good_standing`, `delayed`, `needs_support`, `probation`                                                                 | `academic_analyses.academic_status`                       |
| `risk_level_enum`      | `low`, `medium`, `high`                                                                                                  | `academic_analyses.risk_level`                            |
| `import_status_enum`   | `pending`, `processing`, `completed`, `failed`                                                                           | `import_jobs.status`                                      |
| `issue_severity_enum`  | `info`, `warning`, `error`                                                                                               | `analysis_issues.severity`                                |

**Dependencies**: `001_extensions.sql` (ordering only — enums don't actually use `pgcrypto`, but migrations run sequentially).

---

## 003_schema.sql

**Purpose**: Create all 25 core tables, in strict dependency order, as pure DDL (primary keys, foreign keys, `UNIQUE`/inline `CHECK` constraints that are part of the table definition itself — e.g. `course_prerequisites`'s self-reference check and `reports`'s scoping check). No indexes beyond those implied by PK/UNIQUE, no range `CHECK` constraints beyond inline ones, no seed data.

**Creates** (25 tables, in this order)

1. `departments`
2. `roles`
3. `profiles` (FK → `auth.users`)
4. `user_roles` (FK → `profiles`, `roles`)
5. `grade_scale`
6. `curricula` (FK → `departments`)
7. `curriculum_courses` (FK → `curricula`)
8. `course_prerequisites` (FK → `curriculum_courses` ×2, `grade_scale`)
9. `elective_groups` (FK → `curricula`)
10. `elective_group_courses` (FK → `elective_groups`, `curriculum_courses`)
11. `graduation_requirements` (FK → `curricula`)
12. `academic_rules` (FK → `curricula`)
13. `import_jobs` (FK → `profiles`, `departments`)
14. `imported_files` (FK → `import_jobs`)
15. `students` (FK → `departments`, `curricula`, `import_jobs`)
16. `raw_students` (FK → `import_jobs`, `students`)
17. `raw_courses` (FK → `raw_students`)
18. `student_semesters` (FK → `students`)
19. `student_courses` (FK → `students`, `student_semesters`, `curriculum_courses`, `grade_scale`)
20. `advisor_assignments` (FK → `profiles`, `students`)
21. `advisor_notes` (FK → `students`, `profiles`)
22. `academic_analyses` (FK → `students`)
23. `analysis_issues` (FK → `academic_analyses`)
24. `reports` (FK → `students`, `departments`, `profiles`)
25. `department_statistics` (FK → `departments`)

**Dependencies**: `001_extensions.sql` (for `gen_random_uuid()` defaults) and `002_enums.sql` (for the 6 enum column types). Each table within this file only references tables defined earlier in the same file — see `ERD.md` for the full relationship map.

---

## 004_constraints_indexes.sql

**Purpose**: Add data-integrity `CHECK` constraints (numeric ranges, sanity bounds) and performance indexes for real query patterns — without "indexing everything".

**Creates**

_Range/sanity `CHECK` constraints_ on:

- `curricula` (`total_required_hours > 0`, `min_gpa_to_graduate` 0–4)
- `curriculum_courses` (`credit_hours > 0`, `level` 1–4)
- `elective_groups` (`required_hours > 0`, `min_courses ≥ 1`)
- `graduation_requirements` (`required_hours > 0`, `min_gpa` 0–4, `max_study_years > 0` or null)
- `academic_rules` (`probation_min_gpa` 0–4, term/summer hour bounds, level-progression hour ordering)
- `grade_scale` (`points` 0–4, score range sanity)
- `students` (GPA, percentage, hours, completion rate, level, enrollment year bounds)
- `student_semesters` (GPA, hours, course-count bounds)
- `student_courses` (`credit_hours > 0`, grade points 0–4, `grade_score` 0–100 or null, `attempt_number ≥ 1`)
- `import_jobs` (non-negative counts; `successful + failed ≤ total`)
- `department_statistics` (GPA, rate, and count bounds)

_Indexes_ — grouped by query pattern:

- **Students**: `department_id`, `curriculum_id`, `(enrollment_year, department_id)`, `(is_active, current_level)`. (`student_code` already has an implicit unique index from its `UNIQUE` constraint.)
- **Student courses**: `student_id`, `semester_id`, `curriculum_course_id`, `(student_id, passed)`, `course_code`.
- **Student semesters**: `student_id`.
- **Curriculum lookups**: `curriculum_courses(curriculum_id)`, `(curriculum_id, category)`, `course_code`; `course_prerequisites(course_id)`, `(required_course_id)`.
- **Elective groups**: `curriculum_id`.
- **Analyses & issues**: `(student_id, analyzed_at desc)`, `risk_level`, `academic_status`, `analysis_id`, `rule_code`, `(severity, resolved)`.
- **Advisor workflow**: partial unique index on `advisor_assignments(student_id) WHERE is_active = true`; `advisor_id`; `advisor_notes(student_id)`.
- **Import pipeline**: `import_jobs(department_id)`, `(uploaded_by)`; `imported_files(import_job_id)`; `raw_students(import_job_id)`, `(parsed)`; `raw_courses(raw_student_id)`.
- **Reports & stats**: `reports(student_id)`, `(department_id, report_type)`; `department_statistics(department_id, calculated_at desc)`.
- **Roles**: `user_roles(user_id)` — used by the RLS helper functions in `006`.

**Dependencies**: `003_schema.sql` (every table/column referenced must already exist).

---

## 005_triggers.sql

**Purpose**: Automatic `updated_at` maintenance, and the Supabase Auth → `profiles` integration.

**Creates**

_Part A — generic `updated_at` trigger_

- Function `public.set_updated_at()` — sets `NEW.updated_at = now()`.
- `BEFORE UPDATE` triggers applying it to the 6 tables that declare `updated_at`: `departments`, `profiles`, `curricula`, `students`, `advisor_notes`, `student_courses`.

_Part B — Auth integration_

- Function `public.handle_new_user()` (security definer) — inserts a `profiles` row for a new `auth.users` row, using `raw_user_meta_data ->> 'full_name'` (falling back to email) and the user's email. Uses `ON CONFLICT (id) DO NOTHING` for idempotency.
- Trigger `trg_auth_user_created` — `AFTER INSERT ON auth.users`, calls `handle_new_user()`.

Note: role assignment (`user_roles`) is **not** done automatically — a new account has no role/access until an admin explicitly grants `admin` or `academic_advisor`.

**Dependencies**: `003_schema.sql` (the 6 tables and `profiles` must exist). Requires `auth.users` to exist, which it always does in a Supabase project.

---

## 006_rls.sql

**Purpose**: Enable Row Level Security on every table and define the access policies for the two staff roles, built entirely on `profiles` / `roles` / `user_roles` (no separate permission system). See `RLS_SECURITY.md` for the full policy-by-table breakdown.

**Creates**

_Helper functions_ (all `security definer`, `stable`):

- `public.has_role(p_role_code text) returns boolean`
- `public.is_admin() returns boolean`
- `public.is_advisor() returns boolean`
- `public.is_staff() returns boolean` (= `is_admin() OR is_advisor()`)

_Policy groups_:

- **17 "knowledge-base / academic record" tables** (`departments`, `roles`, `curricula`, `curriculum_courses`, `course_prerequisites`, `elective_groups`, `elective_group_courses`, `graduation_requirements`, `academic_rules`, `grade_scale`, `students`, `student_semesters`, `student_courses`, `advisor_assignments`, `academic_analyses`, `analysis_issues`, `department_statistics`) — RLS enabled via a `DO` loop; each gets a `*_select_staff` policy (`is_staff()`) and a `*_admin_all` policy (`is_admin()`).
- **`profiles`** — select/update own row or admin; admin full access.
- **`user_roles`** — select own grants or admin; admin full access.
- **`import_jobs`** — staff select; insert by staff (`uploaded_by = auth.uid()`); update by owner or admin; delete by admin.
- **`imported_files`, `raw_students`, `raw_courses`** — RLS enabled via a `DO` loop; staff select + insert, admin-only update/delete.
- **`advisor_notes`** — staff select (shared visibility); insert by staff (`advisor_id = auth.uid()`); update/delete by author or admin.
- **`reports`** — staff select; insert by staff (`generated_by = auth.uid()`); update/delete by author or admin.

**Dependencies**: `003_schema.sql` (all tables must exist) and `004_constraints_indexes.sql` (the `user_roles(user_id)` index used by `has_role()` — ordering convenience, not a hard requirement).

---

## 007_storage_notes.sql

**Purpose**: Create the two Supabase Storage buckets used by the application and their access policies, reusing the same `is_staff()` / `is_admin()` helpers from `006`.

**Creates**

- Bucket `imports` (private) — for uploaded Excel workbooks, referenced by `imported_files.storage_path`.
- Bucket `reports` (private) — optional rendered report files; if used, the path is embedded inside `reports.data` (e.g. `data ->> 'file_path'`) — **no new column was added**.
- `storage.objects` policies for both buckets: staff can `select`/`insert`/`update`; `delete` restricted to the object owner or an admin.
- Documents (as comments, not enforced by SQL) the path conventions: `imports/{import_job_id}/{original_name}` and `reports/{report_id}.pdf`.

**Dependencies**: `006_rls.sql` (uses `public.is_staff()` and `public.is_admin()`).

---

## 008_seed.sql

**Purpose**: Insert static reference data only — no fake students or academic records.

**Creates (inserts)**

- `roles`: `admin`, `academic_advisor` (with Arabic/English names and descriptions).
- `grade_scale`: 11 regular letter grades (`A` … `F`) with points and score ranges, plus 8 special symbols (`W`, `AU`, `S`, `MW`, `FW`, `EX`, `IC`, `TC`) with `affects_gpa = false`.

All inserts use `ON CONFLICT DO NOTHING` for safe re-runs.

**Explicitly not seeded** (documented in the file itself): `departments`, `curricula`, `curriculum_courses`, `course_prerequisites`, `elective_groups`/`elective_group_courses`, `graduation_requirements`, `academic_rules`, `students` and all academic records, `profiles`/`user_roles` (created via signup + admin role assignment).

**Dependencies**: `003_schema.sql` (`roles` and `grade_scale` tables must exist).

---

## 009_views.sql

**Purpose**: A small number of views that simplify recurring application queries.

**Creates** (3 views)

1. `latest_academic_analyses` — most recent `academic_analyses` row per student (`DISTINCT ON (student_id) ... ORDER BY analyzed_at DESC`).
2. `student_academic_summary` — one row per student joining `students` + `departments` + `curricula` + `latest_academic_analyses`, with computed `remaining_hours` and `graduation_progress_percent`. Backs report #1 (Academic Summary).
3. `department_status_overview` — per-department live counts of students by `academic_status`/`risk_level` plus average GPA. Backs report #9 (Students Overview).

**Dependencies**: `003_schema.sql` (`students`, `departments`, `curricula`, `academic_analyses`, `student_semesters` — note `student_academic_summary` itself doesn't need `student_semesters`, but `fn_student_academic_summary` in `010` does).

---

## 010_functions.sql

**Purpose**: A small number of RPC functions for computations that are awkward to repeat as client-side SQL — **not** a place for expert-system logic (status diagnosis, risk prediction, recommendations remain in the application layer).

**Creates** (2 functions, both `security invoker`, `stable`)

1. `public.fn_student_completion_percentage(p_student_id uuid) returns numeric` — `completed_hours / curricula.total_required_hours * 100`, rounded to 2 decimals. Distinct from the cached `students.completion_rate` (which is `completed_hours / attempted_hours`).
2. `public.fn_student_academic_summary(p_student_id uuid) returns jsonb` — wraps `student_academic_summary` (from `009`) plus an ordered array of the student's `student_semesters` (semester number, year, term, level, GPA, hours), as one JSON object for rendering report #1 in a single RPC call.

**Dependencies**: `003_schema.sql` (`students`, `curricula`, `student_semesters`) and `009_views.sql` (`student_academic_summary`).

---

## Quick Reference Table

| #   | File                      | Creates                                                            | Depends on     |
| --- | ------------------------- | ------------------------------------------------------------------ | -------------- |
| 001 | `extensions.sql`          | `pgcrypto` extension                                               | —              |
| 002 | `enums.sql`               | 6 enum types                                                       | 001 (ordering) |
| 003 | `schema.sql`              | 25 tables                                                          | 001, 002       |
| 004 | `constraints_indexes.sql` | CHECK constraints + indexes                                        | 003            |
| 005 | `triggers.sql`            | `set_updated_at()`, 6 triggers, `handle_new_user()` + auth trigger | 003            |
| 006 | `rls.sql`                 | 4 helper functions, RLS on all 25 tables                           | 003, 004       |
| 007 | `storage_notes.sql`       | 2 storage buckets + object policies                                | 006            |
| 008 | `seed.sql`                | `roles` + `grade_scale` data                                       | 003            |
| 009 | `views.sql`               | 3 views                                                            | 003            |
| 010 | `functions.sql`           | 2 RPC functions                                                    | 003, 009       |
