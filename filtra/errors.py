"""Domain-specific exception hierarchy for Filtra."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FiltraError(Exception):
    """Base exception for Filtra-specific errors with optional remediation text."""

    message: str
    remediation: str | None = None

    def __post_init__(self) -> None:  # pragma: no cover - dataclass validation hook
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class InputValidationError(FiltraError):
    """Raised when the CLI receives invalid or missing input."""


class PdfExtractionError(FiltraError):
    """Raised when resume/job description parsing fails."""


class NERModelError(FiltraError):
    """Raised when the NER pipeline encounters an unrecoverable issue."""


class LLMRequestError(FiltraError):
    """Raised when the LLM client call fails."""


class TimeoutExceededError(FiltraError):
    """Raised when orchestration exceeds its allotted execution time."""


__all__ = [
    "FiltraError",
    "InputValidationError",
    "PdfExtractionError",
    "NERModelError",
    "LLMRequestError",
    "TimeoutExceededError",
]
