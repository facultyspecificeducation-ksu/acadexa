# Module: Backend - Models
# Responsibility:
# SQLAlchemy model for the rules table (the Expert System Knowledge Base): name, category, description, priority, conditions/actions JSONB, explanation_template, is_active, version, audit fields.
#
# Interaction:
# Read by expert_system/knowledge_base/loader.py. Written via repositories/rule_repository.py from api/v1/endpoints/rules.py (Admin/Developer only).


