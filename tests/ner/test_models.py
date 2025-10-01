from __future__ import annotations

from filtra.ner import (
    CanonicalEntity,
    EntityOccurrence,
    ExtractedEntityCollection,
    normalize_entities,
)


class FakeAliasMap:
    def canonicalize(self, text: str, language: str | None = None):
        canonical = text.strip().title()
        return canonical, [f"Mapped '{text}' to '{canonical}'"]


def test_entities_alias_reflects_canonical_entities() -> None:
    occurrence = EntityOccurrence(
        raw_text="python",
        canonical_text="python",
        category="skill",
        confidence=0.9,
        span=(0, 6),
        document_role="resume",
        document_display="resume.txt",
        source_language="en",
        context_snippet="python",
        ingestion_index=0,
    )
    canonical_entity = CanonicalEntity(
        text="Python",
        category="skill",
        top_confidence=0.9,
        occurrence_count=1,
        occurrences=(occurrence,),
        contexts=("python",),
        sources=("resume:resume.txt",),
        aliases=("python",),
    )
    collection = ExtractedEntityCollection(
        occurrences=(occurrence,),
        canonical_entities=(canonical_entity,),
    )

    assert collection.entities is collection.canonical_entities
    assert len(collection.entities) == 1


def test_normalize_entities_orders_by_ingestion_then_display() -> None:
    alias_map = FakeAliasMap()
    occurrences = (
        EntityOccurrence(
            raw_text="data platform",
            canonical_text="data platform",
            category="skill",
            confidence=0.7,
            span=(0, 13),
            document_role="resume",
            document_display="Resume",
            source_language="es",
            context_snippet="data platform",
            ingestion_index=0,
        ),
        EntityOccurrence(
            raw_text="Data Platform",
            canonical_text="Data Platform",
            category="skill",
            confidence=0.8,
            span=(20, 33),
            document_role="job",
            document_display="Job",
            source_language="en",
            context_snippet="Data Platform",
            ingestion_index=0,
        ),
        EntityOccurrence(
            raw_text="Machine Learning",
            canonical_text="Machine Learning",
            category="skill",
            confidence=0.6,
            span=(40, 56),
            document_role="resume",
            document_display="Resume",
            source_language="en",
            context_snippet="Machine Learning",
            ingestion_index=1,
        ),
    )
    collection = ExtractedEntityCollection(
        occurrences=occurrences,
        canonical_entities=(),
    )

    normalized = normalize_entities(collection, alias_map=alias_map, language_hint="es")

    grouped = {entity.text: entity for entity in normalized.canonical_entities}
    assert "Data Platform" in grouped
    data_platform = grouped["Data Platform"]
    assert data_platform.sources == ("job:Job", "resume:Resume")
    assert data_platform.occurrences[0].document_display == "Job"
    assert data_platform.occurrences[1].document_display == "Resume"
    indices = [occ.ingestion_index for occ in normalized.occurrences]
    assert indices == sorted(indices)

    machine_learning = grouped["Machine Learning"]
    assert machine_learning.occurrence_count == 1
    assert machine_learning.aliases == ("Machine Learning",)
