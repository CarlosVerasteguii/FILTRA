"""Rendering utilities for canonical entity reports."""
from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import Iterable, Mapping, Sequence

from filtra.ner.models import CanonicalEntity

_ENTITY_WIDTH = 32
_MATCHES_WIDTH = 7
_CONFIDENCE_WIDTH = 10
_CONTEXT_WIDTH = 45
_WIDE_CONTEXT_WIDTH = 40
_SOURCES_WIDTH = 60
_SECTION_ORDER = ("skill", "company")
_SECTION_PLACEHOLDERS = {
    "skill": "-- no skills extracted --",
    "company": "-- no companies detected --",
}
_SECTION_DEFAULT_LABELS = {
    "skill": "Skills",
    "company": "Companies",
}
_TITLE_KEY = "entities.title"
_TITLE_DEFAULT = "Canonical Entities Report"


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
    language_profile: object | None = None

    @property
    def has_entities(self) -> bool:
        """Return True when canonical entities are available."""

        return bool(self.canonical_entities)


def render_entities_report(envelope: ReportEnvelope) -> str:
    """Render the canonical entities tables respecting layout options."""

    entities = envelope.canonical_entities
    options = envelope.render_options
    language_profile = envelope.language_profile

    groups = {category: [] for category in _SECTION_ORDER}
    for entity in entities:
        if entity.category in groups:
            groups[entity.category].append(entity)

    lines: list[str] = []
    lines.append(_resolve_label(language_profile, _TITLE_KEY, _TITLE_DEFAULT))

    for category in _SECTION_ORDER:
        lines.append("")
        section_label = _resolve_label(
            language_profile,
            f"entities.{category}",
            _SECTION_DEFAULT_LABELS[category],
        )
        lines.append(section_label)

        table_lines = _build_table(
            groups.get(category, ()),
            placeholder=_SECTION_PLACEHOLDERS[category],
            wide=options.wide,
        )
        lines.extend(table_lines)

    if not options.wide:
        lines.append("")
        lines.append("Tip: re-run with --wide to include source columns.")

    return "\n".join(line for line in lines if line is not None)


def _build_table(
    entities: Sequence[CanonicalEntity],
    *,
    placeholder: str,
    wide: bool,
) -> list[str]:
    columns = _table_columns(wide=wide)
    header_line = _format_header(columns)
    separator_line = _format_separator(columns)

    rows = [_format_row(entity, columns, wide=wide) for entity in entities]
    if not rows:
        rows = [_placeholder_row(columns, placeholder)]

    return [header_line, separator_line, *rows]


def _table_columns(*, wide: bool) -> Sequence[tuple[str, int, str]]:
    context_width = _WIDE_CONTEXT_WIDTH if wide else _CONTEXT_WIDTH
    columns: list[tuple[str, int, str]] = [
        ("Entity", _ENTITY_WIDTH, "left"),
        ("Matches", _MATCHES_WIDTH, "right"),
        ("Confidence", _CONFIDENCE_WIDTH, "right"),
        ("Top Context", context_width, "left"),
    ]
    if wide:
        columns.append(("Sources", _SOURCES_WIDTH, "left"))
    return columns


def _format_header(columns: Sequence[tuple[str, int, str]]) -> str:
    return " | ".join(_pad_text(title.upper(), width) for title, width, _ in columns)


def _format_separator(columns: Sequence[tuple[str, int, str]]) -> str:
    return "-+-".join("-" * width for _, width, _ in columns)


def _format_row(
    entity: CanonicalEntity,
    columns: Sequence[tuple[str, int, str]],
    *,
    wide: bool,
) -> str:
    items: list[str] = []
    column_map = {
        "Entity": entity.text,
        "Matches": str(entity.occurrence_count),
        "Confidence": f"{entity.top_confidence:.2f}",
        "Top Context": _compose_contexts(entity.contexts),
        "Sources": _compose_sources(entity) if wide else "",
    }

    for title, width, alignment in columns:
        value = column_map.get(title, "")
        items.append(_pad_text(value, width, align=alignment))

    return " | ".join(items)


def _placeholder_row(
    columns: Sequence[tuple[str, int, str]],
    placeholder: str,
) -> str:
    padded_first = _pad_text(placeholder, columns[0][1], align=columns[0][2])
    remainder = [
        _pad_text("", width, align=align)
        for _, width, align in columns[1:]
    ]
    return " | ".join([padded_first, *remainder])


def _pad_text(value: str, width: int, *, align: str = "left") -> str:
    text = _truncate(_normalize_text(value), width)
    if align == "right":
        return text.rjust(width)
    if align == "center":
        return text.center(width)
    return text.ljust(width)


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return value[: width - 3] + "..."


def _normalize_text(value: str) -> str:
    text = str(value)
    collapsed = " ".join(text.split())
    normalized = unicodedata.normalize("NFKD", collapsed)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text


def _compose_contexts(contexts: Iterable[str]) -> str:
    ordered = list(dict.fromkeys(_normalize_text(context) for context in contexts if context))
    return "; ".join(filter(None, ordered)) or "--"


def _compose_sources(entity: CanonicalEntity) -> str:
    pairs: list[str] = []
    contexts = list(entity.contexts)
    for index, source in enumerate(entity.sources):
        context = contexts[index] if index < len(contexts) else ""
        display = _normalize_text(context)
        formatted = f"{_normalize_text(source)}"
        if display:
            formatted = f"{formatted} - {display}"
        pairs.append(formatted)

    if len(contexts) > len(entity.sources):
        for context in contexts[len(entity.sources) :]:
            pairs.append(_normalize_text(context))

    unique_pairs = list(dict.fromkeys(filter(None, pairs)))
    return "; ".join(unique_pairs) or "--"


def _resolve_label(profile: object | None, key: str, default: str) -> str:
    if profile is None:
        return default

    candidate: str | None = None
    if isinstance(profile, Mapping):
        labels = profile.get("labels")
        if isinstance(labels, Mapping):
            candidate = labels.get(key)
        elif isinstance(labels, str) and key == _TITLE_KEY:
            candidate = labels
        else:
            candidate = profile.get(key) if isinstance(profile.get(key), str) else candidate
    else:
        labels = getattr(profile, "labels", None)
        if isinstance(labels, Mapping):
            candidate = labels.get(key)
        elif isinstance(labels, str) and key == _TITLE_KEY:
            candidate = labels
        else:
            attr_value = getattr(profile, key.replace(".", "_"), None)
            if isinstance(attr_value, str):
                candidate = attr_value

    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    return default


__all__ = [
    "ReportEnvelope",
    "ReportRenderOptions",
    "render_entities_report",
]
