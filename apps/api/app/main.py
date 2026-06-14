# Module: Backend - App Entry
# Responsibility:
# FastAPI application factory: creates the app instance, configures middleware (CORS, logging), and registers the v1 API router.
#
# Interaction:
# Routes incoming HTTP requests to api/v1/router.py. Reads configuration from core/config.py and initializes db/session.py on startup.


