// Responsibility:
// Exposes window.acadexa.print.* (printReport, exportPdf) by wrapping ipcRenderer.invoke calls to channels defined in shared/ipc-channels.ts.
//
// Layer: Electron Preload - API Surface
//
// Communication:
// Consumed by apps/web shared/lib/electronBridge.ts. Forwards requests to main/ipc/handlers/print-handler.ts.

export {};

