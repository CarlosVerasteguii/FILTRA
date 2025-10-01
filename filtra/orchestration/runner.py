"""Execution orchestrator for Filtra CLI commands."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence

from filtra.configuration import AliasMapDetails, load_alias_map
from filtra.errors import (
    FiltraError,
    InputValidationError,
    LLMRequestError,
    NERModelError,
    PdfExtractionError,
    TimeoutExceededError,
)
from filtra.ner import (
    EntityOccurrence,
    ExtractedEntityCollection,
    extract_entities,
    normalize_entities,
)
from filtra.orchestration.diagnostics import get_proxy_environment, resolve_cache_directory
from filtra.exit_codes import ExitCode
from filtra.ingestion import extract_text as extract_pdf_text
from filtra.reporting import ReportEnvelope, ReportRenderOptions
from filtra.utils import LoadedDocument, load_text_document

logger = logging.getLogger("filtra.orchestration.runner")


@dataclass(frozen=True)
class ExecutionOutcome:
    """Result of invoking the orchestration pipeline."""

    exit_code: ExitCode
    status: str
    message: str | None = None
    remediation: str | None = None
    report: ReportEnvelope | None = None


_ERROR_MAPPINGS: tuple[
    tuple[type[FiltraError], ExitCode, str, str | None],
    ...,
] = (
    (
        InputValidationError,
        ExitCode.INVALID_INPUT,
        "Input validation failed.",
        "Double-check resume and job description paths and file permissions.",
    ),
    (
        PdfExtractionError,
        ExitCode.PARSE_ERROR,
        "Failed to parse supplied documents.",
        "Ensure the resume and job description are readable PDFs or UTF-8 text.",
    ),
    (
        NERModelError,
        ExitCode.NER_ERROR,
        "Entity extraction failed while loading the NER model.",
        "Clear the Hugging Face cache and rerun `filtra warm-up` to rebuild weights.",
    ),
    (
        LLMRequestError,
        ExitCode.LLM_ERROR,
        "The language model gateway reported an error.",
        "Set the OPENROUTER_API_KEY environment variable and verify proxy configuration.",
    ),
    (
        TimeoutExceededError,
        ExitCode.TIMEOUT,
        "Pipeline execution timed out.",
        "Retry with a stable network connection or increase the configured timeout.",
    ),
)


def run_pipeline(
    resume_path: Path,
    jd_path: Path,
    *,
    ner_model: str,
    alias_map_paths: Sequence[Path] | None = None,
    quiet: bool = False,
    wide: bool = False,
) -> ExecutionOutcome:
    """Execute the evaluation orchestration lifecycle."""

    try:
        resume_doc = _load_document(resume_path, description="resume")
        jd_doc = _load_document(jd_path, description="job description")
        normalized_entities, cache_path, alias_details, raw_count = _perform_run(
            resume_doc=resume_doc,
            jd_doc=jd_doc,
            ner_model=ner_model,
            alias_map_paths=alias_map_paths,
        )
    except TimeoutExceededError as error:
        return handle_domain_error(error)
    except FiltraError as error:
        return handle_domain_error(error)
    except TimeoutError as error:  # pragma: no cover - safety net
        return handle_domain_error(
            TimeoutExceededError(
                message=str(error) or "Processing timed out while executing the pipeline.",
                remediation=(
                    "Retry with a stable network connection or increase the configured timeout."
                ),
            )
        )
    except Exception as error:  # pragma: no cover - defensive
        logger.exception("Unexpected error occurred during orchestration.")
        remediation = "Re-run with `--debug` enabled and inspect logs for details before retrying."
        return ExecutionOutcome(
            exit_code=ExitCode.UNEXPECTED_ERROR,
            status="failure",
            message=str(error) or "An unexpected error occurred during the evaluation run.",
            remediation=remediation,
        )

    summary = [
        (
            f"Resume {resume_doc.display_name} decoded as {resume_doc.display_encoding} "
            f"({len(resume_doc.text)} characters)."
        ),
        (
            f"Job description {jd_doc.display_name} decoded as {jd_doc.display_encoding} "
            f"({len(jd_doc.text)} characters)."
        ),
        (
            f"Extracted {raw_count} entities using {ner_model} "
            f"(cache {cache_path})."
        ),
        (
            "Normalised {canonical} canonical entities via {groups} alias groups "
            "({aliases} aliases; overrides: {locales})."
        ).format(
            canonical=len(normalized_entities.canonical_entities),
            groups=alias_details.canonical_count,
            aliases=alias_details.alias_count,
            locales=", ".join(alias_details.locale_codes or ("none",)),
        ),
        "Pipeline execution is not yet implemented in this scaffold.",
    ]

    report = ReportEnvelope(
        canonical_entities=normalized_entities.canonical_entities,
        render_options=ReportRenderOptions(quiet=quiet, wide=wide),
    )

    return ExecutionOutcome(
        exit_code=ExitCode.SUCCESS,
        status="success",
        message="\n".join(summary),
        report=report,
    )


def _load_document(path: Path, *, description: str) -> LoadedDocument:
    """Load a resume or job description, supporting both PDF and text formats."""

    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path, description=description)
    return load_text_document(path, description)



def _perform_run(
    *,
    resume_doc: LoadedDocument,
    jd_doc: LoadedDocument,
    ner_model: str,
    alias_map_paths: Sequence[Path] | None,
) -> tuple[ExtractedEntityCollection, Path, AliasMapDetails, int]:
    """Actual orchestration logic placeholder until the pipeline is wired in."""

    logger.info(
        "Starting evaluation run",
        extra={
            "resume": resume_doc.display_name,
            "jd": jd_doc.display_name,
            "ner_model": ner_model,
        },
    )
    logger.info(
        "Loaded documents",
        extra={
            "resume_encoding": resume_doc.display_encoding,
            "jd_encoding": jd_doc.display_encoding,
            "resume_chars": len(resume_doc.text),
            "jd_chars": len(jd_doc.text),
        },
    )

    cache_path = resolve_cache_directory()
    logger.info(
        "Resolved Hugging Face cache path",
        extra={"huggingface_cache": str(cache_path)},
    )

    proxy_environment = get_proxy_environment()
    logger.info(
        "Proxy environment detected",
        extra={f"proxy_{name.lower()}": bool(value) for name, value in proxy_environment.items()},
    )

    documents = (
        ("resume", resume_doc),
        ("job_description", jd_doc),
    )

    per_document: list[ExtractedEntityCollection] = []
    total_occurrences = 0
    language_profiles: list[object] = []

    for role, document in documents:
        extracted = extract_entities(
            text=document.text,
            language_hint=None,
            model_id=ner_model,
            cache_path=cache_path,
            document_role=role,
            document_display=document.display_name,
        )
        per_document.append(extracted)
        total_occurrences += len(extracted.occurrences)
        if extracted.language_profile is not None:
            language_profiles.append(extracted.language_profile)
        logger.info(
            "Extracted entities",
            extra={
                "document_role": role,
                "document_display": document.display_name,
                "entity_count": len(extracted.occurrences),
                "entity_categories": sorted({occ.category for occ in extracted.occurrences}),
            },
        )

    merged_occurrences: list[EntityOccurrence] = []
    for collection in per_document:
        ordered = sorted(collection.occurrences, key=lambda occ: occ.ingestion_index)
        merged_occurrences.extend(ordered)

    reassigned_occurrences = [
        replace(occurrence, ingestion_index=index)
        for index, occurrence in enumerate(merged_occurrences)
    ]

    language_profile = next((profile for profile in language_profiles if profile is not None), None)
    language_hint = language_profile if isinstance(language_profile, str) else None

    merged_collection = ExtractedEntityCollection(
        occurrences=tuple(reassigned_occurrences),
        canonical_entities=(),
        language_profile=language_profile,
    )

    alias_map = load_alias_map(alias_map_paths)
    alias_details = alias_map.details()
    logger.info(
        "Loaded alias map",
        extra={
            "alias_map_sources": [str(path) for path in alias_details.sources],
            "alias_map_groups": alias_details.canonical_count,
            "alias_map_aliases": alias_details.alias_count,
            "alias_map_locales": alias_details.locale_codes,
        },
    )

    normalized = normalize_entities(merged_collection, alias_map=alias_map, language_hint=language_hint)
    logger.info(
        "Normalised entities",
        extra={
            "raw_entity_count": total_occurrences,
            "canonical_entity_count": len(normalized.canonical_entities),
        },
    )

    logger.info("Pipeline execution is not yet implemented in this scaffold.")
    return normalized, cache_path, alias_details, total_occurrences

def handle_domain_error(error: FiltraError) -> ExecutionOutcome:
    """Translate a domain error into an execution outcome and log remediation hints."""

    exit_code, default_message, default_remediation = _map_error(error)
    message = error.message or default_message
    remediation = error.remediation or default_remediation

    logger.error(message, extra={"exit_code": int(exit_code)})
    if remediation:
        logger.error("Remediation: %s", remediation)

    return ExecutionOutcome(
        exit_code=exit_code,
        status="failure",
        message=message,
        remediation=remediation,
    )


def _map_error(error: FiltraError) -> tuple[ExitCode, str, str | None]:
    """Match an error instance to its configured exit code and remediation."""

    for error_type, exit_code, message, remediation in _ERROR_MAPPINGS:
        if isinstance(error, error_type):
            return exit_code, message, remediation

    return (
        ExitCode.UNEXPECTED_ERROR,
        "An unexpected error occurred during the evaluation run.",
        "Enable debug logging and retry. If the issue persists, open a bug ticket with the logs.",
    )


__all__ = ["ExecutionOutcome", "handle_domain_error", "run_pipeline"]
