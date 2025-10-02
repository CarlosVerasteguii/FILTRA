from __future__ import annotations

from filtra.ner.models import CanonicalEntity
from filtra.reporting import ReportEnvelope, ReportRenderOptions, render_entities_report


def _entity(
    *,
    text: str,
    category: str,
    contexts: tuple[str, ...],
    sources: tuple[str, ...],
    confidence: float = 0.95,
    matches: int = 1,
) -> CanonicalEntity:
    return CanonicalEntity(
        text=text,
        category=category,
        top_confidence=confidence,
        occurrence_count=matches,
        occurrences=(),
        contexts=contexts,
        sources=sources,
        aliases=(text,),
    )


def test_render_entities_report_default_layout() -> None:
    """Default layout renders skill and company tables with context."""

    envelope = ReportEnvelope(
        canonical_entities=(
            _entity(
                text="Python",
                category="skill",
                contexts=("Expert in Python development", "Python-focused projects"),
                sources=("resume:Resume.txt", "job_description:JD.txt"),
                confidence=0.98,
                matches=3,
            ),
            _entity(
                text="Filtra Technologies",
                category="company",
                contexts=("Worked at Filtra",),
                sources=("resume:Resume.txt",),
                confidence=0.88,
                matches=2,
            ),
        ),
        render_options=ReportRenderOptions(wide=False),
    )

    output = render_entities_report(envelope)

    assert "Canonical Entities Report" in output
    assert "Skills" in output
    assert "Companies" in output
    header_line = next(line for line in output.splitlines() if "ENTITY" in line)
    assert "MATCHES" in header_line
    assert "CONFIDENCE" in header_line
    assert "TOP CONTEXT" in header_line
    assert "Python" in output
    assert "Filtra Technologies" in output
    assert "Expert in Python development" in output
    assert "Tip: re-run with --wide" in output


def test_render_entities_report_empty_sections() -> None:
    """Placeholders appear when no entities are available for a section."""

    envelope = ReportEnvelope(
        canonical_entities=(),
        render_options=ReportRenderOptions(wide=False),
    )

    output = render_entities_report(envelope)

    assert "-- no skills extracted --" in output
    assert "-- no companies detected --" in output


def test_render_entities_report_wide_includes_sources() -> None:
    """Wide layout appends sources column with combined context details."""

    envelope = ReportEnvelope(
        canonical_entities=(
            _entity(
                text="Generative AI",
                category="skill",
                contexts=("Mentioned in resume", "Required in job"),
                sources=("resume:Resume.pdf", "job_description:JD.docx"),
            ),
        ),
        render_options=ReportRenderOptions(wide=True),
    )

    output = render_entities_report(envelope)

    assert "SOURCES" in output
    assert "resume:Resume.pdf" in output
    assert "job_description:" in output
    assert "Mentioned in resume" in output
    assert "Required in job" in output
    assert "Tip: re-run with --wide" not in output



def test_render_entities_report_sanitizes_non_ascii_characters() -> None:
    """Renderer coerces accented characters into ASCII for default layout."""

    envelope = ReportEnvelope(
        canonical_entities=(
            _entity(
                text="Développeur",
                category="skill",
                contexts=("Équipe d'intégration IA",),
                sources=("résumé:Résumé.pdf",),
            ),
        ),
        render_options=ReportRenderOptions(wide=False),
    )

    output = render_entities_report(envelope)

    assert "Developpeur" in output
    assert "Développeur" not in output
    assert "Equipe d'integration IA" in output
    assert all(ord(char) < 128 for char in output)
