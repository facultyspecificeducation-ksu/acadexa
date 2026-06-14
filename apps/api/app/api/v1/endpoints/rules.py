# Module: Backend - Endpoint
# Responsibility:
# Defines CRUD endpoints for Expert System rules: GET/POST/PUT /rules, PATCH /rules/{id}/activate, POST /rules/simulate.
#
# Interaction:
# Delegates to repositories/rule_repository.py for persistence and to expert_system/runner.py for the simulate action. Restricted to Admin/Developer roles.


