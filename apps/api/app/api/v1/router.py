# Module: Backend - API Router
# Responsibility:
# Aggregates all v1 endpoint routers (auth, students, academic_structure, courses, grades, rules, recommendations, reports, data_import, ai_assistant, notifications, admin) under a single APIRouter.
#
# Interaction:
# Included by app/main.py with the /api/v1 prefix. Each sub-router lives in api/v1/endpoints/*.


