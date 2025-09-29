"""Utilities for priming and executing the Hugging Face NER pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal, Sequence

from filtra.errors import NERModelError

logger = logging.getLogger("filtra.ner.pipeline")

DEFAULT_MODEL_ID = "Davlan/bert-base-multilingual-cased-ner-hrl"

EntityCategory = Literal["skill", "company", "title", "education", "location"]

_ENTITY_GROUP_MAPPING: dict[str, EntityCategory] = {
    "ORG": "company",
    "COMPANY": "company",
    "PER": "title",
    "PERSON": "title",
    "LOC": "location",
    "LOCATION": "location",
    "MISC": "skill",
    "SKILL": "skill",
    "JOB": "title",
    "TITLE": "title",
    "EDU": "education",
    "EDUCATION": "education",
}


@dataclass(frozen=True)
class ExtractedEntity:
    """Structured representation of a single NER entity."""

    text: str
    category: EntityCategory
    confidence: float
    span: tuple[int, int]
    source_language: str


@dataclass(frozen=True)
class ExtractedEntityCollection:
    """Collection wrapper providing future hooks for normalization metadata."""

    entities: tuple[ExtractedEntity, ...]
    language_profile: object | None = None
    normalization_log: tuple[str, ...] = ()
    source_document_id: str | None = None


def extract_entities(
    *,
    text: str,
    language_hint: str | None = None,
    model_id: str | None = None,
    cache_path: Path | None = None,
    pipeline_factory: Callable[[str, Path | None], Callable[[str], Sequence[dict]]]
    | None = None,
) -> ExtractedEntityCollection:
    """Run the multilingual NER pipeline and return structured entities."""

    resolved_model = (model_id or DEFAULT_MODEL_ID).strip()
    if not resolved_model:
        raise NERModelError(
            message="NER model identifier cannot be empty.",
            remediation="Provide a valid Hugging Face model id such as Davlan/bert-base-multilingual-cased-ner-hrl.",
        )

    logger.info(
        "Loading NER pipeline",
        extra={"model_id": resolved_model, "cache_path": str(cache_path) if cache_path else None},
    )

    factory = pipeline_factory or _build_pipeline
    pipeline = factory(resolved_model, cache_path)

    try:
        raw_results = pipeline(text)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise NERModelError(
            message="Failed to execute the NER pipeline.",
            remediation="Retry after verifying the model cache and proxy settings.",
        ) from exc

    entities = tuple(_convert_predictions(raw_results, language_hint))

    return ExtractedEntityCollection(
        entities=entities,
        language_profile=language_hint,
    )


def warm_cache(*, cache_path: Path, model_id: str = DEFAULT_MODEL_ID) -> None:
    """Ensure the multilingual NER model weights are present in the local cache."""

    try:
        from transformers import AutoModelForTokenClassification, AutoTokenizer
    except ImportError as exc:  # pragma: no cover - dependency should be present
        raise NERModelError(
            message="Transformers dependency is missing; cannot warm the NER cache.",
            remediation="Install project dependencies with 'pip install -r requirements.txt'.",
        ) from exc

    try:
        cache_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise NERModelError(
            message=f"Unable to create Hugging Face cache directory at {cache_path}.",
            remediation="Verify filesystem permissions or override the cache path via TRANSFORMERS_CACHE.",
        ) from exc

    try:
        _prefetch_artifacts(
            AutoModelForTokenClassification=AutoModelForTokenClassification,
            AutoTokenizer=AutoTokenizer,
            model_id=model_id,
            cache_dir=cache_path,
        )
    except Exception as exc:  # pragma: no cover - exercised via mocks in tests
        raise NERModelError(
            message=f"Failed to prefetch NER model '{model_id}'.",
            remediation="Check internet connectivity or rerun warm-up once proxies are configured.",
        ) from exc


def _build_pipeline(model_id: str, cache_path: Path | None) -> Callable[[str], Sequence[dict]]:
    """Instantiate a transformers pipeline for entity extraction."""

    try:
        from transformers import pipeline as hf_pipeline
    except ImportError as exc:  # pragma: no cover - dependency should be present
        raise NERModelError(
            message="Transformers dependency is missing; cannot load the NER pipeline.",
            remediation="Install project dependencies with 'pip install -r requirements.txt'.",
        ) from exc

    pipeline_kwargs = {
        "task": "ner",
        "model": model_id,
        "tokenizer": model_id,
        "device": -1,
        "aggregation_strategy": "simple",
    }

    if cache_path is not None:
        cache_dir = str(cache_path)
        pipeline_kwargs["model_kwargs"] = {"cache_dir": cache_dir}
        pipeline_kwargs["tokenizer_kwargs"] = {"cache_dir": cache_dir}

    try:
        return hf_pipeline(**pipeline_kwargs)
    except Exception as exc:  # pragma: no cover - exercised via mocks in tests
        raise NERModelError(
            message=f"Failed to load NER model '{model_id}'.",
            remediation="Verify the model identifier or prefetch the cache with 'filtra warm-up'.",
        ) from exc


def _prefetch_artifacts(
    *,
    AutoModelForTokenClassification,
    AutoTokenizer,
    model_id: str,
    cache_dir: Path,
) -> None:
    """Download model artefacts into the cache directory."""

    AutoTokenizer.from_pretrained(model_id, cache_dir=str(cache_dir))
    AutoModelForTokenClassification.from_pretrained(model_id, cache_dir=str(cache_dir))


def _convert_predictions(
    predictions: Iterable[dict], language_hint: str | None
) -> Iterable[ExtractedEntity]:
    """Normalise raw pipeline output into ExtractedEntity instances."""

    language = (language_hint or "und").lower()
    entities: list[ExtractedEntity] = []

    for item in predictions:
        if not isinstance(item, dict):
            continue

        raw_group = str(item.get("entity_group") or item.get("entity") or "").upper()
        category = _ENTITY_GROUP_MAPPING.get(raw_group, "skill")

        word = item.get("word") or item.get("text") or ""
        text = word.replace("##", "")
        start = int(item.get("start", 0))
        end = int(item.get("end", start))
        confidence = float(item.get("score", 0.0))

        entities.append(
            ExtractedEntity(
                text=text,
                category=category,
                confidence=confidence,
                span=(start, end),
                source_language=language,
            )
        )

    entities.sort(key=lambda entity: entity.span)
    return entities


__all__ = [
    "DEFAULT_MODEL_ID",
    "EntityCategory",
    "ExtractedEntity",
    "ExtractedEntityCollection",
    "extract_entities",
    "warm_cache",
]
