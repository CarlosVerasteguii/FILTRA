from __future__ import annotations

from pathlib import Path

import pytest
from pypdf.errors import PdfReadError

from filtra.errors import PdfExtractionError
from filtra.ingestion.pdf_loader import extract_text
from filtra.utils import LoadedDocument


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, pages: list[_FakePage], *, encrypted: bool = False) -> None:
        self.pages = pages
        self.is_encrypted = encrypted


@pytest.fixture()
def pdf_path(tmp_path: Path) -> Path:
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"%PDF")
    return path


def test_extract_text_normalizes_content(monkeypatch: pytest.MonkeyPatch, pdf_path: Path) -> None:
    expected_pages = [_FakePage("Hello\u00a0 PDF\r\n"), _FakePage("Second   Page  ")]

    def _reader(handle: object) -> _FakeReader:
        assert handle is not None
        return _FakeReader(expected_pages)

    monkeypatch.setattr("filtra.ingestion.pdf_loader.PdfReader", _reader)

    document = extract_text(pdf_path, description="resume")

    assert isinstance(document, LoadedDocument)
    assert document.text == "Hello PDF\n\nSecond Page"
    assert document.encoding == "utf-8"


def test_extract_text_rejects_encrypted_pdf(
    monkeypatch: pytest.MonkeyPatch, pdf_path: Path
) -> None:
    def _reader(handle: object) -> _FakeReader:
        return _FakeReader([_FakePage("Secret")], encrypted=True)

    monkeypatch.setattr("filtra.ingestion.pdf_loader.PdfReader", _reader)

    with pytest.raises(PdfExtractionError) as exc:
        extract_text(pdf_path, description="resume")

    assert "password" in exc.value.message.lower()


def test_extract_text_detects_image_only_pdf(
    monkeypatch: pytest.MonkeyPatch, pdf_path: Path
) -> None:
    def _reader(handle: object) -> _FakeReader:
        return _FakeReader([_FakePage(""), _FakePage("")])

    monkeypatch.setattr("filtra.ingestion.pdf_loader.PdfReader", _reader)

    with pytest.raises(PdfExtractionError) as exc:
        extract_text(pdf_path, description="resume")

    assert "image-only" in exc.value.message


def test_extract_text_handles_reader_errors(
    monkeypatch: pytest.MonkeyPatch, pdf_path: Path
) -> None:
    def _reader(handle: object) -> _FakeReader:
        raise PdfReadError("corrupt")

    monkeypatch.setattr("filtra.ingestion.pdf_loader.PdfReader", _reader)

    with pytest.raises(PdfExtractionError) as exc:
        extract_text(pdf_path, description="resume")

    assert "not a readable PDF" in exc.value.message


def test_extract_text_handles_page_exceptions(
    monkeypatch: pytest.MonkeyPatch, pdf_path: Path
) -> None:
    class _ExplodingPage:
        def extract_text(self) -> str:
            raise RuntimeError("boom")

    def _reader(handle: object) -> _FakeReader:
        return _FakeReader([_ExplodingPage()])

    monkeypatch.setattr("filtra.ingestion.pdf_loader.PdfReader", _reader)

    with pytest.raises(PdfExtractionError) as exc:
        extract_text(pdf_path, description="resume")

    assert "extracting text" in exc.value.message


def test_extract_text_handles_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.pdf"

    with pytest.raises(PdfExtractionError) as exc:
        extract_text(missing, description="resume")

    assert "Unable to open the resume file" in exc.value.message

