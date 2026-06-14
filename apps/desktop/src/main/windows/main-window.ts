// Responsibility:
// Factory function that creates and configures the main BrowserWindow (size, webPreferences, contextIsolation enabled, nodeIntegration disabled, preload script path).
//
// Layer: Electron Main Process - Windows
//
// Communication:
// Used by main/index.ts. Points webPreferences.preload at the compiled src/preload/index.ts bundle.

export {};

