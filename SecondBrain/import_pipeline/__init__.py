"""Einheitliche Import-Pipeline für lokale Dateien und Connectoren.

Gemeinsame ImportJob-Entität, ParserRegistry durchgängig, nachvollziehbares
Statusmodell, Duplicate Detection, Retry mit Dead Letter, Partial-Failure-
Handling, OCR_REQUIRED-Abbildung, Source Lineage und Import-Historie.

Statusmodell (models.ImportStatus):
    queued -> parsing -> classified -> chunked -> embedded -> indexed
    Terminal: indexed | failed | dead_letter | duplicate | ocr_required
    (duplicate und ocr_required ergänzen das Basismodell dokumentiert:
     duplicate = Inhalt bereits importiert; ocr_required = wartet auf OCR.)
"""

from .models import ImportJob, ImportStatus, TERMINAL_STATUSES
from .store import ImportJobStore
from .dedup import DuplicateDetector
from .pipeline import UnifiedImportPipeline
from .history import ImportHistory

__all__ = [
    "DuplicateDetector", "ImportHistory", "ImportJob", "ImportJobStore",
    "ImportStatus", "TERMINAL_STATUSES", "UnifiedImportPipeline",
]
