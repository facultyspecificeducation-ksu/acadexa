# Acadexa — Seed Data & Initial Setup

`008_seed.sql` inserts **static reference data only** — two roles and the global grading scale. No departments, curricula, students, or academic records are seeded (those require real institutional data entry, documented at the end of this file). All inserts use `ON CONFLICT DO NOTHING`, so this migration is safe to re-run.

---

## 1. `roles` seed

| `code`             | `name_ar`    | `name_en`        | `description`                      |
| ------------------ | ------------ | ---------------- | ---------------------------------- |
| `admin`            | مدير النظام  | Admin            | Full system access                 |
| `academic_advisor` | مرشد أكاديمي | Academic Advisor | Manages students, imports, reports |

These are the **only two roles** in the system (confirmed requirement — students never authenticate). All RLS policies in `006_rls.sql` are written in terms of these two role codes via `is_admin()` / `is_advisor()` / `is_staff()`.

```sql
insert into roles (code, name_ar, name_en, description) values
  ('admin',            'مدير النظام',    'Admin',            'Full system access'),
  ('academic_advisor', 'مرشد أكاديمي',   'Academic Advisor', 'Manages students, imports, reports')
on conflict (code) do nothing;
```

---

## 2. `grade_scale` seed

The single global grading scale used by every curriculum (confirmed: not per-plan). 11 regular letter grades + 8 special symbols = **19 rows**.

### Regular letter grades (A–F)

| `grade_letter` | `name_ar` | `points` | `min_score`–`max_score` | `affects_gpa` | `is_passing` |
| -------------- | --------- | -------- | ----------------------- | ------------- | ------------ |
| A              | ممتاز     | 4.00     | 90–100                  | true          | true         |
| A-             | ممتاز-    | 3.70     | 85–89                   | true          | true         |
| B+             | جيد جداً+ | 3.40     | 82–84                   | true          | true         |
| B              | جيد جداً  | 3.20     | 78–81                   | true          | true         |
| B-             | جيد جداً- | 3.00     | 75–77                   | true          | true         |
| C+             | جيد+      | 2.80     | 72–74                   | true          | true         |
| C              | جيد       | 2.60     | 68–71                   | true          | true         |
| C-             | جيد-      | 2.40     | 65–67                   | true          | true         |
| D+             | مقبول+    | 2.20     | 62–64                   | true          | true         |
| D              | مقبول     | 2.00     | 60–61                   | true          | true         |
| F              | راسب      | 0.00     | 0–59                    | true          | **false**    |

### Special symbols (do not affect GPA)

| `grade_letter` | `name_ar`                   | `affects_gpa` | `is_passing` | `description`                                 |
| -------------- | --------------------------- | ------------- | ------------ | --------------------------------------------- |
| W              | الانسحاب                    | false         | false        | يرصد للطالب المسحب من المقرر                  |
| AU             | مستمع                       | false         | true         | يرصد للطالب المسجل مستمع                      |
| S              | مرضي                        | false         | true         | نتيجة مقرر تم اجتيازه بدون تقدير              |
| MW             | منسحب لأداء الخدمة العسكرية | false         | false        | يرصد للطالب المسحب لأداء الخدمة العسكرية      |
| FW             | الانسحاب الإجباري           | false         | false        | يرصد للطالب المسحب إجباريًا من المقرر (حرمان) |
| EX             | معفي                        | false         | true         | مقرر أعفي الطالب من دراسته                    |
| IC             | غير مكتمل                   | false         | false        | يرصد للطالب الذي لم يكمل متطلبات المقرر       |
| TC             | مقرر منقول                  | false         | true         | مقرر تم دراسته من خلال الجامعة                |

> **Note**: `is_passing` for `S`, `MW`, `AU`, `EX`, `IC`, `TC`, `W`, `FW` was set based on a reasonable interpretation (withdrawal/incomplete = not passing; audited/satisfactory/exempted/transferred = requirement satisfied). If the college's policy differs for any of these eight symbols, it is a one-row `UPDATE` — no structural change needed.

```sql
insert into grade_scale (grade_letter, name_ar, points, min_score, max_score, affects_gpa, is_passing) values
  ('A',  'ممتاز',     4.00, 90, 100, true,  true),
  ('A-', 'ممتاز-',    3.70, 85, 89,  true,  true),
  ('B+', 'جيد جداً+', 3.40, 82, 84,  true,  true),
  ('B',  'جيد جداً',  3.20, 78, 81,  true,  true),
  ('B-', 'جيد جداً-', 3.00, 75, 77,  true,  true),
  ('C+', 'جيد+',      2.80, 72, 74,  true,  true),
  ('C',  'جيد',       2.60, 68, 71,  true,  true),
  ('C-', 'جيد-',      2.40, 65, 67,  true,  true),
  ('D+', 'مقبول+',    2.20, 62, 64,  true,  true),
  ('D',  'مقبول',     2.00, 60, 61,  true,  true),
  ('F',  'راسب',      0.00, 0,  59,  true,  false)
on conflict (grade_letter) do nothing;

insert into grade_scale (grade_letter, name_ar, points, affects_gpa, is_passing, description) values
  ('W',  'الانسحاب',                    0.00, false, false, 'يرصد للطالب المسحب من المقرر'),
  ('AU', 'مستمع',                       0.00, false, true,  'يرصد للطالب المسجل مستمع'),
  ('S',  'مرضي',                        0.00, false, true,  'نتيجة مقرر تم اجتيازه بدون تقدير'),
  ('MW', 'منسحب لأداء الخدمة العسكرية', 0.00, false, false, 'يرصد للطالب المسحب لأداء الخدمة العسكرية'),
  ('FW', 'الانسحاب الإجباري',           0.00, false, false, 'يرصد للطالب المسحب إجباريًا من المقرر (حرمان)'),
  ('EX', 'معفي',                        0.00, false, true,  'مقرر أعفي الطالب من دراسته'),
  ('IC', 'غير مكتمل',                    0.00, false, false, 'يرصد للطالب الذي لم يكمل متطلبات المقرر'),
  ('TC', 'مقرر منقول',                   0.00, false, true,  'مقرر تم دراسته من خلال الجامعة')
on conflict (grade_letter) do nothing;
```

Verify after running:

```sql
select count(*) from roles;        -- expect 2
select count(*) from grade_scale;  -- expect 19
```

---

## 3. First Admin Setup Process

After all 10 migrations have run, the database has tables, RLS, storage buckets, and the two seeds above — but **no profiles and no role grants yet**, because `profiles` rows are only created reactively when someone signs up through Supabase Auth.

### Step 1 — Sign up the first real user

Through the application's normal sign-up flow (Supabase Auth), create an account for the person who will be the first administrator. This fires `trg_auth_user_created` (from `005_triggers.sql`), which runs `handle_new_user()` and inserts a matching row into `public.profiles` automatically (`full_name` from signup metadata or email, `email` copied from `auth.users`).

At this point the user **exists but has no role** — `is_admin()`, `is_advisor()`, and `is_staff()` all return `false` for them, so RLS blocks almost everything.

### Step 2 — Grant the `admin` role (run once, as a superuser / via SQL editor)

```sql
insert into user_roles (user_id, role_id)
select p.id, r.id
from profiles p, roles r
where p.email = 'first-admin@example.com'   -- the email used at signup
  and r.code = 'admin';
```

This must be run with elevated privileges (Supabase SQL editor, which runs as `postgres`/superuser and bypasses RLS) — a regular authenticated user cannot grant themselves a role (`user_roles` write access is `is_admin()`-only, and at this point no admin exists yet).

### Step 3 — Admin populates the knowledge base

Once logged in as the first admin, this person can now (via the app or SQL editor):

1. Insert the **10 `departments`** rows.
2. Insert **`curricula`** rows — one per `(department, regulation_year)` per the regulations document (2019 ×5, 2021 ×1, 2023 ×1, 2024 ×5, 2026 ×10 = 22 rows), each with `total_required_hours` and `min_gpa_to_graduate`.
3. Insert **`curriculum_courses`**, **`course_prerequisites`**, **`elective_groups`** / **`elective_group_courses`** for each curriculum.
4. Insert one **`graduation_requirements`** row and one **`academic_rules`** row per curriculum.

### Step 4 — Onboard advisors

For every additional staff member: they sign up (creates their `profiles` row automatically), then the admin grants them `academic_advisor` (or `admin`) the same way as Step 2:

```sql
insert into user_roles (user_id, role_id)
select p.id, r.id
from profiles p, roles r
where p.email = 'advisor@example.com'
  and r.code = 'academic_advisor';
```

A person can hold both roles — simply run the insert twice with `r.code` set to `'admin'` and `'academic_advisor'`.

### Step 5 — First import

With at least one department + curriculum (+ its `academic_rules`/`graduation_requirements`) in place, an admin or advisor can perform a test Excel import (see `DATABASE_WORKFLOW.md`, Flow A) to validate the pipeline end-to-end before onboarding the rest of the college's data.

---

## 4. What is intentionally NOT seeded

| Data                                                                                                  | Why it's not seeded                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `departments` (10 rows)                                                                               | Real institutional data — codes/names must come from the college's official department list.                                                              |
| `curricula`, `curriculum_courses`, `course_prerequisites`, `elective_groups`/`elective_group_courses` | Each regulation's actual course catalog — requires transcription from the official لائحة documents.                                                       |
| `graduation_requirements`, `academic_rules`                                                           | The actual numeric thresholds per curriculum (required hours, min GPA, load limits, level thresholds) — must be confirmed against each regulation's text. |
| `students`, `student_semesters`, `student_courses`                                                    | Real student data — populated only via the Excel import pipeline, never via seed scripts.                                                                 |
| `profiles`, `user_roles`                                                                              | Created reactively via Supabase Auth signup + admin role grants (Steps 1–4 above), never via seed scripts.                                                |
