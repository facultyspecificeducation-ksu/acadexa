// Responsibility:
// Tracks all open BrowserWindow instances, enforces single-instance lock, and exposes the active window reference for dialogs/printing.
//
// Layer: Electron Main Process - Windows
//
// Communication:
// Used by main/index.ts and by ipc handlers (file-handler, print-handler) that need the active BrowserWindow.

export {};

