from __future__ import annotations

from pathlib import Path

import pytest

from filtra.configuration import load_alias_map
from filtra.errors import InputValidationError
from filtra.ner import (
    EntityOccurrence,
    ExtractedEntityCollection,
    normalize_entities,
)


def test_normalize_entities_deduplicates_and_applies_aliases(tmp_path: Path) -> None:
    extra_alias_map = tmp_path / "alias-extra.yaml"
    extra_alias_map.write_text(
        """
aliases:
  Data Platform:
    - data-platform
locale_overrides:
  es:
    plataforma de datos: Data Platform
""".strip(),
        encoding="utf-8",
    )

    alias_map = load_alias_map([extra_alias_map])

    collection = ExtractedEntityCollection(
        occurrences=(
            EntityOccurrence(
                raw_text="  PyTorch  ",
                canonical_text="  PyTorch  ",
                category="skill",
                confidence=0.61,
                span=(0, 8),
                document_role="resume",
                document_display="resume.txt",
                source_language="en",
                context_snippet="...PyTorch...",
                ingestion_index=0,
            ),
            EntityOccurrence(
                raw_text="pytorch",
                canonical_text="pytorch",
                category="skill",
                confidence=0.74,
                span=(10, 18),
                document_role="job",
                document_display="job.txt",
                source_language="en",
                context_snippet="pytorch stack",
                ingestion_index=1,
            ),
            EntityOccurrence(
                raw_text="ingenieria de datos",
                canonical_text="ingenieria de datos",
                category="skill",
                confidence=0.92,
                span=(20, 40),
                document_role="resume",
                document_display="resume.txt",
                source_language="es",
                context_snippet="ingenieria de datos",
                ingestion_index=2,
            ),
            EntityOccurrence(
                raw_text="AWS",
                canonical_text="AWS",
                category="company",
                confidence=0.88,
                span=(41, 44),
                document_role="resume",
                document_display="resume.txt",
                source_language="en",
                context_snippet="AWS cloud",
                ingestion_index=3,
            ),
        ),
        canonical_entities=(),
        language_profile="es",
    )

    normalized = normalize_entities(collection, alias_map=alias_map)

    canonical_summary = [
        (
            entity.category,
            entity.text,
            entity.top_confidence,
            entity.occurrence_count,
            entity.aliases,
            entity.sources,
        )
        for entity in normalized.canonical_entities
    ]
    assert canonical_summary == [
        (
            "company",
            "Amazon Web Services",
            pytest.approx(0.88),
            1,
            ("AWS",),
            ("resume:resume.txt",),
        ),
        (
            "skill",
            "Data Engineering",
            pytest.approx(0.92),
            1,
            ("ingenieria de datos",),
            ("resume:resume.txt",),
        ),
        (
            "skill",
            "PyTorch",
            pytest.approx(0.74),
            2,
            ("  PyTorch  ", "pytorch"),
            ("resume:resume.txt", "job:job.txt"),
        ),
    ]

    assert [occ.canonical_text for occ in normalized.occurrences] == [
        "PyTorch",
        "PyTorch",
        "Data Engineering",
        "Amazon Web Services",
    ]

    log_message = " ".join(normalized.normalization_log)
    assert "Normalized 4 occurrences to 3 canonical entities" in log_message
    assert "Merged 2 aliases" in log_message
    assert "PyTorch" not in log_message


def test_load_alias_map_merges_additional_sources(tmp_path: Path) -> None:
    override_map = tmp_path / "alias-override.yaml"
    override_map.write_text(
        """
aliases:
  Data Science:
    - data-science
locale_overrides:
  en:
    ds: Data Science
""".strip(),
        encoding="utf-8",
    )

    alias_map = load_alias_map([override_map])

    details = alias_map.details()
    assert override_map.resolve() in details.sources
    assert details.canonical_count >= 4

    canonical, log = alias_map.canonicalize("data-science", language=None)
    assert canonical == "Data Science"
    assert any("Mapped alias" in entry for entry in log)

    canonical_en, log_en = alias_map.canonicalize("DS", language="en")
    assert canonical_en == "Data Science"
    assert any("locale override" in entry.lower() for entry in log_en)


def test_load_alias_map_rejects_canonical_collision(tmp_path: Path) -> None:
    conflict_map = tmp_path / "alias-canonical-conflict.yaml"
    conflict_map.write_text(
        """
aliases:
  python:
    - python
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError) as exc:
        load_alias_map([conflict_map])

    assert "conflicts" in str(exc.value).lower()


def test_load_alias_map_rejects_alias_collision(tmp_path: Path) -> None:
    conflict_map = tmp_path / "alias-entry-conflict.yaml"
    conflict_map.write_text(
        """
aliases:
  PyTorch:
    - python
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError) as exc:
        load_alias_map([conflict_map])

    assert "assigned" in str(exc.value).lower()
