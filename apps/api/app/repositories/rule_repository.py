# Module: Backend - Repositories
# Responsibility:
# Raw SQLAlchemy queries for the rules table: list active rules ordered by priority, CRUD operations, versioning/audit updates.
#
# Interaction:
# Used by api/v1/endpoints/rules.py for CRUD and by expert_system/knowledge_base/loader.py for read-only loading of active rules.


