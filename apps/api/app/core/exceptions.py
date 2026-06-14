# Module: Backend - Core
# Responsibility:
# Defines custom exception classes (NotFoundError, ForbiddenError, ValidationError, ExpertSystemError) and FastAPI exception handlers that map them to HTTP responses.
#
# Interaction:
# Registered in main.py. Raised by services/*, expert_system/*, ai/* and data_processing/* and translated into consistent API error responses.


