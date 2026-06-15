# Acadexa — Row Level Security (RLS) & Roles

This document explains the security model implemented in `006_rls.sql` (and the storage policies in `007_storage_notes.sql`). It is built **entirely** on the existing `profiles` / `roles` / `user_roles` tables — there is no separate permission system.

---

## 1. Architecture

Every one of the 25 tables has **`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`** applied. Postgres RLS works by attaching one or more _policies_ to a table; for a given operation (`SELECT`/`INSERT`/`UPDATE`/`DELETE`), a row is visible/allowed if **any** applicable permissive policy's condition evaluates to `true` (policies are OR'd together).

```
auth.uid()  ──►  profiles.id
                      │
                      ▼
                 user_roles ──► roles.code
                      │
        ┌─────────────┴─────────────┐
        ▼                            ▼
  has_role('admin')          has_role('academic_advisor')
        │                            │
        ▼                            ▼
     is_admin()                  is_advisor()
        │                            │
        └──────────┬─────────────────┘
                    ▼
                is_staff()
```

Two important notes:

1. **`service_role` bypasses RLS entirely.** The Excel parser and the expert-system inference engine run as backend jobs using the Supabase `service_role` key, so they are never blocked by anything in this document, regardless of which user (if any) triggered them.
2. **No `student` role exists.** Per the confirmed requirement, students never authenticate to this system — `roles` contains only `admin` and `academic_advisor` (seeded in `008_seed.sql`). If a student-facing portal is ever added, it would need its own role and policy set, entirely additive to what's below.

---

## 2. Helper Functions

All four are defined in `006_rls.sql` as `security definer`, `stable`, `language sql`, with `search_path = public` (so they can read `user_roles`/`roles` regardless of the calling user's own RLS visibility into those tables).

| Function                     | Returns   | Logic                                                                                                                           |
| ---------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `has_role(p_role_code text)` | `boolean` | `EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE ur.user_id = auth.uid() AND r.code = p_role_code)` |
| `is_admin()`                 | `boolean` | `has_role('admin')`                                                                                                             |
| `is_advisor()`               | `boolean` | `has_role('academic_advisor')`                                                                                                  |
| `is_staff()`                 | `boolean` | `is_admin() OR is_advisor()`                                                                                                    |

These four functions are the **only** building blocks used in every policy below — there is no row-level ownership logic beyond "is this MY row" checks on a handful of tables (`profiles`, `user_roles`, `import_jobs`, `advisor_notes`, `reports`).

---

## 3. Roles

### `admin`

- **Arabic**: مدير النظام
- **Access**: full read/write on every table, including the knowledge-base/configuration tables (`departments`, `curricula`, `curriculum_courses`, `course_prerequisites`, `elective_groups`/`elective_group_courses`, `graduation_requirements`, `academic_rules`, `grade_scale`, `roles`, `user_roles`).
- **Rationale**: these tables represent the institution's official regulations and rules — "values are not hardcoded, but only an authorized admin updates them" (per the original Knowledge Base requirement). Advisors can _read_ this data (they need it to advise) but never modify it.

### `academic_advisor`

- **Arabic**: مرشد أكاديمي
- **Access**: read access to all academic data needed for advising (departments, curricula, curriculum courses, students, transcripts, analyses, issues, etc.). Write access limited to:
  - their own profile,
  - starting/managing their own `import_jobs`,
  - writing `advisor_notes` (visible to everyone, editable only by the author or an admin),
  - generating `reports` (visible to everyone, editable only by the author or an admin).
- **Rationale**: confirmed requirement — _any_ advisor can be responsible for students in _any_ department, and notes are shared across all staff. So an advisor's read access is not scoped to "their" students; `advisor_assignments` is a dashboard filter, not an RLS boundary.

---

## 4. Permission Matrix

Legend: **S** = `is_staff()` (admin or advisor), **A** = `is_admin()` only, **own** = row owned by `auth.uid()` (or admin), **trigger** = row created by a `security definer` trigger function, bypassing normal INSERT policy.

### 4.1 Knowledge base / academic-structure / curriculum tables

_(RLS enabled via the shared `DO` loop in `006_rls.sql` — identical policy shape for all of these)_

| Table                     | SELECT | INSERT | UPDATE | DELETE |
| ------------------------- | ------ | ------ | ------ | ------ |
| `departments`             | S      | A      | A      | A      |
| `roles`                   | S      | A      | A      | A      |
| `curricula`               | S      | A      | A      | A      |
| `curriculum_courses`      | S      | A      | A      | A      |
| `course_prerequisites`    | S      | A      | A      | A      |
| `elective_groups`         | S      | A      | A      | A      |
| `elective_group_courses`  | S      | A      | A      | A      |
| `graduation_requirements` | S      | A      | A      | A      |
| `academic_rules`          | S      | A      | A      | A      |
| `grade_scale`             | S      | A      | A      | A      |

### 4.2 Student-record / advisory / expert-system / reporting tables

_(also via the shared `DO` loop — same policy shape: staff read, admin write)_

| Table                   | SELECT | INSERT | UPDATE | DELETE |
| ----------------------- | ------ | ------ | ------ | ------ |
| `students`              | S      | A      | A      | A      |
| `student_semesters`     | S      | A      | A      | A      |
| `student_courses`       | S      | A      | A      | A      |
| `advisor_assignments`   | S      | A      | A      | A      |
| `academic_analyses`     | S      | A      | A      | A      |
| `analysis_issues`       | S      | A      | A      | A      |
| `department_statistics` | S      | A      | A      | A      |

> In practice, `students`/`student_semesters`/`student_courses`/`academic_analyses`/`analysis_issues` are written by backend jobs via `service_role` (the import pipeline and the expert-system engine), which bypass RLS — the `A`-only policy here is the _fallback for direct admin edits_ through the dashboard/SQL editor, e.g. manually correcting a record.

### 4.3 `profiles`

| Operation | Allowed when                                                                                                         |
| --------- | -------------------------------------------------------------------------------------------------------------------- |
| SELECT    | `id = auth.uid()` **or** `is_admin()`                                                                                |
| UPDATE    | `id = auth.uid()` **or** `is_admin()`                                                                                |
| INSERT    | via `handle_new_user()` trigger (security definer) on signup; also `is_admin()` through the general admin-all policy |
| DELETE    | `is_admin()`                                                                                                         |

A staff member can see and edit their own profile (name, phone, avatar); an admin can see/manage everyone's.

### 4.4 `user_roles`

| Operation                | Allowed when                               |
| ------------------------ | ------------------------------------------ |
| SELECT                   | `user_id = auth.uid()` **or** `is_admin()` |
| INSERT / UPDATE / DELETE | `is_admin()` only                          |

A staff member can see _which roles they hold_, but only an admin can grant/revoke roles — this is the actual "make someone an advisor/admin" action.

### 4.5 `import_jobs`

| Operation | Allowed when                                                                                                  |
| --------- | ------------------------------------------------------------------------------------------------------------- |
| SELECT    | `is_staff()` — all imports are visible to all staff (shared workflow)                                         |
| INSERT    | `is_staff() AND uploaded_by = auth.uid()` — you can only create a job attributed to yourself                  |
| UPDATE    | `is_admin() OR uploaded_by = auth.uid()` — the uploader can update/cancel their own job; admin can update any |
| DELETE    | `is_admin()` only                                                                                             |

### 4.6 `imported_files`, `raw_students`, `raw_courses`

_(RLS enabled via a shared `DO` loop — identical policy shape for all three staging tables)_

| Operation | Allowed when |
| --------- | ------------ |
| SELECT    | `is_staff()` |
| INSERT    | `is_staff()` |
| UPDATE    | `is_admin()` |
| DELETE    | `is_admin()` |

### 4.7 `advisor_notes`

| Operation | Allowed when                                                                                |
| --------- | ------------------------------------------------------------------------------------------- |
| SELECT    | `is_staff()` — **visible to all staff**, confirmed requirement (not private to the author)  |
| INSERT    | `is_staff() AND advisor_id = auth.uid()` — a note is always attributed to its actual author |
| UPDATE    | `is_admin() OR advisor_id = auth.uid()`                                                     |
| DELETE    | `is_admin() OR advisor_id = auth.uid()`                                                     |

### 4.8 `reports`

| Operation | Allowed when                                                  |
| --------- | ------------------------------------------------------------- |
| SELECT    | `is_staff()` — all generated reports are visible to all staff |
| INSERT    | `is_staff() AND generated_by = auth.uid()`                    |
| UPDATE    | `is_admin() OR generated_by = auth.uid()`                     |
| DELETE    | `is_admin() OR generated_by = auth.uid()`                     |

---

## 5. Storage Policies (`007_storage_notes.sql`)

Two private buckets, both using `is_staff()` / `is_admin()` on `storage.objects`:

| Bucket    | SELECT       | INSERT       | UPDATE       | DELETE                             |
| --------- | ------------ | ------------ | ------------ | ---------------------------------- |
| `imports` | `is_staff()` | `is_staff()` | `is_staff()` | `is_admin() OR owner = auth.uid()` |
| `reports` | `is_staff()` | `is_staff()` | `is_staff()` | `is_admin() OR owner = auth.uid()` |

Both buckets are `public = false` — every access goes through these policies or a signed URL generated server-side.

---

## 6. Summary — "Who can do what"

| Action                                                                                                               | admin | academic_advisor                                        |
| -------------------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------- |
| View any department/curriculum/course/rule                                                                           | ✅    | ✅                                                      |
| Edit departments, curricula, courses, prerequisites, electives, graduation requirements, academic rules, grade scale | ✅    | ❌                                                      |
| Grant/revoke roles (`user_roles`)                                                                                    | ✅    | ❌                                                      |
| View any student's transcript, analyses, issues                                                                      | ✅    | ✅                                                      |
| Manually edit a student/transcript row via dashboard                                                                 | ✅    | ❌ (normally done by backend import/expert-system jobs) |
| Upload an Excel workbook (`import_jobs`)                                                                             | ✅    | ✅ (own jobs)                                           |
| View all import jobs / raw staging data                                                                              | ✅    | ✅                                                      |
| Write an advisor note (visible to everyone)                                                                          | ✅    | ✅                                                      |
| Edit/delete _someone else's_ advisor note                                                                            | ✅    | ❌                                                      |
| Generate a report (visible to everyone)                                                                              | ✅    | ✅                                                      |
| Edit/delete _someone else's_ saved report                                                                            | ✅    | ❌                                                      |
| Manage advisor↔student assignments                                                                                   | ✅    | ❌ (read-only — used as a personal dashboard filter)    |
