// routes.config.ts
// Central route definitions for Acadexa.
// Each route is mapped to its page component and protected by RoleGuard where required.
// TODO: Replace placeholder lazy imports with real page components once implemented.

import React, { lazy } from 'react';

// ---- Auth ----
const LoginPage                = lazy(() => import('../pages/auth/LoginPage'));

// ---- Dashboard ----
const DashboardPage            = lazy(() => import('../pages/dashboard/DashboardPage'));

// ---- Students ----
const StudentsListPage         = lazy(() => import('../pages/students/StudentsListPage'));
const StudentProfilePage       = lazy(() => import('../pages/students/StudentProfilePage'));

// ---- Import ----
const ImportPage               = lazy(() => import('../pages/import/ImportPage'));

// ---- Academic Structure ----
const DepartmentsPage          = lazy(() => import('../pages/academic-structure/DepartmentsPage'));
const CurriculaPage            = lazy(() => import('../pages/academic-structure/CurriculaPage'));
const CurriculumDetailPage     = lazy(() => import('../pages/academic-structure/CurriculumDetailPage'));
const CoursesPage              = lazy(() => import('../pages/academic-structure/CoursesPage'));
const AcademicLoadRulesPage    = lazy(() => import('../pages/academic-structure/AcademicLoadRulesPage'));

// ---- Expert System ----
const InferenceRulesPage       = lazy(() => import('../pages/expert-system/InferenceRulesPage'));
const GradeScalePage           = lazy(() => import('../pages/expert-system/GradeScalePage'));

// ---- Reports ----
const StudentReportsPage       = lazy(() => import('../pages/reports/StudentReportsPage'));
const DepartmentAnalyticsPage  = lazy(() => import('../pages/reports/DepartmentAnalyticsPage'));

// ---- Notifications ----
const NotificationsPage        = lazy(() => import('../pages/notifications/NotificationsPage'));

// ---- Settings ----
const UsersRolesPage           = lazy(() => import('../pages/settings/UsersRolesPage'));
const AdvisorAssignmentsPage   = lazy(() => import('../pages/settings/AdvisorAssignmentsPage'));
const SystemSettingsPage       = lazy(() => import('../pages/settings/SystemSettingsPage'));

export interface RouteConfig {
  path: string;
  element: React.LazyExoticComponent<React.FC>;
  requiredRole?: 'admin' | 'academic_advisor';
  layout?: 'dashboard' | 'auth' | 'print';
}

export const routes: RouteConfig[] = [
  // Auth
  { path: '/login',                              element: LoginPage,               layout: 'auth' },

  // Dashboard
  { path: '/',                                   element: DashboardPage,           layout: 'dashboard' },
  { path: '/dashboard',                          element: DashboardPage,           layout: 'dashboard' },

  // Students
  { path: '/students',                           element: StudentsListPage,        layout: 'dashboard' },
  { path: '/students/:id',                       element: StudentProfilePage,      layout: 'dashboard' },

  // Import
  { path: '/import',                             element: ImportPage,              layout: 'dashboard' },
  { path: '/import/history',                     element: ImportPage,              layout: 'dashboard' },

  // Academic Structure (admin only)
  { path: '/academic-structure/departments',     element: DepartmentsPage,         layout: 'dashboard', requiredRole: 'admin' },
  { path: '/academic-structure/curricula',       element: CurriculaPage,           layout: 'dashboard', requiredRole: 'admin' },
  { path: '/academic-structure/curricula/:id',   element: CurriculumDetailPage,    layout: 'dashboard', requiredRole: 'admin' },
  { path: '/academic-structure/courses',         element: CoursesPage,             layout: 'dashboard', requiredRole: 'admin' },
  { path: '/academic-structure/rules',           element: AcademicLoadRulesPage,   layout: 'dashboard', requiredRole: 'admin' },

  // Expert System (admin only)
  { path: '/expert-system/inference',            element: InferenceRulesPage,      layout: 'dashboard', requiredRole: 'admin' },
  { path: '/expert-system/grade-scale',          element: GradeScalePage,          layout: 'dashboard', requiredRole: 'admin' },

  // Reports
  { path: '/reports/students',                   element: StudentReportsPage,      layout: 'dashboard' },
  { path: '/reports/departments',                element: DepartmentAnalyticsPage, layout: 'dashboard' },

  // Notifications
  { path: '/notifications',                      element: NotificationsPage,       layout: 'dashboard' },

  // Settings (admin only)
  { path: '/settings/users',                     element: UsersRolesPage,          layout: 'dashboard', requiredRole: 'admin' },
  { path: '/settings/advisors',                  element: AdvisorAssignmentsPage,  layout: 'dashboard', requiredRole: 'admin' },
  { path: '/settings/system',                    element: SystemSettingsPage,      layout: 'dashboard', requiredRole: 'admin' },
];

export default routes;
