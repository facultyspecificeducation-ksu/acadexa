# Acadexa — Table Relationships

Every foreign-key relationship in the schema, grouped by module, with cardinality and the reasoning behind it. Cardinality notation: **1:1**, **1:N**, **N:M** (implemented via a join table).

---

## 1. Authentication

### profiles 1:N user_roles

```
profiles
   1 ---- N
user_roles
```

A staff member can hold more than one role (e.g. an admin who also advises students). `user_roles` is the join row; deleting a `profiles` row cascades to its `user_roles` rows.

### roles 1:N user_roles

```
roles
   1 ---- N
user_roles
```

Each role (`admin`, `academic_advisor`) can be granted to many staff members.

### profiles N:M roles (via user_roles)

The combination of the two relationships above makes `profiles` and `roles` a many-to-many: a profile can have 0, 1, or 2 roles, and a role can be held by many profiles. This is the entire permission model — there is no separate permissions table.

---

## 2. Academic Structure → Curriculum Management

### departments 1:N curricula

```
departments
   1 ---- N
curricula
```

One department can have **multiple regulations over time** (e.g. 2019, 2024, 2026 for the same department). `UNIQUE (department_id, regulation_year)` ensures at most one curriculum per department per regulation year. This exists because the college's policy is "a student follows the regulation in force at the time of their enrollment for their department" — so the historical curricula must remain queryable, not just the latest one.

### curricula 1:N curriculum_courses

```
curricula
   1 ---- N
curriculum_courses
```

Each curriculum has its own course catalog (codes, hours, levels, categories). Course codes are fixed _per regulation_ — a course can exist in one curriculum and not another (or with different hours/level), so courses cannot be shared directly across curricula.

### curricula 1:1 graduation_requirements

```
curricula
   1 ---- 1
graduation_requirements
```

Every curriculum has exactly one graduation-requirements row (`curriculum_id UNIQUE`). Split from `curricula` itself to keep the "what does it take to graduate" data isolated and easy for the expert system to fetch in one query, without bloating the `curricula` row with rarely-changed configuration.

### curricula 1:1 academic_rules

```
curricula
   1 ---- 1
academic_rules
```

Every curriculum has exactly one academic-rules row (`curriculum_id UNIQUE`) — probation GPA, load limits, level thresholds. Kept separate from `curricula` for the same reason as `graduation_requirements`: this is the **knowledge base** the inference engine queries, and isolating it makes "update the probation threshold for curriculum X" a single-row update with no risk of touching identity/catalog data.

### curricula 1:N elective_groups

```
curricula
   1 ---- N
elective_groups
```

A curriculum can define multiple elective "buckets" (e.g. "University Electives — 4 hours / 1 course", "Major Electives — 6 hours / 2 courses"). Each bucket has its own hour/course-count requirement, so they're separate rows rather than columns on `curricula`.

### elective_groups N:M curriculum_courses (via elective_group_courses)

```
elective_groups
   1 ---- N
elective_group_courses
   N ---- 1
curriculum_courses
```

A course can belong to more than one elective group (rare but possible), and a group contains many courses — hence the join table `elective_group_courses` with composite PK `(group_id, course_id)`. This exists so the expert system can answer "did the student complete the required elective hours/courses?" by joining `student_courses` through this table, **without a separate student-elective-selection table** — the selection is whatever the student actually passed that happens to be in the group.

### curriculum_courses 1:N course_prerequisites (twice — as `course_id` and as `required_course_id`)

```
curriculum_courses (course_id)
   1 ---- N
course_prerequisites
   N ---- 1
curriculum_courses (required_course_id)
```

`course_prerequisites` is a self-referencing relationship on `curriculum_courses`: each row says "to take `course_id`, you must first complete `required_course_id`". Two separate 1:N relationships exist because a single course can be (a) the _subject_ of many prerequisite rules and (b) the _prerequisite for_ many other courses. This is the data the "Prerequisite Violation Report" and the "register prerequisite courses first" recommendation are built from.

### grade_scale 1:N course_prerequisites

```
grade_scale
   1 ---- N
course_prerequisites
```

`course_prerequisites.minimum_grade` is an optional FK to `grade_scale.grade_letter` — most prerequisites only require a _pass_, but this allows a specific course to require, say, at least a `C` in its prerequisite. Nullable because "pass is enough" is the default.

---

## 3. Excel Import Pipeline

### profiles 1:N import_jobs

```
profiles
   1 ---- N
import_jobs
```

Every import is attributed to the staff member who uploaded it (`uploaded_by`) — needed for accountability and for the RLS policy that lets an uploader manage their own in-progress jobs.

### departments 1:N import_jobs

```
departments
   1 ---- N
import_jobs
```

Each Excel workbook represents exactly **one department's students**. The uploader explicitly selects the department at upload time (rather than the system inferring it from sheet contents), so every `import_jobs` row is scoped to one department from the start — this is what lets the transform step assign `students.department_id` reliably.

### import_jobs 1:N imported_files

```
import_jobs
   1 ---- N
imported_files
```

Usually one file per job, but the model allows multiple files per job (and `hash` supports re-upload detection) without changing `import_jobs` itself.

### import_jobs 1:N raw_students

```
import_jobs
   1 ---- N
raw_students
```

Each sheet in the workbook (= one student) becomes one `raw_students` row, holding the **untouched** parser output as JSON. This exists so the original Excel data is never lost even if transform/business logic changes later — re-processing doesn't require re-uploading.

### raw_students 1:N raw_courses

```
raw_students
   1 ---- N
raw_courses
```

Each course line on a student's sheet becomes one `raw_courses` row — a flat, queryable copy of the same data that's also nested inside `raw_students.raw_data`, useful for debugging/inspection without parsing JSON arrays.

### import_jobs 1:N students (via `students.last_import_job_id`)

```
import_jobs
   1 ---- N
students
```

Nullable FK recording which import job **most recently** touched a student record — pure traceability/audit, not an ownership relationship (a student isn't "owned" by one import; their record can be updated by many imports over time, but only the latest is tracked).

### students 0..N raw_students (via `raw_students.student_id`)

```
students
   1 ---- 0..N
raw_students
```

Nullable back-link set once the transform step matches a parsed sheet to a `students` row — lets you trace "which raw uploads contributed to this student's current record" without raw_students needing to be unique per student (a student can appear in multiple workbook uploads over their enrollment, e.g. one per academic year if re-exported).

---

## 4. Student Records

### departments 1:N students

```
departments
   1 ---- N
students
```

Every student belongs to exactly one department — fixed at enrollment and never changed (confirmed business rule: students never change department).

### curricula 1:N students

```
curricula
   1 ---- N
students
```

Every student is permanently bound to the curriculum (regulation) that was in force for their department at their enrollment year — resolved once via `(department_id, enrollment_year)` and never changed afterward, even if newer regulations are added later.

### students 1:N student_semesters

```
students
   1 ---- N
student_semesters
```

One row per semester the student has a transcript entry for. `UNIQUE (student_id, semester_number)` keeps semesters ordered and addressable.

### student_semesters 1:N student_courses

```
student_semesters
   1 ---- N
student_courses
```

One row per course attempted in that semester. This is the finest grain of the transcript — GPA, hours, and pass/fail are all rolled up from here to `student_semesters` and then to `students`.

### students 1:N student_courses

```
students
   1 ---- N
student_courses
```

Denormalized direct link (in addition to the path through `student_semesters`) so per-student course queries (e.g. "all of this student's attempts of MATH101 across semesters" for retake detection) don't require joining through every semester.

### curriculum_courses 0..1:N student_courses

```
curriculum_courses
   1 ---- N
student_courses
```

Optional match (`curriculum_course_id` nullable) linking a transcript line to its definition in the student's curriculum — by `course_code`. Nullable because some transcript lines (notably the no-code community-issues course, or transfer credits) may not match any `curriculum_courses` row by code; the expert system falls back to name-matching for those (per `is_community_issues_course`).

### grade_scale 1:N student_courses

```
grade_scale
   1 ---- N
student_courses
```

Every transcript line's `grade_letter` must exist in the global grading scale — this is what converts the letter into `grade_points` and determines whether it `affects_gpa`.

---

## 5. Advisory

### profiles 1:N advisor_assignments

```
profiles
   1 ---- N
advisor_assignments
```

An advisor (profile with `academic_advisor` role) can be assigned to many students over time.

### students 1:N advisor_assignments

```
students
   1 ---- N
advisor_assignments
```

A student can have a history of advisor assignments (reassignments over the years); a **partial unique index** ensures at most one row `is_active = true` per student at a time — i.e. exactly one _current_ advisor, with full history preserved. Because any advisor can be responsible for students in any department, this relationship is used as a **"my students" dashboard filter**, not as an access-control boundary (all staff can see all students regardless of assignment).

### students 1:N advisor_notes

```
students
   1 ---- N
advisor_notes
```

Free-text notes accumulate over time for a student; all are kept (no overwrite).

### profiles 1:N advisor_notes

```
profiles
   1 ---- N
advisor_notes
```

Each note is attributed to its author (`advisor_id`) for display ("ملاحظة من: ...") and for the RLS rule that lets an author edit/delete their own notes. Notes themselves remain readable by **all** staff regardless of author.

---

## 6. Expert System

### students 1:N academic_analyses

```
students
   1 ---- N
academic_analyses
```

Every time the inference engine runs for a student, a new `academic_analyses` row is added — preserving history (e.g. "GPA decreased from 2.7 to 1.9" requires comparing two analysis runs). The `latest_academic_analyses` view picks the most recent one per student.

### academic_analyses 1:N analysis_issues

```
academic_analyses
   1 ---- N
analysis_issues
```

One analysis run can surface multiple distinct findings (low GPA _and_ a prerequisite violation _and_ elective-hours shortfall, etc.), each independently severity-tagged, explainable, and markable as `resolved`. Splitting issues into their own rows (rather than a JSON array) is what makes "all students with rule X" a plain `WHERE rule_code = ...` filter across the whole college.

---

## 7. Reports & Department Statistics

### students 0..1:N reports

```
students
   1 ---- N
reports
```

A student can have many generated reports over time (profile report, risk report, graduation eligibility, etc.), each a frozen snapshot. `student_id` is nullable because a report can instead be department-scoped or college-wide.

### departments 0..1:N reports

```
departments
   1 ---- N
reports
```

Department-level reports (Students Overview, Department Analytics) are scoped here instead of to a student. The `CHECK` constraint on `reports` guarantees every row has at least a `student_id`, a `department_id`, or is explicitly `report_type = 'college_overview'`.

### profiles 1:N reports

```
profiles
   1 ---- N
reports
```

Every report records who generated it (`generated_by`) — for the RLS rule allowing the generator (or admin) to update/delete their own saved reports, and for display ("Generated by / Generated Date").

### departments 1:N department_statistics

```
departments
   1 ---- N
department_statistics
```

Periodic snapshots (one row per `calculated_at` run) for trend reporting (report #11), distinct from the live `department_status_overview` view which always reflects current data.

---

## 8. Relationship Summary Table

| From               | Cardinality | To                                              | Reason (one line)                                |
| ------------------ | ----------- | ----------------------------------------------- | ------------------------------------------------ |
| profiles           | 1:N         | user_roles                                      | a staff member can hold multiple roles           |
| roles              | 1:N         | user_roles                                      | a role can be granted to multiple staff          |
| departments        | 1:N         | curricula                                       | multiple regulations per department over time    |
| curricula          | 1:N         | curriculum_courses                              | each regulation has its own course catalog       |
| curricula          | 1:1         | graduation_requirements                         | one graduation policy per regulation             |
| curricula          | 1:1         | academic_rules                                  | one set of dynamic thresholds per regulation     |
| curricula          | 1:N         | elective_groups                                 | multiple elective "buckets" per regulation       |
| elective_groups    | N:M         | curriculum_courses (via elective_group_courses) | a course can belong to multiple elective buckets |
| curriculum_courses | 1:N (×2)    | course_prerequisites                            | self-referencing prerequisite graph              |
| grade_scale        | 1:N         | course_prerequisites                            | optional minimum-grade requirement               |
| profiles           | 1:N         | import_jobs                                     | accountability for uploads                       |
| departments        | 1:N         | import_jobs                                     | one workbook = one department                    |
| import_jobs        | 1:N         | imported_files                                  | physical files behind a job                      |
| import_jobs        | 1:N         | raw_students                                    | one row per parsed sheet                         |
| raw_students       | 1:N         | raw_courses                                     | one row per parsed course line                   |
| import_jobs        | 1:N         | students                                        | traceability of last import                      |
| students           | 1:0..N      | raw_students                                    | trace which uploads built this record            |
| departments        | 1:N         | students                                        | fixed department per student                     |
| curricula          | 1:N         | students                                        | fixed regulation per student                     |
| students           | 1:N         | student_semesters                               | one row per semester                             |
| student_semesters  | 1:N         | student_courses                                 | one row per course attempt                       |
| students           | 1:N         | student_courses                                 | direct/denormalized access                       |
| curriculum_courses | 0..1:N      | student_courses                                 | optional curriculum match                        |
| grade_scale        | 1:N         | student_courses                                 | every grade maps to GPA points                   |
| profiles           | 1:N         | advisor_assignments                             | advisor caseload history                         |
| students           | 1:N         | advisor_assignments                             | advisor history per student (1 active at a time) |
| students           | 1:N         | advisor_notes                                   | accumulating notes                               |
| profiles           | 1:N         | advisor_notes                                   | note authorship                                  |
| students           | 1:N         | academic_analyses                               | history of analysis runs                         |
| academic_analyses  | 1:N         | analysis_issues                                 | multiple findings per run                        |
| students           | 0..1:N      | reports                                         | student-scoped reports                           |
| departments        | 0..1:N      | reports                                         | department-scoped reports                        |
| profiles           | 1:N         | reports                                         | report authorship                                |
| departments        | 1:N         | department_statistics                           | periodic snapshots                               |
