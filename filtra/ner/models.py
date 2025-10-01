"""Dataclasses describing canonical entity structures for Filtra."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

EntityCategory = Literal["skill", "company", "title", "education", "location"]


@dataclass(frozen=True)
class EntityOccurrence:
    """Represents a single extracted entity span with document context."""

    raw_text: str
    canonical_text: str
    category: EntityCategory
    confidence: float
    span: Tuple[int, int]
    document_role: str
    document_display: str
    source_language: str
    context_snippet: str
    ingestion_index: int

    def __post_init__(self) -> None:  # pragma: no cover - simple normalization
        span_tuple = tuple(int(value) for value in self.span)
        object.__setattr__(self, "span", span_tuple)
        object.__setattr__(self, "document_role", self.document_role.strip())
        object.__setattr__(self, "document_display", self.document_display.strip())
        object.__setattr__(self, "context_snippet", self.context_snippet or "")


@dataclass(frozen=True)
class CanonicalEntity:
    """Canonical grouping of related occurrences after normalization."""

    text: str
    category: EntityCategory
    top_confidence: float
    occurrence_count: int
    occurrences: Tuple[EntityOccurrence, ...]
    contexts: Tuple[str, ...]
    sources: Tuple[str, ...]
    aliases: Tuple[str, ...]

    def __post_init__(self) -> None:  # pragma: no cover - simple normalization
        object.__setattr__(self, "occurrences", tuple(self.occurrences))
        object.__setattr__(self, "contexts", tuple(self.contexts))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "aliases", tuple(dict.fromkeys(self.aliases)))


@dataclass(frozen=True)
class ExtractedEntityCollection:
    """Aggregate container exposing occurrences and canonical entities."""

    occurrences: Tuple[EntityOccurrence, ...]
    canonical_entities: Tuple[CanonicalEntity, ...]
    language_profile: object | None = None
    normalization_log: Tuple[str, ...] = ()

    def __post_init__(self) -> None:  # pragma: no cover - simple normalization
        object.__setattr__(self, "occurrences", tuple(self.occurrences))
        object.__setattr__(self, "canonical_entities", tuple(self.canonical_entities))
        object.__setattr__(self, "normalization_log", tuple(self.normalization_log))

    @property
    def entities(self) -> Tuple[CanonicalEntity, ...]:
        """Backwards-compatible alias for canonical entities."""

        return self.canonical_entities


__all__ = [
    "EntityCategory",
    "EntityOccurrence",
    "CanonicalEntity",
    "ExtractedEntityCollection",
]
