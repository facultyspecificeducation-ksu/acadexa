# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Maps raw parsed student rows from excel_parser.py into the Student DTO shape expected by schemas/student.py and models/student.py.
#
# Interaction:
# Used by data_processing/importer/import_service.py before validation and persistence.


