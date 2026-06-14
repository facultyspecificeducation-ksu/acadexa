# Module: Backend - Services
# Responsibility:
# Implements login validation (password check via core/security.py) and session issuance/lookup, plus user/role management for admin.
#
# Interaction:
# Used by api/v1/endpoints/auth.py and admin.py. Uses models/user.py via SQLAlchemy session.


