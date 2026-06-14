// Responsibility:
// Lets an Admin/Developer pick a sample student and run the Expert System against a draft rule to preview resulting recommendations before activation.
//
// Layer: Renderer - Feature: expert-system / Components
//
// Communication:
// Calls a simulation endpoint on api/rules.api.ts which invokes apps/api expert_system.runner in a dry-run mode.

export {};

