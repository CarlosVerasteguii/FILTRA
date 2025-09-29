"""PDF ingestion helpers for Filtra."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from filtra.errors import PdfExtractionError
from filtra.utils import LoadedDocument, format_display_path, normalize_newlines

_PDF_ENCODING_LABEL = "utf-8"


def extract_text(path: Path, *, description: str) -> LoadedDocument:
    """Extract text content from a PDF file with whitespace normalization."""

    try:
        handle = path.open("rb")
    except OSError as exc:
        raise PdfExtractionError(
            message=(
                f"Unable to open the {description} file {format_display_path(path)} for reading."
            ),
            remediation="Verify the file is accessible and not locked by another process.",
        ) from exc

    with handle:
        try:
            reader = PdfReader(handle)
        except PdfReadError as exc:
            raise PdfExtractionError(
                message=(
                    f"The {description} file {format_display_path(path)} is not a readable PDF."
                ),
                remediation="Provide a valid text-based PDF export and retry the command.",
            ) from exc

        if reader.is_encrypted:
            raise PdfExtractionError(
                message=(
                    f"The {description} file {format_display_path(path)} is password protected."
                ),
                remediation="Remove the password or export an unencrypted copy before retrying.",
            )

        if not reader.pages:
            raise PdfExtractionError(
                message=(
                    f"The {description} file {format_display_path(path)} "
                    "does not contain any pages."
                ),
                remediation="Export the document as a standard PDF and retry.",
            )

        processed_pages: list[str] = []
        text_found = False
        for index, page in enumerate(reader.pages, start=1):
            try:
                raw_text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover - defensive guard for PyPDF
                raise PdfExtractionError(
                    message=(
                        "An error occurred while extracting text from "
                        f"page {index} of {format_display_path(path)}."
                    ),
                    remediation="Re-export the document as a searchable PDF and retry.",
                ) from exc

            cleaned = _normalize(raw_text)
            if cleaned:
                text_found = True
                processed_pages.append(cleaned)

        if not text_found:
            raise PdfExtractionError(
                message=(
                    f"The {description} file {format_display_path(path)} appears to be image-only."
                ),
                remediation="Run OCR and export a text-based PDF before rerunning Filtra.",
            )

        text = _join_pages(processed_pages)

    return LoadedDocument(path=path, text=text, encoding=_PDF_ENCODING_LABEL)


def _normalize(raw_text: str) -> str:
    """Trim extraneous whitespace while keeping line structure."""

    if not raw_text:
        return ""

    normalized = normalize_newlines(raw_text.replace("\u00a0", " "))
    lines = [line.strip() for line in normalized.split("\n")]

    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if previous_blank:
                continue
            previous_blank = True
            collapsed.append("")
            continue
        previous_blank = False
        collapsed.append(" ".join(line.split()))

    text = "\n".join(collapsed).strip()
    return text


def _join_pages(pages: list[str]) -> str:
    """Combine normalized page content into a single UTF-8 string."""

    combined = "\n\n".join(page for page in pages if page)
    return combined.strip()


__all__ = ["extract_text"]
