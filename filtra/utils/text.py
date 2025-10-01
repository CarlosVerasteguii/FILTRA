"""Text transformation helpers for shared use across modules."""
from __future__ import annotations

from typing import Tuple


def build_context_snippet(text: str, span: Tuple[int, int], window: int = 40) -> str:
    """Return a +/- window-sized snippet around an entity span with ellipses when trimmed."""

    if window < 0:
        raise ValueError("window must be non-negative")

    text_length = len(text)
    start, end = span
    start = max(0, min(start, text_length))
    end = max(start, min(end, text_length))

    prefix_start = max(0, start - window)
    suffix_end = min(text_length, end + window)

    snippet = text[prefix_start:suffix_end]

    prefix = "..." if prefix_start > 0 else ""
    suffix = "..." if suffix_end < text_length else ""

    return f"{prefix}{snippet}{suffix}" if snippet else ""


__all__ = ["build_context_snippet"]
