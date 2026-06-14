# Module: Backend - Services
# Responsibility:
# Implements deterministic GPA calculation (per-semester and cumulative) from grade_points and credit hours.
#
# Interaction:
# Used by services/student_service.py and exposed as a fact to expert_system via facts/fact_builder.py. This is a deterministic calculation, not a rule-engine decision.


