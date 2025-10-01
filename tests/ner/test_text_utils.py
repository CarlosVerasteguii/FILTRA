from __future__ import annotations

import pytest

from filtra.utils.text import build_context_snippet


def test_build_context_snippet_trims_with_ellipses() -> None:
    text = "".join(
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " for _ in range(3)
    )
    span = (30, 35)

    snippet = build_context_snippet(text, span, window=10)

    assert snippet.startswith("...")
    assert snippet.endswith("...")
    assert text[span[0]:span[1]] in snippet
    assert len(snippet) <= (2 * 10) + (span[1] - span[0]) + 6


def test_build_context_snippet_handles_edges() -> None:
    text = "Start middle end"
    start_span = (0, 5)
    end_span = (12, len(text))

    start_snippet = build_context_snippet(text, start_span, window=5)
    end_snippet = build_context_snippet(text, end_span, window=5)

    assert not start_snippet.startswith("...")
    assert start_snippet.endswith("...")
    assert start_snippet.startswith("Start")

    assert end_snippet.startswith("...")
    assert not end_snippet.endswith("...")
    assert end_snippet.endswith("end")


def test_build_context_snippet_rejects_negative_window() -> None:
    with pytest.raises(ValueError):
        build_context_snippet("sample", (0, 1), window=-1)
