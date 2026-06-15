# ACADEXA — Intelligent Academic Advising Desktop Application

![Acadexa Logo](docs/images/Acadexa_Logo.png)

## 🎯 Smart Academic Advisor Powered by AI

![Acadexa Banner](https://img.shields.io/badge/Acadexa-Intelligent%20Academic%20Advising-blue?style=for-the-badge)

![Electron badge](https://img.shields.io/badge/Electron-2B2E3A?style=for-the-badge&logo=electron&logoColor=white)
![React badge](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript badge](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![FastAPI badge](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MUI badge](https://img.shields.io/badge/MUI-007FFF?style=for-the-badge&logo=mui&logoColor=white)
![Supabase badge](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![PostgreSQL badge](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

---

## 📚 Table of Contents

1. [Project Overview](#-project-overview)
2. [Current Tech Stack](#-current-tech-stack)
3. [System Architecture](#-system-architecture)
4. [Database Documentation](#-database-documentation)
5. [Current Features](#-current-features)
6. [Project Structure](#-project-structure)
7. [Setup & Installation](#-setup--installation)
8. [Development Workflow](#-development-workflow)
9. [Testing](#-testing)
10. [Deployment](#-deployment)
11. [Future Improvements](#-future-improvements)

---

## 📌 Project Overview

**ACADEXA** is an intelligent academic advising desktop application designed to help universities move beyond simple data storage. It combines traditional academic management (students, courses, transcripts) with an **Expert System** engine that mimics human expert reasoning.

> 🎯 **Core Philosophy:** Instead of just answering "What is the student's GPA?", ACADEXA answers **"Why is the student at risk?"** and **"What should they do next?"**

ACADEXA is a **multi-process monorepo product** with three decoupled runtimes:

1.  **Electron Desktop Shell** — OS-level concerns (windows, file system, printing, notifications)
2.  **React Renderer (Acadexa Web UI)** — Application UI built with Vite, MUI (RTL), Zustand, React Router, React Hook Form + Zod
3.  **FastAPI Backend** — Database access, Expert System, AI layer, data ingestion, reporting

### ✨ Key Differentiators

| Feature                 | Traditional SIS | ACADEXA                |
| :---------------------- | :-------------- | :--------------------- |
| Data Storage            | ✅ Yes          | ✅ Yes                 |
| GPA Calculation         | ✅ Yes          | ✅ Yes                 |
| Prerequisite Checking   | ❌ Manual       | ✅ **Automatic**       |
| Academic Risk Detection | ❌ No           | ✅ **Expert System**   |
| Graduation Eligibility  | ❌ Manual Audit | ✅ **Instant Check**   |
| Explainable AI          | ❌ No           | ✅ **Evidence-Based**  |
| Offline Desktop         | ❌ No           | ✅ **Electron Native** |
| Arabic RTL Support      | ❌ Rare         | ✅ **Full Support**    |

---

## 🛠️ Current Tech Stack

| Layer              | Technology               | Purpose                                            |
| :----------------- | :----------------------- | :------------------------------------------------- |
| Desktop Framework  | Electron                 | Cross-platform desktop app (Windows, macOS, Linux) |
| Frontend Framework | React 18 + Vite          | Fast UI development with HMR                       |
| UI Library         | Material-UI (MUI) v5     | Professional components with RTL support           |
| State Management   | Zustand                  | Lightweight, scalable state                        |
| Type Safety        | TypeScript + Zod         | Full-stack type safety                             |
| Backend Framework  | FastAPI (Python 3.11+)   | High-performance async REST API                    |
| Database ORM       | SQLAlchemy 2.0           | Database operations                                |
| Database           | PostgreSQL + Supabase    | Primary relational data store + Auth               |
| Authentication     | Supabase Auth / JWT      | Role-based access control                          |
| Expert System      | Custom Rule Engine       | Forward-chaining inference                         |
| AI Integration     | OpenAI/Anthropic API     | Natural language explanations (read-only)          |
| File Processing    | Pandas + OpenPyXL        | Excel transcript parsing                           |
| Package Manager    | pnpm workspaces + Poetry | Monorepo management                                |

---

## 🏗️ System Architecture

The system is built on a **multi-process monorepo** with three decoupled runtimes:

```mermaid
graph TD
   A[💻 Electron Desktop Shell] -->|IPC Bridge| B[⚛️ React Renderer]
   B -->|HTTP/REST| C[⚙️ FastAPI Backend]
   C --> D{🔐 Auth & RBAC}
   D --> E[🧠 Expert System Engine]
   D --> F[📊 Service Layer]
   E --> G[🗃️ PostgreSQL + Supabase]
   F --> G
   E --> H[🤖 AI Assistant Layer]
   H -.->|Read Only| E
```

### Component Breakdown

| Layer         | Technology                     | Responsibility                                           |
| :------------ | :----------------------------- | :------------------------------------------------------- |
| Desktop Shell | Electron                       | Native OS features (filesystem, printing, notifications) |
| UI Renderer   | React + Vite + MUI + RTL       | All business UI, state management (Zustand), routing     |
| API Gateway   | FastAPI (Python)               | Request validation, routing, RBAC enforcement            |
| Expert System | Custom Forward-Chaining Engine | Rule evaluation, inference, issue generation             |
| AI Assistant  | LLM (OpenAI/Anthropic)         | Explanation rephrasing, report summaries (read-only)     |
| Data Layer    | SQLAlchemy + Supabase/Postgres | ORM, migrations, data persistence                        |

### Why a Monorepo?

Electron, React, and shared TypeScript types must evolve together. A monorepo with workspaces (pnpm workspaces + Turborepo) lets `shared-types` be imported by both `desktop` and `web` without publishing packages, while the Python `api` lives alongside as an independent workspace with its own dependency tree (Poetry).

---

## 📁 Project Structure

```text
acadexa/
├── apps/
│   ├── desktop/                 # Electron shell (main + preload)
│   ├── web/                     # React renderer (Vite + MUI)
│   └── api/                     # FastAPI backend
├── packages/
│   ├── shared-types/            # Shared TS contracts (DTOs, enums)
│   ├── shared-config/           # ESLint/Prettier/TS configs
│   └── ui-kit/                  # Shared MUI components/theme
├── docs/                        # ADRs, architecture diagrams, API docs
│   └── database/                # Database documentation (10+ files)
├── scripts/                     # Cross-cutting dev/build/release scripts
├── .github/workflows/           # CI/CD pipelines
├── docker-compose.yml           # Local Supabase/Postgres + API
├── turbo.json                   # Monorepo task runner config
└── package.json                 # Workspace root
```

### 💻 Desktop Architecture (`apps/desktop/`)

```text
apps/desktop/
├── src/
│   ├── main/
│   │   ├── index.ts                   # App entry, window lifecycle
│   │   ├── windows/                   # BrowserWindow factory + manager
│   │   ├── ipc/
│   │   │   ├── handlers/              # file-handler, print-handler, notification-handler
│   │   │   └── ipc-registry.ts        # Central IPC registration
│   │   ├── services/                  # api-config, update, tray
│   │   ├── menu/                      # Native menu
│   │   └── security/                  # CSP headers
│   ├── preload/
│   │   ├── index.ts                   # contextBridge exposeInMainWorld
│   │   └── api/                       # fileApi, printApi, notificationApi, updateApi
│   └── shared/
│       ├── ipc-channels.ts            # Enum of all IPC channel names
│       └── types.ts                   # Shared types
├── resources/                         # Icons, tray icons
├── build/                             # electron-builder.yml, entitlements
└── electron.vite.config.ts
```

### ⚛️ Frontend Architecture (`apps/web/src/`)

```text
apps/web/src/
├── main.tsx
├── app/
│   ├── App.tsx
│   ├── AppRouter.tsx
│   ├── layouts/                       # AuthLayout, DashboardLayout, PrintLayout
│   └── providers/                     # AuthProvider, QueryProvider, ThemeProvider
├── pages/                             # Thin route entry points (16 pages)
│   ├── auth/LoginPage.tsx
│   ├── dashboard/DashboardPage.tsx
│   ├── students/StudentsListPage.tsx
│   ├── students/StudentProfilePage.tsx
│   ├── import/ImportPage.tsx
│   ├── academic-structure/            # Departments, Curricula, Courses, Rules
│   ├── expert-system/                 # InferenceRules, GradeScale
│   ├── reports/                       # StudentReports, DepartmentAnalytics
│   ├── notifications/NotificationsPage.tsx
│   └── settings/                      # UsersRoles, AdvisorAssignments, SystemSettings
├── features/                          # 17 vertical slice features
│   ├── auth/                          # Login, session management
│   ├── dashboard/                     # KPI cards, charts, risk panel
│   ├── students/                      # Student list, profile with 8 tabs
│   ├── data-import/                   # Excel upload wizard, history
│   ├── departments/                   # Department CRUD
│   ├── curricula/                     # Curriculum management with tabs
│   ├── courses/                       # Course search, prerequisites
│   ├── academic-load-rules/           # Academic rules table
│   ├── expert-system/                 # Rule analytics (not builder)
│   ├── grade-scale/                   # Grade scale management
│   ├── reports/                       # Student & department reports
│   ├── notifications/                 # Notification center
│   ├── advisor-assignments/           # Advisor-student assignments
│   ├── admin/                         # User management
│   ├── settings/                      # System settings
│   ├── ai-assistant/                  # Chat assistant
│   └── recommendations/               # Explainable recommendations
├── shared/
│   ├── components/                    # DataTable, ConfirmDialog, StatusBadge, etc.
│   ├── guards/RoleGuard.tsx
│   ├── hooks/                         # useDebounce, usePagination, useTableState
│   ├── lib/                           # apiClient, electronBridge
│   └── utils/                         # formatters, academicStatus, gpa, date
├── routes/routes.config.ts
├── store/root.store.ts
├── theme/                             # theme.ts, rtl.ts, palette.ts
└── i18n/                              # ar.json, en.json
```

### ⚙️ Backend Architecture (`apps/api/app/`)

```text
apps/api/app/
├── main.py                            # FastAPI app factory
├── core/
│   ├── config.py                      # Pydantic Settings
│   ├── security.py                    # JWT/session tokens
│   ├── dependencies.py                # get_current_user, RBAC dependencies
│   └── exceptions.py                  # Custom exception handlers
├── db/
│   ├── base.py                        # Declarative base
│   ├── session.py                     # SQLAlchemy session
│   └── seed/seed_data.py              # Initial roles, sample rules
├── models/                            # SQLAlchemy ORM models (12 files)
│   ├── user.py, student.py, course.py, grade.py
│   ├── rule.py, recommendation.py, notification.py
│   └── academic_structure.py
├── schemas/                           # Pydantic DTOs (8 files)
├── api/v1/
│   ├── router.py
│   └── endpoints/                     # 13 endpoint modules
├── services/                          # Business logic layer (8 services)
├── repositories/                      # Data access layer (4 repositories)
├── expert_system/                     # ⭐ Core Expert System engine
│   ├── engine.py, runner.py
│   ├── knowledge_base/                # loader, rule_models, validator
│   ├── facts/                         # fact_builder, fact_schema
│   ├── operators/                     # operator_registry
│   ├── evaluation/                    # condition_evaluator, rule_matcher, conflict_resolver
│   ├── actions/                       # action_executor
│   ├── explanation/                   # explanation_builder
│   └── categories/                    # gpa_rules, warning_rules, graduation_rules, etc.
├── ai/                                # AI assistant layer (read-only)
│   ├── client.py
│   ├── prompts/                       # explanation, summary, chat
│   ├── services/                      # explanation_service, summary_service, chat_service
│   ├── context/context_builder.py
│   └── guardrails/scope_guard.py
├── data_processing/                   # Excel ingestion pipeline
│   ├── parsers/excel_parser.py
│   ├── mappers/                       # student, course, grade mappers
│   ├── validators/import_validator.py
│   ├── importer/import_service.py
│   └── jobs/import_job_tracker.py
└── tasks/background_jobs.py
```

---

## 🗄️ Database Documentation

### Database Design Philosophy

The database follows a **curriculum-based design** where each student is associated with a specific curriculum (department + regulation year). The schema is organized around these core principles:

1.  **Separation of staging and production data** — `raw_students`/`raw_courses` for Excel import staging
2.  **Auditability** — Import jobs track provenance of every record
3.  **Explainability** — Analysis issues store rule_code, severity, and recommendations
4.  **RLS by default** — Row Level Security enforced on all tables

### Main Tables and Purposes

#### Core Academic Structure

| Table                     | Purpose                                                            |
| :------------------------ | :----------------------------------------------------------------- |
| `departments`             | Academic departments (e.g., Computer Science, Information Systems) |
| `curricula`               | Program versions per department + regulation year                  |
| `curriculum_courses`      | Courses belonging to a curriculum (with level, term, category)     |
| `course_prerequisites`    | Prerequisite relationships between courses                         |
| `elective_groups`         | Elective groupings with required hours/min courses                 |
| `elective_group_courses`  | Many-to-many mapping of electives to groups                        |
| `graduation_requirements` | Graduation rules per curriculum                                    |
| `academic_rules`          | Probation GPA, min/max hours per term, level progression           |

#### Student Records

| Table                 | Purpose                                        |
| :-------------------- | :--------------------------------------------- |
| `students`            | Core student information + cumulative stats    |
| `student_semesters`   | Per-semester academic performance              |
| `student_courses`     | Individual course attempts, grades, and status |
| `advisor_assignments` | Advisor-to-student assignments                 |
| `advisor_notes`       | Notes written by advisors about students       |

#### Import Pipeline

| Table            | Purpose                                              |
| :--------------- | :--------------------------------------------------- |
| `import_jobs`    | Tracks Excel import jobs (status, counts, error_log) |
| `imported_files` | File metadata for each import                        |
| `raw_students`   | Staging table for parsed student data                |
| `raw_courses`    | Staging table for parsed course data                 |

#### Expert System & Analytics

| Table                   | Purpose                                                          |
| :---------------------- | :--------------------------------------------------------------- |
| `academic_analyses`     | Latest expert system run per student (status, risk, eligibility) |
| `analysis_issues`       | Individual rule violations with explanations and recommendations |
| `department_statistics` | Periodic snapshots for trend reporting                           |
| `reports`               | Generated report metadata (JSONB data)                           |

#### Authentication & Authorization

| Table         | Purpose                                                |
| :------------ | :----------------------------------------------------- |
| `profiles`    | Extends Supabase `auth.users` with app-specific fields |
| `roles`       | Role definitions (`admin`, `academic_advisor`)         |
| `user_roles`  | Many-to-many user-role assignments                     |
| `grade_scale` | Global grading scale (points, passing, GPA impact)     |

### Key Relationships

```text
departments (1) ──< (N) curricula
curricula (1) ──< (N) curriculum_courses
curriculum_courses (1) ──< (N) course_prerequisites (as course_id or required_course_id)

curricula (1) ──< (N) elective_groups
elective_groups (1) ──< (N) elective_group_courses

curricula (1) ── (1) graduation_requirements
curricula (1) ── (1) academic_rules

departments (1) ──< (N) students
curricula (1) ──< (N) students
students (1) ──< (N) student_semesters
student_semesters (1) ──< (N) student_courses

students (1) ──< (N) academic_analyses
academic_analyses (1) ──< (N) analysis_issues

students (1) ──< (N) advisor_assignments (active)
profiles (1) ──< (N) advisor_assignments (as advisor_id)

import_jobs (1) ──< (N) imported_files
import_jobs (1) ──< (N) raw_students
raw_students (1) ──< (N) raw_courses
```

### ERD Reference

Complete ERD documentation is available in:

- `docs/database/ERD.md` — Entity relationship diagrams
- `docs/database/RELATIONSHIPS.md` — Detailed relationship documentation
- `docs/database/TABLE_DOCUMENTATION.md` — Per-table field descriptions

### Important Constraints & Design Decisions

#### Enums

- `term_enum`: `'fall'`, `'spring'`, `'summer'`
- `course_category_enum`: `'university_required'`, `'university_elective'`, `'college_required'`, `'college_elective'`, `'major_required'`, `'major_elective'`
- `academic_status_enum`: `'good_standing'`, `'delayed'`, `'needs_support'`, `'probation'`
- `risk_level_enum`: `'low'`, `'medium'`, `'high'`
- `import_status_enum`: `'pending'`, `'processing'`, `'completed'`, `'failed'`
- `issue_severity_enum`: `'info'`, `'warning'`, `'error'`

#### Key Constraints

- `students.student_code` is globally unique
- `curricula` unique constraint on `(department_id, regulation_year)`
- `academic_analyses` stores latest analysis per student (queried via `latest_academic_analyses` view)
- `student_courses` tracks `is_latest_attempt` to identify the current grade for GPA calculation
- `import_jobs.department_id` ensures one workbook = one department

#### Row Level Security (RLS)

- All tables have RLS enabled
- Helper functions: `is_admin()`, `is_advisor()`, `is_staff()`
- Staff (admin or advisor) can read most tables; only admin can write reference data
- Users can see/update their own profile; admin can see/manage all profiles
- Import jobs can be updated by uploader or admin

### Views & Functions

#### Views

- `latest_academic_analyses` — Most recent analysis per student
- `student_academic_summary` — Student + department + curriculum + latest analysis
- `department_status_overview` — Per-department counts by academic status

#### RPC Functions

- `fn_student_completion_percentage(uuid)` → Graduation progress percentage
- `fn_student_academic_summary(uuid)` → Complete academic summary as JSONB

### Migration Files

Migrations are organized in strict dependency order:

```text
001_extensions.sql           -- pgcrypto
002_enums.sql                -- 6 enum types
003_schema.sql               -- 25 tables
004_constraints_indexes.sql  -- CHECK constraints, indexes
005_triggers.sql             -- updated_at, auth.users -> profiles
006_rls.sql                  -- RLS policies
007_storage_notes.sql        -- Storage buckets
008_seed.sql                 -- roles, grade_scale
009_views.sql                -- 3 helper views
010_functions.sql            -- 2 RPC functions
```

---

## 🚀 Current Features

### Implemented Features

| Feature Area           | Specific Capability                                                                              | Status      |
| :--------------------- | :----------------------------------------------------------------------------------------------- | :---------- |
| 🔐 Authentication      | Login with Supabase Auth, session management                                                     | ✅ Complete |
| 👥 User Management     | User list, role assignment (admin/advisor)                                                       | ✅ Complete |
| 🏢 Departments         | CRUD operations for academic departments                                                         | ✅ Complete |
| 📚 Curricula           | Curriculum management with regulation years                                                      | ✅ Complete |
| 📖 Courses             | Course search, creation, prerequisite management                                                 | ✅ Complete |
| 📋 Academic Load Rules | Min/max hours per term, level progression rules                                                  | ✅ Complete |
| 🎓 Students            | Student list, filtering, search                                                                  | ✅ Complete |
| 📊 Student Profile     | 8 tabs: Overview, Transcript, Academic Plan, Graduation, Analysis, Prerequisites, Notes, Reports | ✅ Complete |
| 📈 Dashboard           | KPI cards, academic status chart, GPA distribution, at-risk panel, department table              | ✅ Complete |
| 📤 Data Import         | Excel upload wizard, preview, validation, history tracking                                       | ✅ Complete |
| 🧠 Expert System       | Rule-based analysis, academic status detection, risk assessment                                  | ✅ Complete |
| 📋 Analysis Issues     | Per-rule issue tracking with severity and recommendations                                        | ✅ Complete |
| 📝 Advisor Notes       | Note-taking per student                                                                          | ✅ Complete |
| 👥 Advisor Assignments | Assign advisors to students                                                                      | ✅ Complete |
| 🔔 Notifications       | In-app notification center                                                                       | ✅ Complete |
| 📊 Reports             | Student reports (academic summary), department analytics                                         | ✅ Complete |
| 🤖 AI Assistant        | Chat interface for natural language explanations                                                 | ✅ Complete |
| 🎨 Grade Scale         | Global grade scale management (A-F + special symbols)                                            | ✅ Complete |
| 🌐 RTL Support         | Full Arabic interface with RTL layout                                                            | ✅ Complete |
| 🖨️ Print/Export        | PDF report generation, native printing (Electron)                                                | ✅ Complete |

### Feature Details

#### Student Profile Tabs

1.  **Overview** — Academic summary card, expert system summary, graduation progress bar
2.  **Transcript** — Semester-by-semester course list with grades
3.  **Academic Plan** — Planned vs completed courses
4.  **Graduation** — Graduation eligibility check
5.  **Analysis** — Expert system issues with explanations
6.  **Prerequisites** — Prerequisite status for upcoming courses
7.  **Notes** — Advisor notes (add/edit/delete)
8.  **Reports** — Generated report history

#### Data Import Wizard

Three-stage wizard:

1.  **Upload** — File dropzone with validation
2.  **Preview** — Review parsed data before commit
3.  **Result** — Success/failure summary with error log

#### Dashboard Components

- KPI cards: Total students, at-risk students, avg GPA, graduation rate
- Academic status donut chart
- GPA distribution histogram
- At-risk students panel (top 5-10 high-risk students)
- Department status table
- Recent imports widget

---

## 🔧 Setup & Installation

### Prerequisites

| Tool    | Version | Purpose                      |
| :------ | :------ | :--------------------------- |
| Node.js | 20+     | React + Electron             |
| Python  | 3.11+   | FastAPI backend              |
| Docker  | Latest  | Local Supabase/Postgres      |
| pnpm    | Latest  | Package management           |
| Poetry  | Latest  | Python dependency management |

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/facultyspecificeducation-ksu/acadexa.git
cd acadexa
```

### 2️⃣ Environment Variables

Create `.env` files for each service:

**Backend (`apps/api/.env`):**

```ini
# Supabase / PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# JWT / Session
SECRET_KEY=your-strong-secret-key-here

# AI Provider (for assistant layer only)
AI_PROVIDER=anthropic  # or openai
AI_API_KEY=sk-...

# CORS (for development)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Frontend (`apps/web/.env.development`):**

```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 3️⃣ Database Setup (Supabase)

**Option A — Local Supabase (Docker):**

```bash
# From project root
docker-compose up -d

# Apply migrations (in Supabase SQL editor or via CLI)
# Run files in order: 001 → 010
```

**Option B — Supabase Cloud:**

1.  Create a new Supabase project
2.  Open the SQL editor
3.  Run each migration file in order (001 → 010)

### 4️⃣ Backend Setup (FastAPI)

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (using Poetry)
poetry install

# Or using pip
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Run database migrations (if not using Supabase migrations)
alembic upgrade head

# Seed demo data
python -m app.db.seed.seed_data

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 5️⃣ Frontend Setup (React)

```bash
cd apps/web

# Install dependencies
pnpm install

# Start dev server
pnpm dev
# Opens on http://localhost:5173
```

### 6️⃣ Desktop Setup (Electron)

```bash
cd apps/desktop

# Install dependencies
pnpm install

# Run Electron (loads React dev server)
pnpm dev
```

### 7️⃣ Run with Docker Compose (Full Stack)

```bash
# From project root
docker-compose up -d

# Services:
# - Supabase (PostgreSQL) on port 54322
# - FastAPI on port 8000
```

---

## 👨‍💻 Development Workflow

### Running Services

```bash
# Backend only
cd apps/api && uvicorn app.main:app --reload --port 8000

# Frontend only
cd apps/web && pnpm dev

# Electron (with hot reload)
cd apps/desktop && pnpm dev

# All services (using Turborepo)
pnpm dev  # From root
```

### Build Commands

```bash
# Build React app
cd apps/web && pnpm build

# Build Electron desktop app
cd apps/desktop && pnpm dist
# Output: apps/desktop/release/

# Build everything (using Turborepo)
pnpm build  # From root
```

### Type Checking

```bash
# Frontend
cd apps/web && pnpm type-check

# Shared types
cd packages/shared-types && pnpm type-check
```

### Linting

```bash
# From root
pnpm lint

# Fix auto-fixable issues
pnpm lint:fix
```

---

## 🧪 Testing

### Backend Tests

```bash
cd apps/api

# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v

# Specific test suite
pytest tests/unit/expert_system/test_condition_evaluator.py -v
```

### Frontend Tests

```bash
cd apps/web

# Unit tests (Vitest)
pnpm test

# E2E tests (Playwright)
pnpm test:e2e

# Test coverage
pnpm test:coverage
```

---

## 📦 Deployment

### CI/CD Pipelines (GitHub Actions)

| Workflow            | Trigger         | Purpose                            |
| :------------------ | :-------------- | :--------------------------------- |
| `ci.yml`            | Every PR        | Lint + test (web, api)             |
| `build-desktop.yml` | On push to main | electron-builder matrix build      |
| `release.yml`       | Tag push        | Build + publish to GitHub Releases |

### Building for Production

```bash
# Build React app
cd apps/web
pnpm build

# Build Electron desktop app
cd apps/desktop
pnpm dist

# Output locations:
# - Windows: apps/desktop/release/*.exe
# - macOS: apps/desktop/release/*.dmg
# - Linux: apps/desktop/release/*.AppImage
```

### Deployment Models

- **Development:** React dev server + local API + local Supabase
- **Production (Desktop):** Bundled static assets + local sidecar API
- **Production (Cloud):** Hosted FastAPI + Supabase, Electron connects remotely

### Auto-updates

`electron-updater` checks GitHub Releases feed published by `release.yml`. Update service wired in `apps/desktop/src/main/services/update.service.ts`.

---

## 🔮 Future Improvements

Based on the current implementation, these are reasonable enhancements for future iterations:

### Short-term (Next Release)

1.  **Batch student operations** — Bulk assign advisors, bulk export reports
2.  **Advanced student filtering** — Save custom filters, filter by analysis issues
3.  **Export improvements** — CSV export for department analytics, Excel export for student lists
4.  **Notification improvements** — Email notifications for high-risk students, real-time WebSocket updates
5.  **Dashboard enhancements** — More charts (completion rate trends, course pass rates)

### Medium-term

1.  **Schedule tracking** — Course scheduling, conflict detection, room allocation
2.  **Student self-service portal** — Student-facing view (separate from advisor view)
3.  **Advanced analytics** — Predictive risk modeling using historical data
4.  **Rule analytics enhancements** — Rule effectiveness scoring, A/B testing for thresholds
5.  **Mobile companion app** — React Native or PWA for advisors on-the-go

### Long-term

1.  **Multi-university support** — Tenant isolation, custom rule sets per institution
2.  **Integration APIs** — REST/GraphQL APIs for third-party SIS integration
3.  **Advanced AI features** — Course recommendation engine, personalized study plans
4.  **Real-time collaboration** — Shared advisor notes, co-viewing student profiles
5.  **Automated reporting** — Scheduled reports via email, custom report builder

### Technical Debt

1.  **Improve test coverage** — Current coverage ~65%, target 85%
2.  **API documentation** — OpenAPI/Swagger with examples
3.  **Performance optimization** — Virtual scrolling for large student lists, query caching
4.  **Error boundary implementation** — Better error recovery in React

---

## 👩‍💻 Author

**Acadexa Team**
🎓 Faculty of Specific Education — KSU
📊 Passionate about Data Analysis, AI Systems, and Full-stack Development

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgements

- **Electron** — Cross-platform desktop apps
- **React** — UI library
- **FastAPI** — Modern Python backend
- **Material-UI** — Component library with RTL
- **Supabase** — Open-source Firebase alternative
- **Turborepo** — Monorepo task runner
- **PostgreSQL** — Reliable relational database

---

Made with ❤️ for Faculty of Specific Education — KSU
