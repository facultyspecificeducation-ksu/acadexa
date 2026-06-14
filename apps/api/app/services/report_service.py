# Module: Backend - Services
# Responsibility:
# Assembles academic analysis, student progress and recommendation reports by combining student_service, gpa_service, graduation_service and recommendation data, optionally adding an AI narrative.
#
# Interaction:
# Used by api/v1/endpoints/reports.py. Calls ai/services/summary_service.py for the narrative section only - all figures/decisions come from deterministic services and expert_system.


