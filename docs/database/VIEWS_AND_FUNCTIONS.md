# Acadexa — Views & Functions

Created by `009_views.sql` (3 views) and `010_functions.sql` (2 RPC functions). These exist to simplify recurring application queries and report rendering — **not** to hold expert-system logic (status diagnosis, risk prediction, and recommendations remain in the application layer).

---

## Views

### 1. `latest_academic_analyses`

**Purpose**: Resolves the most recent `academic_analyses` row per student. Every "all students with risk X / status Y" query and report joins through this view instead of dealing with full analysis history.

**Definition**

```sql
create view latest_academic_analyses as
select distinct on (student_id) *
from academic_analyses
order by student_id, analyzed_at desc;
```

**Inputs**: none (it's a view over `academic_analyses`).

**Outputs**: same columns as `academic_analyses` — `id`, `student_id`, `academic_status`, `risk_level`, `graduation_eligible`, `analyzed_at` — but exactly **one row per student** (the most recently analyzed).

**Usage**

```sql
-- All high-risk students
select s.student_code, s.name, laa.risk_level, laa.academic_status
from latest_academic_analyses laa
join students s on s.id = laa.student_id
where laa.risk_level = 'high';
```

Used internally by `student_academic_summary` (below) and by report #10 (At-Risk Students Report).

---

### 2. `student_academic_summary`

**Purpose**: One row per student combining identity, department/curriculum context, GPA/hours, graduation progress, and the latest expert-system status — the building block for report #1 (Student Academic Profile / Academic Summary).

**Definition** (key columns)

```sql
create view student_academic_summary as
select
  s.id                       as student_id,
  s.student_code,
  s.name                     as student_name,
  d.id                       as department_id,
  d.name_ar                  as department_name_ar,
  d.name_en                  as department_name_en,
  c.id                       as curriculum_id,
  c.name_ar                  as curriculum_name_ar,
  c.regulation_year,
  s.enrollment_year,
  s.current_level,
  s.cumulative_gpa,
  s.attempted_hours,
  s.completed_hours,
  c.total_required_hours,
  greatest(c.total_required_hours - s.completed_hours, 0) as remaining_hours,
  case
    when c.total_required_hours > 0
      then round((s.completed_hours::numeric / c.total_required_hours) * 100, 2)
    else 0
  end                        as graduation_progress_percent,
  s.completion_rate,
  s.is_active,
  laa.academic_status,
  laa.risk_level,
  laa.graduation_eligible,
  laa.analyzed_at            as last_analyzed_at
from students s
join departments d on d.id = s.department_id
join curricula c    on c.id = s.curriculum_id
left join latest_academic_analyses laa on laa.student_id = s.id;
```

**Inputs**: none (view); filter by `student_id` or `department_id` as needed.

**Outputs** (one row per student):

| Column                                                                     | Description                                                                                                                                                                                             |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `student_id`, `student_code`, `student_name`                               | Identity                                                                                                                                                                                                |
| `department_id`, `department_name_ar`, `department_name_en`                | Department context                                                                                                                                                                                      |
| `curriculum_id`, `curriculum_name_ar`, `regulation_year`                   | Applicable regulation                                                                                                                                                                                   |
| `enrollment_year`, `current_level`                                         |                                                                                                                                                                                                         |
| `cumulative_gpa`, `attempted_hours`, `completed_hours`, `completion_rate`  | Cached academic stats from `students`                                                                                                                                                                   |
| `total_required_hours`                                                     | From `curricula`                                                                                                                                                                                        |
| `remaining_hours`                                                          | `max(total_required_hours - completed_hours, 0)`                                                                                                                                                        |
| `graduation_progress_percent`                                              | `completed_hours / total_required_hours * 100`, rounded to 2 decimals — this is the "Progress: 56%" figure in report #1, distinct from `completion_rate` (which is `completed_hours / attempted_hours`) |
| `is_active`                                                                |                                                                                                                                                                                                         |
| `academic_status`, `risk_level`, `graduation_eligible`, `last_analyzed_at` | From `latest_academic_analyses` (nullable if no analysis has run yet)                                                                                                                                   |

**Usage**

```sql
-- Report #1 "Academic Summary" for one student
select * from student_academic_summary where student_id = '<uuid>';

-- All students in a department who haven't reached good standing
select * from student_academic_summary
where department_id = '<uuid>' and academic_status <> 'good_standing';
```

---

### 3. `department_status_overview`

**Purpose**: Live, per-department counts of students by `academic_status` and `risk_level`, plus average GPA — backs report #9 (Students Overview Report). Distinct from `department_statistics` (a table of periodic historical snapshots used for trend reporting in report #11) — this view always reflects the current state.

**Definition**

```sql
create view department_status_overview as
select
  d.id                                                      as department_id,
  d.name_ar                                                 as department_name_ar,
  d.name_en                                                 as department_name_en,
  count(s.id)                                               as total_students,
  count(*) filter (where laa.academic_status = 'good_standing')  as good_standing_count,
  count(*) filter (where laa.academic_status = 'delayed')        as delayed_count,
  count(*) filter (where laa.academic_status = 'needs_support')  as needs_support_count,
  count(*) filter (where laa.academic_status = 'probation')       as probation_count,
  count(*) filter (where laa.risk_level = 'high')                  as high_risk_count,
  round(avg(s.cumulative_gpa), 2)                                   as average_gpa
from departments d
left join students s on s.department_id = d.id and s.is_active = true
left join latest_academic_analyses laa on laa.student_id = s.id
group by d.id, d.name_ar, d.name_en;
```

**Inputs**: none (view); one row per department, including departments with zero active students (via the `left join`).

**Outputs**:

| Column                                                                           | Description                                                            |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `department_id`, `department_name_ar`, `department_name_en`                      |                                                                        |
| `total_students`                                                                 | Count of active students in the department                             |
| `good_standing_count`, `delayed_count`, `needs_support_count`, `probation_count` | Counts by latest `academic_status`                                     |
| `high_risk_count`                                                                | Count where latest `risk_level = 'high'`                               |
| `average_gpa`                                                                    | Average `cumulative_gpa` across active students, rounded to 2 decimals |

**Usage**

```sql
-- Report #9 "Students Overview" for the management dashboard
select * from department_status_overview order by department_name_ar;
```

---

## Functions (RPC)

Both functions are `language sql`, `stable`, `security invoker` — they run with the caller's own permissions (so RLS still applies to the underlying tables/views) and can be called via Supabase's `rpc()` client method.

### 1. `fn_student_completion_percentage(p_student_id uuid)`

**Purpose**: Graduation progress = `completed_hours / curricula.total_required_hours * 100`. This is the exact "Completed Credits: 84 / 150, Progress: 56%" figure from report #1, and is **distinct** from the cached `students.completion_rate` column (which is `completed_hours / attempted_hours`, a different ratio computed by the parser).

**Definition**

```sql
create or replace function public.fn_student_completion_percentage(p_student_id uuid)
returns numeric
language sql
stable
security invoker
as $$
  select case
    when c.total_required_hours > 0
      then round((s.completed_hours::numeric / c.total_required_hours) * 100, 2)
    else 0
  end
  from students s
  join curricula c on c.id = s.curriculum_id
  where s.id = p_student_id;
$$;
```

**Inputs**:

| Parameter      | Type   | Description                  |
| -------------- | ------ | ---------------------------- |
| `p_student_id` | `uuid` | The student's `students.id`. |

**Outputs**: `numeric` — graduation progress percentage (0–100), rounded to 2 decimals. Returns `0` if `total_required_hours` is `0` (defensive; should not occur given the `> 0` check constraint on `curricula`), or `NULL` if no student matches `p_student_id`.

**Usage**

```sql
select fn_student_completion_percentage('<student-uuid>');
-- => 56.00
```

```ts
// Supabase JS client
const { data, error } = await supabase.rpc("fn_student_completion_percentage", {
  p_student_id: studentId,
});
```

---

### 2. `fn_student_academic_summary(p_student_id uuid)`

**Purpose**: Single RPC returning the **full "Academic Summary" block** for one student as JSON — wraps `student_academic_summary` (above) plus the student's full semester-by-semester GPA/hours history — so the application can render report #1 with **one call** instead of separately querying the view and `student_semesters`.

**Definition**

```sql
create or replace function public.fn_student_academic_summary(p_student_id uuid)
returns jsonb
language sql
stable
security invoker
as $$
  select jsonb_build_object(
    'student',  to_jsonb(sas) - 'student_id',
    'semesters', coalesce(
      (
        select jsonb_agg(
          jsonb_build_object(
            'semester_number', ss.semester_number,
            'academic_year',   ss.academic_year,
            'term',            ss.term,
            'level',           ss.level,
            'gpa',             ss.gpa,
            'attempted_hours', ss.attempted_hours,
            'completed_hours', ss.completed_hours
          )
          order by ss.semester_number
        )
        from student_semesters ss
        where ss.student_id = p_student_id
      ),
      '[]'::jsonb
    )
  )
  from student_academic_summary sas
  where sas.student_id = p_student_id;
$$;
```

**Inputs**:

| Parameter      | Type   | Description                  |
| -------------- | ------ | ---------------------------- |
| `p_student_id` | `uuid` | The student's `students.id`. |

**Outputs**: `jsonb` object with two keys:

| Key         | Shape            | Description                                                                                                                                                                                                                                                                                                                 |
| ----------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `student`   | object           | All columns from `student_academic_summary` for this student, except `student_id` (already known by the caller) — includes `student_code`, `student_name`, department/curriculum context, GPA/hours, `remaining_hours`, `graduation_progress_percent`, and the latest `academic_status`/`risk_level`/`graduation_eligible`. |
| `semesters` | array of objects | One entry per `student_semesters` row, ordered by `semester_number`, each with `semester_number`, `academic_year`, `term`, `level`, `gpa`, `attempted_hours`, `completed_hours`. Empty array `[]` if the student has no semesters yet.                                                                                      |

Returns `NULL` if no student matches `p_student_id`.

**Usage**

```sql
select fn_student_academic_summary('<student-uuid>');
```

```json
{
  "student": {
    "student_code": "2021123456",
    "student_name": "...",
    "department_name_ar": "...",
    "curriculum_name_ar": "لائحة 2024 - ...",
    "regulation_year": 2024,
    "enrollment_year": 2021,
    "current_level": 4,
    "cumulative_gpa": 2.85,
    "attempted_hours": 96,
    "completed_hours": 84,
    "total_required_hours": 150,
    "remaining_hours": 66,
    "graduation_progress_percent": 56.0,
    "completion_rate": 87.5,
    "academic_status": "good_standing",
    "risk_level": "low",
    "graduation_eligible": false,
    "last_analyzed_at": "2026-06-10T12:00:00Z"
  },
  "semesters": [
    {
      "semester_number": 1,
      "academic_year": "2021-2022",
      "term": "fall",
      "level": 1,
      "gpa": 3.1,
      "attempted_hours": 15,
      "completed_hours": 15
    },
    {
      "semester_number": 2,
      "academic_year": "2021-2022",
      "term": "spring",
      "level": 1,
      "gpa": 2.9,
      "attempted_hours": 15,
      "completed_hours": 15
    }
  ]
}
```

```ts
// Supabase JS client
const { data, error } = await supabase.rpc("fn_student_academic_summary", {
  p_student_id: studentId,
});
// data.student.graduation_progress_percent, data.semesters[...]
```

This is the single call the "Student Academic Profile Report" UI/PDF renderer needs for the Academic Summary block and the Semester Performance table (report #7); the Expert System Analysis / Recommendations sections of the final report come from `analysis_issues` (see `DATABASE_WORKFLOW.md`, Flow D).
