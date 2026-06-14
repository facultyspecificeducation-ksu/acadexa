// Responsibility:
// Application bootstrap. Creates the main BrowserWindow, loads the renderer (Vite dev server in dev, apps/web/dist in prod), registers IPC handlers via ipc-registry, sets up auto-updater and tray.
//
// Layer: Electron Main Process
//
// Communication:
// Calls windows/main-window.ts to create the window, ipc/ipc-registry.ts to wire IPC, and services/update.service.ts + services/tray.service.ts at startup.

export {};

