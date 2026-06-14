# 🎓 ACADEXA — Intelligent Academic Advising Desktop Application

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

## 📌 Project Overview

**ACADEXA** is an intelligent academic advising desktop application designed to help universities move beyond simple data storage. It combines traditional academic management (students, courses, transcripts) with a **Dynamic Expert System (ES)** engine that mimics human expert reasoning.

> 🎯 **Core Philosophy:** Instead of just answering "What is the student's GPA?", ACADEXA answers **"Why is the student at risk?"** and **"What should they do next?"**

ACADEXA is treated as a **multi-process monorepo product**, not a single app. Three runtimes stay decoupled but type-safe with each other:

1. **Electron Desktop Shell** — owns OS-level concerns (windows, file system, printing, notifications, auto-update).
2. **React Renderer (Acadexa Web UI)** — the application UI, built with Vite, MUI (RTL), Zustand, React Router, React Hook Form + Zod.
3. **FastAPI Backend** — the brain: database access, Expert System, AI layer, data ingestion, reporting.

The Electron app is a thin native shell around the React renderer, which talks to the FastAPI backend over HTTP/REST (and optionally WebSockets for live notifications). The backend can run locally (bundled as a sidecar process) or remotely (cloud-hosted FastAPI + Supabase) — the architecture supports both without code changes, only configuration.

Two architectural principles drive every folder decision:

- **Feature-based modularity** — code is grouped by business capability (`expert-system`, `reports`), not by technical type (`students`, `controllers`, `components`). This keeps each module independently testable and replaceable.
- **Strict layering** — UI → State → API client → Backend Router → Service → Repository/ORM → DB. No layer is skipped. The Expert System and AI layer sit as services consumed by routers, never embedded in routers directly.

### ✨ Key Differentiators

| Feature | Traditional SIS | ACADEXA |
| :--- | :--- | :--- |
| Data Storage | ✅ Yes | ✅ Yes |
| GPA Calculation | ✅ Yes | ✅ Yes |
| Prerequisite Checking | ❌ Manual | ✅ **Automatic** |
| Academic Risk Detection | ❌ No | ✅ **Expert System** |
| Graduation Eligibility | ❌ Manual Audit | ✅ **Instant Check** |
| Explainable AI | ❌ No | ✅ **Evidence-Based** |
| Offline Desktop | ❌ No | ✅ **Electron Native** |
| Arabic RTL Support | ❌ Rare | ✅ **Full Support** |

---

## 🧠 System Architecture

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

### 🧩 Component Breakdown

| Layer | Technology | Responsibility |
| :--- | :--- | :--- |
| Desktop Shell | Electron | Native OS features (filesystem, printing, notifications, auto-update) |
| UI Renderer | React + Vite + MUI + RTL | All business UI, state management (Zustand), routing (React Router) |
| API Gateway | FastAPI (Python) | Request validation, routing, RBAC enforcement |
| Expert System | Custom Forward-Chaining Engine | Rule evaluation, inference, recommendation generation |
| AI Assistant | LLM (OpenAI/Anthropic) | Explanation rephrasing, report summaries (read-only) |
| Data Layer | SQLAlchemy + Supabase/Postgres | ORM, migrations, data persistence |

### Why a Monorepo?

Electron, React, and shared TypeScript types must evolve together. A monorepo with workspaces (npm/pnpm workspaces + Turborepo or Nx) lets `shared-types` be imported by both `desktop` and `web` without publishing packages, while the Python `api` lives alongside as an independent workspace with its own dependency tree (Poetry/uv).

---

## 🛠️ Full Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| Desktop Framework | Electron | Cross-platform desktop app (Windows, macOS, Linux) |
| Frontend Framework | React 18 + Vite | Fast UI development with HMR |
| UI Library | Material-UI (MUI) v5 | Professional components with RTL support |
| State Management | Zustand | Lightweight, scalable state |
| Type Safety | TypeScript + Zod | Full-stack type safety |
| Backend Framework | FastAPI (Python 3.11+) | High-performance async REST API |
| Database ORM | SQLAlchemy 2.0 (Async) | Async database operations |
| Database | PostgreSQL (Supabase) | Primary relational data store |
| Authentication | Supabase Auth / JWT | Role-based access control |
| Expert System | Custom Rule Engine | Forward-chaining inference with JSONB rules |
| AI Integration | OpenAI/Anthropic API | Natural language explanations (read-only) |
| File Processing | Pandas + OpenPyXL | Excel transcript parsing |
| Task Queue | BackgroundTasks / Celery | Long-running imports |
| Package Manager | npm workspaces + Poetry | Monorepo management |

---

## 📁 Project Structure (Monorepo)

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
├── docs/                         # ADRs, architecture diagrams, API docs
├── scripts/                       # Cross-cutting dev/build/release scripts
├── .github/workflows/             # CI/CD pipelines
├── docker-compose.yml              # Local Supabase/Postgres + API
├── turbo.json / nx.json            # Monorepo task runner config
└── package.json                    # Workspace root
```

---

## 💻 apps/desktop — Electron Architecture

```text
apps/desktop/
├── src/
│   ├── main/
│   │   ├── index.ts                   # App entry, window lifecycle
│   │   ├── windows/
│   │   │   ├── main-window.ts         # BrowserWindow factory + config
│   │   │   └── window-manager.ts      # Tracks open windows, focus mgmt
│   │   ├── ipc/
│   │   │   ├── handlers/
│   │   │   │   ├── file-handler.ts        # Open/save dialogs, file reads
│   │   │   │   ├── print-handler.ts       # Print/print-to-PDF
│   │   │   │   ├── notification-handler.ts
│   │   │   │   ├── update-handler.ts      # autoUpdater events
│   │   │   │   └── storage-handler.ts     # electron-store local cache
│   │   │   └── ipc-registry.ts        # Central registration of all ipcMain.handle()
│   │   ├── services/
│   │   │   ├── api-config.service.ts  # Resolves backend base URL (local/remote)
│   │   │   ├── update.service.ts      # electron-updater wiring
│   │   │   └── tray.service.ts        # System tray menu
│   │   ├── menu/
│   │   │   └── app-menu.ts            # Native menu (with i18n labels)
│   │   └── security/
│   │       └── csp.ts                 # Content-Security-Policy headers
│   ├── preload/
│   │   ├── index.ts                   # contextBridge exposeInMainWorld
│   │   └── api/
│   │       ├── fileApi.ts             # window.acadexa.files.*
│   │       ├── printApi.ts            # window.acadexa.print.*
│   │       ├── notificationApi.ts     # window.acadexa.notify.*
│   │       └── updateApi.ts           # window.acadexa.updates.*
│   └── shared/
│       ├── ipc-channels.ts            # Enum of all IPC channel names (single source of truth)
│       └── types.ts                   # Shared main/preload/renderer types
├── resources/                          # Icons, tray icons, installer assets
├── build/
│   ├── entitlements.mac.plist
│   └── electron-builder.yml
├── electron.vite.config.ts
└── package.json
```

### Responsibilities & Communication (Data Processing)

- **`main/index.ts`** — App bootstrap: creates the main `BrowserWindow`, loads the Vite dev server URL (dev) or `apps/web/dist/index.html` (prod), registers IPC handlers, sets up auto-updater and tray.
- **`main/ipc/handlers/*`** — Each handler wraps a native OS capability (`dialog`, `fs`, `Notification`, `webContents.print`) behind a single `ipcMain.handle(channel, ...)`. These are the only place Node APIs are touched.
- **`preload/api/*`** — Uses `contextBridge` to expose a strictly-typed `window.acadexa.*` object to the renderer. The renderer never uses `require` or Node APIs directly — only this bridge. This is the security boundary (no `nodeIntegration`).
- **`shared/ipc-channels.ts`** — A single enum/const object imported by both main and preload, so channel name typos become compile errors.

**Why this exists:** Electron is the only layer allowed to touch the filesystem, native dialogs, printers, and OS notifications. Everything else (business logic, data, UI) lives in `web` and `api`, making the desktop shell swappable (e.g., could later become a Tauri shell with minimal changes to `web`/`api`).

### Communication Flow

```text
React Renderer (apps/web)
  ⇅ window.acadexa.* (contextBridge, typed)
Preload Script
  ⇅ ipcRenderer.invoke / ipcMain.handle
Main Process (Electron)
  ⇅ Node fs / dialog / Notification / print / autoUpdater
Operating System
```

All business/academic data flows over HTTP from `apps/web` directly to `apps/api` (FastAPI) — Electron IPC is **not** used as a data tunnel for academic data.

---

## ⚛️ apps/web — Frontend (React Renderer) Architecture

```text
apps/web/
├── src/
│   ├── app/
│   │   ├── App.tsx                    # Root component, providers
│   │   ├── AppRouter.tsx              # React Router route tree
│   │   ├── providers/
│   │   │   ├── ThemeProvider.tsx      # MUI theme + RTL/LTR switch
│   │   │   ├── AuthProvider.tsx       # Session context
│   │   │   └── QueryProvider.tsx      # React Query / API client provider
│   │   └── layouts/
│   │       ├── DashboardLayout.tsx
│   │       ├── AuthLayout.tsx
│   │       └── PrintLayout.tsx        # Minimal layout for print views
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/            # LoginForm, SessionExpiredDialog
│   │   │   ├── hooks/                 # useLogin, useSession
│   │   │   ├── store/                 # auth.store.ts (Zustand)
│   │   │   ├── api/                   # auth.api.ts
│   │   │   └── schemas/               # login.schema.ts (Zod)
│   │   ├── students/
│   │   │   ├── components/            # StudentTable, StudentProfile, GradeHistory
│   │   │   ├── hooks/                 # useStudents, useStudentDetails
│   │   │   ├── store/
│   │   │   ├── api/
│   │   │   └── schemas/
│   │   ├── academic-structure/        # Departments, Programs, Study Plans, Levels, Semesters
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── store/
│   │   │   └── api/
│   │   ├── courses/                   # Courses, Prerequisites, Academic Load Rules (UI)
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── store/
│   │   │   └── api/
│   │   ├── expert-system/             # Rule Builder UI, Rule List, Test/Simulate Rule
│   │   │   ├── components/
│   │   │   │   ├── RuleEditor.tsx     # Condition/Action builder
│   │   │   │   ├── RuleList.tsx
│   │   │   │   └── RuleSimulator.tsx
│   │   │   ├── hooks/
│   │   │   ├── store/
│   │   │   └── api/
│   │   ├── recommendations/           # Displays explainable recommendations
│   │   │   ├── components/
│   │   │   │   ├── RecommendationCard.tsx  # shows reason, evidence, priority
│   │   │   │   └── ExplanationPanel.tsx
│   │   │   ├── hooks/
│   │   │   └── api/
│   │   ├── data-import/               # Excel upload & mapping UI
│   │   │   ├── components/
│   │   │   │   ├── FileDropzone.tsx
│   │   │   │   ├── ImportPreviewTable.tsx
│   │   │   │   └── ImportStatusTracker.tsx
│   │   │   ├── hooks/
│   │   │   └── api/
│   │   ├── reports/                   # Report generation & PDF export UI
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── api/
│   │   ├── ai-assistant/              # Chat assistant UI
│   │   │   ├── components/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   └── ChatBubble.tsx
│   │   │   ├── hooks/
│   │   │   ├── store/
│   │   │   └── api/
│   │   ├── notifications/             # In-app notification center
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── store/
│   │   └── admin/                     # User management, RBAC config, system settings
│   │       ├── components/
│   │       ├── hooks/
│   │       └── api/
│   ├── shared/
│   │   ├── components/                # DataGrid wrappers, ConfirmDialog, EmptyState
│   │   ├── hooks/                      # useDebounce, usePagination, useElectronBridge
│   │   ├── lib/
│   │   │   ├── apiClient.ts           # Axios/fetch instance, interceptors (auth token, errors)
│   │   │   └── electronBridge.ts      # Wraps window.acadexa.* with fallbacks for web-only mode
│   │   ├── guards/
│   │   │   └── RoleGuard.tsx          # RBAC-aware route/component guard
│   │   └── utils/
│   ├── store/
│   │   └── root.store.ts              # Combines/exports feature Zustand stores
│   ├── theme/
│   │   ├── theme.ts                   # MUI theme tokens (colors, typography)
│   │   ├── rtl.ts                     # stylis-plugin-rtl setup
│   │   └── palette.ts
│   ├── i18n/
│   │   ├── ar.json
│   │   ├── en.json
│   │   └── i18n.ts                    # i18next config (default: Arabic/RTL)
│   ├── routes/
│   │   └── routes.config.ts           # Route definitions mapped to roles
│   └── main.tsx
├── public/
├── index.html
└── vite.config.ts
```

### Frontend Responsibilities & Communication

- **`app/providers`** — Global cross-cutting concerns: theme/RTL switching (critical for Arabic UI), authenticated session context (reads/writes via `features/auth/store`), and the API client provider (base URL resolved via Electron preload in desktop mode, `.env` in web-dev mode).
- **`features/*`** — Each feature is a vertical slice: `components` (presentation), `hooks` (data-fetching/business logic via React Query wrapping `api/`), `store` (Zustand slices for local/UI state), `api` (typed REST calls to FastAPI using `shared-types` DTOs), `schemas` (Zod validation matching backend Pydantic schemas).
- **`features/expert-system`** and **`features/recommendations`** are deliberately separate features: the former is the admin authoring tool for rules (Admin/Developer roles), the latter is the consumption view of generated recommendations (Advisor role). Both call different backend routers but share the `shared-types` rule/recommendation DTOs.
- **`shared/guards/RoleGuard.tsx`** — Wraps routes/components, reading the role from `features/auth/store`, enforcing RBAC purely at the presentation layer (the backend enforces it again — defense in depth).
- **`shared/lib/electronBridge.ts`** — Abstraction so feature code calls `electronBridge.files.openExcel()` rather than `window.acadexa.files.openExcel()` directly; this allows the same `web` codebase to run in a plain browser (e.g., for web-only deployment) by swapping the bridge implementation.

**Communication:** `features/*/api` → `shared/lib/apiClient` (Axios instance with base URL + auth header interceptor) → FastAPI `apps/api`. File picking/printing/notifications go through `electronBridge` → Electron preload → main process.

---

## ⚙️ apps/api — Backend (FastAPI) Architecture

```text
apps/api/
├── app/
│   ├── main.py                        # FastAPI app factory, middleware, router registration
│   ├── core/
│   │   ├── config.py                  # Settings (Pydantic Settings, .env driven)
│   │   ├── security.py                # Password/session hashing, JWT/session tokens
│   │   ├── dependencies.py            # get_current_user, get_db, RBAC dependencies
│   │   ├── exceptions.py              # Custom exception classes + handlers
│   │   └── logging.py
│   ├── db/
│   │   ├── base.py                    # Declarative base, naming conventions
│   │   ├── session.py                 # SQLAlchemy session/engine (Supabase Postgres)
│   │   └── seed/
│   │       └── seed_data.py           # Initial roles, sample rules, demo users
│   ├── models/                        # SQLAlchemy ORM models (one module per domain)
│   │   ├── user.py
│   │   ├── student.py
│   │   ├── academic_structure.py      # Department, Program, StudyPlan, Level, Semester
│   │   ├── course.py                  # Course, Prerequisite
│   │   ├── grade.py
│   │   ├── rule.py                    # Rule, RuleCondition, RuleAction
│   │   ├── recommendation.py
│   │   └── notification.py
│   ├── schemas/                       # Pydantic request/response DTOs (mirrors shared-types)
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── academic_structure.py
│   │   ├── course.py
│   │   ├── rule.py
│   │   ├── recommendation.py
│   │   └── report.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py              # Aggregates all v1 routers
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── students.py
│   │           ├── academic_structure.py
│   │           ├── courses.py
│   │           ├── grades.py
│   │           ├── rules.py           # CRUD for Expert System rules
│   │           ├── recommendations.py # Trigger evaluation / fetch recommendations
│   │           ├── reports.py
│   │           ├── data_import.py     # Excel upload endpoints
│   │           ├── ai_assistant.py
│   │           ├── notifications.py
│   │           └── admin.py           # User/role management
│   ├── services/                      # Business logic layer (orchestrates repositories)
│   │   ├── auth_service.py
│   │   ├── student_service.py
│   │   ├── gpa_service.py             # GPA calculation logic
│   │   ├── graduation_service.py      # Graduation requirement checks
│   │   ├── course_service.py
│   │   ├── report_service.py
│   │   └── notification_service.py
│   ├── repositories/                  # Data-access layer (SQLAlchemy queries, isolated from services)
│   │   ├── student_repository.py
│   │   ├── course_repository.py
│   │   ├── rule_repository.py
│   │   └── recommendation_repository.py
│   ├── expert_system/                 # ⭐ Core Expert System engine (see section below)
│   ├── ai/                            # 🤖 AI assistant layer (see section below)
│   ├── data_processing/               # ⭐ Excel ingestion (see section below)
│   └── tasks/
│       └── background_jobs.py         # Long-running jobs (bulk import, batch recommendation runs)
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/                              # See Testing Structure section
├── pyproject.toml
└── .env.example
```

### API Layer: Responsibilities & Communication

- **`core/`** — Cross-cutting infrastructure: configuration (Supabase connection string, JWT secret, AI provider keys), security primitives, and FastAPI dependency injection helpers (`get_current_user` resolves the session and role; `require_role("admin")` is a reusable dependency for RBAC).
- **`db/`** — SQLAlchemy engine/session setup pointed at Supabase Postgres, plus Alembic migrations for schema evolution and a seed script for demo/test data (roles, sample rules, sample students).
- **`models/`** — Pure ORM definitions, one file per domain area, mapped 1:1 to the ER design below.
- **`schemas/`** — Pydantic models define the API contract. These are mirrored (manually or via codegen) into `packages/shared-types` so the React frontend has compile-time accurate DTOs.
- **`api/v1/endpoints/*`** — Thin controllers: validate input via schemas, call a `service`, return a schema. No business logic lives here.
- **`services/*`** — Where business rules that are *not* part of the Expert System live (e.g., GPA calculation formulas, graduation requirement aggregation, report assembly). These services call into `expert_system/` when a decision needs rule-based reasoning, but they own deterministic calculations (GPA math, semester totals).
- **`repositories/*`** — All raw SQLAlchemy queries are isolated here so services remain testable with mocked repositories.

**Communication:** `endpoints` → `services` → (`repositories` for data, `expert_system` for reasoning, `ai` for natural-language tasks, `data_processing` for Excel ingestion) → `models`/`db`.

---

## 🧠 Expert System Architecture (`apps/api/app/expert_system/`)

This is the heart of Acadexa. It must be a genuine rule-based inference engine, not embedded conditionals.

```text
expert_system/
├── __init__.py
├── engine.py                      # InferenceEngine — orchestrates the full evaluation cycle
├── knowledge_base/
│   ├── loader.py                  # Loads active Rule rows from DB → in-memory KB
│   ├── rule_models.py             # Internal dataclasses: Rule, Condition, Action
│   └── rule_validator.py          # Validates rule JSON structure on create/update
├── facts/
│   ├── fact_builder.py            # Builds a "StudentFactSheet" from DB (GPA, grades, levels, courses taken)
│   └── fact_schema.py             # Defines the canonical fact dictionary shape
├── operators/
│   └── operator_registry.py       # Registry of supported operators: ==, !=, >, <, >=, <=, in, between, contains
├── evaluation/
│   ├── condition_evaluator.py     # Evaluates a single Condition against Facts
│   ├── rule_matcher.py            # Determines which rules "fire" for a given fact set
│   └── conflict_resolver.py       # Resolves priority/conflicts when multiple rules fire
├── actions/
│   └── action_executor.py         # Executes the Action of a fired rule (creates Recommendation, triggers Notification)
├── explanation/
│   └── explanation_builder.py     # Builds the structured explanation object (rule id, reason, evidence, etc.)
├── categories/
│   ├── gpa_rules.py                # Category-specific helper logic (registered, not hardcoded business outcomes)
│   ├── warning_rules.py
│   ├── graduation_rules.py
│   ├── prerequisite_rules.py
│   ├── load_rules.py
│   └── registration_rules.py
└── runner.py                       # Public entrypoint: run_evaluation(student_id) -> List[Recommendation]
```

### How It Works (Inference Cycle)

1. **`facts/fact_builder.py`** queries the database via repositories and assembles a `StudentFactSheet`: a normalized dict/dataclass containing GPA, completed credit hours, current semester, grades per course, program requirements, attempted prerequisites, current academic load, etc. This is the engine's "working memory."
2. **`knowledge_base/loader.py`** loads all `Rule` rows where `is_active = true`, ordered by `priority`, and converts each DB row's JSON `conditions`/`actions` into internal `Rule`/`Condition`/`Action` dataclasses (via `rule_models.py`), validated by `rule_validator.py`.
3. **`evaluation/rule_matcher.py`** iterates rules; for each, `evaluation/condition_evaluator.py` evaluates every condition against the `StudentFactSheet` using the operator implementations in `operators/operator_registry.py` (a dict mapping operator strings to lambda/functions — extensible without touching the engine core).
4. Rules whose conditions all evaluate true are "fired." `evaluation/conflict_resolver.py` orders fired rules by priority and removes mutually-exclusive duplicates (e.g., don't show both "good standing" and "academic warning" for the same GPA threshold band if rules overlap).
5. **`actions/action_executor.py`** executes each fired rule's action (e.g., `CREATE_RECOMMENDATION`, `TRIGGER_NOTIFICATION`, `FLAG_PREREQUISITE_VIOLATION`), persisting `Recommendation` rows via `recommendation_repository`.
6. **`explanation/explanation_builder.py`** attaches to every generated recommendation: `rule_id`, `rule_name`, `reason` (human template filled with actual student values), `evidence` (the exact fact values that satisfied each condition), `explanation` (full narrative), and `priority`.
7. **`runner.py`** exposes `run_evaluation(student_id)`, called from `services/` (e.g., whenever new grades are imported, or on-demand from the Advisor UI via `endpoints/recommendations.py`).

### Why This Design

- The engine is **data-driven**: adding a new rule means inserting a row in the `rules` table (via Admin UI → `endpoints/rules.py`), never touching Python code — satisfying "rules must not be hardcoded."
- The `categories/*` modules exist only to hold category-specific helper computations that a condition might reference (e.g., "credits_remaining_to_graduate" — a derived fact, not a hardcoded decision), keeping the core `engine.py` generic across all six rule categories.
- `operator_registry.py` makes the condition language extensible (add a new operator without touching `condition_evaluator.py`).

**Communication:** `expert_system` is called only by `services/` (never directly by `api/endpoints`), and never calls `ai/` — satisfying "AI must not replace the rule engine." `ai/` may read the output of `expert_system` (recommendations + explanations) to rephrase them.

---

## 🗃️ Knowledge Base — Database Design

Core tables (Supabase Postgres, managed via SQLAlchemy models + Alembic):

```text
users                  (id, name, email, password_hash, role, is_active)
students               (id, student_number, name, department_id, program_id, level_id, status)
departments            (id, name, code)
programs               (id, name, department_id, total_required_credits)
study_plans            (id, program_id, version, effective_year)
study_plan_courses     (id, study_plan_id, course_id, level_id, semester_no, is_mandatory)
academic_levels        (id, name, order)
semesters              (id, name, year, term, is_active)
courses                (id, code, name, credit_hours, department_id)
course_prerequisites   (id, course_id, prerequisite_course_id, min_grade)
grades                 (id, student_id, course_id, semester_id, grade, grade_points, attempt_no)

-- Expert System Knowledge Base --
rules                  (id, name, category, description, priority,
                        conditions JSONB, operators JSONB, "values" JSONB,
                        actions JSONB, explanation_template TEXT,
                        is_active BOOLEAN, version INT,
                        created_by, updated_by, created_at, updated_at)

recommendations        (id, student_id, rule_id, rule_name_snapshot,
                        reason TEXT, evidence JSONB, explanation TEXT,
                        priority INT, status, created_at)

-- Supporting modules --
notifications          (id, user_id, title, message, type, is_read, created_at)
import_jobs            (id, file_name, uploaded_by, status, summary JSONB, created_at)
reports                (id, type, student_id, generated_by, file_path, created_at)
audit_logs             (id, user_id, action, entity, entity_id, details JSONB, created_at)
```

### Design Notes

- **`rules.conditions` / `rules.actions` as JSONB**: each condition is `{ "field": "gpa", "operator": "<", "value": 2.0 }`; each action is `{ "type": "CREATE_RECOMMENDATION", "category": "academic_warning", "message_template": "..." }`. JSONB allows the Admin UI's `RuleEditor.tsx` to build arbitrarily complex condition trees (AND/OR groups can be modeled as nested JSON) without schema migrations per rule.
- **`recommendations.evidence`** stores a snapshot of the exact fact values used (e.g., `{ "gpa": 1.8, "threshold": 2.0, "semester": "2025-Fall" }`) — this is what powers the "Why was this recommendation generated?" explanation, even if the student's data later changes.
- **`rules.version`** + **`recommendations.rule_name_snapshot`** ensure historical recommendations remain explainable even after a rule is edited later.
- **`study_plan_courses`** + **`course_prerequisites`** feed the `prerequisite_rules` and `load_rules` categories directly as facts.
- **`audit_logs`** tracks who created/edited/activated rules — important for an "expert system" where trust in rule provenance matters.

---

## 🤖 AI Module Structure (`apps/api/app/ai/`)

```text
ai/
├── __init__.py
├── client.py                       # Thin wrapper around LLM provider SDK (model, API key from config)
├── prompts/
│   ├── explanation_prompt.py       # Template: rephrase ExplanationBuilder output in natural language
│   ├── summary_prompt.py           # Template: summarize academic reports
│   └── chat_prompt.py              # System prompt for chat assistant (scope limited)
├── services/
│   ├── explanation_service.py      # explain(recommendation) -> natural language text
│   ├── summary_service.py          # summarize(report_data) -> narrative summary
│   └── chat_service.py             # chat(messages, context) -> assistant reply
├── context/
│   └── context_builder.py          # Gathers allowed context (student facts + recommendations) for prompts
└── guardrails/
    └── scope_guard.py               # Ensures AI responses cannot assert new academic decisions
```

### Responsibilities & Communication

- **`client.py`** isolates the LLM provider so it can be swapped (OpenAI, Anthropic, local model) via config only.
- **`services/explanation_service.py`** is called after `expert_system.runner.run_evaluation()` — it takes the structured `Recommendation` (rule id, reason, evidence, explanation) and asks the LLM to phrase it conversationally in Arabic/English for the Advisor, never to decide whether a recommendation should exist.
- **`services/summary_service.py`** is used by `services/report_service.py` to add a narrative paragraph to PDF reports, summarizing structured data the Expert System and GPA service already computed.
- **`services/chat_service.py`** powers `endpoints/ai_assistant.py` and the `features/ai-assistant` chat UI. `context/context_builder.py` restricts what data the chat can "see" (the current student's facts/recommendations, not arbitrary DB access), and `guardrails/scope_guard.py` post-processes responses to strip/flag any attempt by the model to invent new rules or recommendations — reinforcing "AI is an assistant layer only."

**Communication:** `ai/` is called only by `services/` (report_service, recommendation-related endpoints), reads from `expert_system` outputs and `repositories` (read-only), and never writes to `rules`, `recommendations`, or academic tables directly.

---

## 📥 Data Processing Module (`apps/api/app/data_processing/`)

```text
data_processing/
├── __init__.py
├── parsers/
│   └── excel_parser.py             # Wraps the existing Python Excel parser
├── mappers/
│   ├── student_mapper.py           # Maps raw parsed rows -> Student DTO
│   ├── course_mapper.py
│   └── grade_mapper.py
├── validators/
│   └── import_validator.py         # Schema/sanity checks before DB write (duplicate detection, missing fields)
├── importer/
│   └── import_service.py           # Orchestrates parse -> map -> validate -> persist, within a DB transaction
└── jobs/
    └── import_job_tracker.py       # Updates `import_jobs` status (pending/processing/done/failed) for UI polling
```

### Parser Responsibilities & Communication

- **`parsers/excel_parser.py`** wraps the project's existing parser as a service-layer module — given a file path/stream, returns raw structured rows (student info, courses, grades).
- **`mappers/*`** convert raw parser output into the same DTOs used by `schemas/` and ORM `models/`, isolating Excel-format quirks from the rest of the system.
- **`validators/import_validator.py`** checks for duplicate student numbers, unknown course codes, invalid grade values, etc., producing a structured report of warnings/errors shown in `ImportPreviewTable.tsx` before commit.
- **`importer/import_service.py`** is the single transactional entry point: called from `endpoints/data_import.py` after the Electron file dialog (via `electronBridge.files.openExcel()`) returns a file path, the file is uploaded/streamed to this endpoint, and on success it can trigger `expert_system.runner.run_evaluation()` for affected students (new grades may produce new recommendations).
- **`jobs/import_job_tracker.py`** persists progress to `import_jobs`, polled by `ImportStatusTracker.tsx` for large files.

**Communication:** `endpoints/data_import.py` → `data_processing.importer` → (`parsers`, `mappers`, `validators`) → `repositories` → DB, then optionally → `expert_system.runner` for re-evaluation, and → `notification_service` to notify advisors of new data.

---

## 🧠 Expert System Deep Dive

The core of ACADEXA is a dynamic rule-based expert system using forward chaining.

### 🔧 Inference Engine Workflow

```text
1. Fact Builder
   └── Queries DB → StudentFactSheet (GPA, credits, grades, prerequisites)

2. Knowledge Base Loader
   └── Loads active rules from 'rules' table (JSONB conditions/actions)

3. Rule Matcher
   └── Evaluates conditions using operator registry (==, >, <, in, contains)

4. Conflict Resolver
   └── Orders fired rules by priority, removes duplicates

5. Action Executor
   └── Persists recommendations with evidence snapshots

6. Explanation Builder
   └── Attaches structured explanation (rule_id, reason, evidence)
```

### 📜 Example Rule (Stored as JSONB)

```json
{
  "name": "Low GPA Warning",
  "category": "academic_warning",
  "priority": 10,
  "conditions": [
    { "field": "gpa", "operator": "<", "value": 2.0 },
    { "field": "current_semester", "operator": ">=", "value": 2 }
  ],
  "actions": [
    { "type": "CREATE_RECOMMENDATION", "category": "warning" }
  ],
  "explanation_template": "Student GPA {gpa} is below {threshold} in semester {current_semester}."
}
```

### 🎯 Why This Design

- ✅ **Data-Driven:** Add/modify rules via Admin UI → No code changes
- ✅ **Explainable:** Every recommendation stores evidence snapshot
- ✅ **Extensible:** Operator registry supports new operators without engine changes
- ✅ **Auditable:** Full version history and audit logs

---

## 🚀 Core Features

| Feature Area | Specific Capability | Powered By |
| :--- | :--- | :--- |
| 📝 Academic Records | CRUD for students, courses, departments, programs | FastAPI + SQLAlchemy |
| 📄 Transcript Import | Upload Excel → Parse → Validate → Store | Pandas + OpenPyXL |
| ✅ Prerequisite Check | Automatic validation before registration | Expert System |
| ⚠️ Risk Detection | Flag low GPA, excessive course load, attendance issues | Expert System |
| 🎓 Graduation Audit | Real-time eligibility check against study plan | Expert System + Services |
| 📊 Academic Analytics | GPA trends, pass rates, semester load reports | Service Layer |
| 🔐 Role-Based Access | Developer / Admin / Academic Advisor | Supabase Auth + RBAC |
| 🤖 AI Assistant | Natural language explanations & report summaries | LLM (read-only) |
| 🖨️ Print & Export | PDF reports, native printing | Electron IPC |
| 🌐 RTL Support | Full Arabic interface | MUI + i18next |
| 📱 Offline Desktop | No internet required after install | Electron + Local API |

---

## 🔄 End-to-End Data Flow Example

> "Advisor imports a new transcript and views recommendations"

1. Advisor clicks "Import Excel" in `features/data-import` → `electronBridge.files.openExcel()` → Electron main `file-handler.ts` opens a native dialog → returns file path/buffer.
2. Frontend uploads the file to `POST /api/v1/data-import/upload` → `endpoints/data_import.py` → `data_processing.importer.import_service`.
3. `excel_parser` extracts rows → `mappers` convert to DTOs → `import_validator` checks integrity → records persisted via `repositories`.
4. `import_service` calls `expert_system.runner.run_evaluation(student_id)` for each affected student.
5. The engine builds a `StudentFactSheet`, loads active `rules` from DB, evaluates conditions, fires matching rules, writes `recommendations` with full `evidence`/`explanation` via `explanation_builder`.
6. `notification_service` creates `notifications` rows for the relevant Advisor; Electron shows a desktop notification via `notification-handler.ts`.
7. Advisor opens `features/recommendations` → `RecommendationCard.tsx` fetches `/api/v1/recommendations?student_id=...` → displays rule id, reason, evidence, explanation, priority.
8. Advisor clicks "Explain in plain language" → `ai.services.explanation_service` rephrases the existing explanation (no new decision made).
9. Advisor generates a PDF report → `report_service` aggregates data + `ai.services.summary_service` narrative → PDF rendered → `electronBridge.print.exportPdf()` or saved via `file-handler.ts`.

This structure gives Acadexa a clean separation between native shell, UI, and intelligent backend, keeps the Expert System genuinely rule-driven and explainable, confines AI to an assistive/explanatory role, and is organized so each module (academic management, expert system, AI, data import, reporting, notifications) can be developed, tested, and scaled independently — appropriate both for a graduation project demo and a future commercial product.

---

## ⚙️ Setup & Installation

### Prerequisites

| Tool | Version | Purpose |
| :--- | :--- | :--- |
| Node.js | 20+ | React + Electron |
| Python | 3.11+ | FastAPI backend |
| Docker | Latest | Local Supabase/Postgres |
| npm or pnpm | Latest | Package management |
| Poetry | Latest | Python dependency management |

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/facultyspecificeducation-ksu/acadexa.git
cd acadexa
```

### 2️⃣ Backend Setup (FastAPI)

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

# Run database migrations
alembic upgrade head

# Seed demo data
python -m app.db.seed.seed_data

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 3️⃣ Frontend Setup (React)

```bash
cd ../web

# Install dependencies
npm install

# Start dev server
npm run dev
# Opens on http://localhost:5173
```

### 4️⃣ Desktop Setup (Electron)

```bash
cd ../desktop

# Install dependencies
npm install

# Run Electron (loads React dev server)
npm run dev
```

### 5️⃣ Run with Docker (Optional)

```bash
# From project root
docker-compose up -d

# Services:
# - PostgreSQL on port 5432
# - FastAPI on port 8000
```

---

## 🔐 Environment Variables (.env.example)

```ini
# Supabase / PostgreSQL
DATABASE_URL=postgresql://acadexa:acadexa@localhost:5432/acadexa

# JWT / Session
SECRET_KEY=your-strong-secret-key-here

# AI Provider (for assistant layer only)
AI_PROVIDER=anthropic  # or openai
AI_API_KEY=sk-...

# CORS (for development)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description | RBAC |
| :--- | :--- | :--- | :--- |
| POST | /api/v1/auth/login | Authenticate user | Public |
| GET | /api/v1/students | List students | Admin, Advisor |
| GET | /api/v1/students/{id} | Student profile | Admin, Advisor |
| POST | /api/v1/data-import/upload | Upload Excel transcript | Admin |
| GET | /api/v1/rules | List expert system rules | Admin, Developer |
| POST | /api/v1/rules | Create new rule | Admin, Developer |
| GET | /api/v1/recommendations?student_id={id} | Get recommendations | Advisor |
| POST | /api/v1/recommendations/evaluate/{student_id} | Run inference | Advisor |
| POST | /api/v1/ai/chat | Chat with AI assistant | Advisor |
| POST | /api/v1/reports/export | Generate PDF report | Advisor |

---

## 🧪 Testing Structure

```text
apps/web/
└── tests/
    ├── unit/             # Vitest + React Testing Library — components, hooks, stores
    ├── integration/      # Feature-level tests (mocked API via MSW)
    └── e2e/               # Playwright tests against the built Electron app

apps/api/
└── tests/
    ├── unit/
    │   ├── expert_system/             # Rule evaluation correctness — critical test suite
    │   │   ├── test_condition_evaluator.py
    │   │   ├── test_rule_matcher.py
    │   │   └── test_explanation_builder.py
    │   ├── services/                  # GPA, graduation, report services
    │   └── data_processing/           # Parser/mapper/validator unit tests with sample Excel fixtures
    ├── integration/
    │   ├── test_api_students.py
    │   ├── test_api_rules.py
    │   └── test_api_recommendations.py
    ├── e2e/
    │   └── test_full_evaluation_flow.py   # Upload Excel -> Run engine -> Verify recommendations
    ├── fixtures/
    │   ├── sample_transcripts/        # .xlsx test files
    │   └── sample_rules.json          # Seed rule sets for engine tests
    └── conftest.py                    # Pytest fixtures: test DB session, test client, seeded data
```

### Why This Matters

The `expert_system` unit tests are the most critical suite in the project — since rules are dynamic/data-driven, tests must verify the engine's mechanics (operator correctness, conflict resolution, explanation completeness) against a fixed set of `sample_rules.json` and synthetic `StudentFactSheet`s, independent of whatever rules an Admin later creates in production. E2E tests then verify the full pipeline: Excel import → fact rebuild → engine run → explainable recommendation → AI rephrase → report PDF.

---

## 📦 Deployment / Build Structure

```text
acadexa/
├── .github/workflows/
│   ├── ci.yml                    # Lint + test (web, api) on every PR
│   ├── build-desktop.yml         # electron-builder matrix build (win/mac/linux)
│   └── release.yml               # Tag-triggered: build + publish to GitHub Releases (auto-update feed)
├── apps/desktop/build/
│   └── electron-builder.yml      # App ID, icons, NSIS/DMG/AppImage targets, publish config
├── apps/api/
│   ├── Dockerfile                # Backend container image (for cloud deployment option)
│   └── docker-compose.yml        # Local Postgres + API for development
├── docker-compose.yml            # Root compose: Supabase local stack + API + (optional) web dev server
└── scripts/
    ├── build-all.sh               # Builds web -> copies dist into desktop -> runs electron-builder
    ├── db-migrate.sh              # Runs Alembic migrations against target environment
    └── seed-demo.sh                # Seeds demo users, rules, students for grad-project demos
```

### Deployment Model

- **Development:** `apps/web` runs on Vite dev server; `apps/api` runs locally (Uvicorn) against a local/dev Supabase project; Electron loads the Vite dev URL with hot reload.
- **Production (Desktop-first):** `apps/web` is built to static assets and bundled inside the Electron app (`apps/desktop`); `apps/api` is either (a) bundled as a local sidecar process started by Electron's main process, or (b) hosted centrally (cloud FastAPI + Supabase) so multiple advisor workstations share one database — the `core/config.py` + `electronBridge` API-base-URL resolution supports both without code changes.
- **Auto-updates:** `electron-updater` (wired in `apps/desktop/src/main/services/update.service.ts`) checks the GitHub Releases feed published by `release.yml`.
- **CI/CD:** `ci.yml` runs `pytest`, `vitest`, type-checking, and linting on every PR (gatekeeping merges); `build-desktop.yml`/`release.yml` produce installable artifacts (`.exe`, `.dmg`, `.AppImage`) per platform.

---

## 🧪 Quick Testing Commands

```bash
# Backend unit tests
cd apps/api
pytest tests/unit -v

# Backend integration tests
pytest tests/integration -v

# Frontend tests
cd apps/web
npm run test

# E2E tests (Playwright)
npm run test:e2e
```

---

## 📦 Building for Production

```bash
# Build React app
cd apps/web
npm run build

# Build Electron desktop app (Windows .exe, macOS .dmg, Linux .AppImage)
cd apps/desktop
npm run dist

# Output location: apps/desktop/release/
```

---

## 🗺️ Project Roadmap

| Phase | Status | Description |
| :--- | :--- | :--- |
| ✅ Phase 1 | Completed | Project structure, monorepo setup, folder scaffolding |
| 🔄 Phase 2 | In Progress | Core CRUD + Authentication (Supabase) |
| 📅 Phase 3 | Planned | Expert System engine (fact builder, condition evaluator) |
| 📅 Phase 4 | Planned | Rule Editor UI + Recommendation display |
| 📅 Phase 5 | Planned | Excel import pipeline |
| 📅 Phase 6 | Planned | AI Assistant integration (read-only) |
| 📅 Phase 7 | Planned | Reporting & PDF export |
| 📅 Phase 8 | Planned | Auto-updater + Production release |

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

---

Made with ❤️ for Faculty of Specific Education — KSU
