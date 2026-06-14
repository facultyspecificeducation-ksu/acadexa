# Module: Backend - Endpoint
# Responsibility:
# Defines CRUD/list endpoints for students: GET /students, GET /students/{id}, PATCH /students/{id}.
#
# Interaction:
# Delegates to services/student_service.py -> repositories/student_repository.py. Role-restricted via core/dependencies.require_role for Admin/Academic Advisor.


