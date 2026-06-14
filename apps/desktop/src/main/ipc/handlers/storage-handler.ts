// Responsibility:
// Handles local key/value storage via electron-store for small, non-academic UI preferences (window bounds, last selected language, last opened file path).
//
// Layer: Electron Main Process - IPC Handler
//
// Communication:
// Registered in ipc/ipc-registry.ts. Invoked from the renderer for local persisted preferences, separate from academic data which always lives in apps/api/Postgres.

export {};

