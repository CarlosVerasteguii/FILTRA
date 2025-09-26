from __future__ import annotations

from pathlib import Path

import pytest

from filtra.errors import InputValidationError
from filtra.utils import load_text_document, normalize_newlines


def test_load_text_document_prefers_utf8(tmp_path: Path) -> None:
    document = tmp_path / "resume.txt"
    document.write_text("línea uno\r\nlinea dos", encoding="utf-8-sig")

    loaded = load_text_document(document, "resume")

    assert loaded.encoding == "utf-8-sig"
    assert loaded.display_encoding == "UTF-8 (with BOM)"
    assert loaded.text == "línea uno\nlinea dos"


def test_load_text_document_falls_back_to_cp1252(tmp_path: Path) -> None:
    document = tmp_path / "jd.txt"
    document.write_bytes("requisición".encode("cp1252"))

    loaded = load_text_document(document, "job description")

    assert loaded.encoding == "cp1252"
    assert loaded.display_encoding == "Windows-1252"
    assert loaded.text == "requisición"


def test_load_text_document_raises_when_unsupported(tmp_path: Path) -> None:
    document = tmp_path / "jd.txt"
    document.write_bytes(bytes([0x81, 0x82, 0x83]))

    with pytest.raises(InputValidationError) as exc:
        load_text_document(document, "job description")

    assert "Windows-1252" in exc.value.message


def test_normalize_newlines_converts_carriage_returns() -> None:
    text = "uno\r\ndos\rtres\n"

    assert normalize_newlines(text) == "uno\ndos\ntres\n"
