// Responsibility:
// Wires up electron-updater: checks the GitHub Releases feed published by .github/workflows/release.yml, downloads updates, and reports status.
//
// Layer: Electron Main Process - Services
//
// Communication:
// Used by ipc/handlers/update-handler.ts; status events are forwarded to the renderer via window.acadexa.updates.onStatus.

export {};

