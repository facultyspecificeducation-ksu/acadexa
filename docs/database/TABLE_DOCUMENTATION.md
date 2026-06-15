# Acadexa — Table Documentation

Every table in the implemented schema (migrations `003_schema.sql` + `004_constraints_indexes.sql`), in the order requested. For each table: **purpose**, **columns** (name, type, constraints, description), and **relationships**.

Conventions used below:

- `uuid` PKs default to `gen_random_uuid()` unless noted.
- "NOT NULL" is omitted from the description column when obvious from the type column (`required` / nullable is stated explicitly only where it matters).
- Enum types are defined in `002_enums.sql`.

---

## profiles

**Purpose**: Staff profile, one row per Supabase Auth user (`auth.users`). Created automatically by the `handle_new_user` trigger on signup. Holds display/contact info and account status; role membership lives in `user_roles`.

| Column       | Type          | Constraints                                         | Description                                                           |
| ------------ | ------------- | --------------------------------------------------- | --------------------------------------------------------------------- |
| `id`         | `uuid`        | PK, FK → `auth.users.id` ON DELETE CASCADE          | Same ID as the Supabase Auth user.                                    |
| `full_name`  | `text`        | NOT NULL                                            | Staff member's display name (from signup metadata, fallback = email). |
| `email`      | `text`        | NOT NULL, UNIQUE                                    | Contact email (copied from `auth.users` at creation).                 |
| `phone`      | `text`        | nullable                                            | Optional contact number.                                              |
| `avatar_url` | `text`        | nullable                                            | Optional profile picture URL.                                         |
| `is_active`  | `boolean`     | NOT NULL, default `true`                            | Soft-disable a staff account without deleting it.                     |
| `created_at` | `timestamptz` | NOT NULL, default `now()`                           |                                                                       |
| `updated_at` | `timestamptz` | NOT NULL, default `now()`, auto-updated via trigger |                                                                       |

**Relationships**

- `auth.users (1) ──► profiles (1)` — one-to-one, created by `trg_auth_user_created`.
- `profiles (1) ──► user_roles (N)` — a profile can hold multiple roles.
- Referenced by: `import_jobs.uploaded_by`, `advisor_assignments.advisor_id`, `advisor_notes.advisor_id`, `reports.generated_by`.

---

## roles

**Purpose**: Static lookup of the two roles in the system. Seeded once in `008_seed.sql`.

| Column        | Type   | Constraints                     | Description                                                |
| ------------- | ------ | ------------------------------- | ---------------------------------------------------------- |
| `id`          | `uuid` | PK, default `gen_random_uuid()` |                                                            |
| `code`        | `text` | NOT NULL, UNIQUE                | Machine-readable role code: `admin` or `academic_advisor`. |
| `name_ar`     | `text` | NOT NULL                        | Arabic display name (e.g. "مدير النظام").                  |
| `name_en`     | `text` | NOT NULL                        | English display name (e.g. "Admin").                       |
| `description` | `text` | nullable                        | Free-text description of what the role can do.             |

**Relationships**

- `roles (1) ──► user_roles (N)`.

---

## user_roles

**Purpose**: Join table granting a role to a profile. A profile can hold both roles (e.g. an admin who also advises). Read by the RLS helper functions `has_role()`, `is_admin()`, `is_advisor()`.

| Column       | Type          | Constraints                                    | Description                |
| ------------ | ------------- | ---------------------------------------------- | -------------------------- |
| `id`         | `uuid`        | PK, default `gen_random_uuid()`                |                            |
| `user_id`    | `uuid`        | NOT NULL, FK → `profiles.id` ON DELETE CASCADE | The staff member.          |
| `role_id`    | `uuid`        | NOT NULL, FK → `roles.id` ON DELETE CASCADE    | The granted role.          |
| `created_at` | `timestamptz` | NOT NULL, default `now()`                      | When the role was granted. |

**Constraints**: `UNIQUE (user_id, role_id)` — a role can't be granted twice to the same user.

**Relationships**

- `profiles (1) ──► user_roles (N) ◄── (1) roles` — many-to-many between profiles and roles.

---

## departments

**Purpose**: The 10 academic departments/programs of the college. The root of the academic-structure module — curricula, students, import jobs, reports and department statistics all hang off this table.

| Column       | Type          | Constraints                                         | Description                                               |
| ------------ | ------------- | --------------------------------------------------- | --------------------------------------------------------- |
| `id`         | `uuid`        | PK, default `gen_random_uuid()`                     |                                                           |
| `code`       | `text`        | NOT NULL, UNIQUE                                    | Short department code.                                    |
| `name_ar`    | `text`        | NOT NULL                                            | Arabic name (e.g. "قسم تكنولوجيا التعليم والحاسب الآلي"). |
| `name_en`    | `text`        | NOT NULL                                            | English name.                                             |
| `short_name` | `text`        | nullable                                            | Optional abbreviation.                                    |
| `is_active`  | `boolean`     | NOT NULL, default `true`                            |                                                           |
| `created_at` | `timestamptz` | NOT NULL, default `now()`                           |                                                           |
| `updated_at` | `timestamptz` | NOT NULL, default `now()`, auto-updated via trigger |                                                           |

**Relationships**

- `departments (1) ──► curricula (N)` — one row per regulation year for this department.
- `departments (1) ──► students (N)`.
- `departments (1) ──► import_jobs (N)` — one workbook = one department, chosen at upload.
- `departments (1) ──► reports (N)` — for department-scoped reports.
- `departments (1) ──► department_statistics (N)`.

---

## curricula

**Purpose**: One row per **(department, regulation year)** — e.g. "قسم الإعلام التربوي — 2024". This is the unit a student is permanently bound to at enrollment (resolved from `department_id` + `enrollment_year`). Everything the expert system needs for that regulation (courses, prerequisites, electives, graduation requirements, rules) hangs off this row.

| Column                 | Type           | Constraints                                         | Description                                                    |
| ---------------------- | -------------- | --------------------------------------------------- | -------------------------------------------------------------- |
| `id`                   | `uuid`         | PK, default `gen_random_uuid()`                     |                                                                |
| `department_id`        | `uuid`         | NOT NULL, FK → `departments.id`                     |                                                                |
| `regulation_year`      | `integer`      | NOT NULL                                            | e.g. `2019`, `2021`, `2023`, `2024`, `2026`.                   |
| `name_ar`              | `text`         | NOT NULL                                            | Display name for the curriculum (e.g. "لائحة 2024 - قسم ..."). |
| `total_required_hours` | `integer`      | NOT NULL, CHECK `> 0`                               | Total credit hours required to graduate under this curriculum. |
| `min_gpa_to_graduate`  | `numeric(4,2)` | NOT NULL, CHECK `0 ≤ x ≤ 4`                         | Minimum cumulative GPA required for graduation.                |
| `is_active`            | `boolean`      | NOT NULL, default `true`                            |                                                                |
| `created_at`           | `timestamptz`  | NOT NULL, default `now()`                           |                                                                |
| `updated_at`           | `timestamptz`  | NOT NULL, default `now()`, auto-updated via trigger |                                                                |

**Constraints**: `UNIQUE (department_id, regulation_year)` — at most one curriculum per department per regulation year.

**Relationships**

- `departments (1) ──► curricula (N)`.
- `curricula (1) ──► curriculum_courses (N)`.
- `curricula (1) ──► graduation_requirements (1)` — one-to-one.
- `curricula (1) ──► academic_rules (1)` — one-to-one.
- `curricula (1) ──► elective_groups (N)`.
- `curricula (1) ──► students (N)`.

---

## curriculum_courses

**Purpose**: The course catalog for one curriculum — every course a student under this regulation may take, with its category, level/term, and special-purpose flags (field training, graduation project, community-issues course).

| Column                       | Type                   | Constraints                                     | Description                                                                                                               |
| ---------------------------- | ---------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `id`                         | `uuid`                 | PK, default `gen_random_uuid()`                 |                                                                                                                           |
| `curriculum_id`              | `uuid`                 | NOT NULL, FK → `curricula.id` ON DELETE CASCADE |                                                                                                                           |
| `course_code`                | `text`                 | nullable                                        | Fixed code per regulation. Nullable because the community-issues course may have none.                                    |
| `name_ar`                    | `text`                 | NOT NULL                                        |                                                                                                                           |
| `name_en`                    | `text`                 | nullable                                        |                                                                                                                           |
| `credit_hours`               | `integer`              | NOT NULL, CHECK `> 0`                           |                                                                                                                           |
| `level`                      | `integer`              | NOT NULL, CHECK `1 ≤ x ≤ 4`                     | Study level the course belongs to.                                                                                        |
| `term`                       | `term_enum`            | NOT NULL                                        | `fall`, `spring`, or `summer`.                                                                                            |
| `category`                   | `course_category_enum` | NOT NULL                                        | `university_required`, `university_elective`, `college_required`, `college_elective`, `major_required`, `major_elective`. |
| `is_field_training`          | `boolean`              | NOT NULL, default `false`                       | Marks the mandatory field-training course.                                                                                |
| `is_graduation_project`      | `boolean`              | NOT NULL, default `false`                       | Marks the graduation project course.                                                                                      |
| `is_community_issues_course` | `boolean`              | NOT NULL, default `false`                       | Marks "القضايا المجتمعية" — identified by this flag (and name) since it may lack a course code.                           |
| `is_active`                  | `boolean`              | NOT NULL, default `true`                        |                                                                                                                           |

**Constraints**: `UNIQUE (curriculum_id, course_code)` — `NULL` codes don't collide (Postgres treats distinct `NULL`s as non-equal), so multiple no-code courses per curriculum are allowed.

**Relationships**

- `curricula (1) ──► curriculum_courses (N)`.
- `curriculum_courses (1) ──► course_prerequisites (N)` — both as `course_id` and `required_course_id`.
- `curriculum_courses (1) ──► elective_group_courses (N)`.
- `curriculum_courses (1) ──► student_courses (N)` — via `student_courses.curriculum_course_id` (nullable match).

---

## course_prerequisites

**Purpose**: Prerequisite graph between courses within the same curriculum. Read by the expert system's "Prerequisite Violation" check and the "next courses to register" recommendation logic.

| Column               | Type   | Constraints                                              | Description                                                                           |
| -------------------- | ------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `id`                 | `uuid` | PK, default `gen_random_uuid()`                          |                                                                                       |
| `course_id`          | `uuid` | NOT NULL, FK → `curriculum_courses.id` ON DELETE CASCADE | The course that has a prerequisite.                                                   |
| `required_course_id` | `uuid` | NOT NULL, FK → `curriculum_courses.id` ON DELETE CASCADE | The course that must be completed first.                                              |
| `minimum_grade`      | `text` | nullable, FK → `grade_scale.grade_letter`                | If set, the prerequisite requires at least this grade; `NULL` means "pass is enough". |

**Constraints**:

- `UNIQUE (course_id, required_course_id)`.
- `CHECK (course_id <> required_course_id)` — a course cannot be its own prerequisite.

**Relationships**

- `curriculum_courses (1) ──► course_prerequisites (N)` (as `course_id`).
- `curriculum_courses (1) ──► course_prerequisites (N)` (as `required_course_id`).
- `grade_scale (1) ──► course_prerequisites (N)` (via `minimum_grade`, optional).

---

## elective_groups

**Purpose**: A named bucket of elective courses with a dual completion requirement — total hours **and** minimum number of distinct courses (e.g. "اختيارية تخصص: 6 ساعات وعدد 2 مقررات على الأقل"). The expert system checks both conditions against `student_courses` joined through `elective_group_courses`.

| Column           | Type                   | Constraints                                     | Description                                                  |
| ---------------- | ---------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| `id`             | `uuid`                 | PK, default `gen_random_uuid()`                 |                                                              |
| `curriculum_id`  | `uuid`                 | NOT NULL, FK → `curricula.id` ON DELETE CASCADE |                                                              |
| `name`           | `text`                 | NOT NULL                                        | Display name of the elective bucket.                         |
| `category`       | `course_category_enum` | NOT NULL                                        | Typically `university_elective` or `major_elective`.         |
| `required_hours` | `integer`              | NOT NULL, CHECK `> 0`                           | Minimum total credit hours required from this group.         |
| `min_courses`    | `integer`              | NOT NULL, default `1`, CHECK `≥ 1`              | Minimum number of distinct courses required from this group. |

**Relationships**

- `curricula (1) ──► elective_groups (N)`.
- `elective_groups (1) ──► elective_group_courses (N)`.

---

## elective_group_courses

**Purpose**: Membership join table — which `curriculum_courses` count toward a given `elective_groups` bucket. No separate "student elective selection" table exists; a student's elective choices are inferred by joining `student_courses` (passed courses) to this table.

| Column      | Type   | Constraints                                                    | Description |
| ----------- | ------ | -------------------------------------------------------------- | ----------- |
| `group_id`  | `uuid` | PK (composite), FK → `elective_groups.id` ON DELETE CASCADE    |             |
| `course_id` | `uuid` | PK (composite), FK → `curriculum_courses.id` ON DELETE CASCADE |             |

**Constraints**: `PRIMARY KEY (group_id, course_id)` — a course can belong to a group only once.

**Relationships**

- `elective_groups (1) ──► elective_group_courses (N) ◄── (1) curriculum_courses` — many-to-many between elective groups and curriculum courses.

---

## graduation_requirements

**Purpose**: One row per curriculum describing the conditions that must all hold for `Graduation Status = Eligible` (hours, GPA, field training, community-issues course, optional max study duration).

| Column                      | Type           | Constraints                                             | Description                                                                                                        |
| --------------------------- | -------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `id`                        | `uuid`         | PK, default `gen_random_uuid()`                         |                                                                                                                    |
| `curriculum_id`             | `uuid`         | NOT NULL, UNIQUE, FK → `curricula.id` ON DELETE CASCADE | One-to-one with `curricula`.                                                                                       |
| `required_hours`            | `integer`      | NOT NULL, CHECK `> 0`                                   | Total hours required to graduate (mirrors `curricula.total_required_hours`, kept here for the requirements check). |
| `min_gpa`                   | `numeric(4,2)` | NOT NULL, CHECK `0 ≤ x ≤ 4`                             | Minimum cumulative GPA to graduate.                                                                                |
| `requires_field_training`   | `boolean`      | NOT NULL, default `true`                                | Whether field training is mandatory.                                                                               |
| `field_training_levels`     | `integer[]`    | nullable                                                | Which study levels field training occurs in (e.g. `{3,4}`).                                                        |
| `requires_community_course` | `boolean`      | NOT NULL, default `true`                                | Whether the community-issues course is mandatory.                                                                  |
| `community_course_name_ar`  | `text`         | default `'القضايا المجتمعية'`                           | Name used to match the course when it has no `course_code`.                                                        |
| `max_study_years`           | `integer`      | nullable, CHECK `(NULL or > 0)`                         | Optional cap on years to complete the program.                                                                     |

**Relationships**

- `curricula (1) ──► graduation_requirements (1)` — one-to-one.

---

## academic_rules

**Purpose**: One row per curriculum holding the **dynamic, database-driven** thresholds the inference engine reads instead of hardcoding (probation GPA, registration load limits, level-progression hour thresholds). `extra_rules` is an open escape hatch for any future rule that doesn't yet have its own column.

| Column                   | Type           | Constraints                                                                    | Description                                                                                   |
| ------------------------ | -------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `id`                     | `uuid`         | PK, default `gen_random_uuid()`                                                |                                                                                               |
| `curriculum_id`          | `uuid`         | NOT NULL, UNIQUE, FK → `curricula.id` ON DELETE CASCADE                        | One-to-one with `curricula`.                                                                  |
| `probation_min_gpa`      | `numeric(4,2)` | NOT NULL, CHECK `0 ≤ x ≤ 4`                                                    | `IF student_gpa < probation_min_gpa THEN status = Probation`.                                 |
| `max_hours_regular_term` | `integer`      | NOT NULL                                                                       | Max credit hours a student may register in a regular (fall/spring) term.                      |
| `min_hours_regular_term` | `integer`      | NOT NULL, CHECK `> 0`, CHECK `max_hours_regular_term ≥ min_hours_regular_term` | Min credit hours per regular term.                                                            |
| `max_hours_summer`       | `integer`      | NOT NULL, CHECK `> 0`                                                          | Max credit hours in a summer term.                                                            |
| `level_2_min_hours`      | `integer`      | NOT NULL, CHECK `≥ 0`                                                          | Minimum completed hours to be considered Level 2.                                             |
| `level_3_min_hours`      | `integer`      | NOT NULL, CHECK `≥ level_2_min_hours`                                          | Minimum completed hours for Level 3.                                                          |
| `level_4_min_hours`      | `integer`      | NOT NULL, CHECK `≥ level_3_min_hours`                                          | Minimum completed hours for Level 4.                                                          |
| `extra_rules`            | `jsonb`        | nullable                                                                       | Open-ended key/value rules (e.g. `{"max_failed_repeats": 3}`) read generically by the engine. |

**Relationships**

- `curricula (1) ──► academic_rules (1)` — one-to-one.

---

## grade_scale

**Purpose**: Global grading scale — the **only** place letter grades map to GPA points, score ranges, and whether they affect GPA. Covers both the regular A..F letters and the special symbols (W, AU, S, MW, FW, EX, IC, TC). Seeded in `008_seed.sql`.

| Column         | Type           | Constraints                              | Description                                                                   |
| -------------- | -------------- | ---------------------------------------- | ----------------------------------------------------------------------------- |
| `grade_letter` | `text`         | PK                                       | e.g. `A`, `A-`, `B+`, ..., `F`, `W`, `AU`, `S`, `MW`, `FW`, `EX`, `IC`, `TC`. |
| `name_ar`      | `text`         | NOT NULL                                 | Arabic name (e.g. "ممتاز", "الانسحاب").                                       |
| `points`       | `numeric(4,2)` | NOT NULL, default `0`, CHECK `0 ≤ x ≤ 4` | GPA points for this grade. `0` for `F` and all special symbols.               |
| `min_score`    | `numeric(5,2)` | nullable                                 | Lower bound of the score range (only meaningful for A..F).                    |
| `max_score`    | `numeric(5,2)` | nullable                                 | Upper bound of the score range.                                               |
| `affects_gpa`  | `boolean`      | NOT NULL, default `true`                 | `false` for all special symbols (W, AU, S, MW, FW, EX, IC, TC).               |
| `is_passing`   | `boolean`      | NOT NULL                                 | Whether this grade counts as "passed" for prerequisite/requirement checks.    |
| `description`  | `text`         | nullable                                 | Free-text explanation (mainly for special symbols).                           |

**Constraints**: `CHECK ((min_score IS NULL AND max_score IS NULL) OR (min_score ≥ 0 AND max_score ≤ 100 AND max_score ≥ min_score))`.

**Relationships**

- `grade_scale (1) ──► course_prerequisites (N)` (via `minimum_grade`, optional).
- `grade_scale (1) ──► student_courses (N)` (via `grade_letter`, required).

---

## import_jobs

**Purpose**: One row per Excel workbook upload. Since one workbook = one department, `department_id` is chosen explicitly by the uploader at upload time (not inferred from the sheet). Tracks status and result counts for the whole job.

| Column               | Type                 | Constraints                        | Description                                                       |
| -------------------- | -------------------- | ---------------------------------- | ----------------------------------------------------------------- |
| `id`                 | `uuid`               | PK, default `gen_random_uuid()`    |                                                                   |
| `uploaded_by`        | `uuid`               | NOT NULL, FK → `profiles.id`       | Staff member who started the import.                              |
| `department_id`      | `uuid`               | NOT NULL, FK → `departments.id`    | The department this workbook belongs to (chosen at upload).       |
| `file_name`          | `text`               | NOT NULL                           | Original workbook filename.                                       |
| `file_url`           | `text`               | nullable                           | Optional direct URL/reference.                                    |
| `status`             | `import_status_enum` | NOT NULL, default `'pending'`      | `pending`, `processing`, `completed`, `failed`.                   |
| `total_students`     | `integer`            | NOT NULL, default `0`, CHECK `≥ 0` | Total sheets/students found.                                      |
| `successful_records` | `integer`            | NOT NULL, default `0`, CHECK `≥ 0` |                                                                   |
| `failed_records`     | `integer`            | NOT NULL, default `0`, CHECK `≥ 0` |                                                                   |
| `error_log`          | `jsonb`              | nullable                           | Array of `{sheet, error}` objects, matching `ExcelParser.errors`. |
| `created_at`         | `timestamptz`        | NOT NULL, default `now()`          |                                                                   |
| `completed_at`       | `timestamptz`        | nullable                           | Set when the job finishes.                                        |

**Constraints**: `CHECK (total_students ≥ 0 AND successful_records ≥ 0 AND failed_records ≥ 0 AND (successful_records + failed_records) ≤ total_students)`.

**Relationships**

- `profiles (1) ──► import_jobs (N)` (uploader).
- `departments (1) ──► import_jobs (N)`.
- `import_jobs (1) ──► imported_files (N)`.
- `import_jobs (1) ──► raw_students (N)`.
- `import_jobs (1) ──► students (N)` (via `students.last_import_job_id`, nullable).

---

## imported_files

**Purpose**: The physical file(s) behind an import job (usually one, but allows multi-file batches and re-upload detection via `hash`). Path stored here corresponds to an object in the `imports` Storage bucket.

| Column          | Type          | Constraints                                       | Description                           |
| --------------- | ------------- | ------------------------------------------------- | ------------------------------------- |
| `id`            | `uuid`        | PK, default `gen_random_uuid()`                   |                                       |
| `import_job_id` | `uuid`        | NOT NULL, FK → `import_jobs.id` ON DELETE CASCADE |                                       |
| `original_name` | `text`        | NOT NULL                                          | Filename as uploaded.                 |
| `storage_path`  | `text`        | NOT NULL                                          | Path in the `imports` Storage bucket. |
| `hash`          | `text`        | nullable                                          | SHA-256, for re-upload detection.     |
| `created_at`    | `timestamptz` | NOT NULL, default `now()`                         |                                       |

**Relationships**

- `import_jobs (1) ──► imported_files (N)`.

---

## raw_students

**Purpose**: **Parser staging** — one row per Excel sheet (= one student record), holding the **untouched** output of `parse_student_info()` + `parse_semesters_with_offset()` as JSON. The transform step reads this (never writes directly to `students`), so transform logic can be re-run later without re-uploading files.

| Column          | Type          | Constraints                                       | Description                                                         |
| --------------- | ------------- | ------------------------------------------------- | ------------------------------------------------------------------- |
| `id`            | `uuid`        | PK, default `gen_random_uuid()`                   |                                                                     |
| `import_job_id` | `uuid`        | NOT NULL, FK → `import_jobs.id` ON DELETE CASCADE |                                                                     |
| `student_id`    | `uuid`        | nullable, FK → `students.id`                      | Set once the transform step matches this sheet to a `students` row. |
| `sheet_name`    | `text`        | NOT NULL                                          | Excel sheet name.                                                   |
| `raw_data`      | `jsonb`       | NOT NULL                                          | `{"student": {...}, "semesters": [...]}` exactly as parsed.         |
| `parsed`        | `boolean`     | NOT NULL, default `false`                         | Whether the transform step has processed this row.                  |
| `parse_error`   | `text`        | nullable                                          | Error message if transform failed for this sheet.                   |
| `created_at`    | `timestamptz` | NOT NULL, default `now()`                         |                                                                     |

**Relationships**

- `import_jobs (1) ──► raw_students (N)`.
- `raw_students (1) ──► raw_courses (N)`.
- `students (1) ──► raw_students (0..N)` — optional back-link once matched.

---

## raw_courses

**Purpose**: **Parser staging** — one row per course line, a flat denormalized copy of each course dict (also nested inside `raw_students.raw_data`) for easy re-processing/debugging without parsing JSON arrays.

| Column            | Type          | Constraints                                        | Description                                                                                           |
| ----------------- | ------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `id`              | `uuid`        | PK, default `gen_random_uuid()`                    |                                                                                                       |
| `raw_student_id`  | `uuid`        | NOT NULL, FK → `raw_students.id` ON DELETE CASCADE |                                                                                                       |
| `semester_raw`    | `text`        | nullable                                           | `level_semester` text as it appeared in the sheet.                                                    |
| `course_raw_data` | `jsonb`       | NOT NULL                                           | One course dict: `seq`, `course_code`, `course_name`, `grade_letter_raw`, `hours`, `passed_raw`, etc. |
| `created_at`      | `timestamptz` | NOT NULL, default `now()`                          |                                                                                                       |

**Relationships**

- `raw_students (1) ──► raw_courses (N)`.

---

## students

**Purpose**: One row per student — identity, fixed department/curriculum (set permanently at enrollment), and cached cumulative statistics computed by the parser/transform step (GPA, hours, completion rate). `student_code` is the globally unique university ID.

| Column                  | Type           | Constraints                                                   | Description                                                                    |
| ----------------------- | -------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `id`                    | `uuid`         | PK, default `gen_random_uuid()`                               |                                                                                |
| `student_code`          | `text`         | NOT NULL, **UNIQUE**                                          | Globally unique university student ID — permanent until graduation.            |
| `name`                  | `text`         | NOT NULL                                                      |                                                                                |
| `department_id`         | `uuid`         | NOT NULL, FK → `departments.id`                               | Fixed at enrollment, never changes.                                            |
| `curriculum_id`         | `uuid`         | NOT NULL, FK → `curricula.id`                                 | Resolved from `(department_id, enrollment_year)` at enrollment, never changes. |
| `enrollment_year`       | `integer`      | NOT NULL, CHECK `≥ 2000`                                      | Year the student joined the college.                                           |
| `current_level`         | `integer`      | nullable, CHECK `(NULL or 1 ≤ x ≤ 4)`                         | Current study level.                                                           |
| `cumulative_gpa`        | `numeric(4,2)` | NOT NULL, default `0`, CHECK `0 ≤ x ≤ 4`                      |                                                                                |
| `cumulative_percentage` | `numeric(5,2)` | nullable, CHECK `(NULL or 0 ≤ x ≤ 100)`                       |                                                                                |
| `attempted_hours`       | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`                            |                                                                                |
| `completed_hours`       | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`, CHECK `≤ attempted_hours` |                                                                                |
| `completion_rate`       | `numeric(5,2)` | NOT NULL, default `0`, CHECK `0 ≤ x ≤ 100`                    | `completed_hours / attempted_hours * 100` (cached).                            |
| `total_passed_courses`  | `integer`      | NOT NULL, default `0`                                         |                                                                                |
| `total_failed_courses`  | `integer`      | NOT NULL, default `0`                                         |                                                                                |
| `is_active`             | `boolean`      | NOT NULL, default `true`                                      |                                                                                |
| `last_import_job_id`    | `uuid`         | nullable, FK → `import_jobs.id`                               | Traceability: which import last updated this row.                              |
| `created_at`            | `timestamptz`  | NOT NULL, default `now()`                                     |                                                                                |
| `updated_at`            | `timestamptz`  | NOT NULL, default `now()`, auto-updated via trigger           |                                                                                |

**Relationships**

- `departments (1) ──► students (N)`.
- `curricula (1) ──► students (N)`.
- `import_jobs (1) ──► students (N)` (via `last_import_job_id`, nullable).
- `students (1) ──► student_semesters (N)`.
- `students (1) ──► advisor_assignments (N)`, `students (1) ──► advisor_notes (N)`.
- `students (1) ──► academic_analyses (N)`, `students (1) ──► reports (N)`.
- `students (0..N) ◄── raw_students` — optional back-link.

---

## student_semesters

**Purpose**: One row per semester per student — academic year, level/term (parsed from the original Arabic text and kept as raw text for traceability), and per-semester GPA/hour statistics computed by the parser.

| Column               | Type           | Constraints                                                   | Description                                                      |
| -------------------- | -------------- | ------------------------------------------------------------- | ---------------------------------------------------------------- |
| `id`                 | `uuid`         | PK, default `gen_random_uuid()`                               |                                                                  |
| `student_id`         | `uuid`         | NOT NULL, FK → `students.id` ON DELETE CASCADE                |                                                                  |
| `semester_number`    | `integer`      | NOT NULL                                                      | Sequential order as it appears in the sheet.                     |
| `academic_year`      | `text`         | nullable                                                      | e.g. `"2024-2025"`.                                              |
| `level_semester_raw` | `text`         | nullable                                                      | Original Arabic text, e.g. "المستوى الثالث/الفصل الدراسى الأول". |
| `term`               | `term_enum`    | nullable                                                      | Parsed from `level_semester_raw`: `fall`, `spring`, `summer`.    |
| `level`              | `integer`      | nullable                                                      | Parsed numeric study level for this semester.                    |
| `gpa`                | `numeric(4,2)` | NOT NULL, default `0`, CHECK `0 ≤ x ≤ 4`                      | Semester GPA.                                                    |
| `attempted_hours`    | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`                            |                                                                  |
| `completed_hours`    | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`, CHECK `≤ attempted_hours` |                                                                  |
| `passed_courses`     | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`                            |                                                                  |
| `failed_courses`     | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`                            |                                                                  |
| `total_courses`      | `integer`      | NOT NULL, default `0`, CHECK `≥ 0`                            |                                                                  |
| `quality_points`     | `numeric(6,2)` | NOT NULL, default `0`                                         | Sum of `hours × grade_points` for the semester.                  |

**Constraints**: `UNIQUE (student_id, semester_number)`.

**Relationships**

- `students (1) ──► student_semesters (N)`.
- `student_semesters (1) ──► student_courses (N)`.

---

## student_courses

**Purpose**: One row per course attempt — the core transcript table. Holds both the letter grade and the raw numeric score from Excel, the matched curriculum course (if any), and retake tracking (`attempt_number` / `is_latest_attempt`, where **only the latest attempt counts toward cumulative GPA**, per `resolve_repeated_courses()`).

| Column                 | Type           | Constraints                                             | Description                                                                                               |
| ---------------------- | -------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `id`                   | `uuid`         | PK, default `gen_random_uuid()`                         |                                                                                                           |
| `student_id`           | `uuid`         | NOT NULL, FK → `students.id` ON DELETE CASCADE          |                                                                                                           |
| `semester_id`          | `uuid`         | NOT NULL, FK → `student_semesters.id` ON DELETE CASCADE |                                                                                                           |
| `curriculum_course_id` | `uuid`         | nullable, FK → `curriculum_courses.id`                  | Matched curriculum course (by `course_code`); `NULL` if unmatched (e.g. no-code community-issues course). |
| `course_code`          | `text`         | nullable                                                | As it appears on the transcript.                                                                          |
| `course_name`          | `text`         | NOT NULL                                                |                                                                                                           |
| `credit_hours`         | `integer`      | NOT NULL, CHECK `> 0`                                   |                                                                                                           |
| `grade_letter`         | `text`         | NOT NULL, FK → `grade_scale.grade_letter`               | Normalized uppercase letter grade.                                                                        |
| `grade_letter_raw`     | `text`         | nullable                                                | Original value as it appeared in the sheet.                                                               |
| `grade_points`         | `numeric(4,2)` | NOT NULL, CHECK `0 ≤ x ≤ 4`                             | GPA points for this attempt (from `grade_scale`).                                                         |
| `grade_score`          | `numeric(5,2)` | nullable, CHECK `(NULL or 0 ≤ x ≤ 100)`                 | Raw numeric grade from Excel (e.g. `95`, `87`), if present.                                               |
| `passed`               | `boolean`      | NOT NULL                                                | Authoritative pass/fail — from the Excel pass/fail column, **not** derived from `grade_points`.           |
| `passed_raw`           | `text`         | nullable                                                | Original pass/fail text from Excel.                                                                       |
| `attempt_number`       | `integer`      | NOT NULL, default `1`, CHECK `≥ 1`                      | `1` = first attempt, `2` = first retake, etc.                                                             |
| `is_latest_attempt`    | `boolean`      | NOT NULL, default `true`                                | `true` if this attempt counts toward cumulative GPA/hours.                                                |
| `updated_at`           | `timestamptz`  | NOT NULL, default `now()`, auto-updated via trigger     |                                                                                                           |

**Constraints**: `UNIQUE (semester_id, course_code, course_name)` — `course_name` is included so multiple no-code courses (distinct by name) within one semester don't collide.

**Relationships**

- `student_semesters (1) ──► student_courses (N)`.
- `students (1) ──► student_courses (N)` (denormalized for direct querying).
- `curriculum_courses (0..1) ──► student_courses (N)` — optional curriculum match.
- `grade_scale (1) ──► student_courses (N)`.

---

## advisor_assignments

**Purpose**: Tracks which advisor is the **primary** advisor for which student over time. Per the confirmed requirement that any advisor may be responsible for students in any department, this is a **dashboard "my students" filter**, not an access boundary — every staff member can still see every student.

| Column        | Type          | Constraints                                    | Description                                                |
| ------------- | ------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| `id`          | `uuid`        | PK, default `gen_random_uuid()`                |                                                            |
| `advisor_id`  | `uuid`        | NOT NULL, FK → `profiles.id`                   |                                                            |
| `student_id`  | `uuid`        | NOT NULL, FK → `students.id` ON DELETE CASCADE |                                                            |
| `assigned_at` | `timestamptz` | NOT NULL, default `now()`                      |                                                            |
| `is_active`   | `boolean`     | NOT NULL, default `true`                       | `true` = current advisor; `false` = historical assignment. |

**Constraints**: Partial unique index `idx_advisor_assignments_active` on `(student_id) WHERE is_active = true` — at most one _active_ advisor per student, but unlimited history.

**Relationships**

- `profiles (1) ──► advisor_assignments (N)`.
- `students (1) ──► advisor_assignments (N)` (full history).

---

## advisor_notes

**Purpose**: Free-text notes about a student, written by any staff member and **visible to all staff** (admin + every advisor) — confirmed shared visibility, not private.

| Column       | Type          | Constraints                                         | Description                                                      |
| ------------ | ------------- | --------------------------------------------------- | ---------------------------------------------------------------- |
| `id`         | `uuid`        | PK, default `gen_random_uuid()`                     |                                                                  |
| `student_id` | `uuid`        | NOT NULL, FK → `students.id` ON DELETE CASCADE      |                                                                  |
| `advisor_id` | `uuid`        | NOT NULL, FK → `profiles.id`                        | Author of the note (for attribution, e.g. "ملاحظة من: د. أحمد"). |
| `note`       | `text`        | NOT NULL                                            |                                                                  |
| `created_at` | `timestamptz` | NOT NULL, default `now()`                           |                                                                  |
| `updated_at` | `timestamptz` | NOT NULL, default `now()`, auto-updated via trigger |                                                                  |

**Relationships**

- `students (1) ──► advisor_notes (N)`.
- `profiles (1) ──► advisor_notes (N)` (author).

---

## academic_analyses

**Purpose**: One row per expert-system run for a student — the headline result (academic status, risk level, graduation eligibility) and timestamp. Individual findings live in `analysis_issues`. The `latest_academic_analyses` view (see `VIEWS_AND_FUNCTIONS.md`) resolves the most recent row per student.

| Column                | Type                   | Constraints                                    | Description                                               |
| --------------------- | ---------------------- | ---------------------------------------------- | --------------------------------------------------------- |
| `id`                  | `uuid`                 | PK, default `gen_random_uuid()`                |                                                           |
| `student_id`          | `uuid`                 | NOT NULL, FK → `students.id` ON DELETE CASCADE |                                                           |
| `academic_status`     | `academic_status_enum` | NOT NULL                                       | `good_standing`, `delayed`, `needs_support`, `probation`. |
| `risk_level`          | `risk_level_enum`      | NOT NULL                                       | `low`, `medium`, `high`.                                  |
| `graduation_eligible` | `boolean`              | NOT NULL                                       |                                                           |
| `analyzed_at`         | `timestamptz`          | NOT NULL, default `now()`                      |                                                           |

**Relationships**

- `students (1) ──► academic_analyses (N)` — full history of analysis runs.
- `academic_analyses (1) ──► analysis_issues (N)`.

---

## analysis_issues

**Purpose**: One row per individual finding from one analysis run (e.g. "low GPA", "unmet prerequisite", "elective hours incomplete"), each with its own severity, Arabic title/description, and explainable recommendation — implementing the "Explainable Recommendations" requirement and enabling reports like "all students with a prerequisite violation" as a plain filter.

| Column              | Type                  | Constraints                                             | Description                                                                                     |
| ------------------- | --------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `id`                | `uuid`                | PK, default `gen_random_uuid()`                         |                                                                                                 |
| `analysis_id`       | `uuid`                | NOT NULL, FK → `academic_analyses.id` ON DELETE CASCADE |                                                                                                 |
| `rule_code`         | `text`                | NOT NULL                                                | Machine-readable rule identifier (e.g. `LOW_GPA`, `PREREQ_VIOLATION`, `GRADUATION_DELAY_RISK`). |
| `severity`          | `issue_severity_enum` | NOT NULL                                                | `info`, `warning`, `error`.                                                                     |
| `title_ar`          | `text`                | NOT NULL                                                | Arabic title of the finding.                                                                    |
| `description_ar`    | `text`                | NOT NULL                                                | Arabic explanation ("why").                                                                     |
| `recommendation_ar` | `text`                | nullable                                                | Arabic recommended action.                                                                      |
| `resolved`          | `boolean`             | NOT NULL, default `false`                               | Whether an advisor has marked this issue as addressed.                                          |
| `created_at`        | `timestamptz`         | NOT NULL, default `now()`                               |                                                                                                 |

**Relationships**

- `academic_analyses (1) ──► analysis_issues (N)`.

---

## reports

**Purpose**: Snapshot of a generated report — student-scoped, department-scoped, or college-wide — so a report can be re-opened later without recomputation, and "Generated Date" is meaningful.

| Column          | Type          | Constraints                                    | Description                                                                                                                      |
| --------------- | ------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `id`            | `uuid`        | PK, default `gen_random_uuid()`                |                                                                                                                                  |
| `student_id`    | `uuid`        | nullable, FK → `students.id` ON DELETE CASCADE | Set for student-scoped reports.                                                                                                  |
| `department_id` | `uuid`        | nullable, FK → `departments.id`                | Set for department-scoped reports.                                                                                               |
| `report_type`   | `text`        | NOT NULL                                       | e.g. `student_profile`, `graduation_eligibility`, `risk_report`, `department_analytics`, `at_risk_students`, `college_overview`. |
| `generated_by`  | `uuid`        | NOT NULL, FK → `profiles.id`                   | Staff member who generated the report.                                                                                           |
| `data`          | `jsonb`       | NOT NULL                                       | Full rendered report payload (Arabic-first text, tables, etc.).                                                                  |
| `created_at`    | `timestamptz` | NOT NULL, default `now()`                      |                                                                                                                                  |

**Constraints**: `CHECK (student_id IS NOT NULL OR department_id IS NOT NULL OR report_type = 'college_overview')` — every report is scoped to a student, a department, or explicitly marked as a college-wide overview.

**Relationships**

- `students (0..1) ──► reports (N)`.
- `departments (0..1) ──► reports (N)`.
- `profiles (1) ──► reports (N)` (generator).

---

## department_statistics

**Purpose**: Periodic snapshot of department-level metrics for trend analytics (report #11 "Department Academic Analytics") and the management dashboard — computed by a scheduled job, not live on every page view. (The live equivalent for current counts is the `department_status_overview` view — see `VIEWS_AND_FUNCTIONS.md`.)

| Column                | Type           | Constraints                                       | Description                   |
| --------------------- | -------------- | ------------------------------------------------- | ----------------------------- |
| `id`                  | `uuid`         | PK, default `gen_random_uuid()`                   |                               |
| `department_id`       | `uuid`         | NOT NULL, FK → `departments.id` ON DELETE CASCADE |                               |
| `calculated_at`       | `timestamptz`  | NOT NULL, default `now()`                         | When this snapshot was taken. |
| `total_students`      | `integer`      | NOT NULL, CHECK `≥ 0`                             |                               |
| `average_gpa`         | `numeric(4,2)` | NOT NULL, CHECK `0 ≤ x ≤ 4`                       |                               |
| `graduation_rate`     | `numeric(5,2)` | NOT NULL, CHECK `0 ≤ x ≤ 100`                     |                               |
| `risk_students_count` | `integer`      | NOT NULL, CHECK `≥ 0`, CHECK `≤ total_students`   |                               |

**Relationships**

- `departments (1) ──► department_statistics (N)` — one row per snapshot date.
