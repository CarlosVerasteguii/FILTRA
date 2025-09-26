"""Utilities for priming the Hugging Face NER pipeline cache."""
from __future__ import annotations

from pathlib import Path

from filtra.errors import NERModelError

DEFAULT_MODEL_ID = "Davlan/bert-base-multilingual-cased-ner-hrl"


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


__all__ = ["DEFAULT_MODEL_ID", "warm_cache"]
