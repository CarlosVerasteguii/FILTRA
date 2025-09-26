from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from filtra.errors import TimeoutExceededError
from filtra.orchestration.warmup import run_warmup


def _fake_prefetch(*, cache_dir: Path, **_: object) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "weights.bin").write_bytes(b"weights")


def test_run_warmup_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("filtra.ner.pipeline._prefetch_artifacts", _fake_prefetch)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://openrouter.ai/api/v1/chat/completions")
        return httpx.Response(200, json={"id": "req-123"})

    transport = httpx.MockTransport(handler)

    result = run_warmup(transport=transport)

    assert result.overall_status == "PASS"
    assert result.cache_size_bytes > 0
    assert result.huggingface_cache.exists()
    assert any(check.name == "OpenRouter connectivity" for check in result.checks)


def test_run_warmup_times_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("filtra.ner.pipeline._prefetch_artifacts", _fake_prefetch)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Timed out", request=request)

    transport = httpx.MockTransport(handler)

    with pytest.raises(TimeoutExceededError):
        run_warmup(transport=transport)
