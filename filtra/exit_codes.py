"""Shared exit code definitions for Filtra CLI operations."""
from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Deterministic exit codes mandated by the PRD."""

    SUCCESS = 0
    UNEXPECTED_ERROR = 1
    INVALID_INPUT = 2
    PARSE_ERROR = 3
    NER_ERROR = 4
    LLM_ERROR = 5
    TIMEOUT = 6


__all__ = ["ExitCode"]
