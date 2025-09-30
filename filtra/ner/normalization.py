"""Normalization workflow for extracted entities."""
from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping

from filtra.configuration import AliasMap
from filtra.ner.pipeline import ExtractedEntity, ExtractedEntityCollection


def normalize_entities(
    collection: ExtractedEntityCollection,
    *,
    alias_map: AliasMap,
    language_hint: str | None = None,
) -> ExtractedEntityCollection:
    """Apply trimming, casefolding, alias mapping, and deduplication."""

    log = list(collection.normalization_log)
    deduped: dict[tuple[str, str], ExtractedEntity] = {}

    for entity in collection.entities:
        language = _resolve_language(
            language_hint,
            collection.language_profile,
            entity.source_language,
        )
        canonical_text, step_log = alias_map.canonicalize(entity.text, language=language)
        log.extend(_sanitize_log_entries(step_log))

        if not canonical_text:
            log.append("Skipped entity with empty canonical text after normalization.")
            continue

        key = (entity.category, canonical_text.casefold())
        normalised_entity = ExtractedEntity(
            text=canonical_text,
            category=entity.category,
            confidence=entity.confidence,
            span=entity.span,
            source_language=entity.source_language,
        )

        existing = deduped.get(key)
        if existing:
            current_descriptor = _entity_descriptor(entity.category, canonical_text)
            existing_descriptor = _entity_descriptor(existing.category, existing.text)
            if entity.confidence > existing.confidence:
                deduped[key] = normalised_entity
                log.append(
                    f"Deduplicated alias {existing_descriptor} "
                    f"in favour of {current_descriptor} based on confidence scores."
                )
            else:
                log.append(
                    f"Discarded duplicate alias {current_descriptor} "
                    f"because {existing_descriptor} has equal or higher confidence."
                )
            continue

        deduped[key] = normalised_entity

    sorted_entities = tuple(
        sorted(
            deduped.values(),
            key=lambda item: (item.category, item.text, item.span[0], item.span[1]),
        )
    )
    log.append(
        "Normalised "
        f"{len(collection.entities)} entities to "
        f"{len(sorted_entities)} canonical entries."
    )

    return ExtractedEntityCollection(
        entities=sorted_entities,
        language_profile=collection.language_profile,
        normalization_log=tuple(log),
        source_document_id=collection.source_document_id,
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







