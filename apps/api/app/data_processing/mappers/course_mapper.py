# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Maps raw parsed course rows from excel_parser.py into the Course DTO shape expected by schemas/course.py and models/course.py.
#
# Interaction:
# Used by data_processing/importer/import_service.py before validation and persistence.


