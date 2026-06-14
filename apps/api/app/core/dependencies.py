# Module: Backend - Core
# Responsibility:
# FastAPI dependency-injection helpers: get_db (DB session), get_current_user (resolves session -> user), and require_role(role) for RBAC enforcement on endpoints.
#
# Interaction:
# Imported by every module in api/v1/endpoints/*. require_role() enforces Developer/Admin/Academic Advisor permissions per endpoint.


