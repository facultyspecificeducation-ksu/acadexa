# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Single transactional entry point for Excel import: orchestrates parsers/excel_parser.py -> mappers/* -> validators/import_validator.py -> persistence via repositories, within a DB transaction.
#
# Interaction:
# Called from api/v1/endpoints/data_import.py. On success, may call expert_system/runner.run_evaluation() for affected students and services/notification_service.py.


