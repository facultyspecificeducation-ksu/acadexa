// Responsibility:
// Defines the Acadexa color palette (primary/secondary/status colors for recommendation priorities, warnings, etc.).
//
// Layer: Renderer - Theme
//
// Communication:
// Imported by theme/theme.ts. Status colors are reused by features/recommendations/components/RecommendationCard.tsx for priority badges.

export {};



// ---- Acadexa semantic color tokens (appended by migration script) ----
export const academicStatusColors = {
  good_standing: '#2e7d32',
  delayed:       '#f57f17',
  needs_support: '#e65100',
  probation:     '#c62828',
} as const;

export const riskLevelColors = {
  low:    '#2e7d32',
  medium: '#f57f17',
  high:   '#c62828',
} as const;

export const gpaBandColors = {
  excellent:  '#1b5e20',
  good:       '#00695c',
  acceptable: '#f57f17',
  weak:       '#e65100',
  probation:  '#c62828',
} as const;
