# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Wraps the project's existing Python Excel parser as a service-layer module: given a file path/stream, returns raw structured rows for student info, courses and grades.
#
# Interaction:
# Used by data_processing/importer/import_service.py as the first step of the import pipeline; its raw output is passed to mappers/*.


