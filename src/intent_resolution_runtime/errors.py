from __future__ import annotations


class IntentIRError(ValueError):
    """Base error for invalid Intent IR data."""


class ValidationError(IntentIRError):
    """Raised when an IR record violates its declared contract."""


class SerializationError(IntentIRError):
    """Raised when canonical JSON cannot be parsed or produced safely."""
