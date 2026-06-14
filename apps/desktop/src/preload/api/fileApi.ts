// Responsibility:
// Exposes window.acadexa.files.* (openExcel, saveFile, readFile) by wrapping ipcRenderer.invoke calls to channels defined in shared/ipc-channels.ts.
//
// Layer: Electron Preload - API Surface
//
// Communication:
// Consumed by apps/web shared/lib/electronBridge.ts. Forwards requests to main/ipc/handlers/file-handler.ts.

export {};

