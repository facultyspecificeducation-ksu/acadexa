// Responsibility:
// Wraps window.acadexa.* (exposed by apps/desktop preload) with safe fallbacks so the same apps/web codebase can run in a plain browser (web-only mode) without crashing when Electron APIs are absent.
//
// Layer: Renderer - Shared / Lib
//
// Communication:
// Used by features/data-import (file picking), features/reports (print/export), and features/notifications (desktop notifications).

export {};

