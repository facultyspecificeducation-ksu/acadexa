// Responsibility:
// Defines a single const object/enum listing every IPC channel name used across the main process, preload bridge and renderer.
//
// Layer: Shared (Main / Preload)
//
// Communication:
// Imported by main/ipc/ipc-registry.ts and every preload/api/* module so channel-name typos become compile errors.

export {};

