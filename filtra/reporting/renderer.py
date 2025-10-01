"""Rendering utilities for canonical entity reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from filtra.ner.models import CanonicalEntity

_ENTITY_LIMIT = 32
_CATEGORY_LIMIT = 12
_MATCHES_WIDTH = 7
_CONFIDENCE_WIDTH = 10
_SOURCES_LIMIT = 40


@dataclass(frozen=True)
class ReportRenderOptions:
    """Render-time switches influencing CLI layout."""

    quiet: bool = False
    wide: bool = False


@dataclass(frozen=True)
class ReportEnvelope:
    """Structured data needed to render the entities section."""

    canonical_entities: tuple[CanonicalEntity, ...]
    render_options: ReportRenderOptions

    @property
    def has_entities(self) -> bool:
        """Return True when canonical entities are available."""

        return bool(self.canonical_entities)


def render_entities_report(envelope: ReportEnvelope) -> str:
    """Render the canonical entities table respecting layout options."""

    entities = envelope.canonical_entities
    options = envelope.render_options

    if not entities:
        return (
            "Canonical Entities\n"
            "No canonical entities were extracted during this run."
        )

    rows = _build_rows(entities, wide=options.wide)
    header = _build_header(rows, wide=options.wide)

    lines = ["Canonical Entities", header.separator, header.header]
    lines.extend(rows)
    lines.append(header.separator)
    lines.append(f"Total canonical entities: {len(entities)}")
    if not options.wide:
        lines.append("Tip: re-run with --wide to include source columns.")

    return "\n".join(lines)


@dataclass(frozen=True)
class _Header:
    header: str
    separator: str


def _build_header(rows: Sequence[str], *, wide: bool) -> _Header:
    columns = ["Entity", "Category", "Matches", "Confidence"]
    widths = [
        _ENTITY_LIMIT,
        _CATEGORY_LIMIT,
        _MATCHES_WIDTH,
        _CONFIDENCE_WIDTH,
    ]

    if wide:
        columns.append("Sources")
        widths.append(_SOURCES_LIMIT)

    header_parts = []
    separator_parts = []
    for name, width in zip(columns, widths):
        padded = name.ljust(width)
        header_parts.append(padded)
        separator_parts.append("-" * width)

    header_line = " | ".join(header_parts)
    separator_line = "-+-".join(separator_parts)

    # Align separator length with data rows (rows already contain padding)
    if rows:
        line_length = len(rows[0])
        if len(header_line) < line_length:
            header_line = header_line.ljust(line_length)
        if len(separator_line) < line_length:
            separator_line = separator_line.ljust(line_length, "-")

    return _Header(header=header_line, separator=separator_line)


def _build_rows(entities: Iterable[CanonicalEntity], *, wide: bool) -> list[str]:
    rows: list[str] = []
    for entity in entities:
        columns = [
            _fit(entity.text, _ENTITY_LIMIT),
            _fit(entity.category.title(), _CATEGORY_LIMIT),
            str(entity.occurrence_count).rjust(_MATCHES_WIDTH),
            f"{entity.top_confidence:.2f}".rjust(_CONFIDENCE_WIDTH),
        ]
        if wide:
            sources = ", ".join(dict.fromkeys(_sanitize_source(value) for value in entity.sources))
            columns.append(_fit(sources, _SOURCES_LIMIT))

        rows.append(" | ".join(columns))
    return rows


def _fit(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text.ljust(limit)
    return f"{text[: max(0, limit - 3)]}..."


def _sanitize_source(value: str) -> str:
    if ":" not in value:
        return value
    role, display = value.split(":", 1)
    return f"{role}:{display.strip()}"


__all__ = [
    "ReportEnvelope",
    "ReportRenderOptions",
    "render_entities_report",
]
