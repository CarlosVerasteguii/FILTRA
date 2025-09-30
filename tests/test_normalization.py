from __future__ import annotations

from pathlib import Path

import pytest

from filtra.configuration import load_alias_map
from filtra.errors import InputValidationError
from filtra.ner import ExtractedEntity, ExtractedEntityCollection, normalize_entities


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
        entities=(
            ExtractedEntity(
                text="  PyTorch  ",
                category="skill",
                confidence=0.61,
                span=(0, 8),
                source_language="en",
            ),
            ExtractedEntity(
                text="pytorch",
                category="skill",
                confidence=0.74,
                span=(10, 18),
                source_language="en",
            ),
            ExtractedEntity(
                text="ingenieria de datos",
                category="skill",
                confidence=0.92,
                span=(20, 40),
                source_language="es",
            ),
            ExtractedEntity(
                text="AWS",
                category="company",
                confidence=0.88,
                span=(41, 44),
                source_language="en",
            ),
        ),
        language_profile="es",
    )

    normalized = normalize_entities(collection, alias_map=alias_map)

    texts_by_category = [
        (entity.category, entity.text, entity.confidence)
        for entity in normalized.entities
    ]
    assert texts_by_category == [
        ("company", "Amazon Web Services", pytest.approx(0.88)),
        ("skill", "Data Engineering", pytest.approx(0.92)),
        ("skill", "PyTorch", pytest.approx(0.74)),
    ]

    combined_log = " ".join(normalized.normalization_log)
    assert "Deduplicated alias" in combined_log
    assert "Applied locale override" in combined_log
    assert "PyTorch" not in combined_log

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




