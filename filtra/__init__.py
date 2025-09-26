"""Filtra CLI package."""
from __future__ import annotations

__all__ = ("__version__", "FiltraError")

__version__ = "0.1.0"


class FiltraError(Exception):
    """Base exception for Filtra-specific errors."""

