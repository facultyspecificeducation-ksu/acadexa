// Responsibility:
// Defines and applies Content-Security-Policy headers for the renderer session to harden the desktop app against script injection.
//
// Layer: Electron Main Process - Security
//
// Communication:
// Applied in main/index.ts / windows/main-window.ts when configuring the BrowserWindow's session.webRequest.

export {};

