# Module: Backend - Endpoint
# Responsibility:
# Defines GET /recommendations?student_id=... and POST /recommendations/evaluate/{student_id} to trigger a fresh inference run.
#
# Interaction:
# Delegates to expert_system/runner.run_evaluation() (via a service) and repositories/recommendation_repository.py for persistence/retrieval.


