from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from filtra.errors import NERModelError
from filtra.exit_codes import ExitCode
from filtra.ner import (
    EntityOccurrence,
    ExtractedEntityCollection,
    extract_entities,
)
from filtra.orchestration.runner import run_pipeline


FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_extract_entities_spanish_fixture(tmp_path: Path) -> None:
    text = _load_fixture("resume_es.txt")
    cache_path = tmp_path / "cache"
    calls: dict[str, object] = {}

    def factory(model_id: str, path: Path | None):
        calls["model_id"] = model_id
        calls["cache_path"] = path

        def _pipeline(_: str) -> list[dict]:
            return [
                {
                    "entity_group": "ORG",
                    "score": 0.98,
                    "word": "Innovación Global",
                    "start": 70,
                    "end": 87,
                },
                {
                    "entity_group": "MISC",
                    "score": 0.87,
                    "word": "Integración continua",
                    "start": 100,
                    "end": 121,
                },
            ]

        return _pipeline

    collection = extract_entities(
        text=text,
        language_hint="es",
        model_id="custom/es-model",
        cache_path=cache_path,
        document_role="resume",
        document_display="resume_es.txt",
        pipeline_factory=factory,
    )

    assert calls["model_id"] == "custom/es-model"
    assert calls["cache_path"] == cache_path
    categories = {occ.category for occ in collection.occurrences}
    assert categories == {"company", "skill"}
    assert any("integraci" in occ.raw_text.lower() for occ in collection.occurrences)
    assert all(occ.source_language == "es" for occ in collection.occurrences)
    assert all(occ.document_role == "resume" for occ in collection.occurrences)
    assert all(len(occ.context_snippet) >= len(occ.raw_text) for occ in collection.occurrences)
    assert [occ.ingestion_index for occ in collection.occurrences] == list(range(len(collection.occurrences)))


@pytest.mark.integration
def test_extract_entities_smoke_multilingual_pipeline(tmp_path: Path) -> None:
    pytest.importorskip("transformers")
    if not os.getenv("FILTRA_ENABLE_SMOKE"):
        pytest.skip("Set FILTRA_ENABLE_SMOKE=1 to run smoke tests with the real NER pipeline.")

    text = _load_fixture("resume_es.txt")

    try:
        collection = extract_entities(
            text=text,
            language_hint="es",
            model_id=None,
            document_role="resume",
            document_display="resume_es.txt",
        )
    except NERModelError as exc:
        pytest.skip(f"NER pipeline unavailable: {exc}")

    assert len(collection.occurrences) >= 1
    assert all(occ.source_language == "es" for occ in collection.occurrences)
    assert any("ó" in occ.raw_text or "ñ" in occ.raw_text for occ in collection.occurrences)


def test_extract_entities_english_fixture() -> None:
    text = _load_fixture("resume_en.txt")
    received: dict[str, object] = {}

    def factory(model_id: str, path: Path | None):
        received["model_id"] = model_id
        received["cache_path"] = path

        def _pipeline(_: str) -> list[dict]:
            return [
                {
                    "entity_group": "ORG",
                    "score": 0.95,
                    "word": "Bright Labs",
                    "start": 64,
                    "end": 75,
                },
                {
                    "entity_group": "MISC",
                    "score": 0.92,
                    "word": "cloud architecture",
                    "start": 92,
                    "end": 110,
                },
            ]

        return _pipeline

    collection = extract_entities(
        text=text,
        language_hint="en",
        model_id="custom/en-model",
        document_role="resume",
        document_display="resume_en.txt",
        pipeline_factory=factory,
    )

    assert received["model_id"] == "custom/en-model"
    assert received["cache_path"] is None
    categories = {occ.category for occ in collection.occurrences}
    assert {"company", "skill"}.issubset(categories)
    assert len(collection.occurrences) >= 2
    assert all(occ.source_language == "en" for occ in collection.occurrences)


def test_run_pipeline_logs_cache_and_proxy_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    resume_path = tmp_path / "resume.txt"
    jd_path = tmp_path / "job.txt"
    resume_path.write_text(_load_fixture("resume_es.txt"), encoding="utf-8")
    jd_path.write_text(_load_fixture("resume_en.txt"), encoding="utf-8")

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.local:8080")
    monkeypatch.setenv("NO_PROXY", "localhost")
    monkeypatch.delenv("HTTP_PROXY", raising=False)

    cache_path = tmp_path / "filtra" / "models"

    def fake_extract_entities(**kwargs):
        assert kwargs["model_id"] == "custom-model"
        assert kwargs["cache_path"] == cache_path
        role = kwargs.get("document_role", "document")
        display = kwargs.get("document_display", "document")
        occurrences = (
            EntityOccurrence(
                raw_text=f"{role}-name",
                canonical_text=f"{role}-name",
                category="company",
                confidence=0.99,
                span=(0, len(str(role))),
                document_role=role,
                document_display=display,
                source_language="es",
                context_snippet=f"context for {role}",
                ingestion_index=0,
            ),
        )
        return ExtractedEntityCollection(
            occurrences=occurrences,
            canonical_entities=(),
            language_profile="es",
        )

    monkeypatch.setattr("filtra.orchestration.runner.extract_entities", fake_extract_entities)

    caplog.set_level(logging.INFO, logger="filtra.orchestration.runner")
    outcome = run_pipeline(resume_path=resume_path, jd_path=jd_path, ner_model="custom-model")

    assert outcome.exit_code == ExitCode.SUCCESS
    assert str(cache_path) in outcome.message
    assert "Normalised" in outcome.message
    assert "alias groups" in outcome.message

    runner_records = [record for record in caplog.records if record.name == "filtra.orchestration.runner"]
    assert any(record.__dict__.get("huggingface_cache") == str(cache_path) for record in runner_records)
    assert any(record.__dict__.get("proxy_https_proxy") is True for record in runner_records)
    assert any(record.__dict__.get("proxy_http_proxy") is False for record in runner_records)
    assert any(record.__dict__.get("proxy_no_proxy") is True for record in runner_records)
    assert any(getattr(record, "alias_map_groups", None) is not None for record in runner_records)
    assert any(getattr(record, "alias_map_aliases", None) is not None for record in runner_records)
    assert any(getattr(record, "document_role", None) == "resume" for record in runner_records)
    assert any(getattr(record, "document_role", None) == "job_description" for record in runner_records)
