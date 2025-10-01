"""Normalization workflow for extracted entities."""
from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Iterable, Mapping

from filtra.configuration import AliasMap
from filtra.ner.models import CanonicalEntity, EntityOccurrence, ExtractedEntityCollection


def normalize_entities(
    collection: ExtractedEntityCollection,
    *,
    alias_map: AliasMap,
    language_hint: str | None = None,
) -> ExtractedEntityCollection:
    """Apply alias mapping and construct canonical entity aggregates."""

    log = list(collection.normalization_log)
    grouped: dict[tuple[str, str], list[EntityOccurrence]] = {}
    normalized_occurrences: list[EntityOccurrence] = []
    observed_documents: set[tuple[str, str]] = set()

    for occurrence in collection.occurrences:
        language = _resolve_language(
            language_hint,
            collection.language_profile,
            occurrence.source_language,
        )
        canonical_text, step_log = alias_map.canonicalize(
            occurrence.raw_text,
            language=language,
        )
        log.extend(_sanitize_log_entries(step_log))

        if not canonical_text:
            log.append("Skipped occurrence with empty canonical text after normalization.")
            continue

        normalized = replace(occurrence, canonical_text=canonical_text)
        key = (normalized.category, canonical_text.casefold())
        grouped.setdefault(key, []).append(normalized)
        normalized_occurrences.append(normalized)
        observed_documents.add((normalized.document_role, normalized.document_display))

    canonical_entities: list[CanonicalEntity] = []

    for (category, _), occurrences in grouped.items():
        ordered = sorted(
            occurrences,
            key=lambda item: (
                item.ingestion_index,
                item.document_display.lower(),
                item.raw_text.lower(),
            ),
        )
        canonical_label = ordered[0].canonical_text
        alias_values = tuple(dict.fromkeys(item.raw_text for item in ordered))
        descriptor = _entity_descriptor(category, canonical_label)

        if len(alias_values) > 1:
            log.append(
                "Merged "
                f"{len(alias_values)} aliases into {descriptor}"
            )

        canonical_entities.append(
            CanonicalEntity(
                text=canonical_label,
                category=category,
                top_confidence=max(item.confidence for item in ordered),
                occurrence_count=len(ordered),
                occurrences=tuple(ordered),
                contexts=tuple(item.context_snippet for item in ordered),
                sources=tuple(f"{item.document_role}:{item.document_display}" for item in ordered),
                aliases=alias_values,
            )
        )

    canonical_entities.sort(key=lambda entity: (entity.category, entity.text.casefold()))

    log.append(
        "Normalized "
        f"{len(collection.occurrences)} occurrences to "
        f"{len(canonical_entities)} canonical entities across "
        f"{len(observed_documents)} documents."
    )

    return ExtractedEntityCollection(
        occurrences=tuple(sorted(
            normalized_occurrences,
            key=lambda item: item.ingestion_index,
        )),
        canonical_entities=tuple(canonical_entities),
        language_profile=collection.language_profile,
        normalization_log=tuple(log),
    )


_QUOTED_VALUE_RE = re.compile(r"'([^']*)'")


def _mask_value(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"<redacted:{digest}>"


def _sanitize_log_entries(entries: Iterable[str]) -> Iterable[str]:
    for entry in entries:
        yield _QUOTED_VALUE_RE.sub(lambda match: f"'{_mask_value(match.group(1))}'", entry)


def _entity_descriptor(category: str, text: str) -> str:
    return f"{category}:{_mask_value(text)}"


def _resolve_language(
    hint: str | None,
    profile: object | None,
    entity_language: str | None,
) -> str | None:
    for candidate in _iter_language_candidates(hint, profile, entity_language):
        if candidate:
            normalized = candidate.strip().lower()
            if normalized:
                return normalized
    return None


def _iter_language_candidates(
    hint: str | None,
    profile: object | None,
    entity_language: str | None,
) -> Iterable[str | None]:
    yield hint

    if isinstance(profile, str):
        yield profile
    elif isinstance(profile, Mapping):
        for key in ("primary", "language", "code"):
            value = profile.get(key)
            if isinstance(value, str):
                yield value
                break
    elif profile is not None:
        for attr in ("primary", "language", "code"):
            value = getattr(profile, attr, None)
            if isinstance(value, str):
                yield value
                break

    yield entity_language


__all__ = ["normalize_entities"]
