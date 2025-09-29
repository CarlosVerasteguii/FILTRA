"""Filesystem helpers with Windows-friendly defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from filtra.errors import InputValidationError

_PREFERRED_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "cp1252")
_ENCODING_LABELS: dict[str, str] = {
    "utf-8-sig": "UTF-8 (with BOM)",
    "cp1252": "Windows-1252",
    "utf-8": "UTF-8",
}


@dataclass(frozen=True)
class LoadedDocument:
    """Represents text loaded from disk with associated metadata."""

    path: Path
    text: str
    encoding: str

    @property
    def display_name(self) -> str:
        """Return the filename quoted when needed for display contexts."""

        return format_display_path(self.path)

    @property
    def display_encoding(self) -> str:
        """Return a human-friendly label for the document encoding."""

        return _ENCODING_LABELS.get(self.encoding, self.encoding)


def normalize_newlines(text: str) -> str:
    """Convert Windows/legacy newline sequences to Unix-style newlines."""

    if "\r" not in text:
        return text

    # Handle the Windows text-mode quirk where writing `\r\n` results in `\r\r\n`.
    text = text.replace("\r\r\n", "\n")
    text = text.replace("\r\n", "\n")
    return text.replace("\r", "\n")


def format_display_path(path: Path) -> str:
    """Format a path for human-readable output without leaking directories."""

    name = path.name
    if " " in name:
        return f'"{name}"'
    return name


def load_text_document(path: Path, description: str) -> LoadedDocument:
    """Read text from disk using UTF-8 BOM first, then Windows-1252 fallback."""

    try:
        data = path.read_bytes()
    except OSError as exc:  # pragma: no cover - mirrors Path error messaging
        raise InputValidationError(
            message=f"Unable to read the {description} file {format_display_path(path)}.",
            remediation=(
                "Verify file permissions and that the file is not locked by another process."
            ),
        ) from exc

    last_error: UnicodeDecodeError | None = None
    for encoding in _PREFERRED_ENCODINGS:
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        normalized = normalize_newlines(text)
        return LoadedDocument(path=path, text=normalized, encoding=encoding)

    supported = ", ".join(_ENCODING_LABELS[enc] for enc in _PREFERRED_ENCODINGS)
    raise InputValidationError(
        message=(
            f"The {description} file {format_display_path(path)} is not encoded as {supported}."
        ),
        remediation="Re-save the document using UTF-8 (with BOM) or Windows-1252 and retry.",
    ) from last_error


__all__ = [
    "LoadedDocument",
    "format_display_path",
    "load_text_document",
    "normalize_newlines",
]

