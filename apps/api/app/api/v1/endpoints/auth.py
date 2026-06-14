# Module: Backend - Endpoint
# Responsibility:
# Defines POST /auth/login and GET /auth/me. Validates credentials via services/auth_service.py and issues a session.
#
# Interaction:
# Thin controller: validates schemas/auth.py DTOs, delegates to services/auth_service.py, returns SessionUser/TokenResponse.


