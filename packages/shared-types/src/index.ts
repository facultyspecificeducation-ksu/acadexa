// Responsibility:
// Re-exports all shared type modules (auth, student, rule, recommendation) for a single import surface.
//
// Layer: Shared Package - Types
//
// Communication:
// Imported by apps/web feature 'api' modules and apps/desktop shared types where DTO shapes must match apps/api/app/schemas.

export {};


// Re-exports after Step 2 migration – types now live in feature folders.
// Remove these re-exports once all consumers are updated.
export * from '../../../apps/web/src/features/auth/types/auth.types';
export * from '../../../apps/web/src/features/students/types/student.types';
export * from '../../../apps/web/src/features/recommendations/types/recommendation.types';
export * from '../../../apps/web/src/features/expert-system/types/rule.types';
