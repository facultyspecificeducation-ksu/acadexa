// Responsibility:
// Preload entry point. Uses contextBridge.exposeInMainWorld('acadexa', ...) to attach a strictly-typed window.acadexa object assembled from src/preload/api/*.
//
// Layer: Electron Preload (Security Boundary)
//
// Communication:
// Runs with contextIsolation enabled. The renderer (apps/web) can ONLY reach Node/OS features through window.acadexa - never via require() or direct ipcRenderer access.

export {};

