# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Performs schema/sanity checks on mapped rows before database write: duplicate student numbers, unknown course codes, invalid/missing grade values.
#
# Interaction:
# Used by data_processing/importer/import_service.py; its structured warnings/errors are returned to apps/web features/data-import/components/ImportPreviewTable.tsx.


