# Module: Backend - Models
# Responsibility:
# SQLAlchemy model for the recommendations table: student_id, rule_id, rule_name_snapshot, reason, evidence JSONB, explanation, priority, status, created_at.
#
# Interaction:
# Written by expert_system/actions/action_executor.py via repositories/recommendation_repository.py. Read by api/v1/endpoints/recommendations.py and ai/services/explanation_service.py.


