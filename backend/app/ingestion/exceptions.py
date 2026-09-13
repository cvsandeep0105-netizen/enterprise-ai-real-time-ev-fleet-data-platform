class IngestionError(Exception):
    """Base exception for ingestion failures."""


class IngestionValidationError(IngestionError):
    """Raised when an ingestion payload violates the ingestion contract."""
