# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Maps raw parsed grade rows from excel_parser.py into the Grade DTO shape expected by schemas/student.py and models/grade.py.
#
# Interaction:
# Used by data_processing/importer/import_service.py before validation and persistence.


