from __future__ import annotations

import os
import logging
from pathlib import Path

import pytest

from filtra.errors import NERModelError
from filtra.exit_codes import ExitCode
from filtra.ner import (
    ExtractedEntity,
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
        pipeline_factory=factory,
    )

    assert calls["model_id"] == "custom/es-model"
    assert calls["cache_path"] == cache_path
    categories = {entity.category for entity in collection.entities}
    assert categories == {"company", "skill"}
    assert any("Integración" in entity.text for entity in collection.entities)
    assert all(entity.source_language == "es" for entity in collection.entities)



@pytest.mark.integration
def test_extract_entities_smoke_multilingual_pipeline(tmp_path: Path) -> None:
    pytest.importorskip("transformers")
    if not os.getenv("FILTRA_ENABLE_SMOKE"):
        pytest.skip("Set FILTRA_ENABLE_SMOKE=1 to run smoke tests with the real NER pipeline.")

    text = _load_fixture("resume_es.txt")

    try:
        collection = extract_entities(text=text, language_hint="es", model_id=None)
    except NERModelError as exc:
        pytest.skip(f"NER pipeline unavailable: {exc}")

    assert len(collection.entities) >= 1
    assert all(entity.source_language == "es" for entity in collection.entities)
    assert any("ó" in entity.text or "ñ" in entity.text for entity in collection.entities)


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
        pipeline_factory=factory,
    )

    assert received["model_id"] == "custom/en-model"
    assert received["cache_path"] is None
    categories = {entity.category for entity in collection.entities}
    assert {"company", "skill"}.issubset(categories)
    assert len(collection.entities) >= 2
    assert all(entity.source_language == "en" for entity in collection.entities)


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
        return ExtractedEntityCollection(
            entities=(
                ExtractedEntity(
                    text="Bright Labs",
                    category="company",
                    confidence=0.99,
                    span=(0, 11),
                    source_language="es",
                ),
                ExtractedEntity(
                    text="Integración",
                    category="skill",
                    confidence=0.88,
                    span=(12, 23),
                    source_language="es",
                ),
            ),
            language_profile="es",
        )

    monkeypatch.setattr("filtra.orchestration.runner.extract_entities", fake_extract_entities)

    caplog.set_level(logging.INFO, logger="filtra.orchestration.runner")
    outcome = run_pipeline(resume_path=resume_path, jd_path=jd_path, ner_model="custom-model")

    assert outcome.exit_code == ExitCode.SUCCESS
    assert str(cache_path) in outcome.message

    runner_records = [record for record in caplog.records if record.name == "filtra.orchestration.runner"]
    assert any(record.__dict__.get("huggingface_cache") == str(cache_path) for record in runner_records)
    assert any(record.__dict__.get("proxy_https_proxy") is True for record in runner_records)
    assert any(record.__dict__.get("proxy_http_proxy") is False for record in runner_records)
    assert any(record.__dict__.get("proxy_no_proxy") is True for record in runner_records)
